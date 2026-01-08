"""
Interviews API Router
HiringReferrals Platform
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import uuid

router = APIRouter(prefix="/interviews", tags=["Interviews"])


# ============= PYDANTIC MODELS =============

class InterviewCreate(BaseModel):
    application_id: str
    interview_type: str = Field(..., pattern="^(phone|video|onsite|technical|hr|panel|case_study)$")
    scheduled_at: str
    duration_minutes: int = Field(60, ge=15, le=480)
    interviewer_ids: List[str] = []
    location: Optional[str] = Field(None, max_length=200)
    meeting_link: Optional[str] = Field(None, max_length=500)
    notes: Optional[str] = None
    preparation_notes: Optional[str] = None


class InterviewUpdate(BaseModel):
    interview_type: Optional[str] = Field(None, pattern="^(phone|video|onsite|technical|hr|panel|case_study)$")
    scheduled_at: Optional[str] = None
    duration_minutes: Optional[int] = Field(None, ge=15, le=480)
    interviewer_ids: Optional[List[str]] = None
    location: Optional[str] = Field(None, max_length=200)
    meeting_link: Optional[str] = Field(None, max_length=500)
    interview_status: Optional[str] = Field(None, pattern="^(scheduled|completed|cancelled|rescheduled|no_show)$")
    notes: Optional[str] = None


class InterviewFeedbackModel(BaseModel):
    rating: int = Field(..., ge=1, le=10)
    technical_score: Optional[int] = Field(None, ge=1, le=10)
    communication_score: Optional[int] = Field(None, ge=1, le=10)
    problem_solving_score: Optional[int] = Field(None, ge=1, le=10)
    cultural_fit_score: Optional[int] = Field(None, ge=1, le=10)
    strengths: List[str] = []
    areas_of_improvement: List[str] = []
    comments: Optional[str] = None
    recommendation: str = Field("proceed", pattern="^(hire|reject|next_round|proceed|hold)$")


class InterviewResponse(BaseModel):
    id: str
    application_id: str
    candidate_id: str
    job_id: str
    interview_type: str
    interview_round: int
    scheduled_at: str
    duration_minutes: int
    interviewer_ids: List[str]
    interviewer_names: List[str]
    location: Optional[str] = None
    meeting_link: Optional[str] = None
    interview_status: str
    feedback: Optional[Dict[str, Any]] = None
    rating: Optional[int] = None
    scores: Dict[str, int] = {}
    recommendation: Optional[str] = None
    notes: Optional[str] = None
    scheduled_by: str
    created_at: str
    updated_at: str


# ============= ROUTE HANDLERS =============

def get_interview_router(db, get_current_user):
    """Create router with database dependency"""
    
    @router.post("", response_model=InterviewResponse)
    async def create_interview(
        interview: InterviewCreate,
        current_user: dict = Depends(get_current_user)
    ):
        """Schedule a new interview"""
        if current_user["role"] not in ["admin", "super_admin", "recruiter", "client"]:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Get application details
        application = await db.applications.find_one({"id": interview.application_id}, {"_id": 0})
        if not application:
            raise HTTPException(status_code=404, detail="Application not found")
        
        # Get existing interviews to determine round
        existing_interviews = await db.interviews.count_documents({
            "application_id": interview.application_id
        })
        interview_round = existing_interviews + 1
        
        # Get interviewer names
        interviewer_names = []
        for interviewer_id in interview.interviewer_ids:
            user = await db.users.find_one({"id": interviewer_id}, {"_id": 0, "full_name": 1})
            if user:
                interviewer_names.append(user.get("full_name", "Unknown"))
        
        interview_doc = {
            "id": str(uuid.uuid4()),
            "application_id": interview.application_id,
            "candidate_id": application["candidate_id"],
            "job_id": application["job_id"],
            "interview_type": interview.interview_type,
            "interview_round": interview_round,
            "scheduled_at": interview.scheduled_at,
            "duration_minutes": interview.duration_minutes,
            "interviewer_ids": interview.interviewer_ids,
            "interviewer_names": interviewer_names,
            "location": interview.location,
            "meeting_link": interview.meeting_link,
            "interview_status": "scheduled",
            "feedback": None,
            "rating": None,
            "scores": {},
            "recommendation": None,
            "notes": interview.notes,
            "preparation_notes": interview.preparation_notes,
            "scheduled_by": current_user["id"],
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        await db.interviews.insert_one(interview_doc)
        
        # Update application status
        await db.applications.update_one(
            {"id": interview.application_id},
            {"$set": {
                "application_status": "interview_scheduled",
                "last_status_change": datetime.now(timezone.utc).isoformat()
            }}
        )
        
        # Create notification for candidate
        await db.notifications.insert_one({
            "id": str(uuid.uuid4()),
            "user_id": application["candidate_id"],
            "notification_type": "interview_scheduled",
            "title": "Interview Scheduled",
            "message": f"Your interview for {application.get('job_title', 'the position')} has been scheduled.",
            "is_read": False,
            "created_at": datetime.now(timezone.utc).isoformat()
        })
        
        return interview_doc
    
    @router.get("", response_model=List[InterviewResponse])
    async def list_interviews(
        skip: int = 0,
        limit: int = 50,
        status: Optional[str] = None,
        interview_type: Optional[str] = None,
        upcoming_only: bool = False,
        current_user: dict = Depends(get_current_user)
    ):
        """List interviews"""
        query = {}
        
        # Filter by user role
        if current_user["role"] == "candidate":
            query["candidate_id"] = current_user["id"]
        elif current_user["role"] not in ["admin", "super_admin", "recruiter", "client"]:
            raise HTTPException(status_code=403, detail="Access denied")
        
        if status:
            query["interview_status"] = status
        
        if interview_type:
            query["interview_type"] = interview_type
        
        if upcoming_only:
            query["scheduled_at"] = {"$gte": datetime.now(timezone.utc).isoformat()}
            query["interview_status"] = "scheduled"
        
        interviews = await db.interviews.find(
            query, {"_id": 0}
        ).sort("scheduled_at", 1).skip(skip).limit(limit).to_list(limit)
        
        return interviews
    
    @router.get("/{interview_id}", response_model=InterviewResponse)
    async def get_interview(
        interview_id: str,
        current_user: dict = Depends(get_current_user)
    ):
        """Get interview by ID"""
        interview = await db.interviews.find_one({"id": interview_id}, {"_id": 0})
        if not interview:
            raise HTTPException(status_code=404, detail="Interview not found")
        
        # Check access
        if current_user["role"] == "candidate" and interview["candidate_id"] != current_user["id"]:
            raise HTTPException(status_code=403, detail="Access denied")
        
        return interview
    
    @router.put("/{interview_id}", response_model=InterviewResponse)
    async def update_interview(
        interview_id: str,
        interview: InterviewUpdate,
        current_user: dict = Depends(get_current_user)
    ):
        """Update interview details"""
        if current_user["role"] not in ["admin", "super_admin", "recruiter", "client"]:
            raise HTTPException(status_code=403, detail="Access denied")
        
        existing = await db.interviews.find_one({"id": interview_id})
        if not existing:
            raise HTTPException(status_code=404, detail="Interview not found")
        
        update_data = interview.dict(exclude_none=True)
        update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
        
        # Update interviewer names if interviewer_ids changed
        if "interviewer_ids" in update_data:
            interviewer_names = []
            for interviewer_id in update_data["interviewer_ids"]:
                user = await db.users.find_one({"id": interviewer_id}, {"_id": 0, "full_name": 1})
                if user:
                    interviewer_names.append(user.get("full_name", "Unknown"))
            update_data["interviewer_names"] = interviewer_names
        
        await db.interviews.update_one(
            {"id": interview_id},
            {"$set": update_data}
        )
        
        updated = await db.interviews.find_one({"id": interview_id}, {"_id": 0})
        return updated
    
    @router.post("/{interview_id}/feedback")
    async def submit_feedback(
        interview_id: str,
        feedback: InterviewFeedbackModel,
        current_user: dict = Depends(get_current_user)
    ):
        """Submit interview feedback"""
        if current_user["role"] not in ["admin", "super_admin", "recruiter", "client"]:
            raise HTTPException(status_code=403, detail="Access denied")
        
        interview = await db.interviews.find_one({"id": interview_id})
        if not interview:
            raise HTTPException(status_code=404, detail="Interview not found")
        
        feedback_doc = {
            **feedback.dict(),
            "submitted_by": current_user["id"],
            "submitted_at": datetime.now(timezone.utc).isoformat()
        }
        
        scores = {}
        if feedback.technical_score:
            scores["technical"] = feedback.technical_score
        if feedback.communication_score:
            scores["communication"] = feedback.communication_score
        if feedback.problem_solving_score:
            scores["problem_solving"] = feedback.problem_solving_score
        if feedback.cultural_fit_score:
            scores["cultural_fit"] = feedback.cultural_fit_score
        
        await db.interviews.update_one(
            {"id": interview_id},
            {"$set": {
                "interview_status": "completed",
                "feedback": feedback_doc,
                "rating": feedback.rating,
                "scores": scores,
                "recommendation": feedback.recommendation,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }}
        )
        
        # Update application status based on recommendation
        new_status = "interview_completed"
        if feedback.recommendation == "reject":
            new_status = "rejected"
        
        await db.applications.update_one(
            {"id": interview["application_id"]},
            {"$set": {
                "application_status": new_status,
                "last_status_change": datetime.now(timezone.utc).isoformat()
            },
            "$push": {
                "interview_feedback": feedback_doc
            }}
        )
        
        return {"status": "feedback_submitted", "interview_id": interview_id}
    
    @router.post("/{interview_id}/cancel")
    async def cancel_interview(
        interview_id: str,
        reason: Optional[str] = None,
        current_user: dict = Depends(get_current_user)
    ):
        """Cancel an interview"""
        if current_user["role"] not in ["admin", "super_admin", "recruiter", "client"]:
            raise HTTPException(status_code=403, detail="Access denied")
        
        interview = await db.interviews.find_one({"id": interview_id})
        if not interview:
            raise HTTPException(status_code=404, detail="Interview not found")
        
        if interview["interview_status"] != "scheduled":
            raise HTTPException(status_code=400, detail="Only scheduled interviews can be cancelled")
        
        await db.interviews.update_one(
            {"id": interview_id},
            {"$set": {
                "interview_status": "cancelled",
                "notes": reason,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }}
        )
        
        # Notify candidate
        await db.notifications.insert_one({
            "id": str(uuid.uuid4()),
            "user_id": interview["candidate_id"],
            "notification_type": "interview_cancelled",
            "title": "Interview Cancelled",
            "message": f"Your interview has been cancelled. {reason or ''}",
            "is_read": False,
            "created_at": datetime.now(timezone.utc).isoformat()
        })
        
        return {"status": "cancelled", "interview_id": interview_id}
    
    @router.get("/calendar/upcoming")
    async def get_calendar_view(
        days: int = 7,
        current_user: dict = Depends(get_current_user)
    ):
        """Get upcoming interviews for calendar view"""
        from datetime import timedelta
        
        start_date = datetime.now(timezone.utc)
        end_date = start_date + timedelta(days=days)
        
        query = {
            "interview_status": "scheduled",
            "scheduled_at": {
                "$gte": start_date.isoformat(),
                "$lte": end_date.isoformat()
            }
        }
        
        if current_user["role"] == "candidate":
            query["candidate_id"] = current_user["id"]
        elif current_user["role"] not in ["admin", "super_admin", "recruiter", "client"]:
            # Interviewer - show interviews they're part of
            query["interviewer_ids"] = current_user["id"]
        
        interviews = await db.interviews.find(
            query, {"_id": 0}
        ).sort("scheduled_at", 1).to_list(100)
        
        # Group by date
        calendar = {}
        for interview in interviews:
            date_key = interview["scheduled_at"][:10]
            if date_key not in calendar:
                calendar[date_key] = []
            calendar[date_key].append(interview)
        
        return {"days": days, "calendar": calendar, "total_interviews": len(interviews)}
    
    return router
