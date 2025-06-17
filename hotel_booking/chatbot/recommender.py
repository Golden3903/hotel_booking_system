# 新建推荐系统模块
class RoomRecommender:
    def __init__(self):
        self.room_features = self._load_room_features()
    
    def _load_room_features(self):
        # 从数据库加载房间特征
        rooms = Room.objects.all()
        features = {}
        for room in rooms:
            features[room.id] = {
                "type": room.name,
                "price": room.price,
                "size": room.size,
                "view": room.has_view,
                "amenities": room.amenities.split(","),
                # 其他特征
            }
        return features
    
    def recommend(self, user_preferences, booking_history=None):
        """基于用户偏好和历史记录推荐房间"""
        scores = {}
        
        # 分析用户偏好
        for room_id, features in self.room_features.items():
            score = self._calculate_match_score(features, user_preferences)
            scores[room_id] = score
        
        # 如果有历史记录，考虑历史偏好
        if booking_history:
            for room_id, features in self.room_features.items():
                history_score = self._calculate_history_score(features, booking_history)
                scores[room_id] += history_score
        
        # 返回排序后的推荐结果
        recommended_rooms = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return recommended_rooms
    
    def _calculate_match_score(self, features, preferences):
        # 计算房间特征与用户偏好的匹配度
        score = 0
        
        # 如果没有偏好，返回基本分数
        if not preferences:
            return score
        
        # 检查房间类型匹配
        if 'room_type' in preferences and features['type'].lower() == preferences['room_type'].lower():
            score += 10
        
        # 检查视图偏好
        if preferences.get('view') and features.get('view'):
            score += 5
        
        # 检查其他偏好
        if preferences.get('balcony') and 'balcony' in features.get('amenities', []):
            score += 3
        
        if preferences.get('quiet') and features.get('quiet', False):
            score += 3
        
        if preferences.get('high_floor') and features.get('floor', 0) > 3:
            score += 3
        
        return score
    
    def _calculate_history_score(self, features, history):
        # 基于历史记录计算偏好分数
        # 简单实现，实际应用中可能需要更复杂的逻辑
        return 0  # 暂时返回0，表示不考虑历史记录

# 在文件顶部添加
from ..models import Room