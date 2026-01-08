from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Dict, Any
from datetime import datetime

# Document Management Models
class Document(BaseModel):
    id: str
    name: str
    file_path: str
    file_type: str
    file_size: int
    uploaded_by: str
    uploaded_at: str
    category: str  # resume, offer_letter, contract, verification_doc, invoice
    related_to: str  # user_id, application_id, etc
    status: str = "active"

class DocumentUploadRequest(BaseModel):
    category: str
    related_to: str
    description: Optional[str] = None

# ATS Models
class ATSStage(BaseModel):
    id: str
    name: str
    order: int
    description: str
    color: str

class ATSPipeline(BaseModel):
    application_id: str
    current_stage: str
    stage_history: List[Dict[str, Any]]
    days_in_current_stage: int
    total_days_in_pipeline: int
    next_action: Optional[str] = None
    scheduled_interviews: List[Dict[str, Any]] = []

# BGV Models
class BGVRequest(BaseModel):
    id: str
    candidate_id: str
    candidate_name: str
    application_id: str
    requested_by: str
    requested_at: str
    status: str  # pending, in_progress, completed, failed
    verification_type: str  # identity, employment, education, criminal, address
    checks_completed: List[str] = []
    checks_pending: List[str] = []
    remarks: Optional[str] = None
    completed_at: Optional[str] = None
    verified_by: Optional[str] = None

class BGVCheckResult(BaseModel):
    check_type: str
    status: str  # verified, discrepancy, failed
    verified_data: Dict[str, Any]
    remarks: str
    verified_at: str
    verified_by: str

# 91-Day Tracking Models
class CandidateTracking(BaseModel):
    id: str
    candidate_id: str
    application_id: str
    job_id: str
    company_id: str
    join_date: str
    tracking_start_date: str
    tracking_end_date: str  # 91 days from join_date
    current_day: int
    status: str  # tracking, completed, resigned
    milestones: List[Dict[str, Any]] = []
    feedback_records: List[Dict[str, Any]] = []
    invoice_eligible: bool = False
    invoice_generated: bool = False

class TrackingMilestone(BaseModel):
    day: int
    title: str
    description: str
    status: str  # pending, completed, skipped
    completed_at: Optional[str] = None
    feedback: Optional[str] = None

# Invoice Models
class Invoice(BaseModel):
    id: str
    invoice_number: str
    company_id: str
    company_name: str
    candidate_tracking_id: str
    candidate_name: str
    job_title: str
    amount: float
    tax_amount: float
    total_amount: float
    currency: str = "INR"
    issue_date: str
    due_date: str
    status: str  # draft, sent, paid, overdue, cancelled
    payment_terms: str
    items: List[Dict[str, Any]]
    notes: Optional[str] = None

class InvoiceItem(BaseModel):
    description: str
    quantity: int
    rate: float
    amount: float

# Automation Models
class AutomationRule(BaseModel):
    id: str
    name: str
    description: str
    trigger_type: str  # time_based, event_based, condition_based
    trigger_config: Dict[str, Any]
    actions: List[Dict[str, Any]]
    is_active: bool = True
    created_by: str
    created_at: str
    last_run: Optional[str] = None
    run_count: int = 0

class AutomationLog(BaseModel):
    id: str
    rule_id: str
    executed_at: str
    status: str  # success, failed, partial
    actions_performed: List[str]
    error_message: Optional[str] = None
