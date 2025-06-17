#!/usr/bin/env python3
"""
测试通过API调用的"book another room"功能
"""

import requests
import json

def test_book_another_room_api():
    """测试通过API的book another room功能"""
    
    print("🧪 测试Book Another Room API功能")
    print("=" * 60)
    
    # API端点
    api_url = "http://127.0.0.1:8000/hotel_booking/chatbot/api/"
    
    # 测试数据 - 模拟已有预订的用户
    session_data = {
        'state': 'greeting',
        'user_data': {
            'is_returning_customer': True,
            'guest_name': 'John Doe',
            'email': 'john.doe@example.com',
            'phone': '0123456789'
        }
    }
    
    print("📋 初始会话状态:")
    print(f"状态: {session_data['state']}")
    print(f"用户数据: {session_data['user_data']}")
    print()
    
    # 测试步骤1: 发起"book another room"请求
    print("🔍 步骤1: 发起book another room请求")
    print("-" * 40)
    
    payload1 = {
        "message": "booking another room",
        "session": session_data
    }
    
    try:
        response1 = requests.post(api_url, json=payload1, timeout=10)
        print(f"HTTP状态码: {response1.status_code}")
        
        if response1.status_code == 200:
            data1 = response1.json()
            print(f"🤖 机器人响应:")
            print(f"{data1['message'][:300]}..." if len(data1['message']) > 300 else data1['message'])
            print()
            print(f"📍 新状态: {data1['session'].get('state')}")
            print(f"📝 用户数据: {data1['session'].get('user_data')}")
            
            # 更新会话数据
            session_data = data1['session']
            
            print("✅ 步骤1成功")
        else:
            print(f"❌ 步骤1失败: HTTP {response1.status_code}")
            print(f"响应内容: {response1.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ 步骤1网络错误: {str(e)}")
        return False
    except Exception as e:
        print(f"❌ 步骤1处理错误: {str(e)}")
        return False
    
    print("\n" + "=" * 60)
    
    # 测试步骤2: 选择房间类型
    print("🔍 步骤2: 选择房间类型")
    print("-" * 40)
    
    payload2 = {
        "message": "deluxe room",
        "session": session_data
    }
    
    try:
        response2 = requests.post(api_url, json=payload2, timeout=10)
        print(f"HTTP状态码: {response2.status_code}")
        
        if response2.status_code == 200:
            data2 = response2.json()
            print(f"🤖 机器人响应:")
            print(f"{data2['message'][:300]}..." if len(data2['message']) > 300 else data2['message'])
            print()
            print(f"📍 新状态: {data2['session'].get('state')}")
            print(f"📝 用户数据: {data2['session'].get('user_data')}")
            
            # 检查是否正确进入日期确认状态
            if data2['session'].get('state') == 'confirming_additional_dates':
                print("✅ 步骤2成功 - 正确进入日期确认状态")
                session_data = data2['session']
            else:
                print(f"❌ 步骤2失败 - 状态错误: {data2['session'].get('state')}")
                return False
        else:
            print(f"❌ 步骤2失败: HTTP {response2.status_code}")
            print(f"响应内容: {response2.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ 步骤2网络错误: {str(e)}")
        return False
    except Exception as e:
        print(f"❌ 步骤2处理错误: {str(e)}")
        return False
    
    print("\n" + "=" * 60)
    
    # 测试步骤3: 确认日期
    print("🔍 步骤3: 确认使用相同日期")
    print("-" * 40)
    
    payload3 = {
        "message": "A",
        "session": session_data
    }
    
    try:
        response3 = requests.post(api_url, json=payload3, timeout=10)
        print(f"HTTP状态码: {response3.status_code}")
        
        if response3.status_code == 200:
            data3 = response3.json()
            print(f"🤖 机器人响应:")
            print(f"{data3['message'][:300]}..." if len(data3['message']) > 300 else data3['message'])
            print()
            print(f"📍 新状态: {data3['session'].get('state')}")
            print(f"📝 用户数据: {data3['session'].get('user_data')}")
            
            # 检查是否正确进入最终确认状态
            if data3['session'].get('state') == 'confirming_additional_booking':
                print("✅ 步骤3成功 - 正确进入最终确认状态")
                session_data = data3['session']
            else:
                print(f"❌ 步骤3失败 - 状态错误: {data3['session'].get('state')}")
                return False
        else:
            print(f"❌ 步骤3失败: HTTP {response3.status_code}")
            print(f"响应内容: {response3.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ 步骤3网络错误: {str(e)}")
        return False
    except Exception as e:
        print(f"❌ 步骤3处理错误: {str(e)}")
        return False
    
    print("\n" + "=" * 60)
    
    # 测试步骤4: 最终确认
    print("🔍 步骤4: 最终确认预订")
    print("-" * 40)
    
    payload4 = {
        "message": "confirm",
        "session": session_data
    }
    
    try:
        response4 = requests.post(api_url, json=payload4, timeout=10)
        print(f"HTTP状态码: {response4.status_code}")
        
        if response4.status_code == 200:
            data4 = response4.json()
            print(f"🤖 机器人响应:")
            print(f"{data4['message'][:300]}..." if len(data4['message']) > 300 else data4['message'])
            print()
            print(f"📍 新状态: {data4['session'].get('state')}")
            print(f"📝 用户数据: {data4['session'].get('user_data')}")
            
            # 检查是否成功完成预订
            if "booking has been confirmed" in data4['message'].lower() or "booking id" in data4['message'].lower():
                print("✅ 步骤4成功 - 预订确认完成")
                return True
            else:
                print(f"❌ 步骤4失败 - 未找到预订确认信息")
                return False
        else:
            print(f"❌ 步骤4失败: HTTP {response4.status_code}")
            print(f"响应内容: {response4.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ 步骤4网络错误: {str(e)}")
        return False
    except Exception as e:
        print(f"❌ 步骤4处理错误: {str(e)}")
        return False

def test_simple_api_connection():
    """测试简单的API连接"""
    print("🔍 测试API连接")
    print("-" * 40)
    
    api_url = "http://127.0.0.1:8000/hotel_booking/chatbot/api/"
    
    payload = {
        "message": "hello",
        "session": {}
    }
    
    try:
        response = requests.post(api_url, json=payload, timeout=5)
        print(f"HTTP状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ API连接成功")
            print(f"响应: {data['message'][:100]}...")
            return True
        else:
            print(f"❌ API连接失败: HTTP {response.status_code}")
            print(f"响应: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ 连接错误: 无法连接到服务器")
        print("请确保Django服务器正在运行在 http://127.0.0.1:8000/")
        return False
    except Exception as e:
        print(f"❌ 其他错误: {str(e)}")
        return False

if __name__ == "__main__":
    print("🚀 开始API测试")
    print("=" * 60)
    
    # 首先测试基本连接
    if test_simple_api_connection():
        print("\n" + "=" * 60)
        # 然后测试完整的book another room流程
        success = test_book_another_room_api()
        
        print("\n" + "=" * 60)
        print("📊 最终测试结果")
        if success:
            print("🎉 Book Another Room API测试完全成功！")
        else:
            print("❌ Book Another Room API测试失败")
    else:
        print("\n❌ 无法连接到API，请检查Django服务器是否正在运行")
