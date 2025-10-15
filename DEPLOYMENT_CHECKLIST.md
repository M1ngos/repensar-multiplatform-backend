# v2 Authentication Deployment Checklist

## Pre-Deployment

### 1. Code Review
- [ ] All new files reviewed and approved
- [ ] Security review completed
- [ ] No hardcoded secrets in code
- [ ] All TODO comments addressed

### 2. Testing
- [ ] Unit tests pass (`pytest tests/test_jwt.py tests/test_jwt_v2.py`)
- [ ] Integration tests pass
- [ ] Manual testing completed
- [ ] Token rotation tested
- [ ] Rate limiting tested
- [ ] Reuse detection tested

### 3. Configuration
- [ ] `SECRET_KEY` generated using `secrets.token_urlsafe(64)`
- [ ] Different `SECRET_KEY` for dev/staging/prod
- [ ] Environment variables configured
- [ ] Redis connection string configured (optional for dev)

## Database Migration

### Option 1: Using SQL Script
```bash
# Backup database first!
pg_dump repensar_db > backup_$(date +%Y%m%d_%H%M%S).sql

# Run migration
psql -U repensar -d repensar_db -f migrations/001_add_token_family.sql
```

- [ ] Database backed up
- [ ] Migration script executed
- [ ] Migration verified (column exists)
- [ ] No errors in migration log

### Option 2: Using Alembic
```bash
# Backup database first!
pg_dump repensar_db > backup_$(date +%Y%m%d_%H%M%S).sql

# Run migration
alembic upgrade head
```

- [ ] Database backed up
- [ ] Alembic migration executed
- [ ] Migration verified
- [ ] Alembic history updated

## Deployment

### 1. Backend Deployment

#### Development
```bash
# Install dependencies
pip install -r requirements.txt  # or use uv

# Run application
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

- [ ] Dependencies installed
- [ ] Application starts successfully
- [ ] No startup errors
- [ ] Health check passes (`curl http://localhost:8000/health`)

#### Production
```bash
# Install production dependencies
pip install redis>=6.4.0

# Set environment variables
export SECRET_KEY="your-production-secret-key"
export REDIS_URL="redis://your-redis-host:6379/0"
export DATABASE_URL="postgresql://user:pass@host:5432/db"

# Run with production server
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

- [ ] Production dependencies installed
- [ ] Environment variables set
- [ ] Redis connection tested
- [ ] Application deployed
- [ ] Multiple workers running
- [ ] Load balancer configured
- [ ] SSL/TLS certificates configured

### 2. Verify Deployment

```bash
# Test health endpoint
curl https://api.yourdomain.com/health

# Test root endpoint
curl https://api.yourdomain.com/

# Test v2 login
curl -X POST https://api.yourdomain.com/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password"}'
```

- [ ] Health endpoint responds
- [ ] Root endpoint shows v2.0.0
- [ ] Login endpoint works
- [ ] Refresh endpoint works
- [ ] Rate limiting works
- [ ] v1 endpoints still accessible at `/auth/v1/*`

## Post-Deployment

### 1. Monitoring Setup
- [ ] Application logs configured
- [ ] Audit logs configured
- [ ] Error tracking enabled (Sentry, etc.)
- [ ] Performance monitoring enabled
- [ ] Alert rules configured

### 2. Metrics to Monitor
- [ ] Login success/failure rates
- [ ] Token refresh rates
- [ ] Rate limit triggers
- [ ] Token reuse detections
- [ ] Response times
- [ ] Error rates
- [ ] Redis connection status

### 3. Client Migration
- [ ] Client migration guide distributed
- [ ] Client developers briefed
- [ ] Test clients updated
- [ ] Production clients scheduled for update

### 4. Documentation
- [ ] API documentation updated
- [ ] Internal wiki updated
- [ ] Team notified of changes
- [ ] Migration timeline communicated

## Rollback Plan

If issues occur:

1. **Immediate Rollback**:
   ```bash
   # Point clients back to v1
   # Update client configurations to use /auth/v1/*
   ```
   - [ ] Clients updated to use v1 URLs
   - [ ] Verify v1 endpoints work
   - [ ] Monitor for stability

2. **Database Rollback** (if needed):
   ```sql
   ALTER TABLE users DROP COLUMN IF EXISTS token_family;
   ```
   - [ ] Column removed
   - [ ] Application restarted
   - [ ] Verified working

3. **Code Rollback** (if needed):
   - [ ] Previous version deployed
   - [ ] Verified working
   - [ ] Incident report filed

## Validation Tests

Run these tests post-deployment:

### 1. Basic Authentication
```bash
# Login
TOKEN=$(curl -s -X POST https://api.yourdomain.com/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password"}' \
  | jq -r '.access_token')

# Get profile
curl -s https://api.yourdomain.com/auth/me \
  -H "Authorization: Bearer $TOKEN"
```
- [ ] Login successful
- [ ] Profile retrieved

### 2. Token Refresh
```bash
# Get tokens
TOKENS=$(curl -s -X POST https://api.yourdomain.com/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password"}')

REFRESH_TOKEN=$(echo $TOKENS | jq -r '.refresh_token')

# Refresh
curl -s -X POST https://api.yourdomain.com/auth/refresh \
  -H "Content-Type: application/json" \
  -d "{\"refresh_token\":\"$REFRESH_TOKEN\"}"
```
- [ ] Refresh successful
- [ ] New tokens received
- [ ] Both tokens changed

### 3. Rate Limiting
```bash
# Try 6 failed logins
for i in {1..6}; do
  curl -s -X POST https://api.yourdomain.com/auth/login \
    -H "Content-Type: application/json" \
    -d '{"email":"test@example.com","password":"wrong"}' \
    | jq '.detail'
done
```
- [ ] First 5 attempts: "Incorrect email or password"
- [ ] 6th attempt: "Too many login attempts"

### 4. Audit Logging
```bash
# Login and check logs
TOKEN=$(curl -s -X POST https://api.yourdomain.com/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password"}' \
  | jq -r '.access_token')

# Get audit log
curl -s https://api.yourdomain.com/auth/audit-log \
  -H "Authorization: Bearer $TOKEN"
```
- [ ] Audit log accessible
- [ ] Events recorded
- [ ] Login events present

## Security Checklist

### Production Security
- [ ] HTTPS only (no HTTP)
- [ ] HSTS header enabled
- [ ] CORS properly configured
- [ ] Security headers enabled
- [ ] Rate limiting working
- [ ] No secrets in logs
- [ ] Database connections encrypted
- [ ] Redis connections secured
- [ ] Firewall rules configured
- [ ] VPN/VPC configured (if applicable)

### Secret Management
- [ ] `SECRET_KEY` rotated from default
- [ ] Secrets stored in secure vault
- [ ] Environment-specific secrets
- [ ] No secrets in version control
- [ ] Access to secrets limited

## Performance Checklist

- [ ] Redis connection pool configured
- [ ] Database connection pool configured
- [ ] Response times < 200ms (95th percentile)
- [ ] No memory leaks detected
- [ ] CPU usage within limits
- [ ] Load testing passed

## Compliance Checklist

- [ ] Audit logging meets requirements
- [ ] Data retention policy implemented
- [ ] PII handling compliant
- [ ] Security policies followed
- [ ] Documentation complete

## Sign-off

| Role | Name | Date | Signature |
|------|------|------|-----------|
| Developer | | | |
| Tech Lead | | | |
| DevOps | | | |
| Security | | | |
| Product Owner | | | |

## Notes

**Deployment Date**: _______________

**Deployed By**: _______________

**Issues Encountered**:
-
-
-

**Resolution**:
-
-
-

---

**Deployment Status**: ⬜ Not Started | ⬜ In Progress | ⬜ Completed | ⬜ Rolled Back

**Last Updated**: 2025-01-07
