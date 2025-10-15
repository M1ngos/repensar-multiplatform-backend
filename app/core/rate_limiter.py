"""
Rate limiting for authentication endpoints to prevent brute force attacks.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional, Dict
from dataclasses import dataclass
from collections import defaultdict
import time


@dataclass
class RateLimitRule:
    """Rate limit rule configuration."""
    max_attempts: int
    window_seconds: int
    lockout_seconds: int = 0


class RateLimitExceeded(Exception):
    """Exception raised when rate limit is exceeded."""

    def __init__(self, retry_after: int):
        self.retry_after = retry_after
        super().__init__(f"Rate limit exceeded. Retry after {retry_after} seconds.")


class InMemoryRateLimiter:
    """
    In-memory rate limiter for development/testing.
    In production, use Redis for distributed rate limiting.
    """

    def __init__(self):
        # Track attempts: key -> [(timestamp, success)]
        self._attempts: Dict[str, list] = defaultdict(list)
        # Track lockouts: key -> lockout_until_timestamp
        self._lockouts: Dict[str, float] = {}

    def check_rate_limit(
        self,
        key: str,
        rule: RateLimitRule,
        success: bool = False
    ) -> None:
        """
        Check if a request exceeds the rate limit.

        Args:
            key: Unique identifier for the rate limit (e.g., IP address, user ID)
            rule: Rate limit rule to apply
            success: Whether the request was successful

        Raises:
            RateLimitExceeded: If rate limit is exceeded
        """
        now = time.time()

        # Check if currently locked out
        if key in self._lockouts:
            lockout_until = self._lockouts[key]
            if now < lockout_until:
                retry_after = int(lockout_until - now)
                raise RateLimitExceeded(retry_after)
            else:
                # Lockout expired
                del self._lockouts[key]
                self._attempts[key] = []

        # Clean up old attempts outside the window
        window_start = now - rule.window_seconds
        self._attempts[key] = [
            (ts, succ) for ts, succ in self._attempts[key]
            if ts > window_start
        ]

        # Count attempts in the current window
        attempts_in_window = len(self._attempts[key])

        # Add current attempt
        self._attempts[key].append((now, success))

        # Check if limit exceeded
        if attempts_in_window >= rule.max_attempts:
            if rule.lockout_seconds > 0:
                self._lockouts[key] = now + rule.lockout_seconds
                raise RateLimitExceeded(rule.lockout_seconds)
            else:
                retry_after = int(window_start + rule.window_seconds - now)
                raise RateLimitExceeded(max(retry_after, 1))

    def reset(self, key: str) -> None:
        """Reset rate limit for a key (e.g., on successful login)."""
        self._attempts.pop(key, None)
        self._lockouts.pop(key, None)

    def get_remaining_attempts(self, key: str, rule: RateLimitRule) -> int:
        """Get the number of remaining attempts."""
        now = time.time()
        window_start = now - rule.window_seconds

        # Clean up old attempts
        self._attempts[key] = [
            (ts, succ) for ts, succ in self._attempts[key]
            if ts > window_start
        ]

        attempts_in_window = len(self._attempts[key])
        return max(0, rule.max_attempts - attempts_in_window)


class RedisRateLimiter:
    """
    Redis-based rate limiter for production use.
    Provides distributed rate limiting across multiple servers.
    """

    def __init__(self, redis_client):
        """
        Initialize with a Redis client.

        Args:
            redis_client: Redis client instance
        """
        self.redis = redis_client
        self._prefix = "ratelimit:"
        self._lockout_prefix = "lockout:"

    def check_rate_limit(
        self,
        key: str,
        rule: RateLimitRule,
        success: bool = False
    ) -> None:
        """
        Check if a request exceeds the rate limit using Redis.

        Args:
            key: Unique identifier for the rate limit
            rule: Rate limit rule to apply
            success: Whether the request was successful

        Raises:
            RateLimitExceeded: If rate limit is exceeded
        """
        now = time.time()
        redis_key = f"{self._prefix}{key}"
        lockout_key = f"{self._lockout_prefix}{key}"

        # Check if currently locked out
        lockout_until = self.redis.get(lockout_key)
        if lockout_until:
            lockout_until = float(lockout_until)
            if now < lockout_until:
                retry_after = int(lockout_until - now)
                raise RateLimitExceeded(retry_after)
            else:
                # Lockout expired
                self.redis.delete(lockout_key)
                self.redis.delete(redis_key)

        # Use sorted set to track attempts with timestamps
        pipe = self.redis.pipeline()

        # Remove old attempts outside the window
        window_start = now - rule.window_seconds
        pipe.zremrangebyscore(redis_key, 0, window_start)

        # Count attempts in window
        pipe.zcard(redis_key)

        # Add current attempt
        pipe.zadd(redis_key, {f"{now}": now})

        # Set expiration on the key
        pipe.expire(redis_key, rule.window_seconds)

        results = pipe.execute()
        attempts_in_window = results[1]  # Result of zcard

        # Check if limit exceeded
        if attempts_in_window >= rule.max_attempts:
            if rule.lockout_seconds > 0:
                lockout_until = now + rule.lockout_seconds
                self.redis.setex(lockout_key, rule.lockout_seconds, lockout_until)
                raise RateLimitExceeded(rule.lockout_seconds)
            else:
                retry_after = int(window_start + rule.window_seconds - now)
                raise RateLimitExceeded(max(retry_after, 1))

    def reset(self, key: str) -> None:
        """Reset rate limit for a key."""
        redis_key = f"{self._prefix}{key}"
        lockout_key = f"{self._lockout_prefix}{key}"
        self.redis.delete(redis_key, lockout_key)

    def get_remaining_attempts(self, key: str, rule: RateLimitRule) -> int:
        """Get the number of remaining attempts."""
        now = time.time()
        redis_key = f"{self._prefix}{key}"
        window_start = now - rule.window_seconds

        # Clean up old attempts and count
        pipe = self.redis.pipeline()
        pipe.zremrangebyscore(redis_key, 0, window_start)
        pipe.zcard(redis_key)
        results = pipe.execute()

        attempts_in_window = results[1]
        return max(0, rule.max_attempts - attempts_in_window)


# Default rate limit rules
DEFAULT_RATE_LIMITS = {
    "login": RateLimitRule(
        max_attempts=5,
        window_seconds=300,  # 5 minutes
        lockout_seconds=900  # 15 minutes lockout
    ),
    "register": RateLimitRule(
        max_attempts=3,
        window_seconds=3600,  # 1 hour
        lockout_seconds=0
    ),
    "password_reset": RateLimitRule(
        max_attempts=3,
        window_seconds=3600,  # 1 hour
        lockout_seconds=0
    ),
    "token_refresh": RateLimitRule(
        max_attempts=10,
        window_seconds=60,  # 1 minute
        lockout_seconds=0
    ),
    "email_verification": RateLimitRule(
        max_attempts=5,
        window_seconds=3600,  # 1 hour
        lockout_seconds=0
    ),
}


# Global rate limiter instance
_rate_limiter: Optional[InMemoryRateLimiter] = None


def get_rate_limiter() -> InMemoryRateLimiter:
    """Get or create the rate limiter instance."""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = InMemoryRateLimiter()
    return _rate_limiter


def initialize_redis_rate_limiter(redis_client):
    """
    Initialize the Redis-based rate limiter.
    Call this during application startup if using Redis.
    """
    global _rate_limiter
    _rate_limiter = RedisRateLimiter(redis_client)
