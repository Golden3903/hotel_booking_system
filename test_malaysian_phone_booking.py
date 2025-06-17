#!/usr/bin/env python3
"""
测试马来西亚电话号码在实际预订流程中的工作情况
"""

import os
import sys
import django
import requests
import json
import time

# 设置Django环境
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
django.setup()

def test_booking_with_malaysian_phone():
    """测试使用马来西亚电话号码的完整预订流程"""

    base_url = "http://127.0.0.1:8000"
    chatbot_url = f"{base_url}/hotel_booking/chatbot/api/"

    # 创建session来处理CSRF
    session = requests.Session()

    # 获取CSRF token
    try:
        csrf_response = session.get(f"{base_url}/hotel_booking/")
        csrf_token = None
        if 'csrftoken' in session.cookies:
            csrf_token = session.cookies['csrftoken']
        print(f"CSRF Token: {csrf_token}")
    except Exception as e:
        print(f"获取CSRF token失败: {e}")
        return

    # 测试用例：不同的马来西亚电话号码格式
    test_cases = [
        {
            "name": "Ahmad Bin Ali",
            "phone": "012-8833903",
            "email": "ahmad.ali@example.com",
            "description": "马来西亚手机号码 (带连字符)"
        },
        {
            "name": "Siti Nurhaliza",
            "phone": "01158763903",
            "email": "siti.nur@example.com",
            "description": "马来西亚手机号码 (11位无连字符)"
        },
        {
            "name": "Raj Kumar",
            "phone": "+60-13-7654321",
            "email": "raj.kumar@example.com",
            "description": "马来西亚国际格式"
        }
    ]

    print("🧪 测试马来西亚电话号码在预订流程中的使用")
    print("=" * 60)

    for i, test_case in enumerate(test_cases, 1):
        print(f"\n测试 {i}: {test_case['description']}")
        print(f"姓名: {test_case['name']}")
        print(f"电话: {test_case['phone']}")
        print(f"邮箱: {test_case['email']}")
        print("-" * 40)

        try:
            # 开始预订流程
            print("1. 开始预订...")
            headers = {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrf_token
            } if csrf_token else {'Content-Type': 'application/json'}

            response = session.post(chatbot_url, json={
                "message": "I want to book a room",
                "user_id": 1
            }, headers=headers)

            if response.status_code == 200:
                data = response.json()
                print(f"✅ 预订开始: {data.get('response', '')[:100]}...")
            else:
                print(f"❌ 预订开始失败: {response.status_code}")
                continue

            # 提供姓名
            print("2. 提供姓名...")
            response = session.post(chatbot_url, json={
                "message": test_case['name'],
                "user_id": 1
            }, headers=headers)

            if response.status_code == 200:
                data = response.json()
                print(f"✅ 姓名已接受")
            else:
                print(f"❌ 姓名提交失败")
                continue

            # 提供电话号码 (关键测试)
            print(f"3. 提供电话号码: {test_case['phone']}")
            response = session.post(chatbot_url, json={
                "message": test_case['phone'],
                "user_id": 1
            }, headers=headers)

            if response.status_code == 200:
                data = response.json()
                response_text = data.get('response', '')

                # 检查是否要求邮箱 (说明电话号码被正确识别)
                if 'email' in response_text.lower():
                    print(f"✅ 电话号码被正确识别，chatbot要求邮箱")
                else:
                    print(f"❌ 电话号码可能未被识别")
                    print(f"   完整响应: {response_text}")
                    continue
            else:
                print(f"❌ 电话号码提交失败")
                continue

            # 提供邮箱
            print("4. 提供邮箱...")
            response = session.post(chatbot_url, json={
                "message": test_case['email'],
                "user_id": 1
            }, headers=headers)

            if response.status_code == 200:
                data = response.json()
                print(f"✅ 邮箱已接受")
            else:
                print(f"❌ 邮箱提交失败")
                continue

            # 选择房间类型
            print("5. 选择房间类型...")
            response = session.post(chatbot_url, json={
                "message": "Standard Room",
                "user_id": 1
            }, headers=headers)

            if response.status_code == 200:
                data = response.json()
                print(f"✅ 房间类型已选择")
            else:
                print(f"❌ 房间类型选择失败")
                continue

            # 提供入住日期
            print("6. 提供入住日期...")
            response = session.post(chatbot_url, json={
                "message": "2025-07-01",
                "user_id": 1
            }, headers=headers)

            if response.status_code == 200:
                data = response.json()
                print(f"✅ 入住日期已接受")
            else:
                print(f"❌ 入住日期提交失败")
                continue

            # 提供退房日期
            print("7. 提供退房日期...")
            response = session.post(chatbot_url, json={
                "message": "2025-07-03",
                "user_id": 1
            }, headers=headers)

            if response.status_code == 200:
                data = response.json()
                response_text = data.get('response', '')

                # 检查是否显示QR码 (说明预订完成)
                if 'qr' in response_text.lower() or 'payment' in response_text.lower():
                    print(f"✅ 预订完成！显示支付QR码")
                    print(f"🎉 测试成功：马来西亚电话号码 {test_case['phone']} 正常工作")
                else:
                    print(f"⚠️  预订可能未完成: {response_text[:100]}...")
            else:
                print(f"❌ 退房日期提交失败")
                continue

        except Exception as e:
            print(f"❌ 测试过程中出错: {str(e)}")
            continue

        print(f"✅ 测试 {i} 完成\n")
        time.sleep(1)  # 避免请求过快

    print("=" * 60)
    print("🎯 马来西亚电话号码测试完成！")

if __name__ == "__main__":
    test_booking_with_malaysian_phone()
