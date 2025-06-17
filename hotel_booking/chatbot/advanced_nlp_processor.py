# Advanced NLP Processor for Hotel Chatbot
# 高级自然语言处理器 - 让聊天机器人更像真正的酒店客服

import re
import logging
import json
import pickle
import os
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from difflib import SequenceMatcher
from collections import defaultdict

# Optional imports for advanced features
try:
    import spacy
    from spacy.matcher import Matcher
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False

try:
    from transformers import pipeline, AutoTokenizer, AutoModel
    import torch
    from sentence_transformers import SentenceTransformer
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    import numpy as np
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

from .hotel_knowledge_base import HotelKnowledgeBase

logger = logging.getLogger(__name__)

class AdvancedNLPProcessor:
    """
    Advanced NLP processor that makes the chatbot respond like a professional hotel customer service representative.
    """

    def __init__(self):
        # Initialize knowledge base
        self.knowledge_base = HotelKnowledgeBase()

        # Initialize spaCy models if available
        if SPACY_AVAILABLE:
            try:
                # Try to load English model first
                self.nlp_en = spacy.load("en_core_web_sm")
                self.matcher_en = Matcher(self.nlp_en.vocab)
                self._setup_entity_patterns()
                logger.info("English spaCy model loaded successfully")
            except OSError:
                logger.warning("English spaCy model not found, using basic processing")
                self.nlp_en = None
                self.matcher_en = None

            try:
                # Try to load Chinese model
                self.nlp_zh = spacy.load("zh_core_web_sm")
                logger.info("Chinese spaCy model loaded successfully")
            except OSError:
                logger.warning("Chinese spaCy model not found")
                self.nlp_zh = None
        else:
            self.nlp_en = None
            self.nlp_zh = None
            self.matcher_en = None

        # Initialize advanced models if available
        if TRANSFORMERS_AVAILABLE:
            try:
                self.sentiment_analyzer = pipeline("sentiment-analysis")
                logger.info("Sentiment analyzer loaded successfully")
            except Exception as e:
                logger.warning(f"Could not load sentiment analyzer: {str(e)}")
                self.sentiment_analyzer = None

            # Initialize sentence transformer for semantic similarity
            try:
                self.sentence_model = SentenceTransformer('all-MiniLM-L6-v2')
                logger.info("Sentence transformer loaded successfully")
            except Exception as e:
                logger.warning(f"Could not load sentence transformer: {str(e)}")
                self.sentence_model = None
        else:
            self.sentiment_analyzer = None
            self.sentence_model = None

        # Initialize TF-IDF vectorizer for similarity matching
        if SKLEARN_AVAILABLE:
            self.tfidf_vectorizer = TfidfVectorizer(stop_words='english', max_features=1000)
            self.intent_vectors = None
            self._setup_intent_similarity()

        # Enhanced conversation context
        self.conversation_context = {
            'previous_intents': [],
            'extracted_entities': {},
            'user_preferences': {},
            'conversation_flow': [],
            'context_entities': defaultdict(list)
        }

        # Spell correction dictionary
        self.spell_corrections = {
            'bokking': 'booking', 'resevation': 'reservation', 'accomodation': 'accommodation',
            'availabe': 'available', 'facilites': 'facilities', 'restarant': 'restaurant',
            'swiming': 'swimming', 'breakfest': 'breakfast', 'chekout': 'checkout',
            'chekin': 'checkin', 'delux': 'deluxe', 'standart': 'standard'
        }

        # Professional hotel service phrases
        self.professional_phrases = {
            "greeting": [
                "Good day! Welcome to Grand Luxury Hotel. How may I assist you today?",
                "Hello and welcome! I'm here to help you with your hotel needs. What can I do for you?",
                "Greetings! Thank you for choosing Grand Luxury Hotel. How may I be of service?",
                "您好！欢迎来到豪华大酒店。今天我能为您做些什么？",
                "您好！很高兴为您服务。请问有什么可以帮助您的吗？"
            ],
            "acknowledgment": [
                "Certainly, I'd be delighted to help you with that.",
                "Of course! I'll be happy to assist you.",
                "Absolutely! Let me help you with that right away.",
                "当然可以！我很乐意为您处理这件事。",
                "没问题！我马上为您安排。"
            ],
            "apology": [
                "I sincerely apologize for any inconvenience.",
                "I'm terribly sorry about that. Let me make it right for you.",
                "Please accept my apologies. I'll resolve this immediately.",
                "非常抱歉给您带来不便。",
                "我深表歉意，让我立即为您解决这个问题。"
            ],
            "clarification": [
                "Could you please provide a bit more detail about that?",
                "I want to ensure I understand correctly. Could you elaborate?",
                "To better assist you, may I ask for some additional information?",
                "为了更好地为您服务，能否请您详细说明一下？",
                "请问您能提供更多细节吗？这样我能更好地帮助您。"
            ]
        }

        # Intent patterns with confidence scoring
        self.intent_patterns = {
            "room_inquiry": {
                "patterns": [
                    r"(?:what|tell me about|describe|show me).*(?:room|accommodation)",
                    r"(?:room|accommodation).*(?:type|option|available|choice)",
                    r"(?:有什么|介绍一下).*(?:房间|房型)",
                    r"(?:房间|房型).*(?:类型|选择|有哪些)"
                ],
                "confidence": 0.9
            },
            "amenity_inquiry": {
                "patterns": [
                    r"(?:what|do you have|tell me about).*(?:amenities|facilities|services)",
                    r"(?:pool|gym|spa|restaurant|wifi|breakfast)",
                    r"(?:有什么|提供).*(?:设施|服务|便利)",
                    r"(?:游泳池|健身房|餐厅|早餐|WiFi)"
                ],
                "confidence": 0.85
            },
            "location_inquiry": {
                "patterns": [
                    r"(?:where|location|address|how to get|direction)",
                    r"(?:near|close to|distance|far from).*(?:airport|city|center)",
                    r"(?:在哪里|地址|位置|怎么去)",
                    r"(?:距离|离).*(?:机场|市中心|景点)"
                ],
                "confidence": 0.9
            },
            "price_inquiry": {
                "patterns": [
                    r"(?:how much|price|cost|rate|fee|charge)",
                    r"(?:多少钱|价格|费用|收费)",
                    r"(?:expensive|cheap|affordable|budget)"
                ],
                "confidence": 0.95
            },
            "booking_intent": {
                "patterns": [
                    r"(?:book|reserve|make.*reservation|want.*room)",
                    r"(?:预订|订房|要.*房间|想.*住)",
                    r"(?:available|vacancy|free.*room)"
                ],
                "confidence": 0.9
            },
            "check_booking_status": {
                "patterns": [
                    r"(?:did i book|check.*booking|booking.*status|my.*reservation)",
                    r"(?:我有预订吗|查看.*预订|预订.*状态|我的.*订单)",
                    r"(?:booking.*id|reservation.*number|order.*number)",
                    r"(?:successful.*reservation|make.*successful)"
                ],
                "confidence": 0.9
            },
            "hotel_info": {
                "patterns": [
                    r"(?:check.*in.*time|what.*time.*check)",
                    r"(?:wi.*fi|wifi|internet)",
                    r"(?:breakfast.*time|when.*breakfast)",
                    r"(?:check.*out.*time|checkout.*time)",
                    r"(?:入住时间|退房时间|早餐时间|网络)"
                ],
                "confidence": 0.9
            },
            "feedback_rating": {
                "patterns": [
                    r"(?:feedback|rating|review|satisfaction)",
                    r"(?:give.*rating|rate.*stay|how.*satisfied)",
                    r"(?:反馈|评价|评分|满意度)",
                    r"(?:very.*satisfied|disappointed|excellent.*service)"
                ],
                "confidence": 0.85
            },
            "cancel_booking": {
                "patterns": [
                    r"(?:cancel.*reservation|cancel.*booking|cancel.*order)",
                    r"(?:not.*going|don't.*need|want.*cancel)",
                    r"(?:取消.*预订|取消.*订单|不去了)",
                    r"(?:cancel.*room|refund)"
                ],
                "confidence": 0.95
            },
            "upgrade_room": {
                "patterns": [
                    r"(?:upgrade.*room|upgrade.*to|change.*to.*better)",
                    r"(?:executive.*suite|deluxe.*room|better.*room)",
                    r"(?:升级.*房间|换.*更好|升级.*到)",
                    r"(?:upgrade.*from.*standard|upgrade.*from.*deluxe)"
                ],
                "confidence": 0.9
            },
            "extend_stay": {
                "patterns": [
                    r"(?:extend.*stay|stay.*longer|one.*more.*day)",
                    r"(?:check.*out.*later|延长.*住宿|多住.*天)",
                    r"(?:extend.*to|until.*friday|stay.*until)",
                    r"(?:延期.*到|住到.*号|多住.*晚)"
                ],
                "confidence": 0.9
            },
            "book_another_room": {
                "patterns": [
                    r"(?:book.*another.*room|add.*another.*room|one.*more.*room)",
                    r"(?:additional.*room|extra.*room|second.*room)",
                    r"(?:再订.*房间|加订.*房间|多订.*间)",
                    r"(?:book.*one.*more|need.*another)"
                ],
                "confidence": 0.9
            },
            "modify_booking_date": {
                "patterns": [
                    r"(?:change.*date|modify.*date|postpone.*booking)",
                    r"(?:change.*check.*in|different.*date|move.*to)",
                    r"(?:修改.*日期|改.*时间|推迟.*预订)",
                    r"(?:换个.*日期|改到.*号|延后.*天)"
                ],
                "confidence": 0.9
            },
            "addon_services": {
                "patterns": [
                    r"(?:breakfast.*service|airport.*transfer|additional.*service)",
                    r"(?:add.*breakfast|need.*transfer|extra.*service)",
                    r"(?:早餐.*服务|机场.*接送|额外.*服务)",
                    r"(?:shuttle.*service|pickup.*service|transport)"
                ],
                "confidence": 0.85
            },
            "non_hotel_topic": {
                "patterns": [
                    r"(?:will.*you.*fall.*in.*love|how.*ai.*works|what.*time.*is.*it)",
                    r"(?:what.*do.*you.*like.*eat|weather.*today|rain.*malaysia)",
                    r"(?:你会.*恋爱吗|人工智能.*工作|现在.*几点)",
                    r"(?:你喜欢.*吃|今天.*天气|会.*下雨)"
                ],
                "confidence": 0.8
            },
            "complaint": {
                "patterns": [
                    r"(?:problem|issue|complaint|wrong|not working|broken)",
                    r"(?:问题|投诉|不满意|坏了|不能用)",
                    r"(?:dirty|noisy|cold|hot|uncomfortable)"
                ],
                "confidence": 0.95
            }
        }

    def _setup_entity_patterns(self):
        """Setup spaCy matcher patterns for better entity recognition."""
        if not self.matcher_en:
            return

        # Room type patterns
        room_patterns = [
            [{"LOWER": {"IN": ["standard", "deluxe", "executive", "suite", "single", "double", "twin"]}},
             {"LOWER": "room", "OP": "?"}],
            [{"LOWER": {"IN": ["presidential", "luxury", "premium"]}},
             {"LOWER": {"IN": ["suite", "room"]}}]
        ]
        self.matcher_en.add("ROOM_TYPE", room_patterns)

        # Date patterns
        date_patterns = [
            [{"LOWER": {"IN": ["check", "checkin", "check-in"]}},
             {"LOWER": {"IN": ["in", "on"]}, "OP": "?"},
             {"ENT_TYPE": "DATE"}],
            [{"LOWER": {"IN": ["checkout", "check-out", "leaving"]}},
             {"LOWER": {"IN": ["on", "at"]}, "OP": "?"},
             {"ENT_TYPE": "DATE"}]
        ]
        self.matcher_en.add("BOOKING_DATE", date_patterns)

    def _setup_intent_similarity(self):
        """Setup intent similarity matching using TF-IDF."""
        if not SKLEARN_AVAILABLE:
            return

        # Sample training data for intent classification
        intent_examples = {
            "room_inquiry": [
                "what rooms do you have", "tell me about your rooms", "room types available",
                "what kind of accommodation", "show me room options"
            ],
            "booking_intent": [
                "I want to book a room", "make a reservation", "book accommodation",
                "reserve a room", "I need a room", "availability check"
            ],
            "amenity_inquiry": [
                "what facilities do you have", "hotel amenities", "do you have a pool",
                "restaurant information", "gym facilities", "spa services"
            ],
            "price_inquiry": [
                "how much does it cost", "room rates", "pricing information",
                "what are your prices", "cost per night", "room charges"
            ]
        }

        # Prepare training data
        texts = []
        labels = []
        for intent, examples in intent_examples.items():
            texts.extend(examples)
            labels.extend([intent] * len(examples))

        try:
            self.intent_vectors = self.tfidf_vectorizer.fit_transform(texts)
            self.intent_labels = labels
            logger.info("Intent similarity model initialized successfully")
        except Exception as e:
            logger.warning(f"Could not initialize intent similarity: {str(e)}")

    def preprocess_text(self, text: str) -> str:
        """Preprocess text with spell correction and normalization."""
        # Basic spell correction
        words = text.lower().split()
        corrected_words = []

        for word in words:
            # Remove punctuation for checking
            clean_word = re.sub(r'[^\w]', '', word)
            if clean_word in self.spell_corrections:
                corrected_words.append(self.spell_corrections[clean_word])
            else:
                corrected_words.append(word)

        return ' '.join(corrected_words)

    def detect_language(self, text: str) -> str:
        """Detect the language of the input text."""
        try:
            from langdetect import detect
            lang = detect(text)
            return 'zh' if lang == 'zh-cn' or lang == 'zh' else 'en'
        except:
            # Fallback: simple heuristic
            chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
            return 'zh' if chinese_chars > len(text) * 0.3 else 'en'

    def get_nlp_model(self, text: str):
        """Get appropriate spaCy model based on language detection."""
        lang = self.detect_language(text)
        if lang == 'zh' and self.nlp_zh:
            return self.nlp_zh
        elif self.nlp_en:
            return self.nlp_en
        return None

    def analyze_user_input(self, text: str, context: Dict = None) -> Dict[str, Any]:
        """
        Comprehensive analysis of user input including intent, entities, sentiment, and context.
        Enhanced with preprocessing, context awareness, and improved accuracy.
        """
        # Preprocess text
        processed_text = self.preprocess_text(text)

        # Update conversation context
        self._update_conversation_context(processed_text, context)

        analysis = {
            "original_text": text,
            "processed_text": processed_text,
            "language": self.detect_language(text),
            "intent": self.detect_intent_enhanced(processed_text),
            "entities": self.extract_entities_enhanced(processed_text),
            "sentiment": self.analyze_sentiment_enhanced(processed_text),
            "context": context or {},
            "response_type": "informational",
            "confidence_score": 0.0
        }

        # Add context-aware entity resolution
        analysis["entities"] = self._resolve_context_entities(analysis["entities"])

        # Determine response type based on intent
        if analysis["intent"]["name"] == "complaint":
            analysis["response_type"] = "service_recovery"
        elif analysis["intent"]["name"] == "booking_intent":
            analysis["response_type"] = "booking_assistance"
        elif "inquiry" in analysis["intent"]["name"]:
            analysis["response_type"] = "informational"

        # Calculate overall confidence score
        analysis["confidence_score"] = (
            analysis["intent"]["confidence"] * 0.6 +
            analysis["sentiment"]["confidence"] * 0.2 +
            (len(analysis["entities"]) > 0) * 0.2
        )

        return analysis

    def _update_conversation_context(self, text: str, context: Dict = None):
        """Update conversation context with current input."""
        self.conversation_context['conversation_flow'].append({
            'text': text,
            'timestamp': datetime.now().isoformat(),
            'context': context or {}
        })

        # Keep only last 10 conversation turns
        if len(self.conversation_context['conversation_flow']) > 10:
            self.conversation_context['conversation_flow'] = \
                self.conversation_context['conversation_flow'][-10:]

    def _resolve_context_entities(self, entities: Dict) -> Dict:
        """Resolve entities using conversation context."""
        # If no dates found but previous context has dates, use them
        if not entities.get('dates') and self.conversation_context['extracted_entities'].get('dates'):
            entities['dates'] = self.conversation_context['extracted_entities']['dates'][-2:]

        # Update context with new entities
        for entity_type, values in entities.items():
            if values:
                self.conversation_context['extracted_entities'][entity_type] = values

        return entities

    def detect_intent_enhanced(self, text: str) -> Dict[str, Any]:
        """
        Enhanced intent detection combining pattern matching, TF-IDF similarity, and context.
        """
        # First try pattern-based detection
        pattern_intent = self.detect_intent_advanced(text)

        # Try TF-IDF similarity if available
        similarity_intent = self._detect_intent_similarity(text)

        # Combine results
        if similarity_intent and similarity_intent["confidence"] > pattern_intent["confidence"]:
            best_intent = similarity_intent
        else:
            best_intent = pattern_intent

        # Apply context boost
        if self.conversation_context['previous_intents']:
            last_intent = self.conversation_context['previous_intents'][-1]
            if last_intent == best_intent["name"]:
                best_intent["confidence"] = min(0.95, best_intent["confidence"] + 0.1)

        # Update context
        self.conversation_context['previous_intents'].append(best_intent["name"])
        if len(self.conversation_context['previous_intents']) > 5:
            self.conversation_context['previous_intents'] = \
                self.conversation_context['previous_intents'][-5:]

        return best_intent

    def detect_intent_advanced(self, text: str) -> Dict[str, Any]:
        """
        Advanced intent detection with confidence scoring and context awareness.
        """
        text_lower = text.lower()
        best_intent = {"name": "general_inquiry", "confidence": 0.3}

        for intent_name, intent_data in self.intent_patterns.items():
            max_confidence = 0
            for pattern in intent_data["patterns"]:
                if re.search(pattern, text_lower):
                    confidence = intent_data["confidence"]
                    if confidence > max_confidence:
                        max_confidence = confidence

            if max_confidence > best_intent["confidence"]:
                best_intent = {"name": intent_name, "confidence": max_confidence}

        return best_intent

    def _detect_intent_similarity(self, text: str) -> Optional[Dict[str, Any]]:
        """Detect intent using TF-IDF similarity."""
        if not SKLEARN_AVAILABLE or self.intent_vectors is None:
            return None

        try:
            # Transform input text
            text_vector = self.tfidf_vectorizer.transform([text])

            # Calculate similarities
            similarities = cosine_similarity(text_vector, self.intent_vectors)[0]

            # Find best match
            best_idx = np.argmax(similarities)
            best_score = similarities[best_idx]

            if best_score > 0.3:  # Threshold for similarity
                return {
                    "name": self.intent_labels[best_idx],
                    "confidence": min(0.9, best_score)
                }
        except Exception as e:
            logger.warning(f"Intent similarity detection failed: {str(e)}")

        return None

    def extract_entities_enhanced(self, text: str) -> Dict[str, List[str]]:
        """
        Enhanced entity extraction using spaCy NER, pattern matching, and context.
        """
        entities = {
            "dates": [],
            "room_types": [],
            "numbers": [],
            "locations": [],
            "amenities": [],
            "names": [],
            "duration": [],
            "special_requests": []
        }

        # Get appropriate NLP model
        nlp_model = self.get_nlp_model(text)
        if not nlp_model:
            return self.extract_entities_basic(text)

        doc = nlp_model(text)

        # Extract named entities using spaCy
        for ent in doc.ents:
            if ent.label_ in ["DATE", "TIME"]:
                entities["dates"].append(ent.text)
            elif ent.label_ == "PERSON":
                entities["names"].append(ent.text)
            elif ent.label_ in ["GPE", "LOC"]:  # Geopolitical entity, Location
                entities["locations"].append(ent.text)
            elif ent.label_ in ["CARDINAL", "QUANTITY"]:  # Numbers
                entities["numbers"].append(ent.text)

        # Use spaCy matcher for better pattern recognition
        if self.matcher_en and nlp_model == self.nlp_en:
            matches = self.matcher_en(doc)
            for match_id, start, end in matches:
                span = doc[start:end]
                label = nlp_model.vocab.strings[match_id]
                if label == "ROOM_TYPE":
                    entities["room_types"].append(span.text.lower())
                elif label == "BOOKING_DATE":
                    entities["dates"].append(span.text)

        # Enhanced keyword extraction
        entities.update(self._extract_domain_entities(text))

        # Extract duration patterns
        duration_patterns = [
            r'(\d+)\s*(?:night|nights|day|days)',
            r'(?:for|stay)\s*(\d+)\s*(?:night|nights|day|days)',
            r'(\d+)\s*晚', r'住\s*(\d+)\s*天'
        ]
        for pattern in duration_patterns:
            matches = re.findall(pattern, text.lower())
            entities["duration"].extend(matches)

        # Remove duplicates and clean up
        for key in entities:
            entities[key] = list(set(entities[key]))

        return entities

    def extract_entities_basic(self, text: str) -> Dict[str, List[str]]:
        """Basic entity extraction fallback when spaCy is not available."""
        entities = {
            "dates": [],
            "room_types": [],
            "numbers": [],
            "locations": [],
            "amenities": [],
            "names": [],
            "duration": [],
            "special_requests": []
        }

        # Basic date patterns
        date_patterns = [
            r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b',
            r'\b\d{4}[/-]\d{1,2}[/-]\d{1,2}\b',
            r'\b(?:january|february|march|april|may|june|july|august|september|october|november|december)\s+\d{1,2}\b'
        ]
        for pattern in date_patterns:
            matches = re.findall(pattern, text.lower())
            entities["dates"].extend(matches)

        # Basic number extraction
        number_matches = re.findall(r'\b\d+\b', text)
        entities["numbers"].extend(number_matches)

        # Domain-specific entities
        entities.update(self._extract_domain_entities(text))

        return entities

    def _extract_domain_entities(self, text: str) -> Dict[str, List[str]]:
        """Extract hotel domain-specific entities."""
        entities = {
            "room_types": [],
            "amenities": [],
            "special_requests": []
        }

        text_lower = text.lower()

        # Enhanced room type extraction
        room_patterns = {
            "standard": ["standard", "basic", "regular", "标准"],
            "deluxe": ["deluxe", "luxury", "premium", "豪华"],
            "suite": ["suite", "executive", "presidential", "套房"],
            "single": ["single", "solo", "one person", "单人"],
            "double": ["double", "twin", "two bed", "双人"],
            "family": ["family", "connecting", "adjoining", "家庭"]
        }

        for room_type, keywords in room_patterns.items():
            if any(keyword in text_lower for keyword in keywords):
                entities["room_types"].append(room_type)

        # Enhanced amenity extraction
        amenity_patterns = {
            "pool": ["pool", "swimming", "swim", "游泳池"],
            "gym": ["gym", "fitness", "exercise", "workout", "健身房"],
            "spa": ["spa", "massage", "wellness", "按摩"],
            "restaurant": ["restaurant", "dining", "food", "餐厅"],
            "wifi": ["wifi", "internet", "wireless", "网络"],
            "breakfast": ["breakfast", "morning meal", "早餐"],
            "parking": ["parking", "car park", "garage", "停车"],
            "bar": ["bar", "lounge", "drinks", "酒吧"],
            "concierge": ["concierge", "service", "help desk", "礼宾"]
        }

        for amenity, keywords in amenity_patterns.items():
            if any(keyword in text_lower for keyword in keywords):
                entities["amenities"].append(amenity)

        # Special requests
        special_patterns = [
            "quiet room", "high floor", "low floor", "city view", "sea view",
            "non-smoking", "smoking", "wheelchair accessible", "late checkout",
            "early checkin", "extra bed", "crib", "baby cot"
        ]

        for pattern in special_patterns:
            if pattern in text_lower:
                entities["special_requests"].append(pattern)

        return entities

    def extract_entities(self, text: str) -> Dict[str, List[str]]:
        """
        Legacy method for backward compatibility.
        """
        return self.extract_entities_enhanced(text)

    def analyze_sentiment_enhanced(self, text: str) -> Dict[str, Any]:
        """
        Enhanced sentiment analysis using multiple approaches.
        """
        # Try transformer-based sentiment analysis first
        if self.sentiment_analyzer:
            try:
                result = self.sentiment_analyzer(text)[0]
                # Convert to our format
                label_map = {"POSITIVE": "positive", "NEGATIVE": "negative", "NEUTRAL": "neutral"}
                return {
                    "label": label_map.get(result["label"], "neutral"),
                    "confidence": result["score"],
                    "method": "transformer"
                }
            except Exception as e:
                logger.warning(f"Transformer sentiment analysis failed: {str(e)}")

        # Fallback to keyword-based analysis
        return self.analyze_sentiment_keywords(text)

    def analyze_sentiment_keywords(self, text: str) -> Dict[str, Any]:
        """
        Keyword-based sentiment analysis with enhanced word lists.
        """
        # Enhanced sentiment word lists
        positive_words = [
            "good", "great", "excellent", "wonderful", "amazing", "perfect", "fantastic",
            "love", "like", "happy", "satisfied", "pleased", "impressed", "awesome",
            "brilliant", "outstanding", "superb", "marvelous", "delightful",
            "好", "很好", "棒", "完美", "满意", "喜欢", "开心", "高兴", "不错", "赞"
        ]

        negative_words = [
            "bad", "terrible", "awful", "horrible", "disappointed", "angry", "hate",
            "dislike", "unhappy", "unsatisfied", "frustrated", "annoyed", "upset",
            "disgusting", "pathetic", "useless", "worst", "nightmare",
            "不好", "糟糕", "失望", "生气", "不满意", "讨厌", "烦", "差", "垃圾", "最差"
        ]

        # Intensity modifiers
        intensifiers = ["very", "extremely", "really", "quite", "absolutely", "totally",
                       "非常", "特别", "真的", "太", "超级"]

        text_lower = text.lower()

        # Count sentiment words with intensity consideration
        positive_score = 0
        negative_score = 0

        words = text_lower.split()
        for i, word in enumerate(words):
            # Check for intensifiers
            intensity = 1.0
            if i > 0 and words[i-1] in [w.lower() for w in intensifiers]:
                intensity = 1.5

            if word in positive_words:
                positive_score += intensity
            elif word in negative_words:
                negative_score += intensity

        # Determine sentiment
        total_score = positive_score + negative_score
        if total_score == 0:
            return {"label": "neutral", "confidence": 0.5, "method": "keyword"}

        if negative_score > positive_score:
            confidence = min(0.9, negative_score / total_score + 0.1)
            return {"label": "negative", "confidence": confidence, "method": "keyword"}
        elif positive_score > negative_score:
            confidence = min(0.9, positive_score / total_score + 0.1)
            return {"label": "positive", "confidence": confidence, "method": "keyword"}
        else:
            return {"label": "neutral", "confidence": 0.6, "method": "keyword"}

    def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """
        Legacy method for backward compatibility.
        """
        return self.analyze_sentiment_enhanced(text)

    def generate_professional_response(self, analysis: Dict[str, Any]) -> str:
        """
        Generate professional hotel service responses based on analysis.
        """
        intent = analysis["intent"]["name"]
        sentiment = analysis["sentiment"]["label"]
        entities = analysis["entities"]

        # Start with appropriate greeting/acknowledgment
        if sentiment == "negative":
            response = self._get_random_phrase("apology") + " "
        else:
            response = self._get_random_phrase("acknowledgment") + " "

        # Generate content based on intent
        if intent == "room_inquiry":
            response += self._generate_room_info_response(entities)
        elif intent == "amenity_inquiry":
            response += self._generate_amenity_info_response(entities)
        elif intent == "location_inquiry":
            response += self._generate_location_info_response()
        elif intent == "price_inquiry":
            response += self._generate_price_info_response(entities)
        elif intent == "booking_intent":
            response += self._generate_booking_assistance_response()
        elif intent == "check_booking_status":
            response += self._generate_booking_status_response()
        elif intent == "hotel_info":
            response += self._generate_hotel_info_response(entities)
        elif intent == "feedback_rating":
            response += self._generate_feedback_response()
        elif intent == "cancel_booking":
            response += self._generate_cancel_booking_response()
        elif intent == "upgrade_room":
            response += self._generate_upgrade_room_response()
        elif intent == "extend_stay":
            response += self._generate_extend_stay_response()
        elif intent == "book_another_room":
            response += self._generate_book_another_room_response()
        elif intent == "modify_booking_date":
            response += self._generate_modify_date_response()
        elif intent == "addon_services":
            response += self._generate_addon_services_response(entities)
        elif intent == "non_hotel_topic":
            response = self._generate_redirect_to_hotel_response()
        elif intent == "complaint":
            response = self._generate_service_recovery_response(analysis)
        else:
            response += self._generate_general_assistance_response()

        # Add helpful closing
        response += " Is there anything else I can help you with today?"

        return response

    def _get_random_phrase(self, phrase_type: str) -> str:
        """Get a random professional phrase of the specified type."""
        import random
        phrases = self.professional_phrases.get(phrase_type, [""])
        return random.choice(phrases)

    def _generate_room_info_response(self, entities: Dict) -> str:
        """Generate detailed room information response."""
        room_types = entities.get("room_types", [])

        if room_types:
            # Specific room type inquiry
            room_type = room_types[0].lower()
            room_info = self.knowledge_base.get_room_info(room_type)
            if room_info:
                return f"Our {room_info['name']} features {room_info['size']} of space, accommodating {room_info['capacity']}. The room includes {', '.join(room_info['amenities'][:5])} and more. Rates start from {room_info['price_range']}."

        # General room information
        return "We offer three types of accommodations: Standard Rooms (RM 300-400/night) perfect for business travelers, Deluxe Rooms (RM 500-600/night) with enhanced amenities and views, and Executive Suites (RM 800-1000/night) featuring separate living areas and premium services."

    def _generate_amenity_info_response(self, entities: Dict) -> str:
        """Generate amenity information response."""
        amenities = entities.get("amenities", [])

        if "pool" in amenities or "游泳池" in amenities:
            return "Our outdoor infinity pool is open from 6:00 AM to 10:00 PM, featuring a pool bar, jacuzzi, and children's area with poolside service available."
        elif "gym" in amenities or "健身房" in amenities:
            return "Our 24-hour fitness center offers state-of-the-art cardio and weight training equipment, with personal trainers and group fitness classes available."
        elif "spa" in amenities:
            return "Serenity Spa operates from 9:00 AM to 9:00 PM, offering massage therapy, facial treatments, body treatments, and romantic couples packages."
        elif "restaurant" in amenities or "餐厅" in amenities:
            return "The Grand Dining serves international cuisine from 6:00 AM to 11:00 PM, while our Lobby Café offers 24-hour light meals and artisan coffee. Room service is also available around the clock."

        return "Our hotel features an outdoor infinity pool, 24-hour fitness center, full-service spa, international restaurant, lobby café, business center, and complimentary WiFi throughout the property."

    def _generate_location_info_response(self) -> str:
        """Generate location and directions response."""
        location = self.knowledge_base.get_location_info()
        return f"We're conveniently located at {location['address']} in the heart of {location['city']}. We're just 2.5km from KLCC Twin Towers, 1.8km from Bukit Bintang shopping district, and 45 minutes from KLIA Airport. Our concierge can arrange transportation or provide detailed directions."

    def _generate_price_info_response(self, entities: Dict) -> str:
        """Generate pricing information response."""
        room_types = entities.get("room_types", [])

        if room_types:
            room_type = room_types[0].lower()
            room_info = self.knowledge_base.get_room_info(room_type)
            if room_info:
                return f"Our {room_info['name']} rates range from {room_info['price_range']}, depending on the season and length of stay. This includes complimentary WiFi, breakfast, and access to all hotel facilities."

        return "Our room rates vary by season: Standard Rooms RM 132/night, Deluxe Rooms RM 205/night, and Executive Suites RM 321/night. All rates include complimentary breakfast, WiFi, and facility access."

    def _generate_booking_assistance_response(self) -> str:
        """Generate booking assistance response."""
        return "I'd be delighted to assist you with your reservation. To provide you with the best available options, could you please share your preferred check-in and check-out dates, the type of room you're interested in, and the number of guests?"

    def _generate_service_recovery_response(self, analysis: Dict) -> str:
        """Generate service recovery response for complaints."""
        return "I sincerely apologize for this inconvenience. Your satisfaction is our top priority, and I want to resolve this matter immediately. Could you please provide me with more details about the issue so I can take appropriate action right away? I'll also ensure this doesn't happen again."

    def _generate_booking_status_response(self) -> str:
        """Generate response for booking status inquiry."""
        return "I'd be happy to help you check your booking status. Could you please provide your booking ID or the name under which the reservation was made? This will allow me to quickly locate your reservation details."

    def _generate_hotel_info_response(self, entities: Dict) -> str:
        """Generate response for hotel information inquiries."""
        # Check for specific info requests
        if any(keyword in str(entities).lower() for keyword in ['check', 'checkin', 'check-in']):
            return "Check-in time starts at 2:00 PM. Early check-in may be available upon request, subject to room availability."
        elif any(keyword in str(entities).lower() for keyword in ['checkout', 'check-out']):
            return "Check-out time is before 12:00 PM (noon). Late check-out can be arranged for an additional fee, subject to availability."
        elif any(keyword in str(entities).lower() for keyword in ['wifi', 'internet', 'wi-fi']):
            return "All rooms provide complimentary high-speed Wi-Fi. The network password is provided on your room key card upon check-in."
        elif any(keyword in str(entities).lower() for keyword in ['breakfast time', 'breakfast hours', 'when breakfast']):
            return "Breakfast is served daily from 6:00 AM to 11:00 AM in our main restaurant. We offer both continental and local Malaysian cuisine options."
        else:
            return "Here's some essential hotel information: Check-in is at 2:00 PM, check-out at 12:00 PM, breakfast is served 6:00-11:00 AM, and complimentary Wi-Fi is available throughout the hotel."

    def _generate_feedback_response(self) -> str:
        """Generate response for feedback and rating requests."""
        return "Thank you for taking the time to share your feedback! Your experience matters greatly to us. How would you rate your stay with us on a scale of 1-5 stars? Please feel free to share any specific comments or suggestions - we value your input for continuous improvement."

    def _generate_cancel_booking_response(self) -> str:
        """Generate response for booking cancellation requests."""
        return "I understand you'd like to cancel your reservation. To assist you with this, please provide your booking ID or the name under which the reservation was made. I'll then review the cancellation policy and process your request accordingly."

    def _generate_upgrade_room_response(self) -> str:
        """Generate response for room upgrade requests."""
        return "I'd be delighted to help you upgrade your room! To check available upgrade options, please provide your current booking details. Our upgrade options include: Deluxe Room (+RM73/night) and Executive Suite (+RM189/night). Upgrades are subject to availability."

    def _generate_extend_stay_response(self) -> str:
        """Generate response for stay extension requests."""
        return "I'd be happy to help extend your stay! Please provide your current booking details and let me know until which date you'd like to extend. I'll check room availability and provide you with the additional charges."

    def _generate_book_another_room_response(self) -> str:
        """Generate response for additional room booking requests."""
        return "Certainly! I can help you book an additional room. Would you like the same room type as your current booking, or would you prefer a different type? Please let me know your preferred room type and if the dates should match your existing reservation."

    def _generate_modify_date_response(self) -> str:
        """Generate response for booking date modification requests."""
        return "I can help you modify your booking dates. Please provide your booking ID and let me know the new check-in and check-out dates you prefer. I'll check availability and update your reservation accordingly."

    def _generate_addon_services_response(self, entities: Dict) -> str:
        """Generate response for add-on services requests."""
        if any(keyword in str(entities).lower() for keyword in ['breakfast']):
            return "Our breakfast service is available for RM20 per person per day. It includes a variety of continental and local Malaysian dishes. How many guests would you like to add breakfast service for?"
        elif any(keyword in str(entities).lower() for keyword in ['airport', 'transfer', 'transport']):
            return "Our airport transfer service is available for RM50 (up to 5 passengers). Please provide your flight details including arrival/departure time and flight number so we can schedule the pickup accordingly."
        else:
            return "We offer several add-on services: Breakfast service (RM20/person/day) and Airport transfer (RM50/up to 5 people). Which service would you like to add to your booking?"

    def _generate_redirect_to_hotel_response(self) -> str:
        """Generate response to redirect non-hotel topics back to hotel services."""
        return "I appreciate your question, but I'm specifically designed to assist with hotel services such as room bookings, facility information, reservations management, and guest services. How can I help you with your hotel needs today?"

    def _generate_general_assistance_response(self) -> str:
        """Generate general assistance response."""
        return "I'm here to help you with any questions about our hotel services, room reservations, local attractions, or special arrangements you might need during your stay."
