from fastapi import FastAPI, APIRouter, HTTPException, Depends, status, UploadFile, File
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import FileResponse, StreamingResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone, timedelta
import jwt
import bcrypt
from emergentintegrations.llm.chat import LlmChat, UserMessage
import io
from PyPDF2 import PdfReader
from docx import Document
import shutil
from utils.invoice_generator import InvoiceGenerator
from utils.backup_manager import BackupManager
from utils.code_export import CodeExporter

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Initialize enterprise utilities
invoice_generator = InvoiceGenerator()
backup_manager = BackupManager()
code_exporter = CodeExporter()

# JWT Configuration
JWT_SECRET = os.environ.get('JWT_SECRET', 'your-secret-key-change-in-production')
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 720

# File upload configuration
UPLOAD_DIR = "/app/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Security
security = HTTPBearer()

app = FastAPI()
api_router = APIRouter(prefix="/api")

# ATS Stage definitions
ATS_STAGES = [
    {"id": "applied", "name": "Applied", "order": 1, "color": "#94a3b8"},
    {"id": "screening", "name": "Screening", "order": 2, "color": "#60a5fa"},
    {"id": "interview", "name": "Interview", "order": 3, "color": "#a78bfa"},
    {"id": "assessment", "name": "Assessment", "order": 4, "color": "#f59e0b"},
    {"id": "offer", "name": "Offer", "order": 5, "color": "#10b981"},
    {"id": "hired", "name": "Hired", "order": 6, "color": "#22c55e"},
    {"id": "rejected", "name": "Rejected", "order": 7, "color": "#ef4444"},
]

# ============= Models =============

class UserBase(BaseModel):
    email: EmailStr
    full_name: str
    role: str  # admin, company, recruiter, candidate

class UserCreate(UserBase):
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(UserBase):
    id: str
    created_at: str
    currency_preference: Optional[str] = "INR"

class TokenResponse(BaseModel):
    access_token: str
    user: UserResponse

class JobCreate(BaseModel):
    title: str
    description: str
    requirements: List[str]
    location: str
    salary_range: str
    experience_level: str
    employment_type: str

class JobResponse(JobCreate):
    id: str
    company_id: str
    company_name: str
    status: str
    created_at: str
    applications_count: int = 0

class ResumeUpload(BaseModel):
    candidate_id: str
    file_name: str

class ResumeAnalysis(BaseModel):
    id: str
    candidate_id: str
    file_name: str
    parsed_data: Dict[str, Any]
    overall_score: int
    skills: List[str]
    experience_years: int
    education: List[str]
    created_at: str

class ApplicationCreate(BaseModel):
    job_id: str
    resume_id: str

class ApplicationResponse(BaseModel):
    id: str
    job_id: str
    candidate_id: str
    candidate_name: str
    resume_id: str
    match_score: int
    status: str  # pending, reviewing, shortlisted, rejected, hired
    created_at: str
    job_title: str

class ReferralCreate(BaseModel):
    job_id: str
    candidate_email: str
    candidate_name: str
    candidate_phone: Optional[str] = None

class ReferralResponse(BaseModel):
    id: str
    job_id: str
    job_title: str
    referrer_id: str
    referrer_name: str
    candidate_email: str
    candidate_name: str
    status: str  # pending, applied, hired, rejected
    reward_amount: int
    created_at: str

class LeaderboardEntry(BaseModel):
    user_id: str
    user_name: str
    role: str
    total_referrals: int
    successful_referrals: int
    total_earnings: int
    rank: int

class DashboardStats(BaseModel):
    total_jobs: int = 0
    active_jobs: int = 0
    total_applications: int = 0
    pending_applications: int = 0
    total_candidates: int = 0
    total_recruiters: int = 0
    total_companies: int = 0

# ============= Helper Functions =============

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def create_token(user_id: str, email: str, role: str) -> str:
    expiration = datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRATION_HOURS)
    payload = {
        "user_id": user_id,
        "email": email,
        "role": role,
        "exp": expiration
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    payload = decode_token(token)
    user = await db.users.find_one({"id": payload["user_id"]}, {"_id": 0, "password": 0})
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user

async def parse_resume_with_ai(file_content: bytes, file_name: str) -> Dict[str, Any]:
    """Parse resume using GPT-4o via emergentintegrations"""
    try:
        # Extract text from PDF or DOCX
        text_content = ""
        
        if file_name.endswith('.pdf'):
            pdf_reader = PdfReader(io.BytesIO(file_content))
            for page in pdf_reader.pages:
                text_content += page.extract_text()
        elif file_name.endswith('.docx'):
            doc = Document(io.BytesIO(file_content))
            for para in doc.paragraphs:
                text_content += para.text + "\n"
        else:
            text_content = file_content.decode('utf-8', errors='ignore')
        
        # Use AI to parse resume
        api_key = os.environ.get('EMERGENT_LLM_KEY', '')
        chat = LlmChat(
            api_key=api_key,
            session_id=str(uuid.uuid4()),
            system_message="You are an expert resume parser. Extract structured information from resumes."
        ).with_model("openai", "gpt-4o")
        
        prompt = f"""Parse this resume and extract the following information in JSON format:
{{
  "name": "Full name",
  "email": "Email address",
  "phone": "Phone number",
  "skills": ["list of skills"],
  "experience_years": number,
  "education": ["list of degrees and institutions"],
  "work_history": ["brief list of positions and companies"],
  "summary": "Brief professional summary"
}}

Resume:
{text_content[:4000]}

Respond ONLY with valid JSON, no additional text."""
        
        response = await chat.send_message(UserMessage(text=prompt))
        
        # Parse JSON response
        import json
        parsed_data = json.loads(response)
        
        return parsed_data
    except Exception as e:
        logging.error(f"Resume parsing error: {str(e)}")
        return {
            "name": "Unknown",
            "email": "",
            "phone": "",
            "skills": [],
            "experience_years": 0,
            "education": [],
            "work_history": [],
            "summary": "Failed to parse resume"
        }

async def score_resume_with_ai(resume_data: Dict, job_description: str) -> Dict[str, Any]:
    """Score resume against job description using AI"""
    try:
        api_key = os.environ.get('EMERGENT_LLM_KEY', '')
        chat = LlmChat(
            api_key=api_key,
            session_id=str(uuid.uuid4()),
            system_message="You are an expert recruiter analyzing candidate fit."
        ).with_model("openai", "gpt-4o")
        
        prompt = f"""Analyze this candidate's resume against the job description and provide a matching score.

Job Description:
{job_description}

Candidate Profile:
Skills: {', '.join(resume_data.get('skills', []))}
Experience: {resume_data.get('experience_years', 0)} years
Education: {', '.join(resume_data.get('education', []))}
Summary: {resume_data.get('summary', '')}

Provide a JSON response with:
{{
  "match_score": <number 0-100>,
  "strengths": ["list of strengths"],
  "gaps": ["list of gaps or missing skills"],
  "recommendation": "Short recommendation"
}}

Respond ONLY with valid JSON."""
        
        response = await chat.send_message(UserMessage(text=prompt))
        
        import json
        score_data = json.loads(response)
        
        return score_data
    except Exception as e:
        logging.error(f"Resume scoring error: {str(e)}")
        return {
            "match_score": 50,
            "strengths": [],
            "gaps": [],
            "recommendation": "Manual review recommended"
        }

# ============= Routes =============

@api_router.post("/auth/register", response_model=TokenResponse)
async def register(user: UserCreate):
    # Check if user exists
    existing = await db.users.find_one({"email": user.email}, {"_id": 0, "id": 1})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create user
    user_id = str(uuid.uuid4())
    user_doc = {
        "id": user_id,
        "email": user.email,
        "full_name": user.full_name,
        "role": user.role,
        "password": hash_password(user.password),
        "currency_preference": "INR",  # Default currency
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.users.insert_one(user_doc)
    
    token = create_token(user_id, user.email, user.role)
    
    return {
        "access_token": token,
        "user": UserResponse(
            id=user_id,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            created_at=user_doc["created_at"]
        )
    }

@api_router.post("/auth/login", response_model=TokenResponse)
async def login(credentials: UserLogin):
    user = await db.users.find_one({"email": credentials.email}, {"_id": 0})
    if not user or not verify_password(credentials.password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = create_token(user["id"], user["email"], user["role"])
    
    return {
        "access_token": token,
        "user": UserResponse(
            id=user["id"],
            email=user["email"],
            full_name=user["full_name"],
            role=user["role"],
            created_at=user["created_at"]
        )
    }

@api_router.get("/auth/me", response_model=UserResponse)
async def get_me(current_user: dict = Depends(get_current_user)):
    return UserResponse(**current_user)

@api_router.post("/jobs", response_model=JobResponse)
async def create_job(job: JobCreate, current_user: dict = Depends(get_current_user)):
    if current_user["role"] not in ["company", "admin"]:
        raise HTTPException(status_code=403, detail="Only companies can post jobs")
    
    job_id = str(uuid.uuid4())
    job_doc = {
        "id": job_id,
        "company_id": current_user["id"],
        "company_name": current_user["full_name"],
        "status": "active",
        "created_at": datetime.now(timezone.utc).isoformat(),
        **job.model_dump()
    }
    
    await db.jobs.insert_one(job_doc)
    
    return JobResponse(**{k: v for k, v in job_doc.items() if k != "_id"}, applications_count=0)

@api_router.get("/jobs", response_model=List[JobResponse])
async def get_jobs(status: Optional[str] = None, limit: int = 100, current_user: dict = Depends(get_current_user)):
    query = {}
    if status:
        query["status"] = status
    if current_user["role"] == "company":
        query["company_id"] = current_user["id"]
    
    # Use aggregation to get application counts in one query
    pipeline = [
        {"$match": query},
        {"$limit": limit},
        {"$lookup": {
            "from": "applications",
            "localField": "id",
            "foreignField": "job_id",
            "as": "applications"
        }},
        {"$addFields": {
            "applications_count": {"$size": "$applications"}
        }},
        {"$project": {
            "_id": 0,
            "applications": 0
        }}
    ]
    
    jobs = await db.jobs.aggregate(pipeline).to_list(limit)
    
    return [JobResponse(**job) for job in jobs]

@api_router.get("/jobs/{job_id}", response_model=JobResponse)
async def get_job(job_id: str, current_user: dict = Depends(get_current_user)):
    job = await db.jobs.find_one({"id": job_id}, {"_id": 0})
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    count = await db.applications.count_documents({"job_id": job_id})
    job["applications_count"] = count
    
    return JobResponse(**job)

@api_router.post("/resumes/upload")
async def upload_resume(file: UploadFile = File(...), current_user: dict = Depends(get_current_user)):
    if current_user["role"] not in ["candidate", "recruiter"]:
        raise HTTPException(status_code=403, detail="Only candidates and recruiters can upload resumes")
    
    # Read file content
    content = await file.read()
    
    # Parse resume with AI
    parsed_data = await parse_resume_with_ai(content, file.filename)
    
    # Calculate overall score based on parsed data
    skills_count = len(parsed_data.get('skills', []))
    experience_years = parsed_data.get('experience_years', 0)
    education_count = len(parsed_data.get('education', []))
    
    overall_score = min(100, (skills_count * 5) + (experience_years * 3) + (education_count * 10))
    
    resume_id = str(uuid.uuid4())
    resume_doc = {
        "id": resume_id,
        "candidate_id": current_user["id"],
        "file_name": file.filename,
        "parsed_data": parsed_data,
        "overall_score": overall_score,
        "skills": parsed_data.get('skills', []),
        "experience_years": experience_years,
        "education": parsed_data.get('education', []),
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.resumes.insert_one(resume_doc)
    
    return ResumeAnalysis(**{k: v for k, v in resume_doc.items() if k != "_id"})

@api_router.get("/resumes", response_model=List[ResumeAnalysis])
async def get_resumes(limit: int = 100, current_user: dict = Depends(get_current_user)):
    query = {}
    if current_user["role"] == "candidate":
        query["candidate_id"] = current_user["id"]
    
    resumes = await db.resumes.find(query, {"_id": 0}).limit(limit).to_list(limit)
    return [ResumeAnalysis(**r) for r in resumes]

@api_router.post("/applications", response_model=ApplicationResponse)
async def create_application(app: ApplicationCreate, current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "candidate":
        raise HTTPException(status_code=403, detail="Only candidates can apply")
    
    # Check if already applied
    existing = await db.applications.find_one({
        "job_id": app.job_id,
        "candidate_id": current_user["id"]
    })
    if existing:
        raise HTTPException(status_code=400, detail="Already applied to this job")
    
    # Get job and resume
    job = await db.jobs.find_one({"id": app.job_id}, {"_id": 0})
    resume = await db.resumes.find_one({"id": app.resume_id}, {"_id": 0})
    
    if not job or not resume:
        raise HTTPException(status_code=404, detail="Job or resume not found")
    
    # Score resume against job
    job_desc = f"{job['title']} - {job['description']} Requirements: {' '.join(job['requirements'])}"
    score_result = await score_resume_with_ai(resume['parsed_data'], job_desc)
    
    app_id = str(uuid.uuid4())
    app_doc = {
        "id": app_id,
        "job_id": app.job_id,
        "job_title": job["title"],
        "candidate_id": current_user["id"],
        "candidate_name": current_user["full_name"],
        "resume_id": app.resume_id,
        "match_score": score_result.get('match_score', 50),
        "score_details": score_result,
        "status": "pending",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.applications.insert_one(app_doc)
    
    return ApplicationResponse(**{k: v for k, v in app_doc.items() if k not in ["_id", "score_details"]})

@api_router.get("/applications", response_model=List[ApplicationResponse])
async def get_applications(job_id: Optional[str] = None, limit: int = 100, current_user: dict = Depends(get_current_user)):
    query = {}
    
    if current_user["role"] == "candidate":
        query["candidate_id"] = current_user["id"]
    elif current_user["role"] == "company":
        # Use aggregation to efficiently get applications for company's jobs
        pipeline = [
            {"$match": {"company_id": current_user["id"]}},
            {"$project": {"id": 1, "_id": 0}},
            {"$limit": limit}
        ]
        jobs = await db.jobs.aggregate(pipeline).to_list(limit)
        job_ids = [j["id"] for j in jobs]
        query["job_id"] = {"$in": job_ids}
    
    if job_id:
        query["job_id"] = job_id
    
    applications = await db.applications.find(query, {"_id": 0}).sort("match_score", -1).limit(limit).to_list(limit)
    return [ApplicationResponse(**{k: v for k, v in app.items() if k != "score_details"}) for app in applications]

@api_router.patch("/applications/{app_id}/status")
async def update_application_status(app_id: str, status: str, current_user: dict = Depends(get_current_user)):
    if current_user["role"] not in ["company", "admin"]:
        raise HTTPException(status_code=403, detail="Only companies can update application status")
    
    result = await db.applications.update_one(
        {"id": app_id},
        {"$set": {"status": status}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Application not found")
    
    return {"message": "Status updated successfully"}

@api_router.post("/referrals", response_model=ReferralResponse)
async def create_referral(referral: ReferralCreate, current_user: dict = Depends(get_current_user)):
    if current_user["role"] not in ["recruiter", "employee"]:
        raise HTTPException(status_code=403, detail="Only recruiters and employees can make referrals")
    
    job = await db.jobs.find_one({"id": referral.job_id}, {"_id": 0})
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    referral_id = str(uuid.uuid4())
    referral_doc = {
        "id": referral_id,
        "job_id": referral.job_id,
        "job_title": job["title"],
        "referrer_id": current_user["id"],
        "referrer_name": current_user["full_name"],
        "candidate_email": referral.candidate_email,
        "candidate_name": referral.candidate_name,
        "candidate_phone": referral.candidate_phone,
        "status": "pending",
        "reward_amount": 5000,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.referrals.insert_one(referral_doc)
    
    return ReferralResponse(**{k: v for k, v in referral_doc.items() if k != "_id"})

@api_router.get("/referrals", response_model=List[ReferralResponse])
async def get_referrals(limit: int = 100, current_user: dict = Depends(get_current_user)):
    query = {}
    if current_user["role"] in ["recruiter", "employee"]:
        query["referrer_id"] = current_user["id"]
    
    referrals = await db.referrals.find(query, {"_id": 0}).limit(limit).to_list(limit)
    return [ReferralResponse(**r) for r in referrals]

@api_router.get("/leaderboard", response_model=List[LeaderboardEntry])
async def get_leaderboard(limit: int = 100):
    # Use aggregation to join user data in one query
    pipeline = [
        {"$group": {
            "_id": "$referrer_id",
            "total_referrals": {"$sum": 1},
            "successful_referrals": {
                "$sum": {"$cond": [{"$eq": ["$status", "hired"]}, 1, 0]}
            },
            "total_earnings": {
                "$sum": {"$cond": [{"$eq": ["$status", "hired"]}, "$reward_amount", 0]}
            }
        }},
        {"$lookup": {
            "from": "users",
            "localField": "_id",
            "foreignField": "id",
            "as": "user_info"
        }},
        {"$unwind": "$user_info"},
        {"$project": {
            "user_id": "$_id",
            "user_name": "$user_info.full_name",
            "role": "$user_info.role",
            "total_referrals": 1,
            "successful_referrals": 1,
            "total_earnings": 1,
            "_id": 0
        }},
        {"$sort": {"successful_referrals": -1, "total_earnings": -1}},
        {"$limit": limit}
    ]
    
    leaderboard = await db.referrals.aggregate(pipeline).to_list(limit)
    
    # Assign ranks
    for idx, entry in enumerate(leaderboard):
        entry["rank"] = idx + 1
    
    return [LeaderboardEntry(**entry) for entry in leaderboard]

@api_router.get("/dashboard/stats", response_model=DashboardStats)
async def get_dashboard_stats(current_user: dict = Depends(get_current_user)):
    stats = DashboardStats()
    
    if current_user["role"] == "admin":
        stats.total_jobs = await db.jobs.count_documents({})
        stats.active_jobs = await db.jobs.count_documents({"status": "active"})
        stats.total_applications = await db.applications.count_documents({})
        stats.pending_applications = await db.applications.count_documents({"status": "pending"})
        stats.total_candidates = await db.users.count_documents({"role": "candidate"})
        stats.total_recruiters = await db.users.count_documents({"role": "recruiter"})
        stats.total_companies = await db.users.count_documents({"role": "company"})
    elif current_user["role"] == "company":
        stats.total_jobs = await db.jobs.count_documents({"company_id": current_user["id"]})
        stats.active_jobs = await db.jobs.count_documents({"company_id": current_user["id"], "status": "active"})
        
        # Use aggregation to count applications across all company jobs
        pipeline = [
            {"$match": {"company_id": current_user["id"]}},
            {"$lookup": {
                "from": "applications",
                "localField": "id",
                "foreignField": "job_id",
                "as": "apps"
            }},
            {"$unwind": {"path": "$apps", "preserveNullAndEmptyArrays": False}},
            {"$facet": {
                "total": [{"$count": "count"}],
                "pending": [
                    {"$match": {"apps.status": "pending"}},
                    {"$count": "count"}
                ]
            }}
        ]
        
        result = await db.jobs.aggregate(pipeline).to_list(1)
        if result:
            stats.total_applications = result[0]["total"][0]["count"] if result[0]["total"] else 0
            stats.pending_applications = result[0]["pending"][0]["count"] if result[0]["pending"] else 0
    elif current_user["role"] == "candidate":
        stats.total_applications = await db.applications.count_documents({"candidate_id": current_user["id"]})
        stats.active_jobs = await db.jobs.count_documents({"status": "active"})
    
    return stats

@api_router.get("/users", response_model=List[UserResponse])
async def get_users(role: Optional[str] = None, limit: int = 100, current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    query = {}
    if role:
        query["role"] = role
    
    users = await db.users.find(query, {"_id": 0, "password": 0}).limit(limit).to_list(limit)
    return [UserResponse(**u) for u in users]


# ============= DOCUMENT MANAGEMENT ENDPOINTS =============

@api_router.post("/documents/upload")
async def upload_document(
    file: UploadFile = File(...),
    category: str = "general",
    related_to: str = "",
    current_user: dict = Depends(get_current_user)
):
    """Upload and store document"""
    try:
        file_id = str(uuid.uuid4())
        file_extension = file.filename.split('.')[-1]
        filename = f"{file_id}.{file_extension}"
        filepath = os.path.join(UPLOAD_DIR, filename)
        
        # Save file
        with open(filepath, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Get file size
        file_size = os.path.getsize(filepath)
        
        # Create document record
        doc_record = {
            "id": file_id,
            "name": file.filename,
            "file_path": filepath,
            "file_type": file_extension,
            "file_size": file_size,
            "uploaded_by": current_user["id"],
            "uploaded_at": datetime.now(timezone.utc).isoformat(),
            "category": category,
            "related_to": related_to,
            "status": "active"
        }
        
        await db.documents.insert_one(doc_record)
        
        return {"message": "Document uploaded successfully", "document": {k: v for k, v in doc_record.items() if k != "_id"}}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@api_router.get("/documents")
async def get_documents(
    category: Optional[str] = None,
    related_to: Optional[str] = None,
    limit: int = 100,
    current_user: dict = Depends(get_current_user)
):
    """Get documents with filters"""
    query = {}
    if category:
        query["category"] = category
    if related_to:
        query["related_to"] = related_to
    
    documents = await db.documents.find(query, {"_id": 0}).limit(limit).to_list(limit)
    return documents

@api_router.get("/documents/{doc_id}/download")
async def download_document(doc_id: str, current_user: dict = Depends(get_current_user)):
    """Download document file"""
    doc = await db.documents.find_one({"id": doc_id}, {"_id": 0})
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    if not os.path.exists(doc["file_path"]):
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(
        doc["file_path"],
        filename=doc["name"],
        media_type="application/octet-stream"
    )

# ============= ATS (Applicant Tracking System) ENDPOINTS =============

@api_router.get("/ats/stages")
async def get_ats_stages():
    """Get all ATS stages"""
    return ATS_STAGES

@api_router.get("/ats/pipeline/{application_id}")
async def get_ats_pipeline(application_id: str, current_user: dict = Depends(get_current_user)):
    """Get ATS pipeline for an application"""
    pipeline = await db.ats_pipelines.find_one({"application_id": application_id}, {"_id": 0})
    if not pipeline:
        # Create initial pipeline
        application = await db.applications.find_one({"id": application_id}, {"_id": 0})
        if not application:
            raise HTTPException(status_code=404, detail="Application not found")
        
        pipeline = {
            "application_id": application_id,
            "current_stage": "applied",
            "stage_history": [{
                "stage": "applied",
                "entered_at": application["created_at"],
                "notes": "Application submitted"
            }],
            "days_in_current_stage": 0,
            "total_days_in_pipeline": 0,
            "next_action": "Review application",
            "scheduled_interviews": []
        }
        await db.ats_pipelines.insert_one(pipeline)
    
    return {k: v for k, v in pipeline.items() if k != "_id"}

@api_router.post("/ats/pipeline/{application_id}/move")
async def move_ats_stage(
    application_id: str,
    new_stage: str,
    notes: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Move application to new stage"""
    if current_user["role"] not in ["company", "admin"]:
        raise HTTPException(status_code=403, detail="Only companies can move stages")
    
    pipeline = await db.ats_pipelines.find_one({"application_id": application_id})
    if not pipeline:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    
    # Update stage history
    stage_entry = {
        "stage": new_stage,
        "entered_at": datetime.now(timezone.utc).isoformat(),
        "notes": notes or f"Moved to {new_stage}"
    }
    
    await db.ats_pipelines.update_one(
        {"application_id": application_id},
        {
            "$set": {"current_stage": new_stage},
            "$push": {"stage_history": stage_entry}
        }
    )
    
    # Update application status
    await db.applications.update_one(
        {"id": application_id},
        {"$set": {"status": new_stage}}
    )
    
    return {"message": "Stage updated successfully"}

# ============= BGV (BACKGROUND VERIFICATION) ENDPOINTS =============

@api_router.post("/bgv/request")
async def create_bgv_request(
    application_id: str,
    verification_types: List[str],
    current_user: dict = Depends(get_current_user)
):
    """Create background verification request"""
    if current_user["role"] not in ["company", "admin"]:
        raise HTTPException(status_code=403, detail="Only companies can request BGV")
    
    application = await db.applications.find_one({"id": application_id}, {"_id": 0})
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    
    bgv_id = str(uuid.uuid4())
    bgv_request = {
        "id": bgv_id,
        "candidate_id": application["candidate_id"],
        "candidate_name": application["candidate_name"],
        "application_id": application_id,
        "requested_by": current_user["id"],
        "requested_at": datetime.now(timezone.utc).isoformat(),
        "status": "pending",
        "verification_types": verification_types,
        "checks_completed": [],
        "checks_pending": verification_types,
        "remarks": None,
        "completed_at": None,
        "verified_by": None
    }
    
    await db.bgv_requests.insert_one(bgv_request)
    
    return {"message": "BGV request created", "bgv_id": bgv_id}

@api_router.get("/bgv/requests")
async def get_bgv_requests(
    status: Optional[str] = None,
    limit: int = 100,
    current_user: dict = Depends(get_current_user)
):
    """Get BGV requests"""
    query = {}
    if status:
        query["status"] = status
    if current_user["role"] == "company":
        query["requested_by"] = current_user["id"]
    
    requests = await db.bgv_requests.find(query, {"_id": 0}).limit(limit).to_list(limit)
    return requests

@api_router.post("/bgv/{bgv_id}/check")
async def complete_bgv_check(
    bgv_id: str,
    check_type: str,
    check_status: str,
    verified_data: dict,
    remarks: str,
    current_user: dict = Depends(get_current_user)
):
    """Complete a BGV check"""
    if current_user["role"] not in ["admin", "bgv"]:
        raise HTTPException(status_code=403, detail="Only BGV team can complete checks")
    
    bgv_request = await db.bgv_requests.find_one({"id": bgv_id})
    if not bgv_request:
        raise HTTPException(status_code=404, detail="BGV request not found")
    
    # Update BGV request
    await db.bgv_requests.update_one(
        {"id": bgv_id},
        {
            "$push": {"checks_completed": check_type},
            "$pull": {"checks_pending": check_type},
            "$set": {
                "status": "in_progress",
                "verified_by": current_user["id"]
            }
        }
    )
    
    # Check if all completed
    updated_bgv = await db.bgv_requests.find_one({"id": bgv_id})
    if not updated_bgv["checks_pending"]:
        await db.bgv_requests.update_one(
            {"id": bgv_id},
            {
                "$set": {
                    "status": "completed",
                    "completed_at": datetime.now(timezone.utc).isoformat()
                }
            }
        )
    
    return {"message": "BGV check completed"}

# ============= 91-DAY TRACKING ENDPOINTS =============

@api_router.post("/tracking/start")
async def start_candidate_tracking(
    application_id: str,
    join_date: str,
    current_user: dict = Depends(get_current_user)
):
    """Start 91-day tracking for hired candidate"""
    if current_user["role"] not in ["company", "admin"]:
        raise HTTPException(status_code=403, detail="Only companies can start tracking")
    
    application = await db.applications.find_one({"id": application_id}, {"_id": 0})
    if not application or application["status"] != "hired":
        raise HTTPException(status_code=400, detail="Application must be in hired status")
    
    tracking_id = str(uuid.uuid4())
    join_date_obj = datetime.fromisoformat(join_date)
    end_date = join_date_obj + timedelta(days=91)
    
    # Create milestones
    milestones = [
        {"day": 7, "title": "Week 1 Check-in", "status": "pending"},
        {"day": 30, "title": "Month 1 Review", "status": "pending"},
        {"day": 60, "title": "Month 2 Review", "status": "pending"},
        {"day": 91, "title": "Final Review", "status": "pending"},
    ]
    
    tracking = {
        "id": tracking_id,
        "candidate_id": application["candidate_id"],
        "application_id": application_id,
        "job_id": application["job_id"],
        "company_id": current_user["id"],
        "join_date": join_date,
        "tracking_start_date": join_date,
        "tracking_end_date": end_date.isoformat(),
        "current_day": 0,
        "status": "tracking",
        "milestones": milestones,
        "feedback_records": [],
        "invoice_eligible": False,
        "invoice_generated": False
    }
    
    await db.candidate_tracking.insert_one(tracking)
    
    return {"message": "Tracking started", "tracking_id": tracking_id}

@api_router.get("/tracking")
async def get_tracking_records(
    status: Optional[str] = None,
    limit: int = 100,
    current_user: dict = Depends(get_current_user)
):
    """Get tracking records"""
    query = {}
    if status:
        query["status"] = status
    if current_user["role"] == "company":
        query["company_id"] = current_user["id"]
    elif current_user["role"] == "candidate":
        query["candidate_id"] = current_user["id"]
    
    # Update current_day for active tracking
    tracking_records = await db.candidate_tracking.find(query, {"_id": 0}).limit(limit).to_list(limit)
    
    for record in tracking_records:
        if record["status"] == "tracking":
            join_date = datetime.fromisoformat(record["join_date"])
            current_day = (datetime.now(timezone.utc).replace(tzinfo=None) - join_date).days
            record["current_day"] = current_day
            
            # Check if 91 days completed
            if current_day >= 91:
                await db.candidate_tracking.update_one(
                    {"id": record["id"]},
                    {"$set": {"status": "completed", "invoice_eligible": True, "current_day": current_day}}
                )
                record["status"] = "completed"
                record["invoice_eligible"] = True
    
    return tracking_records

@api_router.post("/tracking/{tracking_id}/milestone")
async def complete_milestone(
    tracking_id: str,
    day: int,
    feedback: str,
    current_user: dict = Depends(get_current_user)
):
    """Complete a tracking milestone"""
    if current_user["role"] not in ["company", "admin"]:
        raise HTTPException(status_code=403, detail="Only companies can complete milestones")
    
    tracking = await db.candidate_tracking.find_one({"id": tracking_id})
    if not tracking:
        raise HTTPException(status_code=404, detail="Tracking record not found")
    
    # Update milestone
    milestones = tracking["milestones"]
    for milestone in milestones:
        if milestone["day"] == day:
            milestone["status"] = "completed"
            milestone["completed_at"] = datetime.now(timezone.utc).isoformat()
            milestone["feedback"] = feedback
    
    # Add feedback record
    feedback_record = {
        "day": day,
        "feedback": feedback,
        "recorded_at": datetime.now(timezone.utc).isoformat(),
        "recorded_by": current_user["id"]
    }
    
    await db.candidate_tracking.update_one(
        {"id": tracking_id},
        {
            "$set": {"milestones": milestones},
            "$push": {"feedback_records": feedback_record}
        }
    )
    
    return {"message": "Milestone completed"}

# ============= INVOICE ENDPOINTS =============

@api_router.post("/invoices/generate")
async def generate_invoice(
    tracking_id: str,
    amount: float,
    payment_terms: str = "Net 30",
    current_user: dict = Depends(get_current_user)
):
    """Generate invoice for completed tracking"""
    if current_user["role"] not in ["admin"]:
        raise HTTPException(status_code=403, detail="Only admin can generate invoices")
    
    tracking = await db.candidate_tracking.find_one({"id": tracking_id}, {"_id": 0})
    if not tracking:
        raise HTTPException(status_code=404, detail="Tracking record not found")
    
    if not tracking["invoice_eligible"]:
        raise HTTPException(status_code=400, detail="Tracking not eligible for invoice")
    
    if tracking["invoice_generated"]:
        raise HTTPException(status_code=400, detail="Invoice already generated")
    
    # Get company and job details
    company = await db.users.find_one({"id": tracking["company_id"]}, {"_id": 0})
    application = await db.applications.find_one({"id": tracking["application_id"]}, {"_id": 0})
    
    invoice_id = str(uuid.uuid4())
    invoice_number = f"INV-{datetime.now().strftime('%Y%m')}-{str(uuid.uuid4())[:8].upper()}"
    
    tax_rate = 0.18  # 18% GST
    tax_amount = amount * tax_rate
    total_amount = amount + tax_amount
    
    invoice_data = {
        "id": invoice_id,
        "invoice_number": invoice_number,
        "company_id": tracking["company_id"],
        "company_name": company["full_name"],
        "candidate_tracking_id": tracking_id,
        "candidate_name": application["candidate_name"],
        "job_title": application["job_title"],
        "amount": amount,
        "tax_amount": tax_amount,
        "total_amount": total_amount,
        "currency": "INR",
        "issue_date": datetime.now().strftime("%Y-%m-%d"),
        "due_date": (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d"),
        "status": "sent",
        "payment_terms": payment_terms,
        "items": [
            {
                "description": f"Recruitment services for {application['candidate_name']} - {application['job_title']}",
                "quantity": 1,
                "rate": amount,
                "amount": amount
            }
        ],
        "notes": "Thank you for using HiringReferrals platform. Payment is due within 30 days."
    }
    
    # Generate PDF
    try:
        pdf_path = invoice_generator.generate_invoice(invoice_data)
        invoice_data["pdf_path"] = pdf_path
    except Exception as e:
        logging.error(f"PDF generation failed: {str(e)}")
    
    await db.invoices.insert_one(invoice_data)
    
    # Mark tracking as invoiced
    await db.candidate_tracking.update_one(
        {"id": tracking_id},
        {"$set": {"invoice_generated": True}}
    )
    
    return {"message": "Invoice generated", "invoice_id": invoice_id, "invoice_number": invoice_number}

@api_router.get("/invoices")
async def get_invoices(
    status: Optional[str] = None,
    limit: int = 100,
    current_user: dict = Depends(get_current_user)
):
    """Get invoices"""
    query = {}
    if status:
        query["status"] = status
    if current_user["role"] == "company":
        query["company_id"] = current_user["id"]
    
    invoices = await db.invoices.find(query, {"_id": 0}).limit(limit).to_list(limit)
    return invoices

@api_router.get("/invoices/{invoice_id}/download")
async def download_invoice(invoice_id: str, current_user: dict = Depends(get_current_user)):
    """Download invoice PDF"""
    invoice = await db.invoices.find_one({"id": invoice_id}, {"_id": 0})
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    if not invoice.get("pdf_path") or not os.path.exists(invoice["pdf_path"]):
        raise HTTPException(status_code=404, detail="Invoice PDF not found")
    
    return FileResponse(
        invoice["pdf_path"],
        filename=f"invoice_{invoice['invoice_number']}.pdf",
        media_type="application/pdf"
    )

# ============= AUTOMATION ENDPOINTS =============

@api_router.post("/automation/rules")
async def create_automation_rule(
    name: str,
    description: str,
    trigger_type: str,
    trigger_config: dict,
    actions: List[dict],
    current_user: dict = Depends(get_current_user)
):
    """Create automation rule"""
    if current_user["role"] not in ["admin"]:
        raise HTTPException(status_code=403, detail="Only admin can create automation rules")
    
    rule_id = str(uuid.uuid4())
    rule = {
        "id": rule_id,
        "name": name,
        "description": description,
        "trigger_type": trigger_type,
        "trigger_config": trigger_config,
        "actions": actions,
        "is_active": True,
        "created_by": current_user["id"],
        "created_at": datetime.now(timezone.utc).isoformat(),
        "last_run": None,
        "run_count": 0
    }
    
    await db.automation_rules.insert_one(rule)
    
    return {"message": "Automation rule created", "rule_id": rule_id}

@api_router.get("/automation/rules")
async def get_automation_rules(limit: int = 100, current_user: dict = Depends(get_current_user)):
    """Get automation rules"""
    if current_user["role"] not in ["admin"]:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    rules = await db.automation_rules.find({}, {"_id": 0}).limit(limit).to_list(limit)
    return rules

# ============= BACKUP & EXPORT ENDPOINTS =============

@api_router.post("/admin/backup")
async def create_backup(current_user: dict = Depends(get_current_user)):
    """Create full database backup"""
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    collections = [
        "users", "jobs", "applications", "resumes", "referrals",
        "notifications", "documents", "ats_pipelines", "bgv_requests",
        "candidate_tracking", "invoices", "automation_rules"
    ]
    
    backup_path = await backup_manager.create_full_backup(db, collections)
    
    return {
        "message": "Backup created successfully",
        "backup_path": backup_path,
        "created_at": datetime.now().isoformat()
    }

@api_router.get("/admin/backups")
async def list_backups(current_user: dict = Depends(get_current_user)):
    """List all backups"""
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    backups = backup_manager.list_backups()
    return backups

@api_router.get("/admin/backups/{filename}/download")
async def download_backup(filename: str, current_user: dict = Depends(get_current_user)):
    """Download backup file"""
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    backup_path = os.path.join("/app/backups", filename)
    if not os.path.exists(backup_path):
        raise HTTPException(status_code=404, detail="Backup not found")
    
    return FileResponse(backup_path, filename=filename, media_type="application/zip")

@api_router.post("/admin/export-code")
async def export_code(current_user: dict = Depends(get_current_user)):
    """Export complete codebase as ZIP"""
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    archive_path = code_exporter.create_code_archive()
    
    return {
        "message": "Code exported successfully",
        "archive_path": archive_path,
        "created_at": datetime.now().isoformat()
    }

@api_router.get("/admin/exports")
async def list_exports(current_user: dict = Depends(get_current_user)):
    """List all code exports"""
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    exports = code_exporter.list_exports()
    return exports

@api_router.get("/admin/exports/{filename}/download")
async def download_export(filename: str, current_user: dict = Depends(get_current_user)):
    """Download code export"""
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    export_path = os.path.join("/app/exports", filename)
    if not os.path.exists(export_path):
        raise HTTPException(status_code=404, detail="Export not found")
    
    return FileResponse(export_path, filename=filename, media_type="application/zip")

app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()