# Authentication Guide

Complete guide to authentication in the Repensar backend API.

## Table of Contents

- [Overview](#overview)
- [Authentication Methods](#authentication-methods)
- [JWT Token Management](#jwt-token-management)
- [Security Features](#security-features)
- [API Endpoints](#api-endpoints)

---

## Overview

The Repensar backend supports two authentication methods:

1. **Email/Password** - Traditional authentication
2. **Google Sign In** - OAuth 2.0 authentication

All authenticated endpoints require a valid JWT access token in the Authorization header:

```
Authorization: Bearer <access_token>
```

---

## Authentication Methods

### 1. Email/Password Authentication

**Registration:**
```bash
POST /auth/register
{
  "name": "John Doe",
  "email": "john@example.com",
  "password": "SecurePass123",
  "phone": "+1234567890",
  "user_type": "volunteer"
}
```

**Login:**
```bash
POST /auth/login
{
  "email": "john@example.com",
  "password": "SecurePass123"
}
```

**Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1Qi...",
  "refresh_token": "eyJ0eXAiOiJKV1Qi...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

### 2. Google Sign In

See [Google Sign In Documentation](./google-signin.md) for detailed setup instructions.

**Get Login URL:**
```bash
GET /auth/google/login
```

**Complete Login:**
```bash
POST /auth/google/callback
{
  "code": "authorization-code",
  "state": "csrf-token"
}
```

---

## JWT Token Management

### Access Tokens

- **Purpose:** Authenticate API requests
- **Lifetime:** 30 minutes (default)
- **Storage:** Memory or secure cookie (never localStorage)
- **Refresh:** Use refresh token when expired

### Refresh Tokens

- **Purpose:** Obtain new access tokens
- **Lifetime:** 30 days (default)
- **Storage:** HttpOnly cookie (recommended) or secure storage
- **Rotation:** New refresh token issued on each use

### Token Refresh

```bash
POST /auth/refresh
{
  "refresh_token": "eyJ0eXAiOiJKV1Qi..."
}
```

**Response:**
```json
{
  "access_token": "new-access-token",
  "refresh_token": "new-refresh-token",
  "token_type": "bearer",
  "expires_in": 1800
}
```

---

## Security Features

### 1. Account Lockout

- Max failed login attempts: 5 (configurable)
- Lockout duration: 30 minutes (configurable)
- Automatic unlock after timeout

### 2. Rate Limiting

- Login: 10 attempts per 15 minutes per IP
- Registration: 3 attempts per hour per IP
- Token refresh: 20 attempts per 15 minutes per IP
- Password reset: 3 attempts per hour per IP

### 3. Token Security

- **Token Rotation:** New refresh token on each use
- **Token Family:** Detects token reuse attacks
- **Blacklist:** Revoked tokens tracked in Redis
- **Secure Storage:** Refresh tokens hashed in database

### 4. Password Requirements

- Minimum 8 characters
- At least 1 uppercase letter
- At least 1 lowercase letter
- At least 1 digit

### 5. Email Verification

- Required for email/password accounts
- Verification token expires in 24 hours
- Resend verification available
- Google accounts auto-verified

### 6. Audit Logging

All authentication events logged:
- Login success/failure
- Account creation
- Token refresh
- Password changes
- Email verification

---

## API Endpoints

### Authentication

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/auth/register` | Register new account | No |
| POST | `/auth/login` | Login with email/password | No |
| POST | `/auth/refresh` | Refresh access token | No |
| POST | `/auth/logout` | Logout (revoke tokens) | Yes |
| POST | `/auth/logout-all-devices` | Logout from all devices | Yes |
| GET | `/auth/google/login` | Get Google OAuth URL | No |
| POST | `/auth/google/callback` | Handle Google callback | No |

### User Management

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/auth/me` | Get current user profile | Yes |
| GET | `/auth/permissions` | Get user permissions | Yes |
| GET | `/auth/validate-token` | Validate JWT token | Yes |
| GET | `/auth/audit-log` | Get user audit log | Yes |

### Email Verification

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/auth/verify-email?token=...` | Verify email address | No |
| POST | `/auth/resend-verification` | Resend verification email | No |

### Password Management

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/auth/forgot-password` | Request password reset | No |
| POST | `/auth/reset-password` | Reset password with token | No |
| POST | `/auth/change-password` | Change password (logged in) | Yes |

---

## Frontend Integration Examples

### Using Access Tokens

```javascript
// Store tokens securely
const { access_token, refresh_token } = await loginResponse.json();
sessionStorage.setItem('access_token', access_token);
// Store refresh_token in HttpOnly cookie via backend

// Make authenticated requests
const response = await fetch('/api/protected-endpoint', {
  headers: {
    'Authorization': `Bearer ${access_token}`
  }
});
```

### Automatic Token Refresh

```javascript
async function fetchWithAuth(url, options = {}) {
  let response = await fetch(url, {
    ...options,
    headers: {
      ...options.headers,
      'Authorization': `Bearer ${getAccessToken()}`
    }
  });

  // If token expired, refresh and retry
  if (response.status === 401) {
    await refreshAccessToken();

    response = await fetch(url, {
      ...options,
      headers: {
        ...options.headers,
        'Authorization': `Bearer ${getAccessToken()}`
      }
    });
  }

  return response;
}

async function refreshAccessToken() {
  const refreshToken = getRefreshToken();

  const response = await fetch('/auth/refresh', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ refresh_token: refreshToken })
  });

  const { access_token, refresh_token } = await response.json();

  sessionStorage.setItem('access_token', access_token);
  // Update refresh_token in cookie
}
```

### Axios Interceptor Example

```javascript
import axios from 'axios';

// Add request interceptor
axios.interceptors.request.use(
  (config) => {
    const token = sessionStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Add response interceptor for auto-refresh
axios.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    // If token expired and we haven't retried yet
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        const refreshToken = getRefreshToken();
        const response = await axios.post('/auth/refresh', {
          refresh_token: refreshToken
        });

        const { access_token } = response.data;
        sessionStorage.setItem('access_token', access_token);

        // Retry original request
        originalRequest.headers.Authorization = `Bearer ${access_token}`;
        return axios(originalRequest);
      } catch (refreshError) {
        // Refresh failed, redirect to login
        window.location.href = '/login';
        return Promise.reject(refreshError);
      }
    }

    return Promise.reject(error);
  }
);
```

---

## Error Responses

### 401 Unauthorized

Token invalid, expired, or missing:
```json
{
  "detail": "Could not validate credentials"
}
```

### 423 Locked

Account locked due to failed login attempts:
```json
{
  "detail": "Account locked due to too many failed attempts. Try again later."
}
```

### 429 Too Many Requests

Rate limit exceeded:
```json
{
  "detail": "Too many login attempts. Retry after 300 seconds."
}
```

---

## Best Practices

### 1. Token Storage

**Access Token:**
- ✅ Memory (React state)
- ✅ SessionStorage (acceptable for SPAs)
- ❌ LocalStorage (XSS vulnerable)
- ❌ Cookies without HttpOnly flag

**Refresh Token:**
- ✅ HttpOnly cookie (best)
- ✅ Secure storage with encryption
- ❌ LocalStorage
- ❌ SessionStorage

### 2. Security Headers

Always include:
```javascript
{
  'Content-Type': 'application/json',
  'Authorization': `Bearer ${token}`,
  'X-Requested-With': 'XMLHttpRequest'
}
```

### 3. HTTPS Only

- Always use HTTPS in production
- Tokens transmitted over secure connections
- Protects against man-in-the-middle attacks

### 4. Token Validation

- Validate tokens on every request
- Check expiration before use
- Handle token refresh gracefully
- Clear tokens on logout

### 5. Error Handling

```javascript
try {
  const response = await authenticatedFetch(url);
  // Handle success
} catch (error) {
  if (error.status === 401) {
    // Try refresh or redirect to login
  } else if (error.status === 423) {
    // Show account locked message
  } else if (error.status === 429) {
    // Show rate limit message
  }
}
```

---

## Configuration

### Environment Variables

```env
# JWT Configuration
SECRET_KEY=your-secret-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=30

# Security
MAX_LOGIN_ATTEMPTS=5
LOCKOUT_DURATION_MINUTES=30

# Email Configuration (for verification)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
EMAIL_FROM=noreply@repensar.com

# Google OAuth (optional)
GOOGLE_CLIENT_ID=your-client-id
GOOGLE_CLIENT_SECRET=your-client-secret
GOOGLE_REDIRECT_URI=http://localhost:8000/auth/google/callback
```

---

## Related Documentation

- [Google Sign In Setup](./google-signin.md)
- [Email Configuration](./email-configuration.md)
- API Reference (OpenAPI docs at `/docs`)

---

Last updated: 2025-10-15
