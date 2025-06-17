#!/usr/bin/env python3
"""
测试增强的off-topic意图识别功能
"""

import requests
import json
import time

def test_enhanced_off_topic():
    """测试增强的off-topic意图识别和引导功能"""

    base_url = "http://127.0.0.1:8000"
    chatbot_url = f"{base_url}/hotel_booking/chatbot/api/"

    print("🧪 测试增强的Off-Topic意图识别功能")
    print("=" * 60)

    # 测试用例 - 各种off-topic查询（基于你提供的实际例子）
    test_cases = [
        {
            "message": "你是用什么程序写的？",
            "category": "AI/Programming",
            "description": "编程技术问题"
        },
        {
            "message": "你玩游戏吗？",
            "category": "Entertainment/Gaming",
            "description": "游戏娱乐问题"
        },
        {
            "message": "你有兄弟姐妹吗？",
            "category": "Personal/Family",
            "description": "家庭个人问题"
        },
        {
            "message": "你能帮我写作业吗？",
            "category": "Education/Homework",
            "description": "学习作业问题"
        },
        {
            "message": "谁是你的老板？",
            "category": "Personal/Work",
            "description": "工作关系问题"
        },
        {
            "message": "你觉得人类会被AI取代吗？",
            "category": "AI/Future",
            "description": "AI未来问题"
        },
        {
            "message": "马来西亚独立日是哪一天？",
            "category": "General Knowledge",
            "description": "常识问题"
        },
        {
            "message": "你相信命运吗？",
            "category": "Philosophy/Belief",
            "description": "哲学信念问题"
        },
        {
            "message": "你有没有宠物？",
            "category": "Personal/Pets",
            "description": "宠物个人问题"
        },
        {
            "message": "你喜欢海边还是山上？",
            "category": "Personal/Preference",
            "description": "个人偏好问题"
        },
        {
            "message": "我觉得你很可爱",
            "category": "Personal/Compliment",
            "description": "个人赞美"
        },
        {
            "message": "你能告诉我乐透号码吗？",
            "category": "Random/Lottery",
            "description": "随机彩票问题"
        },
        {
            "message": "你支不支持某某政党？",
            "category": "Politics",
            "description": "政治立场问题"
        },
        {
            "message": "你喜欢看什么电影？",
            "category": "Entertainment/Movies",
            "description": "电影娱乐问题"
        },
        {
            "message": "你可以唱歌吗？",
            "category": "Entertainment/Music",
            "description": "音乐娱乐问题"
        },
        {
            "message": "你怎么看AI监管问题？",
            "category": "AI/Regulation",
            "description": "AI监管问题"
        },
        {
            "message": "你知道谁发明了电灯吗？",
            "category": "General Knowledge/History",
            "description": "历史常识问题"
        },
        {
            "message": "你觉得哪家手机最好用？",
            "category": "Technology/Products",
            "description": "产品推荐问题"
        },
        {
            "message": "你多大了？",
            "category": "Personal/Age",
            "description": "年龄个人问题"
        },
        {
            "message": "你住在哪里？",
            "category": "Personal/Location",
            "description": "居住地问题"
        }
    ]

    successful_redirects = 0
    total_tests = len(test_cases)

    for i, test_case in enumerate(test_cases, 1):
        print(f"\n测试 {i}/{total_tests}: {test_case['category']}")
        print(f"用户输入: \"{test_case['message']}\"")
        print(f"描述: {test_case['description']}")
        print("-" * 50)

        try:
            # 发送消息
            response = requests.post(chatbot_url, json={
                "message": test_case['message'],
                "user_id": 1,
                "session": {}
            })

            if response.status_code == 200:
                data = response.json()
                bot_response = data.get('message', '')

                print(f"🤖 Chatbot响应:")
                print(f"{bot_response}")

                # 检查是否成功引导回酒店服务（中英文关键词）
                hotel_keywords = [
                    'hotel', 'room', 'booking', 'book', 'reservation', 'stay',
                    'check-in', 'check-out', 'service', 'accommodation',
                    # 中文关键词
                    '酒店', '房间', '预订', '订房', '住宿', '入住', '服务', '早餐',
                    '房型', '客房', '空房', '房价', '设施', '查看', '安排'
                ]

                if any(keyword in bot_response.lower() for keyword in hotel_keywords):
                    print("✅ 成功引导回酒店服务")
                    successful_redirects += 1
                else:
                    print("❌ 没有成功引导回酒店服务")

            else:
                print(f"❌ 请求失败: {response.status_code}")

        except Exception as e:
            print(f"❌ 测试过程中出错: {str(e)}")

        time.sleep(0.5)  # 避免请求过快

    print("\n" + "=" * 60)
    print("🎯 测试结果总结")
    print(f"总测试数: {total_tests}")
    print(f"成功引导: {successful_redirects}")
    print(f"成功率: {(successful_redirects/total_tests)*100:.1f}%")

    if successful_redirects >= total_tests * 0.8:  # 80%成功率
        print("🎉 测试通过！Off-topic处理表现优秀")
    elif successful_redirects >= total_tests * 0.6:  # 60%成功率
        print("✅ 测试基本通过，还有改进空间")
    else:
        print("⚠️ 测试需要改进，成功率偏低")

    print("\n📋 功能改进总结:")
    print("✅ 扩展了个人问题识别")
    print("✅ 添加了随机/哲学问题处理")
    print("✅ 增强了科技问题识别")
    print("✅ 新增了金融、职业、健康等类别")
    print("✅ 改进了引导策略，更自然地转向酒店服务")
    print("✅ 提供了个性化的回应，而不是通用拒绝")

if __name__ == "__main__":
    test_enhanced_off_topic()
