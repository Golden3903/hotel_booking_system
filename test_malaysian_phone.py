#!/usr/bin/env python3
"""
测试马来西亚电话号码格式识别
"""

import os
import sys
import django

# 设置Django环境
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
django.setup()

from hotel_booking.chatbot.dialog_manager import DialogManager

def test_phone_extraction():
    """测试各种马来西亚电话号码格式"""

    # 创建dialog manager实例
    dialog_manager = DialogManager()

    # 测试用例：各种马来西亚电话号码格式
    test_cases = [
        # 马来西亚手机号码 (10位)
        "0128833903",
        "012-8833903",
        "012 8833903",

        # 马来西亚手机号码 (11位)
        "01158763903",
        "011-58763903",
        "011 58763903",

        # 其他马来西亚手机号码前缀
        "0138833903",
        "013-8833903",
        "0148833903",
        "014-8833903",
        "0158833903",
        "015-8833903",
        "0168833903",
        "016-8833903",
        "0178833903",
        "017-8833903",
        "0188833903",
        "018-8833903",
        "0198833903",
        "019-8833903",

        # 马来西亚固定电话
        "0312345678",
        "03-12345678",
        "03 12345678",
        "041234567",
        "04-1234567",
        "04 1234567",

        # 美国格式 (保持兼容)
        "555-987-6543",
        "555 987 6543",

        # 国际格式
        "+60-12-8833903",
        "+60 12 8833903",
    ]

    print("🧪 测试马来西亚电话号码格式识别")
    print("=" * 50)

    success_count = 0
    total_count = len(test_cases)

    for i, phone_number in enumerate(test_cases, 1):
        print(f"\n测试 {i:2d}: {phone_number}")

        # 测试独立电话号码提取
        result = dialog_manager.extract_booking_info(phone_number, {})

        if 'phone' in result:
            print(f"✅ 成功提取: {result['phone']}")
            success_count += 1
        else:
            print(f"❌ 提取失败")

        # 测试带前缀的电话号码提取
        prefixed_input = f"My phone number is {phone_number}"
        result_prefixed = dialog_manager.extract_booking_info(prefixed_input, {})

        if 'phone' in result_prefixed:
            print(f"✅ 带前缀成功: {result_prefixed['phone']}")
        else:
            print(f"❌ 带前缀失败")

    print("\n" + "=" * 50)
    print(f"📊 测试结果: {success_count}/{total_count} 成功")
    print(f"📈 成功率: {(success_count/total_count)*100:.1f}%")

    if success_count == total_count:
        print("🎉 所有测试通过！")
    else:
        print("⚠️  部分测试失败，需要进一步优化")

if __name__ == "__main__":
    test_phone_extraction()
