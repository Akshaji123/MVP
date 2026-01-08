"""
Enhanced Commission Calculation Engine
HiringReferrals Platform

Multi-tier commission rates based on:
- Annual package level
- User tier multipliers (Bronze → Diamond)
- TDS deductions
- Platform fees
"""

from typing import Dict, Any, Optional
from datetime import datetime, timezone
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class PackageLevel(Enum):
    """Package level tiers based on annual salary"""
    ENTRY = "entry"           # ₹0-3L
    JUNIOR = "junior"         # ₹3-6L
    MID_LEVEL = "mid_level"   # ₹6-12L
    SENIOR = "senior"         # ₹12-20L
    LEADERSHIP = "leadership" # ₹20-35L
    EXECUTIVE = "executive"   # ₹35L+


class UserTier(Enum):
    """User tier based on successful placements"""
    BRONZE = "bronze"       # 0-5 placements
    SILVER = "silver"       # 6-15 placements
    GOLD = "gold"           # 16-30 placements
    PLATINUM = "platinum"   # 31-50 placements
    DIAMOND = "diamond"     # 50+ placements


# Commission rates by package level (percentage of annual package)
PACKAGE_COMMISSION_RATES = {
    PackageLevel.ENTRY: 0.06,       # 6%
    PackageLevel.JUNIOR: 0.08,      # 8%
    PackageLevel.MID_LEVEL: 0.10,   # 10%
    PackageLevel.SENIOR: 0.12,      # 12%
    PackageLevel.LEADERSHIP: 0.15,  # 15%
    PackageLevel.EXECUTIVE: 0.18,   # 18%
}

# User tier multipliers
USER_TIER_MULTIPLIERS = {
    UserTier.BRONZE: 1.0,
    UserTier.SILVER: 1.1,
    UserTier.GOLD: 1.25,
    UserTier.PLATINUM: 1.5,
    UserTier.DIAMOND: 1.75,
}

# Tier thresholds (number of successful placements)
TIER_THRESHOLDS = {
    UserTier.BRONZE: 0,
    UserTier.SILVER: 6,
    UserTier.GOLD: 16,
    UserTier.PLATINUM: 31,
    UserTier.DIAMOND: 51,
}

# Tax and fee rates
TDS_RATE = 0.10  # 10% TDS if commission > ₹30,000
TDS_THRESHOLD = 30000  # TDS applicable if gross > ₹30,000
PLATFORM_FEE_RATE = 0.05  # 5% platform fee (can be 5-8%)


class CommissionCalculator:
    """
    Commission calculation service with multi-tier rates,
    user multipliers, and tax deductions.
    """
    
    def __init__(self, db):
        self.db = db
    
    def get_package_level(self, annual_package: float) -> PackageLevel:
        """Determine package level based on annual salary"""
        if annual_package <= 300000:  # ₹0-3L
            return PackageLevel.ENTRY
        elif annual_package <= 600000:  # ₹3-6L
            return PackageLevel.JUNIOR
        elif annual_package <= 1200000:  # ₹6-12L
            return PackageLevel.MID_LEVEL
        elif annual_package <= 2000000:  # ₹12-20L
            return PackageLevel.SENIOR
        elif annual_package <= 3500000:  # ₹20-35L
            return PackageLevel.LEADERSHIP
        else:  # ₹35L+
            return PackageLevel.EXECUTIVE
    
    async def get_user_tier(self, user_id: str) -> UserTier:
        """Get user tier based on successful placements"""
        # Count successful placements
        placement_count = await self.db.applications.count_documents({
            "$or": [
                {"recruiter_id": user_id, "status": "hired"},
                {"referrer_id": user_id, "status": "hired"}
            ]
        })
        
        # Determine tier
        if placement_count >= TIER_THRESHOLDS[UserTier.DIAMOND]:
            return UserTier.DIAMOND
        elif placement_count >= TIER_THRESHOLDS[UserTier.PLATINUM]:
            return UserTier.PLATINUM
        elif placement_count >= TIER_THRESHOLDS[UserTier.GOLD]:
            return UserTier.GOLD
        elif placement_count >= TIER_THRESHOLDS[UserTier.SILVER]:
            return UserTier.SILVER
        else:
            return UserTier.BRONZE
    
    def calculate_tds(self, gross_amount: float) -> float:
        """Calculate TDS deduction"""
        if gross_amount > TDS_THRESHOLD:
            return gross_amount * TDS_RATE
        return 0.0
    
    def calculate_platform_fee(self, gross_amount: float, fee_rate: float = PLATFORM_FEE_RATE) -> float:
        """Calculate platform fee"""
        return gross_amount * fee_rate
    
    async def calculate_commission(
        self,
        user_id: str,
        annual_package: float,
        currency: str = "INR",
        custom_rate: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Calculate full commission breakdown
        
        Args:
            user_id: The recruiter/referrer ID
            annual_package: Candidate's annual package in INR
            currency: Currency code (INR/USD)
            custom_rate: Optional custom commission rate override
        
        Returns:
            Complete commission breakdown with all deductions
        """
        # Get package level
        package_level = self.get_package_level(annual_package)
        base_rate = PACKAGE_COMMISSION_RATES[package_level]
        
        # Get user tier and multiplier
        user_tier = await self.get_user_tier(user_id)
        tier_multiplier = USER_TIER_MULTIPLIERS[user_tier]
        
        # Calculate effective rate
        if custom_rate:
            effective_rate = custom_rate * tier_multiplier
        else:
            effective_rate = base_rate * tier_multiplier
        
        # Calculate amounts
        gross_commission = annual_package * effective_rate
        
        # Calculate deductions
        tds_amount = self.calculate_tds(gross_commission)
        platform_fee = self.calculate_platform_fee(gross_commission)
        
        # Calculate net commission
        net_commission = gross_commission - tds_amount - platform_fee
        
        # Currency conversion if needed
        exchange_rate = 1.0
        if currency == "USD":
            exchange_rate = 0.012  # 1 INR = 0.012 USD
        
        result = {
            "user_id": user_id,
            "annual_package": annual_package,
            "currency": currency,
            "package_level": package_level.value,
            "user_tier": user_tier.value,
            "calculation_details": {
                "base_commission_rate": base_rate,
                "tier_multiplier": tier_multiplier,
                "effective_rate": effective_rate,
                "gross_commission": round(gross_commission, 2),
                "tds_rate": TDS_RATE if gross_commission > TDS_THRESHOLD else 0,
                "tds_amount": round(tds_amount, 2),
                "platform_fee_rate": PLATFORM_FEE_RATE,
                "platform_fee": round(platform_fee, 2),
                "net_commission": round(net_commission, 2),
            },
            "converted_amounts": {
                "currency": currency,
                "exchange_rate": exchange_rate,
                "gross_commission": round(gross_commission * exchange_rate, 2),
                "net_commission": round(net_commission * exchange_rate, 2),
            },
            "calculated_at": datetime.now(timezone.utc).isoformat()
        }
        
        return result
    
    async def calculate_batch_commissions(
        self,
        user_id: str,
        placements: list[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Calculate commissions for multiple placements
        
        Args:
            user_id: The recruiter/referrer ID
            placements: List of placement details with annual_package
        
        Returns:
            Summary of all commissions
        """
        total_gross = 0.0
        total_tds = 0.0
        total_platform_fee = 0.0
        total_net = 0.0
        breakdown = []
        
        for placement in placements:
            result = await self.calculate_commission(
                user_id=user_id,
                annual_package=placement.get("annual_package", 0),
                currency=placement.get("currency", "INR")
            )
            
            details = result["calculation_details"]
            total_gross += details["gross_commission"]
            total_tds += details["tds_amount"]
            total_platform_fee += details["platform_fee"]
            total_net += details["net_commission"]
            
            breakdown.append({
                "placement_id": placement.get("id"),
                "candidate_name": placement.get("candidate_name"),
                "annual_package": placement.get("annual_package"),
                "gross_commission": details["gross_commission"],
                "net_commission": details["net_commission"]
            })
        
        return {
            "user_id": user_id,
            "total_placements": len(placements),
            "totals": {
                "gross_commission": round(total_gross, 2),
                "tds_amount": round(total_tds, 2),
                "platform_fee": round(total_platform_fee, 2),
                "net_commission": round(total_net, 2)
            },
            "breakdown": breakdown,
            "calculated_at": datetime.now(timezone.utc).isoformat()
        }
    
    async def get_commission_summary(self, user_id: str) -> Dict[str, Any]:
        """Get commission summary for a user including tier info"""
        user_tier = await self.get_user_tier(user_id)
        multiplier = USER_TIER_MULTIPLIERS[user_tier]
        
        # Get placement count
        placement_count = await self.db.applications.count_documents({
            "$or": [
                {"recruiter_id": user_id, "status": "hired"},
                {"referrer_id": user_id, "status": "hired"}
            ]
        })
        
        # Calculate next tier threshold
        tier_order = list(UserTier)
        current_idx = tier_order.index(user_tier)
        next_tier = tier_order[current_idx + 1] if current_idx < len(tier_order) - 1 else None
        placements_to_next = TIER_THRESHOLDS.get(next_tier, 0) - placement_count if next_tier else 0
        
        return {
            "user_id": user_id,
            "current_tier": user_tier.value,
            "tier_multiplier": multiplier,
            "total_placements": placement_count,
            "commission_rates": {
                level.value: f"{rate * 100 * multiplier:.1f}%"
                for level, rate in PACKAGE_COMMISSION_RATES.items()
            },
            "next_tier": next_tier.value if next_tier else None,
            "placements_to_next_tier": max(0, placements_to_next),
            "benefits": {
                "tds_threshold": TDS_THRESHOLD,
                "platform_fee_rate": f"{PLATFORM_FEE_RATE * 100}%"
            }
        }


# Singleton instance creator
def create_commission_calculator(db) -> CommissionCalculator:
    return CommissionCalculator(db)
