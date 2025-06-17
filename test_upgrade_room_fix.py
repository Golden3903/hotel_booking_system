#!/usr/bin/env python3
"""
测试升级房间功能修复
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

def test_upgrade_room_intent():
    """测试升级房间意图识别和处理"""
    
    print("🔍 测试升级房间功能修复")
    print("=" * 50)
    
    factory = RequestFactory()
    
    # 测试用例：用户说"upgrade room"
    test_cases = [
        {
            "name": "基本升级请求",
            "message": "upgrade room",
            "session": {"state": "greeting", "user_data": {}}
        },
        {
            "name": "升级我的房间",
            "message": "upgrade my room",
            "session": {"state": "greeting", "user_data": {}}
        },
        {
            "name": "房间升级",
            "message": "room upgrade",
            "session": {"state": "greeting", "user_data": {}}
        },
        {
            "name": "升级到更好的房间",
            "message": "upgrade to better room",
            "session": {"state": "greeting", "user_data": {}}
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🔍 测试 {i}: {test_case['name']}")
        print("-" * 30)
        print(f"用户输入: '{test_case['message']}'")
        
        try:
            payload = {
                "message": test_case['message'],
                "session": test_case['session']
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
                
                # 检查是否正确处理升级意图
                expected_keywords = [
                    "upgrade", "booking id", "reservation", "help you upgrade",
                    "room upgrade", "provide your booking"
                ]
                
                contains_upgrade_keywords = any(
                    keyword.lower() in response_message.lower() 
                    for keyword in expected_keywords
                )
                
                if contains_upgrade_keywords:
                    print("✅ 正确识别升级意图")
                else:
                    print("❌ 未正确识别升级意图")
                    print(f"   期望包含关键词: {expected_keywords}")
                
                # 检查是否不是问候语
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
    print("🎯 升级房间功能测试完成")

def test_upgrade_flow():
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
                
                # 检查是否进入升级选择状态
                if data2['session'].get('state') == 'selecting_upgrade_room':
                    print("✅ 成功进入房间升级选择状态")
                else:
                    print(f"⚠️ 状态不符合预期，当前状态: {data2['session'].get('state')}")
                    
            else:
                print(f"❌ 步骤2失败: HTTP {response2.status_code}")
                
        else:
            print(f"❌ 步骤1失败: HTTP {response1.status_code}")
            
    except Exception as e:
        print(f"❌ 流程测试异常: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_upgrade_room_intent()
    test_upgrade_flow()
    print("\n🎉 所有测试完成！")
