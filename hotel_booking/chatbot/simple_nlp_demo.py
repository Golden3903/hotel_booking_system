# Simple NLP Demo - Showcasing Enhanced Features
# 简单的NLP演示 - 展示增强功能

import re
import logging
from typing import Dict, List, Any
from datetime import datetime
from difflib import SequenceMatcher

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SimpleNLPDemo:
    """
    Simplified demo of NLP enhancements for hotel chatbot.
    """
    
    def __init__(self):
        # Spell correction dictionary
        self.spell_corrections = {
            'bokking': 'booking', 'resevation': 'reservation', 'accomodation': 'accommodation',
            'availabe': 'available', 'facilites': 'facilities', 'restarant': 'restaurant',
            'swiming': 'swimming', 'breakfest': 'breakfast', 'chekout': 'checkout',
            'chekin': 'checkin', 'delux': 'deluxe', 'standart': 'standard'
        }
        
        # Intent patterns
        self.intent_patterns = {
            "booking_intent": [
                r"(?:book|reserve|make.*reservation|want.*room)",
                r"(?:预订|订房|要.*房间|想.*住)",
                r"(?:available|vacancy|free.*room)"
            ],
            "room_inquiry": [
                r"(?:what|tell me about|describe|show me).*(?:room|accommodation)",
                r"(?:room|accommodation).*(?:type|option|available|choice)",
                r"(?:有什么|介绍一下).*(?:房间|房型)"
            ],
            "amenity_inquiry": [
                r"(?:what|do you have|tell me about).*(?:amenities|facilities|services)",
                r"(?:pool|gym|spa|restaurant|wifi|breakfast)",
                r"(?:有什么|提供).*(?:设施|服务|便利)"
            ],
            "price_inquiry": [
                r"(?:how much|price|cost|rate|fee|charge)",
                r"(?:多少钱|价格|费用|收费)",
                r"(?:expensive|cheap|affordable|budget)"
            ],
            "complaint": [
                r"(?:problem|issue|complaint|wrong|not working|broken)",
                r"(?:问题|投诉|不满意|坏了|不能用)",
                r"(?:dirty|noisy|cold|hot|uncomfortable)"
            ]
        }
        
        # Conversation context
        self.conversation_context = {}
    
    def preprocess_text(self, text: str) -> str:
        """Preprocess text with spell correction."""
        words = text.lower().split()
        corrected_words = []
        
        for word in words:
            clean_word = re.sub(r'[^\w]', '', word)
            if clean_word in self.spell_corrections:
                corrected_words.append(self.spell_corrections[clean_word])
                print(f"   🔧 Corrected: '{clean_word}' → '{self.spell_corrections[clean_word]}'")
            else:
                corrected_words.append(word)
        
        return ' '.join(corrected_words)
    
    def detect_language(self, text: str) -> str:
        """Simple language detection."""
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
        return 'zh' if chinese_chars > len(text) * 0.3 else 'en'
    
    def detect_intent(self, text: str) -> Dict[str, Any]:
        """Detect user intent."""
        text_lower = text.lower()
        best_intent = {"name": "general_inquiry", "confidence": 0.3}
        
        for intent_name, patterns in self.intent_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text_lower):
                    confidence = 0.9
                    if confidence > best_intent["confidence"]:
                        best_intent = {"name": intent_name, "confidence": confidence}
                        break
        
        return best_intent
    
    def extract_entities(self, text: str) -> Dict[str, List[str]]:
        """Extract entities from text."""
        entities = {
            "room_types": [],
            "amenities": [],
            "numbers": [],
            "special_requests": []
        }
        
        text_lower = text.lower()
        
        # Room types
        room_patterns = {
            "standard": ["standard", "basic", "regular"],
            "deluxe": ["deluxe", "luxury", "premium"],
            "suite": ["suite", "executive", "presidential"],
            "single": ["single", "solo", "one person"],
            "double": ["double", "twin", "two bed"],
            "family": ["family", "connecting", "adjoining"]
        }
        
        for room_type, keywords in room_patterns.items():
            if any(keyword in text_lower for keyword in keywords):
                entities["room_types"].append(room_type)
        
        # Amenities
        amenity_keywords = ["pool", "gym", "spa", "restaurant", "wifi", "breakfast", "parking"]
        for amenity in amenity_keywords:
            if amenity in text_lower:
                entities["amenities"].append(amenity)
        
        # Numbers
        numbers = re.findall(r'\b\d+\b', text)
        entities["numbers"].extend(numbers)
        
        # Special requests
        special_patterns = ["quiet room", "high floor", "city view", "non-smoking"]
        for pattern in special_patterns:
            if pattern in text_lower:
                entities["special_requests"].append(pattern)
        
        return entities
    
    def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """Analyze sentiment."""
        positive_words = ["good", "great", "excellent", "wonderful", "amazing", "perfect", "love", "happy"]
        negative_words = ["bad", "terrible", "awful", "horrible", "disappointed", "angry", "hate", "upset"]
        
        text_lower = text.lower()
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        
        if negative_count > positive_count:
            return {"label": "negative", "confidence": 0.8}
        elif positive_count > negative_count:
            return {"label": "positive", "confidence": 0.8}
        else:
            return {"label": "neutral", "confidence": 0.6}
    
    def generate_response(self, analysis: Dict) -> str:
        """Generate response based on analysis."""
        intent = analysis["intent"]["name"]
        sentiment = analysis["sentiment"]["label"]
        entities = analysis["entities"]
        
        # Start with appropriate greeting
        if sentiment == "negative":
            response = "I sincerely apologize for any inconvenience. "
        else:
            response = "Thank you for contacting us! "
        
        # Generate content based on intent
        if intent == "booking_intent":
            response += "I'd be delighted to help you with your reservation. "
            if entities.get("room_types"):
                room_type = entities["room_types"][0]
                response += f"I see you're interested in our {room_type} rooms. "
            response += "Could you please provide your check-in and check-out dates?"
            
        elif intent == "room_inquiry":
            response += "We offer several room types: Standard (RM 132/night), Deluxe (RM 205/night), and Executive Suite (RM 321/night). "
            if entities.get("room_types"):
                room_type = entities["room_types"][0]
                response += f"Our {room_type} rooms are particularly popular with guests."
                
        elif intent == "amenity_inquiry":
            response += "Our hotel features an outdoor pool, fitness center, spa, restaurant, and complimentary WiFi. "
            if entities.get("amenities"):
                amenity = entities["amenities"][0]
                if amenity == "pool":
                    response += "Our infinity pool is open 6 AM to 10 PM with poolside service."
                elif amenity == "gym":
                    response += "Our 24-hour fitness center has modern equipment and personal trainers."
                    
        elif intent == "price_inquiry":
            response += "Our rates vary by season: Standard rooms from RM 132, Deluxe from RM 205, and Suites from RM 321 per night. All rates include breakfast and WiFi."
            
        elif intent == "complaint":
            response = "I sincerely apologize for this issue. Your satisfaction is our priority. Could you please provide more details so I can resolve this immediately?"
            
        else:
            response += "I'm here to help with any questions about our hotel services, reservations, or facilities."
        
        return response
    
    def demo_conversation(self, user_input: str, user_id: str = "demo_user") -> Dict:
        """Demo a complete conversation analysis."""
        print(f"\n🗣️  User Input: '{user_input}'")
        
        # Preprocess
        processed_text = self.preprocess_text(user_input)
        if processed_text != user_input.lower():
            print(f"📝 Processed: '{processed_text}'")
        
        # Language detection
        language = self.detect_language(user_input)
        print(f"🌐 Language: {language}")
        
        # Intent detection
        intent = self.detect_intent(processed_text)
        print(f"🎯 Intent: {intent['name']} (confidence: {intent['confidence']:.2f})")
        
        # Entity extraction
        entities = self.extract_entities(processed_text)
        if any(entities.values()):
            print("🏷️  Entities:")
            for entity_type, values in entities.items():
                if values:
                    print(f"   - {entity_type}: {values}")
        
        # Sentiment analysis
        sentiment = self.analyze_sentiment(processed_text)
        print(f"😊 Sentiment: {sentiment['label']} (confidence: {sentiment['confidence']:.2f})")
        
        # Generate response
        analysis = {
            "intent": intent,
            "entities": entities,
            "sentiment": sentiment,
            "language": language
        }
        
        response = self.generate_response(analysis)
        print(f"🤖 Response: {response}")
        
        return analysis

def main():
    """Run the NLP demo."""
    print("🚀 Hotel Chatbot Enhanced NLP Demo")
    print("=" * 60)
    
    demo = SimpleNLPDemo()
    
    # Test cases
    test_cases = [
        "Hi, I want to book a delux room for 2 nights",
        "What facilites do you have?",
        "How much does a standard room cost?",
        "你好，我想预订房间",
        "I'm very disappointed with the service",
        "Do you have availabe rooms with city view?",
        "I need a quiet room on high floor for 3 people"
    ]
    
    for i, test_input in enumerate(test_cases, 1):
        print(f"\n📋 Test Case {i}:")
        print("-" * 40)
        demo.demo_conversation(test_input)
        print("=" * 60)
    
    print("\n✅ Demo completed successfully!")

if __name__ == "__main__":
    main()
