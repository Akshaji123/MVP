"""
MongoDB Database Connection Module
HiringReferrals Platform

This module provides database connection management, utilities,
and export/import functionality for the MongoDB database.
"""

import os
import json
import asyncio
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo import MongoClient
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

# Database Configuration
DATABASE_CONFIG = {
    "MONGO_URL": os.environ.get("MONGO_URL", "mongodb://localhost:27017"),
    "DB_NAME": os.environ.get("DB_NAME", "test_database"),
    "EXPORT_DIR": "/app/database_export",
    "BACKUP_DIR": "/app/database_backups"
}

class DatabaseConnection:
    """
    Singleton class for managing MongoDB connections.
    Provides both async (Motor) and sync (PyMongo) clients.
    """
    
    _instance = None
    _async_client: Optional[AsyncIOMotorClient] = None
    _sync_client: Optional[MongoClient] = None
    _db: Optional[AsyncIOMotorDatabase] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @classmethod
    def get_async_client(cls) -> AsyncIOMotorClient:
        """Get async Motor client for FastAPI"""
        if cls._async_client is None:
            cls._async_client = AsyncIOMotorClient(DATABASE_CONFIG["MONGO_URL"])
            logger.info(f"Async MongoDB client connected to {DATABASE_CONFIG['MONGO_URL']}")
        return cls._async_client
    
    @classmethod
    def get_sync_client(cls) -> MongoClient:
        """Get sync PyMongo client for scripts and utilities"""
        if cls._sync_client is None:
            cls._sync_client = MongoClient(DATABASE_CONFIG["MONGO_URL"])
            logger.info(f"Sync MongoDB client connected to {DATABASE_CONFIG['MONGO_URL']}")
        return cls._sync_client
    
    @classmethod
    def get_database(cls) -> AsyncIOMotorDatabase:
        """Get the main database instance"""
        if cls._db is None:
            client = cls.get_async_client()
            cls._db = client[DATABASE_CONFIG["DB_NAME"]]
            logger.info(f"Connected to database: {DATABASE_CONFIG['DB_NAME']}")
        return cls._db
    
    @classmethod
    def get_sync_database(cls):
        """Get sync database for scripts"""
        client = cls.get_sync_client()
        return client[DATABASE_CONFIG["DB_NAME"]]
    
    @classmethod
    async def close_connections(cls):
        """Close all database connections"""
        if cls._async_client:
            cls._async_client.close()
            cls._async_client = None
            logger.info("Async MongoDB connection closed")
        if cls._sync_client:
            cls._sync_client.close()
            cls._sync_client = None
            logger.info("Sync MongoDB connection closed")
        cls._db = None
    
    @classmethod
    async def health_check(cls) -> Dict[str, Any]:
        """Check database connection health"""
        try:
            db = cls.get_database()
            # Ping the database
            await db.command("ping")
            
            # Get collection stats
            collections = await db.list_collection_names()
            
            stats = {
                "status": "healthy",
                "database": DATABASE_CONFIG["DB_NAME"],
                "mongo_url": DATABASE_CONFIG["MONGO_URL"].split("@")[-1],  # Hide credentials
                "collections_count": len(collections),
                "collections": collections,
                "checked_at": datetime.now(timezone.utc).isoformat()
            }
            
            return stats
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "checked_at": datetime.now(timezone.utc).isoformat()
            }


class DatabaseExporter:
    """Utility class for exporting and importing database data"""
    
    def __init__(self):
        self.export_dir = Path(DATABASE_CONFIG["EXPORT_DIR"])
        self.export_dir.mkdir(parents=True, exist_ok=True)
    
    async def export_collection(self, collection_name: str) -> Dict[str, Any]:
        """Export a single collection to JSON"""
        db = DatabaseConnection.get_database()
        collection = db[collection_name]
        
        documents = await collection.find({}).to_list(10000)
        
        # Convert ObjectId to string
        for doc in documents:
            if '_id' in doc:
                doc['_id'] = str(doc['_id'])
        
        filepath = self.export_dir / f"{collection_name}.json"
        with open(filepath, 'w') as f:
            json.dump(documents, f, indent=2, default=str)
        
        return {
            "collection": collection_name,
            "documents": len(documents),
            "filepath": str(filepath)
        }
    
    async def export_all(self) -> Dict[str, Any]:
        """Export all collections to JSON files"""
        db = DatabaseConnection.get_database()
        collections = await db.list_collection_names()
        
        results = {}
        for collection_name in collections:
            result = await self.export_collection(collection_name)
            results[collection_name] = result["documents"]
            logger.info(f"Exported {collection_name}: {result['documents']} documents")
        
        # Save summary
        summary = {
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "database": DATABASE_CONFIG["DB_NAME"],
            "collections": results,
            "total_documents": sum(results.values())
        }
        
        summary_path = self.export_dir / "_summary.json"
        with open(summary_path, 'w') as f:
            json.dump(summary, f, indent=2)
        
        return summary
    
    async def import_collection(self, collection_name: str, clear_existing: bool = False) -> Dict[str, Any]:
        """Import a collection from JSON file"""
        db = DatabaseConnection.get_database()
        filepath = self.export_dir / f"{collection_name}.json"
        
        if not filepath.exists():
            return {"error": f"File not found: {filepath}"}
        
        with open(filepath, 'r') as f:
            documents = json.load(f)
        
        if not documents:
            return {"collection": collection_name, "imported": 0}
        
        collection = db[collection_name]
        
        if clear_existing:
            await collection.delete_many({})
        
        # Remove _id fields to let MongoDB generate new ones
        for doc in documents:
            doc.pop('_id', None)
        
        result = await collection.insert_many(documents)
        
        return {
            "collection": collection_name,
            "imported": len(result.inserted_ids)
        }


class DatabaseSeeder:
    """Utility class for seeding initial data"""
    
    @staticmethod
    async def seed_admin_user():
        """Create default admin user if not exists"""
        db = DatabaseConnection.get_database()
        
        existing = await db.users.find_one({"role": "admin"})
        if existing:
            return {"message": "Admin user already exists"}
        
        import bcrypt
        import uuid
        
        admin_user = {
            "id": str(uuid.uuid4()),
            "email": "admin@hiringreferrals.com",
            "full_name": "System Admin",
            "role": "admin",
            "password": bcrypt.hashpw("admin123".encode('utf-8'), bcrypt.gensalt()).decode('utf-8'),
            "currency_preference": "INR",
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        await db.users.insert_one(admin_user)
        logger.info("Default admin user created")
        
        return {"message": "Admin user created", "email": admin_user["email"]}
    
    @staticmethod
    async def seed_sample_data():
        """Seed sample data for testing"""
        db = DatabaseConnection.get_database()
        
        # Check if data exists
        job_count = await db.jobs.count_documents({})
        if job_count > 0:
            return {"message": "Sample data already exists"}
        
        import uuid
        
        # Sample company
        company = {
            "id": str(uuid.uuid4()),
            "email": "demo@company.com",
            "full_name": "Demo Company Inc",
            "role": "company",
            "password": "$2b$12$demo",  # Placeholder
            "currency_preference": "USD",
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        # Sample job
        job = {
            "id": str(uuid.uuid4()),
            "title": "Senior Software Engineer",
            "description": "We are looking for an experienced software engineer...",
            "requirements": ["Python", "React", "MongoDB", "5+ years experience"],
            "location": "Remote",
            "salary_range": "$120k - $150k",
            "experience_level": "Senior",
            "employment_type": "Full-time",
            "company_id": company["id"],
            "company_name": company["full_name"],
            "status": "active",
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        await db.users.insert_one(company)
        await db.jobs.insert_one(job)
        
        logger.info("Sample data seeded successfully")
        return {"message": "Sample data created", "job_id": job["id"]}


# Convenience functions for direct import
def get_db() -> AsyncIOMotorDatabase:
    """Shortcut to get database instance"""
    return DatabaseConnection.get_database()

def get_sync_db():
    """Shortcut to get sync database instance"""
    return DatabaseConnection.get_sync_database()

async def export_database():
    """Shortcut to export all collections"""
    exporter = DatabaseExporter()
    return await exporter.export_all()


# Collection name constants
class Collections:
    USERS = "users"
    JOBS = "jobs"
    APPLICATIONS = "applications"
    RESUMES = "resumes"
    REFERRALS = "referrals"
    DOCUMENTS = "documents"
    BGV_REQUESTS = "bgv_requests"
    CANDIDATE_TRACKING = "candidate_tracking"
    INVOICES = "invoices"
    AUTOMATION_RULES = "automation_rules"
    PLATFORM_SETTINGS = "platform_settings"
    USER_SESSIONS = "user_sessions"
    # Gamification
    GAMIFICATION_ACHIEVEMENTS = "gamification_achievements"
    GAMIFICATION_TIERS = "gamification_tiers"
    GAMIFICATION_LEVELS = "gamification_levels"
    USER_GAMIFICATION = "user_gamification"
    USER_ACHIEVEMENTS = "user_achievements"
    USER_STREAKS = "user_streaks"
