# Google Sign In Integration

This document explains how to configure and use Google Sign In (OAuth 2.0) authentication in the Repensar backend.

## Table of Contents

- [Overview](#overview)
- [Setup Instructions](#setup-instructions)
- [API Endpoints](#api-endpoints)
- [Frontend Integration](#frontend-integration)
- [Security Features](#security-features)
- [Troubleshooting](#troubleshooting)

---

## Overview

The application supports Google Sign In alongside traditional email/password authentication. Users can:

- Sign up using their Google account (no password required)
- Sign in to existing accounts via Google
- Link Google to existing email/password accounts
- Automatically verify email addresses (Google emails are trusted)

**Key Features:**

- OAuth 2.0 compliant
- Automatic user creation for new Google users
- Profile picture import from Google
- Email verification handled automatically
- Secure token management with JWT
- Full audit logging support

---

## Setup Instructions

### 1. Create Google OAuth Credentials

1. **Go to Google Cloud Console**
   - Visit: https://console.cloud.google.com/

2. **Create or Select a Project**
   - Click on project dropdown at the top
   - Create a new project or select an existing one

3. **Enable Required APIs**
   - Navigate to "APIs & Services" → "Library"
   - Search for "Google+ API" or "Google Identity"
   - Click "Enable"

4. **Configure OAuth Consent Screen**
   - Go to "APIs & Services" → "OAuth consent screen"
   - Choose "External" (for public users) or "Internal" (for organization only)
   - Fill in required information:
     - App name: "Repensar"
     - User support email: your email
     - Developer contact: your email
   - Add scopes: `openid`, `email`, `profile`
   - Save and continue

5. **Create OAuth 2.0 Credentials**
   - Go to "APIs & Services" → "Credentials"
   - Click "Create Credentials" → "OAuth 2.0 Client ID"
   - Application type: **Web application**
   - Name: "Repensar Backend"
   - Authorized redirect URIs:
     - Development: `http://localhost:8000/auth/google/callback`
     - Production: `https://yourdomain.com/auth/google/callback`
   - Click "Create"
   - **Save the Client ID and Client Secret**

### 2. Configure Environment Variables

Add the following to your `.env` file:

```env
# Google OAuth Configuration
GOOGLE_CLIENT_ID=your-actual-client-id-here.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-actual-client-secret-here
GOOGLE_REDIRECT_URI=http://localhost:8000/auth/google/callback
```

**Important Notes:**

- **Never commit real credentials to Git**
- Use different credentials for development and production
- Update `GOOGLE_REDIRECT_URI` to match your production domain
- The Client ID typically ends with `.apps.googleusercontent.com`

### 3. Verify Installation

1. **Check dependencies are installed:**
   ```bash
   uv sync
   ```

2. **Verify migration was applied:**
   ```bash
   alembic current
   # Should show: 002 (head)
   ```

3. **Restart your server:**
   ```bash
   uvicorn app.main:app --reload
   ```

4. **Test the endpoint:**
   ```bash
   curl http://localhost:8000/auth/google/login
   ```

   Should return:
   ```json
   {
     "authorization_url": "https://accounts.google.com/o/oauth2/v2/auth?...",
     "state": "random-csrf-token"
   }
   ```

---

## API Endpoints

### GET `/auth/google/login`

Get the Google OAuth authorization URL to redirect users to.

**Response:**
```json
{
  "authorization_url": "https://accounts.google.com/o/oauth2/v2/auth?client_id=...",
  "state": "csrf-protection-token"
}
```

**Status Codes:**
- `200 OK` - Success
- `503 Service Unavailable` - Google OAuth not configured

**Example:**
```bash
curl http://localhost:8000/auth/google/login
```

---

### POST `/auth/google/callback`

Handle the OAuth callback from Google and return JWT tokens.

**Request Body:**
```json
{
  "code": "authorization-code-from-google",
  "state": "csrf-token-from-login-endpoint"
}
```

**Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

**Status Codes:**
- `200 OK` - Success (user logged in)
- `400 Bad Request` - Invalid code or failed to fetch user info
- `500 Internal Server Error` - Server configuration error

**Example:**
```bash
curl -X POST http://localhost:8000/auth/google/callback \
  -H "Content-Type: application/json" \
  -d '{"code": "4/0AY...", "state": "csrf-token"}'
```

---

## Frontend Integration

### React Example

```javascript
// GoogleSignInButton.jsx
import { useState } from 'react';

export default function GoogleSignInButton() {
  const [loading, setLoading] = useState(false);

  const handleGoogleSignIn = async () => {
    setLoading(true);

    try {
      // 1. Get authorization URL
      const response = await fetch('http://localhost:8000/auth/google/login');
      const { authorization_url, state } = await response.json();

      // 2. Store state in sessionStorage for validation (optional)
      sessionStorage.setItem('oauth_state', state);

      // 3. Redirect to Google
      window.location.href = authorization_url;
    } catch (error) {
      console.error('Failed to initiate Google Sign In:', error);
      setLoading(false);
    }
  };

  return (
    <button
      onClick={handleGoogleSignIn}
      disabled={loading}
      className="google-signin-btn"
    >
      {loading ? 'Loading...' : 'Sign in with Google'}
    </button>
  );
}
```

### Callback Handler

```javascript
// pages/auth/callback.jsx
import { useEffect } from 'react';
import { useRouter } from 'next/router';

export default function GoogleCallback() {
  const router = useRouter();

  useEffect(() => {
    const handleCallback = async () => {
      // Get code and state from URL
      const params = new URLSearchParams(window.location.search);
      const code = params.get('code');
      const state = params.get('state');

      if (!code) {
        console.error('No authorization code received');
        router.push('/login?error=oauth_failed');
        return;
      }

      try {
        // Exchange code for tokens
        const response = await fetch('http://localhost:8000/auth/google/callback', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ code, state })
        });

        if (!response.ok) {
          throw new Error('Failed to authenticate');
        }

        const { access_token, refresh_token } = await response.json();

        // Store tokens
        localStorage.setItem('access_token', access_token);
        localStorage.setItem('refresh_token', refresh_token);

        // Redirect to dashboard
        router.push('/dashboard');
      } catch (error) {
        console.error('Authentication failed:', error);
        router.push('/login?error=oauth_failed');
      }
    };

    handleCallback();
  }, [router]);

  return <div>Completing sign in...</div>;
}
```

### Vue.js Example

```vue
<template>
  <button @click="signInWithGoogle" :disabled="loading">
    {{ loading ? 'Loading...' : 'Sign in with Google' }}
  </button>
</template>

<script>
export default {
  data() {
    return {
      loading: false
    };
  },
  methods: {
    async signInWithGoogle() {
      this.loading = true;

      try {
        const response = await fetch('http://localhost:8000/auth/google/login');
        const { authorization_url } = await response.json();

        window.location.href = authorization_url;
      } catch (error) {
        console.error('Failed to initiate Google Sign In:', error);
        this.loading = false;
      }
    }
  }
};
</script>
```

---

## Security Features

### 1. CSRF Protection

- State token is generated for each login request
- Should be validated in production implementations
- Prevents cross-site request forgery attacks

### 2. Token Management

- JWT tokens with expiration
- Refresh token rotation
- Token family tracking for security
- Automatic token revocation on password change

### 3. Email Verification

- Google emails are automatically verified
- No verification email needed
- Trusted identity provider

### 4. Audit Logging

All OAuth events are logged:
- Account creation via Google
- Login via Google
- Failed authentication attempts
- Token issuance and refresh

### 5. Account Security

- OAuth users cannot use password login
- Prevents account takeover via password guessing
- Secure token storage in database (hashed)

---

## Troubleshooting

### Error: "Google Sign In is not configured on this server"

**Cause:** Environment variables not set

**Solution:**
1. Check `.env` file has all three variables:
   - `GOOGLE_CLIENT_ID`
   - `GOOGLE_CLIENT_SECRET`
   - `GOOGLE_REDIRECT_URI`
2. Restart the server after updating `.env`

---

### Error: "redirect_uri_mismatch"

**Cause:** Redirect URI in Google Cloud Console doesn't match your configuration

**Solution:**
1. Go to Google Cloud Console → Credentials
2. Edit your OAuth 2.0 Client ID
3. Add the exact URI from your `.env` file to "Authorized redirect URIs"
4. For development: `http://localhost:8000/auth/google/callback`
5. Must match exactly (including http/https, port, path)

---

### Error: "Failed to exchange authorization code"

**Possible Causes:**
- Invalid Client Secret
- Code already used (codes are single-use)
- Code expired (valid for ~10 minutes)
- Network issues

**Solution:**
1. Verify `GOOGLE_CLIENT_SECRET` is correct
2. Don't reuse authorization codes
3. Complete the flow within 10 minutes
4. Check server logs for detailed error

---

### Error: "This account uses Google Sign In"

**Cause:** User trying to login with password for a Google-only account

**Solution:**
- User should use "Sign in with Google" button
- Account was created via Google OAuth
- No password was ever set for this account

---

### Users can't see their profile picture

**Cause:** Profile picture URL may be expired or restricted

**Solution:**
1. Check `user.profile_picture` field in database
2. Google profile pictures should persist
3. May need to re-fetch on expiration
4. Consider storing images locally if needed

---

### Development: Google OAuth not working on localhost

**Cause:** Some browsers block third-party cookies

**Solution:**
1. Use Chrome/Edge which handle OAuth better
2. Enable third-party cookies for development
3. Or use `127.0.0.1` instead of `localhost`
4. For production, use HTTPS domain

---

## Database Schema

### User Model Fields

```python
oauth_provider: Optional[str]       # "google"
oauth_provider_id: Optional[str]    # Google's user ID (sub)
profile_picture: Optional[str]      # URL to profile picture
password_hash: Optional[str]        # None for OAuth-only users
is_email_verified: bool             # Automatically True for Google users
```

### Migration

The OAuth fields were added in migration `002_add_oauth_fields_to_users.py`:

```bash
# Apply migration
alembic upgrade head

# Rollback if needed
alembic downgrade -1
```

---

## Production Considerations

### 1. Use HTTPS

Always use HTTPS in production:
```env
GOOGLE_REDIRECT_URI=https://yourdomain.com/auth/google/callback
```

### 2. Environment-Specific Credentials

Use different OAuth clients for each environment:
- Development: `localhost` redirect URI
- Staging: `staging.yourdomain.com` redirect URI
- Production: `yourdomain.com` redirect URI

### 3. Implement State Validation

For production, validate the state token:

```python
# Store state in Redis/session
# Validate in callback handler
if stored_state != callback_state:
    raise HTTPException(status_code=400, detail="Invalid state token")
```

### 4. Rate Limiting

Implement rate limiting on OAuth endpoints:
- Prevent callback endpoint abuse
- Limit login attempts per IP

### 5. Monitor OAuth Errors

Set up monitoring for:
- Failed token exchanges
- Invalid credentials
- API quota limits from Google

### 6. Backup Authentication

Always provide alternative authentication:
- Email/password login
- Password reset flow
- Account recovery options

---

## Additional Resources

- [Google OAuth 2.0 Documentation](https://developers.google.com/identity/protocols/oauth2)
- [Google Cloud Console](https://console.cloud.google.com/)
- [OAuth 2.0 Best Practices](https://tools.ietf.org/html/rfc6749)
- [Authlib Documentation](https://docs.authlib.org/)

---

## Support

For issues or questions:
1. Check server logs for detailed errors
2. Verify Google Cloud Console configuration
3. Test with Google's OAuth Playground
4. Review audit logs in database

---

Last updated: 2025-10-15
