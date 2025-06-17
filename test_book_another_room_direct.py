#!/usr/bin/env python3
"""
直接测试"book another room"功能（不通过HTTP API）
"""

import os
import sys
import django

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
django.setup()

from hotel_booking.chatbot.views import chatbot_api
from django.test import RequestFactory
from django.contrib.auth.models import AnonymousUser
import json

def test_book_another_room_direct():
    """直接测试book another room功能"""
    
    print("🧪 直接测试Book Another Room功能")
    print("=" * 60)
    
    # 创建请求工厂
    factory = RequestFactory()
    
    # 测试数据 - 模拟已有预订的用户
    session_data = {
        'state': 'greeting',
        'user_data': {
            'is_returning_customer': True,
            'guest_name': 'John Doe',
            'email': 'john.doe@example.com',
            'phone': '0123456789'
        }
    }
    
    print("📋 初始会话状态:")
    print(f"状态: {session_data['state']}")
    print(f"用户数据: {session_data['user_data']}")
    print()
    
    # 测试步骤1: 发起"book another room"请求
    print("🔍 步骤1: 发起book another room请求")
    print("-" * 40)
    
    payload1 = {
        "message": "booking another room",
        "session": session_data
    }
    
    try:
        # 创建POST请求
        request1 = factory.post(
            '/hotel_booking/chatbot/api/',
            data=json.dumps(payload1),
            content_type='application/json'
        )
        request1.user = AnonymousUser()
        
        # 调用视图函数
        response1 = chatbot_api(request1)
        
        print(f"HTTP状态码: {response1.status_code}")
        
        if response1.status_code == 200:
            data1 = json.loads(response1.content.decode('utf-8'))
            print(f"🤖 机器人响应:")
            print(f"{data1['message'][:300]}..." if len(data1['message']) > 300 else data1['message'])
            print()
            print(f"📍 新状态: {data1['session'].get('state')}")
            print(f"📝 用户数据: {data1['session'].get('user_data')}")
            
            # 更新会话数据
            session_data = data1['session']
            
            print("✅ 步骤1成功")
        else:
            print(f"❌ 步骤1失败: HTTP {response1.status_code}")
            print(f"响应内容: {response1.content.decode('utf-8')}")
            return False
            
    except Exception as e:
        print(f"❌ 步骤1处理错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n" + "=" * 60)
    
    # 测试步骤2: 选择房间类型
    print("🔍 步骤2: 选择房间类型")
    print("-" * 40)
    
    payload2 = {
        "message": "deluxe room",
        "session": session_data
    }
    
    try:
        # 创建POST请求
        request2 = factory.post(
            '/hotel_booking/chatbot/api/',
            data=json.dumps(payload2),
            content_type='application/json'
        )
        request2.user = AnonymousUser()
        
        # 调用视图函数
        response2 = chatbot_api(request2)
        
        print(f"HTTP状态码: {response2.status_code}")
        
        if response2.status_code == 200:
            data2 = json.loads(response2.content.decode('utf-8'))
            print(f"🤖 机器人响应:")
            print(f"{data2['message'][:300]}..." if len(data2['message']) > 300 else data2['message'])
            print()
            print(f"📍 新状态: {data2['session'].get('state')}")
            print(f"📝 用户数据: {data2['session'].get('user_data')}")
            
            # 检查是否正确进入日期确认状态
            if data2['session'].get('state') == 'confirming_additional_dates':
                print("✅ 步骤2成功 - 正确进入日期确认状态")
                session_data = data2['session']
            else:
                print(f"❌ 步骤2失败 - 状态错误: {data2['session'].get('state')}")
                # 检查是否错误地开始了新的预订流程
                if "May I have your name please?" in data2['message']:
                    print("❌ 错误：开始了新的预订流程而不是继续额外房间预订")
                return False
        else:
            print(f"❌ 步骤2失败: HTTP {response2.status_code}")
            print(f"响应内容: {response2.content.decode('utf-8')}")
            return False
            
    except Exception as e:
        print(f"❌ 步骤2处理错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n" + "=" * 60)
    
    # 测试步骤3: 确认日期
    print("🔍 步骤3: 确认使用相同日期")
    print("-" * 40)
    
    payload3 = {
        "message": "A",
        "session": session_data
    }
    
    try:
        # 创建POST请求
        request3 = factory.post(
            '/hotel_booking/chatbot/api/',
            data=json.dumps(payload3),
            content_type='application/json'
        )
        request3.user = AnonymousUser()
        
        # 调用视图函数
        response3 = chatbot_api(request3)
        
        print(f"HTTP状态码: {response3.status_code}")
        
        if response3.status_code == 200:
            data3 = json.loads(response3.content.decode('utf-8'))
            print(f"🤖 机器人响应:")
            print(f"{data3['message'][:300]}..." if len(data3['message']) > 300 else data3['message'])
            print()
            print(f"📍 新状态: {data3['session'].get('state')}")
            print(f"📝 用户数据: {data3['session'].get('user_data')}")
            
            # 检查是否正确进入最终确认状态
            if data3['session'].get('state') == 'confirming_additional_booking':
                print("✅ 步骤3成功 - 正确进入最终确认状态")
                session_data = data3['session']
            else:
                print(f"❌ 步骤3失败 - 状态错误: {data3['session'].get('state')}")
                return False
        else:
            print(f"❌ 步骤3失败: HTTP {response3.status_code}")
            print(f"响应内容: {response3.content.decode('utf-8')}")
            return False
            
    except Exception as e:
        print(f"❌ 步骤3处理错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n" + "=" * 60)
    print("📊 测试结果总结")
    print("✅ Book Another Room功能修复验证成功！")
    print("- 步骤1: 正确识别book another room意图")
    print("- 步骤2: 正确处理房间选择，没有错误地开始新预订流程")
    print("- 步骤3: 正确进入日期确认流程")
    print("🎉 修复完全成功！")
    
    return True

if __name__ == "__main__":
    test_book_another_room_direct()
