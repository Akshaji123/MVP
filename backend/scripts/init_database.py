"""
Database Initialization and Migration Script
HiringReferrals Platform

This script:
1. Creates all required collections
2. Sets up indexes for optimal performance
3. Seeds initial data (roles, email templates)
4. Migrates existing data to new schema structure
"""

import asyncio
import os
import sys
from datetime import datetime, timezone
from typing import Dict, Any, List
import uuid

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

# MongoDB connection
MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.environ.get("DB_NAME", "test_database")


# =====================================================
# INDEX DEFINITIONS
# =====================================================

INDEXES = {
    # Core indexes
    "users": [
        {"keys": [("email", 1)], "unique": True},
        {"keys": [("phone", 1)], "unique": True, "sparse": True},
        {"keys": [("is_active", 1), ("is_verified", 1)]},
        {"keys": [("created_at", -1)]}
    ],
    "roles": [
        {"keys": [("name", 1)], "unique": True}
    ],
    "user_roles": [
        {"keys": [("user_id", 1), ("role_id", 1)], "unique": True},
        {"keys": [("user_id", 1), ("is_active", 1)]}
    ],
    "user_profiles": [
        {"keys": [("user_id", 1)], "unique": True},
        {"keys": [("profile_type", 1)]},
        {"keys": [("company_id", 1)]}
    ],
    "user_sessions": [
        {"keys": [("session_token", 1)], "unique": True},
        {"keys": [("user_id", 1), ("is_active", 1)]},
        {"keys": [("expires_at", 1)]}
    ],
    
    # Business indexes
    "companies": [
        {"keys": [("name", 1)]},
        {"keys": [("is_active", 1)]},
        {"keys": [("industry", 1)]}
    ],
    "jobs": [
        {"keys": [("company_id", 1), ("job_status", 1)]},
        {"keys": [("job_status", 1), ("posted_at", -1)]},
        {"keys": [("location", "text"), ("title", "text"), ("description", "text")]},
        {"keys": [("skills_required", 1)]},
        {"keys": [("experience_level", 1)]},
        {"keys": [("salary_min", 1), ("salary_max", 1)]},
        {"keys": [("created_at", -1)]}
    ],
    "candidates": [
        {"keys": [("user_id", 1)], "unique": True},
        {"keys": [("skills", 1)]},
        {"keys": [("experience_years", 1)]},
        {"keys": [("availability", 1)]},
        {"keys": [("is_available_for_referral", 1)]}
    ],
    "applications": [
        {"keys": [("job_id", 1), ("candidate_id", 1)], "unique": True},
        {"keys": [("job_id", 1), ("application_status", 1)]},
        {"keys": [("candidate_id", 1), ("applied_at", -1)]},
        {"keys": [("recruiter_id", 1)]},
        {"keys": [("application_status", 1)]},
        {"keys": [("screening_score", -1)]}
    ],
    "referrals": [
        {"keys": [("referrer_id", 1), ("referral_status", 1)]},
        {"keys": [("job_id", 1)]},
        {"keys": [("candidate_email", 1)]},
        {"keys": [("is_hired", 1), ("commission_paid", 1)]}
    ],
    "background_verifications": [
        {"keys": [("candidate_id", 1)]},
        {"keys": [("application_id", 1)]},
        {"keys": [("verification_status", 1)]},
        {"keys": [("requested_at", -1)]}
    ],
    "interviews": [
        {"keys": [("application_id", 1)]},
        {"keys": [("candidate_id", 1)]},
        {"keys": [("scheduled_at", 1)]},
        {"keys": [("interview_status", 1)]}
    ],
    "assessments": [
        {"keys": [("candidate_id", 1)]},
        {"keys": [("job_id", 1)]},
        {"keys": [("assessment_status", 1)]}
    ],
    
    # Financial indexes
    "commissions": [
        {"keys": [("referral_id", 1)]},
        {"keys": [("user_id", 1), ("commission_status", 1)]},
        {"keys": [("earned_date", -1)]},
        {"keys": [("payment_due_date", 1)]}
    ],
    "payments": [
        {"keys": [("gateway_transaction_id", 1)]},
        {"keys": [("payee_id", 1), ("payment_status", 1)]},
        {"keys": [("payment_date", -1)]},
        {"keys": [("related_entity_type", 1), ("related_entity_id", 1)]}
    ],
    "invoices": [
        {"keys": [("invoice_number", 1)], "unique": True},
        {"keys": [("company_id", 1)]},
        {"keys": [("invoice_status", 1)]},
        {"keys": [("due_date", 1)]}
    ],
    "payout_requests": [
        {"keys": [("user_id", 1), ("request_status", 1)]},
        {"keys": [("created_at", -1)]}
    ],
    
    # Communication indexes
    "messages": [
        {"keys": [("recipient_id", 1), ("is_read", 1)]},
        {"keys": [("sender_id", 1)]},
        {"keys": [("created_at", -1)]}
    ],
    "notifications": [
        {"keys": [("user_id", 1), ("is_read", 1)]},
        {"keys": [("notification_type", 1)]},
        {"keys": [("created_at", -1)]}
    ],
    "email_templates": [
        {"keys": [("template_name", 1)], "unique": True},
        {"keys": [("template_type", 1), ("is_active", 1)]}
    ],
    "communication_logs": [
        {"keys": [("user_id", 1)]},
        {"keys": [("communication_type", 1)]},
        {"keys": [("created_at", -1)]}
    ],
    
    # Integration indexes
    "ats_integrations": [
        {"keys": [("company_id", 1), ("is_active", 1)]},
        {"keys": [("ats_provider", 1)]}
    ],
    "job_board_syncs": [
        {"keys": [("job_id", 1)]},
        {"keys": [("sync_status", 1)]}
    ],
    "api_keys": [
        {"keys": [("api_key", 1)], "unique": True},
        {"keys": [("user_id", 1), ("is_active", 1)]}
    ],
    "webhook_events": [
        {"keys": [("delivery_status", 1), ("next_retry_at", 1)]},
        {"keys": [("event_type", 1)]},
        {"keys": [("created_at", -1)]}
    ],
    
    # Audit indexes
    "activity_logs": [
        {"keys": [("user_id", 1), ("action", 1), ("created_at", -1)]},
        {"keys": [("resource_type", 1), ("resource_id", 1)]},
        {"keys": [("created_at", -1)]}
    ],
    "data_access_logs": [
        {"keys": [("user_id", 1)]},
        {"keys": [("accessed_user_id", 1)]},
        {"keys": [("created_at", -1)]}
    ],
    
    # Gamification indexes (existing)
    "gamification_achievements": [
        {"keys": [("type", 1)]}
    ],
    "gamification_tiers": [
        {"keys": [("point_threshold", 1)]}
    ],
    "gamification_levels": [
        {"keys": [("min_referrals", 1)]}
    ],
    "user_gamification": [
        {"keys": [("user_id", 1)], "unique": True},
        {"keys": [("total_points", -1)]}
    ],
    "user_achievements": [
        {"keys": [("user_id", 1), ("achievement_id", 1)]}
    ],
    "user_streaks": [
        {"keys": [("user_id", 1)], "unique": True}
    ],
    
    # Additional indexes
    "application_status_logs": [
        {"keys": [("application_id", 1)]},
        {"keys": [("timestamp", -1)]}
    ],
    "job_views": [
        {"keys": [("job_id", 1)]},
        {"keys": [("viewed_at", -1)]}
    ],
    "resumes": [
        {"keys": [("candidate_id", 1)]},
        {"keys": [("skills", 1)]}
    ]
}


# =====================================================
# SEED DATA
# =====================================================

DEFAULT_ROLES = [
    {
        "id": str(uuid.uuid4()),
        "name": "super_admin",
        "description": "Super Administrator with full system access",
        "hierarchy_level": 1,
        "permissions": {"all": True},
        "created_at": datetime.now(timezone.utc).isoformat()
    },
    {
        "id": str(uuid.uuid4()),
        "name": "admin",
        "description": "Administrator with limited system access",
        "hierarchy_level": 2,
        "permissions": {
            "users": ["read", "write", "delete"],
            "jobs": ["read", "write", "delete"],
            "applications": ["read", "write"],
            "reports": ["read", "export"],
            "settings": ["read", "write"]
        },
        "created_at": datetime.now(timezone.utc).isoformat()
    },
    {
        "id": str(uuid.uuid4()),
        "name": "client",
        "description": "Company HR/Recruiter with company-specific access",
        "hierarchy_level": 3,
        "permissions": {
            "jobs": ["read", "write"],
            "candidates": ["read"],
            "applications": ["read", "write"],
            "reports": ["read"]
        },
        "created_at": datetime.now(timezone.utc).isoformat()
    },
    {
        "id": str(uuid.uuid4()),
        "name": "recruiter",
        "description": "Internal recruiter with recruitment operations access",
        "hierarchy_level": 3,
        "permissions": {
            "jobs": ["read", "write"],
            "candidates": ["read", "write"],
            "applications": ["read", "write"],
            "referrals": ["read", "write"],
            "interviews": ["read", "write"]
        },
        "created_at": datetime.now(timezone.utc).isoformat()
    },
    {
        "id": str(uuid.uuid4()),
        "name": "freelancer",
        "description": "Freelancer/Referrer with referral management access",
        "hierarchy_level": 4,
        "permissions": {
            "jobs": ["read"],
            "referrals": ["read", "write"],
            "commissions": ["read"],
            "profile": ["read", "write"]
        },
        "created_at": datetime.now(timezone.utc).isoformat()
    },
    {
        "id": str(uuid.uuid4()),
        "name": "candidate",
        "description": "Job seeker with self-service portal access",
        "hierarchy_level": 5,
        "permissions": {
            "profile": ["read", "write"],
            "applications": ["read", "write"],
            "jobs": ["read"]
        },
        "created_at": datetime.now(timezone.utc).isoformat()
    },
    {
        "id": str(uuid.uuid4()),
        "name": "bgv_specialist",
        "description": "Background verification specialist",
        "hierarchy_level": 3,
        "permissions": {
            "bgv": ["read", "write"],
            "candidates": ["read"],
            "documents": ["read", "write"]
        },
        "created_at": datetime.now(timezone.utc).isoformat()
    }
]


DEFAULT_EMAIL_TEMPLATES = [
    {
        "id": str(uuid.uuid4()),
        "template_name": "welcome_user",
        "template_type": "transactional",
        "subject_template": "Welcome to HiringReferrals, {{first_name}}!",
        "html_template": """
            <h1>Welcome {{first_name}}!</h1>
            <p>Thank you for joining HiringReferrals. We're excited to have you on board.</p>
            <p>Get started by:</p>
            <ul>
                <li>Completing your profile</li>
                <li>Exploring job opportunities</li>
                <li>Referring candidates to earn rewards</li>
            </ul>
            <p><a href="{{dashboard_url}}">Go to Dashboard</a></p>
        """,
        "text_template": "Welcome {{first_name}}! Thank you for joining HiringReferrals.",
        "variables": ["first_name", "dashboard_url"],
        "language": "en",
        "is_active": True,
        "created_at": datetime.now(timezone.utc).isoformat()
    },
    {
        "id": str(uuid.uuid4()),
        "template_name": "application_received",
        "template_type": "transactional",
        "subject_template": "Application Received - {{job_title}}",
        "html_template": """
            <h2>Application Submitted Successfully</h2>
            <p>Dear {{candidate_name}},</p>
            <p>Your application for <strong>{{job_title}}</strong> at <strong>{{company_name}}</strong> has been received.</p>
            <p>We will review your application and get back to you soon.</p>
            <p>Application ID: {{application_id}}</p>
        """,
        "text_template": "Your application for {{job_title}} at {{company_name}} has been received.",
        "variables": ["candidate_name", "job_title", "company_name", "application_id"],
        "language": "en",
        "is_active": True,
        "created_at": datetime.now(timezone.utc).isoformat()
    },
    {
        "id": str(uuid.uuid4()),
        "template_name": "application_shortlisted",
        "template_type": "transactional",
        "subject_template": "Congratulations! You've been shortlisted - {{job_title}}",
        "html_template": """
            <h2>You've Been Shortlisted!</h2>
            <p>Dear {{candidate_name}},</p>
            <p>Great news! Your application for <strong>{{job_title}}</strong> at <strong>{{company_name}}</strong> has been shortlisted.</p>
            <p>Our team will contact you shortly to schedule the next steps.</p>
        """,
        "text_template": "Congratulations! Your application for {{job_title}} has been shortlisted.",
        "variables": ["candidate_name", "job_title", "company_name"],
        "language": "en",
        "is_active": True,
        "created_at": datetime.now(timezone.utc).isoformat()
    },
    {
        "id": str(uuid.uuid4()),
        "template_name": "interview_scheduled",
        "template_type": "transactional",
        "subject_template": "Interview Scheduled - {{job_title}}",
        "html_template": """
            <h2>Interview Scheduled</h2>
            <p>Dear {{candidate_name}},</p>
            <p>Your interview for <strong>{{job_title}}</strong> has been scheduled.</p>
            <p><strong>Date & Time:</strong> {{interview_date}}</p>
            <p><strong>Type:</strong> {{interview_type}}</p>
            <p><strong>Location/Link:</strong> {{location}}</p>
            <p>Please confirm your attendance.</p>
        """,
        "text_template": "Your interview for {{job_title}} is scheduled on {{interview_date}}.",
        "variables": ["candidate_name", "job_title", "interview_date", "interview_type", "location"],
        "language": "en",
        "is_active": True,
        "created_at": datetime.now(timezone.utc).isoformat()
    },
    {
        "id": str(uuid.uuid4()),
        "template_name": "referral_submitted",
        "template_type": "transactional",
        "subject_template": "Referral Submitted Successfully",
        "html_template": """
            <h2>Referral Submitted</h2>
            <p>Dear {{referrer_name}},</p>
            <p>Your referral for <strong>{{candidate_name}}</strong> for the position of <strong>{{job_title}}</strong> has been submitted successfully.</p>
            <p>Referral ID: {{referral_id}}</p>
            <p>We'll notify you when there's an update on your referral.</p>
        """,
        "text_template": "Your referral for {{candidate_name}} has been submitted.",
        "variables": ["referrer_name", "candidate_name", "job_title", "referral_id"],
        "language": "en",
        "is_active": True,
        "created_at": datetime.now(timezone.utc).isoformat()
    },
    {
        "id": str(uuid.uuid4()),
        "template_name": "commission_earned",
        "template_type": "transactional",
        "subject_template": "Commission Earned - {{amount}}",
        "html_template": """
            <h2>Congratulations! Commission Earned</h2>
            <p>Dear {{user_name}},</p>
            <p>You have earned a commission of <strong>{{amount}}</strong> for the successful placement of <strong>{{candidate_name}}</strong>.</p>
            <p><strong>Job:</strong> {{job_title}}</p>
            <p><strong>Company:</strong> {{company_name}}</p>
            <p>The commission will be processed within the next payment cycle.</p>
        """,
        "text_template": "You have earned a commission of {{amount}} for placing {{candidate_name}}.",
        "variables": ["user_name", "amount", "candidate_name", "job_title", "company_name"],
        "language": "en",
        "is_active": True,
        "created_at": datetime.now(timezone.utc).isoformat()
    },
    {
        "id": str(uuid.uuid4()),
        "template_name": "bgv_initiated",
        "template_type": "transactional",
        "subject_template": "Background Verification Initiated",
        "html_template": """
            <h2>Background Verification Started</h2>
            <p>Dear {{candidate_name}},</p>
            <p>A background verification has been initiated as part of your hiring process.</p>
            <p><strong>Verification Types:</strong> {{verification_types}}</p>
            <p>Please ensure all required documents are uploaded to expedite the process.</p>
        """,
        "text_template": "Background verification has been initiated. Please upload required documents.",
        "variables": ["candidate_name", "verification_types"],
        "language": "en",
        "is_active": True,
        "created_at": datetime.now(timezone.utc).isoformat()
    },
    {
        "id": str(uuid.uuid4()),
        "template_name": "offer_letter",
        "template_type": "transactional",
        "subject_template": "Job Offer - {{job_title}} at {{company_name}}",
        "html_template": """
            <h2>Congratulations! You've Received an Offer</h2>
            <p>Dear {{candidate_name}},</p>
            <p>We are pleased to offer you the position of <strong>{{job_title}}</strong> at <strong>{{company_name}}</strong>.</p>
            <p><strong>Package:</strong> {{package}}</p>
            <p><strong>Start Date:</strong> {{start_date}}</p>
            <p>Please review the attached offer letter and respond by {{deadline}}.</p>
        """,
        "text_template": "Congratulations! You've received an offer for {{job_title}} at {{company_name}}.",
        "variables": ["candidate_name", "job_title", "company_name", "package", "start_date", "deadline"],
        "language": "en",
        "is_active": True,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
]


class DatabaseInitializer:
    """Handles database initialization and migration"""
    
    def __init__(self, mongo_url: str, db_name: str):
        self.client = AsyncIOMotorClient(mongo_url)
        self.db = self.client[db_name]
    
    async def create_indexes(self):
        """Create all indexes for collections"""
        print("📊 Creating indexes...")
        
        for collection_name, indexes in INDEXES.items():
            collection = self.db[collection_name]
            for idx in indexes:
                try:
                    keys = idx["keys"]
                    options = {k: v for k, v in idx.items() if k != "keys"}
                    await collection.create_index(keys, **options)
                    print(f"   ✓ Index created on {collection_name}: {keys}")
                except Exception as e:
                    if "already exists" not in str(e).lower():
                        print(f"   ⚠ Index warning on {collection_name}: {e}")
        
        print("✅ Indexes created successfully")
    
    async def seed_roles(self):
        """Seed default roles"""
        print("\n🎭 Seeding roles...")
        
        for role in DEFAULT_ROLES:
            existing = await self.db.roles.find_one({"name": role["name"]})
            if not existing:
                await self.db.roles.insert_one(role)
                print(f"   ✓ Created role: {role['name']}")
            else:
                print(f"   - Role exists: {role['name']}")
        
        print("✅ Roles seeded successfully")
    
    async def seed_email_templates(self):
        """Seed default email templates"""
        print("\n📧 Seeding email templates...")
        
        for template in DEFAULT_EMAIL_TEMPLATES:
            existing = await self.db.email_templates.find_one(
                {"template_name": template["template_name"]}
            )
            if not existing:
                await self.db.email_templates.insert_one(template)
                print(f"   ✓ Created template: {template['template_name']}")
            else:
                print(f"   - Template exists: {template['template_name']}")
        
        print("✅ Email templates seeded successfully")
    
    async def migrate_users(self):
        """Migrate existing users to new schema structure"""
        print("\n👥 Migrating users...")
        
        users = await self.db.users.find({}).to_list(1000)
        migrated = 0
        
        for user in users:
            updates = {}
            
            # Add missing fields
            if "is_active" not in user:
                updates["is_active"] = True
            if "is_verified" not in user:
                updates["is_verified"] = True
            if "failed_login_attempts" not in user:
                updates["failed_login_attempts"] = 0
            if "updated_at" not in user:
                updates["updated_at"] = datetime.now(timezone.utc).isoformat()
            
            if updates:
                await self.db.users.update_one(
                    {"id": user["id"]},
                    {"$set": updates}
                )
                migrated += 1
            
            # Create user_roles entry if not exists
            role_name = user.get("role", "candidate")
            role = await self.db.roles.find_one({"name": role_name})
            
            if role:
                existing_user_role = await self.db.user_roles.find_one({
                    "user_id": user["id"],
                    "role_id": role["id"]
                })
                
                if not existing_user_role:
                    await self.db.user_roles.insert_one({
                        "id": str(uuid.uuid4()),
                        "user_id": user["id"],
                        "role_id": role["id"],
                        "role_name": role_name,
                        "assigned_at": user.get("created_at", datetime.now(timezone.utc).isoformat()),
                        "is_active": True
                    })
            
            # Create user_profile if not exists
            existing_profile = await self.db.user_profiles.find_one({"user_id": user["id"]})
            if not existing_profile:
                profile = {
                    "id": str(uuid.uuid4()),
                    "user_id": user["id"],
                    "first_name": user.get("full_name", "").split()[0] if user.get("full_name") else None,
                    "last_name": " ".join(user.get("full_name", "").split()[1:]) if user.get("full_name") else None,
                    "profile_type": role_name,
                    "created_at": user.get("created_at", datetime.now(timezone.utc).isoformat()),
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }
                await self.db.user_profiles.insert_one(profile)
        
        print(f"✅ Users migrated: {migrated} updated, {len(users)} total")
    
    async def migrate_jobs(self):
        """Migrate existing jobs to new schema structure"""
        print("\n💼 Migrating jobs...")
        
        jobs = await self.db.jobs.find({}).to_list(1000)
        migrated = 0
        
        for job in jobs:
            updates = {}
            
            # Add missing fields
            if "job_status" not in job:
                updates["job_status"] = job.get("status", "published")
            if "remote_policy" not in job:
                updates["remote_policy"] = "onsite"
            if "employment_type" not in job:
                updates["employment_type"] = job.get("employment_type", "full_time")
            if "experience_min" not in job:
                updates["experience_min"] = 0
            if "skills_required" not in job:
                updates["skills_required"] = job.get("requirements", [])
            if "skills_preferred" not in job:
                updates["skills_preferred"] = job.get("preferred_skills", [])
            if "view_count" not in job:
                updates["view_count"] = 0
            if "application_count" not in job:
                updates["application_count"] = await self.db.applications.count_documents({"job_id": job["id"]})
            if "salary_currency" not in job:
                updates["salary_currency"] = "INR"
            if "positions_available" not in job:
                updates["positions_available"] = 1
            if "urgency_level" not in job:
                updates["urgency_level"] = "normal"
            
            if updates:
                await self.db.jobs.update_one(
                    {"id": job["id"]},
                    {"$set": updates}
                )
                migrated += 1
        
        print(f"✅ Jobs migrated: {migrated} updated, {len(jobs)} total")
    
    async def migrate_applications(self):
        """Migrate existing applications to new schema structure"""
        print("\n📋 Migrating applications...")
        
        applications = await self.db.applications.find({}).to_list(5000)
        migrated = 0
        
        for app in applications:
            updates = {}
            
            # Add missing fields
            if "application_status" not in app:
                updates["application_status"] = app.get("status", "submitted")
            if "status_history" not in app:
                updates["status_history"] = [{
                    "status": app.get("status", "submitted"),
                    "timestamp": app.get("created_at", datetime.now(timezone.utc).isoformat()),
                    "changed_by": "system"
                }]
            if "match_score" not in app:
                updates["match_score"] = app.get("screening_score")
            if "match_details" not in app:
                updates["match_details"] = app.get("score_details", {})
            if "additional_documents" not in app:
                updates["additional_documents"] = []
            if "interview_feedback" not in app:
                updates["interview_feedback"] = []
            
            if updates:
                await self.db.applications.update_one(
                    {"id": app["id"]},
                    {"$set": updates}
                )
                migrated += 1
        
        print(f"✅ Applications migrated: {migrated} updated, {len(applications)} total")
    
    async def migrate_referrals(self):
        """Migrate existing referrals to new schema structure"""
        print("\n🤝 Migrating referrals...")
        
        referrals = await self.db.referrals.find({}).to_list(5000)
        migrated = 0
        
        for ref in referrals:
            updates = {}
            
            if "referral_status" not in ref:
                updates["referral_status"] = ref.get("status", "submitted")
            if "quality_score" not in ref:
                updates["quality_score"] = None
            if "feedback" not in ref:
                updates["feedback"] = None
            
            if updates:
                await self.db.referrals.update_one(
                    {"id": ref["id"]},
                    {"$set": updates}
                )
                migrated += 1
        
        print(f"✅ Referrals migrated: {migrated} updated, {len(referrals)} total")
    
    async def migrate_bgv_requests(self):
        """Migrate existing BGV requests to new schema structure"""
        print("\n🔍 Migrating BGV requests...")
        
        bgv_requests = await self.db.bgv_requests.find({}).to_list(1000)
        migrated = 0
        
        for bgv in bgv_requests:
            updates = {}
            
            if "verification_status" not in bgv:
                updates["verification_status"] = bgv.get("status", "pending")
            if "completion_percentage" not in bgv:
                updates["completion_percentage"] = 0
            if "priority" not in bgv:
                updates["priority"] = "normal"
            
            if updates:
                await self.db.bgv_requests.update_one(
                    {"id": bgv["id"]},
                    {"$set": updates}
                )
                migrated += 1
        
        # Rename collection if needed (bgv_requests -> background_verifications)
        # We'll keep both for backward compatibility
        
        print(f"✅ BGV requests migrated: {migrated} updated, {len(bgv_requests)} total")
    
    async def create_missing_collections(self):
        """Create any missing collections with sample structure"""
        print("\n📁 Creating missing collections...")
        
        all_collections = [
            "users", "roles", "user_roles", "user_profiles", "user_sessions",
            "companies", "jobs", "candidates", "applications", "referrals",
            "background_verifications", "interviews", "assessments",
            "commissions", "payments", "invoices", "payout_requests",
            "messages", "notifications", "email_templates", "communication_logs",
            "ats_integrations", "job_board_syncs", "api_keys", "webhook_events",
            "activity_logs", "data_access_logs"
        ]
        
        existing = await self.db.list_collection_names()
        
        for collection in all_collections:
            if collection not in existing:
                # Create collection with a dummy document and then remove it
                await self.db[collection].insert_one({"_init": True})
                await self.db[collection].delete_one({"_init": True})
                print(f"   ✓ Created collection: {collection}")
        
        print("✅ Collections created successfully")
    
    async def run_full_migration(self):
        """Run the complete migration process"""
        print("\n" + "="*60)
        print("🚀 Starting Database Migration")
        print("="*60)
        
        await self.create_missing_collections()
        await self.create_indexes()
        await self.seed_roles()
        await self.seed_email_templates()
        await self.migrate_users()
        await self.migrate_jobs()
        await self.migrate_applications()
        await self.migrate_referrals()
        await self.migrate_bgv_requests()
        
        print("\n" + "="*60)
        print("✅ Database Migration Complete!")
        print("="*60)
        
        # Print summary
        await self.print_summary()
    
    async def print_summary(self):
        """Print database summary"""
        print("\n📊 Database Summary:")
        
        collections = await self.db.list_collection_names()
        total_docs = 0
        
        for col in sorted(collections):
            count = await self.db[col].count_documents({})
            total_docs += count
            if count > 0:
                print(f"   {col}: {count} documents")
        
        print(f"\n   Total: {total_docs} documents in {len(collections)} collections")
    
    async def close(self):
        """Close database connection"""
        self.client.close()


async def main():
    """Main entry point"""
    initializer = DatabaseInitializer(MONGO_URL, DB_NAME)
    
    try:
        await initializer.run_full_migration()
    finally:
        await initializer.close()


if __name__ == "__main__":
    asyncio.run(main())
