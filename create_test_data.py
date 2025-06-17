#!/usr/bin/env python3
"""
创建测试数据用于升级房间功能测试
"""

import os
import sys
import django
from datetime import date, timedelta

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
django.setup()

from hotel_booking.models import Room, Booking

def create_test_data():
    """创建测试数据"""
    
    print("🔧 创建测试数据...")
    
    # 创建房间类型（如果不存在）
    rooms_data = [
        {"name": "Standard Room", "price": 100.0, "description": "Comfortable standard room"},
        {"name": "Deluxe Room", "price": 150.0, "description": "Spacious deluxe room with city view"},
        {"name": "Suite", "price": 250.0, "description": "Luxury suite with separate living area"},
        {"name": "Executive Suite", "price": 350.0, "description": "Premium executive suite with premium amenities"}
    ]
    
    for room_data in rooms_data:
        room, created = Room.objects.get_or_create(
            name=room_data["name"],
            defaults={
                "price": room_data["price"],
                "description": room_data["description"]
            }
        )
        if created:
            print(f"✅ 创建房间: {room.name} (RM{room.price}/night)")
        else:
            print(f"📋 房间已存在: {room.name} (RM{room.price}/night)")
    
    # 创建测试预订
    standard_room = Room.objects.get(name="Standard Room")
    
    # 删除现有的测试预订（如果存在）
    Booking.objects.filter(booking_id="BK-12345").delete()
    
    # 创建新的测试预订
    test_booking = Booking.objects.create(
        booking_id="BK-12345",
        room=standard_room,
        guest_name="Test User",
        guest_email="test@example.com",
        guest_phone="0123456789",
        check_in_date=date.today() + timedelta(days=7),
        check_out_date=date.today() + timedelta(days=9),
        status='confirmed'
    )
    
    print(f"✅ 创建测试预订: {test_booking.booking_id}")
    print(f"   客人: {test_booking.guest_name}")
    print(f"   房间: {test_booking.room.name}")
    print(f"   入住: {test_booking.check_in_date}")
    print(f"   退房: {test_booking.check_out_date}")
    
    print("\n🎯 测试数据创建完成！")
    print("现在可以使用 BK-12345 作为测试预订ID")

if __name__ == "__main__":
    create_test_data()
