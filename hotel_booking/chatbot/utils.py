import json
import pickle
import random
import numpy as np
import os
import re
from datetime import datetime, timedelta
import logging
import sys

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Check Python version
if sys.version_info < (3, 6):
    raise RuntimeError("Python 3.6 or higher is required")

# Check required packages
REQUIRED_PACKAGES = {
    'numpy': 'numpy',
    'nltk': 'nltk',
    'keras': 'keras',
    'tensorflow': 'tensorflow',
    'spacy': 'spacy',
    'transformers': 'transformers'
}

def check_dependencies():
    missing_packages = []
    for package, import_name in REQUIRED_PACKAGES.items():
        try:
            __import__(import_name)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        logger.error(f"Missing required packages: {', '.join(missing_packages)}")
        raise ImportError(f"Please install the following packages: {', '.join(missing_packages)}")

# Check dependencies at startup
try:
    check_dependencies()
except ImportError as e:
    logger.error(f"Dependency check failed: {e}")
    raise

# NLP Libraries
try:
    import nltk
    from nltk.stem import WordNetLemmatizer
    
    # Download necessary NLTK data
    try:
        nltk.data.find('tokenizers/punkt')
        nltk.data.find('corpora/wordnet')
    except LookupError:
        try:
            nltk.download('punkt')
            nltk.download('punkt_tab')
            nltk.download('wordnet')
        except Exception as e:
            logger.error(f"NLTK download error: {e}")
            raise
    
    lemmatizer = WordNetLemmatizer()
except ImportError as e:
    logger.error(f"NLTK import error: {e}")
    raise

# Deep Learning Libraries
try:
    from keras.models import Sequential, load_model
    from keras.layers import Dense, Dropout
    from keras.optimizers import SGD
    from keras.regularizers import l2
except ImportError as e:
    logger.error(f"Keras import error: {e}")
    raise

# Advanced NLP (optional)
ADVANCED_NLP = True  # 将False改为True
nlp = None
sentiment_analyzer = None
ner_pipeline = None

try:
    import spacy
    from transformers import pipeline
    
    try:
        # Try to load small spaCy model first
        nlp = spacy.load("en_core_web_sm")
    except Exception as e:
        logger.warning(f"Failed to load spaCy model: {e}")
        try:
            # Try to download and load the model
            import subprocess
            subprocess.run(["python", "-m", "spacy", "download", "en_core_web_sm"])
            nlp = spacy.load("en_core_web_sm")
        except Exception as e:
            logger.error(f"Failed to download and load spaCy model: {e}")
            nlp = None
    
    # Initialize sentiment analysis with explicit model
    try:
        sentiment_analyzer = pipeline(
            "sentiment-analysis",
            model="distilbert-base-uncased-finetuned-sst-2-english"
        )
    except Exception as e:
        logger.warning(f"Failed to load sentiment analyzer: {e}")
        sentiment_analyzer = None
    
    # Initialize NER with explicit model
    try:
        ner_pipeline = pipeline(
            "ner",
            model="dbmdz/bert-large-cased-finetuned-conll03-english"
        )
    except Exception as e:
        logger.warning(f"Failed to load NER pipeline: {e}")
        ner_pipeline = None
    
    # 在现有NLP初始化代码后添加
    # 添加问答功能
    try:
        qa_pipeline = pipeline(
            "question-answering",
            model="distilbert-base-cased-distilled-squad"
        )
    except Exception as e:
        logger.warning(f"Failed to load QA pipeline: {e}")
        qa_pipeline = None
    
    # 添加文本摘要功能
    try:
        summarizer = pipeline(
            "summarization",
            model="facebook/bart-large-cnn"
        )
    except Exception as e:
        logger.warning(f"Failed to load summarizer: {e}")
        summarizer = None
    
    # 更新ADVANCED_NLP条件
    if nlp and (sentiment_analyzer or ner_pipeline or qa_pipeline or summarizer):
        ADVANCED_NLP = True
        logger.info("Advanced NLP features enabled")
    else:
        logger.warning("Some NLP features are not available. Using basic features only.")
except ImportError:
    logger.warning("Advanced NLP libraries not available. Using basic features only.")

# Constants
MODEL_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'models')
INTENTS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'intents.json')
MODEL_FILE = os.path.join(MODEL_DIR, 'trained_model.h5')
DATA_FILE = os.path.join(MODEL_DIR, 'data.pkl')
IGNORE_LETTERS = ['?', '!', '.', ',']
ERROR_THRESHOLD = 0.25

# 对外暴露的NER函数
def ner(text):
    """Named Entity Recognition implementation for external use"""
    if not ADVANCED_NLP or not ner_pipeline:
        return []
    try:
        return ner_pipeline(text)
    except Exception as e:
        logger.error(f"NER processing failed: {e}")
        return []

class Chatbot:
    def __init__(self):
        self.model = None
        self.words = []
        self.classes = []
        self.intents = None
    
    def load_model(self):
        """加载训练好的模型和数据"""
        try:
            # 确保模型目录存在
            if not os.path.exists(MODEL_DIR):
                os.makedirs(MODEL_DIR)
                
            # 加载数据
            if os.path.exists(DATA_FILE):
                with open(DATA_FILE, 'rb') as file:
                    self.words, self.classes = pickle.load(file)
            else:
                logger.error(f"Data file not found: {DATA_FILE}")
                raise FileNotFoundError(f"Data file not found: {DATA_FILE}")
            
            # 加载模型
            if os.path.exists(MODEL_FILE):
                self.model = load_model(MODEL_FILE)
                logger.info(f"Model loaded: {self.model is not None}")
            else:
                logger.error(f"Model file not found: {MODEL_FILE}")
                raise FileNotFoundError(f"Model file not found: {MODEL_FILE}")
            
            # 加载意图
            if os.path.exists(INTENTS_FILE):
                with open(INTENTS_FILE, 'r', encoding='utf-8') as file:
                    self.intents = json.load(file)
            else:
                logger.error(f"Intents file not found: {INTENTS_FILE}")
                raise FileNotFoundError(f"Intents file not found: {INTENTS_FILE}")
                
            logger.info("Model loaded successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise
    
    def _clean_up_sentence(self, sentence):
        """清理和标记化句子"""
        sentence_words = nltk.word_tokenize(sentence)
        sentence_words = [lemmatizer.lemmatize(word.lower()) for word in sentence_words if word not in IGNORE_LETTERS]
        return sentence_words

    def _bag_of_words(self, sentence):
        """将句子转换为词袋向量"""
        sentence_words = self._clean_up_sentence(sentence)
        bag = [0] * len(self.words)
        for w in sentence_words:
            for i, word in enumerate(self.words):
                if word == w:
                    bag[i] = 1
        return np.array(bag)
    
    def predict_intent(self, text):
        """预测用户输入的意图"""
        bow = self._bag_of_words(text)
        res = self.model.predict(np.array([bow]))[0]
        results = [[i, r] for i, r in enumerate(res) if r > ERROR_THRESHOLD]
        results.sort(key=lambda x: x[1], reverse=True)
        
        if not results:
            return {'intent': 'fallback', 'probability': '1.0'}
        
        return {'intent': self.classes[results[0][0]], 'probability': str(results[0][1])}
    
    def get_response(self, intent_data):
        """根据意图获取响应"""
        tag = intent_data.get('intent', 'fallback')
        
        for intent in self.intents['intents']:
            if intent['tag'] == tag:
                return random.choice(intent['responses'])
        
        return "I'm not sure how to respond to that."

# 单例模式管理
_chatbot_instance = None

# 在get_chatbot函数中添加更详细的日志
def get_chatbot():
    """获取全局聊天机器人实例"""
    global _chatbot_instance
    if _chatbot_instance is None:
        logger.info("Creating new Chatbot instance")
        _chatbot_instance = Chatbot()
        try:
            logger.info("Loading chatbot model")
            _chatbot_instance.load_model()
            logger.info("Chatbot model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to initialize chatbot: {e}")
            import traceback
            logger.error(traceback.format_exc())
            raise
    if _chatbot_instance.model is None:
        logger.error("Chatbot model is still None after loading!")
    return _chatbot_instance

# 兼容性接口
def load_chatbot_model():
    """兼容旧版代码的加载函数"""
    chatbot = get_chatbot()
    return chatbot.model, chatbot.words, chatbot.classes

def predict_class(sentence, model, words, classes):
    """兼容旧版代码的预测函数"""
    chatbot = get_chatbot()
    bow = chatbot._bag_of_words(sentence)
    res = model.predict(np.array([bow]))[0]
    results = [[i, r] for i, r in enumerate(res) if r > ERROR_THRESHOLD]
    results.sort(key=lambda x: x[1], reverse=True)
    return [{'intent': classes[r[0]], 'probability': str(r[1])} for r in results]

def chatbot_response(text):
    """兼容旧版代码的响应函数"""
    chatbot = get_chatbot()
    intent = chatbot.predict_intent(text)
    return chatbot.get_response(intent)

# 对外暴露的NLP功能
def analyze_sentiment(text):
    """对外暴露的情感分析"""
    if not ADVANCED_NLP or not sentiment_analyzer:
        return {"label": "NEUTRAL", "score": 0.0}
    try:
        return sentiment_analyzer(text)[0]
    except Exception as e:
        logger.error(f"Sentiment analysis failed: {e}")
        return {"label": "ERROR", "score": 0.0}

def get_nlp():
    """获取spaCy NLP实例"""
    return nlp if ADVANCED_NLP else None

# 在文件末尾添加train_chatbot_model函数
def train_chatbot_model():
    """训练聊天机器人模型"""
    logger.info("开始训练聊天机器人模型")
    
    try:
        # 确保模型目录存在
        if not os.path.exists(MODEL_DIR):
            os.makedirs(MODEL_DIR)
        
        # 加载意图文件
        with open(INTENTS_FILE, 'r', encoding='utf-8') as file:
            intents = json.load(file)
        
        # 准备训练数据
        words = []
        classes = []
        documents = []
        
        # 遍历所有意图和模式
        for intent in intents['intents']:
            for pattern in intent['patterns']:
                # 标记化每个单词
                word_list = nltk.word_tokenize(pattern)
                words.extend(word_list)
                # 添加文档
                documents.append((word_list, intent['tag']))
                # 添加到类列表
                if intent['tag'] not in classes:
                    classes.append(intent['tag'])
        
        # 词形还原，转换为小写并删除重复项
        words = [lemmatizer.lemmatize(word.lower()) for word in words if word not in IGNORE_LETTERS]
        words = sorted(list(set(words)))
        classes = sorted(list(set(classes)))
        
        logger.info(f"唯一词汇数: {len(words)}")
        logger.info(f"意图类别数: {len(classes)}")
        logger.info(f"训练样本数: {len(documents)}")
        
        # 创建训练数据
        training = []
        output_empty = [0] * len(classes)
        
        for document in documents:
            bag = []
            word_patterns = document[0]
            word_patterns = [lemmatizer.lemmatize(word.lower()) for word in word_patterns]
            
            # 创建词袋数组
            for word in words:
                bag.append(1) if word in word_patterns else bag.append(0)
            
            # 创建输出行
            output_row = list(output_empty)
            output_row[classes.index(document[1])] = 1
            
            training.append([bag, output_row])
        
        # 打乱训练数据
        random.shuffle(training)
        training = np.array(training, dtype=object)
        
        # 分离特征和标签
        train_x = list(training[:, 0])
        train_y = list(training[:, 1])
        
        # 创建模型
        model = Sequential()
        model.add(Dense(128, input_shape=(len(train_x[0]),), activation='relu', kernel_regularizer=l2(0.01)))
        model.add(Dropout(0.5))
        model.add(Dense(64, activation='relu', kernel_regularizer=l2(0.01)))
        model.add(Dropout(0.5))
        model.add(Dense(len(train_y[0]), activation='softmax'))
        
        # 编译模型
        sgd = SGD(learning_rate=0.01, momentum=0.9, nesterov=True)
        model.compile(loss='categorical_crossentropy', optimizer=sgd, metrics=['accuracy'])
        
        # 训练模型
        logger.info("开始训练模型...")
        hist = model.fit(np.array(train_x), np.array(train_y), epochs=200, batch_size=5, verbose=1)
        logger.info(f"模型训练完成，最终准确率: {hist.history['accuracy'][-1]:.4f}")
        
        # 保存模型和数据
        model.save(MODEL_FILE)
        with open(DATA_FILE, 'wb') as file:
            pickle.dump((words, classes), file)
        
        logger.info(f"模型已保存到: {MODEL_FILE}")
        logger.info(f"数据已保存到: {DATA_FILE}")
        
        return True
    except Exception as e:
        logger.error(f"训练模型失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def answer_question(question, context):
    """问答功能"""
    if not ADVANCED_NLP or not qa_pipeline:
        return "I don't have enough information to answer that question."
    try:
        result = qa_pipeline(question=question, context=context)
        return result['answer']
    except Exception as e:
        logger.error(f"QA processing failed: {e}")
        return "Sorry, I couldn't process your question."

def summarize_text(text, max_length=100, min_length=30):
    """文本摘要功能"""
    if not ADVANCED_NLP or not summarizer:
        return text
    try:
        result = summarizer(text, max_length=max_length, min_length=min_length, do_sample=False)
        return result[0]['summary_text']
    except Exception as e:
        logger.error(f"Summarization failed: {e}")
        return text

# 在utils.py中添加安全的NLP处理函数
def safe_nlp_process(text, processor_func, default_return=None):
    """安全地处理NLP功能，确保即使失败也能返回合理的结果"""
    try:
        return processor_func(text)
    except Exception as e:
        logger.error(f"NLP processing failed: {e}")
        return default_return