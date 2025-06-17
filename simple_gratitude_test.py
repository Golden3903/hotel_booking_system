#!/usr/bin/env python3
"""
简单的感谢意图测试
"""

import os
import sys
import django

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
django.setup()

from hotel_booking.chatbot.dialog_manager import DialogManager

def test_gratitude_detection():
    """测试感谢意图检测"""
    
    print("🧪 测试感谢意图检测")
    print("=" * 50)
    
    # 创建对话管理器实例
    dialog_manager = DialogManager()
    
    # 测试感谢表达
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
        "thanks for the help"
    ]
    
    success_count = 0
    
    for expression in gratitude_expressions:
        try:
            detected_intent = dialog_manager.detect_intent(expression)
            
            if detected_intent == 'express_gratitude':
                print(f"✅ '{expression}' -> 正确识别为感谢意图")
                success_count += 1
            else:
                print(f"❌ '{expression}' -> 识别为: {detected_intent}")
                
        except Exception as e:
            print(f"❌ '{expression}' -> 错误: {str(e)}")
    
    print(f"\n📊 检测成功率: {success_count}/{len(gratitude_expressions)} ({(success_count/len(gratitude_expressions))*100:.1f}%)")
    
    return success_count == len(gratitude_expressions)

def test_gratitude_response():
    """测试感谢回应生成"""
    
    print("\n🧪 测试感谢回应生成")
    print("=" * 50)
    
    # 创建对话管理器实例
    dialog_manager = DialogManager()
    
    # 测试不同上下文的感谢回应
    test_cases = [
        {
            "name": "预订完成后",
            "state": "booking_confirmed",
            "user_data": {"booking_id": "BK-12345"}
        },
        {
            "name": "一般对话",
            "state": "greeting", 
            "user_data": {}
        },
        {
            "name": "查看预订后",
            "state": "greeting",
            "user_data": {"last_viewed_booking": {"booking_id": "BK-67890"}}
        }
    ]
    
    for case in test_cases:
        print(f"\n🔍 测试场景: {case['name']}")
        print("-" * 30)
        
        try:
            # 设置对话管理器状态
            dialog_manager.state = case['state']
            dialog_manager.user_data = case['user_data']
            
            # 生成感谢回应
            response = dialog_manager.handle_gratitude_intent("thank you")
            
            print(f"📝 回应: {response[:150]}...")
            
            # 检查回应是否合理
            if "welcome" in response.lower() or "pleasure" in response.lower() or "happy" in response.lower():
                print("✅ 回应包含感谢回复关键词")
            else:
                print("⚠️ 回应可能不够礼貌")
                
        except Exception as e:
            print(f"❌ 错误: {str(e)}")

if __name__ == "__main__":
    print("🚀 开始简单感谢意图测试")
    
    # 测试意图检测
    detection_success = test_gratitude_detection()
    
    # 测试回应生成
    test_gratitude_response()
    
    print("\n" + "=" * 50)
    print("🏁 测试完成")
    
    if detection_success:
        print("🎉 感谢意图功能基本实现成功！")
    else:
        print("❌ 感谢意图检测需要调试")
