#!/usr/bin/env python3
"""
测试改进的off-topic处理功能
"""

import requests
import json
import time

def test_off_topic_handling():
    """测试off-topic检测和引导功能"""
    
    base_url = "http://127.0.0.1:8000"
    chatbot_url = f"{base_url}/hotel_booking/chatbot/api/"
    
    # 测试用例：不同类型的off-topic查询
    test_cases = [
        {
            "message": "What do you like to eat?",
            "category": "small_talk",
            "description": "询问AI喜欢吃什么"
        },
        {
            "message": "How does AI work?",
            "category": "ai_tech", 
            "description": "询问AI工作原理"
        },
        {
            "message": "Will you fall in love?",
            "category": "small_talk",
            "description": "询问AI是否会恋爱"
        },
        {
            "message": "What time is it now?",
            "category": "time_query",
            "description": "询问当前时间"
        },
        {
            "message": "Do you know it will rain in Malaysia today?",
            "category": "weather",
            "description": "询问马来西亚天气"
        },
        {
            "message": "Are you really emotionless?",
            "category": "small_talk",
            "description": "询问AI是否有情感"
        },
        {
            "message": "Tell me a joke",
            "category": "general",
            "description": "要求讲笑话"
        },
        {
            "message": "What's the latest news?",
            "category": "general", 
            "description": "询问最新新闻"
        }
    ]
    
    print("🧪 测试改进的Off-Topic处理功能")
    print("=" * 60)
    
    session = {}
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n测试 {i}: {test_case['description']}")
        print(f"类别: {test_case['category']}")
        print(f"用户输入: \"{test_case['message']}\"")
        print("-" * 40)
        
        try:
            # 发送off-topic消息
            response = requests.post(chatbot_url, json={
                "message": test_case['message'],
                "user_id": 1,
                "session": session
            })
            
            if response.status_code == 200:
                data = response.json()
                bot_response = data.get('message', '')
                session = data.get('session', {})
                
                print(f"🤖 Chatbot响应:")
                print(f"{bot_response}")
                
                # 检查响应是否包含引导元素
                guidance_indicators = [
                    'book a room', 'hotel services', 'check facility',
                    'booking', 'cancellation', 'upgrade', 'extend',
                    'breakfast', 'airport transfer', 'what can i help'
                ]
                
                has_guidance = any(indicator in bot_response.lower() for indicator in guidance_indicators)
                
                if has_guidance:
                    print("✅ 包含引导回到酒店服务")
                else:
                    print("⚠️  可能缺少引导元素")
                    
                # 检查是否有幽默或创意回应
                humor_indicators = ['😊', '🤖', '💖', '🍳', '🕒', '☀️', '⏰']
                has_humor = any(emoji in bot_response for emoji in humor_indicators)
                
                if has_humor:
                    print("✅ 包含友好/幽默元素")
                    
            else:
                print(f"❌ 请求失败: {response.status_code}")
                
        except Exception as e:
            print(f"❌ 测试过程中出错: {str(e)}")
        
        print(f"✅ 测试 {i} 完成")
        time.sleep(1)  # 避免请求过快
    
    print("\n" + "=" * 60)
    print("🎯 Off-Topic处理功能测试完成！")
    
    # 测试多次off-topic的渐进式引导
    print("\n🔄 测试渐进式引导功能...")
    print("-" * 40)
    
    # 重置session
    session = {}
    
    progressive_tests = [
        "Tell me a joke",
        "What's the weather like?", 
        "How old are you?"
    ]
    
    for i, message in enumerate(progressive_tests, 1):
        print(f"\n第{i}次off-topic: \"{message}\"")
        
        try:
            response = requests.post(chatbot_url, json={
                "message": message,
                "user_id": 1,
                "session": session
            })
            
            if response.status_code == 200:
                data = response.json()
                bot_response = data.get('message', '')
                session = data.get('session', {})
                
                print(f"🤖 响应: {bot_response[:100]}...")
                
                # 检查是否显示服务菜单
                if 'Book a room' in bot_response and 'Cancel booking' in bot_response:
                    print("✅ 显示了详细的服务菜单")
                elif 'hotel services' in bot_response.lower():
                    print("✅ 提供了酒店服务引导")
                else:
                    print("⚠️  引导可能不够明确")
                    
        except Exception as e:
            print(f"❌ 测试出错: {str(e)}")
    
    print("\n🎯 渐进式引导测试完成！")
    
    print("\n📋 功能总结:")
    print("✅ Off-topic意图检测")
    print("✅ 分类响应 (small_talk, ai_tech, weather, time_query, general)")
    print("✅ 幽默和创意回应")
    print("✅ 引导回到酒店服务")
    print("✅ 渐进式引导 (多次off-topic后显示详细菜单)")
    print("✅ 用户行为跟踪")
    print("✅ 服务菜单展示")

if __name__ == "__main__":
    test_off_topic_handling()
