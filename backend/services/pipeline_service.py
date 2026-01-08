"""
Application Processing Pipeline
HiringReferrals Platform

Automated screening and evaluation pipeline:
- Auto-screening with weighted scoring
- Status workflow management
- Interview scheduling
- Audit logging
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timezone, timedelta
from enum import Enum
import uuid
import logging

logger = logging.getLogger(__name__)


class ApplicationStatus(Enum):
    """Application status workflow stages"""
    SUBMITTED = "submitted"
    SCREENING = "screening"
    SHORTLISTED = "shortlisted"
    INTERVIEW_SCHEDULED = "interview_scheduled"
    INTERVIEW_COMPLETED = "interview_completed"
    ASSESSMENT = "assessment"
    OFFER_PENDING = "offer_pending"
    OFFER_SENT = "offer_sent"
    OFFER_ACCEPTED = "offer_accepted"
    HIRED = "hired"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"
    ON_HOLD = "on_hold"


class ScreeningStage(Enum):
    """Automated screening stages"""
    RESUME_KEYWORDS = "resume_keywords"
    EXPERIENCE_LEVEL = "experience_level"
    EDUCATION_MATCH = "education_match"
    LOCATION_PREFERENCE = "location_preference"
    SALARY_EXPECTATION = "salary_expectation"


# Screening weights
SCREENING_WEIGHTS = {
    ScreeningStage.RESUME_KEYWORDS: 0.40,      # 40%
    ScreeningStage.EXPERIENCE_LEVEL: 0.25,     # 25%
    ScreeningStage.EDUCATION_MATCH: 0.15,      # 15%
    ScreeningStage.LOCATION_PREFERENCE: 0.10,  # 10%
    ScreeningStage.SALARY_EXPECTATION: 0.10    # 10%
}

# Thresholds
AUTO_SHORTLIST_THRESHOLD = 70
AUTO_REJECT_THRESHOLD = 30
MANUAL_REVIEW_MIN = 50


# Valid status transitions
STATUS_TRANSITIONS = {
    ApplicationStatus.SUBMITTED: [ApplicationStatus.SCREENING, ApplicationStatus.REJECTED, ApplicationStatus.WITHDRAWN],
    ApplicationStatus.SCREENING: [ApplicationStatus.SHORTLISTED, ApplicationStatus.REJECTED, ApplicationStatus.ON_HOLD],
    ApplicationStatus.SHORTLISTED: [ApplicationStatus.INTERVIEW_SCHEDULED, ApplicationStatus.REJECTED, ApplicationStatus.WITHDRAWN],
    ApplicationStatus.INTERVIEW_SCHEDULED: [ApplicationStatus.INTERVIEW_COMPLETED, ApplicationStatus.REJECTED, ApplicationStatus.WITHDRAWN],
    ApplicationStatus.INTERVIEW_COMPLETED: [ApplicationStatus.ASSESSMENT, ApplicationStatus.OFFER_PENDING, ApplicationStatus.REJECTED],
    ApplicationStatus.ASSESSMENT: [ApplicationStatus.OFFER_PENDING, ApplicationStatus.REJECTED],
    ApplicationStatus.OFFER_PENDING: [ApplicationStatus.OFFER_SENT, ApplicationStatus.REJECTED],
    ApplicationStatus.OFFER_SENT: [ApplicationStatus.OFFER_ACCEPTED, ApplicationStatus.REJECTED, ApplicationStatus.WITHDRAWN],
    ApplicationStatus.OFFER_ACCEPTED: [ApplicationStatus.HIRED, ApplicationStatus.WITHDRAWN],
    ApplicationStatus.HIRED: [],  # Terminal state
    ApplicationStatus.REJECTED: [],  # Terminal state
    ApplicationStatus.WITHDRAWN: [],  # Terminal state
    ApplicationStatus.ON_HOLD: [ApplicationStatus.SCREENING, ApplicationStatus.SHORTLISTED, ApplicationStatus.REJECTED]
}


class ApplicationPipeline:
    """
    Application processing pipeline with automated screening,
    status management, and audit logging.
    """
    
    def __init__(self, db, matching_service=None):
        self.db = db
        self.matching_service = matching_service
    
    async def auto_screen_application(
        self,
        application_id: str
    ) -> Dict[str, Any]:
        """
        Run automated screening on an application
        
        Returns:
            Screening result with score and recommendation
        """
        # Get application
        application = await self.db.applications.find_one({"id": application_id}, {"_id": 0})
        if not application:
            return {"error": "Application not found"}
        
        # Get job
        job = await self.db.jobs.find_one({"id": application["job_id"]}, {"_id": 0})
        if not job:
            return {"error": "Job not found"}
        
        # Get resume
        resume = await self.db.resumes.find_one({"id": application.get("resume_id")}, {"_id": 0})
        if not resume:
            return {"error": "Resume not found"}
        
        # Build candidate profile
        candidate = {
            "id": application["candidate_id"],
            "skills": resume.get("skills", []),
            "experience_years": resume.get("experience_years", 0),
            "education": resume.get("education", []),
            "location": resume.get("parsed_data", {}).get("location", ""),
            "expected_salary": resume.get("parsed_data", {}).get("expected_salary", 0)
        }
        
        # Calculate match score using matching service if available
        if self.matching_service:
            match_result = await self.matching_service.calculate_match_score(candidate, job)
            screening_score = match_result["overall_score"]
            screening_details = match_result["breakdown"]
        else:
            # Basic scoring fallback
            screening_score = resume.get("overall_score", 50)
            screening_details = {"fallback": True}
        
        # Determine recommendation
        if screening_score >= AUTO_SHORTLIST_THRESHOLD:
            recommendation = "auto_shortlist"
            new_status = ApplicationStatus.SHORTLISTED.value
        elif screening_score <= AUTO_REJECT_THRESHOLD:
            recommendation = "auto_reject"
            new_status = ApplicationStatus.REJECTED.value
        else:
            recommendation = "manual_review"
            new_status = ApplicationStatus.SCREENING.value
        
        # Update application
        screening_result = {
            "screening_score": round(screening_score, 1),
            "recommendation": recommendation,
            "details": screening_details,
            "screened_at": datetime.now(timezone.utc).isoformat(),
            "auto_processed": recommendation in ["auto_shortlist", "auto_reject"]
        }
        
        await self.db.applications.update_one(
            {"id": application_id},
            {
                "$set": {
                    "screening_score": screening_result["screening_score"],
                    "screening_result": screening_result,
                    "status": new_status,
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }
            }
        )
        
        # Log status change
        await self.log_status_change(
            application_id=application_id,
            old_status=application.get("status", "submitted"),
            new_status=new_status,
            changed_by="system",
            reason=f"Auto-screening: {recommendation} (score: {screening_score})"
        )
        
        return {
            "application_id": application_id,
            "screening_score": screening_result["screening_score"],
            "recommendation": recommendation,
            "new_status": new_status,
            "details": screening_details
        }
    
    async def update_status(
        self,
        application_id: str,
        new_status: str,
        changed_by: str,
        reason: Optional[str] = None,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Update application status with validation and logging
        """
        # Get application
        application = await self.db.applications.find_one({"id": application_id}, {"_id": 0})
        if not application:
            return {"error": "Application not found"}
        
        old_status = application.get("status", "submitted")
        
        # Validate status transition
        try:
            old_status_enum = ApplicationStatus(old_status)
            new_status_enum = ApplicationStatus(new_status)
        except ValueError:
            return {"error": f"Invalid status: {new_status}"}
        
        valid_transitions = STATUS_TRANSITIONS.get(old_status_enum, [])
        if new_status_enum not in valid_transitions:
            return {
                "error": f"Invalid transition from '{old_status}' to '{new_status}'",
                "valid_transitions": [s.value for s in valid_transitions]
            }
        
        # Update application
        update_data = {
            "status": new_status,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        if notes:
            update_data["status_notes"] = notes
        
        await self.db.applications.update_one(
            {"id": application_id},
            {"$set": update_data}
        )
        
        # Log status change
        await self.log_status_change(
            application_id=application_id,
            old_status=old_status,
            new_status=new_status,
            changed_by=changed_by,
            reason=reason,
            notes=notes
        )
        
        # Trigger actions based on new status
        await self.trigger_status_actions(application_id, new_status, application)
        
        return {
            "application_id": application_id,
            "old_status": old_status,
            "new_status": new_status,
            "changed_by": changed_by,
            "updated_at": update_data["updated_at"]
        }
    
    async def log_status_change(
        self,
        application_id: str,
        old_status: str,
        new_status: str,
        changed_by: str,
        reason: Optional[str] = None,
        notes: Optional[str] = None
    ):
        """Log status change in audit log"""
        log_entry = {
            "id": str(uuid.uuid4()),
            "application_id": application_id,
            "old_status": old_status,
            "new_status": new_status,
            "changed_by": changed_by,
            "reason": reason,
            "notes": notes,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        await self.db.application_status_logs.insert_one(log_entry)
    
    async def trigger_status_actions(
        self,
        application_id: str,
        new_status: str,
        application: Dict[str, Any]
    ):
        """Trigger automated actions based on status change"""
        
        # Get candidate email
        candidate = await self.db.users.find_one(
            {"id": application["candidate_id"]},
            {"_id": 0, "email": 1, "full_name": 1}
        )
        
        job = await self.db.jobs.find_one(
            {"id": application["job_id"]},
            {"_id": 0, "title": 1, "company_name": 1}
        )
        
        # Status-specific actions
        if new_status == ApplicationStatus.SHORTLISTED.value:
            # Create notification
            await self.create_notification(
                user_id=application["candidate_id"],
                title="Application Shortlisted!",
                message=f"Your application for {job['title']} at {job['company_name']} has been shortlisted.",
                type="success"
            )
        
        elif new_status == ApplicationStatus.INTERVIEW_SCHEDULED.value:
            await self.create_notification(
                user_id=application["candidate_id"],
                title="Interview Scheduled",
                message=f"An interview has been scheduled for {job['title']} at {job['company_name']}.",
                type="info"
            )
        
        elif new_status == ApplicationStatus.OFFER_SENT.value:
            await self.create_notification(
                user_id=application["candidate_id"],
                title="Job Offer Received!",
                message=f"Congratulations! You have received an offer for {job['title']} at {job['company_name']}.",
                type="success"
            )
        
        elif new_status == ApplicationStatus.HIRED.value:
            # Award gamification points
            await self.award_placement_points(application)
            
            await self.create_notification(
                user_id=application["candidate_id"],
                title="Welcome Aboard!",
                message=f"Congratulations on joining {job['company_name']} as {job['title']}!",
                type="success"
            )
        
        elif new_status == ApplicationStatus.REJECTED.value:
            await self.create_notification(
                user_id=application["candidate_id"],
                title="Application Update",
                message=f"Your application for {job['title']} at {job['company_name']} was not successful this time.",
                type="info"
            )
    
    async def create_notification(
        self,
        user_id: str,
        title: str,
        message: str,
        type: str = "info"
    ):
        """Create a notification for user"""
        notification = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "title": title,
            "message": message,
            "type": type,
            "read": False,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await self.db.notifications.insert_one(notification)
    
    async def award_placement_points(self, application: Dict[str, Any]):
        """Award gamification points for successful placement"""
        # Award to recruiter if exists
        if application.get("recruiter_id"):
            await self.db.user_gamification.update_one(
                {"user_id": application["recruiter_id"]},
                {
                    "$inc": {"total_points": 500},  # Placement bonus
                    "$set": {"updated_at": datetime.now(timezone.utc).isoformat()}
                },
                upsert=True
            )
        
        # Award to referrer if exists
        referral = await self.db.referrals.find_one({
            "job_id": application["job_id"],
            "candidate_email": application.get("candidate_email")
        })
        
        if referral:
            await self.db.user_gamification.update_one(
                {"user_id": referral["referrer_id"]},
                {
                    "$inc": {"total_points": 500},
                    "$set": {"updated_at": datetime.now(timezone.utc).isoformat()}
                },
                upsert=True
            )
            
            # Update referral status
            await self.db.referrals.update_one(
                {"id": referral["id"]},
                {"$set": {"status": "hired"}}
            )
    
    async def schedule_interview(
        self,
        application_id: str,
        interview_type: str,
        scheduled_by: str,
        scheduled_at: str,
        duration_minutes: int = 60,
        location: Optional[str] = None,
        meeting_link: Optional[str] = None,
        interviewers: List[str] = None,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """Schedule an interview for an application"""
        
        application = await self.db.applications.find_one({"id": application_id}, {"_id": 0})
        if not application:
            return {"error": "Application not found"}
        
        interview_id = str(uuid.uuid4())
        interview = {
            "id": interview_id,
            "application_id": application_id,
            "candidate_id": application["candidate_id"],
            "job_id": application["job_id"],
            "interview_type": interview_type,  # phone, video, onsite, technical, hr
            "scheduled_by": scheduled_by,
            "scheduled_at": scheduled_at,
            "duration_minutes": duration_minutes,
            "location": location,
            "meeting_link": meeting_link,
            "interviewers": interviewers or [],
            "notes": notes,
            "status": "scheduled",
            "feedback": None,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        await self.db.interview_schedules.insert_one(interview)
        
        # Update application status
        await self.update_status(
            application_id=application_id,
            new_status=ApplicationStatus.INTERVIEW_SCHEDULED.value,
            changed_by=scheduled_by,
            reason=f"{interview_type.title()} interview scheduled"
        )
        
        return {
            "interview_id": interview_id,
            "application_id": application_id,
            "scheduled_at": scheduled_at,
            "interview_type": interview_type
        }
    
    async def submit_interview_feedback(
        self,
        interview_id: str,
        feedback_by: str,
        rating: int,
        technical_score: Optional[int] = None,
        communication_score: Optional[int] = None,
        cultural_fit_score: Optional[int] = None,
        comments: Optional[str] = None,
        recommendation: str = "proceed"  # proceed, hold, reject
    ) -> Dict[str, Any]:
        """Submit feedback for completed interview"""
        
        interview = await self.db.interview_schedules.find_one({"id": interview_id}, {"_id": 0})
        if not interview:
            return {"error": "Interview not found"}
        
        feedback = {
            "submitted_by": feedback_by,
            "rating": rating,
            "technical_score": technical_score,
            "communication_score": communication_score,
            "cultural_fit_score": cultural_fit_score,
            "comments": comments,
            "recommendation": recommendation,
            "submitted_at": datetime.now(timezone.utc).isoformat()
        }
        
        # Update interview
        await self.db.interview_schedules.update_one(
            {"id": interview_id},
            {
                "$set": {
                    "status": "completed",
                    "feedback": feedback
                }
            }
        )
        
        # Update application status
        new_status = ApplicationStatus.INTERVIEW_COMPLETED.value
        if recommendation == "reject":
            new_status = ApplicationStatus.REJECTED.value
        
        await self.update_status(
            application_id=interview["application_id"],
            new_status=new_status,
            changed_by=feedback_by,
            reason=f"Interview feedback: {recommendation}"
        )
        
        return {
            "interview_id": interview_id,
            "feedback_submitted": True,
            "recommendation": recommendation
        }
    
    async def get_pipeline_stats(self, job_id: Optional[str] = None) -> Dict[str, Any]:
        """Get application pipeline statistics"""
        
        match_filter = {}
        if job_id:
            match_filter["job_id"] = job_id
        
        pipeline = [
            {"$match": match_filter},
            {"$group": {
                "_id": "$status",
                "count": {"$sum": 1}
            }}
        ]
        
        results = await self.db.applications.aggregate(pipeline).to_list(20)
        
        stats = {status.value: 0 for status in ApplicationStatus}
        for result in results:
            if result["_id"] in stats:
                stats[result["_id"]] = result["count"]
        
        total = sum(stats.values())
        
        return {
            "job_id": job_id,
            "total_applications": total,
            "by_status": stats,
            "conversion_rates": {
                "screening_to_shortlist": self._calc_rate(stats, "screening", "shortlisted"),
                "shortlist_to_interview": self._calc_rate(stats, "shortlisted", "interview_scheduled"),
                "interview_to_offer": self._calc_rate(stats, "interview_completed", "offer_sent"),
                "offer_to_hire": self._calc_rate(stats, "offer_sent", "hired")
            },
            "calculated_at": datetime.now(timezone.utc).isoformat()
        }
    
    def _calc_rate(self, stats: Dict, from_status: str, to_status: str) -> str:
        """Calculate conversion rate between statuses"""
        from_count = stats.get(from_status, 0)
        to_count = stats.get(to_status, 0)
        if from_count == 0:
            return "N/A"
        rate = (to_count / from_count) * 100
        return f"{rate:.1f}%"


def create_application_pipeline(db, matching_service=None) -> ApplicationPipeline:
    return ApplicationPipeline(db, matching_service)
