#!/usr/bin/env python3
"""
测试英文off-topic意图识别功能
"""

import requests
import time

def test_english_off_topic():
    """测试英文off-topic意图识别和引导功能"""
    
    base_url = "http://127.0.0.1:8000"
    chatbot_url = f"{base_url}/hotel_booking/chatbot/api/"
    
    print("🧪 测试英文Off-Topic意图识别功能")
    print("=" * 60)
    
    # 英文测试用例
    test_cases = [
        {
            "message": "do you have girlfriend?",
            "category": "Personal/Relationship",
            "description": "个人关系问题"
        },
        {
            "message": "what program are you written in?",
            "category": "AI/Programming",
            "description": "编程技术问题"
        },
        {
            "message": "do you play games?",
            "category": "Entertainment/Gaming",
            "description": "游戏娱乐问题"
        },
        {
            "message": "do you have siblings?",
            "category": "Personal/Family",
            "description": "家庭个人问题"
        },
        {
            "message": "can you help me write homework?",
            "category": "Education/Homework",
            "description": "学习作业问题"
        },
        {
            "message": "who is your boss?",
            "category": "Personal/Work",
            "description": "工作关系问题"
        },
        {
            "message": "will humans be replaced by AI?",
            "category": "AI/Future",
            "description": "AI未来问题"
        },
        {
            "message": "when is Malaysia independence day?",
            "category": "General Knowledge",
            "description": "常识问题"
        },
        {
            "message": "do you believe in fate?",
            "category": "Philosophy/Belief",
            "description": "哲学信念问题"
        },
        {
            "message": "do you have pets?",
            "category": "Personal/Pets",
            "description": "宠物个人问题"
        },
        {
            "message": "do you prefer sea or mountain?",
            "category": "Personal/Preference",
            "description": "个人偏好问题"
        },
        {
            "message": "you are very cute",
            "category": "Personal/Compliment",
            "description": "个人赞美"
        },
        {
            "message": "can you tell me lottery numbers?",
            "category": "Random/Lottery",
            "description": "随机彩票问题"
        },
        {
            "message": "do you support any political party?",
            "category": "Politics",
            "description": "政治立场问题"
        },
        {
            "message": "what movies do you like?",
            "category": "Entertainment/Movies",
            "description": "电影娱乐问题"
        },
        {
            "message": "can you sing?",
            "category": "Entertainment/Music",
            "description": "音乐娱乐问题"
        },
        {
            "message": "what do you think about AI regulation?",
            "category": "AI/Regulation",
            "description": "AI监管问题"
        },
        {
            "message": "who invented the light bulb?",
            "category": "General Knowledge/History",
            "description": "历史常识问题"
        },
        {
            "message": "which phone brand is the best?",
            "category": "Technology/Products",
            "description": "产品推荐问题"
        },
        {
            "message": "how old are you?",
            "category": "Personal/Age",
            "description": "年龄个人问题"
        },
        {
            "message": "where do you live?",
            "category": "Personal/Location",
            "description": "居住地问题"
        },
        {
            "message": "what time is it now?",
            "category": "Time Query",
            "description": "时间查询"
        },
        {
            "message": "will it rain today?",
            "category": "Weather",
            "description": "天气查询"
        },
        {
            "message": "tell me a joke",
            "category": "Entertainment/Joke",
            "description": "笑话娱乐"
        },
        {
            "message": "what's the latest news?",
            "category": "News",
            "description": "新闻查询"
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
                    'guest', 'comfortable', 'amenities', 'facilities'
                ]
                
                # 检查是否是通用的"不理解"回应
                generic_responses = [
                    "i'm not sure i understand",
                    "could you please clarify",
                    "could you provide more details"
                ]
                
                is_generic = any(generic in bot_response.lower() for generic in generic_responses)
                has_hotel_keywords = any(keyword in bot_response.lower() for keyword in hotel_keywords)
                
                if has_hotel_keywords and not is_generic:
                    print("✅ 成功引导回酒店服务")
                    successful_redirects += 1
                elif is_generic:
                    print("❌ 返回了通用的不理解回应")
                else:
                    print("❌ 没有成功引导回酒店服务")
                    
            else:
                print(f"❌ 请求失败: {response.status_code}")
                
        except Exception as e:
            print(f"❌ 测试过程中出错: {str(e)}")
        
        time.sleep(0.5)  # 避免请求过快
    
    print("\n" + "=" * 60)
    print("🎯 英文Off-Topic测试结果总结")
    print(f"总测试数: {total_tests}")
    print(f"成功引导: {successful_redirects}")
    print(f"成功率: {(successful_redirects/total_tests)*100:.1f}%")
    
    if successful_redirects >= total_tests * 0.9:  # 90%成功率
        print("🎉 测试优秀！英文Off-topic处理表现出色")
    elif successful_redirects >= total_tests * 0.7:  # 70%成功率
        print("✅ 测试良好，还有改进空间")
    else:
        print("⚠️ 测试需要改进，部分英文问题未被正确处理")
    
    # 显示未成功处理的问题
    failed_count = total_tests - successful_redirects
    if failed_count > 0:
        print(f"\n⚠️ 有 {failed_count} 个英文问题需要改进处理")

if __name__ == "__main__":
    test_english_off_topic()
