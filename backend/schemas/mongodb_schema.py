"""
HiringReferrals Platform - MongoDB Schema Definition
Equivalent document model based on PostgreSQL schema structure

This module defines the complete MongoDB collection schemas organized by logical domains:
- Core: User management and authentication
- Business: Jobs, candidates, applications, referrals
- Financial: Commissions, payments, invoices
- Communication: Messages, notifications, templates
- Integration: ATS, webhooks, API keys
- Audit: Activity logs, data access logs
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from enum import Enum
from pydantic import BaseModel, Field, EmailStr
import uuid


# =====================================================
# ENUMS AND CONSTANTS
# =====================================================

class UserRole(str, Enum):
    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    CLIENT = "client"
    RECRUITER = "recruiter"
    FREELANCER = "freelancer"
    CANDIDATE = "candidate"
    BGV_SPECIALIST = "bgv_specialist"


class ProfileType(str, Enum):
    CANDIDATE = "candidate"
    RECRUITER = "recruiter"
    CLIENT = "client"
    FREELANCER = "freelancer"
    ADMIN = "admin"


class JobStatus(str, Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    PAUSED = "paused"
    CLOSED = "closed"
    ARCHIVED = "archived"


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


class ReferralStatus(str, Enum):
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    APPLIED = "applied"
    INTERVIEWING = "interviewing"
    HIRED = "hired"
    REJECTED = "rejected"
    EXPIRED = "expired"


class VerificationStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    VERIFIED = "verified"
    FAILED = "failed"
    DISCREPANCY = "discrepancy"


class PaymentStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"


class CommissionStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    PROCESSING = "processing"
    PAID = "paid"
    CANCELLED = "cancelled"


# Default role permissions
DEFAULT_ROLE_PERMISSIONS = {
    "super_admin": {"all": True},
    "admin": {
        "users": ["read", "write", "delete"],
        "jobs": ["read", "write", "delete"],
        "applications": ["read", "write"],
        "reports": ["read", "export"],
        "settings": ["read", "write"]
    },
    "client": {
        "jobs": ["read", "write"],
        "candidates": ["read"],
        "applications": ["read", "write"],
        "reports": ["read"]
    },
    "recruiter": {
        "jobs": ["read", "write"],
        "candidates": ["read", "write"],
        "applications": ["read", "write"],
        "referrals": ["read", "write"],
        "interviews": ["read", "write"]
    },
    "freelancer": {
        "jobs": ["read"],
        "referrals": ["read", "write"],
        "commissions": ["read"],
        "profile": ["read", "write"]
    },
    "candidate": {
        "profile": ["read", "write"],
        "applications": ["read", "write"],
        "jobs": ["read"]
    },
    "bgv_specialist": {
        "bgv": ["read", "write"],
        "candidates": ["read"],
        "documents": ["read", "write"]
    }
}


# =====================================================
# MONGODB COLLECTION SCHEMAS
# =====================================================

# Collection names organized by domain
COLLECTIONS = {
    "core": {
        "users": "users",
        "roles": "roles",
        "user_roles": "user_roles",
        "user_profiles": "user_profiles",
        "user_sessions": "user_sessions"
    },
    "business": {
        "companies": "companies",
        "jobs": "jobs",
        "candidates": "candidates",
        "applications": "applications",
        "referrals": "referrals",
        "background_verifications": "background_verifications",
        "interviews": "interviews",
        "assessments": "assessments"
    },
    "financial": {
        "commissions": "commissions",
        "payments": "payments",
        "invoices": "invoices",
        "payout_requests": "payout_requests"
    },
    "communication": {
        "messages": "messages",
        "notifications": "notifications",
        "email_templates": "email_templates",
        "communication_logs": "communication_logs"
    },
    "integration": {
        "ats_integrations": "ats_integrations",
        "job_board_syncs": "job_board_syncs",
        "api_keys": "api_keys",
        "webhook_events": "webhook_events"
    },
    "audit": {
        "activity_logs": "activity_logs",
        "data_access_logs": "data_access_logs"
    }
}


# =====================================================
# CORE SCHEMA MODELS
# =====================================================

class UserDocument(BaseModel):
    """Core user document schema"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: EmailStr
    phone: Optional[str] = None
    password_hash: str
    is_active: bool = True
    is_verified: bool = False
    last_login: Optional[str] = None
    failed_login_attempts: int = 0
    locked_until: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class RoleDocument(BaseModel):
    """Role definition document"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: Optional[str] = None
    permissions: Dict[str, Any] = {}
    hierarchy_level: int = 5
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class UserRoleDocument(BaseModel):
    """User-role assignment document"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    role_id: str
    role_name: str  # Denormalized for quick access
    assigned_by: Optional[str] = None
    assigned_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    expires_at: Optional[str] = None
    is_active: bool = True


class UserProfileDocument(BaseModel):
    """Extended user profile document"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    profile_type: str = "candidate"
    company_id: Optional[str] = None
    profile_data: Dict[str, Any] = {}  # Flexible data for different profile types
    avatar_url: Optional[str] = None
    bio: Optional[str] = None
    location: Optional[str] = None
    timezone: str = "Asia/Kolkata"
    language_preference: str = "en"
    privacy_settings: Dict[str, Any] = {
        "profile_visible": True,
        "show_email": False,
        "show_phone": False
    }
    # Additional fields
    skills: List[str] = []
    linkedin_url: Optional[str] = None
    portfolio_url: Optional[str] = None
    expected_salary: Optional[float] = None
    notice_period_days: Optional[int] = None
    willing_to_relocate: bool = False
    preferred_locations: List[str] = []
    profile_completion: int = 0
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class UserSessionDocument(BaseModel):
    """User session document"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    session_token: str
    refresh_token: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    device_info: Dict[str, Any] = {}
    expires_at: str
    is_active: bool = True
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


# =====================================================
# BUSINESS SCHEMA MODELS
# =====================================================

class CompanyDocument(BaseModel):
    """Company document schema"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    legal_name: Optional[str] = None
    industry: Optional[str] = None
    company_size: Optional[str] = None  # startup, small, medium, large, enterprise
    website: Optional[str] = None
    description: Optional[str] = None
    logo_url: Optional[str] = None
    headquarters_location: Optional[str] = None
    founded_year: Optional[int] = None
    company_type: Optional[str] = None  # startup, corporation, government, ngo
    tax_id: Optional[str] = None  # Should be encrypted
    billing_address: Dict[str, Any] = {}
    contact_info: Dict[str, Any] = {}
    settings: Dict[str, Any] = {}
    is_active: bool = True
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class JobDocument(BaseModel):
    """Job posting document schema"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    company_id: str
    company_name: Optional[str] = None  # Denormalized
    title: str
    description: str
    requirements: Optional[str] = None
    responsibilities: Optional[str] = None
    location: Optional[str] = None
    remote_policy: str = "onsite"  # remote, hybrid, onsite
    employment_type: str = "full_time"  # full_time, part_time, contract, internship
    experience_level: Optional[str] = None  # entry, junior, mid, senior, lead, executive
    experience_min: int = 0
    experience_max: Optional[int] = None
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    salary_currency: str = "INR"
    benefits: Optional[str] = None
    skills_required: List[str] = []
    skills_preferred: List[str] = []
    qualifications: Dict[str, Any] = {}
    education_required: str = "bachelors"
    application_deadline: Optional[str] = None
    positions_available: int = 1
    job_status: str = "draft"
    referral_bonus: Optional[float] = None
    urgency_level: str = "normal"  # urgent, high, normal, low
    posted_by: Optional[str] = None
    posted_at: Optional[str] = None
    view_count: int = 0
    application_count: int = 0
    last_modified: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class CandidateDocument(BaseModel):
    """Candidate profile document schema"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    resume_url: Optional[str] = None
    portfolio_url: Optional[str] = None
    current_title: Optional[str] = None
    current_company: Optional[str] = None
    experience_years: int = 0
    skills: List[str] = []
    education: List[Dict[str, Any]] = []  # [{degree, institution, year, field}]
    certifications: List[Dict[str, Any]] = []
    work_history: List[Dict[str, Any]] = []  # [{company, title, start, end, description}]
    expected_salary: Optional[float] = None
    current_salary: Optional[float] = None
    preferred_locations: List[str] = []
    availability: str = "immediate"  # immediate, 2weeks, 1month, 3months
    job_preferences: Dict[str, Any] = {}
    is_available_for_referral: bool = True
    visibility_settings: Dict[str, Any] = {"public": True}
    # Parsed resume data
    parsed_resume_data: Dict[str, Any] = {}
    overall_score: Optional[int] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class ApplicationDocument(BaseModel):
    """Job application document schema"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    job_id: str
    job_title: Optional[str] = None  # Denormalized
    candidate_id: str
    candidate_name: Optional[str] = None  # Denormalized
    candidate_email: Optional[str] = None  # Denormalized
    referral_id: Optional[str] = None
    recruiter_id: Optional[str] = None
    application_status: str = "submitted"
    cover_letter: Optional[str] = None
    resume_url: Optional[str] = None
    resume_id: Optional[str] = None
    additional_documents: List[Dict[str, str]] = []
    applied_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    last_status_change: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    status_history: List[Dict[str, Any]] = []
    recruiter_notes: Optional[str] = None
    screening_score: Optional[int] = None
    screening_result: Dict[str, Any] = {}
    match_score: Optional[float] = None
    match_details: Dict[str, Any] = {}
    interview_feedback: List[Dict[str, Any]] = []
    rejection_reason: Optional[str] = None
    offer_details: Dict[str, Any] = {}
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class ReferralDocument(BaseModel):
    """Referral document schema"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    job_id: str
    job_title: Optional[str] = None  # Denormalized
    candidate_id: Optional[str] = None
    candidate_name: str
    candidate_email: str
    candidate_phone: Optional[str] = None
    referrer_id: str
    referrer_name: Optional[str] = None  # Denormalized
    referral_status: str = "submitted"
    referral_notes: Optional[str] = None
    commission_rate: Optional[float] = None
    commission_amount: Optional[float] = None
    application_id: Optional[str] = None
    is_hired: bool = False
    hired_date: Optional[str] = None
    probation_end_date: Optional[str] = None
    commission_paid: bool = False
    quality_score: Optional[int] = None
    feedback: Optional[str] = None
    submitted_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class BackgroundVerificationDocument(BaseModel):
    """Background verification document schema"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    candidate_id: str
    candidate_name: Optional[str] = None
    application_id: Optional[str] = None
    requested_by: str
    requested_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    verification_types: List[str] = []  # employment, education, criminal, medical, address, identity
    verification_status: str = "pending"
    priority: str = "normal"  # urgent, high, normal, low
    deadline: Optional[str] = None
    special_instructions: Optional[str] = None
    checks: List[Dict[str, Any]] = []  # Individual verification checks
    provider_name: Optional[str] = None
    provider_reference: Optional[str] = None
    documents_submitted: List[Dict[str, str]] = []
    verification_results: Dict[str, Any] = {}
    verification_report_url: Optional[str] = None
    overall_result: Optional[str] = None  # clear, discrepancy, failed
    completion_percentage: int = 0
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    completed_by: Optional[str] = None
    expires_at: Optional[str] = None
    cost: Optional[float] = None
    notes: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class InterviewDocument(BaseModel):
    """Interview document schema"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    application_id: str
    candidate_id: str
    job_id: str
    interview_type: str  # phone, video, onsite, technical, hr, panel
    interview_round: int = 1
    scheduled_at: str
    duration_minutes: int = 60
    interviewer_ids: List[str] = []
    interviewer_names: List[str] = []  # Denormalized
    location: Optional[str] = None
    meeting_link: Optional[str] = None
    interview_status: str = "scheduled"  # scheduled, completed, cancelled, rescheduled, no_show
    feedback: Dict[str, Any] = {}
    rating: Optional[int] = None  # 1-10
    scores: Dict[str, int] = {}  # {technical: 8, communication: 7, cultural_fit: 9}
    recommendation: Optional[str] = None  # hire, reject, next_round
    notes: Optional[str] = None
    preparation_notes: Optional[str] = None
    scheduled_by: str
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class AssessmentDocument(BaseModel):
    """Assessment document schema"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    candidate_id: str
    job_id: Optional[str] = None
    application_id: Optional[str] = None
    assessment_type: str  # technical, behavioral, cognitive, coding
    assessment_name: str
    assessment_provider: Optional[str] = None
    assessment_url: Optional[str] = None
    duration_minutes: Optional[int] = None
    max_score: Optional[float] = None
    achieved_score: Optional[float] = None
    percentile_rank: Optional[int] = None
    assessment_status: str = "assigned"  # assigned, started, completed, expired
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    expires_at: Optional[str] = None
    results: Dict[str, Any] = {}
    feedback: Optional[str] = None
    assigned_by: str
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


# =====================================================
# FINANCIAL SCHEMA MODELS
# =====================================================

class CommissionDocument(BaseModel):
    """Commission document schema"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    referral_id: Optional[str] = None
    application_id: Optional[str] = None
    user_id: str  # Commission recipient
    user_name: Optional[str] = None
    commission_type: str  # referral, performance, bonus
    # Calculation details
    base_amount: float  # Annual package
    package_level: str  # entry, junior, mid_level, senior, leadership, executive
    base_commission_rate: float
    user_tier: str  # bronze, silver, gold, platinum, diamond
    tier_multiplier: float
    effective_rate: float
    gross_commission: float
    # Deductions
    tds_rate: float = 0
    tds_amount: float = 0
    platform_fee_rate: float = 0.05
    platform_fee: float = 0
    other_deductions: float = 0
    # Final amounts
    net_commission: float
    currency: str = "INR"
    # Status and dates
    commission_status: str = "pending"
    earned_date: Optional[str] = None
    payment_due_date: Optional[str] = None
    payment_date: Optional[str] = None
    payment_reference: Optional[str] = None
    notes: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class PaymentDocument(BaseModel):
    """Payment transaction document schema"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    payer_id: Optional[str] = None
    payer_name: Optional[str] = None
    payee_id: str
    payee_name: Optional[str] = None
    related_entity_type: str  # commission, invoice, refund, subscription
    related_entity_id: Optional[str] = None
    payment_method: str  # card, bank_transfer, wallet, upi
    payment_gateway: Optional[str] = None  # razorpay, stripe, paypal
    gateway_transaction_id: Optional[str] = None
    amount: float
    currency: str = "INR"
    payment_status: str = "pending"
    failure_reason: Optional[str] = None
    payment_date: Optional[str] = None
    settlement_date: Optional[str] = None
    gateway_fee: float = 0
    tax_amount: float = 0
    net_amount: float = 0
    bank_reference: Optional[str] = None
    metadata: Dict[str, Any] = {}
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class InvoiceDocument(BaseModel):
    """Invoice document schema"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    invoice_number: str
    company_id: str
    company_name: Optional[str] = None
    billing_address: Dict[str, Any] = {}
    billing_period_start: Optional[str] = None
    billing_period_end: Optional[str] = None
    line_items: List[Dict[str, Any]] = []  # [{description, quantity, unit_price, amount}]
    subtotal: float = 0
    tax_rate: float = 0.18  # GST
    tax_amount: float = 0
    total_amount: float = 0
    currency: str = "INR"
    invoice_status: str = "draft"  # draft, sent, paid, overdue, cancelled
    issued_date: Optional[str] = None
    due_date: Optional[str] = None
    paid_date: Optional[str] = None
    payment_terms: int = 30  # days
    notes: Optional[str] = None
    pdf_url: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class PayoutRequestDocument(BaseModel):
    """Payout request document schema"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    user_name: Optional[str] = None
    requested_amount: float
    currency: str = "INR"
    payout_method: str  # bank_transfer, paypal, wallet
    bank_details: Dict[str, Any] = {}  # Encrypted
    request_status: str = "pending"  # pending, approved, processing, completed, rejected
    approved_by: Optional[str] = None
    approved_at: Optional[str] = None
    processed_at: Optional[str] = None
    transaction_reference: Optional[str] = None
    fees_deducted: float = 0
    final_amount: float = 0
    rejection_reason: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


# =====================================================
# COMMUNICATION SCHEMA MODELS
# =====================================================

class MessageDocument(BaseModel):
    """Message document schema"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    sender_id: str
    sender_name: Optional[str] = None
    recipient_id: str
    recipient_name: Optional[str] = None
    related_entity_type: Optional[str] = None  # job, application, referral
    related_entity_id: Optional[str] = None
    subject: Optional[str] = None
    message_body: str
    message_type: str = "text"  # text, file, system
    attachments: List[Dict[str, str]] = []
    is_read: bool = False
    read_at: Optional[str] = None
    replied_to_message_id: Optional[str] = None
    priority: str = "normal"  # urgent, high, normal, low
    expires_at: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class NotificationDocument(BaseModel):
    """Notification document schema"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    notification_type: str  # application_update, interview_scheduled, offer_received, etc.
    title: str
    message: str
    action_url: Optional[str] = None
    action_text: Optional[str] = None
    channels: List[str] = ["in_app"]  # email, sms, push, in_app
    delivery_status: Dict[str, str] = {}  # {email: "sent", push: "delivered"}
    is_read: bool = False
    read_at: Optional[str] = None
    priority: str = "normal"
    scheduled_at: Optional[str] = None
    sent_at: Optional[str] = None
    expires_at: Optional[str] = None
    metadata: Dict[str, Any] = {}
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class EmailTemplateDocument(BaseModel):
    """Email template document schema"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    template_name: str
    template_type: str  # transactional, marketing, system
    subject_template: str
    html_template: str
    text_template: Optional[str] = None
    variables: List[str] = []  # Available template variables
    language: str = "en"
    is_active: bool = True
    created_by: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class CommunicationLogDocument(BaseModel):
    """Communication log document schema"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: Optional[str] = None
    communication_type: str  # email, sms, push, call
    channel: Optional[str] = None  # sendgrid, twilio, firebase
    recipient: str
    subject: Optional[str] = None
    message_content: Optional[str] = None
    delivery_status: str = "pending"
    delivery_timestamp: Optional[str] = None
    response_data: Dict[str, Any] = {}
    cost: Optional[float] = None
    error_message: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


# =====================================================
# INTEGRATION SCHEMA MODELS
# =====================================================

class ATSIntegrationDocument(BaseModel):
    """ATS integration document schema"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    company_id: str
    ats_provider: str  # linkedin, indeed, monster, workday
    integration_name: Optional[str] = None
    api_endpoint: Optional[str] = None
    authentication_type: str  # oauth, api_key, bearer
    credentials: Dict[str, Any] = {}  # Encrypted
    sync_settings: Dict[str, Any] = {}
    last_sync_at: Optional[str] = None
    sync_status: str = "active"
    error_count: int = 0
    last_error: Optional[str] = None
    is_active: bool = True
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class JobBoardSyncDocument(BaseModel):
    """Job board sync document schema"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    job_id: str
    ats_integration_id: str
    external_job_id: Optional[str] = None
    sync_status: str = "pending"
    last_sync_at: Optional[str] = None
    sync_data: Dict[str, Any] = {}
    application_count: int = 0
    view_count: int = 0
    error_message: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class APIKeyDocument(BaseModel):
    """API key document schema"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    key_name: str
    api_key: str  # Hashed
    api_secret: Optional[str] = None  # Encrypted
    permissions: Dict[str, List[str]] = {}
    rate_limit_per_hour: int = 1000
    allowed_ips: List[str] = []
    is_active: bool = True
    last_used_at: Optional[str] = None
    usage_count: int = 0
    expires_at: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class WebhookEventDocument(BaseModel):
    """Webhook event document schema"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    event_type: str
    source_system: Optional[str] = None
    target_url: str
    payload: Dict[str, Any]
    signature: Optional[str] = None
    delivery_status: str = "pending"
    delivery_attempts: int = 0
    last_attempt_at: Optional[str] = None
    response_status: Optional[int] = None
    response_body: Optional[str] = None
    next_retry_at: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


# =====================================================
# AUDIT SCHEMA MODELS
# =====================================================

class ActivityLogDocument(BaseModel):
    """Activity log document schema"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: Optional[str] = None
    user_email: Optional[str] = None
    action: str  # login, logout, create, update, delete, view, export
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    old_values: Optional[Dict[str, Any]] = None
    new_values: Optional[Dict[str, Any]] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    session_id: Optional[str] = None
    result: str = "success"  # success, failure, partial
    error_message: Optional[str] = None
    duration_ms: Optional[int] = None
    metadata: Dict[str, Any] = {}
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class DataAccessLogDocument(BaseModel):
    """Data access log for GDPR compliance"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    accessed_user_id: str
    data_type: str  # personal_info, financial, employment
    access_type: str  # read, write, delete, export
    field_names: List[str] = []
    justification: Optional[str] = None
    ip_address: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
