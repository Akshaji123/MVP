"""
Communication API Router - Messages, Notifications, Email Templates
HiringReferrals Platform
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import uuid

router = APIRouter(prefix="/communication", tags=["Communication"])


# ============= PYDANTIC MODELS =============

class MessageCreate(BaseModel):
    recipient_id: str
    subject: Optional[str] = Field(None, max_length=200)
    message_body: str = Field(..., min_length=1)
    message_type: str = Field("text", pattern="^(text|file|system)$")
    related_entity_type: Optional[str] = None
    related_entity_id: Optional[str] = None
    attachments: List[Dict[str, str]] = []
    priority: str = Field("normal", pattern="^(urgent|high|normal|low)$")


class MessageResponse(BaseModel):
    id: str
    sender_id: str
    sender_name: Optional[str] = None
    recipient_id: str
    recipient_name: Optional[str] = None
    subject: Optional[str] = None
    message_body: str
    message_type: str
    attachments: List[Dict[str, str]] = []
    is_read: bool
    read_at: Optional[str] = None
    priority: str
    created_at: str


class EmailTemplateCreate(BaseModel):
    template_name: str = Field(..., min_length=2, max_length=100)
    template_type: str = Field(..., pattern="^(transactional|marketing|system)$")
    subject_template: str
    html_template: str
    text_template: Optional[str] = None
    variables: List[str] = []
    language: str = Field("en", max_length=10)


class EmailTemplateUpdate(BaseModel):
    template_type: Optional[str] = Field(None, pattern="^(transactional|marketing|system)$")
    subject_template: Optional[str] = None
    html_template: Optional[str] = None
    text_template: Optional[str] = None
    variables: Optional[List[str]] = None
    is_active: Optional[bool] = None


class EmailTemplateResponse(BaseModel):
    id: str
    template_name: str
    template_type: str
    subject_template: str
    html_template: str
    text_template: Optional[str] = None
    variables: List[str]
    language: str
    is_active: bool
    created_at: str
    updated_at: str


# ============= ROUTE HANDLERS =============

def get_communication_router(db, get_current_user):
    """Create router with database dependency"""
    
    # ============= MESSAGES =============
    
    @router.post("/messages", response_model=MessageResponse)
    async def send_message(
        message: MessageCreate,
        current_user: dict = Depends(get_current_user)
    ):
        """Send a message to another user"""
        # Verify recipient exists
        recipient = await db.users.find_one({"id": message.recipient_id}, {"_id": 0, "full_name": 1})
        if not recipient:
            raise HTTPException(status_code=404, detail="Recipient not found")
        
        message_doc = {
            "id": str(uuid.uuid4()),
            "sender_id": current_user["id"],
            "sender_name": current_user.get("full_name"),
            "recipient_id": message.recipient_id,
            "recipient_name": recipient.get("full_name"),
            "subject": message.subject,
            "message_body": message.message_body,
            "message_type": message.message_type,
            "related_entity_type": message.related_entity_type,
            "related_entity_id": message.related_entity_id,
            "attachments": message.attachments,
            "is_read": False,
            "read_at": None,
            "replied_to_message_id": None,
            "priority": message.priority,
            "expires_at": None,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        await db.messages.insert_one(message_doc)
        
        # Create notification
        await db.notifications.insert_one({
            "id": str(uuid.uuid4()),
            "user_id": message.recipient_id,
            "notification_type": "new_message",
            "title": "New Message",
            "message": f"You have a new message from {current_user.get('full_name', 'Someone')}",
            "is_read": False,
            "created_at": datetime.now(timezone.utc).isoformat()
        })
        
        return message_doc
    
    @router.get("/messages/inbox", response_model=List[MessageResponse])
    async def get_inbox(
        skip: int = 0,
        limit: int = 50,
        unread_only: bool = False,
        current_user: dict = Depends(get_current_user)
    ):
        """Get user's inbox messages"""
        query = {"recipient_id": current_user["id"]}
        if unread_only:
            query["is_read"] = False
        
        messages = await db.messages.find(
            query, {"_id": 0}
        ).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)
        
        return messages
    
    @router.get("/messages/sent", response_model=List[MessageResponse])
    async def get_sent_messages(
        skip: int = 0,
        limit: int = 50,
        current_user: dict = Depends(get_current_user)
    ):
        """Get user's sent messages"""
        messages = await db.messages.find(
            {"sender_id": current_user["id"]}, {"_id": 0}
        ).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)
        
        return messages
    
    @router.get("/messages/unread-count")
    async def get_unread_count(
        current_user: dict = Depends(get_current_user)
    ):
        """Get count of unread messages"""
        count = await db.messages.count_documents({
            "recipient_id": current_user["id"],
            "is_read": False
        })
        return {"unread_count": count}
    
    @router.get("/messages/{message_id}", response_model=MessageResponse)
    async def get_message(
        message_id: str,
        current_user: dict = Depends(get_current_user)
    ):
        """Get a specific message"""
        message = await db.messages.find_one({"id": message_id}, {"_id": 0})
        if not message:
            raise HTTPException(status_code=404, detail="Message not found")
        
        # Check access
        if message["sender_id"] != current_user["id"] and message["recipient_id"] != current_user["id"]:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Mark as read if recipient
        if message["recipient_id"] == current_user["id"] and not message["is_read"]:
            await db.messages.update_one(
                {"id": message_id},
                {"$set": {"is_read": True, "read_at": datetime.now(timezone.utc).isoformat()}}
            )
            message["is_read"] = True
            message["read_at"] = datetime.now(timezone.utc).isoformat()
        
        return message
    
    @router.post("/messages/{message_id}/reply", response_model=MessageResponse)
    async def reply_to_message(
        message_id: str,
        reply: MessageCreate,
        current_user: dict = Depends(get_current_user)
    ):
        """Reply to a message"""
        original = await db.messages.find_one({"id": message_id})
        if not original:
            raise HTTPException(status_code=404, detail="Original message not found")
        
        # Determine recipient (original sender)
        recipient_id = original["sender_id"]
        recipient = await db.users.find_one({"id": recipient_id}, {"_id": 0, "full_name": 1})
        
        reply_doc = {
            "id": str(uuid.uuid4()),
            "sender_id": current_user["id"],
            "sender_name": current_user.get("full_name"),
            "recipient_id": recipient_id,
            "recipient_name": recipient.get("full_name") if recipient else None,
            "subject": f"Re: {original.get('subject', '')}",
            "message_body": reply.message_body,
            "message_type": reply.message_type,
            "related_entity_type": original.get("related_entity_type"),
            "related_entity_id": original.get("related_entity_id"),
            "attachments": reply.attachments,
            "is_read": False,
            "read_at": None,
            "replied_to_message_id": message_id,
            "priority": reply.priority,
            "expires_at": None,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        await db.messages.insert_one(reply_doc)
        return reply_doc
    
    @router.get("/messages/unread-count")
    async def get_unread_count(
        current_user: dict = Depends(get_current_user)
    ):
        """Get count of unread messages"""
        count = await db.messages.count_documents({
            "recipient_id": current_user["id"],
            "is_read": False
        })
        return {"unread_count": count}
    
    # ============= EMAIL TEMPLATES =============
    
    @router.post("/email-templates", response_model=EmailTemplateResponse)
    async def create_email_template(
        template: EmailTemplateCreate,
        current_user: dict = Depends(get_current_user)
    ):
        """Create a new email template"""
        if current_user["role"] not in ["admin", "super_admin"]:
            raise HTTPException(status_code=403, detail="Admin access required")
        
        # Check if template name exists
        existing = await db.email_templates.find_one({"template_name": template.template_name})
        if existing:
            raise HTTPException(status_code=400, detail="Template name already exists")
        
        template_doc = {
            "id": str(uuid.uuid4()),
            **template.dict(),
            "is_active": True,
            "created_by": current_user["id"],
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        await db.email_templates.insert_one(template_doc)
        return template_doc
    
    @router.get("/email-templates", response_model=List[EmailTemplateResponse])
    async def list_email_templates(
        template_type: Optional[str] = None,
        active_only: bool = True,
        current_user: dict = Depends(get_current_user)
    ):
        """List email templates"""
        if current_user["role"] not in ["admin", "super_admin"]:
            raise HTTPException(status_code=403, detail="Admin access required")
        
        query = {}
        if template_type:
            query["template_type"] = template_type
        if active_only:
            query["is_active"] = True
        
        templates = await db.email_templates.find(query, {"_id": 0}).to_list(100)
        return templates
    
    @router.get("/email-templates/{template_id}", response_model=EmailTemplateResponse)
    async def get_email_template(
        template_id: str,
        current_user: dict = Depends(get_current_user)
    ):
        """Get email template by ID"""
        if current_user["role"] not in ["admin", "super_admin"]:
            raise HTTPException(status_code=403, detail="Admin access required")
        
        template = await db.email_templates.find_one({"id": template_id}, {"_id": 0})
        if not template:
            raise HTTPException(status_code=404, detail="Template not found")
        return template
    
    @router.put("/email-templates/{template_id}", response_model=EmailTemplateResponse)
    async def update_email_template(
        template_id: str,
        template: EmailTemplateUpdate,
        current_user: dict = Depends(get_current_user)
    ):
        """Update email template"""
        if current_user["role"] not in ["admin", "super_admin"]:
            raise HTTPException(status_code=403, detail="Admin access required")
        
        update_data = template.dict(exclude_none=True)
        update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
        
        result = await db.email_templates.update_one(
            {"id": template_id},
            {"$set": update_data}
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Template not found")
        
        updated = await db.email_templates.find_one({"id": template_id}, {"_id": 0})
        return updated
    
    @router.delete("/email-templates/{template_id}")
    async def delete_email_template(
        template_id: str,
        current_user: dict = Depends(get_current_user)
    ):
        """Delete (deactivate) email template"""
        if current_user["role"] not in ["admin", "super_admin"]:
            raise HTTPException(status_code=403, detail="Admin access required")
        
        result = await db.email_templates.update_one(
            {"id": template_id},
            {"$set": {"is_active": False, "updated_at": datetime.now(timezone.utc).isoformat()}}
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Template not found")
        
        return {"status": "deleted", "template_id": template_id}
    
    @router.post("/email-templates/{template_id}/preview")
    async def preview_email_template(
        template_id: str,
        variables: Dict[str, str],
        current_user: dict = Depends(get_current_user)
    ):
        """Preview email template with variables"""
        if current_user["role"] not in ["admin", "super_admin"]:
            raise HTTPException(status_code=403, detail="Admin access required")
        
        template = await db.email_templates.find_one({"id": template_id}, {"_id": 0})
        if not template:
            raise HTTPException(status_code=404, detail="Template not found")
        
        # Simple variable replacement
        subject = template["subject_template"]
        html = template["html_template"]
        text = template.get("text_template", "")
        
        for key, value in variables.items():
            placeholder = "{{" + key + "}}"
            subject = subject.replace(placeholder, value)
            html = html.replace(placeholder, value)
            text = text.replace(placeholder, value) if text else ""
        
        return {
            "subject": subject,
            "html": html,
            "text": text
        }
    
    # ============= COMMUNICATION LOGS =============
    
    @router.get("/logs")
    async def get_communication_logs(
        skip: int = 0,
        limit: int = 50,
        communication_type: Optional[str] = None,
        current_user: dict = Depends(get_current_user)
    ):
        """Get communication logs"""
        if current_user["role"] not in ["admin", "super_admin"]:
            raise HTTPException(status_code=403, detail="Admin access required")
        
        query = {}
        if communication_type:
            query["communication_type"] = communication_type
        
        logs = await db.communication_logs.find(
            query, {"_id": 0}
        ).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)
        
        return {"logs": logs, "total": len(logs)}
    
    return router
