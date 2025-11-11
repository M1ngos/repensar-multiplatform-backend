"""
Helper functions for authentication routes integrating all security features.
"""

import os
from fastapi import Request
from typing import Optional, Tuple
from datetime import datetime, timezone

from app.core.audit_log import get_audit_logger
from app.core.rate_limiter import get_rate_limiter, DEFAULT_RATE_LIMITS, RateLimitExceeded


def _is_rate_limiting_disabled() -> bool:
    """Check if rate limiting is disabled via environment variable."""
    return os.getenv("DISABLE_RATE_LIMITING", "false").lower() in ("true", "1", "yes")


def get_client_ip(request: Request) -> Optional[str]:
    """Extract client IP address from request."""
    # Check for X-Forwarded-For header (proxy/load balancer)
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        # Take the first IP in the chain
        return forwarded.split(",")[0].strip()

    # Check for X-Real-IP header
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip

    # Fall back to direct client
    if request.client:
        return request.client.host

    return None


def get_user_agent(request: Request) -> Optional[str]:
    """Extract user agent from request."""
    return request.headers.get("User-Agent")


def check_login_rate_limit(identifier: str) -> None:
    """
    Check login rate limit and raise exception if exceeded.

    Args:
        identifier: IP address or user identifier

    Raises:
        RateLimitExceeded: If rate limit is exceeded
    """
    if _is_rate_limiting_disabled():
        return

    rate_limiter = get_rate_limiter()
    rate_limiter.check_rate_limit(
        key=f"login:{identifier}",
        rule=DEFAULT_RATE_LIMITS["login"],
        success=False
    )


def check_register_rate_limit(identifier: str) -> None:
    """Check registration rate limit."""
    if _is_rate_limiting_disabled():
        return

    rate_limiter = get_rate_limiter()
    rate_limiter.check_rate_limit(
        key=f"register:{identifier}",
        rule=DEFAULT_RATE_LIMITS["register"],
        success=False
    )


def check_token_refresh_rate_limit(identifier: str) -> None:
    """Check token refresh rate limit."""
    if _is_rate_limiting_disabled():
        return

    rate_limiter = get_rate_limiter()
    rate_limiter.check_rate_limit(
        key=f"refresh:{identifier}",
        rule=DEFAULT_RATE_LIMITS["token_refresh"],
        success=False
    )


def check_password_reset_rate_limit(identifier: str) -> None:
    """Check password reset rate limit."""
    if _is_rate_limiting_disabled():
        return

    rate_limiter = get_rate_limiter()
    rate_limiter.check_rate_limit(
        key=f"password_reset:{identifier}",
        rule=DEFAULT_RATE_LIMITS["password_reset"],
        success=False
    )


def reset_login_rate_limit(identifier: str) -> None:
    """Reset login rate limit after successful login."""
    rate_limiter = get_rate_limiter()
    rate_limiter.reset(f"login:{identifier}")


def log_and_create_tokens(
    user_id: int,
    email: str,
    ip_address: Optional[str],
    user_agent: Optional[str],
    token_family: Optional[str] = None
) -> Tuple[str, str, str]:
    """
    Create access and refresh tokens with audit logging.

    Returns:
        Tuple of (access_token, refresh_token, token_family)
    """
    from app.core.auth import create_access_token, create_refresh_token

    # Create tokens
    token_data = {"sub": user_id, "email": email}
    access_token = create_access_token(
        token_data,
        ip_address=ip_address,
        user_agent=user_agent
    )
    refresh_token, token_family = create_refresh_token(
        token_data,
        token_family=token_family,
        ip_address=ip_address,
        user_agent=user_agent
    )

    # Log token issuance
    audit_logger = get_audit_logger()
    audit_logger.log_token_issued(
        user_id=user_id,
        token_type="access",
        ip_address=ip_address
    )
    audit_logger.log_token_issued(
        user_id=user_id,
        token_type="refresh",
        ip_address=ip_address
    )

    return access_token, refresh_token, token_family
