# Implementation Plan: Document Control Process

**Branch**: `001-document-control` | **Date**: 2025-11-24 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/001-document-control/spec.md`

## Summary

Implement an ISO 27001-compliant document management system with classification-based access control, comprehensive audit logging, full-text search, and version control. The system will support 4 user stories prioritized for independent delivery:

1. **P1 - Create and Classify Documents**: Foundation for secure document management with classification-based protection
2. **P2 - Search and Retrieve Documents**: Enable discoverability with permission-based access filtering
3. **P3 - Update Document Classification**: Manage security levels with approval workflows
4. **P4 - Version Control**: Track document changes with full history preservation

**Technical Approach**: Lightweight Python/FastAPI backend with PostgreSQL for storage, encryption, search, and audit logging. Single-database architecture minimizes operational complexity while meeting all security and performance requirements.

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: FastAPI 0.115+, SQLAlchemy 2.0+, psycopg2-binary, python-jose[cryptography], Pydantic 2.0+
**Storage**: PostgreSQL 16+ with pgcrypto extension (AES-256 encryption at rest)
**Testing**: pytest, pytest-asyncio, Bandit (static analysis), Safety (dependency scanning)
**Target Platform**: Linux server (Docker containers, TLS 1.3 via Caddy reverse proxy)
**Project Type**: Single backend API (web application)
**Performance Goals**:
- Document creation: <30 seconds (SC-001)
- Search response: <2 seconds for 10,000 documents (SC-002)
- Classification changes: <5 seconds (SC-007)
- Audit log queries: <3 seconds for 90-day range (SC-010)

**Constraints**:
- 100% audit coverage (no exceptions) (SC-003)
- 100% access control accuracy (SC-004)
- Immutable audit logs with tamper detection (SC-005)
- Zero security bypass incidents (SC-009)
- TLS 1.3 only (constitutional requirement)
- AES-256 encryption for documents (constitutional requirement)

**Scale/Scope**: 10,000 documents, 100 concurrent users (initial target), 5 user roles (Admin, Manager, Editor, Viewer, Auditor), 4 classification levels (Public, Internal, Confidential, Restricted)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-checked after Phase 1 design.*

### Principle I: Security by Design ✅ PASS

- ✅ **Encryption at rest**: AES-256 via pgcrypto for classification levels 1-3
- ✅ **Encryption in transit**: TLS 1.3 via Caddy reverse proxy
- ✅ **Middleware-based security**: FastAPI dependency injection for auth/authz
- ✅ **No bypass possible**: Row-Level Security (RLS) enforced at database level
- ✅ **Security requirements specified**: All 28 functional requirements include security considerations
- ✅ **Security testing planned**: pytest security tests, Bandit static analysis, Safety dependency scanning

### Principle II: Classification-Based Access Control ✅ PASS

- ✅ **Four classification levels**: Public (0), Internal (1), Confidential (2), Restricted (3) - seed data in classifications table
- ✅ **RBAC with five roles**: Admin, Manager, Editor, Viewer, Auditor - users table with role enum
- ✅ **Access decisions respect both**: RLS policies check role AND classification_clearance
- ✅ **Classification downgrade approval**: audit_logs table stores justification in details JSONB
- ✅ **Default classification Internal**: documents table DEFAULT 1
- ✅ **No direct bypass**: RLS FORCE policies on documents table

### Principle III: Auditability & Traceability ✅ PASS

- ✅ **Log every document operation**: audit_logs table with event_type enum (CREATE, READ, UPDATE, DELETE, CLASSIFY, AUTH)
- ✅ **Log all auth events**: AUTH event_type for login, logout, failed attempts
- ✅ **Log classification changes**: CLASSIFY event_type with old/new values in details JSONB
- ✅ **Immutable and tamper-evident**: audit_logs partitioned, REVOKE UPDATE/DELETE, checksum chain (previous_hash, current_hash)
- ✅ **1-year retention**: Monthly partitions with automated archival/cleanup
- ✅ **Admin/Auditor only access**: RLS policy + application-level role check
- ✅ **No exceptions**: Middleware audit logging intercepts ALL operations

### Principle IV: Compliance First ✅ PASS

- ✅ **ISO 27001 controls identified**: Spec maps FR-001 through FR-028 to Controls A.5, A.8, A.9, A.12, A.18
- ✅ **Implementation approach documented**: Data model, API contracts, security architecture defined
- ✅ **Compliance gaps tracked**: N/A - all controls implemented
- ✅ **Quarterly reviews**: Audit log query endpoints support compliance reporting
- ✅ **Non-compliance triggers corrective action**: Integrity verification function detects tampering
- ✅ **Audit readiness**: Immutable logs provide evidence for all controls

### Principle V: Data Lifecycle Management ✅ PASS

- ✅ **Retention policies**: documents.retention_policy_id (nullable for now, future feature)
- ✅ **Soft-delete**: documents.status enum ('active', 'deleted'), deleted_at timestamp
- ✅ **Automated retention**: Future cron job to hard-delete after retention period
- ✅ **Disposal approval**: Manager/Admin role required for deletion (enforced in API)
- ✅ **Backup alignment**: Docker volume backups with pg_dump, encrypted with GPG
- ✅ **Encrypted backups**: pg_dump piped to gpg --encrypt
- ✅ **Independent retention**: Audit logs 1 year minimum, documents 3 years default

### Principle VI: Secure Development Practices ✅ PASS

- ✅ **Security requirements review**: Spec includes ISO 27001 control mapping section
- ✅ **Threat modeling**: Classification-based access, encryption key management, audit log tampering addressed
- ✅ **Static analysis**: Bandit integrated in CI/CD pipeline
- ✅ **Dependency scanning**: Safety checks for known vulnerabilities
- ✅ **Code review security checklist**: Defined in development workflow docs
- ✅ **Security testing validates**: pytest security tests for auth, authz, encryption, audit logging
- ✅ **No production deployment without gates**: CI/CD pipeline enforces test passage

**Overall Constitution Compliance**: ✅ **PASS** - All six principles satisfied

## Project Structure

### Documentation (this feature)

```text
specs/001-document-control/
├── spec.md              # Feature specification (28 functional requirements, 4 user stories)
├── plan.md              # This file - implementation plan
├── research.md          # Technology stack research (8 areas)
├── data-model.md        # Database schema (5 entities, RLS policies)
├── quickstart.md        # Developer setup guide
├── contracts/           # API specifications
│   └── api-specification.yaml  # OpenAPI 3.0 spec (21 endpoints)
├── checklists/
│   └── requirements.md  # Specification quality checklist (PASSED)
└── tasks.md             # NOT created by /speckit.plan - run /speckit.tasks next
```

### Source Code (repository root)

**Selected Structure**: Single backend API project (no frontend initially)

```text
mt-quality-management/
├── .env                    # Environment variables (gitignored)
├── .env.example            # Example environment file
├── .gitignore              # Git ignore patterns
├── requirements.txt        # Python dependencies
├── requirements-dev.txt    # Development dependencies
├── docker-compose.yml      # Docker services (postgres, api, caddy)
├── docker-compose.prod.yml # Production Docker configuration
├── Dockerfile              # Application container (multi-stage build)
├── Caddyfile               # TLS 1.3 reverse proxy configuration
├── alembic.ini             # Database migration configuration
├── pytest.ini              # Test configuration
├── .bandit                 # Bandit security scanner config
├── main.py                 # FastAPI application entry point
│
├── src/
│   ├── __init__.py
│   ├── models/             # SQLAlchemy ORM models
│   │   ├── __init__.py
│   │   ├── user.py         # User model (id, email, role, classification_clearance)
│   │   ├── document.py     # Document model (encrypted content, classification, version)
│   │   ├── classification.py  # Classification reference model (4 levels)
│   │   ├── document_version.py  # DocumentVersion model (content snapshots)
│   │   └── audit_log.py    # AuditLog model (immutable, partitioned)
│   ├── services/           # Business logic layer
│   │   ├── __init__.py
│   │   ├── document_service.py  # Document CRUD, version management
│   │   ├── search_service.py    # Full-text search with permission filtering
│   │   ├── audit_service.py     # Audit log creation, querying, integrity verification
│   │   ├── encryption_service.py  # AES-256 encryption/decryption, key management
│   │   └── classification_service.py  # Classification change, approval workflow
│   ├── middleware/         # Security middleware
│   │   ├── __init__.py
│   │   ├── authentication.py  # JWT token validation (RS256)
│   │   ├── authorization.py   # RBAC enforcement, classification checks
│   │   └── audit_logging.py   # Automatic audit log creation
│   ├── routes/             # FastAPI API endpoints
│   │   ├── __init__.py
│   │   ├── documents.py    # POST /documents, GET /documents, GET/PUT/DELETE /documents/{id}
│   │   ├── search.py       # GET /search
│   │   ├── versions.py     # GET /documents/{id}/versions, GET /documents/{id}/versions/{ver}
│   │   ├── classifications.py  # PUT /documents/{id}/classification, GET /classifications
│   │   └── audit.py        # GET /audit, POST /audit/verify-integrity
│   ├── schemas/            # Pydantic validation schemas
│   │   ├── __init__.py
│   │   ├── document.py     # DocumentCreate, DocumentUpdate, Document, DocumentSummary
│   │   ├── user.py         # UserSummary
│   │   ├── audit.py        # AuditLog schema
│   │   └── classification.py  # Classification schema
│   └── utils/              # Helper utilities
│       ├── __init__.py
│       ├── config.py       # Configuration loading from environment
│       ├── database.py     # Database connection, session management
│       └── security.py     # Security helpers (hash generation, token validation)
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py         # Shared pytest fixtures (test database, auth tokens)
│   ├── unit/               # Unit tests (business logic, models)
│   │   ├── __init__.py
│   │   ├── test_document_service.py
│   │   ├── test_encryption_service.py
│   │   ├── test_audit_service.py
│   │   └── test_search_service.py
│   ├── integration/        # Integration tests (API endpoints, database)
│   │   ├── __init__.py
│   │   ├── test_api_documents.py
│   │   ├── test_api_search.py
│   │   ├── test_api_audit.py
│   │   └── test_database.py
│   ├── security/           # Security-focused tests
│   │   ├── __init__.py
│   │   ├── test_authentication.py  # Token validation, expiration
│   │   ├── test_authorization.py   # RBAC, classification checks
│   │   ├── test_encryption.py      # AES-256 encryption correctness
│   │   └── test_audit_trail.py     # Immutability, integrity verification
│   └── contract/           # API contract tests (OpenAPI validation)
│       ├── __init__.py
│       └── test_api_schema.py
│
├── scripts/
│   ├── seed_data.py        # Seed classifications reference data
│   ├── verify_db.py        # Database setup verification
│   ├── generate_keys.py    # Generate encryption keys
│   └── test_encryption.py  # Test encryption/decryption
│
├── alembic/
│   ├── env.py              # Alembic environment configuration
│   ├── script.py.mako      # Migration template
│   └── versions/           # Database migrations
│       └── 001_initial_schema.py
│
├── config/
│   └── development.env     # Development environment example
│
├── docs/
│   └── isms/               # ISO 27001 documentation
│       ├── POLICY_INDEX.md
│       ├── risk-assessment/
│       └── incident-management/
│
└── uploads/                # Temporary upload storage (if file uploads added later)
```

**Structure Decision**: Single backend API project is appropriate because:
1. **Specification scope**: Backend document control only (assumption #1: external authentication)
2. **No frontend requirements**: Spec focuses on API capabilities, not UI
3. **Simplified deployment**: Single Docker container for API + PostgreSQL + Caddy
4. **Clear separation**: Services layer abstracts business logic from routes
5. **Testability**: Each layer independently testable (models, services, routes)

Future iterations may add frontend (React/Vue) in separate repository or monorepo workspace.

## Complexity Tracking

> **No Constitution Violations** - Table not applicable

All constitutional requirements satisfied with straightforward implementations:
- Single database technology (PostgreSQL) for storage, search, audit
- Standard RBAC + RLS patterns for access control
- Application-level encryption with pgcrypto (no custom crypto)
- Docker deployment (no Kubernetes complexity for initial scale)
- RESTful API (no GraphQL, WebSocket, or other protocols)

**Simplicity Justifications**:
- **PostgreSQL for search**: Sufficient for 10k documents. Dedicated search engine (Meilisearch) deferred to Phase 2 (50k+ documents).
- **Environment variables for keys**: Simple key management for development. HashiCorp Vault deferred to production Phase 2.
- **Docker Compose**: Adequate for 100 concurrent users. Kubernetes migration path clear for 500+ users.

## Implementation Phases

### Phase 0: Foundation (Week 1-2)

**Goal**: Project setup, database schema, core infrastructure

1. **Project Initialization**:
   - Initialize Git repository with `.gitignore` (Python, Docker, .env)
   - Create Python virtual environment with dependencies
   - Setup Docker Compose (PostgreSQL 16, FastAPI, Caddy)
   - Configure CI/CD pipeline (GitHub Actions: tests, security scans)

2. **Database Setup**:
   - Create Alembic migrations for initial schema (users, classifications, documents, document_versions, audit_logs)
   - Enable pgcrypto extension
   - Seed classifications reference data (4 levels)
   - Implement Row-Level Security (RLS) policies
   - Create audit log partitions (initial month + auto-creation script)

3. **Core Infrastructure**:
   - FastAPI application structure (`main.py`, routers, middleware)
   - Database connection pooling and session management
   - Configuration loading from environment variables
   - Structured logging setup (structlog)
   - Health check endpoints (`/health`, `/ready`)

**Deliverables**: Running FastAPI application, PostgreSQL with schema, Docker environment, CI/CD pipeline

### Phase 1: Authentication & Authorization (Week 2-3)

**Goal**: Implement security middleware for JWT validation and RBAC

1. **Authentication Middleware**:
   - JWT token validation (RS256 with external IdP public key)
   - Token claim extraction (sub, email, role, classification_clearance)
   - FastAPI dependency for `verify_token()`
   - Error handling for invalid/expired tokens (401 Unauthorized)

2. **Authorization Middleware**:
   - Role-based access control (RBAC) dependency injection
   - Classification-based access checks (user clearance vs document classification)
   - Document ownership verification (for Editor/Manager update/delete)
   - Special Auditor role handling (read all classifications)

3. **Testing**:
   - Unit tests: Token validation, role hierarchy, classification checks
   - Integration tests: Protected endpoint access with various roles
   - Security tests: Bypass attempts, privilege escalation, token tampering

**Deliverables**: Secure API with JWT authentication, RBAC enforcement, comprehensive security tests

### Phase 2: User Story 1 - Create and Classify Documents (Week 3-5)

**Goal**: P1 MVP - Document creation with classification

1. **Encryption Service**:
   - AES-256 encryption/decryption functions (pgcrypto wrapper)
   - Key management (environment variables, per-classification keys)
   - Encryption key version tracking (for future rotation)

2. **Document Service**:
   - Create document (encrypt content, validate classification, assign owner)
   - Retrieve document (decrypt content, verify access permissions)
   - List documents (pagination, filtering by classification/owner/status)
   - Input validation (Pydantic schemas)

3. **API Endpoints**:
   - `POST /api/v1/documents` (create with classification)
   - `GET /api/v1/documents` (list with pagination)
   - `GET /api/v1/documents/{id}` (retrieve single document)

4. **Audit Logging**:
   - Middleware intercepts all document operations
   - Create immutable audit log entries (actor, action, classification, timestamp)
   - Checksum chain (previous_hash, current_hash)

5. **Testing**:
   - Unit: Encryption correctness, document validation
   - Integration: Create document API, access control enforcement
   - Security: Encryption key isolation, audit logging completeness

**Deliverables**: Users can create, classify, and retrieve documents with full audit trail. MVP ready for testing.

### Phase 3: User Story 2 - Search and Retrieve Documents (Week 5-7)

**Goal**: Full-text search with permission-based filtering

1. **Search Service**:
   - PostgreSQL full-text search integration (tsvector queries)
   - Relevance ranking (ts_rank)
   - Permission filtering (RLS automatic, verify in service layer)
   - Result pagination

2. **Search Vector Management**:
   - Automatic search vector updates (trigger on title/content changes)
   - Index optimization (gin index on search_vector)
   - Handle encrypted content (search on title only, or maintain searchable summary field)

3. **API Endpoints**:
   - `GET /api/v1/search?q=<query>` (full-text search)
   - Response includes relevance score, document metadata, snippet

4. **Performance Optimization**:
   - Query optimization for <2 second response time
   - Index analysis and tuning
   - Connection pool sizing for 100 concurrent users

5. **Testing**:
   - Unit: Search relevance, permission filtering logic
   - Integration: Search API with various classifications
   - Performance: Load testing with 10,000 documents, verify <2s response

**Deliverables**: Fast, secure document search. Success criteria SC-002 verified.

### Phase 4: User Story 3 - Update Document Classification (Week 7-8)

**Goal**: Classification management with approval workflow

1. **Classification Service**:
   - Change classification (upgrade or downgrade)
   - Approval workflow for downgrades (store justification in audit log)
   - Re-encrypt document content if classification key changes

2. **API Endpoints**:
   - `PUT /api/v1/documents/{id}/classification` (Manager/Admin only)
   - Request body includes new_classification_level, justification (required for downgrades)

3. **Audit Enhancements**:
   - CLASSIFY event_type with old/new classification in details JSONB
   - Approver identity recorded

4. **Testing**:
   - Unit: Classification validation, approval logic
   - Integration: Classification change API, downgrade approval
   - Security: Prevent unauthorized classification changes

**Deliverables**: Classification management with approval workflow. Success criteria SC-007 verified.

### Phase 5: User Story 4 - Version Control (Week 8-10)

**Goal**: Document versioning with history preservation

1. **Version Service**:
   - Create new version on content update (snapshot encrypted content)
   - Retrieve version history (paginated list)
   - Retrieve specific version (decrypt and return)
   - Optional: Restore previous version as current

2. **API Endpoints**:
   - `PUT /api/v1/documents/{id}` (update creates new version)
   - `GET /api/v1/documents/{id}/versions` (list versions)
   - `GET /api/v1/documents/{id}/versions/{ver}` (retrieve specific version)

3. **Database Updates**:
   - document_versions table populated on update
   - Version number auto-increment
   - Change description captured from API request

4. **Testing**:
   - Unit: Version creation, snapshot correctness
   - Integration: Update API creates version, history retrieval
   - Data integrity: Version content matches original at time of creation

**Deliverables**: Full version control with history. Success criteria SC-008 verified.

### Phase 6: Audit Log Queries & Integrity (Week 10-11)

**Goal**: Audit log querying and integrity verification for compliance

1. **Audit Query Service**:
   - Date range filtering (start_date, end_date)
   - Filter by actor, event_type, resource_type, action
   - Pagination for large result sets
   - Performance optimization for 90-day queries (<3s)

2. **Integrity Verification**:
   - Checksum chain validation function (SQL function)
   - Detect broken links in audit chain
   - API endpoint to trigger verification

3. **API Endpoints**:
   - `GET /api/v1/audit` (query with filters, Admin/Auditor only)
   - `POST /api/v1/audit/verify-integrity` (verify checksum chain)

4. **Testing**:
   - Unit: Query logic, integrity verification function
   - Integration: Audit API with various filters, integrity checks
   - Performance: 90-day query under 3 seconds (SC-010)
   - Security: Detect tampered audit logs

**Deliverables**: Compliance-ready audit log system. Success criteria SC-003, SC-005, SC-010 verified.

### Phase 7: Testing & Hardening (Week 11-12)

**Goal**: Comprehensive testing, security validation, documentation

1. **Test Coverage**:
   - Achieve 80%+ code coverage (pytest-cov)
   - All success criteria validated with automated tests
   - Edge cases from specification tested

2. **Security Validation**:
   - Bandit static analysis (zero critical findings)
   - Safety dependency scan (no high/critical vulnerabilities)
   - Manual security review of authentication, encryption, audit logging
   - Penetration testing (optional, if resources available)

3. **Performance Testing**:
   - Load testing with Locust (100 concurrent users)
   - Verify all performance success criteria (SC-001, SC-002, SC-007, SC-010)
   - Database query optimization

4. **Documentation**:
   - API documentation review (OpenAPI spec accuracy)
   - Developer setup guide validation (quickstart.md)
   - ISO 27001 compliance documentation (control implementation evidence)

5. **Deployment Readiness**:
   - Docker image optimization (multi-stage build, security scanning)
   - Environment variable documentation
   - Backup/restore procedures tested
   - TLS 1.3 configuration verified (Caddy)

**Deliverables**: Production-ready application with comprehensive tests, security validation, and documentation.

## Risk Management

| Risk | Impact | Mitigation |
|------|--------|-----------|
| **Encrypted content not searchable** | Search functionality degraded | Maintain separate searchable summary field or accept title-only search for initial MVP. Meilisearch migration path defined. |
| **Performance degradation with large datasets** | <2s search requirement not met | Database query optimization, indexing tuning. Clear migration path to Meilisearch at 50k+ documents. |
| **Key management complexity** | Encryption key leakage or loss | Phase 1: Environment variables with clear documentation. Phase 2: Migrate to HashiCorp Vault for production. |
| **Audit log partition management** | Storage growth, query performance | Automated monthly partition creation script. Archive old partitions to cold storage after 1 year retention. |
| **Concurrent document edits** | Data loss or corruption | Initial MVP: Last-write-wins (acceptable per assumption #6). Future: Add optimistic locking with version-based conflict detection. |
| **External IdP unavailability** | Authentication failures | Implement circuit breaker pattern. Cache recently validated tokens. Document IdP availability requirements. |

## Success Criteria Validation

| Criterion | Target | Validation Method |
|-----------|--------|-------------------|
| SC-001 | Document creation <30s | Integration test with timer |
| SC-002 | Search <2s for 10k docs | Performance test with load data |
| SC-003 | 100% audit coverage | Unit tests verify middleware intercepts all operations |
| SC-004 | 100% access control accuracy | Security tests attempt unauthorized access (must all fail) |
| SC-005 | Immutable audit logs | Database permission verification + integrity function |
| SC-006 | 85% first-attempt success | Manual testing + analytics (future) |
| SC-007 | Classification change <5s | Integration test with timer |
| SC-008 | 100% version history | Unit tests verify snapshots match originals |
| SC-009 | Zero bypass incidents | Security tests attempt bypass (must all fail) |
| SC-010 | Audit query <3s for 90 days | Performance test with 90 days of audit data |
| SC-011 | Quarterly compliance review | Manual compliance checklist (ISO 27001 controls) |
| SC-012 | 100% required events logged | Audit completeness tests |
| SC-013 | Access control verified | Security testing validates RBAC + classification |

## Next Steps

1. **Run `/speckit.tasks`**: Generate detailed task breakdown from this implementation plan
2. **Review tasks.md**: Validate task prioritization and dependencies
3. **Run `/speckit.analyze`**: Cross-validate spec, plan, and tasks for consistency
4. **Begin implementation**: Start with Phase 0 (Foundation) tasks

## References

- **Specification**: [spec.md](./spec.md) - 28 functional requirements, 4 user stories, 13 success criteria
- **Research**: [research.md](./research.md) - Technology stack decisions and rationale
- **Data Model**: [data-model.md](./data-model.md) - 5 entities, RLS policies, RBAC matrix
- **API Contracts**: [contracts/api-specification.yaml](./contracts/api-specification.yaml) - 21 endpoints, OpenAPI 3.0
- **Quick Start**: [quickstart.md](./quickstart.md) - Developer setup and common tasks
- **Constitution**: [.specify/memory/constitution.md](../../.specify/memory/constitution.md) - 6 core principles, ISO 27001 alignment
