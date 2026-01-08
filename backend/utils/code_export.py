import os
import zipfile
from pathlib import Path
from datetime import datetime

class CodeExporter:
    def __init__(self, export_dir="/app/exports"):
        self.export_dir = export_dir
        os.makedirs(export_dir, exist_ok=True)
        
    def create_code_archive(self, base_path="/app") -> str:
        """Create ZIP archive of entire codebase"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        archive_name = f"hiringreferrals_code_{timestamp}.zip"
        archive_path = os.path.join(self.export_dir, archive_name)
        
        # Directories to include
        include_dirs = ['backend', 'frontend']
        
        # Files/folders to exclude
        exclude_patterns = [
            '__pycache__',
            'node_modules',
            '.git',
            '.venv',
            '*.pyc',
            '.DS_Store',
            'exports',
            'backups',
            'invoices',
            'uploads'
        ]
        
        with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for dir_name in include_dirs:
                dir_path = os.path.join(base_path, dir_name)
                if os.path.exists(dir_path):
                    for root, dirs, files in os.walk(dir_path):
                        # Filter out excluded directories
                        dirs[:] = [d for d in dirs if not any(pattern in d for pattern in exclude_patterns)]
                        
                        for file in files:
                            # Skip excluded files
                            if any(pattern.replace('*', '') in file for pattern in exclude_patterns if '*' in pattern):
                                continue
                            
                            filepath = os.path.join(root, file)
                            arcname = os.path.relpath(filepath, base_path)
                            zipf.write(filepath, arcname)
            
            # Add README
            readme_content = f"""# HiringReferrals Platform Export

Exported on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Structure
- backend/: FastAPI backend application
- frontend/: React frontend application

## Setup Instructions

### Backend
1. cd backend
2. pip install -r requirements.txt
3. Copy .env.example to .env and configure
4. python server.py

### Frontend  
1. cd frontend
2. yarn install
3. Copy .env.example to .env and configure
4. yarn start

## Features
- AI-powered resume parsing and scoring
- Multi-role dashboard (Admin, Company, Recruiter, Candidate)
- ATS with pipeline management
- Document management system
- Background verification (BGV)
- 91-day candidate tracking
- Automated invoice generation
- Gamified referral system with leaderboards
"""
            zipf.writestr('README.md', readme_content)
        
        return archive_path
    
    def list_exports(self) -> list:
        """List all code exports"""
        exports = []
        for file in Path(self.export_dir).glob('hiringreferrals_code_*.zip'):
            exports.append({
                'name': file.name,
                'path': str(file),
                'size': file.stat().st_size,
                'created': datetime.fromtimestamp(file.stat().st_ctime).isoformat()
            })
        return sorted(exports, key=lambda x: x['created'], reverse=True)
