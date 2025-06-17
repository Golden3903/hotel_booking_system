#!/usr/bin/env python3
"""
检查Contact Messages是否保存到数据库
"""

import os
import sys
import django

# 设置Django环境
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
django.setup()

from hotel_booking.models import ContactMessage

def check_contact_messages():
    """检查数据库中的Contact Messages"""
    
    print("🔍 检查数据库中的Contact Messages")
    print("=" * 50)
    
    try:
        # 获取所有contact messages
        messages = ContactMessage.objects.all().order_by('-created_at')
        
        print(f"📊 总共找到 {messages.count()} 条联系消息")
        
        if messages.exists():
            print("\n📝 最近的消息:")
            for i, msg in enumerate(messages[:5], 1):  # 显示最近5条
                print(f"\n{i}. 消息详情:")
                print(f"   姓名: {msg.name}")
                print(f"   邮箱: {msg.email}")
                print(f"   主题: {msg.subject}")
                print(f"   消息: {msg.message[:100]}{'...' if len(msg.message) > 100 else ''}")
                print(f"   创建时间: {msg.created_at}")
                print(f"   已读: {'是' if msg.is_read else '否'}")
                print(f"   已回复: {'是' if msg.replied else '否'}")
                print("-" * 30)
        else:
            print("📭 数据库中暂无联系消息")
            
    except Exception as e:
        print(f"❌ 检查过程中出错: {str(e)}")
    
    print("\n🎯 数据库检查完成！")

if __name__ == "__main__":
    check_contact_messages()
