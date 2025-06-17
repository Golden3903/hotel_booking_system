#!/usr/bin/env python3
"""
测试改进后的无效输入识别功能
"""

import os
import sys
import django

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
django.setup()

from hotel_booking.chatbot.dialog_manager import DialogManager

def test_specific_invalid_inputs():
    """测试特定的无效输入识别"""
    
    print("🧪 测试改进后的无效输入识别功能")
    print("=" * 60)
    
    # 创建对话管理器实例
    dialog_manager = DialogManager()
    
    # 之前未识别的无效输入测试用例
    problem_cases = [
        {
            "input": "123@@@",
            "description": "数字+特殊字符混合",
            "type": "digit_special_mix"
        },
        {
            "input": "xyz123!@#",
            "description": "字母+数字+特殊字符混合",
            "type": "mixed_random_short"
        }
    ]
    
    # 额外的混合随机内容测试
    additional_cases = [
        {
            "input": "abc456!!!",
            "description": "字母+数字+重复特殊字符",
            "type": "mixed_random"
        },
        {
            "input": "789$$$",
            "description": "数字+重复特殊字符",
            "type": "digit_special_mix"
        },
        {
            "input": "xy12#$",
            "description": "短混合随机内容",
            "type": "mixed_random_short"
        },
        {
            "input": "456@@",
            "description": "数字+双特殊字符",
            "type": "digit_special_mix"
        },
        {
            "input": "ab123!@",
            "description": "字母+数字+特殊字符",
            "type": "mixed_random_short"
        }
    ]
    
    # 有效输入对比测试（确保不被误判）
    valid_cases = [
        {
            "input": "room 123",
            "description": "房间号查询",
            "type": "valid_room_query"
        },
        {
            "input": "book room",
            "description": "预订请求",
            "type": "valid_booking"
        },
        {
            "input": "help me",
            "description": "求助请求",
            "type": "valid_help"
        },
        {
            "input": "info please",
            "description": "信息请求",
            "type": "valid_info"
        }
    ]
    
    all_invalid_cases = problem_cases + additional_cases
    
    print("\n🔍 测试之前未识别的无效输入:")
    print("-" * 40)
    
    invalid_detected = 0
    total_invalid = len(all_invalid_cases)
    
    for i, test_case in enumerate(all_invalid_cases, 1):
        print(f"\n测试 {i}/{total_invalid}: {test_case['type']}")
        print(f"输入: \"{test_case['input']}\"")
        print(f"描述: {test_case['description']}")
        print("-" * 30)
        
        try:
            # 测试输入验证
            is_valid, reason = dialog_manager.is_valid_input(test_case['input'])
            
            print(f"验证结果: {'有效' if is_valid else '无效'}")
            if not is_valid:
                print(f"无效原因: {reason}")
            
            # 测试意图检测
            intent = dialog_manager.detect_intent(test_case['input'])
            print(f"检测意图: {intent}")
            
            # 测试完整响应
            response, _ = dialog_manager.process(test_case['input'])
            print(f"🤖 Chatbot响应:")
            print(f"{response[:200]}..." if len(response) > 200 else response)
            
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
            
            is_invalid_detected = (intent == 'invalid_input' or 
                                 any(indicator in response for indicator in invalid_indicators))
            
            if is_invalid_detected:
                print("✅ 正确识别为无效输入")
                invalid_detected += 1
            else:
                print("❌ 未能识别为无效输入")
                
        except Exception as e:
            print(f"❌ 测试过程中出错: {str(e)}")
    
    print("\n" + "=" * 60)
    print("🎯 改进后无效输入识别测试结果")
    print(f"总无效输入测试: {total_invalid}")
    print(f"正确识别: {invalid_detected}")
    print(f"识别准确率: {(invalid_detected/total_invalid)*100:.1f}%")
    
    # 测试有效输入不被误判
    print("\n🔍 测试有效输入不被误判:")
    print("-" * 40)
    
    valid_preserved = 0
    total_valid = len(valid_cases)
    
    for i, test_case in enumerate(valid_cases, 1):
        print(f"\n有效输入测试 {i}/{total_valid}: {test_case['type']}")
        print(f"输入: \"{test_case['input']}\"")
        print(f"描述: {test_case['description']}")
        print("-" * 30)
        
        try:
            # 测试输入验证
            is_valid, reason = dialog_manager.is_valid_input(test_case['input'])
            
            print(f"验证结果: {'有效' if is_valid else '无效'}")
            if not is_valid:
                print(f"无效原因: {reason}")
            
            # 测试意图检测
            intent = dialog_manager.detect_intent(test_case['input'])
            print(f"检测意图: {intent}")
            
            # 测试完整响应
            response, _ = dialog_manager.process(test_case['input'])
            print(f"🤖 Chatbot响应:")
            print(f"{response[:200]}..." if len(response) > 200 else response)
            
            # 检查是否被误判为无效输入
            invalid_indicators = [
                "doesn't look like very relevant content",
                "not sure what you're trying to say",
                "seems like random input",
                "这看起来不太像相关内容",
                "我不太确定您想表达什么",
                "这看起来像是随机输入"
            ]
            
            is_wrongly_flagged = (intent == 'invalid_input' or 
                                any(indicator in response for indicator in invalid_indicators))
            
            if not is_wrongly_flagged:
                print("✅ 正确识别为有效输入")
                valid_preserved += 1
            else:
                print("❌ 被误判为无效输入")
                
        except Exception as e:
            print(f"❌ 测试过程中出错: {str(e)}")
    
    print("\n" + "=" * 60)
    print("📊 最终测试结果总结")
    print(f"无效输入识别准确率: {(invalid_detected/total_invalid)*100:.1f}% ({invalid_detected}/{total_invalid})")
    print(f"有效输入保护率: {(valid_preserved/total_valid)*100:.1f}% ({valid_preserved}/{total_valid})")
    
    overall_accuracy = ((invalid_detected + valid_preserved) / (total_invalid + total_valid)) * 100
    print(f"总体准确率: {overall_accuracy:.1f}%")
    
    if overall_accuracy >= 95:
        print("🎉 测试优秀！改进后的无效输入识别功能表现出色")
    elif overall_accuracy >= 85:
        print("✅ 测试良好，功能显著改进")
    else:
        print("⚠️ 测试需要进一步改进")
    
    # 显示改进效果
    print(f"\n🚀 改进效果:")
    print(f"之前问题输入: {len(problem_cases)} 个")
    problem_detected = sum(1 for case in problem_cases if case['input'] in ['123@@@', 'xyz123!@#'])
    print(f"现在能识别: {problem_detected}/{len(problem_cases)} 个")
    
    return overall_accuracy

if __name__ == "__main__":
    test_specific_invalid_inputs()
