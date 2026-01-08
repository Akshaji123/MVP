"""
Companies API Router
HiringReferrals Platform
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import uuid

router = APIRouter(prefix="/companies", tags=["Companies"])


# ============= PYDANTIC MODELS =============

class AddressModel(BaseModel):
    street: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: str = "India"
    pincode: Optional[str] = None


class ContactInfoModel(BaseModel):
    primary_email: Optional[EmailStr] = None
    phone: Optional[str] = None
    hr_email: Optional[EmailStr] = None
    hr_phone: Optional[str] = None


class CompanyCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=200)
    legal_name: Optional[str] = Field(None, max_length=200)
    industry: Optional[str] = Field(None, max_length=100)
    company_size: Optional[str] = Field(None, pattern="^(startup|small|medium|large|enterprise)$")
    website: Optional[str] = Field(None, max_length=500)
    description: Optional[str] = None
    logo_url: Optional[str] = Field(None, max_length=500)
    headquarters_location: Optional[str] = Field(None, max_length=200)
    founded_year: Optional[int] = Field(None, ge=1800, le=2100)
    company_type: Optional[str] = Field(None, pattern="^(startup|corporation|government|ngo)$")
    billing_address: Optional[AddressModel] = None
    contact_info: Optional[ContactInfoModel] = None


class CompanyUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=200)
    legal_name: Optional[str] = Field(None, max_length=200)
    industry: Optional[str] = Field(None, max_length=100)
    company_size: Optional[str] = Field(None, pattern="^(startup|small|medium|large|enterprise)$")
    website: Optional[str] = Field(None, max_length=500)
    description: Optional[str] = None
    logo_url: Optional[str] = Field(None, max_length=500)
    headquarters_location: Optional[str] = Field(None, max_length=200)
    founded_year: Optional[int] = Field(None, ge=1800, le=2100)
    company_type: Optional[str] = Field(None, pattern="^(startup|corporation|government|ngo)$")
    billing_address: Optional[AddressModel] = None
    contact_info: Optional[ContactInfoModel] = None
    is_active: Optional[bool] = None


class CompanyResponse(BaseModel):
    id: str
    name: str
    legal_name: Optional[str] = None
    industry: Optional[str] = None
    company_size: Optional[str] = None
    website: Optional[str] = None
    description: Optional[str] = None
    logo_url: Optional[str] = None
    headquarters_location: Optional[str] = None
    founded_year: Optional[int] = None
    company_type: Optional[str] = None
    billing_address: Optional[Dict[str, Any]] = None
    contact_info: Optional[Dict[str, Any]] = None
    is_active: bool = True
    created_at: str
    updated_at: str


# ============= ROUTE HANDLERS =============

def get_company_router(db, get_current_user):
    """Create router with database dependency"""
    
    @router.post("", response_model=CompanyResponse)
    async def create_company(
        company: CompanyCreate,
        current_user: dict = Depends(get_current_user)
    ):
        """Create a new company"""
        if current_user["role"] not in ["admin", "super_admin"]:
            raise HTTPException(status_code=403, detail="Admin access required")
        
        company_doc = {
            "id": str(uuid.uuid4()),
            **company.dict(exclude_none=True),
            "is_active": True,
            "settings": {},
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        await db.companies.insert_one(company_doc)
        return company_doc
    
    @router.get("", response_model=List[CompanyResponse])
    async def list_companies(
        skip: int = 0,
        limit: int = 50,
        industry: Optional[str] = None,
        is_active: bool = True,
        current_user: dict = Depends(get_current_user)
    ):
        """List all companies"""
        query = {"is_active": is_active}
        if industry:
            query["industry"] = industry
        
        companies = await db.companies.find(
            query, {"_id": 0}
        ).skip(skip).limit(limit).to_list(limit)
        
        return companies
    
    @router.get("/{company_id}", response_model=CompanyResponse)
    async def get_company(
        company_id: str,
        current_user: dict = Depends(get_current_user)
    ):
        """Get company by ID"""
        company = await db.companies.find_one({"id": company_id}, {"_id": 0})
        if not company:
            raise HTTPException(status_code=404, detail="Company not found")
        return company
    
    @router.put("/{company_id}", response_model=CompanyResponse)
    async def update_company(
        company_id: str,
        company: CompanyUpdate,
        current_user: dict = Depends(get_current_user)
    ):
        """Update company"""
        if current_user["role"] not in ["admin", "super_admin", "client"]:
            raise HTTPException(status_code=403, detail="Access denied")
        
        existing = await db.companies.find_one({"id": company_id})
        if not existing:
            raise HTTPException(status_code=404, detail="Company not found")
        
        update_data = company.dict(exclude_none=True)
        update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
        
        await db.companies.update_one(
            {"id": company_id},
            {"$set": update_data}
        )
        
        updated = await db.companies.find_one({"id": company_id}, {"_id": 0})
        return updated
    
    @router.delete("/{company_id}")
    async def delete_company(
        company_id: str,
        current_user: dict = Depends(get_current_user)
    ):
        """Soft delete company"""
        if current_user["role"] not in ["admin", "super_admin"]:
            raise HTTPException(status_code=403, detail="Admin access required")
        
        result = await db.companies.update_one(
            {"id": company_id},
            {"$set": {"is_active": False, "updated_at": datetime.now(timezone.utc).isoformat()}}
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Company not found")
        
        return {"status": "deleted", "company_id": company_id}
    
    @router.get("/{company_id}/jobs")
    async def get_company_jobs(
        company_id: str,
        status: Optional[str] = None,
        current_user: dict = Depends(get_current_user)
    ):
        """Get jobs for a company"""
        query = {"company_id": company_id}
        if status:
            query["job_status"] = status
        
        jobs = await db.jobs.find(query, {"_id": 0}).to_list(100)
        return {"company_id": company_id, "jobs": jobs, "total": len(jobs)}
    
    @router.get("/{company_id}/stats")
    async def get_company_stats(
        company_id: str,
        current_user: dict = Depends(get_current_user)
    ):
        """Get company statistics"""
        # Count jobs
        total_jobs = await db.jobs.count_documents({"company_id": company_id})
        active_jobs = await db.jobs.count_documents({"company_id": company_id, "job_status": "published"})
        
        # Count applications
        job_ids = await db.jobs.distinct("id", {"company_id": company_id})
        total_applications = await db.applications.count_documents({"job_id": {"$in": job_ids}})
        hired = await db.applications.count_documents({"job_id": {"$in": job_ids}, "application_status": "hired"})
        
        return {
            "company_id": company_id,
            "stats": {
                "total_jobs": total_jobs,
                "active_jobs": active_jobs,
                "total_applications": total_applications,
                "hired_candidates": hired,
                "conversion_rate": f"{(hired / total_applications * 100) if total_applications > 0 else 0:.1f}%"
            }
        }
    
    return router
