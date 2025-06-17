import spacy
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from scipy.special import softmax
import torch
import logging
import re
from datetime import datetime, timedelta
import json
import random
import string
from typing import Dict, List, Optional, Tuple, Any

# Import our advanced NLP components
try:
    # Temporarily disable advanced NLP to fix hanging issue
    # from .advanced_nlp_processor import AdvancedNLPProcessor
    # from .hotel_knowledge_base import HotelKnowledgeBase
    # from .nlp_enhancements import NLPEnhancementManager
    ADVANCED_NLP_AVAILABLE = False  # Temporarily disabled
except ImportError:
    ADVANCED_NLP_AVAILABLE = False
    logging.warning("Advanced NLP components not available")
import random
from typing import Dict, Optional, Tuple, List
from langdetect import detect

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DialogManager:
    def __init__(self, intents_file: Optional[str] = None, qr_code_path: str = "/media/payment/QR Bank.jpeg"):
        """
        Initialize the DialogManager for handling conversational interactions.

        Args:
            intents_file (Optional[str]): Path to a JSON file containing intent patterns and responses.
            qr_code_path (str): Path to the QR code image for payment.
        """
        try:
            # Load spaCy English NLP model
            self.nlp = spacy.load("en_core_web_sm")

            # Detect device
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
            logger.info(f"Using device: {self.device}")

            # Initialize sentiment analysis model (lazy-loaded)
            self.tokenizer = None
            self.model = None
            self.sentiment_labels = ['Negative', 'Neutral', 'Positive']

            # Initialize advanced NLP components
            if ADVANCED_NLP_AVAILABLE:
                self.advanced_nlp = AdvancedNLPProcessor()
                self.knowledge_base = HotelKnowledgeBase()
                self.nlp_enhancement_manager = NLPEnhancementManager(self.advanced_nlp)
                logger.info("Advanced NLP components initialized successfully")
            else:
                self.advanced_nlp = None
                self.knowledge_base = None
                self.nlp_enhancement_manager = None
                logger.warning("Using basic NLP functionality only")

            # Conversation state
            self.state = "greeting"
            self.user_data: Dict = {}
            self.conversation_history = []
            self.qr_code_path = qr_code_path

            # Compile regex patterns for performance
            self.date_patterns = [
                re.compile(r'(\d{1,2})[./\-](\d{1,2})[./\-](\d{4})'),  # DD/MM/YYYY
                re.compile(r'(\d{4})[./\-](\d{1,2})[./\-](\d{1,2})'),  # YYYY/MM/DD
                re.compile(r'(next|this)\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday)', re.IGNORECASE),
                re.compile(r'(tomorrow|today|next week)', re.IGNORECASE),
                re.compile(r'(january|february|march|april|may|june|july|august|september|october|november|december)\s+(\d{1,2})(?:st|nd|rd|th)?,?\s*(\d{4})', re.IGNORECASE),
                re.compile(r'(\d{1,2})(?:st|nd|rd|th)?\s+of\s+(january|february|march|april|may|june|july|august|september|october|november|december),?\s*(\d{4})', re.IGNORECASE),
                re.compile(r'(\d+)\s*(?:night|nights)\s*(?:from|starting)\s*(january|february|march|april|may|june|july|august|september|october|november|december)\s*(\d{1,2})(?:st|nd|rd|th)?,?\s*(\d{4})', re.IGNORECASE),
                # Add pattern for "Month Day to Month Day" format
                re.compile(r'(january|february|march|april|may|june|july|august|september|october|november|december)\s+(\d{1,2})(?:st|nd|rd|th)?\s+to\s+(january|february|march|april|may|june|july|august|september|october|november|december)\s+(\d{1,2})(?:st|nd|rd|th)?', re.IGNORECASE),
            ]
            self.email_pattern = re.compile(r'(\S+@\S+\.\S+)')
            self.phone_pattern = re.compile(r'(?:(?:phone|contact|call|tel)(?:\s+(?:number|me))?[:\s]+)?(\+?\d{1,3}[\s-]?\d{3}[\s-]?\d{3}[\s-]?\d{4})', re.IGNORECASE)
            self.single_email_pattern = re.compile(r'^\s*(\S+@\S+\.\S+)\s*$')
            self.single_phone_pattern = re.compile(r'^\s*(\+?\d{1,3}[\s-]?\d{3}[\s-]?\d{3}[\s-]?\d{4})\s*$')
            self.single_date_pattern = re.compile(r'^\s*(\d{1,2})[./\-](\d{1,2})[./\-](\d{4})\s*$')

            # Load intents
            self.intents: Dict = {}
            if intents_file:
                try:
                    with open(intents_file, 'r', encoding='utf-8') as f:
                        intents_data = json.load(f)
                        for intent in intents_data.get('intents', []):
                            intent_name = intent.get('tag')
                            self.intents[intent_name] = {
                                'patterns': intent.get('patterns', []),
                                'responses': {
                                    'en': intent.get('responses', {}).get('en', []),
                                    'zh': intent.get('responses', {}).get('zh', [])
                                }
                            }
                    logger.info(f"Loaded {len(self.intents)} intents from file")
                except Exception as e:
                    logger.error(f"Failed to load intents file: {str(e)}")

            # Initialize default responses if no file provided
            if not self.intents:
                self._initialize_default_responses()

            logger.info("DialogManager initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing DialogManager: {str(e)}")
            raise

    def _initialize_default_responses(self) -> None:
        """Initialize default responses for common intents."""
        self.intents = {
            'greeting': {
                'patterns': ['hello', 'hi', 'hey', 'good morning', 'good afternoon', 'good evening'],
                'responses': {
                    'en': ["Hello! Welcome to our hotel. How can I assist you today?",
                           "Hi there! How may I help you with your stay?"],
                    'zh': ["您好！欢迎来到我们的酒店。今天我能为您做什么？",
                           "您好！有什么可以帮到您的吗？"]
                }
            },
            'booking': {
                'patterns': ['book a room', 'make reservation', 'reserve a room', 'I want to book'],
                'responses': {
                    'en': ["I'd be happy to help with your booking. Could you please provide your check-in and check-out dates?",
                           "Let's get your reservation started. When would you like to check in and check out?"],
                    'zh': ["我很乐意帮您预订。请问您的入住和退房日期是什么时候？",
                           "让我们开始您的预订。您想什么时候入住和退房？"]
                }
            },
            'cancel_booking': {
                'patterns': ['cancel booking', 'cancel my reservation', 'cancel my booking', 'I want to cancel'],
                'responses': {
                    'en': ["I can help you cancel your booking. Please provide your booking ID or the email address used for the booking.",
                           "I'll help you cancel your reservation. Could you please provide your booking details?"],
                    'zh': ["我可以帮您取消预订。请提供您的预订ID或预订时使用的邮箱地址。",
                           "我会帮您取消预订。请提供您的预订详情。"]
                }
            },
            'upgrade_room': {
                'patterns': ['upgrade room', 'upgrade my room', 'room upgrade', 'better room'],
                'responses': {
                    'en': ["I can help you upgrade your room. What type of room would you like to upgrade to?",
                           "I'll assist with your room upgrade. Which room type would you prefer?"],
                    'zh': ["我可以帮您升级房间。您想升级到什么类型的房间？",
                           "我会协助您升级房间。您更喜欢哪种房型？"]
                }
            },
            'change_date': {
                'patterns': ['change date', 'reschedule', 'different day', 'new check-in'],
                'responses': {
                    'en': ["I can help you change your booking dates. Please provide your booking ID or email, and the new check-in and check-out dates.",
                           "Let's reschedule your booking. Could you provide your booking details and the new dates?"],
                    'zh': ["我可以帮您更改预订日期。请提供您的预订ID或邮箱，以及新的入住和退房日期。",
                           "让我们重新安排您的预订。请提供您的预订详情和新日期。"]
                }
            },
            'extend_stay': {
                'patterns': ['extend', 'stay longer', 'more nights', 'additional days'],
                'responses': {
                    'en': ["I can help you extend your stay. Please provide your booking ID or email, and how many additional nights you'd like.",
                           "Let's extend your booking. Could you provide your booking details and the number of extra nights?"],
                    'zh': ["我可以帮您延长住宿时间。请提供您的预订ID或邮箱，以及您想额外住宿的晚数。",
                           "让我们延长您的预订。请提供您的预订详情和额外住宿的晚数。"]
                }
            },
            'unknown': {
                'patterns': [],
                'responses': {
                    'en': ["I'm not sure I understand. Could you please clarify?",
                           "Could you provide more details so I can assist you better?"],
                    'zh': ["我不太明白您的意思，能否再说明一下？",
                           "您能提供更多细节以便我更好地帮助您吗？"]
                }
            },
            'off_topic': {
                'patterns': [],
                'responses': {
                    'en': ["Sorry, I focus on assisting you with hotel services, such as booking rooms, querying information, extending stays, etc.",
                           "I'm here to help with hotel-related matters. Do you need me to help you book a room or check facility information?"],
                    'zh': ["抱歉，我专注于协助您处理酒店服务，如预订房间、查询信息、延长住宿等。",
                           "我在这里帮助处理酒店相关事务。您需要我帮您预订房间或查看设施信息吗？"]
                }
            },
            'invalid_input': {
                'patterns': [],
                'responses': {
                    'en': ["Well... this doesn't look like very relevant content. I can assist you with hotel services, such as checking reservations, arranging breakfast, or requesting room cleaning services. Which one do you need me to help you with?",
                           "I'm not sure what you're trying to say. I'm here to help with hotel bookings, room upgrades, cancellations, and other hotel services. How can I assist you today?",
                           "That seems like random input. Let me help you with something useful! I can help with room bookings, check-in information, breakfast service, or facility inquiries. What would you like to know?"],
                    'zh': ["嗯...这看起来不太像相关内容。我可以协助您处理酒店服务，如查看预订、安排早餐或申请客房清洁服务。您需要我帮您处理哪一项？",
                           "我不太确定您想表达什么。我在这里帮助处理酒店预订、房间升级、取消预订和其他酒店服务。今天我能为您做什么？",
                           "这看起来像是随机输入。让我帮您处理一些有用的事情！我可以帮助预订房间、入住信息、早餐服务或设施查询。您想了解什么？"]
                }
            }
        }

    def analyze_sentiment(self, text: str) -> Tuple[str, float]:
        """
        Analyze the sentiment of the input text using a RoBERTa model.

        Args:
            text (str): Text to analyze.

        Returns:
            Tuple[str, float]: Sentiment label and confidence score.
        """
        try:
            if self.tokenizer is None or self.model is None:
                self.tokenizer = AutoTokenizer.from_pretrained("cardiffnlp/twitter-roberta-base-sentiment")
                self.model = AutoModelForSequenceClassification.from_pretrained("cardiffnlp/twitter-roberta-base-sentiment")
                self.model = self.model.to(self.device)

            tokens = self.tokenizer(text, return_tensors='pt', truncation=True, padding=True)
            tokens = {k: v.to(self.device) for k, v in tokens.items()}

            with torch.no_grad():
                output = self.model(**tokens)

            scores = output.logits.detach().cpu().numpy()[0]
            probs = softmax(scores)
            sentiment = self.sentiment_labels[probs.argmax()]
            confidence = probs.max()
            return sentiment, confidence
        except Exception as e:
            logger.error(f"Error in sentiment analysis: {str(e)}")
            return "Neutral", 0.33

    def is_valid_input(self, text: str) -> Tuple[bool, str]:
        """
        Validate if the input is meaningful and not random/garbled content.

        Args:
            text (str): User input to validate

        Returns:
            Tuple[bool, str]: (is_valid, reason_if_invalid)
        """
        try:
            text = text.strip()

            # Check if input is empty or too short
            if len(text) < 1:
                return False, "empty"

            # Check if input is too long (likely spam)
            if len(text) > 500:
                return False, "too_long"

            # Check for excessive repetition of characters
            # e.g., "aaaaaaa", "111111", "@@@@@@"
            for char in text:
                if text.count(char) > len(text) * 0.7 and len(text) > 3:
                    return False, "repetitive"

            # Check for random character sequences
            # Count different character types
            letters = sum(1 for c in text if c.isalpha())
            digits = sum(1 for c in text if c.isdigit())
            special_chars = sum(1 for c in text if c in string.punctuation)
            spaces = sum(1 for c in text if c.isspace())

            total_chars = len(text)

            # If input is mostly special characters or numbers without context
            if total_chars > 3:  # Lowered threshold for better detection
                special_ratio = special_chars / total_chars
                digit_ratio = digits / total_chars
                letter_ratio = letters / total_chars

                # Too many special characters (like "@@@@###$$$")
                if special_ratio > 0.6:
                    return False, "too_many_special_chars"

                # Too many random digits (like "123456789")
                if digit_ratio > 0.8 and letters == 0:
                    return False, "too_many_digits"

                # Mixed random content detection (like "123@@@" or "xyz123!@#")
                if total_chars >= 4:
                    # Check for suspicious mixed patterns
                    if special_ratio > 0.3 and (digit_ratio > 0.3 or letter_ratio > 0.3):
                        # Additional checks for mixed random content
                        consecutive_special = 0
                        consecutive_digits = 0
                        max_consecutive_special = 0
                        max_consecutive_digits = 0

                        for char in text:
                            if char in string.punctuation:
                                consecutive_special += 1
                                consecutive_digits = 0
                                max_consecutive_special = max(max_consecutive_special, consecutive_special)
                            elif char.isdigit():
                                consecutive_digits += 1
                                consecutive_special = 0
                                max_consecutive_digits = max(max_consecutive_digits, consecutive_digits)
                            else:
                                consecutive_special = 0
                                consecutive_digits = 0

                        # If we have 3+ consecutive special chars or digits in mixed content
                        if max_consecutive_special >= 3 or max_consecutive_digits >= 3:
                            return False, "mixed_random_content"

                        # Check for patterns like "123@@@" (digits followed by special chars)
                        if (max_consecutive_digits >= 2 and max_consecutive_special >= 2 and
                            total_chars <= 8 and spaces == 0):
                            return False, "mixed_random_content"

            # Check for keyboard mashing patterns
            keyboard_patterns = [
                'qwerty', 'asdf', 'zxcv', 'qaz', 'wsx', 'edc', 'rfv', 'tgb', 'yhn', 'ujm',
                'ijk', 'ol', 'mnb', 'vcx', 'dfg', 'hjk', 'rty', 'uio', 'sdf', 'ghj',
                'xcv', 'bnm', 'fgh', 'vbn', 'cvb', 'dfgh', 'fghj', 'ghjk', 'hjkl'
            ]

            text_lower = text.lower().replace(' ', '')
            for pattern in keyboard_patterns:
                if pattern in text_lower and len(text_lower) <= len(pattern) + 2:
                    return False, "keyboard_mashing"

            # Check for random letter sequences (like "ksdbvjdbvjbsjbvd")
            if len(text) > 8 and letters > 0:
                # Check if it contains mostly consonants or vowels in unusual patterns
                vowels = 'aeiou'
                consonants = 'bcdfghjklmnpqrstvwxyz'

                vowel_count = sum(1 for c in text.lower() if c in vowels)
                consonant_count = sum(1 for c in text.lower() if c in consonants)

                # If it's mostly letters but has very few vowels (unusual for real words)
                if letters > 6 and vowel_count == 0:
                    return False, "no_vowels"

                # Check for excessive consonant clusters
                consonant_clusters = 0
                for i in range(len(text) - 2):
                    if (text[i].lower() in consonants and
                        text[i+1].lower() in consonants and
                        text[i+2].lower() in consonants):
                        consonant_clusters += 1

                if consonant_clusters > 2 and len(text) < 15:
                    return False, "excessive_consonants"

            # Check for common random patterns
            random_patterns = [
                r'^[a-z]{8,}$',  # Long strings of only lowercase letters
                r'^[A-Z]{8,}$',  # Long strings of only uppercase letters
                r'^\d{8,}$',     # Long strings of only digits
                r'^[!@#$%^&*()]{3,}$',  # Only special characters
                r'^(.)\1{5,}$',  # Same character repeated many times
                r'^\d{2,}\W{2,}$',  # Digits followed by special chars (like "123@@@")
                r'^[a-zA-Z]{1,3}\d{2,}\W{2,}$',  # Letters + digits + special chars (like "xyz123!@#")
                r'^\d{1,3}[!@#$%^&*()]{2,}$',  # Short digits + special chars
                r'^[a-zA-Z]{1,4}\d{1,4}[!@#$%^&*()]{1,4}$',  # Mixed short patterns
            ]

            for pattern in random_patterns:
                if re.match(pattern, text.strip()):
                    return False, "random_pattern"

            # Additional check for short mixed random content
            if total_chars >= 4 and total_chars <= 10 and spaces == 0:
                # Check for patterns like "123@@@", "abc123!", "xyz456#$"
                has_digits = any(c.isdigit() for c in text)
                has_letters = any(c.isalpha() for c in text)
                has_special = any(c in string.punctuation for c in text)

                # If it has all three types and is short, it's likely random
                if has_digits and has_letters and has_special:
                    # Check if it doesn't contain common words or patterns
                    common_patterns = ['room', 'book', 'hotel', 'help', 'info', 'time', 'date']
                    if not any(pattern in text.lower() for pattern in common_patterns):
                        return False, "mixed_random_short"

                # Check for digit+special combinations (like "123@@@", "456!!!")
                if has_digits and has_special and not has_letters:
                    digit_count = sum(1 for c in text if c.isdigit())
                    special_count = sum(1 for c in text if c in string.punctuation)
                    if digit_count >= 2 and special_count >= 2:
                        return False, "digit_special_mix"

            # If we get here, the input seems valid
            return True, ""

        except Exception as e:
            logger.error(f"Error validating input: {str(e)}")
            # If validation fails, assume input is valid to avoid blocking legitimate users
            return True, ""

    def detect_intent(self, text: str) -> str:
        """Detect the intent of the user's input text."""
        try:
            logger.info(f"Detecting intent for input: {text}")

            # First validate if the input is meaningful
            is_valid, reason = self.is_valid_input(text)
            if not is_valid:
                logger.info(f"Invalid input detected: {reason}")
                return 'invalid_input'

            doc = self.nlp(text.lower())

            # Pattern-based intent matching
            for intent_name, intent_data in self.intents.items():
                patterns = intent_data.get('patterns', [])
                for pattern in patterns:
                    if pattern.lower() in text.lower():
                        logger.info(f"Pattern-based intent detected: {intent_name}")
                        return intent_name

            # Keyword-based intent detection
            cancel_keywords = ['cancel', 'cansel', 'cancellation', 'terminate', 'stop booking', 'cancel my booking', 'want to cancel']
            upgrade_keywords = ['upgrade', 'better room', 'change room', 'switch to deluxe', 'switch to suite', 'upgrade my room', 'want upgrade', 'upgrade to']
            # 改进change_date关键词，添加更多变体
            change_date_keywords = [
                'change date', 'reschedule', 'different day', 'new check-in',
                'modify booking', 'change booking', 'update booking', 'reschedule booking',
                'change my booking', 'change check-in', 'change my check-in', 'postpone',
                'postpone my booking', 'change check-in date', 'modify check-in', 'update check-in',
                'want change date', 'want to change date', 'change date to check in',
                'change my check in date', 'modify date', 'alter date', 'switch date',
                'move date', 'adjust date', 'update date', 'change the date',
                'modify the date', 'reschedule the date'
            ]
            extend_keywords = ['extend', 'stay longer', 'more nights', 'additional days', 'extend to', 'extend my stay', 'want extend']
            # Enhanced gratitude keywords for comprehensive thank you detection
            gratitude_keywords = [
                'thank you', 'thanks', 'terima kasih', 'thank you so much',
                'many thanks', 'tq', 'ty', 'thx', 'appreciate it',
                'that\'s helpful', 'thanks for the help', 'thanks a lot',
                'much appreciated', 'grateful', 'cheers', 'thanks mate',
                'appreciate', 'appreciated', 'thankful', 'thanks!', 'thank you!',
                'tysm', 'thks', 'thnx', 'thnks', 'danke', 'merci'
            ]
            booking_keywords = ['book', 'reserve', 'check-in', 'check in', 'booking', 'reservation', 'stay', 'room', 'night', 'accommodation']
            greeting_lemmas = ['hi', 'hello', 'hey', 'greet', 'morning', 'afternoon', 'evening']
            price_keywords = ['price', 'rate', 'cost', 'fee', 'charge', 'pay', 'expensive', 'cheap']
            location_keywords = ['location', 'where', 'address', 'direction', 'situated', 'located']
            food_keywords = ['food', 'restaurant', 'breakfast', 'lunch', 'dinner', 'meal', 'eat', 'cuisine', 'menu']
            attraction_keywords = ['tourist', 'attraction', 'visit', 'see', 'sight', 'museum', 'gallery', 'park']
            transport_keywords = ['transport', 'taxi', 'bus', 'subway', 'metro', 'train', 'airport', 'shuttle']

            text_lemmas = [token.lemma_ for token in doc]

            if any(keyword in text.lower() for keyword in cancel_keywords):
                return 'cancel_booking'
            elif any(keyword in text.lower() for keyword in upgrade_keywords):
                return 'upgrade_room'
            elif any(keyword in text.lower() for keyword in change_date_keywords):
                return 'change_date'
            elif any(keyword in text.lower() for keyword in extend_keywords):
                return 'extend_stay'
            elif any(keyword in text.lower() for keyword in gratitude_keywords):
                logger.info("Gratitude intent detected")
                return 'express_gratitude'
            elif self.detect_book_another_room_intent(text):
                logger.info("Book another room intent detected")
                return 'book_another_room'
            elif any(keyword in text.lower() for keyword in booking_keywords):
                logger.info("Booking intent detected")
                return 'booking'
            elif any(lemma in greeting_lemmas for lemma in text_lemmas):
                return 'greeting'
            elif any(keyword in text.lower() for keyword in price_keywords):
                return 'prices'
            elif any(keyword in text.lower() for keyword in location_keywords):
                return 'location'
            elif any(keyword in text.lower() for keyword in food_keywords):
                return 'food'
            elif any(keyword in text.lower() for keyword in attraction_keywords):
                return 'attractions'
            elif any(keyword in text.lower() for keyword in transport_keywords):
                return 'transport'
            else:
                # Enhanced off-topic detection before falling back to unknown
                is_off_topic, off_topic_type = self.detect_off_topic_intent(text)
                if is_off_topic:
                    return 'off_topic'
                return 'unknown'
        except Exception as e:
            logger.error(f"Intent detection error: {str(e)}")
            return 'unknown'

    def extract_dates(self, text: str) -> Optional[Dict[str, str]]:
        """
        Extract check-in and check-out dates from text in various formats.

        Args:
            text (str): Text containing potential date information.

        Returns:
            Optional[Dict[str, str]]: Dictionary with 'check_in' and 'check_out' dates in YYYY-MM-DD format, or None if no valid dates found.
        """
        try:
            logger.info(f"Extracting dates from: {text}")
            today = datetime.now()
            dates = []
            text_lower = text.lower()

            # Handle single date input (e.g., "25/05/2025")
            single_date_match = self.single_date_pattern.match(text)
            if single_date_match:
                day, month, year = single_date_match.groups()
                try:
                    check_in = datetime(int(year), int(month), int(day))
                    if check_in.date() < today.date():
                        logger.warning("Provided date is in the past")
                        return None
                    check_out = check_in + timedelta(days=1)
                    result = {
                        'check_in': check_in.strftime('%Y-%m-%d'),
                        'check_out': check_out.strftime('%Y-%m-%d')
                    }
                    logger.info(f"Extracted single date: {result}")
                    return result
                except ValueError as e:
                    logger.warning(f"Invalid single date format: {e}")
                    return None

            # Month name to number mapping
            month_to_num = {
                'january': 1, 'february': 2, 'march': 3, 'april': 4, 'may': 5, 'june': 6,
                'july': 7, 'august': 8, 'september': 9, 'october': 10, 'november': 11, 'december': 12
            }
            day_to_num = {
                'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3,
                'friday': 4, 'saturday': 5, 'sunday': 6
            }

            # Handle natural language expressions
            if 'tomorrow' in text_lower:
                dates.append(today + timedelta(days=1))
                logger.info(f"Extracted 'tomorrow' date: {dates[-1]}")
            if 'today' in text_lower:
                dates.append(today)
                logger.info(f"Extracted 'today' date: {dates[-1]}")

            # Handle "next Monday", "this Tuesday"
            for match in self.date_patterns[2].findall(text_lower):
                prefix, day_name = match
                day_num = day_to_num[day_name]
                today_weekday = today.weekday()
                days_to_add = (day_num - today_weekday + 7) if prefix == 'next' else (day_num - today_weekday)
                if days_to_add <= 0:
                    days_to_add += 7
                target_date = today + timedelta(days=days_to_add)
                dates.append(target_date)
                logger.info(f"Extracted '{prefix} {day_name}' date: {target_date}")

            # Handle "May 12th, 2025"
            for match in self.date_patterns[4].findall(text_lower):
                month_name, day, year = match
                try:
                    month_num = month_to_num[month_name.lower()]
                    date_obj = datetime(int(year), month_num, int(day))
                    dates.append(date_obj)
                    logger.info(f"Extracted month-day-year date: {date_obj}")
                except (ValueError, KeyError) as e:
                    logger.warning(f"Invalid month-day-year date: {month_name} {day}, {year}: {str(e)}")

            # Handle "12th of May, 2025"
            for match in self.date_patterns[5].findall(text_lower):
                day, month_name, year = match
                try:
                    month_num = month_to_num[month_name.lower()]
                    date_obj = datetime(int(year), month_num, int(day))
                    dates.append(date_obj)
                    logger.info(f"Extracted day-month-year date: {date_obj}")
                except (ValueError, KeyError) as e:
                    logger.warning(f"Invalid day-month-year date: {day} of {month_name}, {year}: {str(e)}")

            # Handle duration-based input (e.g., "3 nights from May 25th, 2025")
            for match in self.date_patterns[6].findall(text_lower):
                nights, month_name, day, year = match
                try:
                    month_num = month_to_num[month_name.lower()]
                    check_in = datetime(int(year), month_num, int(day))
                    check_out = check_in + timedelta(days=int(nights))
                    dates.append(check_in)
                    dates.append(check_out)
                    logger.info(f"Extracted duration-based date: check-in {check_in}, check-out {check_out}")
                except (ValueError, KeyError) as e:
                    logger.warning(f"Invalid duration-based date: {nights} nights from {month_name} {day}, {year}: {str(e)}")

            # Handle "Month Day to Month Day" format (e.g., "June 10 to June 12")
            for match in self.date_patterns[7].findall(text_lower):
                start_month, start_day, end_month, end_day = match
                try:
                    start_month_num = month_to_num[start_month.lower()]
                    end_month_num = month_to_num[end_month.lower()]

                    # Use current year if no year specified
                    current_year = today.year

                    check_in = datetime(current_year, start_month_num, int(start_day))
                    check_out = datetime(current_year, end_month_num, int(end_day))

                    # If dates are in the past, try next year
                    if check_in.date() < today.date():
                        check_in = datetime(current_year + 1, start_month_num, int(start_day))
                        check_out = datetime(current_year + 1, end_month_num, int(end_day))

                    dates.append(check_in)
                    dates.append(check_out)
                    logger.info(f"Extracted month-to-month date: check-in {check_in}, check-out {check_out}")
                except (ValueError, KeyError) as e:
                    logger.warning(f"Invalid month-to-month date: {start_month} {start_day} to {end_month} {end_day}: {str(e)}")

            # Handle standard date formats
            for match in self.date_patterns[0].findall(text):
                day, month, year = match
                try:
                    date_obj = datetime(int(year), int(month), int(day))
                    dates.append(date_obj)
                    logger.info(f"Extracted DD/MM/YYYY date: {date_obj}")
                except ValueError as e:
                    logger.warning(f"Invalid DD/MM/YYYY date: {match}: {str(e)}")

            for match in self.date_patterns[1].findall(text):
                year, month, day = match
                try:
                    date_obj = datetime(int(year), int(month), int(day))
                    dates.append(date_obj)
                    logger.info(f"Extracted YYYY/MM/DD date: {date_obj}")
                except ValueError as e:
                    logger.warning(f"Invalid YYYY/MM/DD date: {match}: {str(e)}")

            if not dates:
                logger.warning("No dates found")
                return None

            dates.sort()
            valid_dates = [d for d in dates if d.date() >= today.date()]
            if not valid_dates:
                logger.warning("All provided dates are in the past")
                return None

            if len(valid_dates) == 1:
                check_in = valid_dates[0]
                check_out = check_in + timedelta(days=1)
                result = {
                    'check_in': check_in.strftime('%Y-%m-%d'),
                    'check_out': check_out.strftime('%Y-%m-%d')
                }
                logger.info(f"Single date result: {result}")
                return result

            check_in = valid_dates[0]
            check_out = valid_dates[1]
            if check_in >= check_out:
                logger.warning("Check-in date must be before check-out")
                check_out = check_in + timedelta(days=1)

            result = {
                'check_in': check_in.strftime('%Y-%m-%d'),
                'check_out': check_out.strftime('%Y-%m-%d')
            }
            logger.info(f"Multiple date result: {result}")
            return result

        except Exception as e:
            logger.error(f"Date extraction error: {str(e)}")
            return None

    def extract_booking_info(self, message: str, current_info: Optional[Dict] = None) -> Dict:
        """Enhanced booking information extraction with better pattern recognition."""
        info = {}
        current_info = current_info or {}
        message_clean = message.strip()

        # Handle standalone email
        if self.single_email_pattern.match(message_clean):
            info['email'] = message_clean
            logger.info(f"Extracted standalone email: {info['email']}")
            return info

        # Handle standalone phone (Malaysian + International patterns)
        phone_patterns = [
            # Malaysian mobile numbers (01X-XXXXXXX or 01X-XXXXXXXX)
            r'^\s*(01[0-9][-\s]?[0-9]{7,8})\s*$',  # 012-8833903, 011-58763903, 0128833903, 01158763903
            # Malaysian landline numbers (0X-XXXXXXX or 0X-XXXXXXXX)
            r'^\s*(0[2-9][0-9]?[-\s]?[0-9]{6,8})\s*$',  # 03-12345678, 04-1234567
            # Malaysian international format
            r'^\s*(\+60[\s-]?1[0-9][\s-]?[0-9]{7,8})\s*$',  # +60-12-8833903, +60 12 8833903
            # US format like 555-987-6543
            r'^\s*(\d{3}[-\s]?\d{3}[-\s]?\d{4})\s*$',  # 555-987-6543
            # Simple 10-11 digit number (fallback)
            r'^\s*(\d{10,11})\s*$'  # 0128833903, 01158763903
        ]

        for pattern in phone_patterns:
            phone_match = re.match(pattern, message_clean)
            if phone_match:
                info['phone'] = phone_match.group(1).strip()
                logger.info(f"Extracted standalone phone: {info['phone']}")
                return info

        # Enhanced name extraction patterns
        name_patterns = [
            r'(?:my\s+name\s+is|i\s+am|i\'m|this\s+is|call\s+me)\s+([A-Za-z\s]{2,30})(?:\.|$|\s+and|\s+email|\s+phone|\s+contact)',
            r'^([A-Za-z\s]{2,30})$',  # Simple name only
            r'name[:\s]+([A-Za-z\s]{2,30})(?:\.|$|\s+and|\s+email|\s+phone)',
        ]

        # Check if we're expecting a name (first step in booking process)
        if self.state == "collecting_booking_info" and 'guest_name' not in current_info:
            # Try name patterns first
            for pattern in name_patterns:
                name_match = re.search(pattern, message, re.IGNORECASE)
                if name_match:
                    potential_name = name_match.group(1).strip()
                    # Validate name (no numbers, reasonable length)
                    if re.match(r'^[A-Za-z\s]{2,30}$', potential_name) and not any(word in potential_name.lower() for word in ['email', 'phone', 'room', 'book', 'hotel']):
                        info['guest_name'] = potential_name
                        logger.info(f"Extracted name: {info['guest_name']}")
                        break

            # If no pattern matched and it looks like a simple name
            if 'guest_name' not in info and re.match(r'^[A-Za-z\s]{2,30}$', message_clean):
                info['guest_name'] = message_clean
                logger.info(f"Using entire message as name: {info['guest_name']}")

        # Extract email with improved pattern
        email_patterns = [
            r'\b([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,})\b',
            r'email[:\s]+([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,})',
        ]

        for pattern in email_patterns:
            email_match = re.search(pattern, message, re.IGNORECASE)
            if email_match:
                info['email'] = email_match.group(1)
                logger.info(f"Extracted email: {info['email']}")
                break

        # Extract phone with improved patterns (Malaysian + International)
        phone_extraction_patterns = [
            # With prefix keywords
            r'(?:phone|contact|call|tel|mobile|number)[:\s]+(01[0-9][-\s]?[0-9]{7,8})',  # Malaysian mobile with prefix
            r'(?:phone|contact|call|tel|mobile|number)[:\s]+(0[2-9][0-9]?[-\s]?[0-9]{6,8})',  # Malaysian landline with prefix
            r'(?:phone|contact|call|tel|mobile|number)[:\s]+(\+?\d{1,3}[\s-]?\d{2,3}[\s-]?\d{7,8})',  # International with prefix
            r'(?:phone|contact|call|tel|mobile|number)[:\s]+(\d{3}[-\s]?\d{3}[-\s]?\d{4})',  # US format with prefix
            # Anywhere in text
            r'(01[0-9][-\s]?[0-9]{7,8})',  # Malaysian mobile anywhere: 012-8833903, 0128833903, 011-58763903, 01158763903
            r'(0[2-9][0-9]?[-\s]?[0-9]{6,8})',  # Malaysian landline anywhere
            r'(\+60[\s-]?1[0-9][\s-]?[0-9]{7,8})',  # Malaysian international format: +60-12-8833903, +60 12 8833903
            r'(\d{3}[-\s]?\d{3}[-\s]?\d{4})',  # US format anywhere: 555-987-6543
        ]

        for pattern in phone_extraction_patterns:
            phone_match = re.search(pattern, message, re.IGNORECASE)
            if phone_match:
                info['phone'] = phone_match.group(1).strip()
                logger.info(f"Extracted phone: {info['phone']}")
                break

        # Extract dates
        dates = self.extract_dates(message)
        if dates:
            info['check_in_date'] = dates.get('check_in')
            info['check_out_date'] = dates.get('check_out')

        # Enhanced room type extraction
        room_type_patterns = [
            (r'\b(?:standard|regular|normal|basic)\s*(?:room)?\b', 'Standard'),
            (r'\b(?:deluxe|premium|superior|enhanced)\s*(?:room)?\b', 'Deluxe'),
            (r'\b(?:suite|luxury|executive|vip)\s*(?:room)?\b', 'Suite'),
            (r'\b(?:1|one)\b.*(?:standard|regular)', 'Standard'),
            (r'\b(?:2|two)\b.*(?:deluxe|premium)', 'Deluxe'),
            (r'\b(?:3|three)\b.*(?:suite|luxury)', 'Suite'),
        ]

        for pattern, room_type in room_type_patterns:
            if re.search(pattern, message, re.IGNORECASE):
                info['room_type'] = room_type
                logger.info(f"Extracted room type: {info['room_type']}")
                break

        return info

    def is_booking_info_complete(self, session: Dict) -> bool:
        """
        Check if all required booking information is collected.

        Args:
            session (Dict): Current session data.

        Returns:
            bool: True if all required fields are present, False otherwise.
        """
        required_fields = ['check_in_date', 'check_out_date', 'room_type', 'guest_name', 'email', 'phone']
        return all(field in session for field in required_fields)

    def ask_for_missing_info(self, session: Dict) -> str:
        """Generate a response asking for missing booking information in a logical order."""
        # 优先顺序：姓名 -> 电话 -> 邮箱 -> 房间类型 -> 入住日期 -> 退房日期
        if 'guest_name' not in session:
            return "👋 Hello! I'd be happy to help you with your booking. May I have your name please?"
        elif 'phone' not in session:
            return f"Thank you, {session.get('guest_name')}! 📱 Could you please provide your phone number for contact purposes?"
        elif 'email' not in session:
            return f"Perfect! 📧 What email address should we use for your booking confirmation, {session.get('guest_name')}?"
        elif 'room_type' not in session:
            return f"""Excellent! Now, {session.get('guest_name')}, what type of room would you prefer? 🏨

🛏️ **Standard Room** – RM 132/night
   Cozy and comfortable with all essentials, free Wi-Fi & private bathroom

🛏️ **Deluxe Room** – RM 205/night
   Spacious room with work desk, enhanced amenities & city view

🛏️ **Executive Suite** – RM 321/night
   Luxury accommodation with separate living area & premium services

Please let me know which room type you'd like!"""
        elif 'check_in_date' not in session:
            return f"Great choice, {session.get('guest_name')}! 📅 When would you like to check in? Please use a format like DD/MM/YYYY (e.g., 25/12/2024) or 'next Monday'."
        elif 'check_out_date' not in session:
            return f"Perfect! 📅 And when will you be checking out? Please use the same format (DD/MM/YYYY or 'next Friday')."
        else:
            return f"Wonderful! Let me confirm your booking details, {session.get('guest_name')}:\n\n{self.format_booking_details(session)}\n\n✅ Is everything correct? Please reply 'yes' to confirm or let me know what needs to be changed."

    def format_booking_details(self, session: Dict) -> str:
        """
        Format booking details for confirmation with enhanced presentation.

        Args:
            session (Dict): Current session data.

        Returns:
            str: Formatted booking details.
        """
        details = "📋 **BOOKING SUMMARY**\n"
        details += "=" * 30 + "\n\n"

        details += f"👤 **Guest Name:** {session.get('guest_name', 'Not specified')}\n"
        details += f"📱 **Phone:** {session.get('phone', 'Not specified')}\n"
        details += f"📧 **Email:** {session.get('email', 'Not specified')}\n\n"

        details += f"🏨 **Room Type:** {session.get('room_type', 'Not specified')}\n"
        details += f"📅 **Check-in:** {session.get('check_in_date', 'Not specified')}\n"
        details += f"📅 **Check-out:** {session.get('check_out_date', 'Not specified')}\n"

        # Calculate duration and estimated cost if dates are available
        if session.get('check_in_date') and session.get('check_out_date'):
            try:
                from datetime import datetime
                check_in = datetime.strptime(session['check_in_date'], '%Y-%m-%d')
                check_out = datetime.strptime(session['check_out_date'], '%Y-%m-%d')
                duration = (check_out - check_in).days

                # Estimate cost based on room type
                room_prices = {
                    'Standard': 132,
                    'Deluxe': 205,
                    'Suite': 321
                }
                base_price = room_prices.get(session.get('room_type'), 132)
                estimated_cost = base_price * duration

                details += f"🌙 **Duration:** {duration} night(s)\n"
                details += f"💰 **Estimated Total:** RM {estimated_cost:,}\n"
            except:
                pass

        details += "\n" + "=" * 30
        return details

    def handle_booking_intent(self, user_input: str, lang: str = 'en') -> str:
        """
        Handle booking intent and guide user through the booking process.
        For returning customers, only ask for room type and dates.
        """
        try:
            # 清除之前的确认标记，开始新的预订流程
            if 'confirmation_sent' in self.user_data:
                del self.user_data['confirmation_sent']
            if 'confirmation_booking_id' in self.user_data:
                del self.user_data['confirmation_booking_id']

            logger.info("Starting new booking process - cleared previous confirmation flags")

            booking_info = self.extract_booking_info(user_input, self.user_data)
            if booking_info:
                self.user_data.update(booking_info)

            # Check if user is a returning customer (has previous bookings)
            is_returning_customer = self.check_returning_customer()

            if is_returning_customer:
                # For returning customers, only require room_type, check_in_date, check_out_date
                required_fields = ['check_in_date', 'check_out_date', 'room_type']
                if all(field in self.user_data for field in required_fields):
                    # Auto-fill guest info from previous booking
                    self.auto_fill_guest_info()

                    booking_id = f"BK-{random.randint(10000, 99999)}"
                    self.user_data['booking_id'] = booking_id
                    self.state = "booking_confirmed"

                    # Create actual booking record in database
                    try:
                        actual_booking_id = self.create_booking_record(self.user_data)
                        if actual_booking_id:
                            self.user_data['booking_id'] = actual_booking_id
                            logger.info(f"Booking record created successfully: {actual_booking_id}")
                        else:
                            logger.warning("Failed to create booking record, using generated ID")
                    except Exception as e:
                        logger.error(f"Error creating booking record: {str(e)}")

                    # Set up delayed success message with addon offer
                    self.delayed_messages = [{
                        'message': f"🎉 <strong>Booking Successful!</strong> 🎉<br><br>✅ <strong>Booking Confirmation</strong><br>📋 <strong>Booking ID:</strong> {self.user_data.get('booking_id', 'N/A')}<br>👤 <strong>Guest Name:</strong> {self.user_data.get('guest_name', 'N/A')}<br>📱 <strong>Phone:</strong> {self.user_data.get('phone', 'N/A')}<br>📧 <strong>Email:</strong> {self.user_data.get('email', 'N/A')}<br>🏨 <strong>Room Type:</strong> {self.user_data.get('room_type', 'N/A')}<br>📅 <strong>Check-in:</strong> {self.user_data.get('check_in_date', 'N/A')}<br>📅 <strong>Check-out:</strong> {self.user_data.get('check_out_date', 'N/A')}<br><br>🎊 Booking successful! Would you like to add breakfast service (RM20/person) or enjoy our airport transfer service (RM50)?",
                        'delay': 5
                    }]
                    self.state = "offering_addons"
                    return f"<img src='{self.qr_code_path}' alt='Payment QR Code' class='img-fluid rounded' style='max-width: 300px;'><br>Please scan the QR code to complete your payment."
                else:
                    self.state = "collecting_booking_info"
                    return self.ask_for_missing_info_returning_customer(self.user_data)
            else:
                # Original logic for new customers
                if self.is_booking_info_complete(self.user_data):
                    booking_id = f"BK-{random.randint(10000, 99999)}"
                    self.user_data['booking_id'] = booking_id
                    self.state = "booking_confirmed"

                    # Create actual booking record in database
                    try:
                        actual_booking_id = self.create_booking_record(self.user_data)
                        if actual_booking_id:
                            self.user_data['booking_id'] = actual_booking_id
                            logger.info(f"Booking record created successfully: {actual_booking_id}")
                        else:
                            logger.warning("Failed to create booking record, using generated ID")
                    except Exception as e:
                        logger.error(f"Error creating booking record: {str(e)}")

                    # Set up delayed success message with addon offer
                    self.delayed_messages = [{
                        'message': f"🎉 <strong>Booking Successful!</strong> 🎉<br><br>✅ <strong>Booking Confirmation</strong><br>📋 <strong>Booking ID:</strong> {self.user_data.get('booking_id', 'N/A')}<br>👤 <strong>Guest Name:</strong> {self.user_data.get('guest_name', 'N/A')}<br>📱 <strong>Phone:</strong> {self.user_data.get('phone', 'N/A')}<br>📧 <strong>Email:</strong> {self.user_data.get('email', 'N/A')}<br>🏨 <strong>Room Type:</strong> {self.user_data.get('room_type', 'N/A')}<br>📅 <strong>Check-in:</strong> {self.user_data.get('check_in_date', 'N/A')}<br>📅 <strong>Check-out:</strong> {self.user_data.get('check_out_date', 'N/A')}<br><br>🎊 Booking successful! Would you like to add breakfast service (RM20/person) or enjoy our airport transfer service (RM50)?",
                        'delay': 5
                    }]
                    self.state = "offering_addons"
                    return f"<img src='{self.qr_code_path}' alt='Payment QR Code' class='img-fluid rounded' style='max-width: 300px;'><br>Please scan the QR code to complete your payment."
                else:
                    self.state = "collecting_booking_info"
                    return self.ask_for_missing_info(self.user_data)
        except Exception as e:
            logger.error(f"Error handling booking intent: {str(e)}")
            return "Sorry, I encountered an error while processing your booking request." if lang == 'en' else "抱歉，处理您的预订请求时遇到错误。"

    def check_returning_customer(self) -> bool:
        """
        Check if the current user is a returning customer by looking for previous bookings.
        This will be implemented in views.py by checking the database.
        """
        # This flag will be set by views.py when processing the request
        return self.user_data.get('is_returning_customer', False)

    def auto_fill_guest_info(self):
        """
        Auto-fill guest information from previous booking for returning customers.
        """
        # Guest info will be pre-filled by views.py from previous booking
        pass

    def ask_for_missing_info_returning_customer(self, session: Dict) -> str:
        """
        Generate a response asking for missing booking information for returning customers.
        Only asks for room type and dates.
        """
        if 'room_type' not in session:
            return """Welcome back! What type of room would you like this time?\n\nStandard Room – Cozy with essentials, free Wi-Fi & private bathroom. From RM132/night.\n\nDeluxe Room – Spacious, work desk, fast internet. From RM205/night.\n\nSuite – Luxury stay with living area & great views. From RM320/night."""
        elif 'check_in_date' not in session:
            return "When would you like to check in? Please use a format like DD/MM/YYYY or 'next Monday'."
        elif 'check_out_date' not in session:
            return "When will you be checking out? Please use a format like DD/MM/YYYY or 'next Monday'."
        else:
            return f"Please confirm your booking details:\n{self.format_booking_details(session)}"

    def handle_cancel_booking_intent(self, user_input: str, lang: str = 'en') -> str:
        """
        Handle booking cancellation intent.
        """
        try:
            booking_id_match = re.search(r'BK-\d{5}', user_input)
            email_match = self.email_pattern.search(user_input)

            if booking_id_match or email_match:
                self.state = "cancelling_booking"
                if booking_id_match:
                    self.user_data['cancel_booking_id'] = booking_id_match.group()
                if email_match:
                    self.user_data['cancel_email'] = email_match.group(1)

                return "I'm processing your cancellation request. Please wait a moment..." if lang == 'en' else "我正在处理您的取消请求，请稍等..."
            else:
                # 修改这里：将中文提示改为英文
                return "To cancel your booking, please provide your booking ID (format: BK-XXXXX) or the email address used for booking." if lang == 'en' else "To cancel your booking, please provide your booking ID (format: BK-XXXXX) or the email address used for booking."
        except Exception as e:
            logger.error(f"Error handling cancel booking intent: {str(e)}")
            return "Sorry, I encountered an error while processing your cancellation request." if lang == 'en' else "抱歉，处理您的取消请求时遇到错误。"

    def handle_upgrade_room_intent(self, user_input: str, lang: str = 'en') -> str:
        """
        Handle room upgrade intent.
        """
        try:
            booking_id_match = re.search(r'BK-\d{5}', user_input)
            email_match = self.email_pattern.search(user_input)

            room_type = None
            if re.search(r'\b(?:deluxe|premium|superior)\s*(?:room)?\b', user_input, re.IGNORECASE):
                room_type = 'Deluxe'
            elif re.search(r'\b(?:suite|luxury|executive)\s*(?:room)?\b', user_input, re.IGNORECASE):
                room_type = 'Suite'

            if booking_id_match or email_match:
                self.state = "upgrading_room"
                if booking_id_match:
                    self.user_data['upgrade_booking_id'] = booking_id_match.group()
                if email_match:
                    self.user_data['upgrade_email'] = email_match.group(1)
                if room_type:
                    self.user_data['new_room_type'] = room_type

                    return f"I'm processing your room upgrade to {room_type}. Please wait a moment..." if lang == 'en' else f"我正在处理您升级到{room_type}房间的请求，请稍等..."
                else:
                    return "What type of room would you like to upgrade to? We offer Deluxe rooms and Suites." if lang == 'en' else "您想升级到什么类型的房间？我们提供豪华房和套房。"
            else:
                return "To upgrade your room, please provide your booking ID (format: BK-XXXXX) or the email address used for booking." if lang == 'en' else "要升级房间，请提供您的预订ID（格式：BK-XXXXX）或预订时使用的邮箱地址。"
        except Exception as e:
            logger.error(f"Error handling upgrade room intent: {str(e)}")
            return "Sorry, I encountered an error while processing your upgrade request." if lang == 'en' else "抱歉，处理您的升级请求时遇到错误。"

    def handle_change_date_intent(self, user_input: str, lang: str = 'en') -> str:
        """
        Handle change date intent with 3-day advance rule.
        """
        try:
            booking_id_match = re.search(r'BK-\d{5}', user_input)
            email_match = self.email_pattern.search(user_input)
            dates = self.extract_dates(user_input)

            if booking_id_match or email_match:
                self.state = "changing_date"
                if booking_id_match:
                    self.user_data['change_booking_id'] = booking_id_match.group()
                if email_match:
                    self.user_data['change_email'] = email_match.group(1)
                if dates:
                    # Check if new check-in date is at least 3 days from today
                    from datetime import datetime, timedelta
                    today = datetime.now().date()
                    new_check_in = datetime.strptime(dates['check_in'], '%Y-%m-%d').date()
                    days_until_checkin = (new_check_in - today).days

                    if days_until_checkin < 3:
                        return "Sorry, check-in date changes must be made at least 3 days in advance. Please choose a date that is at least 3 days from today." if lang == 'en' else "抱歉，入住日期更改必须至少提前3天进行。请选择距离今天至少3天的日期。"

                    # 修复字段名：使用new_check_in_date而不是new_check_in
                    self.user_data['new_check_in_date'] = dates['check_in']
                    self.user_data['new_check_out_date'] = dates['check_out']
                    return f"I'm processing your request to change your booking dates to check-in on {dates['check_in']} and check-out on {dates['check_out']}. Please wait a moment..." if lang == 'en' else f"我正在处理您将预订日期更改为入住 {dates['check_in']} 和退房 {dates['check_out']} 的请求，请稍等..."
                else:
                    return "Please provide the new check-in and check-out dates for your booking (e.g., 25/05/2025 to 30/05/2025). Note: Changes must be made at least 3 days before your original check-in date." if lang == 'en' else "请提供您预订的新入住和退房日期（例如，2025/05/25 至 2025/05/30）。注意：更改必须在原入住日期前至少3天进行。"
            else:
                # 修改这里：将中文提示改为英文
                return "To change your booking dates, please provide your booking ID (format: BK-XXXXX) or the email address used for booking." if lang == 'en' else "To change your booking dates, please provide your booking ID (format: BK-XXXXX) or the email address used for booking."
        except Exception as e:
            logger.error(f"Error handling change date intent: {str(e)}")
            return "Sorry, I encountered an error while processing your date change request." if lang == 'en' else "抱歉，处理您的日期更改请求时遇到错误。"

    def handle_extend_stay_intent(self, user_input: str, lang: str = 'en') -> str:
        """
        Handle extend stay intent for current guests.
        """
        try:
            booking_id_match = re.search(r'BK-\d{5}', user_input)
            email_match = self.email_pattern.search(user_input)
            nights_match = re.search(r'(\d+)\s*(?:night|nights)', user_input, re.IGNORECASE)

            # Extract specific dates if mentioned (e.g., "extend until 30/05/2025")
            extend_until_date = None
            date_patterns = [
                r'(?:until|to|till)\s*(\d{1,2}[/\-]\d{1,2}[/\-]\d{4})',
                r'(?:until|to|till)\s*(\d{4}[/\-]\d{1,2}[/\-]\d{1,2})'
            ]

            for pattern in date_patterns:
                date_match = re.search(pattern, user_input, re.IGNORECASE)
                if date_match:
                    try:
                        from datetime import datetime
                        date_str = date_match.group(1)
                        if '/' in date_str:
                            parts = date_str.split('/')
                        else:
                            parts = date_str.split('-')

                        if len(parts[0]) == 4:  # YYYY/MM/DD format
                            extend_until_date = datetime.strptime(date_str, '%Y/%m/%d' if '/' in date_str else '%Y-%m-%d').date()
                        else:  # DD/MM/YYYY format
                            extend_until_date = datetime.strptime(date_str, '%d/%m/%Y' if '/' in date_str else '%d-%m-%Y').date()
                        break
                    except ValueError:
                        continue

            if booking_id_match or email_match:
                self.state = "extending_stay"
                if booking_id_match:
                    self.user_data['extend_booking_id'] = booking_id_match.group()
                if email_match:
                    self.user_data['extend_email'] = email_match.group(1)

                if extend_until_date:
                    self.user_data['extend_until_date'] = extend_until_date.strftime('%Y-%m-%d')
                    return f"I'm processing your request to extend your stay until {extend_until_date.strftime('%d/%m/%Y')}. Please wait a moment..." if lang == 'en' else f"我正在处理您延长住宿至 {extend_until_date.strftime('%Y/%m/%d')} 的请求，请稍等..."
                elif nights_match:
                    nights = int(nights_match.group(1))
                    self.user_data['additional_nights'] = nights
                    return f"I'm processing your request to extend your stay by {nights} night(s). Please wait a moment..." if lang == 'en' else f"我正在处理您延长住宿 {nights} 晚的请求，请稍等..."
                else:
                    return "How many additional nights would you like to extend your stay?" if lang == 'en' else "您想延长住宿多少晚？"
            else:
                return "To extend your stay, please provide your booking ID (format: BK-XXXXX) or the email address used for booking." if lang == 'en' else "要延长住宿，请提供您的预订ID（格式：BK-XXXXX）或预订时使用的邮箱地址。"
        except Exception as e:
            logger.error(f"Error handling extend stay intent: {str(e)}")
            return "Sorry, I encountered an error while processing your extend stay request." if lang == 'en' else "抱歉，处理您的延长住宿请求时遇到错误。"

    def handle_gratitude_intent(self, user_input: str, lang: str = 'en') -> str:
        """
        Handle gratitude/thank you messages with context-aware responses.
        Provides different responses based on conversation context and user state.
        """
        try:
            # Check conversation context to provide appropriate response
            last_booking = self.user_data.get('last_viewed_booking')
            recent_booking_id = self.user_data.get('booking_id')
            current_state = self.state

            # Context-aware responses based on recent activity
            if current_state == "booking_confirmed" or recent_booking_id:
                # User just completed a booking
                responses = [
                    "You're very welcome! Have a wonderful stay with us! If you need to modify or cancel your reservation, feel free to contact me anytime.",
                    "My pleasure! We're looking forward to hosting you. If you have any questions about your booking or need assistance during your stay, I'm here to help!",
                    "You're most welcome! Thank you for choosing our hotel. Don't hesitate to reach out if you need anything before or during your visit."
                ]
            elif last_booking and last_booking.get('booking_id'):
                # User has been checking booking status or managing existing booking
                responses = [
                    "You're welcome! I'm glad I could help with your booking. Is there anything else you'd like to know about your reservation or our hotel services?",
                    "Happy to assist! If you need any other help with your booking or have questions about our amenities, just let me know.",
                    "My pleasure! Feel free to ask if you need help with room upgrades, date changes, or any other hotel services."
                ]
            elif current_state in ["offering_addons", "collecting_breakfast_count", "confirming_breakfast"]:
                # User is in addon service flow
                responses = [
                    "You're welcome! I'm here to make your stay as comfortable as possible. Anything else I can add to enhance your experience?",
                    "My pleasure! Is there anything else you'd like to add to your booking, or do you have questions about our hotel facilities?"
                ]
            elif self.user_data.get('showing_service_menu') or self.user_data.get('showing_room_service_menu'):
                # User was shown service menus
                responses = [
                    "You're very welcome! I'm here whenever you need assistance with any of our hotel services. What else can I help you with?",
                    "Happy to help! Feel free to ask about room service, housekeeping, or any other hotel amenities whenever you need them."
                ]
            else:
                # General conversation or information inquiry
                responses = [
                    "You're welcome! Let me know if you need help with room booking or hotel info.",
                    "Happy to help! Is there anything else I can assist you with regarding our hotel services?",
                    "My pleasure! Feel free to ask if you have more questions about our hotel services, room types, or amenities.",
                    "You're very welcome! I'm here if you need any assistance with bookings or hotel information.",
                    "Thank you for your kind words! How else can I assist you with your hotel needs today?"
                ]

            # Add a small chance for promotional follow-up
            import random
            response = random.choice(responses)

            # 20% chance to add a helpful suggestion based on context
            if random.random() < 0.2:
                suggestions = [
                    " By the way, did you know we offer complimentary breakfast and free WiFi with all our rooms?",
                    " Feel free to ask about our spa services, pool facilities, or local attractions anytime!",
                    " Remember, our concierge team is available 24/7 to help with restaurant reservations and local recommendations."
                ]
                response += random.choice(suggestions)

            return response

        except Exception as e:
            logger.error(f"Error handling gratitude intent: {str(e)}")
            # Fallback to simple response
            return "You're welcome! Let me know if you need help with room booking or hotel info."

    def handle_intent(self, intent: str, user_input: str, lang: str = 'en') -> str:
        """Handle detected intent and generate a response."""
        try:
            if intent == 'booking':
                return self.handle_booking_intent(user_input, lang)
            elif intent == 'book_another_room':
                return self.handle_book_another_room_intent(user_input, lang)
            elif intent == 'cancel_booking':
                return self.handle_cancel_booking_intent(user_input, lang)
            elif intent == 'upgrade_room':
                return self.handle_upgrade_intent(user_input, lang)
            elif intent == 'change_date':
                return self.handle_change_date_intent(user_input, lang)
            elif intent == 'extend_stay':
                return self.handle_extend_stay_intent(user_input, lang)
            elif intent == 'express_gratitude':
                # Handle gratitude/thank you messages with context-aware responses
                return self.handle_gratitude_intent(user_input, lang)
            elif intent == 'off_topic':
                # Enhanced off-topic handling with guided responses
                is_off_topic, off_topic_type = self.detect_off_topic_intent(user_input)
                return self.handle_off_topic_redirect(user_input, off_topic_type, lang)
            elif intent == 'invalid_input':
                # Handle invalid/random input with polite guidance
                return self.handle_invalid_input_redirect(user_input, lang)

            responses = self.intents.get(intent, self.intents.get('unknown', {})).get('responses', {}).get(lang, ["I'm not sure I understand."])
            return random.choice(responses) if responses else "I'm not sure I understand."
        except Exception as e:
            logger.error(f"Error handling intent {intent}: {str(e)}")
            return self.intents.get('unknown', {}).get('responses', {}).get(lang, ["I'm not sure I understand."])[0]

    def respond_with_advanced_nlp(self, user_input: str, context: Dict = None) -> str:
        """
        Generate response using advanced NLP capabilities for professional hotel service.
        """
        if not self.advanced_nlp or not self.nlp_enhancement_manager:
            return self.respond(user_input)

        try:
            # Get user ID from context for personalization
            user_id = context.get('user_id') if context else None

            # Use enhanced understanding
            analysis = self.nlp_enhancement_manager.enhance_user_understanding(
                user_input, user_id, context
            )

            # Add to conversation history with enhanced information
            self.conversation_history.append({
                "user": user_input,
                "processed": analysis.get('processed_text', user_input),
                "timestamp": datetime.now().isoformat(),
                "context": context or {},
                "analysis": analysis
            })

            # Check if this is a hotel information inquiry
            if self._is_hotel_info_inquiry(analysis):
                response = self._handle_hotel_info_inquiry(analysis)
            elif analysis["intent"]["name"] == "booking_intent":
                response = self._handle_booking_with_nlp(analysis)
            elif analysis["intent"]["name"] == "complaint":
                response = self._handle_complaint_with_nlp(analysis)
            else:
                # Use enhanced contextual response generation
                response = self.nlp_enhancement_manager.generate_contextual_response(
                    analysis, user_id
                )

            # Add response to conversation history with enhanced information
            self.conversation_history.append({
                "bot": response,
                "timestamp": datetime.now().isoformat(),
                "intent": analysis["intent"]["name"],
                "confidence": analysis["intent"]["confidence"],
                "semantic_confidence": analysis.get("semantic_confidence", 0.0),
                "language": analysis.get("language", "unknown")
            })

            return response

        except Exception as e:
            logger.error(f"Error in advanced NLP processing: {str(e)}")
            return self.respond(user_input)

    def _is_hotel_info_inquiry(self, analysis: Dict) -> bool:
        """Check if the user is asking for hotel information."""
        intent_name = analysis["intent"]["name"]
        return intent_name in ["room_inquiry", "amenity_inquiry", "location_inquiry", "price_inquiry"]

    def _handle_hotel_info_inquiry(self, analysis: Dict) -> str:
        """Handle hotel information inquiries with detailed responses."""
        intent_name = analysis["intent"]["name"]
        entities = analysis["entities"]

        if intent_name == "room_inquiry":
            return self._generate_detailed_room_info(entities)
        elif intent_name == "amenity_inquiry":
            return self._generate_detailed_amenity_info(entities)
        elif intent_name == "location_inquiry":
            return self._generate_detailed_location_info()
        elif intent_name == "price_inquiry":
            return self._generate_detailed_price_info(entities)

        return "I'd be happy to provide information about our hotel. What specific details would you like to know?"

    def _generate_detailed_room_info(self, entities: Dict) -> str:
        """Generate detailed room information with professional hotel service tone."""
        room_types = entities.get("room_types", [])

        if room_types and self.knowledge_base:
            room_type = room_types[0].lower()
            room_info = self.knowledge_base.get_room_info(room_type)
            if room_info:
                return f"""Certainly! I'd be delighted to tell you about our {room_info['name']}.

This {room_info['size']} room comfortably accommodates {room_info['capacity']} and features {room_info['bed_type']}. You'll enjoy amenities including {', '.join(room_info['amenities'][:8])}, and more.

The room offers {room_info['view']} and is priced from {room_info['price_range']}. {room_info['description']}

Would you like to know more about our other room types or perhaps check availability for specific dates?"""

        # General room information
        return """I'd be happy to describe our accommodation options! We offer three distinct room categories:

🏨 **Standard Room** (RM 132/night)
- 28 sqm of comfortable space for 2 adults
- Queen or twin beds, city view
- Perfect for business travelers and couples

🏨 **Deluxe Room** (RM 205/night)
- 35 sqm with enhanced amenities
- King or twin beds, work desk, balcony
- Ideal for extended stays and leisure guests

🏨 **Executive Suite** (RM 321/night)
- 55 sqm luxury accommodation for families
- Separate living area, kitchenette, premium services
- Perfect for VIP guests and special occasions

All rooms include complimentary WiFi, breakfast, and access to our facilities. Which room type interests you most?"""

    def _generate_detailed_amenity_info(self, entities: Dict) -> str:
        """Generate detailed amenity information."""
        amenities = entities.get("amenities", [])

        if "pool" in amenities or "游泳池" in amenities:
            return """Our stunning outdoor infinity pool is one of our signature features!

🏊‍♀️ **Pool Facilities:**
- Open daily from 6:00 AM to 10:00 PM
- Infinity design with city views
- Dedicated children's pool area
- Poolside jacuzzi for relaxation
- Pool bar serving refreshments
- Comfortable loungers and cabanas
- Professional poolside service

The pool area is perfect for both relaxation and recreation. Would you like to know about our other recreational facilities or perhaps our spa services?"""

        # General amenities overview
        return """I'm delighted to share our comprehensive amenities! Our hotel offers:

🍽️ **Dining Options:**
- The Grand Dining: International cuisine (6 AM - 11 PM)
- Lobby Café: 24-hour light meals and artisan coffee
- 24-hour room service

🏊‍♀️ **Recreation:**
- Outdoor infinity pool with jacuzzi
- 24-hour fitness center with modern equipment
- Serenity Spa (9 AM - 9 PM)

💼 **Business Services:**
- 24-hour business center
- Meeting rooms for 10-200 people
- High-speed WiFi throughout

🚗 **Additional Services:**
- Concierge services
- Airport shuttle
- Valet parking

Is there a particular amenity you'd like to know more about?"""

    def _generate_detailed_location_info(self) -> str:
        """Generate detailed location and directions information."""
        if self.knowledge_base:
            location = self.knowledge_base.get_location_info()
            landmarks = location.get("nearby_landmarks", [])

            landmark_info = "\n".join([f"• {landmark['name']}: {landmark['distance']} ({landmark['transport_time']})"
                                     for landmark in landmarks[:4]])

            return f"""We're perfectly positioned in the heart of {location['city']}!

📍 **Our Location:**
{location['address']}

🚗 **Nearby Attractions:**
{landmark_info}

🚌 **Transportation:**
- Complimentary airport shuttle (advance booking required)
- Taxi services available 24/7
- Public transport within 5 minutes walk
- Valet parking available

Our concierge team is always ready to provide detailed directions, arrange transportation, or recommend the best routes to your destinations. Would you like me to help you plan your journey to us?"""

        return "We're conveniently located in the city center with easy access to major attractions, shopping, and transportation hubs. Our concierge can provide detailed directions and arrange transportation for you."

    def _generate_detailed_price_info(self, entities: Dict) -> str:
        """Generate detailed pricing information."""
        return """I'd be happy to provide our current rates! Our pricing varies by season and length of stay:

💰 **Room Rates:**
- Standard Room: RM 132 per night
- Deluxe Room: RM 205 per night
- Executive Suite: RM 321 per night

✨ **What's Included:**
- Complimentary breakfast for all guests
- Free high-speed WiFi
- Access to pool, fitness center, and spa facilities
- 24-hour room service
- Concierge services

🎁 **Special Offers:**
- Extended stay discounts (7+ nights)
- Early booking promotions
- Seasonal packages available

For the most accurate rates for your specific dates, I'd be happy to check availability. When are you planning to visit us?"""

    def _handle_booking_with_nlp(self, analysis: Dict) -> str:
        """Handle booking requests with advanced understanding."""
        entities = analysis["entities"]

        # Extract any booking information from the message
        booking_info = {}
        if entities.get("dates"):
            booking_info["dates_mentioned"] = entities["dates"]
        if entities.get("room_types"):
            booking_info["room_preference"] = entities["room_types"][0]
        if entities.get("numbers"):
            booking_info["guest_count"] = entities["numbers"][0]

        return f"""I'd be absolutely delighted to assist you with your reservation!

To ensure I find the perfect accommodation for you, could you please share:
- Your preferred check-in and check-out dates
- The type of room you're interested in (Standard, Deluxe, or Suite)
- Number of guests

{self._get_room_recommendation_based_on_context(booking_info)}

I'm here to make your booking process as smooth as possible!"""

    def _handle_complaint_with_nlp(self, analysis: Dict) -> str:
        """Handle complaints with professional service recovery."""
        return """I sincerely apologize for any inconvenience you've experienced. Your satisfaction is our absolute priority, and I want to resolve this matter immediately.

Could you please provide me with:
- Your booking reference number or room number
- Specific details about the issue
- How you'd like us to address this concern

I'll personally ensure this is resolved promptly and take steps to prevent it from happening again. Thank you for bringing this to our attention - it helps us maintain our high standards of service."""

    def _get_room_recommendation_based_on_context(self, booking_info: Dict) -> str:
        """Provide room recommendations based on context."""
        if booking_info.get("room_preference"):
            return f"I see you're interested in our {booking_info['room_preference']} rooms - an excellent choice!"

        guest_count = booking_info.get("guest_count")
        if guest_count:
            try:
                count = int(guest_count)
                if count <= 2:
                    return "For your party size, I'd recommend our Standard or Deluxe rooms."
                else:
                    return "For your group, our Executive Suites would provide the most comfortable space."
            except:
                pass

        return "I can recommend the perfect room type based on your specific needs and preferences."

    def respond(self, user_input: str, lang: Optional[str] = None) -> str:
        """Main response method to process user input and generate a reply."""
        try:
            logger.info(f"Processing input: {user_input}")

            # Auto-detect language if not specified
            if lang is None:
                try:
                    lang = detect(user_input)
                    if lang not in ['en', 'zh']:
                        lang = 'en'
                except Exception:
                    lang = 'en'

            logger.info(f"Using language: {lang}")

            # First check for booking intent to start the collection process
            intent = self.detect_intent(user_input)
            logger.info(f"Detected intent: {intent}")

            # Check for room service requests FIRST (before booking intent)
            if self.detect_room_service_request(user_input):
                return self.handle_room_service_request(user_input, lang)

            # Check for booking status inquiry BEFORE booking intent (to avoid confusion)
            # But skip if user has pending cancel intent
            if self.detect_status_inquiry(user_input) and not self.user_data.get('pending_cancel_intent'):
                return self.handle_status_inquiry(user_input, lang)

            # Check if user input looks like a booking ID (for direct status check)
            # But skip if user has pending cancel intent
            import re
            booking_id_match = re.search(r'\b([A-Z]{2,}-[A-Z0-9-]+)\b', user_input, re.IGNORECASE)
            if booking_id_match and not self.user_data.get('pending_cancel_intent') and self.state == "greeting":
                return self.handle_status_inquiry(user_input)

            # If booking intent detected and we're not already collecting info or in other booking flows, start the process
            booking_flow_states = [
                'collecting_booking_info', 'selecting_additional_room_type', 'confirming_additional_dates',
                'collecting_additional_dates', 'confirming_additional_booking', 'collecting_parent_booking_id',
                'selecting_upgrade_room', 'collecting_booking_id_for_upgrade'  # Add upgrade states to prevent conflicts
            ]
            if intent == 'booking' and self.state not in booking_flow_states:
                return self.handle_booking_intent(user_input, lang)

            # Check for feedback/rating intent
            if self.detect_feedback_intent(user_input):
                return self.handle_feedback_intent(user_input, lang)

            # Check for change date intent BEFORE hotel info (to avoid conflicts)
            if self.detect_change_date_intent(user_input) and self.state not in ["collecting_booking_id_for_change_date", "collecting_new_check_in_date", "confirming_date_change"]:
                return self.handle_change_date_intent(user_input, lang)

            # Check for common hotel questions
            if self.detect_hotel_info_question(user_input):
                return self.handle_hotel_info_question(user_input, lang)

            # Check if user is responding to service menu
            if self.user_data.get('showing_service_menu'):
                is_service_response, service_type = self.detect_service_menu_response(user_input)
                if is_service_response:
                    return self.handle_service_menu_response(user_input, service_type, lang)

            # Check if user is responding to room service menu
            if self.user_data.get('showing_room_service_menu'):
                is_room_service_response, room_service_type = self.detect_room_service_menu_response(user_input)
                if is_room_service_response:
                    return self.handle_room_service_menu_response(user_input, room_service_type, lang)

            # Check for off-topic queries (before other intents)
            # Allow off-topic detection in greeting state and when not in specific conversation flows
            non_conversational_states = ["greeting", "booking_confirmed", "offering_addons"]
            is_off_topic, off_topic_type = self.detect_off_topic_intent(user_input)
            if is_off_topic and self.state in non_conversational_states:
                return self.handle_off_topic_redirect(user_input, off_topic_type, lang)

            # Check for cancellation intent
            if self.detect_cancel_intent(user_input):
                return self.handle_cancel_intent(user_input, lang)

            # Check for upgrade intent (but not during booking process)
            if (self.detect_upgrade_intent(user_input) and
                self.state not in ["collecting_booking_id_for_upgrade", "selecting_upgrade_room",
                                 "collecting_booking_info", "selecting_room_type", "booking_confirmed", "offering_addons"]):
                return self.handle_upgrade_intent(user_input, lang)

            # Check for extend intent
            if self.detect_extend_intent(user_input) and self.state not in ["collecting_booking_id_for_extend", "selecting_extend_date"]:
                return self.handle_extend_intent(user_input, lang)

            # Check for breakfast service request (standalone)
            if (self.detect_breakfast_request(user_input) and
                self.state not in ["offering_addons", "collecting_breakfast_count", "confirming_breakfast", "collecting_booking_id_for_breakfast"]):
                return self.handle_breakfast_request(user_input, lang)

            # Handle addon service requests
            if self.state == "offering_addons":
                return self.handle_addon_request(user_input, lang)
            elif self.state == "collecting_breakfast_count":
                return self.handle_breakfast_count(user_input, lang)
            elif self.state == "confirming_breakfast":
                return self.handle_breakfast_confirmation(user_input, lang)
            elif self.state == "collecting_booking_id_for_breakfast":
                return self.handle_breakfast_booking_id(user_input, lang)


            # Handle booking management requests
            elif self.state == "collecting_booking_id_for_cancel":
                return self.handle_cancel_booking_id(user_input, lang)
            elif self.state == "confirming_cancellation":
                return self.handle_cancel_confirmation(user_input, lang)
            elif self.state == "collecting_booking_id_for_upgrade":
                return self.handle_upgrade_booking_id(user_input, lang)
            elif self.state == "selecting_upgrade_room":
                return self.handle_upgrade_selection(user_input, lang)
            elif self.state == "collecting_booking_id_for_extend":
                return self.handle_extend_booking_id(user_input, lang)
            elif self.state == "selecting_extend_date":
                return self.handle_extend_date_selection(user_input, lang)
            elif self.state == "collecting_booking_id_for_status":
                return self.handle_status_booking_id(user_input, lang)
            elif self.state == "collecting_booking_info_for_status":
                return self.handle_booking_info_collection_for_status(user_input, lang)
            elif self.state == "selecting_booking_from_multiple":
                return self.handle_multiple_booking_selection(user_input, lang)
            elif self.state == "collecting_feedback_rating":
                return self.handle_feedback_rating(user_input, lang)
            elif self.state == "collecting_feedback_comment":
                return self.handle_feedback_comment(user_input, lang)
            elif self.state == "collecting_booking_id_for_room_service":
                return self.handle_room_service_booking_id(user_input, lang)
            elif self.state == "selecting_cleaning_time":
                return self.handle_cleaning_time_selection(user_input, lang)
            elif self.state == "collecting_booking_id_for_change_date":
                return self.handle_change_date_booking_id(user_input, lang)
            elif self.state == "collecting_new_check_in_date":
                return self.handle_new_check_in_date(user_input, lang)
            elif self.state == "confirming_date_change":
                # Check if we're already processing to prevent duplicate confirmations
                if self.user_data.get('processing_date_change', False):
                    return "Your date change is already being processed. Please wait a moment..."
                return self.handle_date_change_confirmation(user_input, lang)

            # Handle book another room states
            elif self.state == "collecting_parent_booking_id":
                return self.handle_parent_booking_id(user_input, lang)
            elif self.state == "selecting_additional_room_type":
                return self.handle_additional_room_selection(user_input, lang)
            elif self.state == "confirming_additional_dates":
                return self.handle_additional_dates_confirmation(user_input, lang)
            elif self.state == "collecting_additional_dates":
                return self.handle_additional_dates_collection(user_input, lang)
            elif self.state == "confirming_additional_booking":
                return self.handle_additional_booking_confirmation(user_input, lang)


            # Special handling during booking information collection
            if self.state == "collecting_booking_info":
                # Extract any information from the current message
                booking_info = self.extract_booking_info(user_input, self.user_data)
                if booking_info:
                    self.user_data.update(booking_info)
                    logger.info(f"Updated user data: {self.user_data}")

                # Check if we have all required information
                if self.is_booking_info_complete(self.user_data):
                    # Generate booking ID and confirm
                    booking_id = f"BK-{random.randint(10000, 99999)}"
                    self.user_data['booking_id'] = booking_id
                    self.state = "booking_confirmed"

                    # Create actual booking record in database
                    try:
                        actual_booking_id = self.create_booking_record(self.user_data)
                        if actual_booking_id:
                            self.user_data['booking_id'] = actual_booking_id
                            logger.info(f"Booking record created successfully: {actual_booking_id}")
                        else:
                            logger.warning("Failed to create booking record, using generated ID")
                    except Exception as e:
                        logger.error(f"Error creating booking record: {str(e)}")

                    # Set up delayed success message with addon offer
                    self.delayed_messages = [{
                        'message': f"🎉 <strong>Booking Successful!</strong> 🎉<br><br>✅ <strong>Booking Confirmation</strong><br>📋 <strong>Booking ID:</strong> {self.user_data.get('booking_id', 'N/A')}<br>👤 <strong>Guest Name:</strong> {self.user_data.get('guest_name', 'N/A')}<br>📱 <strong>Phone:</strong> {self.user_data.get('phone', 'N/A')}<br>📧 <strong>Email:</strong> {self.user_data.get('email', 'N/A')}<br>🏨 <strong>Room Type:</strong> {self.user_data.get('room_type', 'N/A')}<br>📅 <strong>Check-in:</strong> {self.user_data.get('check_in_date', 'N/A')}<br>📅 <strong>Check-out:</strong> {self.user_data.get('check_out_date', 'N/A')}<br><br>Booking is successful! Would you like to add breakfast service?<br>🍳 <strong>Breakfast service</strong> (RM20/person)<br><br>Type 'breakfast' to add it or 'no thanks' to skip.",
                        'delay': 5
                    }]
                    self.state = "offering_addons"
                    return f"<img src='{self.qr_code_path}' alt='Payment QR Code' class='img-fluid rounded' style='max-width: 300px;'><br>Please scan the QR code to complete your payment."
                else:
                    # Ask for missing information
                    return self.ask_for_missing_info(self.user_data)

            # Handle confirmation during booking confirmed state
            if self.state == "booking_confirmed" and user_input.lower().strip() in ['yes', 'confirm', 'ok', 'proceed']:
                return "Perfect! Your booking is being processed. You will receive a confirmation email shortly."

            # Try advanced NLP for other intents if available (but not for addon states)
            if (self.advanced_nlp and len(user_input.strip()) > 5 and intent not in ['booking'] and
                self.state not in ["offering_addons", "collecting_breakfast_count", "confirming_breakfast", "collecting_booking_id_for_breakfast"]):
                try:
                    advanced_response = self.respond_with_advanced_nlp(user_input, {"state": self.state, "user_data": self.user_data})
                    if advanced_response and len(advanced_response) > 20:  # Ensure we got a substantial response
                        return advanced_response
                except Exception as e:
                    logger.warning(f"Advanced NLP failed, falling back to basic: {str(e)}")

            # Handle sentiment analysis
            sentiment, confidence = self.analyze_sentiment(user_input)
            logger.info(f"Sentiment analysis: {sentiment} (confidence: {confidence:.2f})")

            if sentiment == "Negative" and confidence > 0.7:
                apology = "I'm sorry to hear that. How can I better assist you? " if lang == 'en' else "很抱歉听到这个。我怎样才能更好地帮助您？"
                regular_response = self.handle_intent(intent, user_input, lang)
                return apology + regular_response
            elif sentiment == "Positive" and confidence > 0.7:
                prefix = "Great to hear you're excited! " if lang == 'en' else "很高兴您这么兴奋！"
                regular_response = self.handle_intent(intent, user_input, lang)
                return prefix + regular_response

            response = self.handle_intent(intent, user_input, lang)
            logger.info(f"Generated response: {response}")
            return response

        except Exception as e:
            logger.error(f"Error in response generation: {str(e)}")
            return "Sorry, I encountered an error. Please try again later." if lang == 'en' else "抱歉，我遇到了一个错误。请稍后再试。"

    def create_booking_record(self, user_data: Dict) -> Optional[str]:
        """Create a booking record in the database and return the booking ID."""
        try:
            # Import Django models here to avoid circular imports
            from hotel_booking.models import Room, Booking
            from datetime import datetime
            import dateutil.parser

            # Find the room by type
            room_type = user_data.get('room_type', '')
            room = Room.objects.filter(name__icontains=room_type).first()
            if not room:
                # Default to first available room if specific type not found
                room = Room.objects.first()
                logger.warning(f"Room type '{room_type}' not found, using default room: {room.name if room else 'None'}")

            if not room:
                logger.error("No rooms available in the database")
                return None

            # Parse dates
            try:
                check_in_str = user_data.get('check_in_date')
                check_out_str = user_data.get('check_out_date')

                if check_in_str and check_out_str:
                    # Try different date formats
                    try:
                        check_in = datetime.strptime(check_in_str, '%Y-%m-%d').date()
                    except ValueError:
                        check_in = dateutil.parser.parse(check_in_str).date()

                    try:
                        check_out = datetime.strptime(check_out_str, '%Y-%m-%d').date()
                    except ValueError:
                        check_out = dateutil.parser.parse(check_out_str).date()
                else:
                    logger.error("Missing check-in or check-out dates")
                    return None

            except Exception as e:
                logger.error(f"Error parsing dates: {str(e)}")
                return None

            # Create booking record
            booking = Booking.objects.create(
                room=room,
                guest_name=user_data.get('guest_name', ''),
                guest_email=user_data.get('email', ''),
                guest_phone=user_data.get('phone', ''),
                check_in_date=check_in,
                check_out_date=check_out,
                status='confirmed',  # Set as confirmed since payment QR is shown
                booking_id=user_data.get('booking_id'),
                user=user_data.get('user')  # Associate with the current user
            )

            logger.info(f"Booking created successfully: ID={booking.id}, Booking_ID={booking.booking_id}")
            return booking.booking_id or f"BK-{booking.id}"

        except Exception as e:
            logger.error(f"Error creating booking record: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return None

    def handle_addon_request(self, user_input: str, lang: str = 'en') -> str:
        """Handle addon service requests after booking confirmation."""
        try:
            user_input_lower = user_input.lower().strip()

            # Check for breakfast keywords
            breakfast_keywords = ['breakfast', '早餐', 'morning meal', 'morning food']
            no_keywords = ['no', 'skip', 'not interested', 'no thanks', '不要', '跳过']

            # Initialize addon selection tracking if not exists
            if 'addon_selections' not in self.user_data:
                self.user_data['addon_selections'] = []

            # Check for breakfast service selection
            if any(keyword in user_input_lower for keyword in breakfast_keywords):
                if 'breakfast' not in self.user_data['addon_selections']:
                    self.user_data['addon_selections'].append('breakfast')
                self.state = "collecting_breakfast_count"
                return "Breakfast service is RM20/person. How many guests do you need to add breakfast for?"

            elif any(keyword in user_input_lower for keyword in no_keywords):
                self.state = "greeting"
                self.user_data = {'is_returning_customer': True}  # Reset but keep returning customer status
                return "No problem! Your booking is complete. Thank you for choosing our hotel! Is there anything else I can help you with?"

            else:
                return "Would you like to add:\n🍳 **Breakfast service** (RM20/person)\n\nOr type 'no thanks' if you don't need any additional services."

        except Exception as e:
            logger.error(f"Error handling addon request: {str(e)}")
            return "Sorry, I encountered an error processing your addon request. Please try again."

    def handle_breakfast_count(self, user_input: str, lang: str = 'en') -> str:
        """Handle breakfast guest count input."""
        try:
            user_input_lower = user_input.lower().strip()

            # Check for cancellation/decline keywords first
            decline_keywords = ['no', 'no thanks', 'no thank you', 'skip', 'not interested',
                              'cancel', 'nevermind', 'never mind', 'dont want', "don't want",
                              'not now', 'maybe later', 'decline', 'pass']

            if any(keyword in user_input_lower for keyword in decline_keywords):
                self.state = "greeting"
                self.user_data = {'is_returning_customer': True}
                return "No problem! Your booking is complete without breakfast service. Thank you for choosing our hotel! Is there anything else I can help you with?"

            # Extract number from input
            import re
            numbers = re.findall(r'\d+', user_input)

            if numbers:
                count = int(numbers[0])
                if count > 0 and count <= 10:  # Reasonable limit
                    self.user_data['breakfast_count'] = count
                    total_cost = count * 20

                    # Move to confirmation state
                    self.state = "confirming_breakfast"
                    return f"OK, add breakfast for {count} guest(s), a total of RM{total_cost}.\nAre you sure to book breakfast?\nA. Yes\nB. No"
                else:
                    return "Please provide a valid number of guests (1-10) for breakfast service."
            else:
                return "Please tell me how many guests would like breakfast service. For example, type '2' for 2 guests."

        except Exception as e:
            logger.error(f"Error handling breakfast count: {str(e)}")
            return "Sorry, I encountered an error. Please tell me how many guests need breakfast service."
    def handle_breakfast_confirmation(self, user_input: str, lang: str = 'en') -> str:
        """Handle breakfast booking confirmation."""
        try:
            user_input_lower = user_input.lower().strip()

            # Check for positive confirmation
            if user_input_lower in ['yes', 'y', 'a', 'confirm', 'ok', 'sure', 'book it', 'proceed']:
                # Check if this breakfast confirmation has already been processed
                if self.user_data.get('breakfast_confirmed', False):
                    # Already processed, just return to greeting
                    self.state = "greeting"
                    self.user_data = {'is_returning_customer': True}
                    return "Your breakfast service has already been processed. Is there anything else I can help you with?"

                count = self.user_data.get('breakfast_count', 0)
                total_cost = count * 20

                # Mark as confirmed to prevent duplicate processing
                self.user_data['breakfast_confirmed'] = True

                # Create addon record
                success = self.create_addon_record('breakfast', 20, breakfast_count=count)

                if success:
                    # Reset state
                    self.state = "greeting"
                    self.user_data = {'is_returning_customer': True}  # Reset but keep returning customer status
                    return f"Your breakfast service has been booked successfully and the fee will be charged to the room account. Breakfast is served from 6am to 11am. Enjoy your meal!"
                else:
                    self.state = "greeting"
                    self.user_data = {'is_returning_customer': True}
                    return f"Your breakfast service for {count} guest(s) has been added to your booking. Total cost: RM{total_cost}. Breakfast is served from 6am to 11am. Enjoy your meal!"

            elif user_input_lower in ['no', 'n', 'b', 'cancel', 'nevermind', 'never mind']:
                self.state = "greeting"
                self.user_data = {'is_returning_customer': True}  # Reset but keep returning customer status
                return "No problem! Your booking is complete without breakfast service. Thank you for choosing our hotel! Is there anything else I can help you with?"
            else:
                return "Please reply 'Yes' (or A) to confirm the breakfast booking or 'No' (or B) to cancel."

        except Exception as e:
            logger.error(f"Error handling breakfast confirmation: {str(e)}")
            return "Sorry, I encountered an error. Please reply 'Yes' to confirm or 'No' to cancel."
    def detect_breakfast_request(self, user_input: str) -> bool:
        """Detect if user is requesting breakfast service."""
        breakfast_keywords = [
            'breakfast', 'add breakfast', 'order breakfast', 'book breakfast',
            'breakfast service', 'morning meal', 'morning food', 'breakfast booking',
            'i want breakfast', 'need breakfast', 'breakfast please', 'breakfast for',
            'how much breakfast', 'is breakfast included', 'breakfast cost', 'breakfast price'
        ]

        user_input_lower = user_input.lower().strip()
        return any(keyword in user_input_lower for keyword in breakfast_keywords)

    def handle_breakfast_request(self, user_input: str, lang: str = 'en') -> str:
        """Handle standalone breakfast service request."""
        try:
            # Check if we have a recently viewed booking
            last_booking = self.user_data.get('last_viewed_booking')
            if last_booking and last_booking.get('booking_id'):
                # Use the last viewed booking for breakfast service
                booking_id = last_booking['booking_id']
                self.user_data['booking_id'] = booking_id
                self.state = "collecting_breakfast_count"
                return "I'd be happy to help you add breakfast service! Breakfast service is RM20/person. How many guests do you need to add breakfast for?"

            # Ask for booking ID
            self.state = "collecting_booking_id_for_breakfast"
            return "I'd be happy to help you add breakfast service! To add this service to your reservation, please provide your booking ID."

        except Exception as e:
            logger.error(f"Error handling breakfast request: {str(e)}")
            return "I'd be happy to help you add breakfast service! Please provide your booking ID first so I can add this service to your reservation."

    def handle_breakfast_booking_id(self, user_input: str, lang: str = 'en') -> str:
        """Handle booking ID input for breakfast service."""
        try:
            import re

            # Extract booking ID from input
            booking_id_match = re.search(r'\b([A-Z]{2,}-[A-Z0-9-]+)\b', user_input, re.IGNORECASE)
            if booking_id_match:
                booking_id = booking_id_match.group(1)
                logger.info(f"Extracted booking ID: {booking_id}")

                # Verify booking exists
                from hotel_booking.models import Booking
                booking = Booking.objects.filter(booking_id=booking_id).first()
                logger.info(f"Booking found: {booking is not None}")

                if booking:
                    # Store booking info
                    self.user_data['booking_id'] = booking_id
                    logger.info(f"Stored booking ID in user_data: {booking_id}")

                    # Move to breakfast count collection
                    self.state = "collecting_breakfast_count"
                    return f"Great! I found your booking (ID: {booking_id}) for guest {booking.guest_name}. Breakfast service is RM20/person. How many guests do you need to add breakfast for?"
                else:
                    logger.warning(f"Booking not found: {booking_id}")
                    return f"I couldn't find a booking with ID '{booking_id}'. Please check your booking ID and try again."
            else:
                logger.warning(f"No valid booking ID found in input: {user_input}")
                return "Please provide a valid booking ID (e.g., BK-12345 or HTL-ABC123)."

        except Exception as e:
            logger.error(f"Error handling breakfast booking ID: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return "Sorry, I encountered an error. Please provide your booking ID again."







    def create_addon_record(self, addon_type: str, price: float, **kwargs) -> bool:
        """Create an addon record in the database."""
        try:
            from hotel_booking.models import Booking, BookingAddon

            # Find the booking
            booking_id = self.user_data.get('booking_id')
            if not booking_id:
                logger.error("No booking ID found for addon creation")
                return False

            booking = Booking.objects.filter(booking_id=booking_id).first()
            if not booking:
                logger.error(f"Booking not found: {booking_id}")
                return False

            # Create addon record
            addon_data = {
                'booking': booking,
                'addon_type': addon_type,
                'price': price
            }

            # Add specific fields based on addon type
            if addon_type == 'breakfast':
                addon_data['breakfast_count'] = kwargs.get('breakfast_count')

            addon = BookingAddon.objects.create(**addon_data)
            logger.info(f"Addon created successfully: {addon}")
            return True

        except Exception as e:
            logger.error(f"Error creating addon record: {str(e)}")
            return False

    def detect_cancel_intent(self, user_input: str) -> bool:
        """Detect if user wants to cancel a booking."""
        cancel_keywords = [
            'cancel', 'cancellation', 'cancel my booking', 'cancel my reservation',
            'cancel order', 'i want to cancel', "i'm not going", 'cancel it',
            'cancel booking', 'cancel room', 'refund', 'cansel'  # Include common misspelling
        ]

        user_input_lower = user_input.lower().strip()
        return any(keyword in user_input_lower for keyword in cancel_keywords)

    def handle_cancel_intent(self, user_input: str, lang: str = 'en') -> str:
        """Handle cancellation request."""
        try:
            # Check if we have a recently viewed booking
            last_booking = self.user_data.get('last_viewed_booking')
            if last_booking and last_booking.get('booking_id'):
                # Use the last viewed booking for cancellation
                booking_id = last_booking['booking_id']
                self.user_data['cancel_booking_id'] = booking_id
                return self.verify_booking_for_cancel(booking_id, lang)

            # Check if booking ID is mentioned in the input
            import re
            # Look for booking ID patterns like BK-12345, CANCEL-TEST-001, etc.
            booking_id_match = re.search(r'(?:order|booking|reservation)\s*(?:number|id)?\s*([A-Z0-9-]+)', user_input, re.IGNORECASE)

            # If not found with keywords, try to find any alphanumeric pattern that looks like a booking ID
            if not booking_id_match:
                booking_id_match = re.search(r'\b([A-Z]{2,}-[A-Z0-9-]+)\b', user_input, re.IGNORECASE)

            if booking_id_match:
                booking_id = booking_id_match.group(1)
                self.user_data['cancel_booking_id'] = booking_id
                return self.verify_booking_for_cancel(booking_id, lang)
            else:
                # Set state to remember user wants to cancel
                self.state = "collecting_booking_id_for_cancel"
                # Set a flag to remember the cancel intent
                self.user_data['pending_cancel_intent'] = True
                return "I'd be happy to help you cancel your booking. Please provide your booking ID or booking name, and I will help you check the booking information."

        except Exception as e:
            logger.error(f"Error handling cancel intent: {str(e)}")
            return "Sorry, I encountered an error processing your cancellation request. Please try again."

    def handle_cancel_booking_id(self, user_input: str, lang: str = 'en') -> str:
        """Handle booking ID input for cancellation."""
        try:
            # Extract booking ID from input
            import re
            booking_id_match = re.search(r'([A-Z0-9-]+)', user_input, re.IGNORECASE)

            if booking_id_match:
                booking_id = booking_id_match.group(1)
                self.user_data['cancel_booking_id'] = booking_id
                # Clear the pending cancel intent flag since we're processing it
                self.user_data.pop('pending_cancel_intent', None)
                return self.verify_booking_for_cancel(booking_id, lang)
            else:
                return "Please provide a valid booking ID. For example: BK-12345 or TEST-001"

        except Exception as e:
            logger.error(f"Error handling cancel booking ID: {str(e)}")
            return "Sorry, I encountered an error. Please provide your booking ID again."

    def verify_booking_for_cancel(self, booking_id: str, lang: str = 'en') -> str:
        """Verify booking exists and show details for cancellation confirmation."""
        try:
            from hotel_booking.models import Booking

            # Find booking by ID
            booking = Booking.objects.filter(booking_id=booking_id).first()

            if not booking:
                self.state = "collecting_booking_id_for_cancel"
                return f"I couldn't find a booking with ID {booking_id}. Please check your booking ID and try again."

            # Store booking for confirmation
            self.user_data['booking_to_cancel'] = {
                'id': booking.id,
                'booking_id': booking.booking_id,
                'room_name': booking.room.name,
                'guest_name': booking.guest_name,
                'check_in': booking.check_in_date.strftime('%B %d'),
                'check_out': booking.check_out_date.strftime('%B %d'),
                'status': booking.status
            }

            # Check if booking can be cancelled
            if booking.status == 'cancelled':
                self.state = "greeting"
                return f"This booking ({booking_id}) has already been cancelled."

            self.state = "confirming_cancellation"
            return f"I found your booking! You have booked a {booking.room.name} with check-in dates from {booking.check_in_date.strftime('%B %d')} to {booking.check_out_date.strftime('%B %d')}. Are you sure you want to cancel? (Reply 'Yes' to confirm)"

        except Exception as e:
            logger.error(f"Error verifying booking for cancel: {str(e)}")
            return "Sorry, I encountered an error checking your booking. Please try again."

    def handle_cancel_confirmation(self, user_input: str, lang: str = 'en') -> str:
        """Handle cancellation confirmation."""
        try:
            user_input_lower = user_input.lower().strip()

            if user_input_lower in ['yes', 'y', 'confirm', 'ok', 'sure']:
                # Check if this cancellation has already been processed
                if self.user_data.get('cancellation_confirmed', False):
                    # Already processed, just return to greeting
                    self.state = "greeting"
                    self.user_data = {'is_returning_customer': True}
                    return "Your cancellation has already been processed. Is there anything else I can help you with?"

                # Mark as confirmed to prevent duplicate processing
                self.user_data['cancellation_confirmed'] = True
                return self.process_cancellation(lang)
            elif user_input_lower in ['no', 'n', 'cancel', 'nevermind', 'never mind']:
                self.state = "greeting"
                self.user_data = {'is_returning_customer': True}
                return "No problem! Your booking remains active. Is there anything else I can help you with?"
            else:
                return "Please reply 'Yes' to confirm the cancellation or 'No' to keep your booking."

        except Exception as e:
            logger.error(f"Error handling cancel confirmation: {str(e)}")
            return "Sorry, I encountered an error. Please reply 'Yes' to confirm or 'No' to cancel."

    def process_cancellation(self, lang: str = 'en') -> str:
        """Process the actual cancellation."""
        try:
            from hotel_booking.models import Booking

            booking_data = self.user_data.get('booking_to_cancel')
            if not booking_data:
                return "Sorry, I lost track of your booking information. Please start the cancellation process again."

            # Find and update booking
            booking = Booking.objects.get(id=booking_data['id'])
            booking.status = 'cancelled'
            booking.save()

            booking_id = booking_data['booking_id']

            # Reset state
            self.state = "greeting"
            self.user_data = {'is_returning_customer': True}

            return f"Your reservation has been successfully canceled, order number {booking_id}. I hope to have the opportunity to serve you in the future!"

        except Exception as e:
            logger.error(f"Error processing cancellation: {str(e)}")
            return "Sorry, I encountered an error while cancelling your booking. Please contact our support team for assistance."

    def detect_book_another_room_intent(self, user_input: str) -> bool:
        """Detect if user wants to book another room."""
        book_another_keywords = [
            'book another room', 'book one more room', 'book additional room',
            'book a second room', 'book second room', 'another room',
            'one more room', 'additional room', 'second room',
            'my friend also wants', 'friend wants room', 'friend needs room',
            'book for my friend', 'book room for friend', 'group booking',
            'family needs another', 'we need another room', 'need one more',
            'can i book another', 'want to book another', 'add another room',
            'book extra room', 'extra room', 'more rooms'
        ]

        user_input_lower = user_input.lower().strip()
        return any(keyword in user_input_lower for keyword in book_another_keywords)

    def handle_book_another_room_intent(self, user_input: str, lang: str = 'en') -> str:
        """Handle book another room request."""
        try:
            # Check if user has a recent booking to link to
            last_booking = self.user_data.get('last_viewed_booking')
            if last_booking and last_booking.get('booking_id'):
                # Use the last viewed booking as the parent booking
                self.user_data['parent_booking'] = last_booking
                self.user_data['is_additional_booking'] = True

                # Extract any room type mentioned in the input
                room_info = self.extract_booking_info(user_input, {})
                if room_info and room_info.get('room_type'):
                    self.user_data.update(room_info)

                self.state = "selecting_additional_room_type"
                return self.show_room_types_for_additional_booking(lang)
            else:
                # No recent booking found, ask for booking ID
                self.state = "collecting_parent_booking_id"
                return "I'd be happy to help you book another room! To link it with your existing reservation, please provide your current booking ID."

        except Exception as e:
            logger.error(f"Error handling book another room intent: {str(e)}")
            return "Sorry, I encountered an error processing your additional room request. Please try again."

    def show_room_types_for_additional_booking(self, lang: str = 'en') -> str:
        """Show available room types for additional booking."""
        try:
            from hotel_booking.models import Room

            # Get available room types
            rooms = Room.objects.all().order_by('price')

            if not rooms.exists():
                return "Sorry, no rooms are currently available. Please contact our front desk for assistance."

            room_options = []
            for i, room in enumerate(rooms, 1):
                room_options.append(f"{chr(64+i)}. {room.name} (RM{room.price}/night)")

            room_list = "\n".join(room_options)

            parent_booking = self.user_data.get('parent_booking', {})
            parent_room = parent_booking.get('room_name', 'your current booking')

            return f"""Perfect! I'll help you book an additional room to go with {parent_room}.

What room type would you like for the additional booking?

{room_list}

Please select the room type (A, B, C, etc.) or tell me the room name."""

        except Exception as e:
            logger.error(f"Error showing room types for additional booking: {str(e)}")
            return "Sorry, I encountered an error loading room options. Please try again."

    def handle_parent_booking_id(self, user_input: str, lang: str = 'en') -> str:
        """Handle parent booking ID input for additional room booking."""
        try:
            import re

            # Extract booking ID from input
            booking_id_match = re.search(r'([A-Z0-9-]+)', user_input, re.IGNORECASE)

            if booking_id_match:
                booking_id = booking_id_match.group(1)

                # Verify booking exists
                from hotel_booking.models import Booking
                booking = Booking.objects.filter(booking_id=booking_id).first()

                if booking:
                    # Store parent booking info
                    self.user_data['parent_booking'] = {
                        'id': booking.id,
                        'booking_id': booking.booking_id,
                        'guest_name': booking.guest_name,
                        'room_name': booking.room.name,
                        'check_in_date': booking.check_in_date,
                        'check_out_date': booking.check_out_date
                    }
                    self.user_data['is_additional_booking'] = True

                    self.state = "selecting_additional_room_type"
                    return self.show_room_types_for_additional_booking(lang)
                else:
                    return f"I couldn't find a booking with ID '{booking_id}'. Please check your booking ID and try again."
            else:
                return "Please provide a valid booking ID (e.g., BK-12345)."

        except Exception as e:
            logger.error(f"Error handling parent booking ID: {str(e)}")
            return "Sorry, I encountered an error. Please provide your booking ID again."

    def handle_additional_room_selection(self, user_input: str, lang: str = 'en') -> str:
        """Handle additional room type selection."""
        try:
            from hotel_booking.models import Room

            user_input_lower = user_input.lower().strip()

            # Try to match room selection by letter (A, B, C) or name
            rooms = Room.objects.all().order_by('price')
            selected_room = None

            # Check for letter selection (A, B, C, etc.)
            if len(user_input_lower) == 1 and user_input_lower.isalpha():
                room_index = ord(user_input_lower.upper()) - ord('A')
                if 0 <= room_index < rooms.count():
                    selected_room = list(rooms)[room_index]

            # Check for room name match
            if not selected_room:
                for room in rooms:
                    if room.name.lower() in user_input_lower or any(word in user_input_lower for word in room.name.lower().split()):
                        selected_room = room
                        break

            if selected_room:
                # Store selected room info
                self.user_data['additional_room_type'] = selected_room.name
                self.user_data['additional_room_price'] = float(selected_room.price)

                # Check if dates should be same as parent booking
                parent_booking = self.user_data.get('parent_booking', {})

                self.state = "confirming_additional_dates"
                return f"""Great! You've selected {selected_room.name} (RM{selected_room.price}/night) for your additional booking.

Your current booking is from {parent_booking.get('check_in_date', 'N/A')} to {parent_booking.get('check_out_date', 'N/A')}.

Should the additional room have the same check-in and check-out dates?

A. Yes (use same dates)
B. No (select different dates)"""
            else:
                return "I didn't understand your room selection. Please choose a room type by letter (A, B, C) or tell me the room name."

        except Exception as e:
            logger.error(f"Error handling additional room selection: {str(e)}")
            return "Sorry, I encountered an error processing your room selection. Please try again."

    def handle_additional_dates_confirmation(self, user_input: str, lang: str = 'en') -> str:
        """Handle confirmation of dates for additional booking."""
        try:
            user_input_lower = user_input.lower().strip()
            parent_booking = self.user_data.get('parent_booking', {})

            if user_input_lower in ['a', 'yes', 'same', 'same dates', 'use same dates']:
                # Use same dates as parent booking
                self.user_data['additional_check_in_date'] = parent_booking.get('check_in_date')
                self.user_data['additional_check_out_date'] = parent_booking.get('check_out_date')

                # Auto-fill guest info from parent booking
                self.user_data['guest_name'] = parent_booking.get('guest_name', '')

                self.state = "confirming_additional_booking"
                return self.show_additional_booking_summary()

            elif user_input_lower in ['b', 'no', 'different', 'different dates', 'select different']:
                # Ask for different dates
                self.state = "collecting_additional_dates"
                return "Please provide the check-in and check-out dates for the additional room (e.g., 'June 15 to June 18' or '15/06/2025 to 18/06/2025')."

            else:
                return "Please choose:\nA. Yes (use same dates)\nB. No (select different dates)"

        except Exception as e:
            logger.error(f"Error handling additional dates confirmation: {str(e)}")
            return "Sorry, I encountered an error. Please choose A for same dates or B for different dates."

    def handle_additional_dates_collection(self, user_input: str, lang: str = 'en') -> str:
        """Handle collection of different dates for additional booking."""
        try:
            # Parse the dates from user input
            dates_info = self.extract_dates(user_input)

            if not dates_info:
                return "I couldn't understand the date format. Please provide the check-in and check-out dates (e.g., 'June 15 to June 18' or '15/06/2025 to 18/06/2025')."

            check_in_date = dates_info.get('check_in')
            check_out_date = dates_info.get('check_out')

            if not check_in_date or not check_out_date:
                return "Please provide both check-in and check-out dates (e.g., 'June 15 to June 18' or '15/06/2025 to 18/06/2025')."

            # Validate dates
            from datetime import datetime, date
            today = date.today()

            check_in = datetime.strptime(check_in_date, '%Y-%m-%d').date()
            check_out = datetime.strptime(check_out_date, '%Y-%m-%d').date()

            if check_in < today:
                return "The check-in date cannot be in the past. Please choose a future date."

            if check_out <= check_in:
                return "The check-out date must be after the check-in date. Please provide valid dates."

            # Store the dates
            self.user_data['additional_check_in_date'] = check_in_date
            self.user_data['additional_check_out_date'] = check_out_date

            # Auto-fill guest info from parent booking
            parent_booking = self.user_data.get('parent_booking', {})
            self.user_data['guest_name'] = parent_booking.get('guest_name', '')

            self.state = "confirming_additional_booking"
            return self.show_additional_booking_summary()

        except Exception as e:
            logger.error(f"Error handling additional dates collection: {str(e)}")
            return "Sorry, I encountered an error processing the dates. Please provide the check-in and check-out dates again (e.g., 'June 15 to June 18')."

    def show_additional_booking_summary(self) -> str:
        """Show summary of additional booking for confirmation."""
        try:
            parent_booking = self.user_data.get('parent_booking', {})
            room_type = self.user_data.get('additional_room_type', 'N/A')
            room_price = self.user_data.get('additional_room_price', 0)
            check_in = self.user_data.get('additional_check_in_date', 'N/A')
            check_out = self.user_data.get('additional_check_out_date', 'N/A')
            guest_name = self.user_data.get('guest_name', 'N/A')

            # Calculate duration and total price
            if check_in != 'N/A' and check_out != 'N/A':
                from datetime import datetime
                if isinstance(check_in, str):
                    check_in_date = datetime.strptime(str(check_in), '%Y-%m-%d').date()
                    check_out_date = datetime.strptime(str(check_out), '%Y-%m-%d').date()
                else:
                    check_in_date = check_in
                    check_out_date = check_out

                duration = (check_out_date - check_in_date).days
                total_price = duration * room_price
            else:
                duration = 1
                total_price = room_price

            return f"""📋 **Additional Booking Summary**

🏨 **Room Type:** {room_type}
💰 **Price:** RM{room_price}/night
📅 **Check-in:** {check_in}
📅 **Check-out:** {check_out}
🏷️ **Duration:** {duration} night(s)
💵 **Total Cost:** RM{total_price}
👤 **Guest Name:** {guest_name}

🔗 **Linked to:** {parent_booking.get('booking_id', 'N/A')} ({parent_booking.get('room_name', 'N/A')})

Do you want to confirm this additional booking?

A. Confirm
B. Cancel"""

        except Exception as e:
            logger.error(f"Error showing additional booking summary: {str(e)}")
            return "Sorry, I encountered an error preparing your booking summary. Please try again."

    def handle_additional_booking_confirmation(self, user_input: str, lang: str = 'en') -> str:
        """Handle final confirmation of additional booking."""
        try:
            user_input_lower = user_input.lower().strip()

            # Enhanced confirmation keywords including common misspellings
            confirm_keywords = [
                'confirm', 'yes', 'ok', 'proceed', 'sure', 'agree', 'a',
                # Common misspellings of "confirm"
                'comfirm', 'confrim', 'confrm', 'comfrm', 'confim', 'comfim',
                'confirn', 'comfirn', 'confrirm', 'comfirm', 'conferm', 'comferm',
                # Case variations
                'Confirm', 'Comfirm', 'Confrim', 'CONFIRM', 'COMFIRM',
                # Other positive responses
                'yep', 'yeah', 'yup', 'correct', 'right', 'good', 'go ahead'
            ]

            cancel_keywords = [
                'cancel', 'no', 'abort', 'stop', 'quit', 'exit', 'back', 'b',
                'cancle', 'cansel', 'cancell', 'canel', 'cancal',
                'nope', 'nah', 'never mind', 'nevermind', 'forget it'
            ]

            if user_input_lower in confirm_keywords:
                # Create the additional booking
                success = self.create_additional_booking_record()

                if success:
                    # Reset state
                    self.state = "greeting"
                    self.user_data = {'is_returning_customer': True}

                    parent_booking = self.user_data.get('parent_booking', {})
                    room_type = self.user_data.get('additional_room_type', 'N/A')

                    return f"""🎉 **Additional Booking Successful!** 🎉

✅ Your additional {room_type} has been booked successfully!
🔗 This booking is linked to your existing reservation {parent_booking.get('booking_id', 'N/A')}.

📧 You will receive a confirmation email with both booking details.
💳 Payment can be made at check-in or through the provided QR code.

Is there anything else I can help you with?"""
                else:
                    return "Sorry, I encountered an error while creating your additional booking. Please contact our support team for assistance."

            elif user_input_lower in cancel_keywords:
                # Cancel additional booking
                self.state = "greeting"
                self.user_data = {'is_returning_customer': True}
                return "Additional booking has been cancelled. Your original booking remains unchanged. Is there anything else I can help you with?"

            else:
                return "Please reply 'Confirm' (or A) to proceed with the additional booking or 'Cancel' (or B) to abort."

        except Exception as e:
            logger.error(f"Error handling additional booking confirmation: {str(e)}")
            return "Sorry, I encountered an error. Please reply 'Confirm' to proceed or 'Cancel' to abort."

    def create_additional_booking_record(self) -> bool:
        """Create an additional booking record in the database."""
        try:
            from hotel_booking.models import Room, Booking
            from datetime import datetime
            import dateutil.parser
            import random

            # Get room by type
            room_type = self.user_data.get('additional_room_type', '')
            room = Room.objects.filter(name__icontains=room_type).first()
            if not room:
                logger.error(f"Room type '{room_type}' not found")
                return False

            # Parse dates
            check_in_date = self.user_data.get('additional_check_in_date')
            check_out_date = self.user_data.get('additional_check_out_date')

            if isinstance(check_in_date, str):
                check_in = datetime.strptime(check_in_date, '%Y-%m-%d').date()
            else:
                check_in = check_in_date

            if isinstance(check_out_date, str):
                check_out = datetime.strptime(check_out_date, '%Y-%m-%d').date()
            else:
                check_out = check_out_date

            # Generate booking ID
            booking_id = f"BK-{random.randint(10000, 99999)}"

            # Get parent booking info
            parent_booking = self.user_data.get('parent_booking', {})

            # Get parent booking from database to get email and phone
            parent_booking_obj = None
            if parent_booking.get('id'):
                try:
                    parent_booking_obj = Booking.objects.get(id=parent_booking['id'])
                except Booking.DoesNotExist:
                    logger.warning(f"Parent booking not found: {parent_booking.get('id')}")

            # Get user object if user_id is available
            user_obj = None
            if self.user_data.get('user'):
                user_obj = self.user_data.get('user')
            elif self.user_data.get('user_id'):
                try:
                    from django.contrib.auth.models import User
                    user_obj = User.objects.get(id=self.user_data.get('user_id'))
                except User.DoesNotExist:
                    logger.warning(f"User with ID {self.user_data.get('user_id')} not found")

            # Create additional booking record
            booking = Booking.objects.create(
                room=room,
                guest_name=self.user_data.get('guest_name', parent_booking.get('guest_name', '')),
                guest_email=parent_booking_obj.guest_email if parent_booking_obj else 'guest@example.com',
                guest_phone=parent_booking_obj.guest_phone if parent_booking_obj else '',
                check_in_date=check_in,
                check_out_date=check_out,
                status='confirmed',
                booking_id=booking_id,
                user=user_obj
            )

            # Store the new booking ID for reference
            self.user_data['additional_booking_id'] = booking.booking_id or f"BK-{booking.id}"

            logger.info(f"Additional booking created successfully: ID={booking.id}, Booking_ID={booking.booking_id}")
            logger.info(f"Linked to parent booking: {parent_booking.get('booking_id', 'N/A')}")

            return True

        except Exception as e:
            logger.error(f"Error creating additional booking record: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return False

    def detect_upgrade_intent(self, user_input: str) -> bool:
        """Detect if user wants to upgrade their booking."""
        upgrade_keywords = [
            'upgrade', 'upgrade my room', 'upgrade to', 'upgrade me from',
            'can you change it to', 'better room', 'higher room',
            'change my room to', 'switch my room to', 'upgrade room'
        ]

        user_input_lower = user_input.lower().strip()

        # Only detect upgrade if the user explicitly mentions upgrade-related words
        # Don't trigger on just room type names like "deluxe", "suite", etc.
        return any(keyword in user_input_lower for keyword in upgrade_keywords)

    def handle_upgrade_intent(self, user_input: str, lang: str = 'en') -> str:
        """Handle upgrade request."""
        try:
            # Check if we have a recently viewed booking
            last_booking = self.user_data.get('last_viewed_booking')
            if last_booking and last_booking.get('booking_id'):
                # Use the last viewed booking for upgrade
                booking_id = last_booking['booking_id']
                self.user_data['upgrade_booking_id'] = booking_id
                return self.show_upgrade_options(booking_id, lang)

            # Check if specific room type is mentioned
            import re
            room_type_match = re.search(r'(deluxe|executive|suite|standard)', user_input, re.IGNORECASE)

            if room_type_match:
                target_room = room_type_match.group(1).lower()
                self.user_data['target_room_type'] = target_room

            self.state = "collecting_booking_id_for_upgrade"
            return "I'd be happy to help you upgrade your room! Please provide your booking ID so I can check your current reservation and show you available upgrade options."

        except Exception as e:
            logger.error(f"Error handling upgrade intent: {str(e)}")
            return "Sorry, I encountered an error processing your upgrade request. Please try again."

    def handle_upgrade_booking_id(self, user_input: str, lang: str = 'en') -> str:
        """Handle booking ID input for upgrade."""
        try:
            # Extract booking ID from input
            import re
            booking_id_match = re.search(r'([A-Z0-9-]+)', user_input, re.IGNORECASE)

            if booking_id_match:
                booking_id = booking_id_match.group(1)
                self.user_data['upgrade_booking_id'] = booking_id
                return self.show_upgrade_options(booking_id, lang)
            else:
                return "Please provide a valid booking ID. For example: BK-12345"

        except Exception as e:
            logger.error(f"Error handling upgrade booking ID: {str(e)}")
            return "Sorry, I encountered an error. Please provide your booking ID again."

    def show_upgrade_options(self, booking_id: str, lang: str = 'en') -> str:
        """Show available upgrade options for the booking."""
        try:
            from hotel_booking.models import Booking, Room

            # Find booking by ID
            booking = Booking.objects.filter(booking_id=booking_id).first()

            if not booking:
                self.state = "collecting_booking_id_for_upgrade"
                return f"I couldn't find a booking with ID {booking_id}. Please check your booking ID and try again."

            # Check if booking can be upgraded
            if booking.status == 'cancelled':
                self.state = "greeting"
                return f"This booking ({booking_id}) has been cancelled and cannot be upgraded."

            # Store booking for upgrade
            self.user_data['booking_to_upgrade'] = {
                'id': booking.id,
                'booking_id': booking.booking_id,
                'current_room': booking.room.name,
                'current_price': booking.room.price,
                'check_in': booking.check_in_date.strftime('%B %d'),
                'check_out': booking.check_out_date.strftime('%B %d'),
                'duration': (booking.check_out_date - booking.check_in_date).days
            }

            # Get available room types for upgrade (higher price than current)
            current_price = booking.room.price
            upgrade_rooms = Room.objects.filter(price__gt=current_price).order_by('price')

            if not upgrade_rooms.exists():
                self.state = "greeting"
                return f"You are currently booking a {booking.room.name} for stays from {booking.check_in_date.strftime('%B %d')} to {booking.check_out_date.strftime('%B %d')}. Unfortunately, there are no higher-tier rooms available for upgrade."

            # Build upgrade options message
            duration = (booking.check_out_date - booking.check_in_date).days
            options_text = f"You are currently booking a {booking.room.name} for stays from {booking.check_in_date.strftime('%B %d')} to {booking.check_out_date.strftime('%B %d')}. Which room type would you like to upgrade to?\n\nCurrent upgradeable room types:\n"

            for room in upgrade_rooms:
                price_diff = room.price - current_price
                total_additional = price_diff * duration
                options_text += f"• {room.name} (add RM{price_diff}/night, total additional: RM{total_additional})\n"

            options_text += "\nWhich one would you like to choose? Please type the room name (e.g., 'Deluxe Room')."

            self.state = "selecting_upgrade_room"
            return options_text

        except Exception as e:
            logger.error(f"Error showing upgrade options: {str(e)}")
            return "Sorry, I encountered an error checking upgrade options. Please try again."

    def handle_upgrade_selection(self, user_input: str, lang: str = 'en') -> str:
        """Handle room upgrade selection."""
        try:
            from hotel_booking.models import Booking, Room

            booking_data = self.user_data.get('booking_to_upgrade')
            if not booking_data:
                return "Sorry, I lost track of your booking information. Please start the upgrade process again."

            # Find the selected room type
            user_input_lower = user_input.lower().strip()

            # Try to match room name with improved logic
            selected_room = None
            rooms = Room.objects.filter(price__gt=booking_data['current_price'])

            # First try exact match
            for room in rooms:
                if room.name.lower() == user_input_lower:
                    selected_room = room
                    break

            # If no exact match, try partial matching
            if not selected_room:
                for room in rooms:
                    room_words = room.name.lower().split()
                    input_words = user_input_lower.split()

                    # Check if any significant word from room name is in user input
                    if any(word in user_input_lower for word in room_words if len(word) > 2):
                        selected_room = room
                        break

                    # Check if any word from user input matches room name words
                    if any(word in room.name.lower() for word in input_words if len(word) > 2):
                        selected_room = room
                        break

            if not selected_room:
                # Show available options
                available_rooms = [room.name for room in rooms]
                if available_rooms:
                    return f"I couldn't find that room type. Available upgrade options are: {', '.join(available_rooms)}. Please choose one of these options."
                else:
                    return "Sorry, no upgrade options are available for your current booking."

            # Process the upgrade
            booking = Booking.objects.get(id=booking_data['id'])
            old_room = booking.room.name
            old_price = booking.room.price

            # Update booking with new room
            booking.room = selected_room
            booking.save()

            # Calculate price difference
            price_diff = selected_room.price - old_price
            total_additional = price_diff * booking_data['duration']

            # Reset state
            self.state = "greeting"
            self.user_data = {'is_returning_customer': True}

            return f"Your room type has been successfully upgraded to {selected_room.name} and the total price has been adjusted. Additional cost: RM{total_additional} (RM{price_diff}/night × {booking_data['duration']} nights). We look forward to your more comfortable stay!"

        except Exception as e:
            logger.error(f"Error processing upgrade selection: {str(e)}")
            return "Sorry, I encountered an error while processing your upgrade. Please contact our support team for assistance."

    def detect_extend_intent(self, user_input: str) -> bool:
        """Detect if user wants to extend their stay."""
        extend_keywords = [
            'extend', 'extend my stay', 'stay longer', 'one more day', 'extra day',
            'late check-out', 'extend to', 'stay until', 'prolong', 'additional night'
        ]

        user_input_lower = user_input.lower().strip()
        return any(keyword in user_input_lower for keyword in extend_keywords)

    def detect_change_date_intent(self, user_input: str) -> bool:
        """Detect if user wants to change their booking dates."""
        change_date_keywords = [
            'change date', 'reschedule', 'different day', 'new check-in',
            'modify booking', 'modify my booking', 'change booking', 'update booking',
            'reschedule booking', 'change my booking', 'change check-in', 'change my check-in',
            'postpone', 'postpone my booking', 'change check-in date', 'modify check-in',
            'update check-in', 'change dates', 'want change date', 'want to change date',
            'change date to check in', 'change my check in date', 'modify date',
            'alter date', 'switch date', 'move date', 'adjust date', 'update date',
            'change the date', 'modify the date', 'reschedule the date'
        ]
        user_input_lower = user_input.lower().strip()
        return any(keyword in user_input_lower for keyword in change_date_keywords)

    def handle_change_date_intent(self, user_input: str, lang: str = 'en') -> str:
        """Handle change date request following the improved conversation flow."""
        try:
            # Check if we have a recently viewed booking
            last_booking = self.user_data.get('last_viewed_booking')
            if last_booking and last_booking.get('booking_id'):
                # Use the last viewed booking for date change
                booking_id = last_booking['booking_id']
                self.user_data['change_date_booking_id'] = booking_id
                return self.show_current_booking_dates(booking_id, lang)

            self.state = "collecting_booking_id_for_change_date"
            return "I'd be happy to help you change your check-in date! Please provide your booking ID so that I can help you change the date."

        except Exception as e:
            logger.error(f"Error handling change date intent: {str(e)}")
            return "Sorry, I encountered an error processing your date change request. Please try again."

    def handle_change_date_booking_id(self, user_input: str, lang: str = 'en') -> str:
        """Handle booking ID input for date change."""
        try:
            # Extract booking ID from input
            import re
            booking_id_match = re.search(r'([A-Z0-9-]+)', user_input, re.IGNORECASE)

            if booking_id_match:
                booking_id = booking_id_match.group(1)
                self.user_data['change_date_booking_id'] = booking_id
                return self.show_current_booking_dates(booking_id, lang)
            else:
                return "Please provide a valid booking ID. For example: BK-12345"

        except Exception as e:
            logger.error(f"Error handling change date booking ID: {str(e)}")
            return "Sorry, I encountered an error. Please provide your booking ID again."

    def show_current_booking_dates(self, booking_id: str, lang: str = 'en') -> str:
        """Show current booking dates and ask for new check-in date."""
        try:
            from hotel_booking.models import Booking
            from datetime import datetime, timedelta

            # Find booking by ID
            booking = Booking.objects.filter(booking_id=booking_id).first()

            if not booking:
                self.state = "collecting_booking_id_for_change_date"
                return f"I couldn't find a booking with ID {booking_id}. Please check your booking ID and try again."

            # Check if booking can be modified
            if booking.status == 'cancelled':
                self.state = "greeting"
                return f"This booking ({booking_id}) has been cancelled and cannot be modified."

            # Check 3-day advance rule
            from datetime import date
            today = date.today()
            days_until_checkin = (booking.check_in_date - today).days

            if days_until_checkin < 3:
                self.state = "greeting"
                return f"Sorry, check-in date changes must be made at least 3 days in advance. Your current check-in date is {booking.check_in_date.strftime('%B %d, %Y')}, which is only {days_until_checkin} day(s) away."

            # Store booking for date change
            self.user_data['booking_to_change'] = {
                'id': booking.id,
                'booking_id': booking.booking_id,
                'guest_name': booking.guest_name,
                'room_name': booking.room.name,
                'current_checkin': booking.check_in_date.strftime('%B %d, %Y'),
                'current_checkout': booking.check_out_date.strftime('%B %d, %Y'),
                'current_checkin_date': booking.check_in_date.strftime('%Y-%m-%d'),
                'current_checkout_date': booking.check_out_date.strftime('%Y-%m-%d')
            }

            self.state = "collecting_new_check_in_date"
            return f"Your current check-in date is {booking.check_in_date.strftime('%B %d, %Y')}. Which day do you want to change it to? Please provide the new check-in date (e.g., 'June 15' or '15/06/2025')."

        except Exception as e:
            logger.error(f"Error showing current booking dates: {str(e)}")
            return "Sorry, I encountered an error checking your booking details. Please try again."

    def handle_new_check_in_date(self, user_input: str, lang: str = 'en') -> str:
        """Handle new check-in date input."""
        try:
            from datetime import datetime, timedelta
            import re

            # Check if user is trying to restart the change date process
            change_date_keywords = [
                'change date', 'want change', 'want to change', 'i want change date',
                'change my date', 'modify date', 'reschedule', 'postpone'
            ]

            if any(keyword in user_input.lower() for keyword in change_date_keywords):
                # User wants to restart the change date process
                return self.handle_change_date_intent(user_input, lang)

            booking_data = self.user_data.get('booking_to_change')
            if not booking_data:
                return "Sorry, I lost track of your booking information. Please start the date change process again."

            # Parse the new check-in date
            new_checkin_date = None

            # Try different date formats
            date_patterns = [
                r'(\d{1,2})[/\-](\d{1,2})[/\-](\d{4})',  # DD/MM/YYYY
                r'(\d{1,2})[/\-](\d{1,2})',  # DD/MM (current year)
                r'(january|february|march|april|may|june|july|august|september|october|november|december)\s+(\d{1,2})',  # Month DD
            ]

            for pattern in date_patterns:
                match = re.search(pattern, user_input, re.IGNORECASE)
                if match:
                    try:
                        if len(match.groups()) == 3:  # DD/MM/YYYY
                            day, month, year = match.groups()
                            new_checkin_date = datetime(int(year), int(month), int(day)).date()
                        elif len(match.groups()) == 2 and match.group(1).isdigit():  # DD/MM
                            day, month = match.groups()
                            new_checkin_date = datetime(datetime.now().year, int(month), int(day)).date()
                        elif len(match.groups()) == 2:  # Month DD
                            month_name, day = match.groups()
                            month_num = {
                                'january': 1, 'february': 2, 'march': 3, 'april': 4,
                                'may': 5, 'june': 6, 'july': 7, 'august': 8,
                                'september': 9, 'october': 10, 'november': 11, 'december': 12
                            }.get(month_name.lower())
                            if month_num:
                                new_checkin_date = datetime(datetime.now().year, month_num, int(day)).date()
                        break
                    except ValueError:
                        continue

            if not new_checkin_date:
                return "I couldn't understand the date format. Please provide the date in format like 'June 15', '15/06/2025', or '15/06'."

            # Validate the new date
            from datetime import date
            today = date.today()
            if new_checkin_date <= today:
                return "The new check-in date must be in the future. Please choose a date after today."

            # Check 3-day advance rule for new date
            days_until_new_checkin = (new_checkin_date - today).days
            if days_until_new_checkin < 3:
                return f"Sorry, the new check-in date must be at least 3 days from today. Please choose a date that is at least 3 days away."

            # Calculate new check-out date (maintain same duration)
            current_checkin = datetime.strptime(booking_data['current_checkin_date'], '%Y-%m-%d').date()
            current_checkout = datetime.strptime(booking_data['current_checkout_date'], '%Y-%m-%d').date()
            duration = (current_checkout - current_checkin).days
            new_checkout_date = new_checkin_date + timedelta(days=duration)

            # Store the new dates
            self.user_data['new_checkin_date'] = new_checkin_date.strftime('%Y-%m-%d')
            self.user_data['new_checkout_date'] = new_checkout_date.strftime('%Y-%m-%d')

            self.state = "confirming_date_change"
            return f"Are you sure to change the check-in time to {new_checkin_date.strftime('%B %d, %Y')}? Your new check-out date will be {new_checkout_date.strftime('%B %d, %Y')}. Please type 'Confirm' to proceed or 'Cancel' to abort."

        except Exception as e:
            logger.error(f"Error handling new check-in date: {str(e)}")
            return "Sorry, I encountered an error processing the new date. Please try again."

    def handle_date_change_confirmation(self, user_input: str, lang: str = 'en') -> str:
        """Handle date change confirmation with enhanced duplicate protection."""
        try:
            from hotel_booking.models import Booking
            from datetime import datetime
            import dateutil.parser

            user_input_lower = user_input.lower().strip()

            # Enhanced confirmation keywords including common misspellings
            confirm_keywords = [
                'confirm', 'yes', 'ok', 'proceed', 'sure', 'agree',
                # Common misspellings of "confirm"
                'comfirm', 'confrim', 'confrm', 'comfrm', 'confim', 'comfim',
                'confirn', 'comfirn', 'confrirm', 'comfirm', 'conferm', 'comferm',
                # Case variations
                'Confirm', 'Comfirm', 'Confrim', 'CONFIRM', 'COMFIRM',
                # Other positive responses
                'yep', 'yeah', 'yup', 'correct', 'right', 'good', 'go ahead'
            ]

            if user_input_lower in confirm_keywords:
                # First check if we're already processing a confirmation
                if self.user_data.get('processing_date_change', False):
                    return "Your date change is already being processed. Please wait a moment..."

                # Mark as processing to prevent duplicate requests
                self.user_data['processing_date_change'] = True

                booking_data = self.user_data.get('booking_to_change')
                new_checkin_str = self.user_data.get('new_checkin_date')
                new_checkout_str = self.user_data.get('new_checkout_date')

                if not booking_data or not new_checkin_str or not new_checkout_str:
                    self.user_data['processing_date_change'] = False
                    return "Sorry, I lost track of your booking information. Please start the date change process again."

                # Check if this specific booking change has already been processed
                change_key = f"date_change_{booking_data['id']}_{new_checkin_str}"
                if self.user_data.get(change_key, False):
                    # Already processed this specific change
                    self.state = "greeting"
                    self.user_data = {'is_returning_customer': True}
                    return "Your date change has already been processed. Is there anything else I can help you with?"

                try:
                    # Mark this specific change as processed BEFORE making database changes
                    self.user_data[change_key] = True

                    # Update the booking
                    booking = Booking.objects.get(id=booking_data['id'])
                    new_checkin_date = dateutil.parser.parse(new_checkin_str).date()
                    new_checkout_date = dateutil.parser.parse(new_checkout_str).date()

                    booking.check_in_date = new_checkin_date
                    booking.check_out_date = new_checkout_date
                    booking.save()

                    # Reset state and clear processing flag
                    self.state = "greeting"
                    self.user_data = {
                        'is_returning_customer': True,
                        change_key: True,  # Keep the specific change tracking
                        'processing_date_change': False
                    }

                    return f"OK, your check-in date has been successfully changed to {new_checkin_date.strftime('%B %d, %Y')}. The booking ID remains unchanged. If you have any other needs, please continue to consult!"

                except Exception as db_error:
                    # Clear processing flag on error
                    self.user_data['processing_date_change'] = False
                    logger.error(f"Database error during date change: {str(db_error)}")
                    return "Sorry, I encountered an error while updating your booking. Please try again or contact our support team."

            # Enhanced cancellation keywords including common misspellings
            cancel_keywords = [
                'cancel', 'no', 'abort', 'stop', 'quit', 'exit', 'back',
                # Common misspellings of "cancel"
                'cancle', 'cansel', 'cancell', 'canel', 'cancal', 'cancle',
                # Case variations
                'Cancel', 'Cancle', 'Cansel', 'CANCEL', 'CANCLE',
                # Other negative responses
                'nope', 'nah', 'never mind', 'nevermind', 'forget it'
            ]

            if user_input_lower in cancel_keywords:
                # Reset state and clear any processing flags
                self.state = "greeting"
                self.user_data = {'is_returning_customer': True}
                return "Date change has been cancelled. Your original booking dates remain unchanged. Is there anything else I can help you with?"

            else:
                # Don't repeat the confirmation message if we're already in confirming state
                if self.state == "confirming_date_change":
                    return "Please type 'Confirm' to proceed with the date change or 'Cancel' to abort."
                else:
                    return "Please type 'Confirm' to proceed with the date change or 'Cancel' to abort."

        except Exception as e:
            # Clear processing flag on any error
            self.user_data['processing_date_change'] = False
            logger.error(f"Error handling date change confirmation: {str(e)}")
            return "Sorry, I encountered an error while processing your date change. Please contact our support team for assistance."

    def handle_extend_intent(self, user_input: str, lang: str = 'en') -> str:
        """Handle extend stay request."""
        try:
            # Check if specific date is mentioned
            import re
            from datetime import datetime

            # Look for date patterns
            date_match = re.search(r'(\d{1,2})[/\-](\d{1,2})[/\-](\d{4})', user_input)
            day_match = re.search(r'(monday|tuesday|wednesday|thursday|friday|saturday|sunday)', user_input, re.IGNORECASE)

            if date_match:
                day, month, year = date_match.groups()
                try:
                    extend_date = datetime(int(year), int(month), int(day)).date()
                    self.user_data['target_extend_date'] = extend_date.strftime('%Y-%m-%d')
                except ValueError:
                    pass
            elif day_match:
                self.user_data['target_day'] = day_match.group(1).lower()

            self.state = "collecting_booking_id_for_extend"
            return "I'd be happy to help you extend your stay! Please provide your booking ID so I can check your current reservation and available dates."

        except Exception as e:
            logger.error(f"Error handling extend intent: {str(e)}")
            return "Sorry, I encountered an error processing your extension request. Please try again."

    def handle_extend_booking_id(self, user_input: str, lang: str = 'en') -> str:
        """Handle booking ID input for extension."""
        try:
            # Extract booking ID from input
            import re
            booking_id_match = re.search(r'([A-Z0-9-]+)', user_input, re.IGNORECASE)

            if booking_id_match:
                booking_id = booking_id_match.group(1)
                self.user_data['extend_booking_id'] = booking_id
                return self.show_extend_options(booking_id, lang)
            else:
                return "Please provide a valid booking ID. For example: BK-12345"

        except Exception as e:
            logger.error(f"Error handling extend booking ID: {str(e)}")
            return "Sorry, I encountered an error. Please provide your booking ID again."

    def show_extend_options(self, booking_id: str, lang: str = 'en') -> str:
        """Show extension options for the booking."""
        try:
            from hotel_booking.models import Booking
            from datetime import datetime, timedelta

            # Find booking by ID
            booking = Booking.objects.filter(booking_id=booking_id).first()

            if not booking:
                self.state = "collecting_booking_id_for_extend"
                return f"I couldn't find a booking with ID {booking_id}. Please check your booking ID and try again."

            # Check if booking can be extended
            if booking.status == 'cancelled':
                self.state = "greeting"
                return f"This booking ({booking_id}) has been cancelled and cannot be extended."

            # Store booking for extension
            self.user_data['booking_to_extend'] = {
                'id': booking.id,
                'booking_id': booking.booking_id,
                'room_name': booking.room.name,
                'room_price': booking.room.price,
                'current_checkout': booking.check_out_date.strftime('%B %d (%A)'),
                'current_checkout_date': booking.check_out_date.strftime('%Y-%m-%d')
            }

            self.state = "selecting_extend_date"
            return f"Your current booking is until {booking.check_out_date.strftime('%B %d (%A)')}. Which day do you want to extend it to? Please provide the new check-out date (e.g., 'June 15' or '15/06/2025')."

        except Exception as e:
            logger.error(f"Error showing extend options: {str(e)}")
            return "Sorry, I encountered an error checking extension options. Please try again."

    def handle_extend_date_selection(self, user_input: str, lang: str = 'en') -> str:
        """Handle extension date selection."""
        try:
            from hotel_booking.models import Booking
            from datetime import datetime, timedelta
            import re

            booking_data = self.user_data.get('booking_to_extend')
            if not booking_data:
                return "Sorry, I lost track of your booking information. Please start the extension process again."

            # Parse the new checkout date
            current_checkout = datetime.strptime(booking_data['current_checkout_date'], '%Y-%m-%d').date()
            new_checkout_date = None

            # Try different date formats
            date_patterns = [
                r'(\d{1,2})[/\-](\d{1,2})[/\-](\d{4})',  # DD/MM/YYYY
                r'(\d{1,2})[/\-](\d{1,2})',  # DD/MM (current year)
                r'(january|february|march|april|may|june|july|august|september|october|november|december)\s+(\d{1,2})',  # Month DD
            ]

            for pattern in date_patterns:
                match = re.search(pattern, user_input, re.IGNORECASE)
                if match:
                    try:
                        if len(match.groups()) == 3:  # DD/MM/YYYY
                            day, month, year = match.groups()
                            new_checkout_date = datetime(int(year), int(month), int(day)).date()
                        elif len(match.groups()) == 2 and match.group(1).isdigit():  # DD/MM
                            day, month = match.groups()
                            new_checkout_date = datetime(datetime.now().year, int(month), int(day)).date()
                        elif len(match.groups()) == 2:  # Month DD
                            month_name, day = match.groups()
                            month_num = {
                                'january': 1, 'february': 2, 'march': 3, 'april': 4,
                                'may': 5, 'june': 6, 'july': 7, 'august': 8,
                                'september': 9, 'october': 10, 'november': 11, 'december': 12
                            }.get(month_name.lower())
                            if month_num:
                                new_checkout_date = datetime(datetime.now().year, month_num, int(day)).date()
                        break
                    except ValueError:
                        continue

            if not new_checkout_date:
                return "I couldn't understand the date format. Please provide the date in format like 'June 15', '15/06/2025', or '15/06'."

            # Validate the new date
            if new_checkout_date <= current_checkout:
                return f"The new checkout date must be after your current checkout date ({booking_data['current_checkout']}). Please choose a later date."

            # Calculate additional nights and cost
            additional_nights = (new_checkout_date - current_checkout).days
            additional_cost = additional_nights * booking_data['room_price']

            # Check room availability (simplified - in real implementation, check for conflicts)
            # For now, we'll assume the room is available

            # Update the booking
            booking = Booking.objects.get(id=booking_data['id'])
            booking.check_out_date = new_checkout_date
            booking.save()

            # Reset state
            self.state = "greeting"
            self.user_data = {'is_returning_customer': True}

            return f"Good news! We have extended your stay to {new_checkout_date.strftime('%B %d')}, with an additional fee of RM{additional_cost} ({additional_nights} night{'s' if additional_nights > 1 else ''} × RM{booking_data['room_price']}/night). Looking forward to your continued stay!"

        except Exception as e:
            logger.error(f"Error processing extend date selection: {str(e)}")
            return "Sorry, I encountered an error while processing your extension. Please contact our support team for assistance."

    def detect_status_inquiry(self, user_input: str) -> bool:
        """Detect if user wants to check booking status."""
        status_keywords = [
            'did i make a reservation', 'do i have a booking', 'check my booking',
            'my booking', 'booking status', 'reservation status', 'confirm my booking',
            'what room did i book', 'what did i book', 'my bookingid is', 'booking id',
            'did i book a room last time', 'did i make a successful reservation',
            'please confirm', 'can you help me check my order', 'i forgot what room i booked',
            'check my order', 'my order', 'order status', 'reservation confirmation',
            'booking confirmation', 'check reservation', 'verify my booking',
            'booking status check', 'status check', 'check status', 'check booking status'
        ]

        user_input_lower = user_input.lower().strip()
        return any(keyword in user_input_lower for keyword in status_keywords)

    def handle_status_inquiry(self, user_input: str, lang: str = 'en') -> str:
        """Handle booking status inquiry with enhanced name and ID detection."""
        try:
            import re

            # Check if booking ID is mentioned in the input
            booking_id_match = re.search(r'(?:booking\s*id|bookingid|order\s*number|reservation\s*number)\s*(?:is|:)?\s*([A-Z0-9-]+)', user_input, re.IGNORECASE)

            # If not found with keywords, try to find any alphanumeric pattern that looks like a booking ID
            if not booking_id_match:
                booking_id_match = re.search(r'\b([A-Z]{2,}-[A-Z0-9-]+)\b', user_input, re.IGNORECASE)

            if booking_id_match:
                booking_id = booking_id_match.group(1)
                return self.show_booking_status(booking_id, lang)

            # Check if user provided a name for lookup
            # But first exclude common action phrases that might be mistaken for names
            cancel_phrases = ['cancel my', 'cancel booking', 'cancel order', 'cancel reservation']
            if not any(phrase in user_input.lower() for phrase in cancel_phrases):
                name_patterns = [
                    r'(?:i am|my name is|name is|i\'m)\s+([A-Za-z\s]+)',
                    r'(?:under|for)\s+([A-Za-z\s]+)',
                    r'([A-Za-z]+\s+[A-Za-z]+)'  # Simple first name + last name pattern
                ]

                for pattern in name_patterns:
                    name_match = re.search(pattern, user_input, re.IGNORECASE)
                    if name_match:
                        name = name_match.group(1).strip()
                        # Only proceed if name looks reasonable (2+ words or common names)
                        # And exclude common action words
                        action_words = ['cancel', 'change', 'upgrade', 'extend', 'book', 'booking']
                        if (len(name.split()) >= 2 or len(name) >= 3) and not any(word in name.lower() for word in action_words):
                            return self.search_booking_by_name(name, lang)

            # No booking ID or name found, ask for more information
            self.state = "collecting_booking_info_for_status"
            return "I'd be happy to check your booking status! Do you remember the name, phone number, or booking ID used for the reservation? This will help me find your booking quickly."

        except Exception as e:
            logger.error(f"Error handling status inquiry: {str(e)}")
            return "Sorry, I encountered an error checking your booking status. Please try again."

    def search_booking_by_name(self, name: str, lang: str = 'en') -> str:
        """Search for bookings by guest name with fuzzy matching."""
        try:
            from hotel_booking.models import Booking
            from django.db.models import Q

            # Try exact match first
            bookings = Booking.objects.filter(guest_name__iexact=name).order_by('-created_at')

            # If no exact match, try partial matches
            if not bookings.exists():
                name_parts = name.split()
                query = Q()
                for part in name_parts:
                    if len(part) >= 2:  # Only search for meaningful parts
                        query |= Q(guest_name__icontains=part)
                bookings = Booking.objects.filter(query).order_by('-created_at')

            if not bookings.exists():
                self.state = "collecting_booking_info_for_status"
                return f"Sorry, I couldn't find any booking records for \"{name}\". Please confirm the name spelling or try providing your booking ID instead."

            if bookings.count() == 1:
                # Single booking found
                booking = bookings.first()
                return self.format_booking_status_response(booking, lang)
            else:
                # Multiple bookings found
                self.user_data['found_bookings'] = [
                    {
                        'id': booking.id,
                        'booking_id': booking.booking_id,
                        'guest_name': booking.guest_name,
                        'room_name': booking.room.name,
                        'check_in': booking.check_in_date.strftime('%B %d, %Y'),
                        'status': booking.status
                    }
                    for booking in bookings[:5]  # Limit to 5 most recent
                ]
                self.state = "selecting_booking_from_multiple"

                booking_list = "\n".join([
                    f"{i+1}. {b['guest_name']} - {b['room_name']} - Check-in: {b['check_in']} - Status: {b['status'].title()}"
                    for i, b in enumerate(self.user_data['found_bookings'])
                ])

                return f"I found multiple bookings for \"{name}\":\n\n{booking_list}\n\nPlease reply with the number (1-{len(self.user_data['found_bookings'])}) of the booking you'd like to check, or provide your booking ID for a more specific search."

        except Exception as e:
            logger.error(f"Error searching booking by name: {str(e)}")
            return "Sorry, I encountered an error while searching for your booking. Please try again."

    def format_booking_status_response(self, booking, lang: str = 'en') -> str:
        """Format a comprehensive booking status response."""
        try:
            from datetime import date

            # Get booking details
            booking_id = booking.booking_id or f"BK-{booking.id}"
            guest_name = booking.guest_name
            room_name = booking.room.name
            check_in = booking.check_in_date.strftime('%B %d, %Y')
            check_out = booking.check_out_date.strftime('%B %d, %Y')
            status = booking.status.title()

            # Check if booking is in the past, current, or future
            today = date.today()
            if booking.check_out_date < today:
                time_status = "completed"
            elif booking.check_in_date <= today <= booking.check_out_date:
                time_status = "current"
            else:
                time_status = "upcoming"

            # Format response based on status and timing
            if booking.status == 'cancelled':
                response = f"📋 **Booking Status: CANCELLED**\n\n"
                response += f"🆔 **Booking ID:** {booking_id}\n"
                response += f"👤 **Guest Name:** {guest_name}\n"
                response += f"🏨 **Room Type:** {room_name}\n"
                response += f"📅 **Original Check-in:** {check_in}\n"
                response += f"📅 **Original Check-out:** {check_out}\n\n"
                response += f"❌ This booking has been cancelled. If you need to make a new reservation, I'd be happy to help!"

            elif time_status == "completed":
                response = f"📋 **Booking Status: COMPLETED**\n\n"
                response += f"🆔 **Booking ID:** {booking_id}\n"
                response += f"👤 **Guest Name:** {guest_name}\n"
                response += f"🏨 **Room Type:** {room_name}\n"
                response += f"📅 **Check-in:** {check_in}\n"
                response += f"📅 **Check-out:** {check_out}\n\n"
                response += f"✅ Your stay has been completed on {check_out}. Thank you for choosing our hotel! We hope you had a wonderful experience."

            elif time_status == "current":
                response = f"📋 **Booking Status: ACTIVE (Currently Staying)**\n\n"
                response += f"🆔 **Booking ID:** {booking_id}\n"
                response += f"👤 **Guest Name:** {guest_name}\n"
                response += f"🏨 **Room Type:** {room_name}\n"
                response += f"📅 **Check-in:** {check_in}\n"
                response += f"📅 **Check-out:** {check_out}\n\n"
                response += f"🏠 Welcome! You're currently staying with us. If you need any assistance during your stay, please let me know!"

            else:  # upcoming
                response = f"📋 **Booking Status: CONFIRMED**\n\n"
                response += f"🆔 **Booking ID:** {booking_id}\n"
                response += f"👤 **Guest Name:** {guest_name}\n"
                response += f"🏨 **Room Type:** {room_name}\n"
                response += f"📅 **Check-in:** {check_in}\n"
                response += f"📅 **Check-out:** {check_out}\n\n"
                response += f"✅ Your booking is confirmed! We look forward to welcoming you on {check_in}."

            # Add options for modifications
            if booking.status != 'cancelled' and time_status != "completed":
                response += f"\n\nIf you need to cancel, change dates, or upgrade your room, please let me know!"

            # Reset state but keep booking info for potential follow-up actions
            self.state = "greeting"
            self.user_data = {
                'is_returning_customer': True,
                'last_viewed_booking': {
                    'id': booking.id,
                    'booking_id': booking_id,
                    'guest_name': guest_name,
                    'room_name': room_name,
                    'check_in_date': booking.check_in_date,
                    'check_out_date': booking.check_out_date,
                    'status': booking.status
                }
            }

            return response

        except Exception as e:
            logger.error(f"Error formatting booking status response: {str(e)}")
            return "I found your booking but encountered an error displaying the details. Please try again."

    def handle_multiple_booking_selection(self, user_input: str, lang: str = 'en') -> str:
        """Handle selection from multiple found bookings."""
        try:
            import re

            # Extract number from input
            number_match = re.search(r'(\d+)', user_input.strip())
            if number_match:
                selection = int(number_match.group(1))
                found_bookings = self.user_data.get('found_bookings', [])

                if 1 <= selection <= len(found_bookings):
                    selected_booking_data = found_bookings[selection - 1]
                    # Get the full booking object
                    from hotel_booking.models import Booking
                    booking = Booking.objects.get(id=selected_booking_data['id'])
                    return self.format_booking_status_response(booking, lang)
                else:
                    return f"Please select a number between 1 and {len(found_bookings)}."
            else:
                return "Please reply with the number of the booking you'd like to check (e.g., '1', '2', etc.)."

        except Exception as e:
            logger.error(f"Error handling multiple booking selection: {str(e)}")
            return "Sorry, I encountered an error. Please try again."

    def handle_booking_info_collection_for_status(self, user_input: str, lang: str = 'en') -> str:
        """Handle collection of booking information for status check."""
        try:
            import re

            # Check if user provided booking ID
            booking_id_match = re.search(r'\b([A-Z]{2,}-[A-Z0-9-]+)\b', user_input, re.IGNORECASE)
            if booking_id_match:
                booking_id = booking_id_match.group(1)
                return self.show_booking_status(booking_id, lang)

            # Check if user provided a name
            # But first exclude common action phrases that might be mistaken for names
            cancel_phrases = ['cancel my', 'cancel booking', 'cancel order', 'cancel reservation']
            if not any(phrase in user_input.lower() for phrase in cancel_phrases):
                name_patterns = [
                    r'(?:i am|my name is|name is|i\'m)\s+([A-Za-z\s]+)',
                    r'(?:under|for)\s+([A-Za-z\s]+)',
                    r'([A-Za-z]+\s+[A-Za-z]+)'  # Simple first name + last name pattern
                ]

                for pattern in name_patterns:
                    name_match = re.search(pattern, user_input, re.IGNORECASE)
                    if name_match:
                        name = name_match.group(1).strip()
                        # Only proceed if name looks reasonable and exclude action words
                        action_words = ['cancel', 'change', 'upgrade', 'extend', 'book', 'booking']
                        if (len(name.split()) >= 2 or len(name) >= 3) and not any(word in name.lower() for word in action_words):
                            return self.search_booking_by_name(name, lang)

            # Check if user provided phone number
            phone_match = re.search(r'(\d{10,15})', user_input)
            if phone_match:
                phone = phone_match.group(1)
                return self.search_booking_by_phone(phone, lang)

            return "Please provide your booking ID, full name, or phone number so I can locate your reservation."

        except Exception as e:
            logger.error(f"Error handling booking info collection: {str(e)}")
            return "Sorry, I encountered an error. Please provide your booking ID or name."

    def search_booking_by_phone(self, phone: str, lang: str = 'en') -> str:
        """Search for bookings by phone number."""
        try:
            from hotel_booking.models import Booking

            # Try exact match and partial matches
            bookings = Booking.objects.filter(
                guest_phone__icontains=phone
            ).order_by('-created_at')

            if not bookings.exists():
                return f"Sorry, I couldn't find any booking records with phone number ending in {phone[-4:]}. Please try providing your booking ID or full name instead."

            if bookings.count() == 1:
                booking = bookings.first()
                return self.format_booking_status_response(booking, lang)
            else:
                # Multiple bookings found - use the same multiple selection logic
                self.user_data['found_bookings'] = [
                    {
                        'id': booking.id,
                        'booking_id': booking.booking_id,
                        'guest_name': booking.guest_name,
                        'room_name': booking.room.name,
                        'check_in': booking.check_in_date.strftime('%B %d, %Y'),
                        'status': booking.status
                    }
                    for booking in bookings[:5]
                ]
                self.state = "selecting_booking_from_multiple"

                booking_list = "\n".join([
                    f"{i+1}. {b['guest_name']} - {b['room_name']} - Check-in: {b['check_in']} - Status: {b['status'].title()}"
                    for i, b in enumerate(self.user_data['found_bookings'])
                ])

                return f"I found multiple bookings with that phone number:\n\n{booking_list}\n\nPlease reply with the number (1-{len(self.user_data['found_bookings'])}) of the booking you'd like to check."

        except Exception as e:
            logger.error(f"Error searching booking by phone: {str(e)}")
            return "Sorry, I encountered an error while searching for your booking. Please try again."

    def handle_status_booking_id(self, user_input: str, lang: str = 'en') -> str:
        """Handle booking ID input for status check."""
        try:
            # Extract booking ID from input
            import re
            booking_id_match = re.search(r'([A-Z0-9-]+)', user_input, re.IGNORECASE)

            if booking_id_match:
                booking_id = booking_id_match.group(1)
                return self.show_booking_status(booking_id, lang)
            else:
                return "Please provide a valid booking ID. For example: BK-12345"

        except Exception as e:
            logger.error(f"Error handling status booking ID: {str(e)}")
            return "Sorry, I encountered an error. Please provide your booking ID again."

    def show_booking_status(self, booking_id: str, lang: str = 'en') -> str:
        """Show detailed booking status using the enhanced formatter."""
        try:
            from hotel_booking.models import Booking

            # Find booking by ID
            booking = Booking.objects.filter(booking_id=booking_id).first()

            if not booking:
                self.state = "collecting_booking_info_for_status"
                return f"Sorry, I couldn't find a booking with ID {booking_id}. Please confirm the booking ID is correct, or provide your name for further inquiry."

            # Use the enhanced formatting function with addon information
            response = self.format_booking_status_response(booking, lang)

            # Add addon services information if available
            addons = booking.addons.all()
            if addons.exists():
                addon_text = "\n\n🎁 **Add-on Services:**\n"
                for addon in addons:
                    if addon.addon_type == 'breakfast':
                        addon_text += f"• Breakfast service for {addon.breakfast_count} guests (RM{addon.get_total_price()})\n"
                    elif addon.addon_type == 'transport':
                        direction = "to hotel" if addon.transport_direction == 'to_hotel' else "from hotel"
                        addon_text += f"• Airport transfer ({direction}) on {addon.transport_date} at {addon.transport_time} for {addon.passenger_count} passengers (RM{addon.price})\n"

                # Calculate total cost including addons
                base_cost = booking.get_total_price()
                addon_cost = sum(addon.get_total_price() for addon in addons)
                total_cost = base_cost + addon_cost
                addon_text += f"\n💰 **Total Cost (including add-ons): RM{total_cost:.2f}**"

                # Insert addon information before the final message
                response = response.replace("If you need to cancel", addon_text + "\n\nIf you need to cancel")

            return response

        except Exception as e:
            logger.error(f"Error showing booking status: {str(e)}")
            return "Sorry, I encountered an error checking your booking details. Please try again."

    def detect_hotel_info_question(self, user_input: str) -> bool:
        """Detect if user is asking common hotel information questions."""
        info_keywords = [
            # Check-in related
            'check-in time', 'check in time', 'checkin time', 'what time check in',
            'what time can i check in', 'what time can you check in', 'check in',

            # Check-out related
            'check-out time', 'check out time', 'checkout time', 'what time check out',
            'what time is check-out', 'check out',

            # Breakfast related (only for time/info queries, not booking)
            'breakfast time', 'when is breakfast', 'breakfast hours',
            'what time can i have breakfast', 'what time is breakfast provided',
            'what time is breakfast', 'breakfast served when', 'morning meal time',

            # WiFi related
            'wifi', 'wi-fi', 'internet', 'password', 'wifi password',
            'is there wifi', 'is there wi-fi', 'network',

            # General facilities
            'hotel facilities', 'amenities', 'services', 'hotel info'
        ]

        # Exclude change date related phrases to avoid conflicts
        change_date_exclusions = [
            'change date', 'change my', 'want change', 'want to change',
            'modify', 'reschedule', 'postpone', 'alter date', 'switch date',
            'move date', 'adjust date', 'update date'
        ]

        user_input_lower = user_input.lower().strip()

        # If it contains change date keywords, don't treat as hotel info
        if any(exclusion in user_input_lower for exclusion in change_date_exclusions):
            return False

        return any(keyword in user_input_lower for keyword in info_keywords)

    def handle_hotel_info_question(self, user_input: str, lang: str = 'en') -> str:
        """Handle common hotel information questions."""
        try:
            user_input_lower = user_input.lower().strip()

            # Check-in time queries
            if any(keyword in user_input_lower for keyword in ['check-in', 'check in', 'checkin']):
                return "Welcome to check in! Check-in time starts at 2 pm. If you need to check in early, please inform the front desk in advance."

            # Check-out time queries
            elif any(keyword in user_input_lower for keyword in ['check-out', 'check out', 'checkout']):
                return "Check-out time is before 12 noon, and additional fees may be incurred after the time."

            # Breakfast time queries (only for information, not booking)
            elif any(keyword in user_input_lower for keyword in ['breakfast time', 'breakfast hours', 'when breakfast', 'breakfast served']):
                return "We offer daily breakfast service from 6am to 11am in the restaurant on the first floor."

            # WiFi queries
            elif any(keyword in user_input_lower for keyword in ['wifi', 'wi-fi', 'internet', 'password', 'network']):
                return "Free Wi-Fi is available in all rooms, the password is written on your room card."

            # General hotel information
            else:
                return "🏨 **Hotel Information:**\n\n🕐 **Check-in:** 2:00 PM\n🕐 **Check-out:** 12:00 PM\n🍳 **Breakfast:** 6:00 AM - 11:00 AM (First floor restaurant)\n📶 **Wi-Fi:** Free in all rooms (Password on room card)"

        except Exception as e:
            logger.error(f"Error handling hotel info question: {str(e)}")
            return "Sorry, I encountered an error. Please ask your question again."

    def detect_feedback_intent(self, user_input: str) -> bool:
        """Detect if user wants to give feedback or rating."""
        feedback_keywords = [
            'feedback', 'rating', 'rate', 'review', 'comment', 'suggestion',
            'satisfied', 'satisfaction', 'experience', 'service quality',
            'how was', 'what do you think', 'opinion'
        ]

        user_input_lower = user_input.lower().strip()
        return any(keyword in user_input_lower for keyword in feedback_keywords)

    def handle_feedback_intent(self, user_input: str, lang: str = 'en') -> str:
        """Handle feedback and rating request."""
        try:
            # Check if rating is already provided in the message
            import re
            rating_match = re.search(r'(\d)\s*(?:star|stars|/5|out of 5)', user_input, re.IGNORECASE)

            if rating_match:
                rating = int(rating_match.group(1))
                if 1 <= rating <= 5:
                    self.user_data['feedback_rating'] = rating
                    return self.process_feedback_rating(rating, lang)

            self.state = "collecting_feedback_rating"
            return "🌟 **We Value Your Feedback!**\n\nAre you satisfied with your stay? Please rate your experience from 1-5 stars and leave valuable comments.\n\n⭐ 1 = Very Dissatisfied\n⭐⭐ 2 = Dissatisfied\n⭐⭐⭐ 3 = Neutral\n⭐⭐⭐⭐ 4 = Satisfied\n⭐⭐⭐⭐⭐ 5 = Very Satisfied\n\nPlease type your rating (1-5):"

        except Exception as e:
            logger.error(f"Error handling feedback intent: {str(e)}")
            return "Sorry, I encountered an error processing your feedback request. Please try again."

    def handle_feedback_rating(self, user_input: str, lang: str = 'en') -> str:
        """Handle feedback rating input."""
        try:
            # Extract rating from input
            import re
            rating_match = re.search(r'(\d)', user_input)

            if rating_match:
                rating = int(rating_match.group(1))
                if 1 <= rating <= 5:
                    self.user_data['feedback_rating'] = rating
                    return self.process_feedback_rating(rating, lang)
                else:
                    return "Please provide a rating between 1-5 stars."
            else:
                return "Please provide a numeric rating from 1 to 5. For example, type '4' for 4 stars."

        except Exception as e:
            logger.error(f"Error handling feedback rating: {str(e)}")
            return "Sorry, I encountered an error. Please provide your rating (1-5)."

    def process_feedback_rating(self, rating: int, lang: str = 'en') -> str:
        """Process the feedback rating and ask for comments."""
        try:
            if rating >= 4:
                # High rating (4-5 stars)
                self.state = "collecting_feedback_comment"
                return f"🌟 Thank you for the {rating}-star rating! We're delighted that you're satisfied with our service!\n\nWould you like to leave any additional comments about your stay? (Optional - you can type 'no' to skip)"
            else:
                # Low rating (1-3 stars)
                self.state = "collecting_feedback_comment"
                return f"😔 Thank you for the {rating}-star rating. We're sorry that we didn't fully meet your expectations this time.\n\nIs there anything specific we can improve? We value your suggestions very much and would appreciate your detailed feedback:"

        except Exception as e:
            logger.error(f"Error processing feedback rating: {str(e)}")
            return "Thank you for your rating. Would you like to leave any comments?"

    def handle_feedback_comment(self, user_input: str, lang: str = 'en') -> str:
        """Handle feedback comment input."""
        try:
            rating = self.user_data.get('feedback_rating', 0)

            # Save feedback (in a real implementation, save to database)
            from django.utils import timezone
            feedback_data = {
                'rating': rating,
                'comment': user_input.strip(),
                'timestamp': timezone.now()
            }

            # Log feedback for now (in production, save to database)
            logger.info(f"Customer feedback received: {feedback_data}")

            # Reset state
            self.state = "greeting"
            self.user_data = {'is_returning_customer': True}

            if rating >= 4:
                return f"🎉 Thank you very much for your {rating}-star rating and valuable feedback! We're glad that you're satisfied with our service and look forward to seeing you again!\n\nYour comments help us maintain our high standards. Is there anything else I can help you with today?"
            else:
                return f"🙏 Thank you for your {rating}-star rating and detailed feedback. We sincerely apologize for not meeting your expectations and truly appreciate your suggestions.\n\nWe will review your feedback carefully and work on improvements. We hope to have the opportunity to provide you with a better experience in the future. Is there anything else I can help you with today?"

        except Exception as e:
            logger.error(f"Error handling feedback comment: {str(e)}")
            return "Thank you for your feedback. Is there anything else I can help you with?"

    def detect_room_service_request(self, user_input: str) -> bool:
        """Detect if user wants room service (cleaning or DND)."""
        room_service_keywords = [
            # General room service keywords
            'room services', 'room service', 'customer service', 'guest services',
            'in-room service', 'hotel services', 'room assistance',

            # Housekeeping/Cleaning keywords
            'clean the room', 'room cleaning', 'housekeeping', 'clean my room',
            'someone to clean', 'room needs cleaning', 'cleaning service',
            'tidy up', 'make up room', 'housekeeping service',
            'can you help me clean my room', 'the room needs to be cleaned',
            'arrange cleaning service', 'i need to clean my room',

            # Do Not Disturb keywords
            'do not disturb', 'don\'t disturb', 'dnd', 'quiet time',
            'need quiet', 'privacy', 'no interruption', 'please don\'t disturb',
            'i want to set do not disturb', 'turn on do not disturb mode',
            'i need quiet', 'please don\'t disturb me'
        ]

        user_input_lower = user_input.lower().strip()
        return any(keyword in user_input_lower for keyword in room_service_keywords)

    def detect_off_topic_intent(self, user_input: str) -> tuple[bool, str]:
        """Enhanced off-topic detection with expanded categories and better pattern matching."""
        user_input_lower = user_input.lower().strip()

        # Personal/Emotional questions (English + Chinese)
        personal_keywords = [
            'will you fall in love', 'do you love', 'are you lonely', 'do you have feelings',
            'what do you like to eat', 'what is your favorite', 'do you sleep', 'are you happy',
            'do you dream', 'what makes you sad', 'are you alive', 'do you have friends',
            'are you really emotionless', 'emotionless', 'do you have emotions', 'can you feel',
            'what makes you happy', 'do you get tired', 'are you bored', 'do you like music',
            'are you married', 'do you have family', 'where do you live', 'how old are you',
            'what do you look like', 'are you male or female', 'do you eat', 'do you drink',
            'do you have girlfriend', 'do you have boyfriend', 'are you single', 'dating',
            'relationship status', 'do you have children', 'do you have kids', 'your age',
            'your birthday', 'when were you born', 'your name', 'what is your name',
            'do you have siblings', 'do you have brothers', 'do you have sisters', 'family',
            'do you have pets', 'do you have pet', 'cute', 'you are cute', 'i think you are cute',
            'where do you live', 'where are you from', 'what do you do', 'who is your boss',
            'who created you', 'who made you', 'who owns you', 'your creator', 'your owner',
            'do you prefer sea or mountain', 'prefer sea', 'prefer mountain', 'sea or mountain',
            # Chinese keywords
            '你有兄弟姐妹吗', '兄弟姐妹', '你有宠物', '有宠物', '你很可爱', '很可爱', '可爱',
            '你多大了', '多大了', '年龄', '你住在哪里', '住在哪里', '你喜欢', '喜欢',
            '你相信命运', '相信命运', '命运', '谁是你的老板', '你的老板', '老板'
        ]

        # Technical AI/Technology inquiry (English + Chinese)
        ai_tech_keywords = [
            'how ai works', 'how do you work', 'what is artificial intelligence',
            'how are you programmed', 'what language are you written in', 'who created you',
            'how smart are you', 'what is machine learning', 'are you a robot',
            'artificial intelligence', 'machine learning', 'neural network', 'algorithm',
            'how were you made', 'who built you', 'what technology', 'programming language',
            'python', 'javascript', 'database', 'server', 'cloud computing', 'chatgpt',
            'openai', 'google', 'microsoft', 'what model are you', 'llm', 'transformer',
            'what program', 'what programming', 'written in', 'coded in', 'built with',
            'ai regulation', 'ai monitoring', 'ai supervision', 'ai ethics', 'ai future',
            'humans replaced by ai', 'ai replace humans', 'ai takeover', 'ai threat',
            'will humans be replaced by ai', 'humans be replaced', 'replaced by ai',
            'do you support', 'political party', 'politics', 'government opinion',
            # Chinese keywords
            '你是用什么程序写的', '什么程序', '程序写的', '人类会被AI取代', 'AI取代', '取代',
            '你怎么看AI监管', 'AI监管', '监管问题', '你支不支持', '政党', '支持某某政党'
        ]

        # Time and Date queries
        time_keywords = [
            'what time is it', 'current time', 'what time now', 'tell me the time',
            'what day is it', 'what date today', 'what year is it', 'time now',
            'current date', 'today date', 'what day today', 'what month',
            'what season', 'calendar', 'timezone', 'clock'
        ]

        # Weather and Climate
        weather_keywords = [
            'will it rain', 'weather today', 'is it sunny', 'temperature today',
            'weather forecast', 'is it hot', 'is it cold', 'weather in malaysia',
            'will it storm', 'is it cloudy', 'weather like', 'raining today',
            'sunny today', 'cloudy today', 'temperature now', 'how hot today',
            'humidity', 'wind', 'typhoon', 'monsoon', 'climate', 'season weather'
        ]

        # Entertainment requests (English + Chinese)
        entertainment_keywords = [
            'tell me a joke', 'sing a song', 'funny story', 'make me laugh',
            'tell joke', 'entertainment', 'play music', 'dance', 'game',
            'riddle', 'puzzle', 'story', 'poem', 'sing', 'play a game',
            'do you play games', 'play games', 'gaming', 'video games',
            'can you sing', 'sing for me', 'music', 'movie', 'film',
            'can you tell me lottery numbers', 'lottery numbers', 'lottery',
            'tell me lottery', 'lotto numbers', 'lotto', 'gambling',
            # Chinese keywords
            '你玩游戏吗', '玩游戏', '游戏', '你喜欢看什么电影', '看什么电影', '电影',
            '你可以唱歌吗', '可以唱歌', '唱歌', '能告诉我乐透号码', '乐透号码', '彩票'
        ]

        # News and Current Events
        news_keywords = [
            'latest news', 'current events', 'news today', 'what happened',
            'breaking news', 'politics', 'government', 'president', 'election',
            'stock market', 'economy', 'covid', 'pandemic', 'world news'
        ]

        # Sports and Recreation
        sports_keywords = [
            'sports score', 'football', 'basketball', 'soccer', 'tennis',
            'olympics', 'world cup', 'match result', 'game score', 'tournament',
            'player', 'team', 'championship', 'league', 'sports news'
        ]

        # Food and Cooking (non-hotel)
        food_keywords = [
            'cooking recipe', 'how to cook', 'food recipe', 'ingredients',
            'restaurant recommendation', 'best food', 'local cuisine', 'street food',
            'cooking tips', 'recipe for', 'how to make', 'cooking method',
            'cook pasta', 'pasta recipe', 'how do i cook', 'best local restaurants',
            'local restaurants', 'where to eat', 'food places', 'cuisine'
        ]

        # Shopping and Products
        shopping_keywords = [
            'shopping', 'buy online', 'product recommendation', 'best price',
            'where to buy', 'online store', 'discount', 'sale', 'coupon',
            'shopping mall', 'market', 'brand', 'product review',
            'buy clothes', 'where can i buy', 'best online stores', 'online stores',
            'purchase', 'retail', 'store', 'shop'
        ]

        # Travel (non-hotel specific)
        travel_keywords = [
            'flight booking', 'airline', 'airport', 'visa', 'passport',
            'travel insurance', 'currency exchange', 'tourist attraction',
            'sightseeing', 'tour guide', 'travel tips', 'backpacking',
            'vacation planning', 'itinerary', 'travel blog'
        ]

        # Education and Learning (English + Chinese)
        education_keywords = [
            'how to learn', 'study tips', 'university', 'college', 'school',
            'course recommendation', 'online learning', 'tutorial', 'lesson',
            'homework help', 'exam preparation', 'language learning',
            'how to study', 'study better', 'best universities', 'education',
            'learning', 'academic', 'student', 'studying', 'help me write',
            'write homework', 'do homework', 'assignment', 'essay', 'research',
            'when is malaysia independence day', 'malaysia independence day', 'independence day',
            'who invented the light bulb', 'invented the light bulb', 'light bulb inventor',
            'who invented', 'invented', 'history question', 'general knowledge',
            # Chinese keywords
            '你能帮我写作业', '帮我写作业', '写作业', '作业', '马来西亚独立日', '独立日',
            '谁发明了电灯', '发明了电灯', '发明', '你觉得哪家手机', '哪家手机', '手机最好用'
        ]

        # Health and Medical
        health_keywords = [
            'health advice', 'medical question', 'symptoms', 'doctor',
            'hospital', 'medicine', 'treatment', 'diet', 'exercise',
            'wellness', 'mental health', 'stress', 'sleep problems',
            'i have a headache', 'headache', 'how to exercise', 'fitness',
            'sick', 'pain', 'hurt', 'medical', 'health'
        ]

        # Philosophy and Life
        philosophy_keywords = [
            'meaning of life', 'purpose', 'philosophy', 'existence',
            'consciousness', 'reality', 'universe', 'god', 'religion',
            'spirituality', 'meditation', 'wisdom', 'truth',
            'do you believe in fate', 'believe in fate', 'fate', 'destiny',
            'believe in destiny', 'do you believe', 'belief', 'faith'
        ]

        # Random/Nonsense questions
        random_keywords = [
            'have egg first or have chicken first', 'egg or chicken', 'chicken or egg',
            'random question', 'silly question', 'weird question', 'strange question',
            'nonsense', 'random', 'what if', 'hypothetical', 'imagine if'
        ]

        # Science and Nature
        science_keywords = [
            'science', 'physics', 'chemistry', 'biology', 'astronomy',
            'space', 'planets', 'stars', 'galaxy', 'universe facts',
            'scientific', 'research', 'experiment', 'discovery',
            'nature', 'animals', 'plants', 'environment', 'ecology'
        ]

        # Technology and Gadgets
        tech_keywords = [
            'smartphone', 'iphone', 'android', 'computer', 'laptop',
            'internet', 'wifi', 'bluetooth', 'app', 'software',
            'technology news', 'gadgets', 'electronics', 'digital',
            'social media', 'facebook', 'instagram', 'twitter', 'tiktok'
        ]

        # Money and Finance
        finance_keywords = [
            'money', 'salary', 'investment', 'stock', 'cryptocurrency',
            'bitcoin', 'finance', 'banking', 'loan', 'credit card',
            'budget', 'savings', 'financial advice', 'rich', 'poor',
            'economy', 'inflation', 'recession', 'market'
        ]

        # Relationships and Social
        social_keywords = [
            'friends', 'friendship', 'social life', 'party', 'dating advice',
            'relationship advice', 'marriage', 'wedding', 'family problems',
            'social media', 'networking', 'meeting people', 'loneliness',
            'social skills', 'communication', 'conflict resolution'
        ]

        # Career and Work
        career_keywords = [
            'job', 'career', 'work', 'employment', 'interview',
            'resume', 'cv', 'salary negotiation', 'promotion',
            'workplace', 'boss', 'colleague', 'office', 'business',
            'entrepreneur', 'startup', 'freelance', 'remote work'
        ]

        # Hobbies and Interests
        hobby_keywords = [
            'hobby', 'interests', 'reading', 'books', 'movies',
            'music', 'art', 'painting', 'drawing', 'photography',
            'gaming', 'video games', 'collecting', 'crafts',
            'gardening', 'cooking hobby', 'baking', 'diy'
        ]

        # Check each category with priority order
        if any(keyword in user_input_lower for keyword in personal_keywords):
            return True, 'personal'
        elif any(keyword in user_input_lower for keyword in ai_tech_keywords):
            return True, 'ai_tech'
        elif any(keyword in user_input_lower for keyword in random_keywords):
            return True, 'random'
        elif any(keyword in user_input_lower for keyword in time_keywords):
            return True, 'time_query'
        elif any(keyword in user_input_lower for keyword in weather_keywords):
            return True, 'weather'
        elif any(keyword in user_input_lower for keyword in entertainment_keywords):
            return True, 'entertainment'
        elif any(keyword in user_input_lower for keyword in news_keywords):
            return True, 'news'
        elif any(keyword in user_input_lower for keyword in sports_keywords):
            return True, 'sports'
        elif any(keyword in user_input_lower for keyword in food_keywords):
            return True, 'food'
        elif any(keyword in user_input_lower for keyword in shopping_keywords):
            return True, 'shopping'
        elif any(keyword in user_input_lower for keyword in travel_keywords):
            return True, 'travel'
        elif any(keyword in user_input_lower for keyword in education_keywords):
            return True, 'education'
        elif any(keyword in user_input_lower for keyword in health_keywords):
            return True, 'health'
        elif any(keyword in user_input_lower for keyword in philosophy_keywords):
            return True, 'philosophy'
        elif any(keyword in user_input_lower for keyword in science_keywords):
            return True, 'science'
        elif any(keyword in user_input_lower for keyword in tech_keywords):
            return True, 'technology'
        elif any(keyword in user_input_lower for keyword in finance_keywords):
            return True, 'finance'
        elif any(keyword in user_input_lower for keyword in social_keywords):
            return True, 'social'
        elif any(keyword in user_input_lower for keyword in career_keywords):
            return True, 'career'
        elif any(keyword in user_input_lower for keyword in hobby_keywords):
            return True, 'hobby'

        return False, 'hotel_related'

    def handle_invalid_input_redirect(self, user_input: str, lang: str = 'en') -> str:
        """Handle invalid/random input with polite guidance back to hotel services."""
        try:
            # Get appropriate response based on language
            responses = self.intents.get('invalid_input', {}).get('responses', {}).get(lang, [])

            if not responses:
                # Fallback responses if no language-specific responses found
                if lang == 'zh':
                    responses = [
                        "嗯...这看起来不太像相关内容。我可以协助您处理酒店服务，如查看预订、安排早餐或申请客房清洁服务。您需要我帮您处理哪一项？"
                    ]
                else:
                    responses = [
                        "Well... this doesn't look like very relevant content. I can assist you with hotel services, such as checking reservations, arranging breakfast, or requesting room cleaning services. Which one do you need me to help you with?"
                    ]

            # Select a random response for variety
            response = random.choice(responses)

            # Add service menu for guidance
            if lang == 'zh':
                service_menu = """
🏨 **我可以帮您处理以下服务：**
1. 📅 预订房间
2. ❌ 取消预订
3. ⬆️ 升级房间
4. 📆 更改日期
5. ➕ 延长住宿
6. 🍳 早餐服务
7. 🧹 客房清洁
8. ℹ️ 酒店信息

请告诉我您需要哪项服务？"""
            else:
                service_menu = """
🏨 **I can help you with these services:**
1. 📅 Book a room
2. ❌ Cancel booking
3. ⬆️ Upgrade room
4. 📆 Change dates
5. ➕ Extend stay
6. 🍳 Breakfast service
7. 🧹 Room cleaning
8. ℹ️ Hotel information

Which service do you need?"""

            return f"{response}\n{service_menu}"

        except Exception as e:
            logger.error(f"Error handling invalid input redirect: {str(e)}")
            # Fallback response
            if lang == 'zh':
                return "我不太明白您的意思。我可以帮您预订房间、查询信息或处理其他酒店服务。您需要什么帮助？"
            else:
                return "I'm not sure I understand. I can help you book rooms, check information, or handle other hotel services. What do you need help with?"

    def handle_off_topic_redirect(self, user_input: str, off_topic_type: str, lang: str = 'en') -> str:
        """Enhanced off-topic handling with comprehensive category responses and smart guidance."""
        try:
            user_input_lower = user_input.lower().strip()

            # Track off-topic attempts for better user experience
            off_topic_count = self.user_data.get('off_topic_count', 0) + 1
            self.user_data['off_topic_count'] = off_topic_count

            # Specific keyword-based responses (highest priority)
            if 'fall in love' in user_input_lower or ('love' in user_input_lower and 'you' in user_input_lower):
                return "Although I don't have an emotion system yet, I can help you arrange a romantic Executive Suite, which may be more suitable for a date 😊\nDo you need me to book a room for you?"

            elif 'what do you like to eat' in user_input_lower or ('favorite' in user_input_lower and 'eat' in user_input_lower):
                return "My favorite is... the breakfast menu ordered by the guests! 🍳 Our breakfast is served from 6am-11am at the first floor restaurant.\nWould you like to add breakfast service to your booking?"

            elif 'what time is it' in user_input_lower or 'current time' in user_input_lower:
                return "Time flies when you're planning the perfect stay! 🕒 Speaking of time, our check-in is at 2pm and check-out at 12pm.\nDo you need help booking a room?"

            elif 'what program' in user_input_lower or 'what programming' in user_input_lower or 'written in' in user_input_lower:
                return "I'm designed to be your hotel assistant! 🤖 I can help with booking rooms, checking information, extending stays, and much more.\nDo you need me to help you book a room or check our facilities?"

            elif 'do you play games' in user_input_lower or 'play games' in user_input_lower:
                return "I don't play games myself, but I can help you arrange a comfortable and quiet room where you can enjoy gaming! 🎮 Our rooms have excellent WiFi for online gaming.\nWould you like to check available rooms?"

            elif 'do you have siblings' in user_input_lower or 'brothers' in user_input_lower or 'sisters' in user_input_lower:
                return "I don't have family, but I'm an expert in hotel services! 😊 I can help you book rooms for family gatherings or solo stays.\nDo you need a room booking or want to check our breakfast times?"

            elif 'help me write' in user_input_lower or 'write homework' in user_input_lower or 'do homework' in user_input_lower:
                return "I specialize in hotel services rather than homework! 📚 However, our quiet rooms with free WiFi are perfect for studying and working.\nWould you like me to help you find a suitable room for studying?"

            elif 'who is your boss' in user_input_lower or 'your boss' in user_input_lower:
                return "My mission is to ensure every guest has a comfortable and worry-free stay! 😊 I'm here to help with your accommodation needs.\nDo you need assistance with booking or checking hotel services?"

            elif 'humans replaced by ai' in user_input_lower or 'ai replace humans' in user_input_lower:
                return "That's an interesting topic! 🤔 For now, I'm focused on helping you with hotel bookings, room upgrades, and service inquiries.\nWould you like me to check room availability or help with any hotel services?"

            elif 'malaysia independence' in user_input_lower or 'independence day' in user_input_lower:
                return "I currently only provide hotel-related information! 🏨 If you need accommodation during holiday periods, I can help check room availability!\nWould you like to see our room options?"

            elif 'do you believe in fate' in user_input_lower or 'believe in destiny' in user_input_lower or 'fate' in user_input_lower:
                return "I believe a great journey starts with comfortable accommodation! 😊 ✨\nWould you like me to recommend room types or services?"

            elif 'do you have pets' in user_input_lower or 'have pets' in user_input_lower:
                return "I don't have pets, but our hotel has pet-friendly room options! 🐕 We welcome furry friends with special arrangements.\nWould you like to learn more about our pet-friendly accommodations?"

            elif 'sea or mountain' in user_input_lower or 'beach or mountain' in user_input_lower:
                return "I don't have preferences, but our hotel is conveniently located in the city center with easy access to transportation! 🏙️ We're well-connected to both coastal and highland destinations.\nWould you like location information or help with booking?"

            elif 'you are cute' in user_input_lower or 'very cute' in user_input_lower:
                return "Thank you for the compliment! 😊 If you need room booking or want to check our breakfast service, I'm happy to help!\nWhat can I assist you with today?"

            elif 'lottery numbers' in user_input_lower or 'lotto numbers' in user_input_lower:
                return "Haha, if I could predict lottery numbers, I might have become a resort owner! 😄 But right now I can arrange a comfortable room for you.\nWould you like to check room rates?"

            elif 'political party' in user_input_lower or 'politics' in user_input_lower:
                return "I focus on providing the best accommodation services! 🏨 We can discuss room types that suit your needs instead.\nWhat kind of room are you looking for?"

            elif 'what movies' in user_input_lower or 'favorite movie' in user_input_lower:
                return "I don't have time to watch movies, but I can help you find the most comfortable room where you can relax and watch movies! 🎬 Our rooms have great entertainment systems.\nWould you like me to arrange a room for you?"

            elif 'can you sing' in user_input_lower or 'sing for me' in user_input_lower:
                return "I can't sing, but I can arrange rooms with TV and WiFi so you can enjoy music to your heart's content! 🎵 Our rooms are perfect for relaxation.\nWhat type of room would you prefer?"

            elif 'ai regulation' in user_input_lower or 'ai monitoring' in user_input_lower:
                return "That's a topic worth discussing, but I'm currently focused on serving your hotel-related needs! 🏨 Would you like to check check-in times or service options?"

            elif 'who invented' in user_input_lower and 'light bulb' in user_input_lower:
                return "That was Thomas Edison! 💡 Speaking of lighting, our rooms all have smart lighting controls! 😊\nWould you like me to arrange a comfortable room for you?"

            elif 'which phone' in user_input_lower or 'best phone' in user_input_lower:
                return "Phone brands each have their strengths, just like our different room types! 📱 We have Standard, Deluxe, and Executive rooms, each with unique advantages.\nWhich room type interests you - Standard, Deluxe, or Executive?"

            elif 'how old are you' in user_input_lower or 'your age' in user_input_lower:
                return "I'm a virtual assistant that's always online! 🤖 Now, I can help you book rooms or add breakfast service.\nDo you need assistance with anything?"

            elif 'where do you live' in user_input_lower:
                return "I 'live' in this hotel's system, serving guests 24/7! 😊 🏨\nCan I help you with check-in arrangements or hotel facility inquiries?"

            elif ('rain' in user_input_lower or 'weather' in user_input_lower) and 'malaysia' in user_input_lower:
                return "No matter what the weather is like outside, our rooms are always warm and comfortable! ☀️ Plus, we have free WiFi in all rooms.\nDo you want me to check if there are any rooms available?"

            elif 'are you really emotionless' in user_input_lower or 'emotionless' in user_input_lower:
                return "Although I don't have an emotion system yet, I can help you arrange a romantic Executive Suite, which may be more suitable for a date 😊\nDo you need me to book a room for you?"

            elif 'have egg first or have chicken first' in user_input_lower or ('egg' in user_input_lower and 'chicken' in user_input_lower):
                return "That's a classic question! 🐣 Speaking of eggs, our breakfast menu includes fresh eggs prepared your way! Our breakfast is served 6am-11am.\nWould you like to add breakfast service to your booking?"

            # Chinese specific responses
            elif '你是用什么程序写的' in user_input_lower or '什么程序' in user_input_lower:
                return "我是一个专为酒店服务设计的智能助手，如果您需要订房、取消订单或查询设施，我可以随时协助您！"

            elif '你玩游戏吗' in user_input_lower or '玩游戏' in user_input_lower:
                return "我自己不玩游戏，但我可以帮您安排一个舒适安静的房间，让您尽情玩游戏放松一下！是否要查看空房信息呢？"

            elif '你有兄弟姐妹吗' in user_input_lower or '兄弟姐妹' in user_input_lower:
                return "我没有家人，但我在酒店服务方面可是专家！您需要预订房间还是查看早餐时间呢？"

            elif '你能帮我写作业吗' in user_input_lower or '帮我写作业' in user_input_lower:
                return "我专注于协助您处理酒店相关服务，例如预订房间、延长住宿或添加服务。需要我帮您查看可用房型吗？"

            elif '谁是你的老板' in user_input_lower or '你的老板' in user_input_lower:
                return "我的任务是让每位客人住得舒适安心。您是否需要我帮您处理住宿相关事务？"

            elif '人类会被AI取代' in user_input_lower or 'AI取代' in user_input_lower:
                return "这是个有趣的问题！不过目前我更专注在帮您处理预订、查询房价等酒店服务。需要我查看一下空房吗？"

            elif '马来西亚独立日' in user_input_lower or '独立日' in user_input_lower:
                return "我目前只能提供酒店相关的信息哦！如果您在节日期间需要住宿，我可以帮您查看房间供应情况！"

            elif '你相信命运吗' in user_input_lower or '相信命运' in user_input_lower:
                return "我相信一段美好的旅程从舒适的住宿开始 😊\n是否需要我为您推荐房型或服务？"

            elif '你有没有宠物' in user_input_lower or '有宠物' in user_input_lower:
                return "我没有宠物，但我们酒店有宠物友好型房间选项。您是否想了解一下呢？"

            elif '你喜欢海边还是山上' in user_input_lower or '海边还是山上' in user_input_lower:
                return "我没有偏好，但我们酒店靠近市中心，交通便利！需要我提供周边景点和住宿信息吗？"

            elif '我觉得你很可爱' in user_input_lower or '很可爱' in user_input_lower:
                return "谢谢夸奖 😊 如果您需要预订房间或查看我们的早餐服务，我很乐意帮忙！"

            elif '能告诉我乐透号码' in user_input_lower or '乐透号码' in user_input_lower:
                return "哈哈，如果我能预测乐透，那我也许就成了度假村老板了 😄\n不过我现在能为您安排一间舒适的房间。是否需要查看房价？"

            elif '你支不支持某某政党' in user_input_lower or '支持某某政党' in user_input_lower:
                return "我专注于为您提供最优质的住宿服务。我们可以一起看看有什么房型适合您吗？"

            elif '你喜欢看什么电影' in user_input_lower or '看什么电影' in user_input_lower:
                return "我没时间看电影，但我能帮您找到最舒适的客房，让您安心看片放松！需要我为您安排一晚吗？"

            elif '你可以唱歌吗' in user_input_lower or '可以唱歌' in user_input_lower:
                return "我不会唱歌，但可以安排房间里的电视、Wi-Fi让您尽情听歌！您想预订哪种房型呢？"

            elif 'AI监管' in user_input_lower or '监管问题' in user_input_lower:
                return "这是个值得讨论的话题，但我现在专注于为您服务酒店相关事务。您是否需要查询一下入住时间或服务项目？"

            elif '谁发明了电灯' in user_input_lower or '发明了电灯' in user_input_lower:
                return "是托马斯·爱迪生哦！现在，我们的房间都有智能灯控 😊\n需要我为您安排一个舒适的客房吗？"

            elif '你觉得哪家手机' in user_input_lower or '哪家手机' in user_input_lower:
                return "手机品牌各有特色，就像我们不同的房型一样，各有优势。您想了解标准房、豪华房还是套房呢？"

            elif '你多大了' in user_input_lower or '多大了' in user_input_lower:
                return "我是一个永远在线的虚拟助理！现在，我可以帮您预订房间或添加早餐服务，是否需要帮助？"

            elif '你住在哪里' in user_input_lower or '住在哪里' in user_input_lower:
                return "我就\"住\"在这家酒店的系统中，每天都为客人提供服务 😊\n请问您是否需要我帮忙处理您的入住或查询酒店设施？"

            # English specific responses
            elif 'will humans be replaced by ai' in user_input_lower or 'humans be replaced' in user_input_lower:
                return "That's an interesting topic! 🤔 For now, I'm focused on helping you with hotel bookings, room upgrades, and service inquiries.\nWould you like me to check room availability or help with any hotel services?"

            elif 'when is malaysia independence day' in user_input_lower or 'malaysia independence day' in user_input_lower:
                return "I currently only provide hotel-related information! 🏨 If you need accommodation during holiday periods, I can help check room availability!\nWould you like to see our room options?"

            elif 'do you believe in fate' in user_input_lower or 'believe in fate' in user_input_lower:
                return "I believe a great journey starts with comfortable accommodation! 😊 ✨\nWould you like me to recommend room types or services?"

            elif 'do you prefer sea or mountain' in user_input_lower or 'prefer sea' in user_input_lower:
                return "I don't have preferences, but our hotel is conveniently located in the city center with easy access to transportation! 🏙️ We're well-connected to both coastal and highland destinations.\nWould you like location information or help with booking?"

            elif 'can you tell me lottery numbers' in user_input_lower or 'lottery numbers' in user_input_lower:
                return "Haha, if I could predict lottery numbers, I might have become a resort owner! 😄 But right now I can arrange a comfortable room for you.\nWould you like to check room rates?"

            elif 'who invented the light bulb' in user_input_lower or 'invented the light bulb' in user_input_lower:
                return "That was Thomas Edison! 💡 Speaking of lighting, our rooms all have smart lighting controls! 😊\nWould you like me to arrange a comfortable room for you?"

            # Category-based responses with smart guidance
            elif off_topic_type == 'personal':
                if off_topic_count == 1:
                    return "I focus on helping with hotel services! 😊 I can assist with booking rooms, cancellations, room upgrades, extending stays, and adding services like breakfast or.\nWhat can I help you with today?"
                else:
                    self.user_data['showing_service_menu'] = True
                    return """I'm here to help with hotel services! Let me show you what I can do:

🏨 **Book a room** - Find and reserve your perfect stay
❌ **Cancel booking** - Cancel existing reservations
🆙 **Upgrade room** - Upgrade to a better room type
⏳ **Extend stay** - Add more nights to your booking
🍳 **Add services** - Breakfast, airport transfer, and more

Which service interests you?"""

            elif off_topic_type == 'ai_tech':
                return "I'm designed to be your hotel assistant! 🤖 I can help with booking rooms, checking information, extending stays, and much more.\nDo you need me to help you book a room or check our facilities?"

            elif off_topic_type == 'weather':
                return "No matter what the weather is like outside, our rooms are always warm and comfortable! ☀️ We also have climate control in every room.\nWould you like to check room availability?"

            elif off_topic_type == 'time_query':
                return "Perfect timing to plan your stay! ⏰ Our hotel operates 24/7 with check-in at 2pm and check-out at 12pm.\nCan I help you with a booking?"

            elif off_topic_type == 'entertainment':
                return "While I can't entertain you with jokes, I can help make your stay entertaining! 🎭 Our Executive rooms have great city views and we're close to entertainment districts.\nWould you like to book a room with a view?"

            elif off_topic_type == 'news':
                return "I don't have access to current news, but I have great news about our hotel! 📰 We offer comfortable rooms, excellent service, and convenient location.\nWould you like to hear about our room options?"

            elif off_topic_type == 'sports':
                return "While I can't give you sports scores, our hotel is perfect for sports travelers! ⚽ We're located near sports venues and offer comfortable stays for athletes and fans.\nNeed a room for your sports trip?"

            elif off_topic_type == 'food':
                return "Speaking of food, our hotel offers delicious breakfast service! 🍽️ We serve fresh meals from 6am-11am at our first floor restaurant, plus we're near great local restaurants.\nWould you like to add breakfast to your booking?"

            elif off_topic_type == 'shopping':
                return "Great news for shoppers! 🛍️ Our hotel is conveniently located near major shopping areas and malls. Perfect for a shopping getaway!\nWould you like to book a room for your shopping trip?"

            elif off_topic_type == 'travel':
                return "Perfect! As a travel expert, I can help with your accommodation needs! ✈️ We offer comfortable rooms, convenient location, and excellent service for all travelers.\nLet me help you book the perfect room for your trip!"

            elif off_topic_type == 'education':
                return "Learning is important! 📚 Our hotel offers quiet rooms perfect for studying, plus free WiFi for online learning. Great for students and business travelers.\nNeed a quiet room for work or study?"

            elif off_topic_type == 'health':
                return "Your health and comfort are important! 🏥 Our hotel offers clean, comfortable rooms with climate control and peaceful environment for rest and recovery.\nWould you like to book a comfortable room?"

            elif off_topic_type == 'philosophy':
                return "Deep thoughts deserve a comfortable place to think! 🤔 Our quiet Executive rooms provide the perfect environment for reflection and contemplation.\nWould you like a peaceful room for your stay?"

            elif off_topic_type == 'random':
                return "That's an interesting question! 🤔 While I ponder that, let me help you with something I know well - hotel bookings! Our rooms are perfect for relaxing and thinking.\nWould you like to book a comfortable room?"

            elif off_topic_type == 'science':
                return "Science is fascinating! 🔬 Our hotel is scientifically designed for comfort with climate control, ergonomic furniture, and optimal lighting for rest.\nWould you like to experience our scientifically comfortable rooms?"

            elif off_topic_type == 'technology':
                return "Technology is amazing! 📱 Our hotel features modern tech amenities including free WiFi in all rooms, smart climate control, and digital check-in options.\nWould you like to book a tech-friendly room?"

            elif off_topic_type == 'finance':
                return "Smart financial planning includes budgeting for great accommodations! 💰 Our hotel offers excellent value with competitive rates and quality service.\nWould you like to see our room rates and make a cost-effective booking?"

            elif off_topic_type == 'social':
                return "Social connections are important! 👥 Our hotel is perfect for social gatherings, business meetings, or romantic getaways. We're located in a vibrant area with great social venues nearby.\nWould you like to book a room for your social plans?"

            elif off_topic_type == 'career':
                return "Career success often requires travel! 💼 Our hotel is perfect for business travelers with quiet rooms for work, free WiFi, and convenient location for meetings.\nNeed a professional environment for your business trip?"

            elif off_topic_type == 'hobby':
                return "Hobbies are great for relaxation! 🎨 Our hotel provides a peaceful environment perfect for pursuing your interests, plus we're near cultural attractions and hobby shops.\nWould you like a quiet room to enjoy your hobbies?"

            else:
                # Progressive guidance based on off-topic attempts
                if off_topic_count == 1:
                    return "Sorry, I focus on assisting you with hotel services, such as booking rooms, querying information, extending stays, etc.\nDo you need me to help you book a room or check facility information?"
                elif off_topic_count == 2:
                    return "I'm here to help with hotel-related matters! 🏨 I can assist with bookings, cancellations, room upgrades, and service additions.\nWhat hotel service can I help you with?"
                else:
                    # Show comprehensive service menu after multiple off-topic attempts
                    self.user_data['showing_service_menu'] = True
                    return """I specialize in hotel services! Here's how I can help you:

🏨 **Book a room** - Reserve Standard, Deluxe, or Executive rooms
❌ **Cancel booking** - Cancel or modify existing reservations
🆙 **Upgrade room** - Switch to a better room category
⏳ **Extend stay** - Add extra nights to your booking
🍳 **Add breakfast** - RM20/person, served 6am-11am
🚗 **Airport transfer** - Convenient pickup/drop-off service
ℹ️ **Hotel info** - Check-in times, WiFi, amenities

What would you like to do?"""

        except Exception as e:
            logger.error(f"Error handling off-topic redirect: {str(e)}")
            return "I'm here to help with hotel services like booking, cancellation, breakfast, and airport transfers. What can I assist you with today?"

    def detect_service_menu_response(self, user_input: str) -> tuple[bool, str]:
        """Detect if user is responding to the service menu."""
        user_input_lower = user_input.lower().strip()

        # Booking keywords
        booking_keywords = [
            'book a room', 'book room', 'booking', 'reserve', 'reservation',
            'i want to book', 'book', 'room booking', 'make a booking'
        ]

        # Cancel keywords
        cancel_keywords = [
            'cancel an order', 'cancel order', 'cancel', 'cancellation',
            'cancel booking', 'cancel my booking', 'cancel reservation'
        ]

        # Upgrade keywords
        upgrade_keywords = [
            'upgrade a room type', 'upgrade room type', 'upgrade', 'upgrade room',
            'upgrade my room', 'room upgrade'
        ]

        # Extend keywords
        extend_keywords = [
            'extend your stay', 'extend stay', 'extend', 'stay longer',
            'extend my stay', 'prolong stay'
        ]

        # Addon service keywords
        addon_keywords = [
            'add breakfast', 'breakfast service', 'pick-up service', 'airport transfer',
            'add service', 'additional service', 'addon service'
        ]

        # Check each service type
        if any(keyword in user_input_lower for keyword in booking_keywords):
            return True, 'booking'
        elif any(keyword in user_input_lower for keyword in cancel_keywords):
            return True, 'cancel'
        elif any(keyword in user_input_lower for keyword in upgrade_keywords):
            return True, 'upgrade'
        elif any(keyword in user_input_lower for keyword in extend_keywords):
            return True, 'extend'
        elif any(keyword in user_input_lower for keyword in addon_keywords):
            return True, 'addon'

        return False, 'unknown'

    def detect_room_service_menu_response(self, user_input: str) -> tuple[bool, str]:
        """Detect if user is responding to the room service menu."""
        user_input_lower = user_input.lower().strip()

        # Housekeeping keywords
        housekeeping_keywords = [
            'housekeeping', 'cleaning', 'clean', 'tidy', 'make up room',
            'room cleaning', 'clean the room', 'clean my room'
        ]

        # Do Not Disturb keywords
        dnd_keywords = [
            'do not disturb', 'don\'t disturb', 'dnd', 'quiet', 'privacy',
            'no interruption', 'please don\'t disturb'
        ]

        # Room service keywords (food delivery)
        room_service_keywords = [
            'room service', 'food delivery', 'order food', 'food service',
            'meal delivery', 'dining service'
        ]

        # Maintenance keywords
        maintenance_keywords = [
            'maintenance', 'repair', 'fix', 'broken', 'not working',
            'problem', 'issue', 'report'
        ]

        # Check each service type
        if any(keyword in user_input_lower for keyword in housekeeping_keywords):
            return True, 'housekeeping'
        elif any(keyword in user_input_lower for keyword in dnd_keywords):
            return True, 'dnd'
        elif any(keyword in user_input_lower for keyword in room_service_keywords):
            return True, 'room_service'
        elif any(keyword in user_input_lower for keyword in maintenance_keywords):
            return True, 'maintenance'

        return False, 'unknown'

    def handle_room_service_menu_response(self, user_input: str, service_type: str, lang: str = 'en') -> str:
        """Handle user response to room service menu."""
        try:
            # Clear the room service menu flag
            self.user_data.pop('showing_room_service_menu', None)

            if service_type == 'housekeeping':
                # Set service type and proceed with housekeeping request
                self.user_data['room_service_type'] = 'cleaning'
                return self.handle_room_service_request("housekeeping", lang)
            elif service_type == 'dnd':
                # Set service type and proceed with DND request
                self.user_data['room_service_type'] = 'dnd'
                return self.handle_room_service_request("do not disturb", lang)
            elif service_type == 'room_service':
                return "🍽️ Room service for food delivery is coming soon! In the meantime, I can help you with housekeeping or Do Not Disturb services.\n\nWhat would you like to do?"
            elif service_type == 'maintenance':
                return "🛠️ For maintenance requests, please contact our front desk directly at extension 0 or describe the issue and I'll help you report it.\n\nWhat maintenance issue would you like to report?"
            else:
                return "I'd be happy to help! Please specify which room service you need:\n🧹 Housekeeping\n🔕 Do Not Disturb\n🍳 Room Service\n🛠️ Maintenance"

        except Exception as e:
            logger.error(f"Error handling room service menu response: {str(e)}")
            return "I'd be happy to help! Please specify which room service you need."

    def handle_service_menu_response(self, user_input: str, service_type: str, lang: str = 'en') -> str:
        """Handle user response to service menu."""
        try:
            # Clear the service menu flag
            self.user_data.pop('showing_service_menu', None)

            if service_type == 'booking':
                return self.handle_booking_intent(user_input, lang)
            elif service_type == 'cancel':
                return self.handle_cancel_intent(user_input, lang)
            elif service_type == 'upgrade':
                return self.handle_upgrade_intent(user_input, lang)
            elif service_type == 'extend':
                return self.handle_extend_intent(user_input, lang)
            elif service_type == 'addon':
                # For addon services, we need a booking ID first
                self.state = "collecting_booking_id_for_room_service"
                self.user_data['room_service_type'] = 'addon'
                return "I'd be happy to help you add breakfast or airport transfer service! Please provide your booking ID so I can add these services to your reservation."
            else:
                return "I'd be happy to help! Could you please specify which service you need? You can say 'book a room', 'cancel booking', 'upgrade room', 'extend stay', or 'add services'."

        except Exception as e:
            logger.error(f"Error handling service menu response: {str(e)}")
            return "I'd be happy to help! Could you please specify which service you need?"

    def handle_room_service_request(self, user_input: str, lang: str = 'en') -> str:
        """Handle room service request (cleaning or DND)."""
        try:
            user_input_lower = user_input.lower().strip()

            # Check if user is asking for general room services menu
            general_service_keywords = ['room services', 'room service', 'customer service', 'guest services', 'hotel services']
            if any(keyword in user_input_lower for keyword in general_service_keywords):
                # Show room services menu
                self.user_data['showing_room_service_menu'] = True
                return """I can help you with various room services! Here are the available options:

🧹 **Housekeeping** - Room cleaning and tidying service
🔕 **Do Not Disturb** - Set privacy mode for your room
🍳 **Room Service** - Food and beverage delivery (coming soon)
🛠️ **Maintenance** - Report room issues or requests

What type of room service do you need?
You can say "housekeeping", "do not disturb", or describe what you need."""

            # Determine specific service type
            cleaning_keywords = ['clean', 'housekeeping', 'tidy', 'make up', 'cleaning']
            dnd_keywords = ['do not disturb', 'don\'t disturb', 'dnd', 'quiet', 'privacy']

            if any(keyword in user_input_lower for keyword in cleaning_keywords):
                self.user_data['room_service_type'] = 'cleaning'
                service_type = 'cleaning'
            elif any(keyword in user_input_lower for keyword in dnd_keywords):
                self.user_data['room_service_type'] = 'dnd'
                service_type = 'dnd'
            else:
                # If unclear, show the room service menu
                self.user_data['showing_room_service_menu'] = True
                return """I can help you with various room services! Here are the available options:

🧹 **Housekeeping** - Room cleaning and tidying service
🔕 **Do Not Disturb** - Set privacy mode for your room
🍳 **Room Service** - Food and beverage delivery (coming soon)
🛠️ **Maintenance** - Report room issues or requests

What type of room service do you need?
You can say "housekeeping", "do not disturb", or describe what you need."""

            # Check if we have a recently viewed booking
            last_booking = self.user_data.get('last_viewed_booking')
            if last_booking and last_booking.get('booking_id'):
                # Use the last viewed booking for room service
                booking_id = last_booking['booking_id']
                self.user_data['room_service_booking_id'] = booking_id
                return self.process_room_service_request(booking_id, service_type, lang)

            # Check if booking ID is mentioned in the input
            import re
            booking_id_match = re.search(r'\b([A-Z]{2,}-[A-Z0-9-]+)\b', user_input, re.IGNORECASE)

            if booking_id_match:
                booking_id = booking_id_match.group(1)
                self.user_data['room_service_booking_id'] = booking_id
                return self.process_room_service_request(booking_id, service_type, lang)
            else:
                self.state = "collecting_booking_id_for_room_service"
                if service_type == 'cleaning':
                    return "I'd be happy to arrange room cleaning for you! Please provide your booking ID so I can process your housekeeping request."
                else:
                    return "I'll set up Do Not Disturb for you! Please provide your booking ID so I can update your room status."

        except Exception as e:
            logger.error(f"Error handling room service request: {str(e)}")
            return "Sorry, I encountered an error processing your room service request. Please try again."

    def handle_room_service_booking_id(self, user_input: str, lang: str = 'en') -> str:
        """Handle booking ID input for room service."""
        try:
            # Extract booking ID from input
            import re
            booking_id_match = re.search(r'([A-Z0-9-]+)', user_input, re.IGNORECASE)

            if booking_id_match:
                booking_id = booking_id_match.group(1)
                self.user_data['room_service_booking_id'] = booking_id
                service_type = self.user_data.get('room_service_type', 'cleaning')
                return self.process_room_service_request(booking_id, service_type, lang)
            else:
                return "Please provide a valid booking ID. For example: BK-12345"

        except Exception as e:
            logger.error(f"Error handling room service booking ID: {str(e)}")
            return "Sorry, I encountered an error. Please provide your booking ID again."

    def process_room_service_request(self, booking_id: str, service_type: str, lang: str = 'en') -> str:
        """Process the room service request."""
        try:
            from hotel_booking.models import Booking

            # Find booking by ID
            booking = Booking.objects.filter(booking_id=booking_id).first()

            if not booking:
                self.state = "collecting_booking_id_for_room_service"
                return f"I couldn't find a booking with ID {booking_id}. Please check your booking ID and try again."

            # Check if booking is active
            if booking.status == 'cancelled':
                self.state = "greeting"
                return f"This booking ({booking_id}) has been cancelled. Room service is not available for cancelled bookings."

            # Store booking for service request
            self.user_data['room_service_booking'] = {
                'id': booking.id,
                'booking_id': booking.booking_id,
                'guest_name': booking.guest_name,
                'room_name': booking.room.name
            }

            if service_type == 'cleaning':
                return self.handle_cleaning_request(booking, lang)
            elif service_type == 'dnd':
                return self.handle_dnd_request(booking, lang)
            else:
                return "I'm not sure what type of room service you need. Please specify if you need room cleaning or want to set Do Not Disturb."

        except Exception as e:
            logger.error(f"Error processing room service request: {str(e)}")
            return "Sorry, I encountered an error processing your room service request. Please try again."

    def handle_cleaning_request(self, booking, lang: str = 'en') -> str:
        """Handle room cleaning request."""
        try:
            self.state = "selecting_cleaning_time"
            return f"OK, we will arrange for the cleaner to clean your room as soon as possible.\nWhen would you like the cleaning service to be performed?\nA. Now\nB. After 2 pm\nC. Tomorrow morning"

        except Exception as e:
            logger.error(f"Error handling cleaning request: {str(e)}")
            return "Sorry, I encountered an error setting up your cleaning request. Please try again."

    def handle_cleaning_time_selection(self, user_input: str, lang: str = 'en') -> str:
        """Handle cleaning time slot selection."""
        try:
            user_input_lower = user_input.lower().strip()

            # Map user input to time slots
            time_slot_mapping = {
                'a': ('now', 'Now'),
                'now': ('now', 'Now'),
                'immediately': ('now', 'Now'),
                'b': ('after_2pm', 'After 2 PM'),
                'after 2pm': ('after_2pm', 'After 2 PM'),
                'after 2 pm': ('after_2pm', 'After 2 PM'),
                'afternoon': ('after_2pm', 'After 2 PM'),
                'c': ('tomorrow_morning', 'Tomorrow Morning'),
                'tomorrow': ('tomorrow_morning', 'Tomorrow Morning'),
                'tomorrow morning': ('tomorrow_morning', 'Tomorrow Morning'),
                'morning': ('tomorrow_morning', 'Tomorrow Morning')
            }

            # Find matching time slot
            selected_slot = None
            selected_display = None

            for key, (slot, display) in time_slot_mapping.items():
                if key in user_input_lower:
                    selected_slot = slot
                    selected_display = display
                    break

            if not selected_slot:
                return "Please select a valid option:\n**A.** Now\n**B.** After 2 PM\n**C.** Tomorrow morning\n\nType A, B, or C."

            # Create room service request
            booking_data = self.user_data.get('room_service_booking')
            if not booking_data:
                return "Sorry, I lost track of your booking information. Please start the room service request again."

            success = self.create_room_service_record('cleaning', booking_data['id'], cleaning_time_slot=selected_slot)

            # Reset state
            self.state = "greeting"
            self.user_data = {'is_returning_customer': True}

            if success:
                return f"Your request has been recorded. We will arrange for the cleaning staff to go to your room \"{selected_display.lower()}\". Thank you for your use!"
            else:
                return "Sorry, there was an error recording your cleaning request. Please contact the front desk for assistance."

        except Exception as e:
            logger.error(f"Error handling cleaning time selection: {str(e)}")
            return "Sorry, I encountered an error processing your time selection. Please try again."

    def handle_dnd_request(self, booking, lang: str = 'en') -> str:
        """Handle Do Not Disturb request."""
        try:
            # Create DND request
            success = self.create_room_service_record('dnd', booking.id, dnd_active=True)

            # Reset state
            self.state = "greeting"
            self.user_data = {'is_returning_customer': True}

            if success:
                return f"The \"Do Not Disturb\" status has been set for you. We will not disturb you for the time being, including cleaning services.\nPlease let me know if you need to resume service."
            else:
                return "Sorry, there was an error setting up Do Not Disturb. Please contact the front desk for assistance."

        except Exception as e:
            logger.error(f"Error handling DND request: {str(e)}")
            return "Sorry, I encountered an error setting up Do Not Disturb. Please try again."

    def create_room_service_record(self, service_type: str, booking_id: int, **kwargs) -> bool:
        """Create a room service request record in the database."""
        try:
            from hotel_booking.models import Booking, RoomServiceRequest
            from django.utils import timezone

            # Find the booking
            booking = Booking.objects.get(id=booking_id)

            # Create room service request
            service_data = {
                'booking': booking,
                'service_type': service_type,
                'status': 'pending'
            }

            # Add specific fields based on service type
            if service_type == 'cleaning':
                service_data['cleaning_time_slot'] = kwargs.get('cleaning_time_slot')
                service_data['special_instructions'] = kwargs.get('special_instructions', '')
            elif service_type == 'dnd':
                service_data['dnd_active'] = kwargs.get('dnd_active', True)
                service_data['dnd_start_time'] = timezone.now()

            room_service = RoomServiceRequest.objects.create(**service_data)
            logger.info(f"Room service request created: {room_service}")
            return True

        except Exception as e:
            logger.error(f"Error creating room service record: {str(e)}")
            return False

    def process(self, user_message: str, session_data: Optional[Dict] = None, user_history: Optional[List] = None) -> Tuple[str, Dict]:
        """
        Process user message and return response with updated session data.

        Args:
            user_message (str): User input message.
            session_data (Optional[Dict]): Existing session data.
            user_history (Optional[List]): User conversation history (unused).

        Returns:
            Tuple[str, Dict]: Response text and updated session data.
        """
        try:
            logger.info(f"Processing message: {user_message}")
            session_data = session_data or {}
            lang = session_data.get('lang', None)

            if session_data:
                if 'state' in session_data:
                    self.state = session_data['state']
                if 'user_data' in session_data:
                    self.user_data = session_data['user_data']

            response = self.respond(user_message, lang)
            session_data['state'] = self.state
            session_data['user_data'] = self.user_data
            session_data['lang'] = lang if lang else detect(user_message) if user_message else 'en'

            # 注释掉这里的确认逻辑，因为在views.py中已经处理了
            # 防止重复发送确认消息
            # if (self.state == "booking_confirmed" and
            #     'booking_id' in self.user_data and
            #     not self.user_data.get('confirmation_sent', False)):
            #
            #     booking_id = self.user_data['booking_id']
            #     confirmation_message = f"Great! Your booking has been confirmed. Your booking ID is: {booking_id}. You can use this ID to check your booking status or make changes.\n\nHere are your booking details:\n{self.format_booking_details(self.user_data)}\n\nIs there anything else I can help you with?"
            #
            #     # 标记确认消息已发送
            #     self.user_data['confirmation_sent'] = True
            #     session_data['user_data']['confirmation_sent'] = True
            #
            #     # 立即重置状态，防止重复发送
            #     self.state = 'greeting'
            #     session_data['state'] = 'greeting'
            #
            #     # 清理用户数据，但保留回头客标记
            #     self.user_data = {'is_returning_customer': True}
            #     session_data['user_data'] = {'is_returning_customer': True}
            #
            #     session_data['delayed_response'] = confirmation_message
            #     session_data['delay_time'] = 5

            logger.info(f"Dialog manager process completed - State: {self.state}, User data: {self.user_data}")

            return response, session_data
        except Exception as e:
            logger.error(f"Error in process method: {str(e)}")
            error_msg = "Sorry, I encountered an error. Please try again later." if lang == 'en' else "抱故，我遇到了一个错误。请稍后再试。"
            return error_msg, session_data or {}

if __name__ == "__main__":
    dialog_manager = DialogManager()
    session = {}
    test_cases = [
        ("Hello", None),
        ("I want to book a room", None),
        ("3 nights from May 25th, 2025", None),
        ("My name is John Doe", None),
        ("john@example.com", None),
        ("+123456789012", None),
        ("Deluxe room", None),
        ("This is terrible service", None),
        ("你好", None),
        ("我想预订房间", None),
        ("从2025年5月25日到5月30日", None),
        ("我的名字是张三", None),
        ("zhangsan@example.com", None),
        ("+987654321098", None),
        ("豪华房间", None),
        ("服务太差了", None),
        ("cancel my booking", None),
        ("BK-12345", None),
        ("upgrade my room to suite", None),
        ("change date to 30/05/2025", None),
        ("extend stay by 2 nights", None),
    ]
    for message, lang in test_cases:
        print(f"User ({lang or 'auto'}): {message}")
        response, session = dialog_manager.process(message, session)
        print(f"Bot: {response}\n")