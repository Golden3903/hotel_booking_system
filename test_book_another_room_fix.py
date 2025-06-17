#!/usr/bin/env python3
"""
测试修复后的"book another room"功能
"""

import os
import sys
import django

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
django.setup()

from hotel_booking.chatbot.dialog_manager import DialogManager

def test_book_another_room_flow():
    """测试完整的book another room流程"""
    
    print("🧪 测试修复后的Book Another Room功能")
    print("=" * 60)
    
    # 创建对话管理器实例
    dialog_manager = DialogManager()
    
    # 模拟用户数据，假设已经有一个现有预订
    dialog_manager.user_data = {
        'parent_booking': {
            'id': 1,
            'booking_id': 'BK-12345',
            'guest_name': 'John Doe',
            'room_name': 'Suite',
            'check_in_date': '2025-06-15',
            'check_out_date': '2025-06-18'
        },
        'is_additional_booking': True
    }
    
    # 设置状态为选择额外房间类型
    dialog_manager.state = "selecting_additional_room_type"
    
    print("📋 初始状态设置:")
    print(f"状态: {dialog_manager.state}")
    print(f"用户数据: {dialog_manager.user_data}")
    print()
    
    # 测试用例
    test_cases = [
        {
            "input": "deluxe room",
            "description": "选择豪华房间",
            "expected_state": "confirming_additional_dates",
            "should_contain": ["Great! You've selected", "Deluxe Room", "same check-in and check-out dates"]
        },
        {
            "input": "B",
            "description": "通过字母选择房间",
            "expected_state": "confirming_additional_dates", 
            "should_contain": ["Great! You've selected", "same check-in and check-out dates"]
        },
        {
            "input": "standard",
            "description": "选择标准房间",
            "expected_state": "confirming_additional_dates",
            "should_contain": ["Great! You've selected", "Standard Room", "same check-in and check-out dates"]
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"🔍 测试 {i}: {test_case['description']}")
        print(f"输入: \"{test_case['input']}\"")
        print("-" * 40)
        
        # 重置状态为选择额外房间类型
        dialog_manager.state = "selecting_additional_room_type"
        dialog_manager.user_data = {
            'parent_booking': {
                'id': 1,
                'booking_id': 'BK-12345',
                'guest_name': 'John Doe',
                'room_name': 'Suite',
                'check_in_date': '2025-06-15',
                'check_out_date': '2025-06-18'
            },
            'is_additional_booking': True
        }
        
        try:
            # 处理用户输入
            response = dialog_manager.respond(test_case['input'])
            
            print(f"🤖 机器人响应:")
            print(f"{response[:300]}..." if len(response) > 300 else response)
            print()
            print(f"📍 新状态: {dialog_manager.state}")
            print(f"📝 用户数据: {dialog_manager.user_data}")
            print()
            
            # 验证结果
            success = True
            
            # 检查状态是否正确
            if dialog_manager.state != test_case['expected_state']:
                print(f"❌ 状态错误: 期望 '{test_case['expected_state']}', 实际 '{dialog_manager.state}'")
                success = False
            
            # 检查响应内容
            for expected_text in test_case['should_contain']:
                if expected_text not in response:
                    print(f"❌ 响应缺少期望内容: '{expected_text}'")
                    success = False
            
            # 检查是否错误地开始了新的预订流程
            if "May I have your name please?" in response:
                print("❌ 错误地开始了新的预订流程")
                success = False
            
            if success:
                print("✅ 测试通过")
            else:
                print("❌ 测试失败")
                
        except Exception as e:
            print(f"❌ 测试过程中出错: {str(e)}")
            import traceback
            traceback.print_exc()
        
        print("=" * 60)
    
    # 测试完整流程
    print("\n🔄 测试完整的额外房间预订流程:")
    print("=" * 60)
    
    # 重置状态
    dialog_manager.state = "selecting_additional_room_type"
    dialog_manager.user_data = {
        'parent_booking': {
            'id': 1,
            'booking_id': 'BK-12345',
            'guest_name': 'John Doe',
            'room_name': 'Suite',
            'check_in_date': '2025-06-15',
            'check_out_date': '2025-06-18'
        },
        'is_additional_booking': True
    }
    
    # 步骤1: 选择房间类型
    print("步骤1: 选择房间类型")
    response1 = dialog_manager.respond("deluxe room")
    print(f"响应: {response1[:200]}...")
    print(f"状态: {dialog_manager.state}")
    print()
    
    # 步骤2: 确认日期
    print("步骤2: 确认使用相同日期")
    response2 = dialog_manager.respond("A")
    print(f"响应: {response2[:200]}...")
    print(f"状态: {dialog_manager.state}")
    print()
    
    # 步骤3: 最终确认
    print("步骤3: 最终确认预订")
    response3 = dialog_manager.respond("confirm")
    print(f"响应: {response3[:200]}...")
    print(f"状态: {dialog_manager.state}")
    print()
    
    print("🎉 完整流程测试完成!")

if __name__ == "__main__":
    test_book_another_room_flow()
