"""
HiringReferrals Gamified Referral System

Advanced gamification system with tiered rewards, achievements,
leaderboards, and activity streaks functionality
"""

import os
import json
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Optional, Any
import logging

logger = logging.getLogger(__name__)

# Achievement types
class AchievementTypes:
    REFERRAL = 'referral'
    NETWORK = 'network'
    MENTOR = 'mentor'
    PLACEMENT = 'placement'
    PROFILE = 'profile'
    STREAK = 'streak'
    MILESTONE = 'milestone'

# Default achievement configuration
DEFAULT_ACHIEVEMENTS = [
    # Referral achievements
    {
        'id': 'first_referral',
        'name': 'First Connection',
        'description': 'Successfully refer your first candidate',
        'type': AchievementTypes.REFERRAL,
        'points': 100,
        'tier': 1,
        'icon': 'trophy_bronze'
    },
    {
        'id': 'referral_5',
        'name': 'Growing Network',
        'description': 'Successfully refer 5 candidates',
        'type': AchievementTypes.REFERRAL,
        'points': 250,
        'tier': 2,
        'icon': 'trophy_silver'
    },
    {
        'id': 'referral_10',
        'name': 'Referral Pro',
        'description': 'Successfully refer 10 candidates',
        'type': AchievementTypes.REFERRAL,
        'points': 500,
        'tier': 3,
        'icon': 'trophy_gold'
    },
    {
        'id': 'referral_25',
        'name': 'Referral Master',
        'description': 'Successfully refer 25 candidates',
        'type': AchievementTypes.REFERRAL,
        'points': 1000,
        'tier': 4,
        'icon': 'trophy_platinum'
    },
    # Mentor achievements
    {
        'id': 'first_mentorship',
        'name': 'Mentor Initiate',
        'description': 'Complete your first mentorship session',
        'type': AchievementTypes.MENTOR,
        'points': 150,
        'tier': 1,
        'icon': 'mentor_bronze'
    },
    # Placement achievements
    {
        'id': 'first_hire',
        'name': 'First Success',
        'description': 'Your first referral gets hired',
        'type': AchievementTypes.PLACEMENT,
        'points': 500,
        'tier': 2,
        'icon': 'hire_silver'
    },
    {
        'id': 'placement_5',
        'name': 'Talent Scout',
        'description': '5 of your referrals get hired',
        'type': AchievementTypes.PLACEMENT,
        'points': 1500,
        'tier': 3,
        'icon': 'hire_gold'
    },
    # Profile achievements
    {
        'id': 'profile_complete',
        'name': 'Identity Established',
        'description': 'Complete your profile with all details',
        'type': AchievementTypes.PROFILE,
        'points': 50,
        'tier': 1,
        'icon': 'profile_bronze'
    },
    # Streak achievements
    {
        'id': 'streak_week',
        'name': 'Weekly Streak',
        'description': 'Active for 7 days in a row',
        'type': AchievementTypes.STREAK,
        'points': 100,
        'tier': 1,
        'icon': 'streak_bronze',
        'renewable': True
    },
    {
        'id': 'streak_month',
        'name': 'Monthly Dedication',
        'description': 'Active for 30 days in a row',
        'type': AchievementTypes.STREAK,
        'points': 500,
        'tier': 3,
        'icon': 'streak_gold',
        'renewable': True
    },
    # Milestone achievements
    {
        'id': 'join_milestone',
        'name': 'New Journey',
        'description': 'Join the HiringReferrals platform',
        'type': AchievementTypes.MILESTONE,
        'points': 25,
        'tier': 1,
        'icon': 'milestone_bronze'
    },
]

# Reward tiers with enhanced benefits
DEFAULT_REWARD_TIERS = [
    {
        'id': 'tier1',
        'name': 'Bronze',
        'point_threshold': 0,
        'rewards': [
            {'id': 'profile_badge_bronze', 'name': 'Bronze Profile Badge', 'type': 'badge'}
        ]
    },
    {
        'id': 'tier2',
        'name': 'Silver',
        'point_threshold': 1000,
        'rewards': [
            {'id': 'profile_badge_silver', 'name': 'Silver Profile Badge', 'type': 'badge'},
            {'id': 'fee_discount_5', 'name': '5% Fee Discount', 'type': 'discount'}
        ]
    },
    {
        'id': 'tier3',
        'name': 'Gold',
        'point_threshold': 3000,
        'rewards': [
            {'id': 'profile_badge_gold', 'name': 'Gold Profile Badge', 'type': 'badge'},
            {'id': 'fee_discount_10', 'name': '10% Fee Discount', 'type': 'discount'},
            {'id': 'priority_support', 'name': 'Priority Support', 'type': 'service'}
        ]
    },
    {
        'id': 'tier4',
        'name': 'Platinum',
        'point_threshold': 7500,
        'rewards': [
            {'id': 'profile_badge_platinum', 'name': 'Platinum Profile Badge', 'type': 'badge'},
            {'id': 'fee_discount_15', 'name': '15% Fee Discount', 'type': 'discount'},
            {'id': 'priority_support', 'name': 'Priority Support', 'type': 'service'},
            {'id': 'early_access', 'name': 'Early Access to Features', 'type': 'feature'}
        ]
    },
    {
        'id': 'tier5',
        'name': 'Diamond',
        'point_threshold': 15000,
        'rewards': [
            {'id': 'profile_badge_diamond', 'name': 'Diamond Profile Badge', 'type': 'badge'},
            {'id': 'fee_discount_20', 'name': '20% Fee Discount', 'type': 'discount'},
            {'id': 'priority_support', 'name': 'Priority Support', 'type': 'service'},
            {'id': 'early_access', 'name': 'Early Access to Features', 'type': 'feature'},
            {'id': 'commission_boost_5', 'name': '5% Commission Boost', 'type': 'boost'}
        ]
    }
]

# Referral level definitions with commission rates
DEFAULT_REFERRAL_LEVELS = [
    {
        'id': 'level1',
        'name': 'Referral Associate',
        'min_referrals': 0,
        'commission_rate': 0.05,  # 5%
        'color': '#B87333',  # Bronze
        'icon': 'level1_icon'
    },
    {
        'id': 'level2',
        'name': 'Referral Specialist',
        'min_referrals': 5,
        'commission_rate': 0.075,  # 7.5%
        'color': '#C0C0C0',  # Silver
        'icon': 'level2_icon'
    },
    {
        'id': 'level3',
        'name': 'Referral Expert',
        'min_referrals': 10,
        'commission_rate': 0.1,  # 10%
        'color': '#FFD700',  # Gold
        'icon': 'level3_icon'
    },
    {
        'id': 'level4',
        'name': 'Referral Master',
        'min_referrals': 25,
        'commission_rate': 0.125,  # 12.5%
        'color': '#E5E4E2',  # Platinum
        'icon': 'level4_icon'
    },
    {
        'id': 'level5',
        'name': 'Referral Champion',
        'min_referrals': 50,
        'commission_rate': 0.15,  # 15%
        'color': '#B9F2FF',  # Diamond
        'icon': 'level5_icon'
    }
]

class GamificationService:
    def __init__(self, db):
        self.db = db
        
    async def initialize(self):
        """Initialize gamification data in database"""
        try:
            # Check if achievements exist
            count = await self.db.gamification_achievements.count_documents({})
            
            if count == 0:
                # Initialize with defaults
                await self.db.gamification_achievements.insert_many(DEFAULT_ACHIEVEMENTS)
                await self.db.gamification_tiers.insert_many(DEFAULT_REWARD_TIERS)
                await self.db.gamification_levels.insert_many(DEFAULT_REFERRAL_LEVELS)
                
                logger.info("Gamification system initialized with default data")
            
            return True
        except Exception as e:
            logger.error(f"Failed to initialize gamification: {e}")
            return False
    
    async def get_all_achievements(self):
        """Get all available achievements"""
        achievements = await self.db.gamification_achievements.find({}, {"_id": 0}).to_list(100)
        return achievements
    
    async def get_user_achievements(self, user_id: str):
        """Get achievements earned by user"""
        achievements = await self.db.user_achievements.find(
            {"user_id": user_id},
            {"_id": 0}
        ).to_list(100)
        return achievements
    
    async def get_user_points(self, user_id: str):
        """Get user's gamification points and tier"""
        user_data = await self.db.user_gamification.find_one(
            {"user_id": user_id},
            {"_id": 0}
        )
        
        if not user_data:
            # Initialize new user
            user_data = {
                "user_id": user_id,
                "total_points": 0,
                "current_tier": "tier1",
                "current_level": "level1",
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            await self.db.user_gamification.insert_one(user_data)
            user_data.pop("_id", None)
        
        # Get tier and level info
        tier = await self.db.gamification_tiers.find_one({"id": user_data["current_tier"]}, {"_id": 0})
        level = await self.db.gamification_levels.find_one({"id": user_data["current_level"]}, {"_id": 0})
        
        # Find next tier
        next_tier = await self.db.gamification_tiers.find_one(
            {"point_threshold": {"$gt": user_data["total_points"]}},
            {"_id": 0}
        )
        
        return {
            "user_id": user_id,
            "total_points": user_data["total_points"],
            "current_tier": tier,
            "current_level": level,
            "next_tier": next_tier
        }
    
    async def get_user_streak(self, user_id: str):
        """Get user's activity streak"""
        streak = await self.db.user_streaks.find_one(
            {"user_id": user_id},
            {"_id": 0}
        )
        
        if not streak:
            # Initialize new streak
            today = datetime.now(timezone.utc).date().isoformat()
            streak = {
                "user_id": user_id,
                "current_streak": 1,
                "max_streak": 1,
                "last_active_date": today,
                "streak_freeze_available": False
            }
            await self.db.user_streaks.insert_one(streak)
            streak.pop("_id", None)
        
        return streak
    
    async def update_user_streak(self, user_id: str):
        """Update user's activity streak"""
        today = datetime.now(timezone.utc).date()
        streak_data = await self.get_user_streak(user_id)
        
        last_active = datetime.fromisoformat(streak_data["last_active_date"]).date()
        day_diff = (today - last_active).days
        
        if day_diff == 0:
            return {**streak_data, "updated": False, "message": "Already updated today"}
        
        current_streak = streak_data["current_streak"]
        max_streak = streak_data["max_streak"]
        freeze_available = streak_data["streak_freeze_available"]
        
        if day_diff == 1:
            # Consecutive day
            current_streak += 1
            if current_streak % 14 == 0:
                freeze_available = True
        elif day_diff == 2 and freeze_available:
            # Use streak freeze
            freeze_available = False
        else:
            # Streak broken
            current_streak = 1
        
        # Update max streak
        if current_streak > max_streak:
            max_streak = current_streak
        
        # Update database
        await self.db.user_streaks.update_one(
            {"user_id": user_id},
            {"$set": {
                "current_streak": current_streak,
                "max_streak": max_streak,
                "last_active_date": today.isoformat(),
                "streak_freeze_available": freeze_available
            }}
        )
        
        # Check for streak achievements
        if current_streak >= 7 and current_streak % 7 == 0:
            await self.award_achievement(user_id, "streak_week")
        
        if current_streak >= 30 and current_streak % 30 == 0:
            await self.award_achievement(user_id, "streak_month")
        
        return {
            "user_id": user_id,
            "current_streak": current_streak,
            "max_streak": max_streak,
            "last_active_date": today.isoformat(),
            "streak_freeze_available": freeze_available,
            "updated": True
        }
    
    async def award_achievement(self, user_id: str, achievement_id: str):
        """Award an achievement to a user"""
        # Get achievement details
        achievement = await self.db.gamification_achievements.find_one(
            {"id": achievement_id},
            {"_id": 0}
        )
        
        if not achievement:
            return {"success": False, "error": "Achievement not found"}
        
        # Check if already awarded (unless renewable)
        existing = await self.db.user_achievements.find_one({
            "user_id": user_id,
            "achievement_id": achievement_id
        })
        
        if existing and not achievement.get("renewable", False):
            return {"success": False, "reason": "already_awarded"}
        
        # Award achievement
        points = achievement["points"]
        now = datetime.now(timezone.utc).isoformat()
        
        if achievement.get("renewable") and existing:
            # Update existing
            await self.db.user_achievements.update_one(
                {"user_id": user_id, "achievement_id": achievement_id},
                {"$set": {"achieved_at": now, "points": points}}
            )
        else:
            # Insert new
            await self.db.user_achievements.insert_one({
                "user_id": user_id,
                "achievement_id": achievement_id,
                "achieved_at": now,
                "points": points
            })
        
        # Update user points and check for tier/level progression
        user_data = await self.get_user_points(user_id)
        new_total = user_data["total_points"] + points
        
        # Find new tier
        tiers = await self.db.gamification_tiers.find({}, {"_id": 0}).sort("point_threshold", -1).to_list(10)
        new_tier = tiers[-1]["id"]
        for tier in tiers:
            if new_total >= tier["point_threshold"]:
                new_tier = tier["id"]
                break
        
        # Update user gamification data
        await self.db.user_gamification.update_one(
            {"user_id": user_id},
            {"$set": {
                "total_points": new_total,
                "current_tier": new_tier
            }}
        )
        
        return {
            "success": True,
            "achievement": achievement,
            "points_awarded": points,
            "total_points": new_total
        }
    
    async def get_leaderboard(self, limit: int = 10):
        """Get top users by points"""
        pipeline = [
            {"$lookup": {
                "from": "users",
                "localField": "user_id",
                "foreignField": "id",
                "as": "user"
            }},
            {"$unwind": "$user"},
            {"$sort": {"total_points": -1}},
            {"$limit": limit},
            {"$project": {
                "_id": 0,
                "user_id": 1,
                "total_points": 1,
                "current_tier": 1,
                "current_level": 1,
                "username": "$user.full_name",
                "email": "$user.email"
            }}
        ]
        
        leaderboard = await self.db.user_gamification.aggregate(pipeline).to_list(limit)
        
        # Add ranks
        for idx, entry in enumerate(leaderboard):
            entry["rank"] = idx + 1
        
        return leaderboard
    
    async def calculate_commission(self, user_id: str, base_amount: float):
        """Calculate commission based on user level"""
        user_data = await self.get_user_points(user_id)
        level = user_data["current_level"]
        
        commission_rate = level.get("commission_rate", 0.05)
        commission = base_amount * commission_rate
        
        return {
            "user_id": user_id,
            "base_amount": base_amount,
            "commission_rate": commission_rate,
            "commission": commission,
            "level_name": level.get("name", "Unknown")
        }
    
    async def get_user_stats(self, user_id: str):
        """Get comprehensive stats for a user"""
        points = await self.get_user_points(user_id)
        streak = await self.get_user_streak(user_id)
        achievements = await self.get_user_achievements(user_id)
        
        return {
            "user_id": user_id,
            "points": points,
            "streak": streak,
            "achievements": {
                "total": len(achievements),
                "recent": achievements[:5] if len(achievements) > 5 else achievements
            }
        }
