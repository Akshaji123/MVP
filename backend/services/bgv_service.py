"""
Background Verification (BGV) Service
HiringReferrals Platform

Comprehensive BGV workflow:
- Multiple verification types
- Specialist assignment
- Status tracking
- Report generation
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timezone, timedelta
from enum import Enum
import uuid
import logging

logger = logging.getLogger(__name__)


class BGVType(Enum):
    """Types of background verification checks"""
    IDENTITY = "identity"
    ADDRESS = "address"
    EMPLOYMENT = "employment"
    EDUCATION = "education"
    CRIMINAL = "criminal"
    CREDIT = "credit"
    REFERENCE = "reference"
    DRUG_TEST = "drug_test"
    GLOBAL_DATABASE = "global_database"


class BGVStatus(Enum):
    """Status of BGV checks"""
    PENDING = "pending"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    AWAITING_DOCUMENTS = "awaiting_documents"
    UNDER_REVIEW = "under_review"
    VERIFIED = "verified"
    FAILED = "failed"
    DISCREPANCY = "discrepancy"
    INSUFFICIENT_INFO = "insufficient_info"


class BGVPriority(Enum):
    """Priority levels for BGV requests"""
    URGENT = "urgent"      # 24 hours
    HIGH = "high"          # 3 days
    NORMAL = "normal"      # 7 days
    LOW = "low"            # 14 days


# Estimated TAT (Turn Around Time) in days
BGV_TAT = {
    BGVType.IDENTITY: 1,
    BGVType.ADDRESS: 3,
    BGVType.EMPLOYMENT: 5,
    BGVType.EDUCATION: 5,
    BGVType.CRIMINAL: 7,
    BGVType.CREDIT: 2,
    BGVType.REFERENCE: 3,
    BGVType.DRUG_TEST: 2,
    BGVType.GLOBAL_DATABASE: 1
}

# Required documents for each check type
REQUIRED_DOCUMENTS = {
    BGVType.IDENTITY: ["aadhaar_card", "pan_card", "passport"],
    BGVType.ADDRESS: ["utility_bill", "rent_agreement", "aadhaar_card"],
    BGVType.EMPLOYMENT: ["offer_letter", "relieving_letter", "payslips"],
    BGVType.EDUCATION: ["degree_certificate", "marksheets", "provisional_certificate"],
    BGVType.CRIMINAL: ["consent_form", "id_proof"],
    BGVType.CREDIT: ["consent_form", "pan_card"],
    BGVType.REFERENCE: ["reference_contact_details"],
    BGVType.DRUG_TEST: ["consent_form", "id_proof"],
    BGVType.GLOBAL_DATABASE: ["passport", "consent_form"]
}


class BGVService:
    """
    Background Verification Service with specialist workflow
    """
    
    def __init__(self, db):
        self.db = db
    
    async def create_bgv_request(
        self,
        candidate_id: str,
        application_id: str,
        requested_by: str,
        verification_types: List[str],
        priority: str = "normal",
        deadline: Optional[str] = None,
        special_instructions: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a new BGV request"""
        
        # Get candidate details
        candidate = await self.db.users.find_one({"id": candidate_id}, {"_id": 0})
        if not candidate:
            return {"error": "Candidate not found"}
        
        # Validate verification types
        valid_types = [t.value for t in BGVType]
        for vtype in verification_types:
            if vtype not in valid_types:
                return {"error": f"Invalid verification type: {vtype}"}
        
        # Calculate estimated completion
        max_tat = max(BGV_TAT.get(BGVType(t), 7) for t in verification_types)
        priority_multiplier = {"urgent": 0.5, "high": 0.75, "normal": 1.0, "low": 1.5}
        estimated_days = int(max_tat * priority_multiplier.get(priority, 1.0))
        estimated_completion = (datetime.now(timezone.utc) + timedelta(days=estimated_days)).isoformat()
        
        bgv_id = str(uuid.uuid4())
        
        # Create individual checks
        checks = []
        for vtype in verification_types:
            check = {
                "check_id": str(uuid.uuid4()),
                "check_type": vtype,
                "status": BGVStatus.PENDING.value,
                "assigned_to": None,
                "required_documents": REQUIRED_DOCUMENTS.get(BGVType(vtype), []),
                "submitted_documents": [],
                "verification_data": {},
                "discrepancies": [],
                "remarks": None,
                "started_at": None,
                "completed_at": None
            }
            checks.append(check)
        
        bgv_request = {
            "id": bgv_id,
            "candidate_id": candidate_id,
            "candidate_name": candidate.get("full_name"),
            "candidate_email": candidate.get("email"),
            "application_id": application_id,
            "requested_by": requested_by,
            "requested_at": datetime.now(timezone.utc).isoformat(),
            "priority": priority,
            "deadline": deadline,
            "special_instructions": special_instructions,
            "status": "pending",
            "verification_types": verification_types,
            "checks": checks,
            "overall_result": None,
            "completion_percentage": 0,
            "estimated_completion": estimated_completion,
            "completed_at": None,
            "report_url": None,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        await self.db.bgv_requests.insert_one(bgv_request)
        
        # Create notification for candidate
        await self._create_notification(
            user_id=candidate_id,
            title="Background Verification Initiated",
            message=f"A background verification has been initiated for your application. Please ensure all required documents are uploaded.",
            type="info"
        )
        
        return {
            "bgv_id": bgv_id,
            "status": "created",
            "verification_types": verification_types,
            "estimated_completion": estimated_completion
        }
    
    async def assign_specialist(
        self,
        bgv_id: str,
        check_type: str,
        specialist_id: str
    ) -> Dict[str, Any]:
        """Assign a BGV specialist to a specific check"""
        
        # Verify specialist role
        specialist = await self.db.users.find_one({"id": specialist_id}, {"_id": 0})
        if not specialist or specialist.get("role") not in ["bgv_specialist", "admin"]:
            return {"error": "Invalid specialist"}
        
        # Update check assignment
        result = await self.db.bgv_requests.update_one(
            {"id": bgv_id, "checks.check_type": check_type},
            {
                "$set": {
                    "checks.$.assigned_to": specialist_id,
                    "checks.$.status": BGVStatus.ASSIGNED.value,
                    "checks.$.started_at": datetime.now(timezone.utc).isoformat(),
                    "status": "in_progress"
                }
            }
        )
        
        if result.modified_count == 0:
            return {"error": "BGV request or check not found"}
        
        return {
            "bgv_id": bgv_id,
            "check_type": check_type,
            "assigned_to": specialist_id,
            "status": "assigned"
        }
    
    async def update_check_status(
        self,
        bgv_id: str,
        check_type: str,
        new_status: str,
        specialist_id: str,
        verification_data: Optional[Dict[str, Any]] = None,
        discrepancies: Optional[List[str]] = None,
        remarks: Optional[str] = None
    ) -> Dict[str, Any]:
        """Update the status of a BGV check"""
        
        # Validate status
        try:
            status_enum = BGVStatus(new_status)
        except ValueError:
            return {"error": f"Invalid status: {new_status}"}
        
        update_data = {
            "checks.$.status": new_status,
            "checks.$.remarks": remarks
        }
        
        if verification_data:
            update_data["checks.$.verification_data"] = verification_data
        
        if discrepancies:
            update_data["checks.$.discrepancies"] = discrepancies
        
        if status_enum in [BGVStatus.VERIFIED, BGVStatus.FAILED, BGVStatus.DISCREPANCY]:
            update_data["checks.$.completed_at"] = datetime.now(timezone.utc).isoformat()
        
        result = await self.db.bgv_requests.update_one(
            {"id": bgv_id, "checks.check_type": check_type},
            {"$set": update_data}
        )
        
        if result.modified_count == 0:
            return {"error": "BGV request or check not found"}
        
        # Update overall progress
        await self._update_overall_progress(bgv_id)
        
        return {
            "bgv_id": bgv_id,
            "check_type": check_type,
            "new_status": new_status
        }
    
    async def submit_documents(
        self,
        bgv_id: str,
        check_type: str,
        documents: List[Dict[str, str]]
    ) -> Dict[str, Any]:
        """Submit documents for a BGV check"""
        
        # Documents format: [{"name": "aadhaar_card", "url": "/uploads/..."}]
        
        result = await self.db.bgv_requests.update_one(
            {"id": bgv_id, "checks.check_type": check_type},
            {
                "$set": {
                    "checks.$.submitted_documents": documents,
                    "checks.$.status": BGVStatus.IN_PROGRESS.value
                }
            }
        )
        
        if result.modified_count == 0:
            return {"error": "BGV request or check not found"}
        
        return {
            "bgv_id": bgv_id,
            "check_type": check_type,
            "documents_submitted": len(documents)
        }
    
    async def complete_verification(
        self,
        bgv_id: str,
        specialist_id: str,
        overall_result: str,  # clear, discrepancy, failed
        summary: str,
        recommendations: Optional[str] = None
    ) -> Dict[str, Any]:
        """Complete BGV verification and generate report"""
        
        bgv_request = await self.db.bgv_requests.find_one({"id": bgv_id}, {"_id": 0})
        if not bgv_request:
            return {"error": "BGV request not found"}
        
        # Check all checks are completed
        pending_checks = [c for c in bgv_request["checks"] 
                        if c["status"] not in ["verified", "failed", "discrepancy"]]
        
        if pending_checks:
            return {
                "error": "Not all checks are completed",
                "pending": [c["check_type"] for c in pending_checks]
            }
        
        # Generate report
        report = await self._generate_bgv_report(bgv_request, overall_result, summary, recommendations)
        
        # Update BGV request
        await self.db.bgv_requests.update_one(
            {"id": bgv_id},
            {
                "$set": {
                    "status": "completed",
                    "overall_result": overall_result,
                    "completion_percentage": 100,
                    "completed_at": datetime.now(timezone.utc).isoformat(),
                    "completed_by": specialist_id,
                    "report_summary": summary,
                    "recommendations": recommendations,
                    "report_url": report.get("report_path")
                }
            }
        )
        
        # Notify stakeholders
        await self._notify_bgv_completion(bgv_request, overall_result)
        
        return {
            "bgv_id": bgv_id,
            "overall_result": overall_result,
            "report_url": report.get("report_path"),
            "completed_at": datetime.now(timezone.utc).isoformat()
        }
    
    async def _update_overall_progress(self, bgv_id: str):
        """Update overall BGV progress percentage"""
        
        bgv_request = await self.db.bgv_requests.find_one({"id": bgv_id}, {"_id": 0})
        if not bgv_request:
            return
        
        total_checks = len(bgv_request["checks"])
        completed_checks = sum(1 for c in bgv_request["checks"] 
                             if c["status"] in ["verified", "failed", "discrepancy"])
        
        percentage = int((completed_checks / total_checks) * 100) if total_checks > 0 else 0
        
        # Determine overall status
        if percentage == 100:
            all_verified = all(c["status"] == "verified" for c in bgv_request["checks"])
            has_discrepancy = any(c["status"] == "discrepancy" for c in bgv_request["checks"])
            
            if all_verified:
                status = "verified"
            elif has_discrepancy:
                status = "discrepancy"
            else:
                status = "completed"
        elif percentage > 0:
            status = "in_progress"
        else:
            status = "pending"
        
        await self.db.bgv_requests.update_one(
            {"id": bgv_id},
            {"$set": {"completion_percentage": percentage, "status": status}}
        )
    
    async def _generate_bgv_report(
        self,
        bgv_request: Dict[str, Any],
        overall_result: str,
        summary: str,
        recommendations: Optional[str]
    ) -> Dict[str, Any]:
        """Generate BGV report document"""
        
        report_id = str(uuid.uuid4())
        report_path = f"/app/bgv_reports/{report_id}.json"
        
        report = {
            "report_id": report_id,
            "bgv_id": bgv_request["id"],
            "candidate_name": bgv_request["candidate_name"],
            "candidate_email": bgv_request["candidate_email"],
            "application_id": bgv_request["application_id"],
            "verification_period": {
                "initiated": bgv_request["requested_at"],
                "completed": datetime.now(timezone.utc).isoformat()
            },
            "overall_result": overall_result,
            "summary": summary,
            "recommendations": recommendations,
            "checks": bgv_request["checks"],
            "generated_at": datetime.now(timezone.utc).isoformat()
        }
        
        # Save report
        import os
        import json
        os.makedirs("/app/bgv_reports", exist_ok=True)
        with open(report_path, "w") as f:
            json.dump(report, f, indent=2)
        
        return {"report_id": report_id, "report_path": report_path}
    
    async def _notify_bgv_completion(self, bgv_request: Dict[str, Any], result: str):
        """Send notifications on BGV completion"""
        
        # Notify candidate
        result_text = {
            "clear": "Your background verification has been completed successfully.",
            "discrepancy": "Your background verification found some discrepancies. HR will contact you.",
            "failed": "Your background verification could not be completed. Please contact HR."
        }
        
        await self._create_notification(
            user_id=bgv_request["candidate_id"],
            title="Background Verification Complete",
            message=result_text.get(result, "Your background verification has been completed."),
            type="success" if result == "clear" else "warning"
        )
    
    async def _create_notification(
        self,
        user_id: str,
        title: str,
        message: str,
        type: str = "info"
    ):
        """Create notification"""
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
    
    async def get_specialist_workload(self, specialist_id: str) -> Dict[str, Any]:
        """Get workload statistics for a BGV specialist"""
        
        # Active assignments
        pipeline = [
            {"$unwind": "$checks"},
            {"$match": {
                "checks.assigned_to": specialist_id,
                "checks.status": {"$nin": ["verified", "failed", "discrepancy"]}
            }},
            {"$group": {
                "_id": "$checks.check_type",
                "count": {"$sum": 1}
            }}
        ]
        
        active = await self.db.bgv_requests.aggregate(pipeline).to_list(20)
        
        # Completed this month
        month_start = datetime.now(timezone.utc).replace(day=1, hour=0, minute=0, second=0)
        completed_pipeline = [
            {"$unwind": "$checks"},
            {"$match": {
                "checks.assigned_to": specialist_id,
                "checks.completed_at": {"$gte": month_start.isoformat()},
                "checks.status": {"$in": ["verified", "failed", "discrepancy"]}
            }},
            {"$count": "total"}
        ]
        
        completed_result = await self.db.bgv_requests.aggregate(completed_pipeline).to_list(1)
        completed_count = completed_result[0]["total"] if completed_result else 0
        
        return {
            "specialist_id": specialist_id,
            "active_assignments": {r["_id"]: r["count"] for r in active},
            "total_active": sum(r["count"] for r in active),
            "completed_this_month": completed_count,
            "calculated_at": datetime.now(timezone.utc).isoformat()
        }


def create_bgv_service(db) -> BGVService:
    return BGVService(db)
