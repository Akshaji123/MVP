"""
Financial API Router - Commissions, Payments, Invoices, Payouts
HiringReferrals Platform
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone, timedelta
import uuid

router = APIRouter(prefix="/financial", tags=["Financial"])


# ============= PYDANTIC MODELS =============

class CommissionCreate(BaseModel):
    referral_id: Optional[str] = None
    application_id: Optional[str] = None
    user_id: str
    commission_type: str = Field(..., pattern="^(referral|performance|bonus)$")
    base_amount: float = Field(..., gt=0)
    notes: Optional[str] = None


class PaymentCreate(BaseModel):
    payee_id: str
    related_entity_type: str = Field(..., pattern="^(commission|invoice|refund|subscription)$")
    related_entity_id: Optional[str] = None
    payment_method: str = Field(..., pattern="^(card|bank_transfer|wallet|upi)$")
    amount: float = Field(..., gt=0)
    currency: str = Field("INR", pattern="^(INR|USD)$")


class InvoiceCreate(BaseModel):
    company_id: str
    billing_period_start: Optional[str] = None
    billing_period_end: Optional[str] = None
    line_items: List[Dict[str, Any]]
    tax_rate: float = Field(0.18, ge=0, le=1)
    payment_terms: int = Field(30, ge=1, le=90)
    notes: Optional[str] = None


class InvoiceLineItem(BaseModel):
    description: str
    quantity: int = Field(1, ge=1)
    unit_price: float = Field(..., gt=0)


class PayoutRequestCreate(BaseModel):
    requested_amount: float = Field(..., gt=0)
    payout_method: str = Field(..., pattern="^(bank_transfer|paypal|wallet)$")
    bank_details: Optional[Dict[str, Any]] = None


# ============= RESPONSE MODELS =============

class CommissionResponse(BaseModel):
    id: str
    referral_id: Optional[str] = None
    application_id: Optional[str] = None
    user_id: str
    user_name: Optional[str] = None
    commission_type: str
    base_amount: float
    package_level: str
    base_commission_rate: float
    user_tier: str
    tier_multiplier: float
    effective_rate: float
    gross_commission: float
    tds_rate: float
    tds_amount: float
    platform_fee_rate: float
    platform_fee: float
    net_commission: float
    currency: str
    commission_status: str
    earned_date: Optional[str] = None
    payment_due_date: Optional[str] = None
    created_at: str


class PaymentResponse(BaseModel):
    id: str
    payer_id: Optional[str] = None
    payee_id: str
    payee_name: Optional[str] = None
    related_entity_type: str
    related_entity_id: Optional[str] = None
    payment_method: str
    amount: float
    currency: str
    payment_status: str
    gateway_transaction_id: Optional[str] = None
    created_at: str


class InvoiceResponse(BaseModel):
    id: str
    invoice_number: str
    company_id: str
    company_name: Optional[str] = None
    line_items: List[Dict[str, Any]]
    subtotal: float
    tax_rate: float
    tax_amount: float
    total_amount: float
    currency: str
    invoice_status: str
    issued_date: Optional[str] = None
    due_date: Optional[str] = None
    created_at: str


# ============= ROUTE HANDLERS =============

def get_financial_router(db, get_current_user, commission_calculator):
    """Create router with database dependency"""
    
    # ============= COMMISSIONS =============
    
    @router.post("/commissions", response_model=CommissionResponse)
    async def create_commission(
        commission: CommissionCreate,
        current_user: dict = Depends(get_current_user)
    ):
        """Create a new commission record"""
        if current_user["role"] not in ["admin", "super_admin"]:
            raise HTTPException(status_code=403, detail="Admin access required")
        
        # Calculate commission using the calculator service
        calc_result = await commission_calculator.calculate_commission(
            user_id=commission.user_id,
            annual_package=commission.base_amount,
            currency="INR"
        )
        
        # Get user name
        user = await db.users.find_one({"id": commission.user_id}, {"_id": 0, "full_name": 1})
        
        commission_doc = {
            "id": str(uuid.uuid4()),
            "referral_id": commission.referral_id,
            "application_id": commission.application_id,
            "user_id": commission.user_id,
            "user_name": user.get("full_name") if user else None,
            "commission_type": commission.commission_type,
            "base_amount": commission.base_amount,
            "package_level": calc_result["package_level"],
            "base_commission_rate": calc_result["calculation_details"]["base_commission_rate"],
            "user_tier": calc_result["user_tier"],
            "tier_multiplier": calc_result["calculation_details"]["tier_multiplier"],
            "effective_rate": calc_result["calculation_details"]["effective_rate"],
            "gross_commission": calc_result["calculation_details"]["gross_commission"],
            "tds_rate": calc_result["calculation_details"]["tds_rate"],
            "tds_amount": calc_result["calculation_details"]["tds_amount"],
            "platform_fee_rate": calc_result["calculation_details"]["platform_fee_rate"],
            "platform_fee": calc_result["calculation_details"]["platform_fee"],
            "net_commission": calc_result["calculation_details"]["net_commission"],
            "currency": "INR",
            "commission_status": "pending",
            "earned_date": datetime.now(timezone.utc).isoformat(),
            "payment_due_date": (datetime.now(timezone.utc) + timedelta(days=30)).isoformat(),
            "notes": commission.notes,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        await db.commissions.insert_one(commission_doc)
        
        # Update user gamification points
        await db.user_gamification.update_one(
            {"user_id": commission.user_id},
            {"$inc": {"total_points": 100}},
            upsert=True
        )
        
        return commission_doc
    
    @router.get("/commissions", response_model=List[CommissionResponse])
    async def list_commissions(
        skip: int = 0,
        limit: int = 50,
        status: Optional[str] = None,
        user_id: Optional[str] = None,
        current_user: dict = Depends(get_current_user)
    ):
        """List commissions"""
        query = {}
        
        # Filter by role
        if current_user["role"] not in ["admin", "super_admin"]:
            query["user_id"] = current_user["id"]
        elif user_id:
            query["user_id"] = user_id
        
        if status:
            query["commission_status"] = status
        
        commissions = await db.commissions.find(
            query, {"_id": 0}
        ).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)
        
        return commissions
    
    @router.get("/commissions/{commission_id}", response_model=CommissionResponse)
    async def get_commission(
        commission_id: str,
        current_user: dict = Depends(get_current_user)
    ):
        """Get commission by ID"""
        commission = await db.commissions.find_one({"id": commission_id}, {"_id": 0})
        if not commission:
            raise HTTPException(status_code=404, detail="Commission not found")
        
        # Check access
        if current_user["role"] not in ["admin", "super_admin"] and commission["user_id"] != current_user["id"]:
            raise HTTPException(status_code=403, detail="Access denied")
        
        return commission
    
    @router.put("/commissions/{commission_id}/status")
    async def update_commission_status(
        commission_id: str,
        new_status: str,
        current_user: dict = Depends(get_current_user)
    ):
        """Update commission status"""
        if current_user["role"] not in ["admin", "super_admin"]:
            raise HTTPException(status_code=403, detail="Admin access required")
        
        valid_statuses = ["pending", "approved", "processing", "paid", "cancelled"]
        if new_status not in valid_statuses:
            raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {valid_statuses}")
        
        result = await db.commissions.update_one(
            {"id": commission_id},
            {"$set": {
                "commission_status": new_status,
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "payment_date": datetime.now(timezone.utc).isoformat() if new_status == "paid" else None
            }}
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Commission not found")
        
        return {"status": "updated", "new_status": new_status}
    
    # ============= PAYMENTS =============
    
    @router.post("/payments", response_model=PaymentResponse)
    async def create_payment(
        payment: PaymentCreate,
        current_user: dict = Depends(get_current_user)
    ):
        """Create a new payment record"""
        if current_user["role"] not in ["admin", "super_admin"]:
            raise HTTPException(status_code=403, detail="Admin access required")
        
        # Get payee name
        payee = await db.users.find_one({"id": payment.payee_id}, {"_id": 0, "full_name": 1})
        
        payment_doc = {
            "id": str(uuid.uuid4()),
            "payer_id": None,  # Platform
            "payer_name": "HiringReferrals",
            "payee_id": payment.payee_id,
            "payee_name": payee.get("full_name") if payee else None,
            "related_entity_type": payment.related_entity_type,
            "related_entity_id": payment.related_entity_id,
            "payment_method": payment.payment_method,
            "payment_gateway": None,
            "gateway_transaction_id": None,
            "amount": payment.amount,
            "currency": payment.currency,
            "payment_status": "pending",
            "failure_reason": None,
            "payment_date": None,
            "settlement_date": None,
            "gateway_fee": 0,
            "tax_amount": 0,
            "net_amount": payment.amount,
            "bank_reference": None,
            "metadata": {},
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        await db.payments.insert_one(payment_doc)
        return payment_doc
    
    @router.get("/payments", response_model=List[PaymentResponse])
    async def list_payments(
        skip: int = 0,
        limit: int = 50,
        status: Optional[str] = None,
        current_user: dict = Depends(get_current_user)
    ):
        """List payments"""
        query = {}
        
        if current_user["role"] not in ["admin", "super_admin"]:
            query["payee_id"] = current_user["id"]
        
        if status:
            query["payment_status"] = status
        
        payments = await db.payments.find(
            query, {"_id": 0}
        ).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)
        
        return payments
    
    @router.put("/payments/{payment_id}/process")
    async def process_payment(
        payment_id: str,
        transaction_id: Optional[str] = None,
        current_user: dict = Depends(get_current_user)
    ):
        """Process a payment"""
        if current_user["role"] not in ["admin", "super_admin"]:
            raise HTTPException(status_code=403, detail="Admin access required")
        
        payment = await db.payments.find_one({"id": payment_id})
        if not payment:
            raise HTTPException(status_code=404, detail="Payment not found")
        
        # Simulate payment processing
        await db.payments.update_one(
            {"id": payment_id},
            {"$set": {
                "payment_status": "completed",
                "gateway_transaction_id": transaction_id or f"TXN_{uuid.uuid4().hex[:12].upper()}",
                "payment_date": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat()
            }}
        )
        
        # If linked to commission, update commission status
        if payment["related_entity_type"] == "commission" and payment["related_entity_id"]:
            await db.commissions.update_one(
                {"id": payment["related_entity_id"]},
                {"$set": {
                    "commission_status": "paid",
                    "payment_date": datetime.now(timezone.utc).isoformat()
                }}
            )
        
        return {"status": "processed", "payment_id": payment_id}
    
    # ============= INVOICES =============
    
    @router.post("/invoices", response_model=InvoiceResponse)
    async def create_invoice(
        invoice: InvoiceCreate,
        current_user: dict = Depends(get_current_user)
    ):
        """Create a new invoice"""
        if current_user["role"] not in ["admin", "super_admin"]:
            raise HTTPException(status_code=403, detail="Admin access required")
        
        # Get company
        company = await db.companies.find_one({"id": invoice.company_id}, {"_id": 0})
        if not company:
            raise HTTPException(status_code=404, detail="Company not found")
        
        # Calculate totals
        subtotal = sum(item.get("quantity", 1) * item.get("unit_price", 0) for item in invoice.line_items)
        tax_amount = subtotal * invoice.tax_rate
        total_amount = subtotal + tax_amount
        
        # Generate invoice number
        count = await db.invoices.count_documents({})
        invoice_number = f"INV-{datetime.now().strftime('%Y%m')}-{count + 1:04d}"
        
        invoice_doc = {
            "id": str(uuid.uuid4()),
            "invoice_number": invoice_number,
            "company_id": invoice.company_id,
            "company_name": company.get("name"),
            "billing_address": company.get("billing_address", {}),
            "billing_period_start": invoice.billing_period_start,
            "billing_period_end": invoice.billing_period_end,
            "line_items": invoice.line_items,
            "subtotal": round(subtotal, 2),
            "tax_rate": invoice.tax_rate,
            "tax_amount": round(tax_amount, 2),
            "total_amount": round(total_amount, 2),
            "currency": "INR",
            "invoice_status": "draft",
            "issued_date": None,
            "due_date": None,
            "paid_date": None,
            "payment_terms": invoice.payment_terms,
            "notes": invoice.notes,
            "pdf_url": None,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        await db.invoices.insert_one(invoice_doc)
        return invoice_doc
    
    @router.get("/invoices", response_model=List[InvoiceResponse])
    async def list_invoices(
        skip: int = 0,
        limit: int = 50,
        status: Optional[str] = None,
        company_id: Optional[str] = None,
        current_user: dict = Depends(get_current_user)
    ):
        """List invoices"""
        if current_user["role"] not in ["admin", "super_admin", "client"]:
            raise HTTPException(status_code=403, detail="Access denied")
        
        query = {}
        if status:
            query["invoice_status"] = status
        if company_id:
            query["company_id"] = company_id
        
        invoices = await db.invoices.find(
            query, {"_id": 0}
        ).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)
        
        return invoices
    
    @router.put("/invoices/{invoice_id}/send")
    async def send_invoice(
        invoice_id: str,
        current_user: dict = Depends(get_current_user)
    ):
        """Send an invoice"""
        if current_user["role"] not in ["admin", "super_admin"]:
            raise HTTPException(status_code=403, detail="Admin access required")
        
        invoice = await db.invoices.find_one({"id": invoice_id})
        if not invoice:
            raise HTTPException(status_code=404, detail="Invoice not found")
        
        issued_date = datetime.now(timezone.utc)
        due_date = issued_date + timedelta(days=invoice.get("payment_terms", 30))
        
        await db.invoices.update_one(
            {"id": invoice_id},
            {"$set": {
                "invoice_status": "sent",
                "issued_date": issued_date.isoformat(),
                "due_date": due_date.isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat()
            }}
        )
        
        return {"status": "sent", "invoice_id": invoice_id, "due_date": due_date.isoformat()}
    
    @router.put("/invoices/{invoice_id}/mark-paid")
    async def mark_invoice_paid(
        invoice_id: str,
        current_user: dict = Depends(get_current_user)
    ):
        """Mark invoice as paid"""
        if current_user["role"] not in ["admin", "super_admin"]:
            raise HTTPException(status_code=403, detail="Admin access required")
        
        result = await db.invoices.update_one(
            {"id": invoice_id},
            {"$set": {
                "invoice_status": "paid",
                "paid_date": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat()
            }}
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Invoice not found")
        
        return {"status": "paid", "invoice_id": invoice_id}
    
    # ============= PAYOUT REQUESTS =============
    
    @router.post("/payout-requests")
    async def create_payout_request(
        payout: PayoutRequestCreate,
        current_user: dict = Depends(get_current_user)
    ):
        """Request a payout"""
        # Check available balance (sum of paid commissions - paid payouts)
        paid_commissions = await db.commissions.aggregate([
            {"$match": {"user_id": current_user["id"], "commission_status": "paid"}},
            {"$group": {"_id": None, "total": {"$sum": "$net_commission"}}}
        ]).to_list(1)
        
        paid_payouts = await db.payout_requests.aggregate([
            {"$match": {"user_id": current_user["id"], "request_status": "completed"}},
            {"$group": {"_id": None, "total": {"$sum": "$final_amount"}}}
        ]).to_list(1)
        
        available = (paid_commissions[0]["total"] if paid_commissions else 0) - \
                   (paid_payouts[0]["total"] if paid_payouts else 0)
        
        if payout.requested_amount > available:
            raise HTTPException(
                status_code=400, 
                detail=f"Insufficient balance. Available: ₹{available:.2f}"
            )
        
        payout_doc = {
            "id": str(uuid.uuid4()),
            "user_id": current_user["id"],
            "user_name": current_user.get("full_name"),
            "requested_amount": payout.requested_amount,
            "currency": "INR",
            "payout_method": payout.payout_method,
            "bank_details": payout.bank_details or {},
            "request_status": "pending",
            "approved_by": None,
            "approved_at": None,
            "processed_at": None,
            "transaction_reference": None,
            "fees_deducted": 0,
            "final_amount": payout.requested_amount,
            "rejection_reason": None,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        await db.payout_requests.insert_one(payout_doc)
        return payout_doc
    
    @router.get("/payout-requests")
    async def list_payout_requests(
        skip: int = 0,
        limit: int = 50,
        status: Optional[str] = None,
        current_user: dict = Depends(get_current_user)
    ):
        """List payout requests"""
        query = {}
        
        if current_user["role"] not in ["admin", "super_admin"]:
            query["user_id"] = current_user["id"]
        
        if status:
            query["request_status"] = status
        
        payouts = await db.payout_requests.find(
            query, {"_id": 0}
        ).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)
        
        return {"payouts": payouts, "total": len(payouts)}
    
    @router.put("/payout-requests/{payout_id}/approve")
    async def approve_payout(
        payout_id: str,
        current_user: dict = Depends(get_current_user)
    ):
        """Approve a payout request"""
        if current_user["role"] not in ["admin", "super_admin"]:
            raise HTTPException(status_code=403, detail="Admin access required")
        
        result = await db.payout_requests.update_one(
            {"id": payout_id, "request_status": "pending"},
            {"$set": {
                "request_status": "approved",
                "approved_by": current_user["id"],
                "approved_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat()
            }}
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Payout request not found or not pending")
        
        return {"status": "approved", "payout_id": payout_id}
    
    # ============= DASHBOARD =============
    
    @router.get("/dashboard")
    async def get_financial_dashboard(
        current_user: dict = Depends(get_current_user)
    ):
        """Get financial dashboard summary"""
        if current_user["role"] not in ["admin", "super_admin"]:
            # User dashboard
            user_id = current_user["id"]
            
            # Total earnings
            earnings = await db.commissions.aggregate([
                {"$match": {"user_id": user_id}},
                {"$group": {
                    "_id": "$commission_status",
                    "total": {"$sum": "$net_commission"},
                    "count": {"$sum": 1}
                }}
            ]).to_list(10)
            
            earnings_by_status = {e["_id"]: {"total": e["total"], "count": e["count"]} for e in earnings}
            
            # Pending payouts
            pending_payouts = await db.payout_requests.count_documents({
                "user_id": user_id,
                "request_status": "pending"
            })
            
            return {
                "earnings": earnings_by_status,
                "total_earned": sum(e["total"] for e in earnings),
                "pending_payouts": pending_payouts
            }
        else:
            # Admin dashboard
            # Total commissions
            total_commissions = await db.commissions.aggregate([
                {"$group": {
                    "_id": "$commission_status",
                    "total": {"$sum": "$net_commission"},
                    "count": {"$sum": 1}
                }}
            ]).to_list(10)
            
            # Total payments
            total_payments = await db.payments.aggregate([
                {"$group": {
                    "_id": "$payment_status",
                    "total": {"$sum": "$amount"},
                    "count": {"$sum": 1}
                }}
            ]).to_list(10)
            
            # Pending invoices
            pending_invoices = await db.invoices.aggregate([
                {"$match": {"invoice_status": {"$in": ["draft", "sent"]}}},
                {"$group": {
                    "_id": "$invoice_status",
                    "total": {"$sum": "$total_amount"},
                    "count": {"$sum": 1}
                }}
            ]).to_list(10)
            
            return {
                "commissions": {c["_id"]: c for c in total_commissions},
                "payments": {p["_id"]: p for p in total_payments},
                "invoices": {i["_id"]: i for i in pending_invoices}
            }
    
    return router
