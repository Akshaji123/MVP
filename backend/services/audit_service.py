"""
Audit Logging Service
HiringReferrals Platform

Comprehensive audit logging for:
- User actions
- Data changes
- Security events
- Compliance tracking
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
from enum import Enum
import uuid
import logging

logger = logging.getLogger(__name__)


class AuditAction(Enum):
    """Types of auditable actions"""
    # User actions
    LOGIN = "login"
    LOGOUT = "logout"
    LOGIN_FAILED = "login_failed"
    PASSWORD_CHANGE = "password_change"
    PROFILE_UPDATE = "profile_update"
    
    # CRUD operations
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    
    # Application flow
    APPLICATION_SUBMIT = "application_submit"
    STATUS_CHANGE = "status_change"
    INTERVIEW_SCHEDULE = "interview_schedule"
    OFFER_SEND = "offer_send"
    HIRE = "hire"
    REJECT = "reject"
    
    # Admin actions
    USER_ACTIVATE = "user_activate"
    USER_DEACTIVATE = "user_deactivate"
    PERMISSION_CHANGE = "permission_change"
    SETTINGS_CHANGE = "settings_change"
    
    # Data operations
    EXPORT = "export"
    IMPORT = "import"
    BACKUP = "backup"
    RESTORE = "restore"
    
    # BGV
    BGV_INITIATE = "bgv_initiate"
    BGV_COMPLETE = "bgv_complete"
    
    # Payment
    COMMISSION_CALCULATE = "commission_calculate"
    PAYMENT_INITIATE = "payment_initiate"
    PAYMENT_COMPLETE = "payment_complete"


class AuditLogger:
    """
    Audit logging service for compliance and security tracking
    """
    
    def __init__(self, db):
        self.db = db
    
    async def log(
        self,
        user_id: str,
        action: AuditAction,
        resource_type: str,
        resource_id: Optional[str] = None,
        old_value: Optional[Dict[str, Any]] = None,
        new_value: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        success: bool = True,
        error_message: Optional[str] = None
    ) -> str:
        """
        Log an audit event
        
        Args:
            user_id: ID of user performing action
            action: Type of action
            resource_type: Type of resource being acted upon
            resource_id: ID of specific resource
            old_value: Previous value (for updates)
            new_value: New value (for creates/updates)
            ip_address: Client IP address
            user_agent: Client user agent
            metadata: Additional context
            success: Whether action succeeded
            error_message: Error details if failed
            
        Returns:
            Audit log entry ID
        """
        log_id = str(uuid.uuid4())
        
        # Sanitize sensitive data
        if old_value:
            old_value = self._sanitize_sensitive_data(old_value)
        if new_value:
            new_value = self._sanitize_sensitive_data(new_value)
        
        entry = {
            "id": log_id,
            "user_id": user_id,
            "action": action.value,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "old_value": old_value,
            "new_value": new_value,
            "ip_address": ip_address,
            "user_agent": user_agent,
            "metadata": metadata or {},
            "success": success,
            "error_message": error_message,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        await self.db.audit_logs.insert_one(entry)
        
        # Log critical actions
        if action in [AuditAction.LOGIN_FAILED, AuditAction.PERMISSION_CHANGE, 
                      AuditAction.DELETE, AuditAction.PAYMENT_COMPLETE]:
            logger.info(f"AUDIT: {action.value} by {user_id} on {resource_type}/{resource_id}")
        
        return log_id
    
    def _sanitize_sensitive_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Remove or mask sensitive fields"""
        sensitive_fields = ['password', 'password_hash', 'token', 'secret', 
                          'credit_card', 'ssn', 'bank_account', 'api_key']
        
        sanitized = {}
        for key, value in data.items():
            if any(field in key.lower() for field in sensitive_fields):
                sanitized[key] = "***REDACTED***"
            elif isinstance(value, dict):
                sanitized[key] = self._sanitize_sensitive_data(value)
            else:
                sanitized[key] = value
        
        return sanitized
    
    async def get_user_activity(
        self,
        user_id: str,
        limit: int = 50,
        action_filter: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """Get activity log for a specific user"""
        query = {"user_id": user_id}
        if action_filter:
            query["action"] = {"$in": action_filter}
        
        logs = await self.db.audit_logs.find(
            query, 
            {"_id": 0}
        ).sort("timestamp", -1).limit(limit).to_list(limit)
        
        return logs
    
    async def get_resource_history(
        self,
        resource_type: str,
        resource_id: str,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get change history for a specific resource"""
        logs = await self.db.audit_logs.find(
            {"resource_type": resource_type, "resource_id": resource_id},
            {"_id": 0}
        ).sort("timestamp", -1).limit(limit).to_list(limit)
        
        return logs
    
    async def get_security_events(
        self,
        since: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get security-related audit events"""
        security_actions = [
            AuditAction.LOGIN.value,
            AuditAction.LOGOUT.value,
            AuditAction.LOGIN_FAILED.value,
            AuditAction.PASSWORD_CHANGE.value,
            AuditAction.PERMISSION_CHANGE.value,
            AuditAction.USER_ACTIVATE.value,
            AuditAction.USER_DEACTIVATE.value
        ]
        
        query = {"action": {"$in": security_actions}}
        if since:
            query["timestamp"] = {"$gte": since}
        
        logs = await self.db.audit_logs.find(
            query,
            {"_id": 0}
        ).sort("timestamp", -1).limit(limit).to_list(limit)
        
        return logs
    
    async def get_failed_logins(
        self,
        hours: int = 24,
        min_attempts: int = 3
    ) -> List[Dict[str, Any]]:
        """Get users with multiple failed login attempts"""
        from datetime import timedelta
        
        since = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()
        
        pipeline = [
            {
                "$match": {
                    "action": AuditAction.LOGIN_FAILED.value,
                    "timestamp": {"$gte": since}
                }
            },
            {
                "$group": {
                    "_id": "$user_id",
                    "failed_attempts": {"$sum": 1},
                    "ip_addresses": {"$addToSet": "$ip_address"},
                    "last_attempt": {"$max": "$timestamp"}
                }
            },
            {
                "$match": {
                    "failed_attempts": {"$gte": min_attempts}
                }
            },
            {
                "$sort": {"failed_attempts": -1}
            }
        ]
        
        results = await self.db.audit_logs.aggregate(pipeline).to_list(100)
        return results
    
    async def generate_compliance_report(
        self,
        start_date: str,
        end_date: str
    ) -> Dict[str, Any]:
        """Generate compliance report for date range"""
        
        # Get action counts
        pipeline = [
            {
                "$match": {
                    "timestamp": {"$gte": start_date, "$lte": end_date}
                }
            },
            {
                "$group": {
                    "_id": "$action",
                    "count": {"$sum": 1},
                    "success_count": {
                        "$sum": {"$cond": ["$success", 1, 0]}
                    },
                    "failure_count": {
                        "$sum": {"$cond": ["$success", 0, 1]}
                    }
                }
            }
        ]
        
        action_stats = await self.db.audit_logs.aggregate(pipeline).to_list(50)
        
        # Get unique users
        unique_users = await self.db.audit_logs.distinct(
            "user_id",
            {"timestamp": {"$gte": start_date, "$lte": end_date}}
        )
        
        # Get data access patterns
        resource_pipeline = [
            {
                "$match": {
                    "timestamp": {"$gte": start_date, "$lte": end_date}
                }
            },
            {
                "$group": {
                    "_id": "$resource_type",
                    "access_count": {"$sum": 1}
                }
            }
        ]
        
        resource_stats = await self.db.audit_logs.aggregate(resource_pipeline).to_list(20)
        
        return {
            "report_period": {
                "start": start_date,
                "end": end_date
            },
            "summary": {
                "total_events": sum(s["count"] for s in action_stats),
                "unique_users": len(unique_users),
                "success_rate": self._calc_success_rate(action_stats)
            },
            "action_breakdown": {s["_id"]: s for s in action_stats},
            "resource_access": {s["_id"]: s["access_count"] for s in resource_stats},
            "generated_at": datetime.now(timezone.utc).isoformat()
        }
    
    def _calc_success_rate(self, stats: List[Dict]) -> str:
        """Calculate overall success rate"""
        total = sum(s["count"] for s in stats)
        success = sum(s["success_count"] for s in stats)
        if total == 0:
            return "N/A"
        return f"{(success / total) * 100:.1f}%"


def create_audit_logger(db) -> AuditLogger:
    return AuditLogger(db)
