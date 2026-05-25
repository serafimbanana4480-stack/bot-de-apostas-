# Security Architecture — VBQ-UNIFIED

This document covers authentication, authorization, rate limiting, input validation, and audit logging for the VBQ-UNIFIED API.

---

## 1. Authentication Flow

The API uses JWT (JSON Web Token) bearer authentication.

### Endpoints
- `POST /auth/register` — Create a new user account.
- `POST /auth/login` — Authenticate and receive an `access_token`.
- `GET /auth/me` — Retrieve the current authenticated user's profile.

### Token Details
- **Algorithm**: HS256
- **Secret**: `JWT_SECRET_KEY` environment variable (must be >= 32 random characters).
- **Expiration**: Configurable via `JWT_EXPIRE_MINUTES` (default 30 minutes).
- **Header**: `Authorization: Bearer <token>`

### Password Security
- Passwords are hashed with bcrypt via `passlib`.
- Minimum password length enforced at registration: 8 characters.
- Plaintext passwords are never stored or logged.

---

## 2. Authorization

Three dependency levels are available:

- `get_current_user` — Validates JWT and returns the `User` object.
- `get_current_active_user` — Extends above; rejects inactive accounts (`is_active=false`).
- `require_admin` — Extends above; rejects non-admin users (`is_admin=false`).

### Route Protection
| Route Group | Auth Requirement |
|-------------|-----------------|
| `/health` | Public |
| `/auth/*` | Public (except `/auth/me`) |
| `/predict/*` | Authenticated active user |
| `/signals/*` | Authenticated active user |
| `/admin/*` | Admin only |

---

## 3. Secrets Management

All secrets are injected via environment variables. The `.env.example` template documents every required variable.

| Variable | Purpose |
|----------|---------|
| `JWT_SECRET_KEY` | Signing key for JWT tokens |
| `ENCRYPTION_KEY` | General encryption key for sensitive data at rest |
| `DATABASE_URL` | PostgreSQL connection string |
| `REDIS_PASSWORD` | Redis authentication |

**Rules:**
- Never commit `.env` to version control.
- Rotate `JWT_SECRET_KEY` immediately if leaked; all existing sessions will be invalidated.
- Use a secrets manager (e.g., AWS Secrets Manager, HashiCorp Vault) in production instead of flat files.

---

## 4. CORS Policy

CORS origins are no longer wildcard (`*`).

- **Source**: `ALLOWED_ORIGINS` environment variable (comma-separated list).
- **Default**: `http://localhost:3000,http://localhost:8000`
- **Methods**: `GET, POST, PUT, DELETE, OPTIONS`
- **Headers**: `Authorization, Content-Type, X-Request-ID`

In production, restrict `ALLOWED_ORIGINS` to the exact frontend domain(s).

---

## 5. Rate Limits

Rate limiting is backed by Redis and enforced via `slowapi`.

| Scope | Limit |
|-------|-------|
| Global default | 100 requests / minute |
| `/predict/*` | 10 requests / minute |
| `/signals/*` | 20 requests / minute |

- **Toggle**: `RATE_LIMIT_ENABLED=true|false`
- **Backend**: Redis (`REDIS_URL`)
- Exceeding a limit returns HTTP 429.

---

## 6. Input Validation

All inbound data is validated with Pydantic models before reaching business logic.

### Prediction Endpoints
- `game_id`: Alphanumeric uppercase, 8-20 characters.
- `features`: Optional list, max 500 elements.
- `probability`: Must be between 0.0 and 1.0.
- `limit`: Integer 1-500.

### Signal Endpoints
- `signal_id`: Alphanumeric plus `_` and `-`, 8-50 characters.
- `odd_executed`: Optional float, 1.01-1000.0.
- `notes`: Optional string, max 1000 characters.
- `limit`: Integer 1-500.

### Auth Endpoints
- `username`: 3-50 characters.
- `email`: Valid email format.
- `password`: 8-128 characters.

---

## 7. Audit Logging

Every request is logged with structured JSON (production) or colored console output (development).

### Log Fields
- `timestamp` — ISO 8601 UTC
- `request_id` — UUID generated per request (also returned in `X-Request-ID` header)
- `method` — HTTP method
- `path` — Request path
- `status` — HTTP response status code
- `duration` — Request processing time in seconds
- `client` — Client IP address
- `user_id` — Authenticated user identifier (where applicable)

### Log Format
- **Development**: Human-readable colored console output.
- **Production**: JSON lines with full traceback support.

### Middleware
- `request_id_middleware` — Injects `X-Request-ID` and binds it to structlog contextvars.
- `logging_middleware` — Captures method, path, status, duration, and emits a structured log entry.

---

## 8. Error Handling

Custom exception handlers ensure consistent error responses and prevent information leakage.

| Exception | Response | Details |
|-----------|----------|---------|
| `ValidationError` (Pydantic) | 422 | Field-level error array |
| `HTTPException` (FastAPI) | As-is | Preserves status and detail |
| Generic `Exception` | 500 | Generic "Internal server error"; full error logged server-side |

All error responses include the `request_id` for traceability.

---

## 9. Security Checklist

- [ ] Rotate default `JWT_SECRET_KEY` before production deployment.
- [ ] Restrict `ALLOWED_ORIGINS` to production frontend domain.
- [ ] Enable `RATE_LIMIT_ENABLED=true` in production.
- [ ] Run PostgreSQL with TLS enabled.
- [ ] Run Redis with `requirepass` and TLS in production.
- [ ] Enable HTTPS termination at the reverse proxy / load balancer.
- [ ] Disable Uvicorn auto-reload (`--reload`) in production.
- [ ] Regularly update dependencies (`pip-audit`, `safety`).
