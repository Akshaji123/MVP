#!/usr/bin/env python3
"""
Database Management CLI Tool
HiringReferrals Platform

Usage:
    python db_manager.py export          # Export all collections to JSON
    python db_manager.py import          # Import from JSON files
    python db_manager.py status          # Check database status
    python db_manager.py seed            # Seed initial data
    python db_manager.py collections     # List all collections
    python db_manager.py count           # Count documents in all collections
    python db_manager.py query <collection> [limit]  # Query a collection
"""

import asyncio
import sys
import json
from pathlib import Path

# Add backend to path
sys.path.insert(0, '/app/backend')

from database import (
    DatabaseConnection, 
    DatabaseExporter, 
    DatabaseSeeder,
    DATABASE_CONFIG
)


async def export_database():
    """Export all collections to JSON files"""
    print("📦 Exporting database...")
    exporter = DatabaseExporter()
    result = await exporter.export_all()
    
    print(f"\n✅ Export complete!")
    print(f"   Database: {result['database']}")
    print(f"   Total documents: {result['total_documents']}")
    print(f"   Export location: {DATABASE_CONFIG['EXPORT_DIR']}")
    print("\n   Collections:")
    for name, count in result['collections'].items():
        print(f"     - {name}: {count} documents")


async def import_database():
    """Import collections from JSON files"""
    print("📥 Importing database...")
    exporter = DatabaseExporter()
    export_dir = Path(DATABASE_CONFIG['EXPORT_DIR'])
    
    if not export_dir.exists():
        print("❌ Export directory not found. Run 'export' first.")
        return
    
    json_files = list(export_dir.glob("*.json"))
    json_files = [f for f in json_files if not f.name.startswith("_")]
    
    for filepath in json_files:
        collection_name = filepath.stem
        result = await exporter.import_collection(collection_name)
        print(f"   Imported {collection_name}: {result.get('imported', 0)} documents")
    
    print("\n✅ Import complete!")


async def check_status():
    """Check database connection status"""
    print("🔍 Checking database status...")
    result = await DatabaseConnection.health_check()
    
    if result['status'] == 'healthy':
        print(f"\n✅ Database Status: HEALTHY")
        print(f"   Database: {result['database']}")
        print(f"   Collections: {result['collections_count']}")
        print(f"   Checked at: {result['checked_at']}")
        print("\n   Available collections:")
        for col in result['collections']:
            print(f"     - {col}")
    else:
        print(f"\n❌ Database Status: UNHEALTHY")
        print(f"   Error: {result.get('error', 'Unknown')}")


async def seed_data():
    """Seed initial data"""
    print("🌱 Seeding database...")
    
    # Seed admin user
    result = await DatabaseSeeder.seed_admin_user()
    print(f"   Admin: {result['message']}")
    
    # Seed sample data
    result = await DatabaseSeeder.seed_sample_data()
    print(f"   Sample data: {result['message']}")
    
    print("\n✅ Seeding complete!")


async def list_collections():
    """List all collections"""
    print("📋 Collections in database:")
    db = DatabaseConnection.get_database()
    collections = await db.list_collection_names()
    
    for col in sorted(collections):
        count = await db[col].count_documents({})
        print(f"   - {col}: {count} documents")


async def count_documents():
    """Count documents in all collections"""
    print("📊 Document counts:")
    db = DatabaseConnection.get_database()
    collections = await db.list_collection_names()
    
    total = 0
    for col in sorted(collections):
        count = await db[col].count_documents({})
        total += count
        print(f"   {col}: {count}")
    
    print(f"\n   Total: {total} documents")


async def query_collection(collection_name: str, limit: int = 5):
    """Query a collection and show sample documents"""
    print(f"🔎 Querying {collection_name} (limit: {limit})...")
    db = DatabaseConnection.get_database()
    
    if collection_name not in await db.list_collection_names():
        print(f"❌ Collection '{collection_name}' not found")
        return
    
    documents = await db[collection_name].find({}, {"_id": 0}).limit(limit).to_list(limit)
    
    print(f"\n   Found {len(documents)} documents:\n")
    for i, doc in enumerate(documents, 1):
        print(f"   --- Document {i} ---")
        print(json.dumps(doc, indent=4, default=str))
        print()


def print_help():
    """Print help message"""
    print(__doc__)


async def main():
    if len(sys.argv) < 2:
        print_help()
        return
    
    command = sys.argv[1].lower()
    
    try:
        if command == 'export':
            await export_database()
        elif command == 'import':
            await import_database()
        elif command == 'status':
            await check_status()
        elif command == 'seed':
            await seed_data()
        elif command == 'collections':
            await list_collections()
        elif command == 'count':
            await count_documents()
        elif command == 'query':
            if len(sys.argv) < 3:
                print("Usage: python db_manager.py query <collection> [limit]")
                return
            collection = sys.argv[2]
            limit = int(sys.argv[3]) if len(sys.argv) > 3 else 5
            await query_collection(collection, limit)
        elif command in ['help', '-h', '--help']:
            print_help()
        else:
            print(f"Unknown command: {command}")
            print_help()
    finally:
        await DatabaseConnection.close_connections()


if __name__ == "__main__":
    asyncio.run(main())
