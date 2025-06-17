#!/usr/bin/env python3
"""
简单测试chatbot API
"""

import requests
import json

def test_simple_chatbot():
    """简单测试chatbot API"""
    
    base_url = "http://127.0.0.1:8000"
    chatbot_url = f"{base_url}/hotel_booking/chatbot/api/"
    
    print("🧪 简单测试chatbot API")
    print("=" * 40)
    
    # 测试1: 开始预订
    print("1. 测试开始预订...")
    try:
        response = requests.post(chatbot_url, json={
            "message": "I want to book a room",
            "user_id": 1
        })
        
        print(f"状态码: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"响应: {data.get('response', '')}")
            session = data.get('session', {})
            print(f"Session状态: {session.get('state', '')}")
        else:
            print(f"错误: {response.text}")
            return
            
    except Exception as e:
        print(f"请求失败: {e}")
        return
    
    # 测试2: 提供姓名
    print("\n2. 测试提供姓名...")
    try:
        response = requests.post(chatbot_url, json={
            "message": "John Smith",
            "user_id": 1,
            "session": session
        })
        
        print(f"状态码: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"响应: {data.get('response', '')}")
            session = data.get('session', {})
            print(f"Session状态: {session.get('state', '')}")
        else:
            print(f"错误: {response.text}")
            return
            
    except Exception as e:
        print(f"请求失败: {e}")
        return
    
    # 测试3: 提供马来西亚电话号码
    print("\n3. 测试提供马来西亚电话号码...")
    try:
        response = requests.post(chatbot_url, json={
            "message": "012-8833903",
            "user_id": 1,
            "session": session
        })
        
        print(f"状态码: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            response_text = data.get('response', '')
            print(f"响应: {response_text}")
            session = data.get('session', {})
            print(f"Session状态: {session.get('state', '')}")
            
            # 检查是否要求邮箱
            if 'email' in response_text.lower():
                print("✅ 电话号码被正确识别！")
            else:
                print("❌ 电话号码可能未被识别")
        else:
            print(f"错误: {response.text}")
            
    except Exception as e:
        print(f"请求失败: {e}")
    
    print("\n" + "=" * 40)
    print("🎯 测试完成！")

if __name__ == "__main__":
    test_simple_chatbot()
