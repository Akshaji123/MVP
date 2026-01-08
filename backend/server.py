from fastapi import FastAPI, APIRouter, HTTPException, Depends, status, UploadFile, File
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
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

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# JWT Configuration
JWT_SECRET = os.environ.get('JWT_SECRET', 'your-secret-key-change-in-production')
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 720

# Security
security = HTTPBearer()

app = FastAPI()
api_router = APIRouter(prefix="/api")

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
    user = await db.users.find_one({"id": payload["user_id"]}, {"_id": 0})
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
    existing = await db.users.find_one({"email": user.email}, {"_id": 0})
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
async def get_resumes(current_user: dict = Depends(get_current_user)):
    query = {}
    if current_user["role"] == "candidate":
        query["candidate_id"] = current_user["id"]
    
    resumes = await db.resumes.find(query, {"_id": 0}).to_list(1000)
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
async def get_applications(job_id: Optional[str] = None, current_user: dict = Depends(get_current_user)):
    query = {}
    
    if current_user["role"] == "candidate":
        query["candidate_id"] = current_user["id"]
    elif current_user["role"] == "company":
        jobs = await db.jobs.find({"company_id": current_user["id"]}, {"_id": 0, "id": 1}).to_list(1000)
        job_ids = [j["id"] for j in jobs]
        query["job_id"] = {"$in": job_ids}
    
    if job_id:
        query["job_id"] = job_id
    
    applications = await db.applications.find(query, {"_id": 0}).sort("match_score", -1).to_list(1000)
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
async def get_referrals(current_user: dict = Depends(get_current_user)):
    query = {}
    if current_user["role"] in ["recruiter", "employee"]:
        query["referrer_id"] = current_user["id"]
    
    referrals = await db.referrals.find(query, {"_id": 0}).to_list(1000)
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
        
        jobs = await db.jobs.find({"company_id": current_user["id"]}, {"_id": 0, "id": 1}).to_list(1000)
        job_ids = [j["id"] for j in jobs]
        
        stats.total_applications = await db.applications.count_documents({"job_id": {"$in": job_ids}})
        stats.pending_applications = await db.applications.count_documents({
            "job_id": {"$in": job_ids},
            "status": "pending"
        })
    elif current_user["role"] == "candidate":
        stats.total_applications = await db.applications.count_documents({"candidate_id": current_user["id"]})
        stats.active_jobs = await db.jobs.count_documents({"status": "active"})
    
    return stats

@api_router.get("/users", response_model=List[UserResponse])
async def get_users(role: Optional[str] = None, current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    query = {}
    if role:
        query["role"] = role
    
    users = await db.users.find(query, {"_id": 0, "password": 0}).to_list(1000)
    return [UserResponse(**u) for u in users]

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