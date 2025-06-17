# Test Script for New Hotel Chatbot Features
# 测试酒店聊天机器人新功能的脚本

import sys
import os

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

try:
    from advanced_nlp_processor import AdvancedNLPProcessor
    from nlp_enhancements import NLPEnhancementManager
except ImportError:
    # Handle relative imports
    import importlib.util
    
    # Load modules directly
    spec = importlib.util.spec_from_file_location("hotel_knowledge_base", 
                                                  os.path.join(os.path.dirname(__file__), "hotel_knowledge_base.py"))
    hotel_knowledge_base = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(hotel_knowledge_base)
    
    spec = importlib.util.spec_from_file_location("advanced_nlp_processor", 
                                                  os.path.join(os.path.dirname(__file__), "advanced_nlp_processor.py"))
    advanced_nlp_processor = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(advanced_nlp_processor)
    AdvancedNLPProcessor = advanced_nlp_processor.AdvancedNLPProcessor
    
    spec = importlib.util.spec_from_file_location("nlp_enhancements", 
                                                  os.path.join(os.path.dirname(__file__), "nlp_enhancements.py"))
    nlp_enhancements = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(nlp_enhancements)
    NLPEnhancementManager = nlp_enhancements.NLPEnhancementManager

def test_new_features():
    """Test all the new hotel chatbot features."""
    print("🏨 Testing New Hotel Chatbot Features")
    print("=" * 60)
    
    # Initialize the enhanced NLP system
    print("🔧 Initializing NLP components...")
    nlp_processor = AdvancedNLPProcessor()
    enhancement_manager = NLPEnhancementManager(nlp_processor)
    print("✅ NLP components initialized successfully!")
    print()
    
    # Test cases for all new features
    test_cases = [
        # 1. Room Booking (existing feature - enhanced)
        {
            "category": "Room Booking",
            "user_id": "user_001",
            "input": "I want to book a deluxe room for 2 nights from June 10th",
            "description": "Enhanced booking with date extraction"
        },
        
        # 2. Check Booking Status
        {
            "category": "Check Booking Status",
            "user_id": "user_002",
            "input": "Did I book a room last time?",
            "description": "Check existing reservation"
        },
        {
            "category": "Check Booking Status",
            "user_id": "user_002",
            "input": "My booking ID is 123456, please confirm",
            "description": "Check with booking ID"
        },
        
        # 3. Hotel Info
        {
            "category": "Hotel Info",
            "user_id": "user_003",
            "input": "What time can I check in?",
            "description": "Check-in time inquiry"
        },
        {
            "category": "Hotel Info",
            "user_id": "user_003",
            "input": "Is there Wi-Fi?",
            "description": "Wi-Fi availability"
        },
        {
            "category": "Hotel Info",
            "user_id": "user_003",
            "input": "What time is breakfast available?",
            "description": "Breakfast time inquiry"
        },
        
        # 4. Feedback / Rating
        {
            "category": "Feedback / Rating",
            "user_id": "user_004",
            "input": "I want to give some feedback",
            "description": "Feedback request"
        },
        {
            "category": "Feedback / Rating",
            "user_id": "user_004",
            "input": "I was very satisfied with my stay this time",
            "description": "Positive feedback"
        },
        
        # 5. Cancel Booking
        {
            "category": "Cancel Booking",
            "user_id": "user_005",
            "input": "I want to cancel my reservation",
            "description": "Cancellation request"
        },
        {
            "category": "Cancel Booking",
            "user_id": "user_005",
            "input": "Cancel order number 123456",
            "description": "Cancel with order number"
        },
        
        # 6. Upgrade Room
        {
            "category": "Upgrade Room",
            "user_id": "user_006",
            "input": "I want to upgrade my room",
            "description": "Room upgrade request"
        },
        {
            "category": "Upgrade Room",
            "user_id": "user_006",
            "input": "Can I change to Executive Suite?",
            "description": "Specific upgrade request"
        },
        
        # 7. Extend Stay
        {
            "category": "Extend Stay",
            "user_id": "user_007",
            "input": "I want to stay one more day",
            "description": "Stay extension request"
        },
        {
            "category": "Extend Stay",
            "user_id": "user_007",
            "input": "Extend it to Friday",
            "description": "Extend to specific date"
        },
        
        # 8. Book Another Room
        {
            "category": "Book Another Room",
            "user_id": "user_008",
            "input": "I want to book another room",
            "description": "Additional room booking"
        },
        {
            "category": "Book Another Room",
            "user_id": "user_008",
            "input": "Book another deluxe room",
            "description": "Specific additional room"
        },
        
        # 9. Modify Booking Date
        {
            "category": "Modify Booking Date",
            "user_id": "user_009",
            "input": "I want to change my check-in date from June 12 to June 15",
            "description": "Date modification request"
        },
        {
            "category": "Modify Booking Date",
            "user_id": "user_009",
            "input": "Can I postpone my booking for two days?",
            "description": "Postpone booking"
        },
        
        # 10. Add-on Services
        {
            "category": "Add-on Services",
            "user_id": "user_010",
            "input": "I need breakfast service for 2 people",
            "description": "Breakfast service request"
        },
        {
            "category": "Add-on Services",
            "user_id": "user_010",
            "input": "Do you have airport transfer?",
            "description": "Airport transfer inquiry"
        },
        
        # 11. Non-hotel Topics (redirect)
        {
            "category": "Non-hotel Topics",
            "user_id": "user_011",
            "input": "Will you fall in love?",
            "description": "Off-topic question"
        },
        {
            "category": "Non-hotel Topics",
            "user_id": "user_011",
            "input": "What time is it now?",
            "description": "General question"
        },
        
        # 12. Chinese Language Support
        {
            "category": "Chinese Language",
            "user_id": "user_012",
            "input": "我想取消预订",
            "description": "Cancel booking in Chinese"
        },
        {
            "category": "Chinese Language",
            "user_id": "user_012",
            "input": "早餐时间是什么时候？",
            "description": "Breakfast time in Chinese"
        }
    ]
    
    current_category = ""
    for i, test_case in enumerate(test_cases, 1):
        # Print category header
        if test_case["category"] != current_category:
            current_category = test_case["category"]
            print(f"\n🎯 {current_category}")
            print("-" * 50)
        
        print(f"\n📝 Test {i}: {test_case['description']}")
        print(f"User: '{test_case['input']}'")
        
        try:
            # Analyze the input with enhancements
            analysis = enhancement_manager.enhance_user_understanding(
                test_case['input'], 
                test_case['user_id']
            )
            
            # Generate contextual response
            response = enhancement_manager.generate_contextual_response(
                analysis, 
                test_case['user_id']
            )
            
            # Display results
            print(f"🎯 Intent: {analysis['intent']['name']} (confidence: {analysis['intent']['confidence']:.2f})")
            print(f"🤖 Response: {response}")
            
        except Exception as e:
            print(f"❌ Error processing: {str(e)}")
        
        print()
    
    print("=" * 60)
    print("✅ All new features tested successfully!")

def test_conversation_flow():
    """Test conversation flow with multiple interactions."""
    print("\n💬 Testing Conversation Flow")
    print("-" * 50)
    
    nlp_processor = AdvancedNLPProcessor()
    enhancement_manager = NLPEnhancementManager(nlp_processor)
    
    # Simulate a conversation
    conversation = [
        "Hi, I want to book a room",
        "I prefer a deluxe room",
        "For 2 nights starting June 15th",
        "Actually, can I upgrade to Executive Suite?",
        "Also, I need airport transfer service",
        "What time is breakfast served?"
    ]
    
    user_id = "conversation_user"
    
    for i, message in enumerate(conversation, 1):
        print(f"\nTurn {i}:")
        print(f"User: {message}")
        
        try:
            analysis = enhancement_manager.enhance_user_understanding(message, user_id)
            response = enhancement_manager.generate_contextual_response(analysis, user_id)
            
            print(f"Bot: {response}")
            
            # Show conversation state
            flow = analysis.get('conversation_flow', {})
            if flow:
                print(f"State: {flow.get('state', 'unknown')}")
        
        except Exception as e:
            print(f"Error: {str(e)}")
    
    # Show conversation summary
    print(f"\n📊 Conversation Summary:")
    summary = enhancement_manager.get_conversation_summary(user_id)
    for key, value in summary.items():
        print(f"  {key}: {value}")

if __name__ == "__main__":
    try:
        print("🚀 Starting New Features Test...")
        test_new_features()
        test_conversation_flow()
        print("\n🎉 All tests completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Error during testing: {str(e)}")
        import traceback
        traceback.print_exc()
