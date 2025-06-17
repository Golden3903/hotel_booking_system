#!/usr/bin/env python3
"""
调试chatbot API
"""

import requests
import json

def debug_chatbot():
    """调试chatbot API"""
    
    base_url = "http://127.0.0.1:8000"
    
    print("🔍 调试chatbot API")
    print("=" * 40)
    
    # 测试不同的URL
    urls_to_test = [
        f"{base_url}/hotel_booking/chatbot/api/",
        f"{base_url}/hotel_booking/chatbot/",
    ]
    
    for url in urls_to_test:
        print(f"\n测试URL: {url}")
        try:
            # 先测试GET请求
            print("  GET请求...")
            response = requests.get(url)
            print(f"  状态码: {response.status_code}")
            if response.status_code != 404:
                print(f"  响应: {response.text[:100]}...")
            
            # 再测试POST请求
            print("  POST请求...")
            response = requests.post(url, json={
                "message": "hello",
                "user_id": 1
            })
            print(f"  状态码: {response.status_code}")
            print(f"  响应: {response.text[:200]}...")
            
        except Exception as e:
            print(f"  错误: {e}")
    
    print("\n" + "=" * 40)
    print("🎯 调试完成！")

if __name__ == "__main__":
    debug_chatbot()
