# Tasks: Document Control Process

**Input**: Design documents from `specs/001-document-control/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root
- Paths shown below assume single project structure from plan.md

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create project structure with directories: src/, tests/, scripts/, alembic/, config/, docs/isms/
- [ ] T002 Initialize Python virtual environment and install dependencies from requirements.txt
- [ ] T003 [P] Create .gitignore file for Python, Docker, .env, and IDE files
- [ ] T004 [P] Create .env.example with all required environment variables (DATABASE_URL, ENCRYPTION_KEY_LEVEL_*, JWT_PUBLIC_KEY)
- [ ] T005 [P] Create requirements.txt with FastAPI, SQLAlchemy, psycopg2-binary, python-jose, Pydantic, structlog
- [ ] T006 [P] Create requirements-dev.txt with pytest, pytest-asyncio, bandit, safety, pytest-cov
- [ ] T007 Create docker-compose.yml with PostgreSQL 16, FastAPI API, and Caddy services
- [ ] T008 [P] Create Dockerfile with multi-stage build (builder + runtime with non-root user)
- [ ] T009 [P] Create Caddyfile for TLS 1.3 reverse proxy configuration
- [ ] T010 [P] Create pytest.ini with test paths and coverage configuration
- [ ] T011 [P] Create .bandit configuration file for security scanning exclusions

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T012 Create src/__init__.py to mark source directory as Python package
- [ ] T013 Create src/utils/config.py to load configuration from environment variables (DATABASE_URL, ENCRYPTION_KEY_LEVEL_1/2/3, JWT_PUBLIC_KEY per .env.example)
- [ ] T014 Create src/utils/database.py with SQLAlchemy engine, session maker, and Base class
- [ ] T015 Create src/utils/security.py with hash generation and token validation helpers
- [ ] T016 Create main.py with FastAPI application initialization and health check endpoints (/health, /ready)
- [ ] T017 Create alembic.ini configuration file for database migrations
- [ ] T018 Create alembic/env.py with SQLAlchemy Base import and migration settings
- [ ] T019 Create initial database migration script (001_initial_schema.py) with all table definitions
- [ ] T020 Enable pgcrypto extension in PostgreSQL via migration script
- [ ] T021 Create scripts/seed_data.py to populate classifications table (4 levels: Public, Internal, Confidential, Restricted)
- [ ] T022 [P] Create scripts/generate_keys.py to generate AES-256 encryption keys
- [ ] T023 [P] Create scripts/verify_db.py to verify database connection and schema
- [ ] T024 [P] Create tests/__init__.py and tests/conftest.py with shared fixtures (test database, auth tokens)
- [ ] T025 Run Alembic migrations to create database schema
- [ ] T026 Run seed_data.py script to populate classifications reference data
- [ ] T027 Create src/middleware/__init__.py for middleware package
- [ ] T028 Create src/middleware/authentication.py with JWT token validation (RS256) and verify_token dependency
- [ ] T029 Create src/middleware/authorization.py with RBAC role checker and classification clearance validation (Note: User role changes handled by external user management system per spec assumption #2)
- [ ] T030 Create src/middleware/audit_logging.py with middleware to intercept all requests and create audit log entries
- [ ] T031 Integrate authentication, authorization, and audit logging middleware into main.py FastAPI application
- [ ] T032 Create GitHub Actions CI/CD workflow file (.github/workflows/ci.yml) with pytest, bandit, and safety checks

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Create and Classify Documents (Priority: P1) 🎯 MVP

**Goal**: Enable document creation with security classification and full audit trail

**Independent Test**: Create a document with classification, verify it's stored encrypted with correct metadata, and audit log entry exists

### Implementation for User Story 1

- [ ] T033 [P] [US1] Create src/models/__init__.py for models package
- [ ] T034 [P] [US1] Create src/models/user.py with User SQLAlchemy model (id, email, role, classification_clearance, active, last_login)
- [ ] T035 [P] [US1] Create src/models/classification.py with Classification SQLAlchemy model (level_code, level_name, access_rules, handling_requirements)
- [ ] T036 [US1] Create src/models/document.py with Document SQLAlchemy model (id, title, content_encrypted, classification_level, version, owner_id, status, created_at, modified_at, search_vector, encryption_key_version)
- [ ] T037 [US1] Add Row-Level Security (RLS) policies to document.py model for classification-based access control (depends on T036 completion)
- [ ] T038 [US1] Add automatic timestamp triggers to document.py model (update modified_at on UPDATE)
- [ ] T039 [P] [US1] Create src/models/audit_log.py with AuditLog SQLAlchemy model (partitioned table with checksum chain: previous_hash, current_hash)
- [ ] T040 [P] [US1] Create src/services/__init__.py for services package
- [ ] T041 [US1] Create src/services/encryption_service.py with encrypt_document and decrypt_document functions using pgcrypto
- [ ] T042 [US1] Add get_encryption_key function to encryption_service.py (separate keys per classification level from environment)
- [ ] T043 [US1] Create src/services/audit_service.py with create_audit_log function (HMAC-SHA-256 checksum chain using external key, store previous_hash/current_hash)
- [ ] T044 [US1] Create src/services/document_service.py with create_document function (encrypt content, validate classification, assign owner, create audit log)
- [ ] T045 [US1] Add get_document function to document_service.py (decrypt content, verify access permissions via RLS)
- [ ] T046 [US1] Add list_documents function to document_service.py (pagination, filtering by classification/owner/status)
- [ ] T047 [P] [US1] Create src/schemas/__init__.py for schemas package
- [ ] T048 [P] [US1] Create src/schemas/document.py with Pydantic models: DocumentCreate, Document, DocumentSummary (Note: T064 and T087 will extend this file with SearchResult and DocumentVersion schemas)
- [ ] T049 [P] [US1] Create src/schemas/user.py with Pydantic model: UserSummary
- [ ] T050 [P] [US1] Create src/schemas/classification.py with Pydantic model: Classification
- [ ] T051 [P] [US1] Create src/routes/__init__.py for routes package
- [ ] T052 [US1] Create src/routes/documents.py with POST /api/v1/documents endpoint (create document with classification, validate file size limit per edge case requirement)
- [ ] T053 [US1] Add GET /api/v1/documents endpoint to documents.py (list documents with pagination and filters)
- [ ] T054 [US1] Add GET /api/v1/documents/{id} endpoint to documents.py (retrieve single document with decryption)
- [ ] T055 [US1] Create src/routes/classifications.py with GET /api/v1/classifications endpoint (list all classification levels)
- [ ] T056 [US1] Register documents and classifications routers in main.py FastAPI application

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Search and Retrieve Documents (Priority: P2)

**Goal**: Enable full-text search with permission-based filtering and fast retrieval

**Independent Test**: Search for documents by keywords, verify results respect user permissions, and retrieve document content

### Implementation for User Story 2

- [ ] T057 [US2] Create src/services/search_service.py with search_documents function using PostgreSQL full-text search (tsvector)
- [ ] T058 [US2] Add relevance ranking to search_service.py using PostgreSQL ts_rank function with weighted title (A) and content (B) vectors
- [ ] T059 [US2] Add permission filtering logic to search_service.py (verify RLS policies apply automatically)
- [ ] T060 [US2] Add pagination support to search_service.py (page, page_size parameters)
- [ ] T061 [US2] Update src/models/document.py to add search_vector tsvector column with gin index
- [ ] T062 [US2] Add trigger to document.py model to auto-update search_vector on title/content changes
- [ ] T063 [US2] Create database migration for search_vector column and trigger
- [ ] T064 [US2] Add SearchResult Pydantic model to src/schemas/document.py with snippet and relevance_score (extends file created in T048)
- [ ] T065 [US2] Create src/routes/search.py with GET /api/v1/search endpoint (query parameter q, pagination)
- [ ] T066 [US2] Add audit logging to search.py for all search operations (READ event type)
- [ ] T067 [US2] Register search router in main.py FastAPI application
- [ ] T068 [US2] Optimize PostgreSQL queries in search_service.py to meet <2 second response time requirement (SC-002)
- [ ] T069 [US2] Add connection pool configuration to database.py for 100 concurrent users

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Update Document Classification (Priority: P3)

**Goal**: Enable classification management with approval workflows for downgrades

**Independent Test**: Change document classification (upgrade and downgrade), verify approvals are required for downgrades, and changes are audited

### Implementation for User Story 3

- [ ] T070 [US3] Create src/services/classification_service.py with change_classification function
- [ ] T071 [US3] Add upgrade_classification function to classification_service.py (no approval required)
- [ ] T072 [US3] Add downgrade_classification function to classification_service.py (requires approval and justification)
- [ ] T073 [US3] Add re-encryption logic to classification_service.py if classification key changes
- [ ] T074 [US3] Update audit_service.py to handle CLASSIFY event type with old/new classification in details JSONB
- [ ] T075 [US3] Create src/schemas/document.py ClassificationChange Pydantic model (new_classification_level, justification)
- [ ] T076 [US3] Create src/routes/classifications.py PUT /api/v1/documents/{id}/classification endpoint (Manager/Admin only)
- [ ] T077 [US3] Add authorization check to classifications.py route (require Manager or Admin role)
- [ ] T078 [US3] Add approval workflow logic to classifications.py for downgrades (store justification in audit log)

**Checkpoint**: All three user stories (US1, US2, US3) should now be independently functional

---

## Phase 6: User Story 4 - Version Control for Documents (Priority: P4)

**Goal**: Enable document versioning with full history preservation and restoration

**Independent Test**: Update document content, verify new version created with history preserved, retrieve previous versions

### Implementation for User Story 4

- [ ] T079 [P] [US4] Create src/models/document_version.py with DocumentVersion SQLAlchemy model (document_id, version_number, content_snapshot, author_id, change_description, classification_at_version, encryption_key_version)
- [ ] T080 [US4] Add cascade delete relationship from Document to DocumentVersion in models
- [ ] T081 [US4] Create database migration for document_versions table
- [ ] T082 [US4] Create src/services/version_service.py with create_version function (snapshot encrypted content)
- [ ] T083 [US4] Add get_version_history function to version_service.py (paginated list of versions)
- [ ] T084 [US4] Add get_version function to version_service.py (retrieve specific version with decryption)
- [ ] T085 [US4] Add restore_version function to version_service.py (optional: restore previous version as current)
- [ ] T086 [US4] Update document_service.py update_document function to create new version on content change
- [ ] T087 [US4] Add DocumentVersion and DocumentUpdate Pydantic models to src/schemas/document.py (extends file created in T048)
- [ ] T088 [US4] Update src/routes/documents.py PUT /api/v1/documents/{id} endpoint to accept change_description
- [ ] T089 [US4] Create src/routes/versions.py with GET /api/v1/documents/{id}/versions endpoint (list versions)
- [ ] T090 [US4] Add GET /api/v1/documents/{id}/versions/{ver} endpoint to versions.py (retrieve specific version)
- [ ] T091 [US4] Register versions router in main.py FastAPI application
- [ ] T092 [US4] Update audit logging to record version numbers (old and new) for UPDATE events

**Checkpoint**: All user stories should now be independently functional with version control

---

## Phase 7: Audit Log Queries & Integrity (Cross-Cutting)

**Purpose**: Audit log querying and integrity verification for compliance

- [ ] T093 Add query_audit_logs function to audit_service.py with date range and filter parameters (actor, event_type, resource_type, action)
- [ ] T094 Add audit log partition management to audit_service.py (create monthly partitions; automated retention cleanup deferred to Phase 2 future enhancement)
- [ ] T095 Create PostgreSQL verify_audit_chain function in migration script (verify chain linkage; optionally recompute HMAC when app.audit_hmac_key is provided)
- [ ] T096 Add verify_integrity function to audit_service.py (wrapper for SQL function)
- [ ] T097 Create src/schemas/audit.py with AuditLog Pydantic model and query parameters
- [ ] T098 Create src/routes/audit.py with GET /api/v1/audit endpoint (date range filters, Admin/Auditor only)
- [ ] T099 Add POST /api/v1/audit/verify-integrity endpoint to audit.py (trigger integrity verification)
- [ ] T100 Add authorization check to audit.py routes (require Admin or Auditor role)
- [ ] T101 Register audit router in main.py FastAPI application
- [ ] T102 Optimize audit log queries in audit_service.py to meet <3 second requirement for 90-day range (SC-010)

---

## Phase 8: Testing & Hardening (Cross-Cutting)

**Purpose**: Comprehensive testing, security validation, documentation

- [ ] T103 [P] Create tests/unit/test_encryption_service.py (test AES-256 encryption/decryption correctness)
- [ ] T104 [P] Create tests/unit/test_document_service.py (test create, get, list, update document logic)
- [ ] T105 [P] Create tests/unit/test_audit_service.py (test audit log creation and checksum chain)
- [ ] T106 [P] Create tests/unit/test_search_service.py (test search logic and relevance ranking)
- [ ] T107 [P] Create tests/integration/test_api_documents.py (test document API endpoints end-to-end)
- [ ] T108 [P] Create tests/integration/test_api_search.py (test search API endpoint with various queries)
- [ ] T109 [P] Create tests/integration/test_api_audit.py (test audit log query and integrity verification APIs)
- [ ] T110 [P] Create tests/security/test_authentication.py (test JWT validation, token expiration, invalid tokens)
- [ ] T111 [P] Create tests/security/test_authorization.py (test RBAC enforcement, classification checks, role hierarchy)
- [ ] T112 [P] Create tests/security/test_encryption.py (test encryption key isolation, classification-based encryption)
- [ ] T113 [P] Create tests/security/test_audit_trail.py (test immutability, integrity verification, 100% coverage)
- [ ] T114 [P] Create tests/contract/test_api_schema.py (validate OpenAPI specification against actual endpoints)
- [ ] T115 Run pytest with coverage report (target: 80%+ coverage)
- [ ] T116 Run bandit security scanner and resolve all critical findings
- [ ] T117 Run safety dependency scanner and resolve high/critical vulnerabilities
- [ ] T118 Create performance tests with Locust for 100 concurrent users
- [ ] T119 Verify all success criteria (SC-001 through SC-013) with automated tests
- [ ] T120 Run quickstart.md validation (verify all setup steps work end-to-end)
- [ ] T121 Optimize Docker image (multi-stage build, minimize layers, security scan with Docker Scout)
- [ ] T122 Document encryption key rotation procedure in docs/isms/
- [ ] T123 Test backup/restore procedures (pg_dump with GPG encryption)
- [ ] T124 Verify TLS 1.3 configuration in Caddy (test with ssllabs.com or testssl.sh)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phases 3-6)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3 → P4)
- **Audit System (Phase 7)**: Can proceed in parallel with user stories (separate routes)
- **Testing & Hardening (Phase 8)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Requires documents to exist (create via US1 or seed data)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Requires documents to exist (create via US1 or seed data)
- **User Story 4 (P4)**: Can start after Foundational (Phase 2) - Requires document update functionality (integrates with US1)

### Within Each User Story

- Models before services (data structure first)
- Services before routes (business logic before API)
- Schemas can be created in parallel with models
- Routes depend on services being complete
- Audit logging integrated throughout (middleware handles automatically)

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- Models within a story marked [P] can run in parallel
- Schemas within a story marked [P] can run in parallel
- Testing tasks marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all models for User Story 1 together:
Task: "Create src/models/user.py with User model"
Task: "Create src/models/classification.py with Classification model"
Task: "Create src/models/audit_log.py with AuditLog model"

# These can all run in parallel because they create different files
# document.py runs after because it has FK relationships to user and classification
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001-T011)
2. Complete Phase 2: Foundational (T012-T032) - CRITICAL - blocks all stories
3. Complete Phase 3: User Story 1 (T033-T056)
4. **STOP and VALIDATE**: Test User Story 1 independently
   - Create documents with classification
   - Verify encryption at rest
   - Verify audit logging (100% coverage)
   - Verify access control (role and classification checks)
5. Deploy/demo if ready

**MVP Deliverables**: Secure document creation with classification, encryption, and full audit trail

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo (Search capability)
4. Add User Story 3 → Test independently → Deploy/Demo (Classification management)
5. Add User Story 4 → Test independently → Deploy/Demo (Version control)
6. Add Audit System (Phase 7) → Test independently → Deploy/Demo (Compliance queries)
7. Complete Testing & Hardening (Phase 8) → Production-ready
8. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (T033-T056)
   - Developer B: User Story 2 (T057-T069)
   - Developer C: User Story 3 (T070-T078)
   - Developer D: User Story 4 (T079-T092)
3. Stories complete and integrate independently
4. Shared middleware (auth, audit) handles cross-cutting concerns automatically

---

## Notes

- **[P] tasks** = different files, no dependencies, run in parallel
- **[Story] label** maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Middleware handles audit logging automatically (no per-story audit tasks needed)
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- **Avoid**: vague tasks, same file conflicts, cross-story dependencies that break independence

---

## Task Count Summary

- **Phase 1 (Setup)**: 11 tasks
- **Phase 2 (Foundational)**: 21 tasks (BLOCKING - must complete first)
- **Phase 3 (User Story 1 - P1 MVP)**: 24 tasks
- **Phase 4 (User Story 2 - P2)**: 13 tasks
- **Phase 5 (User Story 3 - P3)**: 9 tasks
- **Phase 6 (User Story 4 - P4)**: 14 tasks
- **Phase 7 (Audit System)**: 10 tasks
- **Phase 8 (Testing & Hardening)**: 22 tasks

**Total**: 124 tasks

**Parallel Opportunities**: 43 tasks marked [P] can run concurrently within their phase

**MVP Scope** (Minimum Viable Product): Phases 1-3 (56 tasks)
- Delivers User Story 1: Create and Classify Documents
- Full encryption, audit logging, and access control
- Independently testable and deployable

**Full Feature Scope**: All 124 tasks
- All 4 user stories independently functional
- Comprehensive testing and security validation
- Production-ready deployment
