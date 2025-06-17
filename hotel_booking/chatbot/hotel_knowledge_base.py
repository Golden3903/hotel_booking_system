# Hotel Knowledge Base for Advanced NLP Chatbot
# 酒店知识库 - 为聊天机器人提供专业的酒店信息

import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class HotelKnowledgeBase:
    """
    Comprehensive hotel knowledge base for providing detailed information
    about hotel services, amenities, policies, and local attractions.
    """

    def __init__(self):
        self.hotel_info = {
            "name": "Grand Luxury Hotel",
            "location": {
                "address": "123 Hotel Street, City Center",
                "city": "Kuala Lumpur",
                "country": "Malaysia",
                "coordinates": {"lat": 3.1390, "lng": 101.6869},
                "nearby_landmarks": [
                    {"name": "KLCC Twin Towers", "distance": "2.5 km", "transport_time": "10 minutes by car"},
                    {"name": "Bukit Bintang Shopping District", "distance": "1.8 km", "transport_time": "8 minutes by car"},
                    {"name": "KL Sentral Station", "distance": "5.2 km", "transport_time": "15 minutes by car"},
                    {"name": "KLIA Airport", "distance": "45 km", "transport_time": "45 minutes by car"}
                ]
            },
            "contact": {
                "phone": "+60 3-1234-5678",
                "email": "reservations@grandluxuryhotel.com",
                "website": "www.grandluxuryhotel.com",
                "emergency": "+60 3-1234-5679"
            }
        }

        self.room_types = {
            "standard": {
                "name": "Standard Room",
                "size": "28 sqm",
                "capacity": "2 adults",
                "bed_type": "Queen bed or Twin beds",
                "price_range": "RM 132 per night",
                "amenities": [
                    "Free WiFi", "Air conditioning", "32-inch LED TV", "Mini-bar",
                    "Coffee/tea maker", "Safe deposit box", "Hair dryer", "Bathroom amenities"
                ],
                "view": "City view",
                "description": "Comfortable and well-appointed rooms perfect for business or leisure travelers."
            },
            "deluxe": {
                "name": "Deluxe Room",
                "size": "35 sqm",
                "capacity": "2 adults + 1 child",
                "bed_type": "King bed or Twin beds",
                "price_range": "RM 205 per night",
                "amenities": [
                    "Free WiFi", "Air conditioning", "42-inch LED TV", "Mini-bar",
                    "Coffee/tea maker", "Safe deposit box", "Hair dryer", "Bathroom amenities",
                    "Work desk", "Seating area", "Balcony", "Bathtub"
                ],
                "view": "City or partial sea view",
                "description": "Spacious rooms with enhanced amenities and stunning views, ideal for extended stays."
            },
            "suite": {
                "name": "Executive Suite",
                "size": "55 sqm",
                "capacity": "4 adults + 2 children",
                "bed_type": "King bed + Sofa bed",
                "price_range": "RM 321 per night",
                "amenities": [
                    "Free WiFi", "Air conditioning", "55-inch LED TV", "Mini-bar",
                    "Coffee/tea maker", "Safe deposit box", "Hair dryer", "Bathroom amenities",
                    "Separate living area", "Dining table", "Kitchenette", "Jacuzzi",
                    "Premium toiletries", "Complimentary fruit basket", "Butler service"
                ],
                "view": "Premium city or sea view",
                "description": "Luxurious suites with separate living areas, perfect for families or VIP guests."
            }
        }

        self.hotel_amenities = {
            "dining": {
                "main_restaurant": {
                    "name": "The Grand Dining",
                    "cuisine": "International buffet and à la carte",
                    "hours": "6:00 AM - 11:00 PM",
                    "specialties": ["Malaysian cuisine", "Western dishes", "Asian fusion"],
                    "dress_code": "Smart casual"
                },
                "cafe": {
                    "name": "Lobby Café",
                    "cuisine": "Light meals, coffee, pastries",
                    "hours": "24 hours",
                    "specialties": ["Artisan coffee", "Fresh pastries", "Light snacks"]
                },
                "room_service": {
                    "availability": "24 hours",
                    "menu": "Full dining menu available",
                    "delivery_time": "30-45 minutes"
                }
            },
            "recreation": {
                "swimming_pool": {
                    "type": "Outdoor infinity pool",
                    "hours": "6:00 AM - 10:00 PM",
                    "features": ["Pool bar", "Jacuzzi", "Children's pool", "Poolside service"]
                },
                "fitness_center": {
                    "hours": "24 hours",
                    "equipment": ["Cardio machines", "Weight training", "Yoga mats"],
                    "services": ["Personal trainer available", "Group fitness classes"]
                },
                "spa": {
                    "name": "Serenity Spa",
                    "hours": "9:00 AM - 9:00 PM",
                    "services": ["Massage therapy", "Facial treatments", "Body treatments", "Couples packages"]
                }
            },
            "business": {
                "business_center": {
                    "hours": "24 hours",
                    "services": ["Printing", "Fax", "Internet access", "Meeting rooms"]
                },
                "meeting_rooms": {
                    "capacity": "10-200 people",
                    "equipment": ["Projectors", "Audio systems", "Video conferencing"],
                    "catering": "Available upon request"
                }
            }
        }

        self.policies = {
            "check_in_out": {
                "check_in": "3:00 PM",
                "check_out": "11:00 AM",
                "early_check_in": "Available from 12:00 PM (subject to availability)",
                "late_check_out": "Available until 2:00 PM (additional charges may apply)"
            },
            "cancellation": {
                "free_cancellation": "Up to 24 hours before arrival",
                "late_cancellation": "Fee equivalent to one night's stay",
                "no_show": "Full booking amount charged"
            },
            "payment": {
                "accepted_methods": ["Credit cards", "Debit cards", "Cash", "Bank transfer"],
                "deposit": "Credit card required to guarantee booking",
                "currency": "Malaysian Ringgit (RM)"
            },
            "pets": {
                "allowed": True,
                "fee": "RM 50 per night per pet",
                "restrictions": "Maximum 2 pets per room, weight limit 15kg each"
            },
            "smoking": {
                "policy": "Non-smoking hotel",
                "designated_areas": "Outdoor terrace and pool area",
                "violation_fee": "RM 500 cleaning fee"
            }
        }

    def get_room_info(self, room_type: str = None) -> Dict[str, Any]:
        """Get detailed information about room types."""
        if room_type:
            room_type = room_type.lower()
            return self.room_types.get(room_type, {})
        return self.room_types

    def get_amenity_info(self, category: str = None) -> Dict[str, Any]:
        """Get information about hotel amenities."""
        if category:
            return self.hotel_amenities.get(category, {})
        return self.hotel_amenities

    def get_policy_info(self, policy_type: str = None) -> Dict[str, Any]:
        """Get information about hotel policies."""
        if policy_type:
            return self.policies.get(policy_type, {})
        return self.policies

    def get_location_info(self) -> Dict[str, Any]:
        """Get hotel location and nearby attractions."""
        return self.hotel_info["location"]

    def search_information(self, query: str) -> List[Dict[str, Any]]:
        """
        Search for information based on user query.
        Returns relevant information from the knowledge base.
        """
        query = query.lower()
        results = []

        # Search in room information
        for room_type, info in self.room_types.items():
            if any(keyword in query for keyword in [room_type, info["name"].lower()]):
                results.append({
                    "category": "room",
                    "type": room_type,
                    "info": info
                })

        # Search in amenities
        for category, amenities in self.hotel_amenities.items():
            if category in query:
                results.append({
                    "category": "amenity",
                    "type": category,
                    "info": amenities
                })

        # Search in policies
        for policy_type, policy_info in self.policies.items():
            if policy_type.replace("_", " ") in query or any(keyword in query for keyword in policy_type.split("_")):
                results.append({
                    "category": "policy",
                    "type": policy_type,
                    "info": policy_info
                })

        return results

    def get_recommendations(self, user_preferences: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Provide room recommendations based on user preferences.
        """
        recommendations = []

        # Analyze preferences
        budget = user_preferences.get("budget", "medium")
        group_size = user_preferences.get("group_size", 2)
        purpose = user_preferences.get("purpose", "leisure")

        # Recommend based on group size
        if group_size <= 2:
            if budget == "low":
                recommendations.append(self.room_types["standard"])
            elif budget == "high":
                recommendations.append(self.room_types["suite"])
            else:
                recommendations.append(self.room_types["deluxe"])
        else:
            recommendations.append(self.room_types["suite"])

        return recommendations
