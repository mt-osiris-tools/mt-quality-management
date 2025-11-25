# Technology Stack Research: Document Control Process

**Feature**: 001-document-control
**Date**: 2025-11-24
**Purpose**: Resolve technical unknowns and select technology stack for ISO 27001-compliant document management system

## Executive Summary

Selected a **lightweight, security-focused stack** optimized for ISO 27001 compliance:
- **Backend**: Python 3.11+ with FastAPI
- **Database**: PostgreSQL 16+ with pgcrypto (AES-256 encryption)
- **Search**: PostgreSQL native full-text search
- **Authentication**: JWT middleware with RBAC
- **Deployment**: Docker Compose (Phase 1) → Kubernetes (Phase 2)

This stack meets all constitutional requirements while maintaining simplicity and clear scaling paths.

## 1. Backend Language & Framework

### Decision: Python 3.11+ with FastAPI 0.115+

### Rationale:
- **Security Ecosystem**: Mature security libraries (bandit, safety) and explicit error handling ideal for compliance-focused development
- **Middleware Security**: FastAPI's dependency injection system elegantly implements constitutional requirement for middleware-based security enforcement
- **Performance**: Async-native architecture delivers 3,000+ RPS, exceeding 100 concurrent user requirement
- **ISO 27001 Alignment**: Automatic OpenAPI documentation supports Control A.14 (documented interfaces)
- **Audit Logging**: Structured logging with `structlog` simplifies immutable audit trail implementation
- **Type Safety**: Pydantic validation prevents entire classes of input vulnerabilities

### Alternatives Considered:
- **Django REST Framework**: Too heavyweight for API-focused system, synchronous architecture impacts performance
- **Node.js/NestJS**: Less mature security tooling, callback complexity in security-critical paths
- **Go**: Best performance but smaller ISO 27001 library ecosystem, development velocity tradeoff
- **Java Spring Boot**: Enterprise-grade but too resource-intensive for initial scale

### Implementation Notes:
- Use FastAPI 0.115+ (latest 2025 version)
- Integrate `fastapi-jwt-auth` for JWT validation
- Implement `structlog` for structured audit logging
- Add security headers via middleware
- Use `python-multipart` for secure file upload validation

## 2. Database for Document Storage

### Decision: PostgreSQL 16+ with pgcrypto extension

### Rationale:
- **AES-256 Encryption**: pgcrypto provides column-level encryption via `pgp_sym_encrypt()` with `cipher-algo=aes256`
- **ACID Transactions**: Critical for audit trail integrity (ISO 27001 Control A.12)
- **Full-Text Search**: Native `tsvector` and `ts_vector` handle 10,000 documents with <2s search requirement
- **JSONB Support**: Flexible document metadata storage with indexing
- **Version Control**: Temporal tables or trigger-based history for document versioning
- **Row-Level Security**: Database-level RBAC enforcement (defense in depth)

### Alternatives Considered:
- **MongoDB**: Eventual consistency risks for audit trails, weaker transaction guarantees
- **SQL Server TDE**: Licensing costs, Windows-centric, heavier resource footprint

### Implementation Notes:
```sql
-- Enable encryption extension
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Encrypt document content (separate keys per classification)
INSERT INTO documents (content_encrypted)
VALUES (pgp_sym_encrypt('document text', :key, 'cipher-algo=aes256'));

-- Decrypt at query time
SELECT pgp_sym_decrypt(content_encrypted, :key) FROM documents;

-- Full-text search setup
ALTER TABLE documents ADD COLUMN search_vector tsvector;
CREATE INDEX idx_search ON documents USING gin(search_vector);
UPDATE documents SET search_vector = to_tsvector('english', title || ' ' || content);
```

**Challenge**: Encrypted data cannot be searched directly.
**Solution**: Maintain separate searchable summary field OR decrypt at query time (performance tradeoff for initial scale acceptable).

## 3. Full-Text Search Engine

### Decision: PostgreSQL Native Full-Text Search (initial) with Meilisearch migration path

### Rationale:
- **Sufficient Performance**: PostgreSQL with gin indexes meets <2s requirement for 10,000 documents
- **Simplified Architecture**: Single database reduces operational complexity and security audit surface
- **Permission Integration**: Row-level security integrates directly with search queries
- **Cost-Effective**: No additional infrastructure for initial scale

### Migration Trigger:
Switch to **Meilisearch** when:
- Document count exceeds 50,000, OR
- P95 search latency exceeds 1.5 seconds

### Alternatives Considered:
- **Meilisearch**: 7x faster indexing than Elasticsearch, but added operational complexity not justified for 10k docs
- **Elasticsearch**: Industry standard but overkill for initial scale (better for petabyte-scale)

### Implementation Notes:
```sql
-- Weighted full-text search (title more important than content)
ALTER TABLE documents ADD COLUMN search_vector tsvector;
UPDATE documents SET search_vector =
  setweight(to_tsvector('english', title), 'A') ||
  setweight(to_tsvector('english', content), 'B');

-- Automatic search vector updates
CREATE TRIGGER documents_search_update
BEFORE INSERT OR UPDATE ON documents
FOR EACH ROW EXECUTE FUNCTION
tsvector_update_trigger(search_vector, 'pg_catalog.english', title, content);

-- Search with ranking
SELECT * FROM documents
WHERE search_vector @@ to_tsquery('search_term')
ORDER BY ts_rank(search_vector, to_tsquery('search_term')) DESC;
```

## 4. Audit Log Storage

### Decision: PostgreSQL append-only table with partitioning + checksum chain

### Rationale:
- **Immutability**: Revoke DELETE/UPDATE permissions enforces append-only behavior
- **Integrity Verification**: Blockchain-style checksum chain (each entry includes hash of previous)
- **Query Performance**: Monthly partitioning optimizes audit reviews
- **ACID Guarantees**: Never lose audit logs during failures
- **Simplified Operations**: Single database technology

### Alternative for Phase 2: immudb Vault
Evaluate **immudb** for cryptographic verification if automated audit verification becomes critical compliance requirement.

### Alternatives Considered:
- **Separate Audit Database**: Physical isolation benefits don't justify doubled operational overhead
- **Blockchain solutions**: Over-engineered for ISO 27001 requirements

### Implementation Notes:
```sql
-- Append-only audit table with checksum chain
CREATE TABLE audit_logs (
  id BIGSERIAL PRIMARY KEY,
  timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  event_type VARCHAR(50) NOT NULL,
  actor_id INTEGER NOT NULL,
  actor_role VARCHAR(20) NOT NULL,
  resource_type VARCHAR(50) NOT NULL,
  resource_id INTEGER,
  action VARCHAR(50) NOT NULL,
  classification_level INTEGER,
  ip_address INET,
  user_agent TEXT,
  details JSONB,
  previous_hash VARCHAR(64),
  current_hash VARCHAR(64) GENERATED ALWAYS AS (
    encode(sha256((id || timestamp || event_type || actor_id || action || COALESCE(previous_hash, ''))::bytea), 'hex')
  ) STORED
);

-- Partition by month
CREATE TABLE audit_logs_2025_11 PARTITION OF audit_logs
FOR VALUES FROM ('2025-11-01') TO ('2025-12-01');

-- Enforce immutability
REVOKE DELETE, UPDATE ON audit_logs FROM PUBLIC;
GRANT INSERT, SELECT ON audit_logs TO app_user;
```

**Integrity Verification Function**:
```sql
CREATE FUNCTION verify_audit_chain() RETURNS BOOLEAN AS $$
DECLARE broken_link RECORD;
BEGIN
  SELECT * INTO broken_link FROM audit_logs a1
  LEFT JOIN audit_logs a2 ON a1.previous_hash = a2.current_hash
  WHERE a1.id > 1 AND a2.id IS NULL LIMIT 1;
  RETURN NOT FOUND;
END;
$$ LANGUAGE plpgsql;
```

## 5. Authentication & Authorization

### Decision: JWT-based authentication with middleware RBAC enforcement

### Rationale:
- **External Authentication**: Per spec assumption #1, JWT tokens issued by external IdP
- **Stateless**: No session storage bottleneck, supports 100+ concurrent users efficiently
- **Middleware Security**: Constitutional requirement for middleware-based enforcement
- **RBAC Integration**: JWT claims include role and classification clearance

### JWT Structure:
```json
{
  "sub": "user_id",
  "email": "user@example.com",
  "role": "Editor",
  "classification_clearance": 2,
  "iat": 1700000000,
  "exp": 1700003600
}
```

### Alternatives Considered:
- **Session-based**: Requires session store, contradicts external authentication assumption
- **API Keys**: No user context, difficult role management, poor audit trail
- **OAuth2 introspection**: Network call on every request impacts <2s search requirement

### Implementation Notes:
```python
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer
from jose import jwt, JWTError

security = HTTPBearer()

async def verify_token(credentials = Depends(security)):
    try:
        payload = jwt.decode(
            credentials.credentials,
            SECRET_KEY,
            algorithms=["RS256"]  # Verify with IdP public key
        )
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

def require_role(required_role: str):
    def role_checker(token_payload: dict = Depends(verify_token)):
        user_role = token_payload.get("role")
        if not has_role_access(user_role, required_role):
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return token_payload
    return role_checker

# Role hierarchy
ROLE_HIERARCHY = {
    "Admin": 4,
    "Manager": 3,
    "Editor": 2,
    "Viewer": 1,
    "Auditor": 0  # Special role
}
```

## 6. Encryption Strategy

### Decision: Application-level encryption with pgcrypto + Environment-based key management (dev) → HashiCorp Vault (production)

### Rationale:
- **Granular Control**: Separate encryption keys per classification level (Public, Internal, Confidential, Restricted)
- **Key Rotation**: Zero-downtime rotation with versioned keys
- **Defense in Depth**: Protects against database compromise
- **ISO 27001 Control A.10**: Proper cryptographic key management

### Key Hierarchy:
```
Master Encryption Key (MEK)
  ├─ Level 0 (Public - no encryption)
  ├─ Level 1 Key (Internal)
  ├─ Level 2 Key (Confidential)
  └─ Level 3 Key (Restricted)
```

### Alternatives Considered:
- **Database TDE**: Coarse-grained, doesn't prevent insider threats
- **File System Encryption**: Too coarse for classification-based requirements

### Implementation Notes:
```python
def encrypt_document(content: str, classification: int, conn) -> str:
    key = get_encryption_key(classification)
    if key is None:  # Public documents not encrypted
        return content
    result = conn.execute(
        text("SELECT pgp_sym_encrypt(:content, :key, 'cipher-algo=aes256')"),
        {"content": content, "key": key}
    )
    return result.scalar()

def get_encryption_key(classification: int) -> str:
    key_map = {
        0: None,  # Public
        1: os.getenv("ENCRYPTION_KEY_LEVEL_1"),
        2: os.getenv("ENCRYPTION_KEY_LEVEL_2"),
        3: os.getenv("ENCRYPTION_KEY_LEVEL_3")
    }
    return key_map[classification]
```

**Key Rotation (90-day schedule)**:
1. Generate new key (v2)
2. Deploy with both keys (v1, v2)
3. Background job: decrypt with v1, re-encrypt with v2
4. Mark documents with key version
5. Retire v1 after migration

**Phase 2**: Migrate to **HashiCorp Vault** for automated rotation, HSM-backed storage, and audit logging.

## 7. Testing Framework

### Decision: Pytest with security testing plugins

### Test Components:
- **Unit Testing**: Pytest core
- **Integration Testing**: `pytest-asyncio` for FastAPI
- **Security Testing**: Bandit (static analysis), Safety (dependency scanning), Pynt (API security)
- **Coverage**: `pytest-cov` (minimum 80%)

### Rationale:
- **Comprehensive**: Single framework for all test types
- **Security Integration**: Native support for Bandit, Safety, OWASP testing
- **ISO 27001 Evidence**: Test results serve as Control A.14 compliance artifacts
- **CI/CD**: Native GitHub Actions, Jenkins, GitLab CI integration

### Alternatives Considered:
- **unittest**: Less powerful fixture system, weaker security plugin ecosystem
- **Behave**: Better for BDD but less suited for security testing

### Implementation Notes:
```python
# tests/security/test_authentication.py
import pytest

@pytest.mark.security
async def test_authentication_required(client):
    response = await client.get("/documents")
    assert response.status_code == 401

@pytest.mark.security
async def test_authorization_enforcement(authenticated_client):
    # Viewer attempting Editor action
    response = await authenticated_client.post("/documents", json={"title": "Test"})
    assert response.status_code == 403

@pytest.mark.security
async def test_audit_logging(client, db_session):
    await client.post("/documents", headers={"Authorization": "Bearer <token>"})
    audit_log = db_session.query(AuditLog).filter_by(action="CREATE_DOCUMENT").first()
    assert audit_log is not None
```

**CI/CD Integration**:
```yaml
# .github/workflows/security.yml
- name: Run security tests
  run: pytest tests/security -m security
- name: Static analysis
  run: bandit -r src/ -f json
- name: Dependency scanning
  run: safety check --json
```

## 8. Deployment Target

### Decision: Docker + Docker Compose (Phase 1) with Kubernetes migration path

### Rationale:
- **Environment Consistency**: Identical dev/prod (ISO 27001 Control A.12)
- **Simplified Deployment**: Single-command deployment for initial scale
- **Container Security**: Image scanning, isolation, vulnerability detection
- **TLS Termination**: Caddy reverse proxy (automatic HTTPS, TLS 1.3)
- **Migration Path**: Clear upgrade to Kubernetes at 500+ concurrent users

### Alternatives Considered:
- **Kubernetes (immediate)**: Operational complexity not justified for 100 users
- **Traditional server**: Environment drift violates Control A.12
- **Cloud PaaS**: Vendor lock-in, less control over security

### Deployment Architecture:

**Phase 1: Docker Compose (0-100 users)**
```yaml
version: '3.8'
services:
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: qms
      POSTGRES_USER: qms_user
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    command: ["postgres", "-c", "data_checksums=on"]

  api:
    build: .
    environment:
      DATABASE_URL: postgresql://qms_user:${DB_PASSWORD}@postgres:5432/qms
      ENCRYPTION_KEY_LEVEL_1: ${ENCRYPTION_KEY_LEVEL_1}
      ENCRYPTION_KEY_LEVEL_2: ${ENCRYPTION_KEY_LEVEL_2}
      ENCRYPTION_KEY_LEVEL_3: ${ENCRYPTION_KEY_LEVEL_3}
      JWT_PUBLIC_KEY: ${JWT_PUBLIC_KEY}

  caddy:
    image: caddy:2-alpine
    ports:
      - "443:443"
      - "80:80"
    volumes:
      - ./Caddyfile:/etc/caddy/Caddyfile
```

**Caddyfile (TLS 1.3)**:
```
qms.example.com {
    reverse_proxy api:8000
    tls {
        protocols tls1.3
    }
    header {
        Strict-Transport-Security "max-age=31536000"
        X-Content-Type-Options "nosniff"
        X-Frame-Options "DENY"
    }
}
```

**Phase 2: Kubernetes** (500+ users)
- Auto-scaling based on load
- Pod security policies
- Network policies for isolation
- RBAC for cluster resources
- Secrets management
- Service mesh (Istio) for advanced security

### Security Best Practices:
- Run containers as non-root user
- Scan images with Docker Scout
- Use official base images
- Pin dependency versions
- Enable Docker Content Trust
- Limit container resources

## Technology Stack Summary

| Component | Technology | Version | Justification |
|-----------|-----------|---------|---------------|
| **Backend** | Python + FastAPI | 3.11+ / 0.115+ | Security ecosystem, async performance, middleware security |
| **Database** | PostgreSQL | 16+ | AES-256 encryption, ACID, full-text search |
| **Search** | PostgreSQL FTS | Built-in | Sufficient for 10k docs, permission integration |
| **Audit Storage** | PostgreSQL append-only | Built-in | Immutable with checksums, simplified architecture |
| **Authentication** | JWT middleware | python-jose | Stateless, external IdP, RBAC-friendly |
| **Encryption** | pgcrypto + app-level | AES-256-GCM | Granular control, classification-based keys |
| **Key Management** | Env vars → Vault | HashiCorp Vault | Simple dev, enterprise production |
| **Testing** | Pytest + Bandit | Latest | Comprehensive security testing |
| **Deployment** | Docker Compose → K8s | Docker 24+ | Environment consistency, container security |
| **Reverse Proxy** | Caddy | 2.7+ | Automatic TLS 1.3, certificate management |

## Implementation Effort Estimate

**MVP Development**: 12-16 weeks
- Backend API: 4-5 weeks
- Database schema & encryption: 2-3 weeks
- Authentication & RBAC: 2 weeks
- Audit logging: 1-2 weeks
- Testing & security validation: 3-4 weeks

**Operational Complexity**: Low
- Single database technology
- Containerized deployment
- Automated certificate management
- Native PostgreSQL backup tools

**Security Posture**: Strong
- AES-256 encryption at rest, TLS 1.3 in transit
- Immutable audit trails with integrity verification
- Classification-based access control at multiple layers
- Comprehensive security testing in CI/CD

## Phase 2 Enhancement Roadmap

Migration triggers for advanced technologies:

1. **Meilisearch**: Document count > 50,000 OR search P95 > 1.5s
2. **HashiCorp Vault**: Production deployment with automated key rotation
3. **immudb Vault**: Cryptographic audit verification compliance requirement
4. **Kubernetes**: Concurrent users > 500 OR multi-region requirement
5. **Redis**: Performance bottlenecks in session caching or rate limiting

This stack provides optimal balance of security, compliance, performance, and maintainability for ISO 27001 document management at initial scale.
