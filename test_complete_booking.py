#!/usr/bin/env python3
"""
Complete booking test to verify user association.
"""

import requests

def complete_booking_test():
    """Test complete booking flow with user association."""
    print("🚀 Testing Complete Booking Flow with User Association")
    print("=" * 55)
    
    api_url = "http://127.0.0.1:8000/hotel_booking/chatbot/api/"
    session_data = {}
    
    try:
        # Step 1: Start booking
        print("📋 Step 1: Starting booking 'book a room'")
        response1 = requests.post(api_url, json={
            "message": "book a room",
            "session": session_data,
            "user_id": 1
        }, headers={
            "Content-Type": "application/json",
            "X-Requested-With": "XMLHttpRequest"
        }, timeout=10)
        
        if response1.status_code == 200:
            data1 = response1.json()
            session_data = data1.get('session', {})
            print(f"✅ Response: {data1['message'][:50]}...")
        else:
            print(f"❌ Status: {response1.status_code}")
            return False
        
        # Step 2: Provide guest name (not room type)
        print("📋 Step 2: Providing guest name 'John Smith'")
        response2 = requests.post(api_url, json={
            "message": "John Smith",
            "session": session_data,
            "user_id": 1
        }, headers={
            "Content-Type": "application/json",
            "X-Requested-With": "XMLHttpRequest"
        }, timeout=10)
        
        if response2.status_code == 200:
            data2 = response2.json()
            session_data = data2.get('session', {})
            print(f"✅ Response: {data2['message'][:50]}...")
        else:
            print(f"❌ Status: {response2.status_code}")
            return False
        
        # Step 3: Provide room type
        print("📋 Step 3: Providing room type 'Standard Room'")
        response3 = requests.post(api_url, json={
            "message": "Standard Room",
            "session": session_data,
            "user_id": 1
        }, headers={
            "Content-Type": "application/json",
            "X-Requested-With": "XMLHttpRequest"
        }, timeout=10)
        
        if response3.status_code == 200:
            data3 = response3.json()
            session_data = data3.get('session', {})
            print(f"✅ Response: {data3['message'][:50]}...")
        else:
            print(f"❌ Status: {response3.status_code}")
            return False
        
        # Step 4: Provide dates
        print("📋 Step 4: Providing dates 'June 28 to June 30'")
        response4 = requests.post(api_url, json={
            "message": "June 28 to June 30",
            "session": session_data,
            "user_id": 1
        }, headers={
            "Content-Type": "application/json",
            "X-Requested-With": "XMLHttpRequest"
        }, timeout=10)
        
        if response4.status_code == 200:
            data4 = response4.json()
            session_data = data4.get('session', {})
            print(f"✅ Response: {data4['message'][:50]}...")
        else:
            print(f"❌ Status: {response4.status_code}")
            return False
        
        # Step 5: Provide email
        print("📋 Step 5: Providing email 'john.smith@example.com'")
        response5 = requests.post(api_url, json={
            "message": "john.smith@example.com",
            "session": session_data,
            "user_id": 1
        }, headers={
            "Content-Type": "application/json",
            "X-Requested-With": "XMLHttpRequest"
        }, timeout=10)
        
        if response5.status_code == 200:
            data5 = response5.json()
            session_data = data5.get('session', {})
            print(f"✅ Response: {data5['message'][:50]}...")
        else:
            print(f"❌ Status: {response5.status_code}")
            return False
        
        # Step 6: Provide phone
        print("📋 Step 6: Providing phone '555-987-6543'")
        response6 = requests.post(api_url, json={
            "message": "555-987-6543",
            "session": session_data,
            "user_id": 1
        }, headers={
            "Content-Type": "application/json",
            "X-Requested-With": "XMLHttpRequest"
        }, timeout=10)
        
        if response6.status_code == 200:
            data6 = response6.json()
            session_data = data6.get('session', {})
            print(f"✅ Response: {data6['message'][:100]}...")
            
            # Check if booking was created
            if "booking" in data6['message'].lower() and ("id" in data6['message'].lower() or "confirmed" in data6['message'].lower()):
                print("🎉 Booking created successfully!")
                
                # Extract booking ID from response
                import re
                booking_id_match = re.search(r'BK-\d+', data6['message'])
                if booking_id_match:
                    booking_id = booking_id_match.group(0)
                    print(f"📋 Booking ID: {booking_id}")
                    return True
                else:
                    print("❓ Booking created but couldn't extract ID")
                    return True
            else:
                print("❓ Unexpected response - may need confirmation")
                print(f"Full response: {data6['message']}")
                
                # Try confirming if it's asking for confirmation
                if "confirm" in data6['message'].lower():
                    print("📋 Step 7: Confirming booking 'yes'")
                    response7 = requests.post(api_url, json={
                        "message": "yes",
                        "session": session_data,
                        "user_id": 1
                    }, headers={
                        "Content-Type": "application/json",
                        "X-Requested-With": "XMLHttpRequest"
                    }, timeout=10)
                    
                    if response7.status_code == 200:
                        data7 = response7.json()
                        print(f"✅ Confirmation response: {data7['message'][:100]}...")
                        
                        # Check for booking ID in confirmation
                        booking_id_match = re.search(r'BK-\d+', data7['message'])
                        if booking_id_match:
                            booking_id = booking_id_match.group(0)
                            print(f"📋 Booking ID: {booking_id}")
                            print("🎉 Booking confirmed successfully!")
                            return True
                        else:
                            print("❓ Booking confirmed but couldn't extract ID")
                            return True
                    else:
                        print(f"❌ Confirmation failed: {response7.status_code}")
                        return False
                else:
                    return False
        else:
            print(f"❌ Status: {response6.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

if __name__ == "__main__":
    print("🚀 Starting Complete Booking Test")
    print("=" * 35)
    
    success = complete_booking_test()
    
    if success:
        print("\n🎉 Complete booking test passed!")
        print("📋 Next steps:")
        print("   1. Check Django admin to verify booking exists")
        print("   2. Verify booking is associated with user ID 1")
        print("   3. Login to website and check profile page")
        print("   4. Confirm booking appears in booking history")
    else:
        print("\n❌ Complete booking test failed.")
        
    print("\n📝 Note: If successful, the booking should be associated with user ID 1")
    print("   and should appear in that user's profile booking history.")
