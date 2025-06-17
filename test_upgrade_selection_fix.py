#!/usr/bin/env python3
"""
测试升级房间选择功能修复
"""

import os
import sys
import django
import json

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
django.setup()

from django.test import RequestFactory
from django.contrib.auth.models import AnonymousUser
from hotel_booking.chatbot.views import chatbot_api

def test_upgrade_room_selection():
    """测试升级房间选择功能"""
    
    print("🔍 测试升级房间选择功能修复")
    print("=" * 50)
    
    factory = RequestFactory()
    
    # 模拟升级房间选择状态
    session_data = {
        "state": "selecting_upgrade_room",
        "user_data": {
            "booking_to_upgrade": {
                "id": 1,
                "booking_id": "BK-12345",
                "current_price": 100.0,
                "duration": 2
            }
        }
    }
    
    # 测试用例：用户选择不同的房间类型
    test_cases = [
        {
            "name": "选择Deluxe Room",
            "message": "deluxe room",
            "expected_keywords": ["upgraded", "deluxe", "additional cost"]
        },
        {
            "name": "选择Deluxe",
            "message": "deluxe",
            "expected_keywords": ["upgraded", "deluxe", "additional cost"]
        },
        {
            "name": "选择Suite",
            "message": "suite",
            "expected_keywords": ["upgraded", "suite", "additional cost"]
        },
        {
            "name": "选择Executive Suite",
            "message": "executive suite",
            "expected_keywords": ["upgraded", "executive", "additional cost"]
        },
        {
            "name": "选择不存在的房间",
            "message": "presidential villa",
            "expected_keywords": ["couldn't find", "available", "options"]
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🔍 测试 {i}: {test_case['name']}")
        print("-" * 30)
        print(f"用户输入: '{test_case['message']}'")
        
        try:
            payload = {
                "message": test_case['message'],
                "session": session_data.copy()  # 使用副本避免状态污染
            }
            
            request = factory.post(
                '/hotel_booking/chatbot/api/',
                data=json.dumps(payload),
                content_type='application/json'
            )
            request.user = AnonymousUser()
            
            response = chatbot_api(request)
            
            if response.status_code == 200:
                data = json.loads(response.content.decode('utf-8'))
                response_message = data['message']
                new_state = data['session'].get('state', 'unknown')
                
                print(f"✅ 响应成功")
                print(f"📝 机器人回复: {response_message[:200]}...")
                print(f"📍 新状态: {new_state}")
                
                # 检查是否包含期望的关键词
                contains_expected = any(
                    keyword.lower() in response_message.lower() 
                    for keyword in test_case['expected_keywords']
                )
                
                if contains_expected:
                    print("✅ 包含期望的关键词")
                else:
                    print("❌ 未包含期望的关键词")
                    print(f"   期望关键词: {test_case['expected_keywords']}")
                
                # 检查是否不是错误的问候语
                greeting_keywords = ["hello", "may i have your name", "happy to help you with your booking"]
                is_greeting = any(
                    keyword.lower() in response_message.lower() 
                    for keyword in greeting_keywords
                )
                
                if not is_greeting:
                    print("✅ 不是错误的问候语回复")
                else:
                    print("❌ 错误地回复了问候语")
                    
            else:
                print(f"❌ HTTP错误: {response.status_code}")
                print(f"响应内容: {response.content.decode('utf-8')}")
                
        except Exception as e:
            print(f"❌ 测试异常: {str(e)}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 50)
    print("🎯 升级房间选择功能测试完成")

def test_complete_upgrade_flow():
    """测试完整的升级流程"""
    
    print("\n🔍 测试完整升级流程")
    print("=" * 50)
    
    factory = RequestFactory()
    session_data = {"state": "greeting", "user_data": {}}
    
    # 步骤1: 用户说"upgrade room"
    print("\n📍 步骤1: 用户请求升级房间")
    print("-" * 30)
    
    try:
        payload1 = {
            "message": "upgrade room",
            "session": session_data
        }
        
        request1 = factory.post(
            '/hotel_booking/chatbot/api/',
            data=json.dumps(payload1),
            content_type='application/json'
        )
        request1.user = AnonymousUser()
        
        response1 = chatbot_api(request1)
        
        if response1.status_code == 200:
            data1 = json.loads(response1.content.decode('utf-8'))
            print(f"✅ 机器人回复: {data1['message'][:150]}...")
            print(f"📍 状态: {data1['session'].get('state')}")
            
            # 更新会话数据
            session_data = data1['session']
            
            # 步骤2: 用户提供booking ID
            print("\n📍 步骤2: 用户提供booking ID")
            print("-" * 30)
            
            payload2 = {
                "message": "BK-12345",
                "session": session_data
            }
            
            request2 = factory.post(
                '/hotel_booking/chatbot/api/',
                data=json.dumps(payload2),
                content_type='application/json'
            )
            request2.user = AnonymousUser()
            
            response2 = chatbot_api(request2)
            
            if response2.status_code == 200:
                data2 = json.loads(response2.content.decode('utf-8'))
                print(f"✅ 机器人回复: {data2['message'][:150]}...")
                print(f"📍 状态: {data2['session'].get('state')}")
                
                # 更新会话数据
                session_data = data2['session']
                
                # 步骤3: 用户选择房间类型
                print("\n📍 步骤3: 用户选择房间类型")
                print("-" * 30)
                
                payload3 = {
                    "message": "deluxe room",
                    "session": session_data
                }
                
                request3 = factory.post(
                    '/hotel_booking/chatbot/api/',
                    data=json.dumps(payload3),
                    content_type='application/json'
                )
                request3.user = AnonymousUser()
                
                response3 = chatbot_api(request3)
                
                if response3.status_code == 200:
                    data3 = json.loads(response3.content.decode('utf-8'))
                    print(f"✅ 机器人回复: {data3['message'][:150]}...")
                    print(f"📍 状态: {data3['session'].get('state')}")
                    
                    # 检查是否成功升级
                    if "upgraded" in data3['message'].lower():
                        print("✅ 成功完成房间升级")
                    else:
                        print(f"⚠️ 升级可能未成功，回复内容: {data3['message']}")
                        
                else:
                    print(f"❌ 步骤3失败: HTTP {response3.status_code}")
                    
            else:
                print(f"❌ 步骤2失败: HTTP {response2.status_code}")
                
        else:
            print(f"❌ 步骤1失败: HTTP {response1.status_code}")
            
    except Exception as e:
        print(f"❌ 流程测试异常: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_upgrade_room_selection()
    test_complete_upgrade_flow()
    print("\n🎉 所有测试完成！")
