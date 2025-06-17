#!/usr/bin/env python3
"""
测试chatbot预订与booking history同步功能
"""

import os
import sys
import django
import json
from datetime import date, timedelta

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
django.setup()

from django.test import RequestFactory, Client
from django.contrib.auth.models import User
from hotel_booking.models import Room, Booking
from hotel_booking.chatbot.views import chatbot_api

def test_chatbot_booking_to_history_sync():
    """测试chatbot预订到booking history的同步"""
    
    print("🔍 测试chatbot预订与booking history同步")
    print("=" * 50)
    
    # 创建测试用户
    test_user, created = User.objects.get_or_create(
        username='testuser',
        defaults={
            'email': 'testuser@example.com',
            'first_name': 'Test',
            'last_name': 'User'
        }
    )
    if created:
        test_user.set_password('testpass123')
        test_user.save()
        print(f"✅ 创建测试用户: {test_user.username}")
    else:
        print(f"📋 使用现有测试用户: {test_user.username}")
    
    # 确保有房间数据
    standard_room, created = Room.objects.get_or_create(
        name="Standard Room",
        defaults={
            "price": 132.0,
            "description": "Comfortable standard room"
        }
    )
    
    factory = RequestFactory()
    client = Client()
    
    # 登录用户
    client.login(username='testuser', password='testpass123')
    
    print("\n📍 步骤1: 通过chatbot进行完整预订流程")
    print("-" * 30)
    
    # 模拟完整的预订流程
    session_data = {"state": "greeting", "user_data": {}}
    
    # 步骤1: 用户说"book room"
    print("用户输入: 'book room'")
    payload1 = {
        "message": "book room",
        "session": session_data
    }
    
    request1 = factory.post(
        '/hotel_booking/chatbot/api/',
        data=json.dumps(payload1),
        content_type='application/json'
    )
    request1.user = test_user
    
    response1 = chatbot_api(request1)
    
    if response1.status_code == 200:
        data1 = json.loads(response1.content.decode('utf-8'))
        print(f"✅ 机器人回复: {data1['message'][:100]}...")
        session_data = data1['session']
        
        # 步骤2: 提供预订信息
        print("\n用户输入预订信息...")
        booking_info = "John Doe, john@example.com, 0123456789, Standard Room, 2025-06-20, 2025-06-22"
        
        payload2 = {
            "message": booking_info,
            "session": session_data
        }
        
        request2 = factory.post(
            '/hotel_booking/chatbot/api/',
            data=json.dumps(payload2),
            content_type='application/json'
        )
        request2.user = test_user
        
        response2 = chatbot_api(request2)
        
        if response2.status_code == 200:
            data2 = json.loads(response2.content.decode('utf-8'))
            print(f"✅ 机器人回复: {data2['message'][:100]}...")
            session_data = data2['session']
            
            # 检查是否生成了booking ID
            booking_id = session_data.get('user_data', {}).get('booking_id')
            if booking_id:
                print(f"✅ 生成的Booking ID: {booking_id}")
                
                # 步骤3: 检查数据库中的预订记录
                print("\n📍 步骤2: 检查数据库中的预订记录")
                print("-" * 30)
                
                booking = Booking.objects.filter(booking_id=booking_id).first()
                if booking:
                    print(f"✅ 数据库中找到预订记录:")
                    print(f"   Booking ID: {booking.booking_id}")
                    print(f"   客人姓名: {booking.guest_name}")
                    print(f"   关联用户: {booking.user.username if booking.user else 'None'}")
                    print(f"   房间类型: {booking.room.name}")
                    print(f"   入住日期: {booking.check_in_date}")
                    print(f"   退房日期: {booking.check_out_date}")
                    print(f"   状态: {booking.status}")
                    
                    # 步骤4: 检查用户个人资料页面的booking history
                    print("\n📍 步骤3: 检查用户个人资料页面")
                    print("-" * 30)
                    
                    response = client.get('/hotel_booking/profile/')
                    if response.status_code == 200:
                        print("✅ 成功访问用户个人资料页面")
                        
                        # 检查页面内容是否包含booking ID
                        content = response.content.decode('utf-8')
                        if booking_id in content:
                            print(f"✅ Booking ID {booking_id} 出现在个人资料页面中")
                        else:
                            print(f"❌ Booking ID {booking_id} 未出现在个人资料页面中")
                        
                        # 检查是否包含其他预订信息
                        if booking.guest_name in content:
                            print(f"✅ 客人姓名 {booking.guest_name} 出现在页面中")
                        
                        if booking.room.name in content:
                            print(f"✅ 房间类型 {booking.room.name} 出现在页面中")
                        
                        print("✅ 预订信息成功同步到booking history")
                        
                    else:
                        print(f"❌ 访问用户个人资料页面失败: HTTP {response.status_code}")
                        
                else:
                    print(f"❌ 数据库中未找到Booking ID为 {booking_id} 的预订记录")
                    
            else:
                print("❌ 未生成Booking ID")
                
        else:
            print(f"❌ 步骤2失败: HTTP {response2.status_code}")
            
    else:
        print(f"❌ 步骤1失败: HTTP {response1.status_code}")
    
    print("\n" + "=" * 50)
    print("🎯 测试完成")

def test_booking_history_display():
    """测试booking history页面显示"""
    
    print("\n🔍 测试booking history页面显示")
    print("=" * 50)
    
    client = Client()
    
    # 登录测试用户
    client.login(username='testuser', password='testpass123')
    
    # 访问用户个人资料页面
    response = client.get('/hotel_booking/profile/')
    
    if response.status_code == 200:
        print("✅ 成功访问用户个人资料页面")
        
        # 检查页面是否包含Booking ID列
        content = response.content.decode('utf-8')
        
        if 'Booking ID' in content:
            print("✅ 页面包含 'Booking ID' 列标题")
        else:
            print("❌ 页面不包含 'Booking ID' 列标题")
        
        # 查找用户的所有预订
        test_user = User.objects.get(username='testuser')
        user_bookings = Booking.objects.filter(user=test_user)
        
        print(f"📊 用户共有 {user_bookings.count()} 个预订记录")
        
        for booking in user_bookings:
            if booking.booking_id and booking.booking_id in content:
                print(f"✅ Booking ID {booking.booking_id} 显示在页面中")
            elif booking.booking_id:
                print(f"❌ Booking ID {booking.booking_id} 未显示在页面中")
            else:
                print(f"⚠️ 预订 {booking.id} 没有booking_id")
                
    else:
        print(f"❌ 访问用户个人资料页面失败: HTTP {response.status_code}")

if __name__ == "__main__":
    test_chatbot_booking_to_history_sync()
    test_booking_history_display()
    print("\n🎉 所有测试完成！")
