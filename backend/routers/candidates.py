"""
Candidates API Router
HiringReferrals Platform
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import uuid

router = APIRouter(prefix="/candidates", tags=["Candidates"])


# ============= PYDANTIC MODELS =============

class EducationModel(BaseModel):
    degree: str
    institution: str
    field: Optional[str] = None
    start_year: Optional[int] = None
    end_year: Optional[int] = None
    grade: Optional[str] = None


class WorkHistoryModel(BaseModel):
    company: str
    title: str
    start_date: str
    end_date: Optional[str] = None
    is_current: bool = False
    description: Optional[str] = None
    skills_used: List[str] = []


class CandidateCreate(BaseModel):
    user_id: str
    resume_url: Optional[str] = None
    portfolio_url: Optional[str] = None
    current_title: Optional[str] = Field(None, max_length=200)
    current_company: Optional[str] = Field(None, max_length=200)
    experience_years: int = Field(0, ge=0, le=50)
    skills: List[str] = []
    education: List[EducationModel] = []
    work_history: List[WorkHistoryModel] = []
    expected_salary: Optional[float] = Field(None, ge=0)
    current_salary: Optional[float] = Field(None, ge=0)
    preferred_locations: List[str] = []
    availability: str = Field("immediate", pattern="^(immediate|2weeks|1month|3months)$")
    is_available_for_referral: bool = True


class CandidateUpdate(BaseModel):
    resume_url: Optional[str] = None
    portfolio_url: Optional[str] = None
    current_title: Optional[str] = Field(None, max_length=200)
    current_company: Optional[str] = Field(None, max_length=200)
    experience_years: Optional[int] = Field(None, ge=0, le=50)
    skills: Optional[List[str]] = None
    education: Optional[List[EducationModel]] = None
    work_history: Optional[List[WorkHistoryModel]] = None
    expected_salary: Optional[float] = Field(None, ge=0)
    current_salary: Optional[float] = Field(None, ge=0)
    preferred_locations: Optional[List[str]] = None
    availability: Optional[str] = Field(None, pattern="^(immediate|2weeks|1month|3months)$")
    is_available_for_referral: Optional[bool] = None


class CandidateResponse(BaseModel):
    id: str
    user_id: str
    resume_url: Optional[str] = None
    portfolio_url: Optional[str] = None
    current_title: Optional[str] = None
    current_company: Optional[str] = None
    experience_years: int = 0
    skills: List[str] = []
    education: List[Dict[str, Any]] = []
    work_history: List[Dict[str, Any]] = []
    expected_salary: Optional[float] = None
    current_salary: Optional[float] = None
    preferred_locations: List[str] = []
    availability: str = "immediate"
    is_available_for_referral: bool = True
    overall_score: Optional[int] = None
    created_at: str
    updated_at: str


# ============= ROUTE HANDLERS =============

def get_candidate_router(db, get_current_user):
    """Create router with database dependency"""
    
    @router.post("", response_model=CandidateResponse)
    async def create_candidate(
        candidate: CandidateCreate,
        current_user: dict = Depends(get_current_user)
    ):
        """Create a new candidate profile"""
        # Check if candidate profile already exists
        existing = await db.candidates.find_one({"user_id": candidate.user_id})
        if existing:
            raise HTTPException(status_code=400, detail="Candidate profile already exists")
        
        candidate_doc = {
            "id": str(uuid.uuid4()),
            **candidate.dict(),
            "certifications": [],
            "job_preferences": {},
            "visibility_settings": {"public": True},
            "parsed_resume_data": {},
            "overall_score": None,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        await db.candidates.insert_one(candidate_doc)
        return candidate_doc
    
    @router.get("", response_model=List[CandidateResponse])
    async def list_candidates(
        skip: int = 0,
        limit: int = 50,
        skills: Optional[str] = None,
        min_experience: Optional[int] = None,
        max_experience: Optional[int] = None,
        availability: Optional[str] = None,
        current_user: dict = Depends(get_current_user)
    ):
        """List candidates with filters"""
        if current_user["role"] not in ["admin", "super_admin", "recruiter", "client"]:
            raise HTTPException(status_code=403, detail="Access denied")
        
        query = {"is_available_for_referral": True}
        
        if skills:
            skill_list = [s.strip() for s in skills.split(",")]
            query["skills"] = {"$in": skill_list}
        
        if min_experience is not None:
            query["experience_years"] = {"$gte": min_experience}
        
        if max_experience is not None:
            if "experience_years" in query:
                query["experience_years"]["$lte"] = max_experience
            else:
                query["experience_years"] = {"$lte": max_experience}
        
        if availability:
            query["availability"] = availability
        
        candidates = await db.candidates.find(
            query, {"_id": 0}
        ).skip(skip).limit(limit).to_list(limit)
        
        return candidates
    
    @router.get("/me", response_model=CandidateResponse)
    async def get_my_candidate_profile(
        current_user: dict = Depends(get_current_user)
    ):
        """Get current user's candidate profile"""
        candidate = await db.candidates.find_one(
            {"user_id": current_user["id"]}, {"_id": 0}
        )
        if not candidate:
            raise HTTPException(status_code=404, detail="Candidate profile not found")
        return candidate
    
    @router.get("/{candidate_id}", response_model=CandidateResponse)
    async def get_candidate(
        candidate_id: str,
        current_user: dict = Depends(get_current_user)
    ):
        """Get candidate by ID"""
        candidate = await db.candidates.find_one({"id": candidate_id}, {"_id": 0})
        if not candidate:
            raise HTTPException(status_code=404, detail="Candidate not found")
        return candidate
    
    @router.put("/{candidate_id}", response_model=CandidateResponse)
    async def update_candidate(
        candidate_id: str,
        candidate: CandidateUpdate,
        current_user: dict = Depends(get_current_user)
    ):
        """Update candidate profile"""
        existing = await db.candidates.find_one({"id": candidate_id})
        if not existing:
            raise HTTPException(status_code=404, detail="Candidate not found")
        
        # Only allow owner or admin to update
        if existing["user_id"] != current_user["id"] and current_user["role"] not in ["admin", "super_admin"]:
            raise HTTPException(status_code=403, detail="Access denied")
        
        update_data = candidate.dict(exclude_none=True)
        update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
        
        await db.candidates.update_one(
            {"id": candidate_id},
            {"$set": update_data}
        )
        
        updated = await db.candidates.find_one({"id": candidate_id}, {"_id": 0})
        return updated
    
    @router.get("/{candidate_id}/applications")
    async def get_candidate_applications(
        candidate_id: str,
        status: Optional[str] = None,
        current_user: dict = Depends(get_current_user)
    ):
        """Get applications for a candidate"""
        candidate = await db.candidates.find_one({"id": candidate_id})
        if not candidate:
            raise HTTPException(status_code=404, detail="Candidate not found")
        
        # Only allow owner or admin
        if candidate["user_id"] != current_user["id"] and current_user["role"] not in ["admin", "super_admin", "recruiter"]:
            raise HTTPException(status_code=403, detail="Access denied")
        
        query = {"candidate_id": candidate_id}
        if status:
            query["application_status"] = status
        
        applications = await db.applications.find(query, {"_id": 0}).to_list(100)
        return {"candidate_id": candidate_id, "applications": applications}
    
    @router.post("/{candidate_id}/skills")
    async def add_skills(
        candidate_id: str,
        skills: List[str],
        current_user: dict = Depends(get_current_user)
    ):
        """Add skills to candidate profile"""
        candidate = await db.candidates.find_one({"id": candidate_id})
        if not candidate:
            raise HTTPException(status_code=404, detail="Candidate not found")
        
        if candidate["user_id"] != current_user["id"] and current_user["role"] not in ["admin", "super_admin"]:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Add unique skills
        existing_skills = set(candidate.get("skills", []))
        new_skills = existing_skills.union(set(skills))
        
        await db.candidates.update_one(
            {"id": candidate_id},
            {"$set": {"skills": list(new_skills), "updated_at": datetime.now(timezone.utc).isoformat()}}
        )
        
        return {"status": "updated", "skills": list(new_skills)}
    
    @router.get("/{candidate_id}/match-jobs")
    async def find_matching_jobs(
        candidate_id: str,
        limit: int = 20,
        current_user: dict = Depends(get_current_user)
    ):
        """Find matching jobs for a candidate"""
        candidate = await db.candidates.find_one({"id": candidate_id}, {"_id": 0})
        if not candidate:
            raise HTTPException(status_code=404, detail="Candidate not found")
        
        # Get active jobs
        jobs = await db.jobs.find(
            {"job_status": "published"},
            {"_id": 0}
        ).limit(100).to_list(100)
        
        # Simple matching based on skills
        candidate_skills = set(s.lower() for s in candidate.get("skills", []))
        matches = []
        
        for job in jobs:
            job_skills = set(s.lower() for s in job.get("skills_required", []))
            matching_skills = candidate_skills.intersection(job_skills)
            
            if matching_skills:
                match_score = (len(matching_skills) / len(job_skills)) * 100 if job_skills else 0
                matches.append({
                    "job_id": job["id"],
                    "job_title": job["title"],
                    "company_name": job.get("company_name"),
                    "location": job.get("location"),
                    "match_score": round(match_score, 1),
                    "matching_skills": list(matching_skills)
                })
        
        # Sort by match score
        matches.sort(key=lambda x: x["match_score"], reverse=True)
        
        return {"candidate_id": candidate_id, "matches": matches[:limit]}
    
    return router
