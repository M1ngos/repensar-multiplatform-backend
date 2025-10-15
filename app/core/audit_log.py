"""
Security audit logging for authentication and authorization events.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, asdict
import json
import logging


class AuditEventType(Enum):
    """Types of security events to audit."""
    # Authentication events
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILED = "login_failed"
    LOGIN_LOCKED = "login_locked"
    LOGOUT = "logout"

    # Token events
    TOKEN_ISSUED = "token_issued"
    TOKEN_REFRESHED = "token_refreshed"
    TOKEN_REVOKED = "token_revoked"
    TOKEN_REUSE_DETECTED = "token_reuse_detected"
    TOKEN_FAMILY_REVOKED = "token_family_revoked"

    # Account events
    ACCOUNT_CREATED = "account_created"
    ACCOUNT_LOCKED = "account_locked"
    ACCOUNT_UNLOCKED = "account_unlocked"
    ACCOUNT_DEACTIVATED = "account_deactivated"
    ACCOUNT_ACTIVATED = "account_activated"

    # Password events
    PASSWORD_CHANGED = "password_changed"
    PASSWORD_RESET_REQUESTED = "password_reset_requested"
    PASSWORD_RESET_COMPLETED = "password_reset_completed"

    # Email events
    EMAIL_VERIFIED = "email_verified"
    EMAIL_VERIFICATION_SENT = "email_verification_sent"

    # Security events
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    PERMISSION_DENIED = "permission_denied"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"


class AuditEventSeverity(Enum):
    """Severity levels for audit events."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class AuditEvent:
    """Represents a security audit event."""
    event_type: AuditEventType
    severity: AuditEventSeverity
    timestamp: datetime
    user_id: Optional[int] = None
    email: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    success: bool = True
    error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary for logging."""
        data = asdict(self)
        data["event_type"] = self.event_type.value
        data["severity"] = self.severity.value
        data["timestamp"] = self.timestamp.isoformat()
        return data

    def to_json(self) -> str:
        """Convert event to JSON string."""
        return json.dumps(self.to_dict())


class AuditLogger:
    """
    Audit logger for security events.
    Supports multiple backends: file, database, SIEM integration.
    """

    def __init__(self, app_name: str = "repensar-backend"):
        self.app_name = app_name
        self.logger = logging.getLogger(f"{app_name}.audit")
        self._setup_logging()
        self._events: List[AuditEvent] = []  # In-memory storage for development

    def _setup_logging(self):
        """Configure the audit logger."""
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)

    def log_event(self, event: AuditEvent) -> None:
        """
        Log an audit event.

        Args:
            event: The audit event to log
        """
        # Store in memory (for development/testing)
        self._events.append(event)

        # Log to standard logger
        log_level = {
            AuditEventSeverity.INFO: logging.INFO,
            AuditEventSeverity.WARNING: logging.WARNING,
            AuditEventSeverity.ERROR: logging.ERROR,
            AuditEventSeverity.CRITICAL: logging.CRITICAL,
        }.get(event.severity, logging.INFO)

        self.logger.log(log_level, event.to_json())

    def log_login_success(
        self,
        user_id: int,
        email: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> None:
        """Log successful login."""
        event = AuditEvent(
            event_type=AuditEventType.LOGIN_SUCCESS,
            severity=AuditEventSeverity.INFO,
            timestamp=datetime.now(timezone.utc),
            user_id=user_id,
            email=email,
            ip_address=ip_address,
            user_agent=user_agent,
            success=True
        )
        self.log_event(event)

    def log_login_failed(
        self,
        email: str,
        reason: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> None:
        """Log failed login attempt."""
        event = AuditEvent(
            event_type=AuditEventType.LOGIN_FAILED,
            severity=AuditEventSeverity.WARNING,
            timestamp=datetime.now(timezone.utc),
            email=email,
            ip_address=ip_address,
            user_agent=user_agent,
            success=False,
            error_message=reason
        )
        self.log_event(event)

    def log_account_locked(
        self,
        user_id: int,
        email: str,
        ip_address: Optional[str] = None
    ) -> None:
        """Log account lockout."""
        event = AuditEvent(
            event_type=AuditEventType.ACCOUNT_LOCKED,
            severity=AuditEventSeverity.WARNING,
            timestamp=datetime.now(timezone.utc),
            user_id=user_id,
            email=email,
            ip_address=ip_address,
            details={"reason": "Too many failed login attempts"}
        )
        self.log_event(event)

    def log_token_issued(
        self,
        user_id: int,
        token_type: str,
        ip_address: Optional[str] = None
    ) -> None:
        """Log token issuance."""
        event = AuditEvent(
            event_type=AuditEventType.TOKEN_ISSUED,
            severity=AuditEventSeverity.INFO,
            timestamp=datetime.now(timezone.utc),
            user_id=user_id,
            ip_address=ip_address,
            details={"token_type": token_type}
        )
        self.log_event(event)

    def log_token_refreshed(
        self,
        user_id: int,
        ip_address: Optional[str] = None
    ) -> None:
        """Log token refresh."""
        event = AuditEvent(
            event_type=AuditEventType.TOKEN_REFRESHED,
            severity=AuditEventSeverity.INFO,
            timestamp=datetime.now(timezone.utc),
            user_id=user_id,
            ip_address=ip_address
        )
        self.log_event(event)

    def log_token_revoked(
        self,
        user_id: int,
        reason: str,
        ip_address: Optional[str] = None
    ) -> None:
        """Log token revocation."""
        event = AuditEvent(
            event_type=AuditEventType.TOKEN_REVOKED,
            severity=AuditEventSeverity.WARNING,
            timestamp=datetime.now(timezone.utc),
            user_id=user_id,
            ip_address=ip_address,
            details={"reason": reason}
        )
        self.log_event(event)

    def log_token_reuse_detected(
        self,
        user_id: int,
        token_family: str,
        ip_address: Optional[str] = None
    ) -> None:
        """Log refresh token reuse (potential compromise)."""
        event = AuditEvent(
            event_type=AuditEventType.TOKEN_REUSE_DETECTED,
            severity=AuditEventSeverity.CRITICAL,
            timestamp=datetime.now(timezone.utc),
            user_id=user_id,
            ip_address=ip_address,
            details={
                "token_family": token_family,
                "action": "All tokens in family revoked"
            }
        )
        self.log_event(event)

    def log_password_changed(
        self,
        user_id: int,
        email: str,
        ip_address: Optional[str] = None
    ) -> None:
        """Log password change."""
        event = AuditEvent(
            event_type=AuditEventType.PASSWORD_CHANGED,
            severity=AuditEventSeverity.INFO,
            timestamp=datetime.now(timezone.utc),
            user_id=user_id,
            email=email,
            ip_address=ip_address
        )
        self.log_event(event)

    def log_unauthorized_access(
        self,
        resource: str,
        ip_address: Optional[str] = None,
        user_id: Optional[int] = None
    ) -> None:
        """Log unauthorized access attempt."""
        event = AuditEvent(
            event_type=AuditEventType.UNAUTHORIZED_ACCESS,
            severity=AuditEventSeverity.WARNING,
            timestamp=datetime.now(timezone.utc),
            user_id=user_id,
            ip_address=ip_address,
            success=False,
            details={"resource": resource}
        )
        self.log_event(event)

    def get_events(
        self,
        user_id: Optional[int] = None,
        event_type: Optional[AuditEventType] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100
    ) -> List[AuditEvent]:
        """
        Retrieve audit events with filters.

        Args:
            user_id: Filter by user ID
            event_type: Filter by event type
            start_time: Filter events after this time
            end_time: Filter events before this time
            limit: Maximum number of events to return

        Returns:
            List of audit events
        """
        filtered_events = self._events

        if user_id is not None:
            filtered_events = [e for e in filtered_events if e.user_id == user_id]

        if event_type is not None:
            filtered_events = [e for e in filtered_events if e.event_type == event_type]

        if start_time is not None:
            filtered_events = [e for e in filtered_events if e.timestamp >= start_time]

        if end_time is not None:
            filtered_events = [e for e in filtered_events if e.timestamp <= end_time]

        return filtered_events[-limit:]


# Global audit logger instance
_audit_logger: Optional[AuditLogger] = None


def get_audit_logger() -> AuditLogger:
    """Get or create the audit logger instance."""
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = AuditLogger()
    return _audit_logger
