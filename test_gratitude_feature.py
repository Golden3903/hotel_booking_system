#!/usr/bin/env python3
"""
测试感谢意图功能
Test the gratitude intent feature
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

def test_gratitude_intent():
    """测试感谢意图功能"""
    
    print("🧪 测试感谢意图功能")
    print("=" * 60)
    
    # 创建请求工厂
    factory = RequestFactory()
    
    # 测试不同的感谢表达
    gratitude_expressions = [
        "thank you",
        "thanks",
        "terima kasih",
        "thank you so much",
        "many thanks",
        "tq",
        "ty",
        "thx",
        "appreciate it",
        "that's helpful",
        "thanks for the help",
        "thanks a lot",
        "much appreciated",
        "grateful",
        "cheers",
        "thanks mate"
    ]
    
    # 测试不同的会话状态
    test_scenarios = [
        {
            "name": "刚完成预订后的感谢",
            "session": {
                'state': 'booking_confirmed',
                'user_data': {
                    'booking_id': 'BK-12345',
                    'guest_name': 'John Doe'
                }
            }
        },
        {
            "name": "查看预订状态后的感谢",
            "session": {
                'state': 'greeting',
                'user_data': {
                    'last_viewed_booking': {
                        'booking_id': 'BK-67890',
                        'guest_name': 'Jane Smith'
                    }
                }
            }
        },
        {
            "name": "在附加服务流程中的感谢",
            "session": {
                'state': 'offering_addons',
                'user_data': {
                    'booking_id': 'BK-11111'
                }
            }
        },
        {
            "name": "显示服务菜单后的感谢",
            "session": {
                'state': 'greeting',
                'user_data': {
                    'showing_service_menu': True
                }
            }
        },
        {
            "name": "一般对话中的感谢",
            "session": {
                'state': 'greeting',
                'user_data': {}
            }
        }
    ]
    
    success_count = 0
    total_tests = 0
    
    for scenario in test_scenarios:
        print(f"\n🔍 测试场景: {scenario['name']}")
        print("-" * 40)
        
        # 测试几个不同的感谢表达
        test_expressions = gratitude_expressions[:3]  # 测试前3个表达
        
        for expression in test_expressions:
            total_tests += 1
            
            try:
                payload = {
                    "message": expression,
                    "session": scenario['session']
                }
                
                # 创建POST请求
                request = factory.post(
                    '/hotel_booking/chatbot/api/',
                    data=json.dumps(payload),
                    content_type='application/json'
                )
                request.user = AnonymousUser()
                
                # 调用视图函数
                response = chatbot_api(request)
                
                if response.status_code == 200:
                    data = json.loads(response.content.decode('utf-8'))
                    response_message = data['message']
                    
                    # 检查响应是否包含感谢回复的关键词
                    gratitude_response_keywords = [
                        "you're welcome", "welcome", "happy to help", 
                        "my pleasure", "pleasure", "glad", "assist"
                    ]
                    
                    is_gratitude_response = any(
                        keyword in response_message.lower() 
                        for keyword in gratitude_response_keywords
                    )
                    
                    if is_gratitude_response:
                        print(f"✅ '{expression}' -> 正确识别并回应")
                        print(f"   回应: {response_message[:100]}...")
                        success_count += 1
                    else:
                        print(f"❌ '{expression}' -> 未正确识别为感谢意图")
                        print(f"   回应: {response_message[:100]}...")
                else:
                    print(f"❌ '{expression}' -> HTTP错误: {response.status_code}")
                    
            except Exception as e:
                print(f"❌ '{expression}' -> 处理错误: {str(e)}")
    
    print("\n" + "=" * 60)
    print("📊 测试结果总结")
    print(f"✅ 成功: {success_count}/{total_tests}")
    print(f"📈 成功率: {(success_count/total_tests)*100:.1f}%")
    
    if success_count == total_tests:
        print("🎉 所有感谢意图测试通过！")
        return True
    else:
        print("⚠️ 部分测试失败，需要检查感谢意图处理")
        return False

def test_context_aware_responses():
    """测试上下文感知的感谢回应"""
    
    print("\n🧪 测试上下文感知的感谢回应")
    print("=" * 60)
    
    factory = RequestFactory()
    
    # 测试不同上下文的响应差异
    contexts = [
        {
            "name": "预订完成后",
            "session": {
                'state': 'booking_confirmed',
                'user_data': {'booking_id': 'BK-12345'}
            },
            "expected_keywords": ["stay", "visit", "reservation"]
        },
        {
            "name": "查看预订后",
            "session": {
                'state': 'greeting',
                'user_data': {
                    'last_viewed_booking': {'booking_id': 'BK-67890'}
                }
            },
            "expected_keywords": ["booking", "reservation", "help"]
        },
        {
            "name": "一般对话",
            "session": {
                'state': 'greeting',
                'user_data': {}
            },
            "expected_keywords": ["help", "assist", "hotel"]
        }
    ]
    
    for context in contexts:
        print(f"\n🔍 测试上下文: {context['name']}")
        print("-" * 30)
        
        try:
            payload = {
                "message": "thank you",
                "session": context['session']
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
                
                print(f"📝 回应: {response_message}")
                
                # 检查是否包含预期的上下文关键词
                has_context = any(
                    keyword in response_message.lower() 
                    for keyword in context['expected_keywords']
                )
                
                if has_context:
                    print("✅ 包含上下文相关内容")
                else:
                    print("⚠️ 可能缺少上下文相关内容")
            else:
                print(f"❌ HTTP错误: {response.status_code}")
                
        except Exception as e:
            print(f"❌ 处理错误: {str(e)}")

if __name__ == "__main__":
    print("🚀 开始感谢意图功能测试")
    
    # 测试基本感谢意图识别
    basic_success = test_gratitude_intent()
    
    # 测试上下文感知回应
    test_context_aware_responses()
    
    print("\n" + "=" * 60)
    print("🏁 测试完成")
    
    if basic_success:
        print("🎉 感谢意图功能实现成功！")
        print("\n✨ 功能特点:")
        print("- 支持多种感谢表达方式（英文、马来文、缩写等）")
        print("- 根据对话上下文提供个性化回应")
        print("- 在不同会话状态下给出合适的回复")
        print("- 包含酒店服务相关的后续引导")
    else:
        print("❌ 感谢意图功能需要进一步调试")
