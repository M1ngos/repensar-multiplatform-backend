# Authentication API Specification (Legacy v1)

## Overview

The Authentication (v1 - Legacy) module provides JWT-based authentication with token refresh, password reset, email verification, and user permissions. This is the legacy authentication API under `/auth/v1/`.

**Note**: For new implementations, use the enhanced authentication API at `/auth/` which provides additional security features like token rotation, audit logging, rate limiting, and Google OAuth.

## Permissions

- **Login**: Public (unauthenticated)
- **Register**: Public (unauthenticated)
- **Refresh Token**: Public (requires valid refresh token)
- **Logout**: Authenticated users
- **Get Profile**: Authenticated users
- **Change Password**: Authenticated users
- **Forgot Password**: Public (unauthenticated)
- **Reset Password**: Public (requires reset token)
- **Verify Email**: Public (requires verification token)
- **Resend Verification**: Public (unauthenticated)
- **Validate Token**: Authenticated users
- **Get Auth Status**: Public (optional authentication)
- **Get Permissions**: Authenticated users

## Models

### Token

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "expires_in": 1800
}
```

### UserProfile

```json
{
  "id": 1,
  "name": "John Doe",
  "email": "john@example.com",
  "user_type": "staff_member",
  "is_active": true,
  "is_email_verified": true,
  "last_login": "2025-01-15T10:30:00Z",
  "created_at": "2025-01-01T08:00:00Z"
}
```

## Endpoints

### Login

```
POST /api/v1/auth/v1/login
```

**Request Body:**
```json
{
  "email": "john@example.com",
  "password": "SecurePassword123!"
}
```

**Response: 200 OK**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "expires_in": 1800
}
```

**Response: 400 Bad Request**
```json
{
  "detail": "User is already logged in with a valid token"
}
```

**Response: 401 Unauthorized**
```json
{
  "detail": "Incorrect email or password"
}
```

**Response: 401 Unauthorized (Deactivated)**
```json
{
  "detail": "Account is deactivated"
}
```

**Response: 423 Locked**
```json
{
  "detail": "Account locked due to too many failed attempts. Try again later."
}
```

### Register

```
POST /api/v1/auth/v1/register
```

**Request Body:**
```json
{
  "name": "John Doe",
  "email": "john@example.com",
  "password": "SecurePassword123!",
  "phone": "+1234567890",
  "user_type": "volunteer"
}
```

**Response: 200 OK**
```json
{
  "message": "User registered successfully. Please check your email to verify your account."
}
```

**Response: 400 Bad Request**
```json
{
  "detail": "Email already registered"
}
```

**Response: 400 Bad Request (Invalid Type)**
```json
{
  "detail": "Invalid user type"
}
```

### Refresh Token

```
POST /api/v1/auth/v1/refresh
```

**Request Body:**
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response: 200 OK**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "expires_in": 1800
}
```

**Response: 401 Unauthorized**
```json
{
  "detail": "Invalid refresh token"
}
```

**Response: 401 Unauthorized (Expired)**
```json
{
  "detail": "Refresh token expired"
}
```

### Logout

```
POST /api/v1/auth/v1/logout
```

**Authentication**: Required

**Response: 200 OK**
```json
{
  "message": "Successfully logged out"
}
```

### Get Current User Profile

```
GET /api/v1/auth/v1/me
```

**Authentication**: Required

**Response: 200 OK**
```json
{
  "id": 1,
  "name": "John Doe",
  "email": "john@example.com",
  "user_type": "staff_member",
  "is_active": true,
  "is_email_verified": true,
  "last_login": "2025-01-15T10:30:00Z",
  "created_at": "2025-01-01T08:00:00Z"
}
```

### Change Password

```
POST /api/v1/auth/v1/change-password
```

**Authentication**: Required

**Request Body:**
```json
{
  "current_password": "OldPassword123!",
  "new_password": "NewSecurePassword123!"
}
```

**Response: 200 OK**
```json
{
  "message": "Password changed successfully"
}
```

**Response: 400 Bad Request**
```json
{
  "detail": "Incorrect current password"
}
```

### Forgot Password

```
POST /api/v1/auth/v1/forgot-password
```

**Request Body:**
```json
{
  "email": "john@example.com"
}
```

**Response: 200 OK**
```json
{
  "message": "If an account with this email exists, you will receive a password reset link."
}
```

### Reset Password

```
POST /api/v1/auth/v1/reset-password
```

**Request Body:**
```json
{
  "token": "reset-token-from-email",
  "new_password": "NewSecurePassword123!"
}
```

**Response: 200 OK**
```json
{
  "message": "Password reset successfully"
}
```

**Response: 400 Bad Request**
```json
{
  "detail": "Invalid or expired reset token"
}
```

**Response: 400 Bad Request (Expired)**
```json
{
  "detail": "Reset token has expired"
}
```

### Verify Email

```
POST /api/v1/auth/v1/verify-email
```

**Query Parameters:**
- `token` (required): Email verification token from email

**Response: 200 OK**
```json
{
  "message": "Email verified successfully"
}
```

**Response: 400 Bad Request**
```json
{
  "detail": "Invalid or expired verification token"
}
```

**Response: 400 Bad Request (Expired)**
```json
{
  "detail": "Verification token has expired"
}
```

### Resend Verification Email

```
POST /api/v1/auth/v1/resend-verification
```

**Request Body:**
```json
{
  "email": "john@example.com"
}
```

**Response: 200 OK**
```json
{
  "message": "If an account with this email exists, a verification email will be sent."
}
```

**Response: 400 Bad Request (Already Verified)**
```json
{
  "detail": "Email is already verified"
}
```

### Validate Token

```
GET /api/v1/auth/v1/validate-token
```

**Authentication**: Required

**Response: 200 OK**
```json
{
  "valid": true,
  "user": {
    "id": 1,
    "name": "John Doe",
    "email": "john@example.com",
    "user_type": "staff_member",
    "is_active": true,
    "is_email_verified": true
  }
}
```

**Response: 200 OK (Invalid)**
```json
{
  "valid": false,
  "user": null
}
```

### Get Auth Status

```
GET /api/v1/auth/v1/status
```

**Headers** (optional):
- `Authorization`: Bearer token

**Response: 200 OK (Authenticated)**
```json
{
  "authenticated": true,
  "user": {
    "id": 1,
    "name": "John Doe",
    "email": "john@example.com",
    "user_type": "staff_member",
    "is_active": true,
    "is_email_verified": true,
    "permissions": {...},
    "dashboard_config": {...}
  },
  "message": "Valid token"
}
```

**Response: 200 OK (Not Authenticated)**
```json
{
  "authenticated": false,
  "user": null,
  "message": "No token provided"
}
```

### Get User Permissions

```
GET /api/v1/auth/v1/permissions
```

**Authentication**: Required

**Response: 200 OK**
```json
{
  "user_type": "staff_member",
  "permissions": {
    "projects": ["view", "create", "edit"],
    "tasks": ["view", "create", "edit", "assign"],
    "volunteers": ["view", "manage"],
    "reports": ["view", "export"]
  },
  "dashboard_config": {
    "widgets": ["projects", "tasks", "volunteers", "reports"],
    "default_view": "dashboard"
  },
  "description": "Staff member with extended permissions"
}
```

**Response: 404 Not Found**
```json
{
  "detail": "User type not found"
}
```

## Error Responses

All endpoints may return:

**401 Unauthorized**
```json
{
  "detail": "Not authenticated"
}
```

**500 Internal Server Error**
```json
{
  "detail": "Internal server error"
}
```

## Security Notes

- Access tokens expire after 30 minutes (configurable)
- Refresh tokens expire after 7 days (configurable)
- Account lockout occurs after 5 failed login attempts
- Password reset tokens expire after 1 hour
- Email verification tokens expire after 24 hours
- All tokens are JWT-based with HS256 signing
- Passwords must meet strength requirements (enforced by application)
