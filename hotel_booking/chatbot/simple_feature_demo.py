# Simple Demo for New Hotel Chatbot Features
# 新酒店聊天机器人功能简单演示

import re
from typing import Dict, List, Any

class SimpleHotelChatbot:
    """
    Simplified hotel chatbot demonstrating all new features.
    """
    
    def __init__(self):
        # Intent patterns for new features
        self.intent_patterns = {
            "booking_intent": [
                r"(?:book|reserve|make.*reservation|want.*room)",
                r"(?:预订|订房|要.*房间|想.*住)"
            ],
            "check_booking_status": [
                r"(?:did i book|check.*booking|booking.*status|my.*reservation)",
                r"(?:我有预订吗|查看.*预订|预订.*状态|我的.*订单)",
                r"(?:booking.*id|reservation.*number|order.*number)"
            ],
            "hotel_info": [
                r"(?:check.*in.*time|what.*time.*check)",
                r"(?:wi.*fi|wifi|internet)",
                r"(?:breakfast.*time|when.*breakfast)",
                r"(?:check.*out.*time|checkout.*time)"
            ],
            "feedback_rating": [
                r"(?:feedback|rating|review|satisfaction)",
                r"(?:give.*rating|rate.*stay|how.*satisfied)",
                r"(?:反馈|评价|评分|满意度)"
            ],
            "cancel_booking": [
                r"(?:cancel.*reservation|cancel.*booking|cancel.*order)",
                r"(?:not.*going|don't.*need|want.*cancel)",
                r"(?:取消.*预订|取消.*订单|不去了)"
            ],
            "upgrade_room": [
                r"(?:upgrade.*room|upgrade.*to|change.*to.*better)",
                r"(?:executive.*suite|deluxe.*room|better.*room)",
                r"(?:升级.*房间|换.*更好|升级.*到)"
            ],
            "extend_stay": [
                r"(?:extend.*stay|stay.*longer|one.*more.*day)",
                r"(?:check.*out.*later|延长.*住宿|多住.*天)",
                r"(?:extend.*to|until.*friday|stay.*until)"
            ],
            "book_another_room": [
                r"(?:book.*another.*room|add.*another.*room|one.*more.*room)",
                r"(?:additional.*room|extra.*room|second.*room)",
                r"(?:再订.*房间|加订.*房间|多订.*间)"
            ],
            "modify_booking_date": [
                r"(?:change.*date|modify.*date|postpone.*booking)",
                r"(?:change.*check.*in|different.*date|move.*to)",
                r"(?:修改.*日期|改.*时间|推迟.*预订)"
            ],
            "addon_services": [
                r"(?:breakfast.*service|airport.*transfer|additional.*service)",
                r"(?:add.*breakfast|need.*transfer|extra.*service)",
                r"(?:早餐.*服务|机场.*接送|额外.*服务)"
            ],
            "non_hotel_topic": [
                r"(?:will.*you.*fall.*in.*love|how.*ai.*works|what.*time.*is.*it)",
                r"(?:what.*do.*you.*like.*eat|weather.*today|rain.*malaysia)",
                r"(?:你会.*恋爱吗|人工智能.*工作|现在.*几点)"
            ]
        }
        
        # Response templates
        self.responses = {
            "booking_intent": "I'd be delighted to assist you with your reservation. To provide you with the best available options, could you please share your preferred check-in and check-out dates, the type of room you're interested in, and the number of guests?",
            
            "check_booking_status": "I'd be happy to help you check your booking status. Could you please provide your booking ID or the name under which the reservation was made? This will allow me to quickly locate your reservation details.",
            
            "hotel_info": {
                "checkin": "Check-in time starts at 2:00 PM. Early check-in may be available upon request, subject to room availability.",
                "checkout": "Check-out time is before 12:00 PM (noon). Late check-out can be arranged for an additional fee, subject to availability.",
                "wifi": "All rooms provide complimentary high-speed Wi-Fi. The network password is provided on your room key card upon check-in.",
                "breakfast": "Breakfast is served daily from 6:00 AM to 11:00 AM in our main restaurant. We offer both continental and local Malaysian cuisine options.",
                "general": "Here's some essential hotel information: Check-in is at 2:00 PM, check-out at 12:00 PM, breakfast is served 6:00-11:00 AM, and complimentary Wi-Fi is available throughout the hotel."
            },
            
            "feedback_rating": "Thank you for taking the time to share your feedback! Your experience matters greatly to us. How would you rate your stay with us on a scale of 1-5 stars? Please feel free to share any specific comments or suggestions - we value your input for continuous improvement.",
            
            "cancel_booking": "I understand you'd like to cancel your reservation. To assist you with this, please provide your booking ID or the name under which the reservation was made. I'll then review the cancellation policy and process your request accordingly.",
            
            "upgrade_room": "I'd be delighted to help you upgrade your room! To check available upgrade options, please provide your current booking details. Our upgrade options include: Deluxe Room (+RM73/night) and Executive Suite (+RM189/night). Upgrades are subject to availability.",
            
            "extend_stay": "I'd be happy to help extend your stay! Please provide your current booking details and let me know until which date you'd like to extend. I'll check room availability and provide you with the additional charges.",
            
            "book_another_room": "Certainly! I can help you book an additional room. Would you like the same room type as your current booking, or would you prefer a different type? Please let me know your preferred room type and if the dates should match your existing reservation.",
            
            "modify_booking_date": "I can help you modify your booking dates. Please provide your booking ID and let me know the new check-in and check-out dates you prefer. I'll check availability and update your reservation accordingly.",
            
            "addon_services": {
                "breakfast": "Our breakfast service is available for RM20 per person per day. It includes a variety of continental and local Malaysian dishes. How many guests would you like to add breakfast service for?",
                "airport": "Our airport transfer service is available for RM50 (up to 5 passengers). Please provide your flight details including arrival/departure time and flight number so we can schedule the pickup accordingly.",
                "general": "We offer several add-on services: Breakfast service (RM20/person/day) and Airport transfer (RM50/up to 5 people). Which service would you like to add to your booking?"
            },
            
            "non_hotel_topic": "I appreciate your question, but I'm specifically designed to assist with hotel services such as room bookings, facility information, reservations management, and guest services. How can I help you with your hotel needs today?"
        }
    
    def detect_intent(self, text: str) -> str:
        """Detect user intent from text."""
        text_lower = text.lower()
        
        for intent, patterns in self.intent_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text_lower):
                    return intent
        
        return "general_inquiry"
    
    def generate_response(self, text: str, intent: str) -> str:
        """Generate response based on intent."""
        text_lower = text.lower()
        
        if intent == "hotel_info":
            if any(keyword in text_lower for keyword in ['check', 'checkin', 'check-in']):
                return self.responses["hotel_info"]["checkin"]
            elif any(keyword in text_lower for keyword in ['checkout', 'check-out']):
                return self.responses["hotel_info"]["checkout"]
            elif any(keyword in text_lower for keyword in ['wifi', 'internet', 'wi-fi']):
                return self.responses["hotel_info"]["wifi"]
            elif any(keyword in text_lower for keyword in ['breakfast']):
                return self.responses["hotel_info"]["breakfast"]
            else:
                return self.responses["hotel_info"]["general"]
        
        elif intent == "addon_services":
            if any(keyword in text_lower for keyword in ['breakfast']):
                return self.responses["addon_services"]["breakfast"]
            elif any(keyword in text_lower for keyword in ['airport', 'transfer', 'transport']):
                return self.responses["addon_services"]["airport"]
            else:
                return self.responses["addon_services"]["general"]
        
        elif intent in self.responses:
            return self.responses[intent]
        
        else:
            return "I'm here to help you with any questions about our hotel services, room reservations, local attractions, or special arrangements you might need during your stay. How can I assist you today?"
    
    def chat(self, user_input: str) -> Dict[str, Any]:
        """Process user input and return response."""
        intent = self.detect_intent(user_input)
        response = self.generate_response(user_input, intent)
        
        return {
            "user_input": user_input,
            "detected_intent": intent,
            "response": response
        }

def demo_all_features():
    """Demo all new hotel chatbot features."""
    print("🏨 Hotel Chatbot New Features Demo")
    print("=" * 60)
    
    chatbot = SimpleHotelChatbot()
    
    # Test cases for all new features
    test_cases = [
        # Room Booking
        ("Room Booking", "I want to book a deluxe room for 2 nights"),
        
        # Check Booking Status
        ("Check Booking Status", "Did I book a room last time?"),
        ("Check Booking Status", "My booking ID is 123456, please confirm"),
        
        # Hotel Info
        ("Hotel Info", "What time can I check in?"),
        ("Hotel Info", "Is there Wi-Fi?"),
        ("Hotel Info", "What time is breakfast available?"),
        ("Hotel Info", "What time is the checkout time?"),
        
        # Feedback / Rating
        ("Feedback / Rating", "I want to give some feedback"),
        ("Feedback / Rating", "I was very satisfied with my stay this time"),
        
        # Cancel Booking
        ("Cancel Booking", "I want to cancel my reservation"),
        ("Cancel Booking", "Cancel order number 123456"),
        
        # Upgrade Room
        ("Upgrade Room", "I want to upgrade my room"),
        ("Upgrade Room", "Can I change to Executive Suite?"),
        
        # Extend Stay
        ("Extend Stay", "I want to stay one more day"),
        ("Extend Stay", "Extend it to Friday"),
        
        # Book Another Room
        ("Book Another Room", "I want to book another room"),
        ("Book Another Room", "Book another deluxe room"),
        
        # Modify Booking Date
        ("Modify Booking Date", "I want to change my check-in date from June 12 to June 15"),
        ("Modify Booking Date", "Can I postpone my booking for two days?"),
        
        # Add-on Services
        ("Add-on Services", "I need breakfast service for 2 people"),
        ("Add-on Services", "Do you have airport transfer?"),
        
        # Non-hotel Topics
        ("Non-hotel Topics", "Will you fall in love?"),
        ("Non-hotel Topics", "What time is it now?"),
        
        # Chinese Language
        ("Chinese Language", "我想取消预订"),
        ("Chinese Language", "早餐时间是什么时候？")
    ]
    
    current_category = ""
    for category, user_input in test_cases:
        # Print category header
        if category != current_category:
            current_category = category
            print(f"\n🎯 {category}")
            print("-" * 50)
        
        # Process input
        result = chatbot.chat(user_input)
        
        print(f"\n💬 User: '{user_input}'")
        print(f"🎯 Intent: {result['detected_intent']}")
        print(f"🤖 Bot: {result['response']}")
    
    print("\n" + "=" * 60)
    print("✅ All features demonstrated successfully!")

def demo_conversation_scenarios():
    """Demo specific conversation scenarios."""
    print("\n\n🎭 Conversation Scenarios Demo")
    print("=" * 60)
    
    chatbot = SimpleHotelChatbot()
    
    scenarios = [
        {
            "title": "Booking Process",
            "conversation": [
                "Hi, I want to book a room",
                "What room types do you have?",
                "I'll take a deluxe room for 2 nights"
            ]
        },
        {
            "title": "Service Inquiries",
            "conversation": [
                "What time is check-in?",
                "Do you have Wi-Fi?",
                "I need airport transfer service"
            ]
        },
        {
            "title": "Booking Management",
            "conversation": [
                "I want to check my booking status",
                "Can I upgrade my room?",
                "I need to extend my stay by one day"
            ]
        }
    ]
    
    for scenario in scenarios:
        print(f"\n📋 Scenario: {scenario['title']}")
        print("-" * 40)
        
        for i, message in enumerate(scenario['conversation'], 1):
            result = chatbot.chat(message)
            print(f"\nTurn {i}:")
            print(f"User: {message}")
            print(f"Bot: {result['response']}")

if __name__ == "__main__":
    try:
        demo_all_features()
        demo_conversation_scenarios()
        print("\n🎉 Demo completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Error during demo: {str(e)}")
        import traceback
        traceback.print_exc()
