# Demo Script for Enhanced NLP Features
# 演示增强NLP功能的脚本

import sys
import os

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

try:
    from advanced_nlp_processor import AdvancedNLPProcessor
    from nlp_enhancements import NLPEnhancementManager
    from hotel_knowledge_base import HotelKnowledgeBase
except ImportError:
    # Handle relative imports
    import importlib.util
    import os

    # Load modules directly
    spec = importlib.util.spec_from_file_location("hotel_knowledge_base",
                                                  os.path.join(os.path.dirname(__file__), "hotel_knowledge_base.py"))
    hotel_knowledge_base = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(hotel_knowledge_base)
    HotelKnowledgeBase = hotel_knowledge_base.HotelKnowledgeBase

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

def demo_enhanced_nlp():
    """Demo the enhanced NLP features without Django dependencies."""
    print("🤖 Hotel Chatbot Enhanced NLP Features Demo")
    print("=" * 60)

    # Initialize the enhanced NLP system
    print("🔧 Initializing NLP components...")
    nlp_processor = AdvancedNLPProcessor()
    enhancement_manager = NLPEnhancementManager(nlp_processor)
    print("✅ NLP components initialized successfully!")
    print()

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
        print(f"📝 Test Case {i}: {test_case['description']}")
        print(f"User ID: {test_case['user_id']}")
        print(f"Input: '{test_case['input']}'")
        print("-" * 40)

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
            print(f"😊 Sentiment: {analysis['sentiment']['label']} (confidence: {analysis['sentiment']['confidence']:.2f})")
            print(f"🌐 Language: {analysis.get('language', 'unknown')}")

            # Show preprocessing
            if analysis.get('processed_text') != analysis.get('original_text'):
                print(f"🔤 Corrected: '{analysis.get('processed_text')}'")

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

        except Exception as e:
            print(f"❌ Error processing: {str(e)}")

        print("=" * 60)

    # Test conversation summaries
    print("\n📊 Conversation Summaries:")
    print("-" * 40)
    for user_id in ["user_001", "user_002", "user_003"]:
        try:
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
        except Exception as e:
            print(f"Error getting summary for {user_id}: {str(e)}")

def demo_spell_correction():
    """Demo spell correction functionality."""
    print("\n🔤 Spell Correction Demo")
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
        try:
            corrected = nlp_processor.preprocess_text(input_text)
            print(f"Original:  '{input_text}'")
            print(f"Corrected: '{corrected}'")
            print()
        except Exception as e:
            print(f"Error correcting '{input_text}': {str(e)}")

def demo_language_detection():
    """Demo language detection functionality."""
    print("\n🌐 Language Detection Demo")
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
        try:
            language = nlp_processor.detect_language(input_text)
            print(f"Text: '{input_text}'")
            print(f"Detected Language: {language}")
            print()
        except Exception as e:
            print(f"Error detecting language for '{input_text}': {str(e)}")

def demo_entity_extraction():
    """Demo enhanced entity extraction."""
    print("\n🏷️  Enhanced Entity Extraction Demo")
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
        try:
            entities = nlp_processor.extract_entities_enhanced(input_text)
            print(f"Input: '{input_text}'")
            print("Extracted entities:")
            for entity_type, values in entities.items():
                if values:
                    print(f"  - {entity_type}: {values}")
            print()
        except Exception as e:
            print(f"Error extracting entities from '{input_text}': {str(e)}")

def demo_sentiment_analysis():
    """Demo enhanced sentiment analysis."""
    print("\n😊 Enhanced Sentiment Analysis Demo")
    print("-" * 40)

    nlp_processor = AdvancedNLPProcessor()

    test_inputs = [
        "I love this hotel, it's absolutely amazing!",
        "The service is terrible and I'm very disappointed",
        "The room is okay, nothing special",
        "非常满意这次的住宿体验",
        "服务太差了，很失望",
        "I'm extremely happy with the excellent facilities"
    ]

    for input_text in test_inputs:
        try:
            sentiment = nlp_processor.analyze_sentiment_enhanced(input_text)
            print(f"Text: '{input_text}'")
            print(f"Sentiment: {sentiment['label']} (confidence: {sentiment['confidence']:.2f}, method: {sentiment.get('method', 'unknown')})")
            print()
        except Exception as e:
            print(f"Error analyzing sentiment for '{input_text}': {str(e)}")

if __name__ == "__main__":
    try:
        print("🚀 Starting Enhanced NLP Demo...")
        demo_enhanced_nlp()
        demo_spell_correction()
        demo_language_detection()
        demo_entity_extraction()
        demo_sentiment_analysis()
        print("\n✅ All demos completed successfully!")

    except Exception as e:
        print(f"\n❌ Error during demo: {str(e)}")
        import traceback
        traceback.print_exc()
