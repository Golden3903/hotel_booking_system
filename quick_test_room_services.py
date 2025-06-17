#!/usr/bin/env python3
"""
快速测试room services功能
"""

import requests
import json

def test_room_services():
    """快速测试room services按钮功能"""

    base_url = "http://127.0.0.1:8000"
    chatbot_url = f"{base_url}/hotel_booking/chatbot/api/"

    print("🧪 快速测试Room Services功能")
    print("=" * 50)

    # 测试1: 点击room services按钮
    print("\n测试1: 点击room services按钮")
    try:
        response = requests.post(chatbot_url, json={
            "message": "room services",
            "user_id": 1,
            "session": {}
        })

        if response.status_code == 200:
            data = response.json()
            bot_response = data.get('message', '')

            print(f"🤖 响应: {bot_response}")

            if "housekeeping" in bot_response.lower() and "do not disturb" in bot_response.lower():
                print("✅ 成功显示room services菜单")
            else:
                print("❌ 没有显示正确的room services菜单")

        else:
            print(f"❌ 请求失败: {response.status_code}")

    except Exception as e:
        print(f"❌ 测试出错: {str(e)}")

    # 测试2: 选择housekeeping
    print("\n测试2: 选择housekeeping")
    try:
        response = requests.post(chatbot_url, json={
            "message": "housekeeping",
            "user_id": 1,
            "session": {
                "user_data": {"showing_room_service_menu": True},
                "state": "greeting",
                "lang": "en"
            }
        })

        if response.status_code == 200:
            data = response.json()
            bot_response = data.get('message', '')

            print(f"🤖 响应: {bot_response}")

            if "booking id" in bot_response.lower() and "housekeeping" in bot_response.lower():
                print("✅ 成功处理housekeeping选择")
            else:
                print("❌ 没有正确处理housekeeping选择")

        else:
            print(f"❌ 请求失败: {response.status_code}")

    except Exception as e:
        print(f"❌ 测试出错: {str(e)}")

    # 测试3: 选择DND
    print("\n测试3: 选择Do Not Disturb")
    try:
        response = requests.post(chatbot_url, json={
            "message": "do not disturb",
            "user_id": 1,
            "session": {
                "user_data": {"showing_room_service_menu": True},
                "state": "greeting",
                "lang": "en"
            }
        })

        if response.status_code == 200:
            data = response.json()
            bot_response = data.get('message', '')

            print(f"🤖 响应: {bot_response}")

            if "booking id" in bot_response.lower() and ("do not disturb" in bot_response.lower() or "dnd" in bot_response.lower()):
                print("✅ 成功处理DND选择")
            else:
                print("❌ 没有正确处理DND选择")

        else:
            print(f"❌ 请求失败: {response.status_code}")

    except Exception as e:
        print(f"❌ 测试出错: {str(e)}")

    print("\n🎯 Room Services功能测试完成！")
    print("\n📋 修复总结:")
    print("✅ 添加了'room services'关键词检测")
    print("✅ 创建了room services菜单显示")
    print("✅ 实现了菜单选项处理")
    print("✅ 区分了客房服务和房间预订")
    print("✅ 提供了清晰的服务选项")

if __name__ == "__main__":
    test_room_services()
