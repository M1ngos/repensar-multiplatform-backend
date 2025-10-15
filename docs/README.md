# Repensar Backend Documentation

Welcome to the Repensar backend API documentation.

## 📚 Documentation Index

### Authentication & Security

- **[Authentication Guide](./authentication.md)** - Complete guide to authentication methods, JWT tokens, and security features
- **[Google Sign In Setup](./google-signin.md)** - Step-by-step guide to configure and integrate Google OAuth

### Getting Started

1. **Setup:** Follow `.env.example` for environment configuration
2. **Authentication:** Read the [Authentication Guide](./authentication.md)
3. **Google OAuth:** Configure using [Google Sign In Setup](./google-signin.md)
4. **API Reference:** Visit `/docs` endpoint when server is running

## 🚀 Quick Start

### 1. Install Dependencies

```bash
uv sync
```

### 2. Configure Environment

Copy and update environment variables:

```bash
cp .env.example .env
# Edit .env with your configuration
```

### 3. Run Database Migrations

```bash
alembic upgrade head
```

### 4. Start Server

```bash
uvicorn app.main:app --reload
```

### 5. Access API Documentation

Visit: http://localhost:8000/docs

## 🔐 Authentication Methods

The API supports two authentication methods:

### Email/Password

Traditional registration and login with JWT tokens.

**Endpoints:**
- `POST /auth/register` - Register new account
- `POST /auth/login` - Login with credentials
- `POST /auth/refresh` - Refresh access token

### Google Sign In

OAuth 2.0 authentication via Google.

**Endpoints:**
- `GET /auth/google/login` - Get authorization URL
- `POST /auth/google/callback` - Handle OAuth callback

**Setup Required:** See [Google Sign In Setup](./google-signin.md)

## 🔧 Configuration

### Required Environment Variables

```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/database

# Security
SECRET_KEY=your-secret-key
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=30

# Email (for verification)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
EMAIL_FROM=noreply@repensar.com
```

### Optional: Google OAuth

```env
GOOGLE_CLIENT_ID=your-client-id
GOOGLE_CLIENT_SECRET=your-client-secret
GOOGLE_REDIRECT_URI=http://localhost:8000/auth/google/callback
```

### Optional: Redis (Production)

```env
REDIS_URL=redis://localhost:6379/0
```

## 📖 API Documentation

### Interactive Documentation

When the server is running, access interactive API documentation:

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

### Authentication Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/register` | Register new user |
| POST | `/auth/login` | Login with email/password |
| POST | `/auth/refresh` | Refresh access token |
| POST | `/auth/logout` | Logout (revoke tokens) |
| GET | `/auth/me` | Get current user profile |
| GET | `/auth/google/login` | Get Google OAuth URL |
| POST | `/auth/google/callback` | Handle Google callback |

### Making Authenticated Requests

Include the access token in the Authorization header:

```bash
curl -H "Authorization: Bearer <access_token>" \
     http://localhost:8000/auth/me
```

## 🛡️ Security Features

- ✅ JWT access and refresh tokens
- ✅ Token rotation and family tracking
- ✅ Account lockout after failed attempts
- ✅ Rate limiting on sensitive endpoints
- ✅ Email verification
- ✅ Password strength validation
- ✅ Audit logging
- ✅ OAuth 2.0 (Google Sign In)
- ✅ CSRF protection
- ✅ Secure password hashing (bcrypt)

## 🔍 Troubleshooting

### Common Issues

**"Could not validate credentials"**
- Token expired → Use refresh token
- Token invalid → Re-authenticate
- Missing Authorization header → Add Bearer token

**"Google Sign In is not configured"**
- Check `.env` has Google OAuth variables
- Restart server after updating `.env`
- See [Google Sign In Setup](./google-signin.md)

**"Email already registered"**
- User exists with this email
- Use login instead of register
- Or use password reset if forgotten

**"Account locked"**
- Too many failed login attempts
- Wait 30 minutes or contact support
- Check audit logs for details

### Database Issues

**Reset database:**
```bash
alembic downgrade base
alembic upgrade head
```

**Check current migration:**
```bash
alembic current
```

**Create new migration:**
```bash
alembic revision --autogenerate -m "Description"
```

## 🧪 Testing

### Manual Testing with curl

**Register user:**
```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test User",
    "email": "test@example.com",
    "password": "SecurePass123",
    "user_type": "volunteer"
  }'
```

**Login:**
```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "SecurePass123"
  }'
```

**Get profile:**
```bash
curl http://localhost:8000/auth/me \
  -H "Authorization: Bearer <access_token>"
```

## 📝 Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [JWT Best Practices](https://tools.ietf.org/html/rfc8725)
- [Google OAuth 2.0](https://developers.google.com/identity/protocols/oauth2)
- [OAuth 2.0 Security](https://tools.ietf.org/html/rfc6749)

## 🤝 Support

For questions or issues:
1. Check the documentation in this directory
2. Review server logs for errors
3. Check audit logs for security events
4. Consult API documentation at `/docs`

---

Last updated: 2025-10-15
