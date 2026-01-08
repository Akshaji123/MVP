"""
Extended Database Models
HiringReferrals Platform

Additional models for:
- User Profiles
- Interview Schedules  
- Application Status Logs
- Job Skills
- Job Views
- Audit Logs
"""

from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


# ============= ENUMS =============

class UserRole(str, Enum):
    ADMIN = "admin"
    COMPANY = "company"
    RECRUITER = "recruiter"
    CANDIDATE = "candidate"
    EMPLOYEE = "employee"
    BGV_SPECIALIST = "bgv_specialist"


class UserStatus(str, Enum):
    PENDING = "pending"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    DEACTIVATED = "deactivated"


class ApplicationStatus(str, Enum):
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


class InterviewType(str, Enum):
    PHONE = "phone"
    VIDEO = "video"
    ONSITE = "onsite"
    TECHNICAL = "technical"
    HR = "hr"
    PANEL = "panel"
    CASE_STUDY = "case_study"


class BGVType(str, Enum):
    IDENTITY = "identity"
    ADDRESS = "address"
    EMPLOYMENT = "employment"
    EDUCATION = "education"
    CRIMINAL = "criminal"
    CREDIT = "credit"
    REFERENCE = "reference"
    DRUG_TEST = "drug_test"


class BGVStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    VERIFIED = "verified"
    FAILED = "failed"
    DISCREPANCY = "discrepancy"


# ============= USER MODELS =============

class Address(BaseModel):
    street: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = "India"
    pincode: Optional[str] = None


class Experience(BaseModel):
    company: str
    title: str
    start_date: str
    end_date: Optional[str] = None
    is_current: bool = False
    description: Optional[str] = None
    skills_used: List[str] = []


class Education(BaseModel):
    institution: str
    degree: str
    field: Optional[str] = None
    start_year: int
    end_year: Optional[int] = None
    grade: Optional[str] = None


class UserProfileCreate(BaseModel):
    user_id: str
    first_name: str
    last_name: str
    phone: Optional[str] = None
    address: Optional[Address] = None
    date_of_birth: Optional[str] = None
    gender: Optional[str] = None
    linkedin_url: Optional[str] = None
    portfolio_url: Optional[str] = None
    bio: Optional[str] = None
    skills: List[str] = []
    experience: List[Experience] = []
    education: List[Education] = []
    languages: List[str] = []
    certifications: List[str] = []
    expected_salary: Optional[float] = None
    current_salary: Optional[float] = None
    notice_period_days: Optional[int] = None
    willing_to_relocate: bool = False
    preferred_locations: List[str] = []
    documents: Dict[str, str] = {}  # {doc_type: file_path}


class UserProfileResponse(UserProfileCreate):
    id: str
    profile_completion: int = 0
    verified: bool = False
    verified_at: Optional[str] = None
    created_at: str
    updated_at: str


# ============= INTERVIEW MODELS =============

class InterviewFeedback(BaseModel):
    submitted_by: str
    rating: int = Field(ge=1, le=5)
    technical_score: Optional[int] = Field(None, ge=1, le=10)
    communication_score: Optional[int] = Field(None, ge=1, le=10)
    cultural_fit_score: Optional[int] = Field(None, ge=1, le=10)
    problem_solving_score: Optional[int] = Field(None, ge=1, le=10)
    comments: Optional[str] = None
    strengths: List[str] = []
    areas_of_improvement: List[str] = []
    recommendation: str = "proceed"  # proceed, hold, reject
    submitted_at: str


class InterviewScheduleCreate(BaseModel):
    application_id: str
    interview_type: InterviewType
    scheduled_at: str
    duration_minutes: int = 60
    location: Optional[str] = None
    meeting_link: Optional[str] = None
    interviewers: List[str] = []
    notes: Optional[str] = None
    preparation_notes: Optional[str] = None


class InterviewScheduleResponse(InterviewScheduleCreate):
    id: str
    candidate_id: str
    job_id: str
    scheduled_by: str
    status: str = "scheduled"  # scheduled, completed, cancelled, rescheduled, no_show
    feedback: Optional[InterviewFeedback] = None
    created_at: str
    updated_at: Optional[str] = None


# ============= APPLICATION STATUS LOG =============

class ApplicationStatusLog(BaseModel):
    id: str
    application_id: str
    old_status: str
    new_status: str
    changed_by: str
    reason: Optional[str] = None
    notes: Optional[str] = None
    metadata: Dict[str, Any] = {}
    timestamp: str


# ============= JOB MODELS =============

class JobSkill(BaseModel):
    id: str
    job_id: str
    skill_name: str
    skill_type: str = "required"  # required, preferred, bonus
    experience_years: Optional[int] = None
    proficiency_level: Optional[str] = None  # beginner, intermediate, advanced, expert


class JobView(BaseModel):
    id: str
    job_id: str
    viewer_id: Optional[str] = None
    viewer_ip: Optional[str] = None
    source: Optional[str] = None  # direct, search, referral, email
    viewed_at: str


class JobCreate(BaseModel):
    title: str
    description: str
    requirements: List[str]
    preferred_skills: List[str] = []
    location: str
    remote_available: bool = False
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    salary_currency: str = "INR"
    experience_min: int = 0
    experience_max: Optional[int] = None
    education_required: str = "bachelors"
    employment_type: str = "full_time"  # full_time, part_time, contract, internship
    department: Optional[str] = None
    reporting_to: Optional[str] = None
    team_size: Optional[int] = None
    benefits: List[str] = []
    application_deadline: Optional[str] = None


# ============= AUDIT LOG =============

class AuditLogType(str, Enum):
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    LOGIN = "login"
    LOGOUT = "logout"
    VIEW = "view"
    EXPORT = "export"
    IMPORT = "import"
    STATUS_CHANGE = "status_change"
    PERMISSION_CHANGE = "permission_change"


class AuditLog(BaseModel):
    id: str
    user_id: str
    action_type: AuditLogType
    resource_type: str  # user, job, application, etc.
    resource_id: Optional[str] = None
    old_value: Optional[Dict[str, Any]] = None
    new_value: Optional[Dict[str, Any]] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    metadata: Dict[str, Any] = {}
    timestamp: str


# ============= BGV MODELS =============

class BGVCheckResult(BaseModel):
    check_type: BGVType
    status: BGVStatus
    verified_data: Dict[str, Any] = {}
    discrepancies: List[str] = []
    documents: List[str] = []
    verified_by: Optional[str] = None
    verified_at: Optional[str] = None
    remarks: Optional[str] = None


class BGVRequestCreate(BaseModel):
    candidate_id: str
    application_id: str
    verification_types: List[BGVType]
    priority: str = "normal"  # urgent, high, normal, low
    deadline: Optional[str] = None
    special_instructions: Optional[str] = None


class BGVRequestResponse(BaseModel):
    id: str
    candidate_id: str
    candidate_name: str
    application_id: str
    requested_by: str
    requested_at: str
    status: str
    verification_types: List[str]
    checks_completed: List[BGVCheckResult] = []
    checks_pending: List[str] = []
    overall_status: str = "pending"
    completion_percentage: int = 0
    completed_at: Optional[str] = None
    report_url: Optional[str] = None


# ============= NOTIFICATION MODEL =============

class NotificationType(str, Enum):
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    ACTION_REQUIRED = "action_required"


class Notification(BaseModel):
    id: str
    user_id: str
    title: str
    message: str
    type: NotificationType = NotificationType.INFO
    read: bool = False
    action_url: Optional[str] = None
    metadata: Dict[str, Any] = {}
    created_at: str
    read_at: Optional[str] = None


# ============= PAYMENT/COMMISSION MODELS =============

class PaymentStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"


class CommissionPayment(BaseModel):
    id: str
    application_id: str
    recruiter_id: str
    candidate_id: str
    job_id: str
    annual_package: float
    base_commission_rate: float
    tier_multiplier: float
    gross_commission: float
    tds_amount: float
    platform_fee: float
    net_commission: float
    currency: str = "INR"
    payment_method: Optional[str] = None
    transaction_id: Optional[str] = None
    bank_reference: Optional[str] = None
    status: PaymentStatus = PaymentStatus.PENDING
    initiated_at: str
    processed_at: Optional[str] = None
    notes: Optional[str] = None
