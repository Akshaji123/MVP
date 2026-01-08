"""
WhatsApp Notification Service (Mocked)
This service provides a mocked implementation of WhatsApp notifications via Twilio.
When real Twilio credentials are provided, it can be easily switched to send actual messages.
"""
import os
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from enum import Enum

logger = logging.getLogger(__name__)

class MessageType(str, Enum):
    TEXT = "text"
    TEMPLATE = "template"
    MEDIA = "media"

class NotificationType(str, Enum):
    APPLICATION_UPDATE = "application_update"
    INTERVIEW_SCHEDULED = "interview_scheduled"
    INTERVIEW_REMINDER = "interview_reminder"
    OFFER_LETTER = "offer_letter"
    JOB_MATCH = "job_match"
    PAYMENT_RECEIVED = "payment_received"
    COMMISSION_EARNED = "commission_earned"
    GENERAL = "general"

# Message templates for different notification types
MESSAGE_TEMPLATES = {
    NotificationType.APPLICATION_UPDATE: """
💼 *Application Update*

Hi {candidate_name},

Your application for *{job_title}* at *{company_name}* has been updated.

*New Status:* {status}

{additional_info}

Best regards,
Hiring Referrals Team
""",
    NotificationType.INTERVIEW_SCHEDULED: """
📅 *Interview Scheduled*

Hi {candidate_name},

Great news! Your interview has been scheduled.

*Position:* {job_title}
*Company:* {company_name}
*Date:* {interview_date}
*Time:* {interview_time}
*Type:* {interview_type}
{meeting_link}

Good luck!
Hiring Referrals Team
""",
    NotificationType.INTERVIEW_REMINDER: """
⏰ *Interview Reminder*

Hi {candidate_name},

This is a reminder that your interview is scheduled for *today*.

*Position:* {job_title}
*Time:* {interview_time}
*Type:* {interview_type}
{meeting_link}

Be prepared and good luck!
""",
    NotificationType.OFFER_LETTER: """
🎉 *Congratulations!*

Hi {candidate_name},

We are thrilled to inform you that you have been selected for the position of *{job_title}* at *{company_name}*!

*Offered CTC:* {offered_ctc}
*Joining Date:* {joining_date}

Please check your email for the detailed offer letter.

Welcome aboard!
""",
    NotificationType.JOB_MATCH: """
💫 *New Job Match*

Hi {candidate_name},

We found a job that matches your profile!

*Position:* {job_title}
*Company:* {company_name}
*Location:* {location}
*Match Score:* {match_score}%

Interested? Apply now on our platform!
""",
    NotificationType.PAYMENT_RECEIVED: """
💰 *Payment Received*

Hi {user_name},

Your payment has been processed successfully.

*Amount:* {amount}
*Transaction ID:* {transaction_id}
*Date:* {payment_date}

Thank you for using Hiring Referrals!
""",
    NotificationType.COMMISSION_EARNED: """
🌟 *Commission Earned*

Hi {user_name},

Congratulations! You've earned a commission.

*Amount:* {amount}
*For:* {candidate_name} placed at {company_name}
*Status:* {status}

Keep up the great work!
""",
    NotificationType.GENERAL: """
📢 *Notification*

Hi {recipient_name},

{message}

Best regards,
Hiring Referrals Team
"""
}

class WhatsAppService:
    """
    Mocked WhatsApp notification service.
    Logs all messages instead of sending them via Twilio.
    Can be easily switched to real Twilio integration by providing credentials.
    """
    
    def __init__(self):
        self.account_sid = os.environ.get('TWILIO_ACCOUNT_SID')
        self.auth_token = os.environ.get('TWILIO_AUTH_TOKEN')
        self.whatsapp_number = os.environ.get('TWILIO_WHATSAPP_NUMBER')
        self.is_mocked = not all([self.account_sid, self.auth_token, self.whatsapp_number])
        
        # In-memory log of sent messages (for mocked mode)
        self.message_log: List[Dict[str, Any]] = []
        
        if self.is_mocked:
            logger.info("WhatsApp service running in MOCKED mode. Messages will be logged but not sent.")
        else:
            logger.info("WhatsApp service initialized with Twilio credentials.")
    
    def _format_message(self, notification_type: NotificationType, variables: Dict[str, Any]) -> str:
        """Format a message template with provided variables."""
        template = MESSAGE_TEMPLATES.get(notification_type, MESSAGE_TEMPLATES[NotificationType.GENERAL])
        try:
            return template.format(**variables)
        except KeyError as e:
            logger.warning(f"Missing variable in template: {e}")
            return template
    
    async def send_message(
        self,
        to_number: str,
        message: str,
        message_type: MessageType = MessageType.TEXT
    ) -> Dict[str, Any]:
        """
        Send a WhatsApp message.
        In mocked mode, logs the message instead of sending.
        """
        timestamp = datetime.now(timezone.utc).isoformat()
        
        message_record = {
            "id": f"msg_{len(self.message_log) + 1}_{int(datetime.now().timestamp())}",
            "to": to_number,
            "message": message,
            "message_type": message_type,
            "timestamp": timestamp,
            "status": "delivered" if self.is_mocked else "pending",
            "is_mocked": self.is_mocked
        }
        
        if self.is_mocked:
            # Log the message
            logger.info(f"[MOCKED WhatsApp] To: {to_number}")
            logger.info(f"[MOCKED WhatsApp] Message: {message[:100]}...")
            self.message_log.append(message_record)
            return {
                "success": True,
                "message_id": message_record["id"],
                "status": "mocked_delivered",
                "note": "Message logged but not sent (mocked mode)"
            }
        else:
            # Real Twilio integration would go here
            try:
                # from twilio.rest import Client
                # client = Client(self.account_sid, self.auth_token)
                # message = client.messages.create(
                #     from_=f'whatsapp:{self.whatsapp_number}',
                #     body=message,
                #     to=f'whatsapp:{to_number}'
                # )
                # return {"success": True, "message_id": message.sid, "status": message.status}
                pass
            except Exception as e:
                logger.error(f"Failed to send WhatsApp message: {e}")
                return {"success": False, "error": str(e)}
    
    async def send_notification(
        self,
        to_number: str,
        notification_type: NotificationType,
        variables: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Send a templated notification.
        """
        message = self._format_message(notification_type, variables)
        return await self.send_message(to_number, message, MessageType.TEMPLATE)
    
    async def send_application_update(
        self,
        to_number: str,
        candidate_name: str,
        job_title: str,
        company_name: str,
        status: str,
        additional_info: str = ""
    ) -> Dict[str, Any]:
        """Send application status update notification."""
        return await self.send_notification(
            to_number,
            NotificationType.APPLICATION_UPDATE,
            {
                "candidate_name": candidate_name,
                "job_title": job_title,
                "company_name": company_name,
                "status": status,
                "additional_info": additional_info
            }
        )
    
    async def send_interview_scheduled(
        self,
        to_number: str,
        candidate_name: str,
        job_title: str,
        company_name: str,
        interview_date: str,
        interview_time: str,
        interview_type: str,
        meeting_link: Optional[str] = None
    ) -> Dict[str, Any]:
        """Send interview scheduled notification."""
        link_text = f"*Meeting Link:* {meeting_link}" if meeting_link else ""
        return await self.send_notification(
            to_number,
            NotificationType.INTERVIEW_SCHEDULED,
            {
                "candidate_name": candidate_name,
                "job_title": job_title,
                "company_name": company_name,
                "interview_date": interview_date,
                "interview_time": interview_time,
                "interview_type": interview_type,
                "meeting_link": link_text
            }
        )
    
    async def send_job_match(
        self,
        to_number: str,
        candidate_name: str,
        job_title: str,
        company_name: str,
        location: str,
        match_score: int
    ) -> Dict[str, Any]:
        """Send job match notification."""
        return await self.send_notification(
            to_number,
            NotificationType.JOB_MATCH,
            {
                "candidate_name": candidate_name,
                "job_title": job_title,
                "company_name": company_name,
                "location": location,
                "match_score": match_score
            }
        )
    
    async def send_commission_earned(
        self,
        to_number: str,
        user_name: str,
        amount: str,
        candidate_name: str,
        company_name: str,
        status: str = "Pending"
    ) -> Dict[str, Any]:
        """Send commission earned notification."""
        return await self.send_notification(
            to_number,
            NotificationType.COMMISSION_EARNED,
            {
                "user_name": user_name,
                "amount": amount,
                "candidate_name": candidate_name,
                "company_name": company_name,
                "status": status
            }
        )
    
    def get_message_log(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent message log (mocked mode only)."""
        return self.message_log[-limit:]
    
    def get_service_status(self) -> Dict[str, Any]:
        """Get service status."""
        return {
            "is_mocked": self.is_mocked,
            "messages_sent": len(self.message_log),
            "status": "active",
            "note": "Running in mocked mode. Provide Twilio credentials to send real messages." if self.is_mocked else "Connected to Twilio"
        }

# Singleton instance
whatsapp_service = WhatsAppService()
