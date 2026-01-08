import logging
from typing import List, Optional
from datetime import datetime

class EmailService:
    """Mock email service for testing - logs emails instead of sending"""
    
    def __init__(self):
        self.logger = logging.getLogger("EmailService")
        self.sent_emails = []
    
    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        from_email: str = "noreply@hiringreferrals.com"
    ) -> dict:
        """Send email (mock - logs only)"""
        email_data = {
            "id": f"email_{len(self.sent_emails) + 1}",
            "from": from_email,
            "to": to_email,
            "subject": subject,
            "html_content": html_content,
            "sent_at": datetime.utcnow().isoformat(),
            "status": "logged"
        }
        
        self.sent_emails.append(email_data)
        
        self.logger.info(f"📧 EMAIL LOGGED: To={to_email}, Subject={subject}")
        self.logger.debug(f"Content: {html_content[:200]}...")
        
        return email_data
    
    async def send_application_status_update(
        self,
        candidate_email: str,
        candidate_name: str,
        job_title: str,
        new_status: str,
        company_name: str
    ):
        """Send application status update email"""
        subject = f"Application Update: {job_title} at {company_name}"
        
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <div style="background: linear-gradient(135deg, #4338ca 0%, #a3e635 100%); padding: 30px; text-align: center; border-radius: 10px 10px 0 0;">
                    <h1 style="color: white; margin: 0;">HiringReferrals</h1>
                </div>
                
                <div style="background: #f9fafb; padding: 30px; border-radius: 0 0 10px 10px;">
                    <h2 style="color: #4338ca; margin-top: 0;">Application Status Update</h2>
                    
                    <p>Hi {candidate_name},</p>
                    
                    <p>Your application for <strong>{job_title}</strong> at <strong>{company_name}</strong> has been updated.</p>
                    
                    <div style="background: white; padding: 20px; border-left: 4px solid #4338ca; margin: 20px 0;">
                        <p style="margin: 0;"><strong>New Status:</strong> <span style="color: #4338ca; text-transform: capitalize;">{new_status}</span></p>
                    </div>
                    
                    <p>Log in to your dashboard to view more details and next steps.</p>
                    
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="https://hiringreferrals.com/dashboard" style="background: #4338ca; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; display: inline-block;">View Application</a>
                    </div>
                    
                    <p style="color: #6b7280; font-size: 14px; margin-top: 30px;">Best regards,<br>HiringReferrals Team</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return await self.send_email(candidate_email, subject, html_content)
    
    async def send_interview_invite(
        self,
        candidate_email: str,
        candidate_name: str,
        job_title: str,
        company_name: str,
        interview_date: str,
        interview_time: str,
        meeting_link: Optional[str] = None
    ):
        """Send interview invitation email"""
        subject = f"Interview Invitation: {job_title} at {company_name}"
        
        meeting_info = f'<p><strong>Meeting Link:</strong> <a href="{meeting_link}">{meeting_link}</a></p>' if meeting_link else ''
        
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <div style="background: linear-gradient(135deg, #4338ca 0%, #a3e635 100%); padding: 30px; text-align: center; border-radius: 10px 10px 0 0;">
                    <h1 style="color: white; margin: 0;">🎉 Interview Invitation</h1>
                </div>
                
                <div style="background: #f9fafb; padding: 30px; border-radius: 0 0 10px 10px;">
                    <p>Hi {candidate_name},</p>
                    
                    <p>Congratulations! You've been selected for an interview for <strong>{job_title}</strong> at <strong>{company_name}</strong>.</p>
                    
                    <div style="background: white; padding: 20px; border-left: 4px solid #a3e635; margin: 20px 0;">
                        <p style="margin: 5px 0;"><strong>Date:</strong> {interview_date}</p>
                        <p style="margin: 5px 0;"><strong>Time:</strong> {interview_time}</p>
                        {meeting_info}
                    </div>
                    
                    <p>Please confirm your attendance and prepare accordingly. Good luck!</p>
                    
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="https://hiringreferrals.com/dashboard" style="background: #a3e635; color: #1e293b; padding: 12px 30px; text-decoration: none; border-radius: 5px; display: inline-block; font-weight: bold;">Confirm Attendance</a>
                    </div>
                    
                    <p style="color: #6b7280; font-size: 14px; margin-top: 30px;">Best regards,<br>HiringReferrals Team</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return await self.send_email(candidate_email, subject, html_content)
    
    async def send_referral_success(
        self,
        recruiter_email: str,
        recruiter_name: str,
        candidate_name: str,
        job_title: str,
        reward_amount: int
    ):
        """Send referral success notification"""
        subject = f"🎉 Referral Successful! Earned ₹{reward_amount}"
        
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <div style="background: linear-gradient(135deg, #a3e635 0%, #22c55e 100%); padding: 30px; text-align: center; border-radius: 10px 10px 0 0;">
                    <h1 style="color: white; margin: 0;">🎉 Congratulations!</h1>
                </div>
                
                <div style="background: #f9fafb; padding: 30px; border-radius: 0 0 10px 10px;">
                    <p>Hi {recruiter_name},</p>
                    
                    <p>Great news! Your referral has been successfully hired.</p>
                    
                    <div style="background: white; padding: 25px; text-align: center; border-radius: 10px; margin: 20px 0; border: 2px solid #a3e635;">
                        <h2 style="color: #22c55e; margin: 0 0 10px 0; font-size: 36px;">₹{reward_amount}</h2>
                        <p style="margin: 0; color: #6b7280;">Reward Earned</p>
                    </div>
                    
                    <div style="background: white; padding: 20px; border-left: 4px solid #a3e635; margin: 20px 0;">
                        <p style="margin: 5px 0;"><strong>Candidate:</strong> {candidate_name}</p>
                        <p style="margin: 5px 0;"><strong>Position:</strong> {job_title}</p>
                    </div>
                    
                    <p>Keep up the great work! Continue referring top talent to earn more rewards.</p>
                    
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="https://hiringreferrals.com/leaderboard" style="background: #a3e635; color: #1e293b; padding: 12px 30px; text-decoration: none; border-radius: 5px; display: inline-block; font-weight: bold;">View Leaderboard</a>
                    </div>
                    
                    <p style="color: #6b7280; font-size: 14px; margin-top: 30px;">Best regards,<br>HiringReferrals Team</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return await self.send_email(recruiter_email, subject, html_content)
    
    def get_sent_emails(self, limit: int = 50) -> List[dict]:
        """Get list of sent (logged) emails"""
        return self.sent_emails[-limit:]
