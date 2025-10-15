"""
Production-grade JWT token management with blacklisting, rotation, and audit logging.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, Set
from dataclasses import dataclass
import secrets
import hashlib
from enum import Enum

from app.core.config import settings


class TokenStatus(Enum):
    """Token status enumeration."""
    ACTIVE = "active"
    REVOKED = "revoked"
    EXPIRED = "expired"
    COMPROMISED = "compromised"


@dataclass
class TokenMetadata:
    """Metadata for token tracking."""
    jti: str  # JWT ID
    user_id: int
    token_family: str  # For refresh token rotation
    issued_at: datetime
    expires_at: datetime
    token_type: str  # "access" or "refresh"
    issued_from_ip: Optional[str] = None
    user_agent: Optional[str] = None
    status: TokenStatus = TokenStatus.ACTIVE


class InMemoryTokenBlacklist:
    """
    In-memory token blacklist for development/testing.
    In production, use Redis or another distributed cache.
    """

    def __init__(self):
        self._blacklist: Set[str] = set()
        self._token_metadata: Dict[str, TokenMetadata] = {}
        self._family_tokens: Dict[str, Set[str]] = {}  # token_family -> set of jtis

    def add_to_blacklist(self, jti: str, expires_at: datetime) -> None:
        """Add a token to the blacklist."""
        self._blacklist.add(jti)

    def is_blacklisted(self, jti: str) -> bool:
        """Check if a token is blacklisted."""
        return jti in self._blacklist

    def store_token_metadata(self, metadata: TokenMetadata) -> None:
        """Store token metadata for tracking."""
        self._token_metadata[metadata.jti] = metadata

        # Track token families for rotation
        if metadata.token_family not in self._family_tokens:
            self._family_tokens[metadata.token_family] = set()
        self._family_tokens[metadata.token_family].add(metadata.jti)

    def get_token_metadata(self, jti: str) -> Optional[TokenMetadata]:
        """Retrieve token metadata."""
        return self._token_metadata.get(jti)

    def revoke_token_family(self, token_family: str) -> int:
        """
        Revoke all tokens in a family (for refresh token rotation compromise detection).
        Returns the number of tokens revoked.
        """
        if token_family not in self._family_tokens:
            return 0

        jtis = self._family_tokens[token_family]
        for jti in jtis:
            self._blacklist.add(jti)
            if jti in self._token_metadata:
                self._token_metadata[jti].status = TokenStatus.COMPROMISED

        return len(jtis)

    def revoke_user_tokens(self, user_id: int) -> int:
        """
        Revoke all tokens for a specific user.
        Returns the number of tokens revoked.
        """
        count = 0
        for jti, metadata in self._token_metadata.items():
            if metadata.user_id == user_id and metadata.status == TokenStatus.ACTIVE:
                self._blacklist.add(jti)
                metadata.status = TokenStatus.REVOKED
                count += 1
        return count

    def cleanup_expired(self) -> int:
        """
        Remove expired tokens from the blacklist and metadata storage.
        Returns the number of tokens cleaned up.
        """
        now = datetime.now(timezone.utc)
        expired_jtis = []

        for jti, metadata in self._token_metadata.items():
            if metadata.expires_at < now:
                expired_jtis.append(jti)

        for jti in expired_jtis:
            self._blacklist.discard(jti)
            metadata = self._token_metadata.pop(jti, None)
            if metadata and metadata.token_family in self._family_tokens:
                self._family_tokens[metadata.token_family].discard(jti)

        return len(expired_jtis)


class RedisTokenBlacklist:
    """
    Redis-based token blacklist for production use.
    Provides distributed caching and automatic expiration.
    """

    def __init__(self, redis_client):
        """
        Initialize with a Redis client.

        Args:
            redis_client: Redis client instance (from redis-py or aioredis)
        """
        self.redis = redis_client
        self._blacklist_prefix = "token:blacklist:"
        self._metadata_prefix = "token:metadata:"
        self._family_prefix = "token:family:"
        self._user_tokens_prefix = "user:tokens:"

    def add_to_blacklist(self, jti: str, expires_at: datetime) -> None:
        """Add a token to the blacklist with automatic expiration."""
        ttl = int((expires_at - datetime.now(timezone.utc)).total_seconds())
        if ttl > 0:
            self.redis.setex(
                f"{self._blacklist_prefix}{jti}",
                ttl,
                "1"
            )

    def is_blacklisted(self, jti: str) -> bool:
        """Check if a token is blacklisted."""
        return self.redis.exists(f"{self._blacklist_prefix}{jti}") > 0

    def store_token_metadata(self, metadata: TokenMetadata) -> None:
        """Store token metadata with automatic expiration."""
        ttl = int((metadata.expires_at - datetime.now(timezone.utc)).total_seconds())
        if ttl > 0:
            # Store metadata
            key = f"{self._metadata_prefix}{metadata.jti}"
            self.redis.hset(key, mapping={
                "user_id": metadata.user_id,
                "token_family": metadata.token_family,
                "token_type": metadata.token_type,
                "issued_at": metadata.issued_at.isoformat(),
                "expires_at": metadata.expires_at.isoformat(),
                "status": metadata.status.value,
                "issued_from_ip": metadata.issued_from_ip or "",
                "user_agent": metadata.user_agent or "",
            })
            self.redis.expire(key, ttl)

            # Track token family
            family_key = f"{self._family_prefix}{metadata.token_family}"
            self.redis.sadd(family_key, metadata.jti)
            self.redis.expire(family_key, ttl)

            # Track user tokens
            user_key = f"{self._user_tokens_prefix}{metadata.user_id}"
            self.redis.sadd(user_key, metadata.jti)
            self.redis.expire(user_key, ttl)

    def get_token_metadata(self, jti: str) -> Optional[TokenMetadata]:
        """Retrieve token metadata."""
        key = f"{self._metadata_prefix}{jti}"
        data = self.redis.hgetall(key)

        if not data:
            return None

        return TokenMetadata(
            jti=jti,
            user_id=int(data[b"user_id"]),
            token_family=data[b"token_family"].decode(),
            token_type=data[b"token_type"].decode(),
            issued_at=datetime.fromisoformat(data[b"issued_at"].decode()),
            expires_at=datetime.fromisoformat(data[b"expires_at"].decode()),
            status=TokenStatus(data[b"status"].decode()),
            issued_from_ip=data[b"issued_from_ip"].decode() or None,
            user_agent=data[b"user_agent"].decode() or None,
        )

    def revoke_token_family(self, token_family: str) -> int:
        """Revoke all tokens in a family."""
        family_key = f"{self._family_prefix}{token_family}"
        jtis = self.redis.smembers(family_key)

        count = 0
        for jti in jtis:
            jti_str = jti.decode() if isinstance(jti, bytes) else jti
            metadata = self.get_token_metadata(jti_str)
            if metadata:
                self.add_to_blacklist(jti_str, metadata.expires_at)
                count += 1

        return count

    def revoke_user_tokens(self, user_id: int) -> int:
        """Revoke all tokens for a specific user."""
        user_key = f"{self._user_tokens_prefix}{user_id}"
        jtis = self.redis.smembers(user_key)

        count = 0
        for jti in jtis:
            jti_str = jti.decode() if isinstance(jti, bytes) else jti
            metadata = self.get_token_metadata(jti_str)
            if metadata:
                self.add_to_blacklist(jti_str, metadata.expires_at)
                count += 1

        return count

    def cleanup_expired(self) -> int:
        """Redis handles expiration automatically, so this is a no-op."""
        return 0


# Global token blacklist instance
_token_blacklist: Optional[InMemoryTokenBlacklist] = None


def get_token_blacklist() -> InMemoryTokenBlacklist:
    """Get or create the token blacklist instance."""
    global _token_blacklist
    if _token_blacklist is None:
        _token_blacklist = InMemoryTokenBlacklist()
    return _token_blacklist


def initialize_redis_blacklist(redis_client):
    """
    Initialize the Redis-based token blacklist.
    Call this during application startup if using Redis.
    """
    global _token_blacklist
    _token_blacklist = RedisTokenBlacklist(redis_client)


def generate_jti() -> str:
    """Generate a unique JWT ID."""
    return secrets.token_urlsafe(32)


def generate_token_family() -> str:
    """Generate a unique token family ID for refresh token rotation."""
    return secrets.token_urlsafe(16)


def hash_token(token: str) -> str:
    """Create a hash of a token for secure storage."""
    return hashlib.sha256(token.encode()).hexdigest()


def revoke_token(jti: str, expires_at: datetime) -> None:
    """Revoke a specific token."""
    blacklist = get_token_blacklist()
    blacklist.add_to_blacklist(jti, expires_at)


def is_token_revoked(jti: str) -> bool:
    """Check if a token has been revoked."""
    blacklist = get_token_blacklist()
    return blacklist.is_blacklisted(jti)


def revoke_all_user_tokens(user_id: int) -> int:
    """
    Revoke all tokens for a user.
    Useful for security incidents or account compromise.
    """
    blacklist = get_token_blacklist()
    return blacklist.revoke_user_tokens(user_id)


def revoke_refresh_token_family(token_family: str) -> int:
    """
    Revoke all tokens in a refresh token family.
    Used when refresh token reuse is detected (potential compromise).
    """
    blacklist = get_token_blacklist()
    return blacklist.revoke_token_family(token_family)
