"""
Google OAuth integration for authentication.
Handles OAuth flow, token exchange, and user profile fetching.
"""

import logging
from typing import Optional, Dict, Any
from authlib.integrations.starlette_client import OAuth
from fastapi import HTTPException, status
import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

# Initialize OAuth client
oauth = OAuth()

def register_oauth_clients():
    """
    Register OAuth clients (Google, etc.) with the application.
    Call this during app startup.
    """
    if settings.GOOGLE_CLIENT_ID and settings.GOOGLE_CLIENT_SECRET:
        oauth.register(
            name='google',
            client_id=settings.GOOGLE_CLIENT_ID,
            client_secret=settings.GOOGLE_CLIENT_SECRET,
            server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
            client_kwargs={
                'scope': 'openid email profile',
                'prompt': 'select_account',  # Always show account selector
            }
        )
        logger.info("Google OAuth client registered successfully")
    else:
        logger.warning("Google OAuth credentials not configured. Google Sign In will be disabled.")


async def get_google_user_info(access_token: str) -> Optional[Dict[str, Any]]:
    """
    Fetch user information from Google using the access token.

    Args:
        access_token: OAuth access token from Google

    Returns:
        Dictionary containing user info (email, name, picture, sub)
        Returns None if the request fails
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                'https://www.googleapis.com/oauth2/v3/userinfo',
                headers={'Authorization': f'Bearer {access_token}'}
            )
            response.raise_for_status()
            return response.json()
    except httpx.HTTPError as e:
        logger.error(f"Failed to fetch Google user info: {e}")
        return None


async def verify_google_oauth_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Verify Google OAuth token and extract user information.

    Args:
        token: OAuth token from Google

    Returns:
        Dictionary containing verified user info
        Returns None if verification fails
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f'https://oauth2.googleapis.com/tokeninfo?id_token={token}'
            )
            response.raise_for_status()
            token_info = response.json()

            # Verify the token is for our app
            if token_info.get('aud') != settings.GOOGLE_CLIENT_ID:
                logger.error("Invalid Google token audience")
                return None

            return token_info
    except httpx.HTTPError as e:
        logger.error(f"Failed to verify Google token: {e}")
        return None


def validate_google_oauth_config() -> bool:
    """
    Check if Google OAuth is properly configured.

    Returns:
        True if configuration is valid, False otherwise
    """
    if not settings.GOOGLE_CLIENT_ID:
        logger.error("GOOGLE_CLIENT_ID not configured")
        return False

    if not settings.GOOGLE_CLIENT_SECRET:
        logger.error("GOOGLE_CLIENT_SECRET not configured")
        return False

    if not settings.GOOGLE_REDIRECT_URI:
        logger.error("GOOGLE_REDIRECT_URI not configured")
        return False

    return True


def get_google_oauth_url(state: str) -> str:
    """
    Generate Google OAuth authorization URL.

    Args:
        state: CSRF protection state token

    Returns:
        Authorization URL to redirect user to
    """
    if not validate_google_oauth_config():
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Google OAuth is not properly configured"
        )

    # Build authorization URL
    base_url = "https://accounts.google.com/o/oauth2/v2/auth"
    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": "openid email profile",
        "state": state,
        "access_type": "offline",
        "prompt": "select_account"
    }

    # Construct URL with query parameters
    param_string = "&".join([f"{k}={v}" for k, v in params.items()])
    return f"{base_url}?{param_string}"


async def exchange_code_for_tokens(code: str) -> Optional[Dict[str, Any]]:
    """
    Exchange authorization code for access and ID tokens.

    Args:
        code: Authorization code from Google

    Returns:
        Dictionary containing tokens (access_token, id_token, etc.)
        Returns None if exchange fails
    """
    if not validate_google_oauth_config():
        return None

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                'https://oauth2.googleapis.com/token',
                data={
                    'code': code,
                    'client_id': settings.GOOGLE_CLIENT_ID,
                    'client_secret': settings.GOOGLE_CLIENT_SECRET,
                    'redirect_uri': settings.GOOGLE_REDIRECT_URI,
                    'grant_type': 'authorization_code'
                }
            )
            response.raise_for_status()
            return response.json()
    except httpx.HTTPError as e:
        logger.error(f"Failed to exchange code for tokens: {e}")
        return None
