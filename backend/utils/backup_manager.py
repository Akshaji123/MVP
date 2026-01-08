import json
import os
import zipfile
from datetime import datetime
from pathlib import Path

class BackupManager:
    def __init__(self, backup_dir="/app/backups"):
        self.backup_dir = backup_dir
        os.makedirs(backup_dir, exist_ok=True)
        
    async def create_full_backup(self, db, collections: list) -> str:
        """Create full database backup"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"backup_{timestamp}"
        backup_path = os.path.join(self.backup_dir, backup_name)
        os.makedirs(backup_path, exist_ok=True)
        
        # Export each collection to JSON
        for collection_name in collections:
            collection = db[collection_name]
            documents = await collection.find({}, {"_id": 0}).to_list(None)
            
            filepath = os.path.join(backup_path, f"{collection_name}.json")
            with open(filepath, 'w') as f:
                json.dump(documents, f, indent=2, default=str)
        
        # Create ZIP archive
        zip_path = f"{backup_path}.zip"
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(backup_path):
                for file in files:
                    filepath = os.path.join(root, file)
                    arcname = os.path.relpath(filepath, backup_path)
                    zipf.write(filepath, arcname)
        
        # Clean up unzipped folder
        import shutil
        shutil.rmtree(backup_path)
        
        return zip_path
    
    async def restore_from_backup(self, db, backup_path: str):
        """Restore database from backup"""
        # Extract ZIP
        extract_path = backup_path.replace('.zip', '')
        with zipfile.ZipFile(backup_path, 'r') as zipf:
            zipf.extractall(extract_path)
        
        # Import each collection
        for json_file in Path(extract_path).glob('*.json'):
            collection_name = json_file.stem
            with open(json_file, 'r') as f:
                documents = json.load(f)
            
            if documents:
                await db[collection_name].insert_many(documents)
        
        # Clean up
        import shutil
        shutil.rmtree(extract_path)
        
        return True
    
    def list_backups(self) -> list:
        """List all available backups"""
        backups = []
        for file in Path(self.backup_dir).glob('backup_*.zip'):
            backups.append({
                'name': file.name,
                'path': str(file),
                'size': file.stat().st_size,
                'created': datetime.fromtimestamp(file.stat().st_ctime).isoformat()
            })
        return sorted(backups, key=lambda x: x['created'], reverse=True)
