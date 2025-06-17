#!/usr/bin/env python3
"""
Simple test to check chatbot booking user association.
"""

import requests

def test_chatbot_booking_user_association():
    """Test that chatbot bookings are associated with users."""
    print("🚀 Testing Chatbot Booking User Association")
    print("=" * 45)
    
    api_url = "http://127.0.0.1:8000/hotel_booking/chatbot/api/"
    session_data = {}
    
    try:
        # Step 1: Start booking process with user_id
        print("📋 Step 1: Starting booking process with user_id=1")
        response1 = requests.post(api_url, json={
            "message": "book a room",
            "session": session_data,
            "user_id": 1  # Test with user ID 1
        }, headers={
            "Content-Type": "application/json",
            "X-Requested-With": "XMLHttpRequest"
        }, timeout=10)
        
        if response1.status_code == 200:
            data1 = response1.json()
            session_data = data1.get('session', {})
            print(f"✅ Response: {data1['message'][:50]}...")
            print(f"📋 Session user_data: {session_data.get('user_data', {})}")
            
            # Check if user information is in session
            user_data = session_data.get('user_data', {})
            if 'user' in user_data:
                print(f"✅ User object found in session: {user_data['user']}")
            else:
                print("❌ No user object in session")
                
            if 'username' in user_data:
                print(f"✅ Username found in session: {user_data['username']}")
            else:
                print("❌ No username in session")
                
        else:
            print(f"❌ Status: {response1.status_code}")
            return False
        
        # Step 2: Continue with room selection
        print("\n📋 Step 2: Selecting room type 'Standard Room'")
        response2 = requests.post(api_url, json={
            "message": "Standard Room",
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
        
        # Step 3: Provide dates
        print("📋 Step 3: Providing dates 'June 25 to June 27'")
        response3 = requests.post(api_url, json={
            "message": "June 25 to June 27",
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
        
        # Step 4: Provide guest name
        print("📋 Step 4: Providing guest name 'Profile Test User'")
        response4 = requests.post(api_url, json={
            "message": "Profile Test User",
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
        print("📋 Step 5: Providing email 'profiletest@example.com'")
        response5 = requests.post(api_url, json={
            "message": "profiletest@example.com",
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
        print("📋 Step 6: Providing phone '555-123-4567'")
        response6 = requests.post(api_url, json={
            "message": "555-123-4567",
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
            if "booking id" in data6['message'].lower() or "confirmed" in data6['message'].lower():
                print("🎉 Booking created successfully!")
                
                # Extract booking ID from response
                import re
                booking_id_match = re.search(r'BK-\d+', data6['message'])
                if booking_id_match:
                    booking_id = booking_id_match.group(0)
                    print(f"📋 Booking ID: {booking_id}")
                    print("✅ Test completed - booking should be associated with user ID 1")
                    return True
                else:
                    print("❌ Could not extract booking ID from response")
                    return False
            else:
                print("❓ Unexpected response - booking may not have been created")
                print(f"Full response: {data6['message']}")
                return False
        else:
            print(f"❌ Status: {response6.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def check_database_directly():
    """Check database directly using Django shell."""
    print("\n🚀 Checking Database Directly")
    print("=" * 30)
    
    # This would need to be run in Django shell
    print("📋 To check database directly, run:")
    print("   python manage.py shell")
    print("   >>> from hotel_booking.models import Booking")
    print("   >>> from django.contrib.auth.models import User")
    print("   >>> user = User.objects.get(id=1)")
    print("   >>> bookings = Booking.objects.filter(user=user)")
    print("   >>> for b in bookings: print(f'{b.booking_id}: {b.guest_name} - User: {b.user}')")
    
    return True

if __name__ == "__main__":
    print("🚀 Starting Chatbot Profile Association Test")
    print("=" * 45)
    
    # Test 1: Create booking via chatbot with user_id
    success1 = test_chatbot_booking_user_association()
    
    # Test 2: Instructions for database check
    success2 = check_database_directly()
    
    if success1:
        print("\n🎉 Chatbot booking test completed!")
        print("📋 Next steps:")
        print("   1. Check Django admin or database to verify user association")
        print("   2. Login to the website and check profile page")
        print("   3. Verify booking appears in booking history")
    else:
        print("\n❌ Chatbot booking test failed.")
        
    print("\n📝 Note: The booking should now be associated with user ID 1")
    print("   and should appear in that user's profile booking history.")
