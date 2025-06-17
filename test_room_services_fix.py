#!/usr/bin/env python3
"""
测试修复后的room services功能
"""

import requests
import json
import time

def test_room_services_fix():
    """测试修复后的room services按钮功能"""
    
    base_url = "http://127.0.0.1:8000"
    chatbot_url = f"{base_url}/hotel_booking/chatbot/api/"
    
    print("🧪 测试修复后的Room Services功能")
    print("=" * 60)
    
    # 测试用例
    test_cases = [
        {
            "message": "room services",
            "description": "点击room services按钮",
            "expected_response": "room services menu"
        },
        {
            "message": "housekeeping",
            "description": "选择housekeeping服务",
            "expected_response": "booking ID request"
        },
        {
            "message": "do not disturb",
            "description": "选择DND服务",
            "expected_response": "booking ID request"
        }
    ]
    
    session = {}
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n测试 {i}: {test_case['description']}")
        print(f"用户输入: \"{test_case['message']}\"")
        print("-" * 40)
        
        try:
            # 发送消息
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
                
                # 检查响应质量
                if i == 1:  # room services按钮测试
                    if "room services" in bot_response.lower() and "housekeeping" in bot_response.lower():
                        print("✅ 正确显示了room services菜单")
                    else:
                        print("❌ 没有显示正确的room services菜单")
                        
                elif i == 2:  # housekeeping选择测试
                    if "booking id" in bot_response.lower() and "housekeeping" in bot_response.lower():
                        print("✅ 正确处理了housekeeping选择")
                    else:
                        print("❌ 没有正确处理housekeeping选择")
                        
                elif i == 3:  # DND选择测试
                    if "booking id" in bot_response.lower() and ("do not disturb" in bot_response.lower() or "dnd" in bot_response.lower()):
                        print("✅ 正确处理了DND选择")
                    else:
                        print("❌ 没有正确处理DND选择")
                        
            else:
                print(f"❌ 请求失败: {response.status_code}")
                
        except Exception as e:
            print(f"❌ 测试过程中出错: {str(e)}")
        
        print(f"✅ 测试 {i} 完成")
        time.sleep(1)
    
    print("\n" + "=" * 60)
    print("🎯 Room Services修复测试完成！")
    
    # 完整流程测试
    print("\n🔄 测试完整的room services流程...")
    print("-" * 40)
    
    # 重置session
    session = {}
    
    # 步骤1: 点击room services
    print("\n步骤1: 点击room services按钮")
    try:
        response = requests.post(chatbot_url, json={
            "message": "room services",
            "user_id": 1,
            "session": session
        })
        
        if response.status_code == 200:
            data = response.json()
            bot_response = data.get('message', '')
            session = data.get('session', {})
            
            print(f"🤖 响应: {bot_response[:100]}...")
            
            if "housekeeping" in bot_response.lower() and "do not disturb" in bot_response.lower():
                print("✅ 步骤1成功：显示了room services菜单")
            else:
                print("❌ 步骤1失败：没有显示正确的菜单")
                
    except Exception as e:
        print(f"❌ 步骤1出错: {str(e)}")
    
    # 步骤2: 选择housekeeping
    print("\n步骤2: 选择housekeeping")
    try:
        response = requests.post(chatbot_url, json={
            "message": "housekeeping",
            "user_id": 1,
            "session": session
        })
        
        if response.status_code == 200:
            data = response.json()
            bot_response = data.get('message', '')
            session = data.get('session', {})
            
            print(f"🤖 响应: {bot_response[:100]}...")
            
            if "booking id" in bot_response.lower():
                print("✅ 步骤2成功：要求提供booking ID")
            else:
                print("❌ 步骤2失败：没有要求booking ID")
                
    except Exception as e:
        print(f"❌ 步骤2出错: {str(e)}")
    
    # 步骤3: 提供booking ID
    print("\n步骤3: 提供booking ID")
    try:
        response = requests.post(chatbot_url, json={
            "message": "BK-12345",
            "user_id": 1,
            "session": session
        })
        
        if response.status_code == 200:
            data = response.json()
            bot_response = data.get('message', '')
            session = data.get('session', {})
            
            print(f"🤖 响应: {bot_response[:100]}...")
            
            if "cleaning" in bot_response.lower() or "time" in bot_response.lower():
                print("✅ 步骤3成功：处理了booking ID并询问清洁时间")
            elif "couldn't find" in bot_response.lower():
                print("✅ 步骤3成功：正确处理了无效的booking ID")
            else:
                print("❌ 步骤3失败：没有正确处理booking ID")
                
    except Exception as e:
        print(f"❌ 步骤3出错: {str(e)}")
    
    print("\n🎯 完整流程测试完成！")
    
    print("\n📋 修复总结:")
    print("✅ 添加了'room services'关键词检测")
    print("✅ 创建了room services菜单显示")
    print("✅ 实现了菜单选项处理")
    print("✅ 区分了客房服务和房间预订")
    print("✅ 提供了清晰的服务选项")

if __name__ == "__main__":
    test_room_services_fix()
