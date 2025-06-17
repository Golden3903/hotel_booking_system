# NLP Enhancement Features for Hotel Chatbot
# 酒店聊天机器人NLP增强功能

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import re

logger = logging.getLogger(__name__)

class NLPEnhancementManager:
    """
    Manager class for additional NLP enhancement features.
    Provides context-aware conversation management, semantic similarity matching,
    and intelligent response generation.
    """
    
    def __init__(self, advanced_nlp_processor):
        self.nlp_processor = advanced_nlp_processor
        self.conversation_memory = {}
        self.user_preferences = {}
        self.semantic_cache = {}
        
    def enhance_user_understanding(self, user_input: str, user_id: str = None, context: Dict = None) -> Dict[str, Any]:
        """
        Comprehensive user input understanding with context and memory.
        """
        # Get basic analysis
        analysis = self.nlp_processor.analyze_user_input(user_input, context)
        
        # Add user-specific context
        if user_id:
            analysis = self._add_user_context(analysis, user_id)
        
        # Enhance with semantic understanding
        analysis = self._add_semantic_understanding(analysis)
        
        # Add conversation flow analysis
        analysis = self._analyze_conversation_flow(analysis, user_id)
        
        return analysis
    
    def _add_user_context(self, analysis: Dict, user_id: str) -> Dict:
        """Add user-specific context and preferences."""
        if user_id not in self.user_preferences:
            self.user_preferences[user_id] = {
                'preferred_room_type': None,
                'budget_range': None,
                'special_needs': [],
                'language_preference': 'en',
                'interaction_history': []
            }
        
        user_prefs = self.user_preferences[user_id]
        
        # Update language preference based on current input
        if analysis.get('language'):
            user_prefs['language_preference'] = analysis['language']
        
        # Infer preferences from entities
        entities = analysis.get('entities', {})
        if entities.get('room_types'):
            user_prefs['preferred_room_type'] = entities['room_types'][0]
        
        # Add to interaction history
        user_prefs['interaction_history'].append({
            'timestamp': datetime.now().isoformat(),
            'intent': analysis.get('intent', {}).get('name'),
            'entities': entities,
            'sentiment': analysis.get('sentiment', {}).get('label')
        })
        
        # Keep only last 20 interactions
        if len(user_prefs['interaction_history']) > 20:
            user_prefs['interaction_history'] = user_prefs['interaction_history'][-20:]
        
        analysis['user_context'] = user_prefs
        return analysis
    
    def _add_semantic_understanding(self, analysis: Dict) -> Dict:
        """Add semantic similarity and understanding."""
        text = analysis.get('processed_text', analysis.get('original_text', ''))
        
        # Check for similar previous queries
        similar_queries = self._find_similar_queries(text)
        if similar_queries:
            analysis['similar_queries'] = similar_queries
        
        # Add semantic intent confidence
        analysis['semantic_confidence'] = self._calculate_semantic_confidence(analysis)
        
        return analysis
    
    def _find_similar_queries(self, text: str) -> List[Dict]:
        """Find semantically similar previous queries."""
        # This would use sentence transformers for semantic similarity
        # For now, using simple keyword matching
        similar = []
        
        # Simple keyword-based similarity (can be enhanced with sentence transformers)
        keywords = set(text.lower().split())
        
        for cached_query, cached_data in self.semantic_cache.items():
            cached_keywords = set(cached_query.lower().split())
            similarity = len(keywords.intersection(cached_keywords)) / len(keywords.union(cached_keywords))
            
            if similarity > 0.5:  # Threshold for similarity
                similar.append({
                    'query': cached_query,
                    'similarity': similarity,
                    'previous_response': cached_data.get('response'),
                    'intent': cached_data.get('intent')
                })
        
        return sorted(similar, key=lambda x: x['similarity'], reverse=True)[:3]
    
    def _calculate_semantic_confidence(self, analysis: Dict) -> float:
        """Calculate overall semantic understanding confidence."""
        intent_conf = analysis.get('intent', {}).get('confidence', 0.0)
        sentiment_conf = analysis.get('sentiment', {}).get('confidence', 0.0)
        entity_score = min(1.0, len(analysis.get('entities', {})) * 0.2)
        
        # Boost confidence if we have similar queries
        similarity_boost = 0.1 if analysis.get('similar_queries') else 0.0
        
        return min(1.0, (intent_conf * 0.5 + sentiment_conf * 0.2 + entity_score * 0.2 + similarity_boost))
    
    def _analyze_conversation_flow(self, analysis: Dict, user_id: str = None) -> Dict:
        """Analyze conversation flow and context."""
        if not user_id or user_id not in self.conversation_memory:
            if user_id:
                self.conversation_memory[user_id] = {
                    'conversation_state': 'greeting',
                    'pending_information': [],
                    'conversation_turns': 0,
                    'last_intent': None
                }
            analysis['conversation_flow'] = {'state': 'new_conversation'}
            return analysis
        
        memory = self.conversation_memory[user_id]
        memory['conversation_turns'] += 1
        
        current_intent = analysis.get('intent', {}).get('name')
        
        # Determine conversation state
        if current_intent == 'booking_intent':
            memory['conversation_state'] = 'booking_process'
        elif current_intent in ['room_inquiry', 'amenity_inquiry', 'price_inquiry']:
            memory['conversation_state'] = 'information_gathering'
        elif current_intent == 'complaint':
            memory['conversation_state'] = 'service_recovery'
        
        # Check for missing information in booking process
        if memory['conversation_state'] == 'booking_process':
            entities = analysis.get('entities', {})
            required_info = ['dates', 'room_types', 'numbers']
            missing_info = [info for info in required_info if not entities.get(info)]
            memory['pending_information'] = missing_info
        
        memory['last_intent'] = current_intent
        
        analysis['conversation_flow'] = {
            'state': memory['conversation_state'],
            'turns': memory['conversation_turns'],
            'pending_info': memory['pending_information'],
            'context_continuity': memory['last_intent'] == current_intent
        }
        
        return analysis
    
    def generate_contextual_response(self, analysis: Dict, user_id: str = None) -> str:
        """Generate contextually aware response."""
        # Use the enhanced analysis to generate better responses
        base_response = self.nlp_processor.generate_professional_response(analysis)
        
        # Add contextual enhancements
        if user_id and user_id in self.user_preferences:
            user_prefs = self.user_preferences[user_id]
            
            # Personalize based on language preference
            if user_prefs['language_preference'] == 'zh':
                base_response = self._add_chinese_elements(base_response)
            
            # Add personalized touches
            if user_prefs.get('preferred_room_type'):
                room_type = user_prefs['preferred_room_type']
                if 'room' in base_response.lower() and room_type not in base_response.lower():
                    base_response += f" Based on your previous interest, I'd particularly recommend our {room_type} rooms."
        
        # Add conversation flow context
        flow = analysis.get('conversation_flow', {})
        if flow.get('pending_info'):
            missing = ', '.join(flow['pending_info'])
            base_response += f" To complete your booking, I'll need information about: {missing}."
        
        # Cache the response for future similarity matching
        original_text = analysis.get('original_text', '')
        if original_text:
            self.semantic_cache[original_text] = {
                'response': base_response,
                'intent': analysis.get('intent', {}).get('name'),
                'timestamp': datetime.now().isoformat()
            }
        
        return base_response
    
    def _add_chinese_elements(self, response: str) -> str:
        """Add Chinese language elements to response."""
        # Simple bilingual response enhancement
        chinese_greetings = {
            "Good day": "您好",
            "Hello": "您好",
            "Thank you": "谢谢",
            "Welcome": "欢迎"
        }
        
        for english, chinese in chinese_greetings.items():
            if english in response:
                response = response.replace(english, f"{chinese} ({english})")
                break
        
        return response
    
    def get_conversation_summary(self, user_id: str) -> Dict:
        """Get summary of user's conversation and preferences."""
        if user_id not in self.user_preferences:
            return {"status": "no_history"}
        
        prefs = self.user_preferences[user_id]
        memory = self.conversation_memory.get(user_id, {})
        
        return {
            "user_id": user_id,
            "conversation_turns": memory.get('conversation_turns', 0),
            "current_state": memory.get('conversation_state', 'unknown'),
            "preferred_room_type": prefs.get('preferred_room_type'),
            "language_preference": prefs.get('language_preference'),
            "recent_intents": [h.get('intent') for h in prefs.get('interaction_history', [])[-5:]],
            "pending_information": memory.get('pending_information', [])
        }
    
    def reset_conversation(self, user_id: str):
        """Reset conversation state for a user."""
        if user_id in self.conversation_memory:
            del self.conversation_memory[user_id]
        
        # Keep user preferences but reset interaction history
        if user_id in self.user_preferences:
            self.user_preferences[user_id]['interaction_history'] = []
