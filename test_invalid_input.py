#!/usr/bin/env python3
"""
测试无效输入识别功能
"""

import requests
import time

def test_invalid_input_detection():
    """测试无效输入识别和引导功能"""
    
    base_url = "http://127.0.0.1:8000"
    chatbot_url = f"{base_url}/hotel_booking/chatbot/api/"
    
    print("🧪 测试无效输入识别功能")
    print("=" * 60)
    
    # 无效输入测试用例
    test_cases = [
        {
            "input": "ksdbvjdbvjbsjbvd",
            "description": "随机字母序列",
            "type": "random_letters"
        },
        {
            "input": "asdfasdf",
            "description": "键盘连击",
            "type": "keyboard_mashing"
        },
        {
            "input": "123@@@",
            "description": "数字+特殊字符",
            "type": "mixed_random"
        },
        {
            "input": "qwertyuiop",
            "description": "键盘第一行",
            "type": "keyboard_pattern"
        },
        {
            "input": "aaaaaaaaaa",
            "description": "重复字符",
            "type": "repetitive"
        },
        {
            "input": "12345678901234567890",
            "description": "长数字序列",
            "type": "long_digits"
        },
        {
            "input": "!@#$%^&*()",
            "description": "特殊字符序列",
            "type": "special_chars"
        },
        {
            "input": "zxcvbnm",
            "description": "键盘底行",
            "type": "keyboard_pattern"
        },
        {
            "input": "hjklmnbvcxz",
            "description": "随机键盘字符",
            "type": "random_keyboard"
        },
        {
            "input": "dfghjklqwerty",
            "description": "混合键盘模式",
            "type": "mixed_keyboard"
        },
        {
            "input": "111111111",
            "description": "重复数字",
            "type": "repetitive_digits"
        },
        {
            "input": "@@@@@@@@",
            "description": "重复特殊字符",
            "type": "repetitive_special"
        },
        {
            "input": "bcdfghjklmnp",
            "description": "无元音字母序列",
            "type": "no_vowels"
        },
        {
            "input": "mnbvcxzlkjhgfdsa",
            "description": "反向键盘序列",
            "type": "reverse_keyboard"
        },
        {
            "input": "xyz123!@#",
            "description": "混合随机内容",
            "type": "mixed_random"
        }
    ]
    
    # 有效输入对比测试
    valid_test_cases = [
        {
            "input": "hello",
            "description": "正常问候",
            "type": "valid_greeting"
        },
        {
            "input": "book a room",
            "description": "预订请求",
            "type": "valid_booking"
        },
        {
            "input": "what time is check-in?",
            "description": "信息查询",
            "type": "valid_info"
        }
    ]
    
    invalid_detected = 0
    total_invalid = len(test_cases)
    
    print("\n🔍 测试无效输入识别:")
    print("-" * 40)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n测试 {i}/{total_invalid}: {test_case['type']}")
        print(f"输入: \"{test_case['input']}\"")
        print(f"描述: {test_case['description']}")
        print("-" * 30)
        
        try:
            # 发送消息
            response = requests.post(chatbot_url, json={
                "message": test_case['input'],
                "user_id": 1,
                "session": {}
            })
            
            if response.status_code == 200:
                data = response.json()
                bot_response = data.get('message', '')
                
                print(f"🤖 Chatbot响应:")
                print(f"{bot_response}")
                
                # 检查是否正确识别为无效输入
                invalid_indicators = [
                    "doesn't look like very relevant content",
                    "not sure what you're trying to say",
                    "seems like random input",
                    "这看起来不太像相关内容",
                    "我不太确定您想表达什么",
                    "这看起来像是随机输入",
                    "I can help you with these services",
                    "我可以帮您处理以下服务"
                ]
                
                is_invalid_detected = any(indicator in bot_response for indicator in invalid_indicators)
                
                if is_invalid_detected:
                    print("✅ 正确识别为无效输入")
                    invalid_detected += 1
                else:
                    print("❌ 未能识别为无效输入")
                    
            else:
                print(f"❌ 请求失败: {response.status_code}")
                
        except Exception as e:
            print(f"❌ 测试过程中出错: {str(e)}")
        
        time.sleep(0.3)  # 避免请求过快
    
    print("\n" + "=" * 60)
    print("🎯 无效输入识别测试结果")
    print(f"总无效输入测试: {total_invalid}")
    print(f"正确识别: {invalid_detected}")
    print(f"识别准确率: {(invalid_detected/total_invalid)*100:.1f}%")
    
    # 测试有效输入不被误判
    print("\n🔍 测试有效输入不被误判:")
    print("-" * 40)
    
    valid_preserved = 0
    total_valid = len(valid_test_cases)
    
    for i, test_case in enumerate(valid_test_cases, 1):
        print(f"\n有效输入测试 {i}/{total_valid}: {test_case['type']}")
        print(f"输入: \"{test_case['input']}\"")
        print(f"描述: {test_case['description']}")
        print("-" * 30)
        
        try:
            response = requests.post(chatbot_url, json={
                "message": test_case['input'],
                "user_id": 1,
                "session": {}
            })
            
            if response.status_code == 200:
                data = response.json()
                bot_response = data.get('message', '')
                
                print(f"🤖 Chatbot响应:")
                print(f"{bot_response}")
                
                # 检查是否被误判为无效输入
                invalid_indicators = [
                    "doesn't look like very relevant content",
                    "not sure what you're trying to say",
                    "seems like random input",
                    "这看起来不太像相关内容",
                    "我不太确定您想表达什么",
                    "这看起来像是随机输入"
                ]
                
                is_wrongly_flagged = any(indicator in bot_response for indicator in invalid_indicators)
                
                if not is_wrongly_flagged:
                    print("✅ 正确识别为有效输入")
                    valid_preserved += 1
                else:
                    print("❌ 被误判为无效输入")
                    
        except Exception as e:
            print(f"❌ 测试过程中出错: {str(e)}")
        
        time.sleep(0.3)
    
    print("\n" + "=" * 60)
    print("📊 最终测试结果总结")
    print(f"无效输入识别准确率: {(invalid_detected/total_invalid)*100:.1f}% ({invalid_detected}/{total_invalid})")
    print(f"有效输入保护率: {(valid_preserved/total_valid)*100:.1f}% ({valid_preserved}/{total_valid})")
    
    overall_accuracy = ((invalid_detected + valid_preserved) / (total_invalid + total_valid)) * 100
    print(f"总体准确率: {overall_accuracy:.1f}%")
    
    if overall_accuracy >= 90:
        print("🎉 测试优秀！无效输入识别功能表现出色")
    elif overall_accuracy >= 75:
        print("✅ 测试良好，功能基本可用")
    else:
        print("⚠️ 测试需要改进，识别准确率偏低")

if __name__ == "__main__":
    test_invalid_input_detection()
