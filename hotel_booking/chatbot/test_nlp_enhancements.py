# Test Script for Enhanced NLP Features
# 测试增强NLP功能的脚本

import sys
import os
import django

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hotel_booking.settings')
django.setup()

from advanced_nlp_processor import AdvancedNLPProcessor
from nlp_enhancements import NLPEnhancementManager

def test_enhanced_nlp():
    """Test the enhanced NLP features."""
    print("🤖 Testing Enhanced Hotel Chatbot NLP Features")
    print("=" * 60)
    
    # Initialize the enhanced NLP system
    nlp_processor = AdvancedNLPProcessor()
    enhancement_manager = NLPEnhancementManager(nlp_processor)
    
    # Test cases with different types of user inputs
    test_cases = [
        {
            "user_id": "user_001",
            "input": "Hi, I want to book a deluxe room for 2 nights",
            "description": "Initial booking request"
        },
        {
            "user_id": "user_001", 
            "input": "What amenities do you have?",
            "description": "Follow-up amenity inquiry"
        },
        {
            "user_id": "user_001",
            "input": "How much does it cost?",
            "description": "Price inquiry with context"
        },
        {
            "user_id": "user_002",
            "input": "你好，我想预订一间房间",
            "description": "Chinese language booking request"
        },
        {
            "user_id": "user_003",
            "input": "I'm very disappointed with the service",
            "description": "Negative sentiment complaint"
        },
        {
            "user_id": "user_003",
            "input": "The room is too noisy and dirty",
            "description": "Specific complaint with details"
        },
        {
            "user_id": "user_004",
            "input": "Do you have availabe rooms for tommorow?",
            "description": "Input with spelling errors"
        },
        {
            "user_id": "user_005",
            "input": "I need a quiet room on high floor with city view for 3 people",
            "description": "Complex request with multiple entities"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📝 Test Case {i}: {test_case['description']}")
        print(f"User ID: {test_case['user_id']}")
        print(f"Input: '{test_case['input']}'")
        print("-" * 40)
        
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
        print(f"😊 Sentiment: {analysis['sentiment']['label']} (confidence: {analysis['sentiment']['confidence']:.2f})")
        print(f"🌐 Language: {analysis.get('language', 'unknown')}")
        
        entities = analysis.get('entities', {})
        if any(entities.values()):
            print("🏷️  Entities found:")
            for entity_type, values in entities.items():
                if values:
                    print(f"   - {entity_type}: {values}")
        
        # Show conversation flow
        flow = analysis.get('conversation_flow', {})
        if flow:
            print(f"💬 Conversation State: {flow.get('state', 'unknown')}")
            if flow.get('pending_info'):
                print(f"⏳ Pending Info: {flow['pending_info']}")
        
        # Show user context
        user_context = analysis.get('user_context', {})
        if user_context.get('preferred_room_type'):
            print(f"👤 User Preference: {user_context['preferred_room_type']} rooms")
        
        print(f"🤖 Response: {response}")
        print("=" * 60)
    
    # Test conversation summaries
    print("\n📊 Conversation Summaries:")
    print("-" * 40)
    for user_id in ["user_001", "user_002", "user_003"]:
        summary = enhancement_manager.get_conversation_summary(user_id)
        if summary.get("status") != "no_history":
            print(f"User {user_id}:")
            print(f"  - Turns: {summary.get('conversation_turns', 0)}")
            print(f"  - State: {summary.get('current_state', 'unknown')}")
            print(f"  - Language: {summary.get('language_preference', 'unknown')}")
            print(f"  - Recent intents: {summary.get('recent_intents', [])}")
            if summary.get('pending_information'):
                print(f"  - Pending: {summary['pending_information']}")
            print()

def test_spell_correction():
    """Test spell correction functionality."""
    print("\n🔤 Testing Spell Correction")
    print("-" * 40)
    
    nlp_processor = AdvancedNLPProcessor()
    
    test_inputs = [
        "I want to make a resevation",
        "Do you have availabe rooms?",
        "What facilites do you have?",
        "I need accomodation for tonight",
        "Can I book a delux room?"
    ]
    
    for input_text in test_inputs:
        corrected = nlp_processor.preprocess_text(input_text)
        print(f"Original:  '{input_text}'")
        print(f"Corrected: '{corrected}'")
        print()

def test_language_detection():
    """Test language detection functionality."""
    print("\n🌐 Testing Language Detection")
    print("-" * 40)
    
    nlp_processor = AdvancedNLPProcessor()
    
    test_inputs = [
        "Hello, I want to book a room",
        "你好，我想预订房间",
        "Bonjour, je voudrais réserver une chambre",
        "Hola, quiero reservar una habitación",
        "こんにちは、部屋を予約したいです"
    ]
    
    for input_text in test_inputs:
        language = nlp_processor.detect_language(input_text)
        print(f"Text: '{input_text}'")
        print(f"Detected Language: {language}")
        print()

def test_entity_extraction():
    """Test enhanced entity extraction."""
    print("\n🏷️  Testing Enhanced Entity Extraction")
    print("-" * 40)
    
    nlp_processor = AdvancedNLPProcessor()
    
    test_inputs = [
        "I need a deluxe room for 3 nights from December 25th",
        "Book a family suite with city view for 4 people",
        "Do you have wheelchair accessible rooms with late checkout?",
        "I want a quiet room on high floor with spa access",
        "Reserve a standard room for John Smith arriving tomorrow"
    ]
    
    for input_text in test_inputs:
        entities = nlp_processor.extract_entities_enhanced(input_text)
        print(f"Input: '{input_text}'")
        print("Extracted entities:")
        for entity_type, values in entities.items():
            if values:
                print(f"  - {entity_type}: {values}")
        print()

if __name__ == "__main__":
    try:
        print("🚀 Starting Enhanced NLP Tests...")
        test_enhanced_nlp()
        test_spell_correction()
        test_language_detection()
        test_entity_extraction()
        print("\n✅ All tests completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Error during testing: {str(e)}")
        import traceback
        traceback.print_exc()
