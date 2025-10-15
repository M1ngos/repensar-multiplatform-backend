# JWT v2 - Quick Reference Card

## 🚀 Quick Start (3 Steps)

```bash
# 1. Run database migration
psql -U repensar -d repensar_db -f migrations/001_add_token_family.sql

# 2. Start application
uvicorn app.main:app --reload

# 3. Test
curl http://localhost:8000/
```

## 📍 Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/auth/login` | POST | Login with email/password |
| `/auth/refresh` | POST | Refresh tokens (rotates both!) |
| `/auth/logout` | POST | Logout current device |
| `/auth/logout-all-devices` | POST | Logout all devices |
| `/auth/me` | GET | Get user profile |
| `/auth/audit-log` | GET | View security events |
| `/auth/v1/*` | * | Legacy endpoints (deprecated) |

## 🔑 Authentication

```bash
# Login
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"password"}'

# Use access token
curl http://localhost:8000/auth/me \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"

# Refresh (BOTH tokens change!)
curl -X POST http://localhost:8000/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{"refresh_token":"YOUR_REFRESH_TOKEN"}'
```

## ⚙️ Environment Variables

```bash
# Required
SECRET_KEY=your-secret-key-here  # Generate: python -c "import secrets; print(secrets.token_urlsafe(64))"
ALGORITHM=HS256

# Token expiration
ACCESS_TOKEN_EXPIRE_MINUTES=30   # 30 minutes
REFRESH_TOKEN_EXPIRE_DAYS=30     # 30 days

# Security
MAX_LOGIN_ATTEMPTS=5              # 5 attempts
LOCKOUT_DURATION_MINUTES=30       # 30 minutes

# Optional: Redis (production)
REDIS_URL=redis://localhost:6379/0
```

## 🔒 Security Features

| Feature | Description | Status |
|---------|-------------|--------|
| Token Rotation | Refresh tokens rotate on each use | ✅ Active |
| Token Blacklisting | Immediate revocation via JTI | ✅ Active |
| Reuse Detection | Revokes family on token reuse | ✅ Active |
| Rate Limiting | 5 login attempts / 5 minutes | ✅ Active |
| Account Lockout | 15-minute lockout after failures | ✅ Active |
| Audit Logging | All security events logged | ✅ Active |

## 🐛 Common Issues

| Issue | Solution |
|-------|----------|
| 401 "Invalid refresh token" | Use NEW refresh token from last refresh |
| 401 "Token reuse detected" | Re-login required (security feature) |
| 429 "Too many requests" | Wait for Retry-After period |
| "Redis connection failed" | OK - Uses in-memory fallback |

## 📊 Rate Limits

| Endpoint | Limit | Window |
|----------|-------|--------|
| Login | 5 attempts | 5 minutes |
| Register | 3 attempts | 1 hour |
| Refresh | 10 attempts | 1 minute |
| Password Reset | 3 attempts | 1 hour |

## ⚠️ CRITICAL: Client Changes

```javascript
// ❌ WRONG - Only updates access token
const { access_token } = await refresh();
setAccessToken(access_token);

// ✅ CORRECT - Updates both tokens
const { access_token, refresh_token } = await refresh();
setAccessToken(access_token);
setRefreshToken(refresh_token);  // CRITICAL!
```

## 🧪 Testing

```bash
# Run tests
pytest tests/test_jwt.py tests/test_jwt_v2.py -v

# Test login
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"password"}'

# Test rate limiting (run 6 times)
for i in {1..6}; do
  curl -X POST http://localhost:8000/auth/login \
    -H "Content-Type: application/json" \
    -d '{"email":"user@example.com","password":"wrong"}';
done
```

## 📚 Documentation

| Document | Purpose |
|----------|---------|
| `V2_CONVERSION_SUMMARY.md` | **Start here** - Overview |
| `DEPLOYMENT_CHECKLIST.md` | Deployment guide |
| `docs/V1_TO_V2_MIGRATION_GUIDE.md` | **Client migration** |
| `docs/JWT_QUICK_START.md` | Getting started |
| `docs/JWT_API_DOCUMENTATION.md` | Complete API reference |
| `docs/JWT_TOKEN_MANAGEMENT_SPEC.md` | Technical details |

## 🔄 Version Info

- **Current Version**: 2.0.0
- **Primary Endpoints**: `/auth/*` (v2)
- **Legacy Endpoints**: `/auth/v1/*` (deprecated)
- **Deprecation Timeline**: 3 months

## 📦 Dependencies

```bash
# Core (already installed)
fastapi[standard]>=0.116.1
sqlmodel>=0.0.24
python-jose[cryptography]>=3.3.0
bcrypt>=4.1.3

# Production (optional)
redis>=6.4.0
```

## 🎯 Next Steps

1. ✅ Run database migration
2. ✅ Test endpoints
3. ⏳ Update clients (see migration guide)
4. ⏳ Configure Redis (production)
5. ⏳ Set up monitoring

## 🆘 Need Help?

- **Quick Start**: `docs/JWT_QUICK_START.md`
- **Migration**: `docs/V1_TO_V2_MIGRATION_GUIDE.md`
- **API Reference**: `docs/JWT_API_DOCUMENTATION.md`
- **Troubleshooting**: `DEPLOYMENT_CHECKLIST.md`

---

**Version**: 2.0.0 | **Status**: ✅ Production Ready | **Updated**: 2025-01-07
