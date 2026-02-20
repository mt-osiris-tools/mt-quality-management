# Detailed Analysis Tables - Document Control Process

## Complete Requirement-to-Task Traceability Matrix

### Document Lifecycle Requirements (FR-001 to FR-011)

| FR ID | Requirement | User Story | Task(s) | Phase | Acceptance Scenario | Test Type |
|---|---|---|---|---|---|---|
| FR-001 | Create documents (Editor/Manager role) | US1 | T044 | Phase 3 | "Given Editor, When create document, Then save with ID" | Integration |
| FR-002 | Default classification "Internal" | US1 | T044 | Phase 3 | "Given no classification specified, Then default to Internal" | Unit |
| FR-003 | Support 4 classification levels | US1 | T021, T055 | Phase 2, 3 | "Given 4 levels exist, Then can use all" | Integration |
| FR-004 | Manager can change classification | US3 | T076 | Phase 5 | "Given Manager role, When change classification, Then accept" | Integration |
| FR-005 | Downgrade requires approval + justification | US3 | T078 | Phase 5 | "Given downgrade attempt, When missing justification, Then reject" | Integration |
| FR-006 | Unique document ID assignment | US1 | T044 | Phase 3 | "Given create document, Then assign unique ID" | Unit |
| FR-007 | Record metadata (title, classification, version, owner, timestamps) | US1 | T036, T044 | Phase 2, 3 | "Given create document, Then metadata captured" | Integration |
| FR-008 | Allow content updates | US4 | T086 | Phase 6 | "Given document owner, When update content, Then save changes" | Integration |
| FR-009 | Maintain version history | US4 | T082 | Phase 6 | "Given update, When save, Then preserve old version" | Unit |
| FR-010 | View version history | US4 | T089 | Phase 6 | "Given document with versions, When view history, Then see all versions" | Integration |
| FR-011 | Support soft-delete | US1 | T036 | Phase 3 | "Given delete request, Then mark deleted, retain data" | Unit |

---

### Search and Retrieval Requirements (FR-012 to FR-016)

| FR ID | Requirement | User Story | Task(s) | Phase | Acceptance Scenario | Test Type |
|---|---|---|---|---|---|---|
| FR-012 | Full-text search across titles + content | US2 | T057 | Phase 4 | "Given search query, When search, Then return matching documents" | Integration |
| FR-013 | Filter results by role + classification permissions | US2 | T059 | Phase 4 | "Given Viewer with Internal clearance, When search, Then exclude Confidential/Restricted" | Security |
| FR-014 | Retrieve full document content | US1 | T054 | Phase 3 | "Given document ID, When retrieve, Then return full encrypted content" | Integration |
| FR-015 | Display metadata in search results | US2 | T054, T064 | Phase 3, 4 | "Given search results, Then include title, classification, version, owner, dates" | Integration |
| FR-016 | Rank results by relevance | US2 | T058 | Phase 4 | "Given search results, Then highest relevance first" | Unit |

---

### Access Control Requirements (FR-017 to FR-021)

| FR ID | Requirement | User Story | Task(s) | Phase | Acceptance Scenario | Test Type |
|---|---|---|---|---|---|---|
| FR-017 | RBAC with 5 roles | Foundation | T029 | Phase 2 | "Given 5 roles defined, Then assign to users" | Unit |
| FR-018 | Enforce role permissions | Foundation | T029 | Phase 2 | "Given Editor role, When attempt delete, Then deny" | Security |
| FR-019 | Access based on role + classification | US2 | T059 | Phase 4 | "Given role + classification check, Then enforce both" | Security |
| FR-020 | Deny with error messages | Foundation | T029 | Phase 2 | "Given unauthorized attempt, Then 403 Forbidden with message" | Integration |
| FR-021 | No bypass via direct access | US1 | T037 | Phase 3 | "Given RLS policy, When direct SQL attempt, Then enforce policy" | Security |

---

### Audit and Compliance Requirements (FR-022 to FR-028)

| FR ID | Requirement | User Story | Task(s) | Phase | Acceptance Scenario | Test Type |
|---|---|---|---|---|---|---|
| FR-022 | Log all document operations (create, read, update, delete, classify) | Foundation | T030, T043 | Phase 2, 3 | "Given any document operation, When complete, Then create audit entry" | Integration |
| FR-023 | Log authentication events (login, logout, failed attempts) | Foundation | T030 | Phase 2 | "Given login, When authenticate, Then log AUTH event" | Integration |
| FR-024 | Tamper-evident with checksums | Audit | T043, T095 | Phase 3, 7 | "Given audit log entry, Then calculate checksum" | Unit |
| FR-025 | Immutable audit logs (no modification/deletion) | Audit | T095 | Phase 7 | "Given audit log, When attempt UPDATE, Then database rejects" | Security |
| FR-026 | Retain audit logs 1 year minimum | Audit | T094 | Phase 7 | "Given audit entry 1 year old, When retention check, Then preserve" | Integration |
| FR-027 | Restrict access to Admin/Auditor only | Audit | T098 | Phase 7 | "Given Viewer role, When query audit, Then 403 Forbidden" | Security |
| FR-028 | Query + filter capabilities (date, user, action, document) | Audit | T093 | Phase 7 | "Given audit query with date filter, Then return matching entries" | Integration |

---

## Entity Implementation Completeness

### Document Entity Lifecycle

| Stage | File/Task | Responsibility | Details |
|---|---|---|---|
| **1. Model Definition** | T036 | Create SQLAlchemy ORM | Columns: id, title, content_encrypted, classification_level, version, owner_id, status (active/deleted), created_at, modified_at, search_vector, encryption_key_version |
| **2. Relationships** | T037, T080 | Add RLS policies + cascade | T037: Row-Level Security for classification-based access; T080: Cascade delete to DocumentVersion |
| **3. Triggers** | T038, T062 | Automatic updates | T038: Update modified_at on UPDATE; T062: Auto-update search_vector on title/content changes |
| **4. Creation Service** | T044 | Business logic for CREATE | Encrypt content, validate classification, assign owner, generate unique ID |
| **5. Retrieval Service** | T045 | Business logic for READ | Decrypt content, verify RLS permissions, return to user |
| **6. List Service** | T046 | Business logic for LIST | Pagination, filtering by classification/owner/status, RLS applied |
| **7. Update Service** | T086 | Business logic for UPDATE | Version snapshot created (T082), content updated, modified_at updated |
| **8. Delete Service** | (Implicit in T046) | Business logic for DELETE | Soft-delete: set status='deleted', deleted_at=now() |
| **9. API Routes** | T052-T054 | HTTP endpoints | POST /documents, GET /documents, GET /documents/{id} |
| **10. Audit Logging** | T030, T043 | Automatic audit trail | Middleware intercepts all operations, creates immutable log entries |
| **11. Search Integration** | T057-T062 | Full-text indexing | search_vector column, tsvector trigger, gin index |
| **12. Versioning Integration** | T082, T086 | Version snapshots | DocumentVersion records created on content updates |
| **13. Testing** | T104, T107, T113 | Quality assurance | Unit tests (create/get/list/update logic), integration tests (API endpoints), security tests |

**Coverage**: 13/13 stages complete ✅

---

### User Entity Role-Based Access

| Role | RBAC Task | Authorization Task | Capabilities | Audit Evidence |
|---|---|---|---|---|
| **Admin** | T034 | T029 | Full access (CRUD all documents, modify classifications, query audit logs) | T043 |
| **Manager** | T034 | T029 | Create/read/update/delete documents; change classifications (with approval for downgrades); query audit logs | T043 |
| **Editor** | T034 | T029 | Create documents; read/update own documents; cannot change classifications | T043 |
| **Viewer** | T034 | T029 | Read documents they have clearance for; cannot modify; no audit log access | T043 |
| **Auditor** | T034 | T029 | Query audit logs; cannot modify documents; read-only access to all classifications | T043 |

**Authorization Matrix**: T029 (complete RBAC enforcement)
**Model Definition**: T034 (role column in User table)
**Audit Trail**: T043 (all role-based decisions logged)

---

### Classification Entity Governance

| Aspect | Level 0 | Level 1 | Level 2 | Level 3 | Implementation |
|---|---|---|---|---|---|
| **Name** | Public | Internal | Confidential | Restricted | T021 seed data |
| **Encryption** | No | AES-256 | AES-256 | AES-256 | T042 (per-level keys) |
| **Viewer Access** | All roles | Manager/Editor/Viewer | Manager/Editor | Manager/Admin only | T029 authorization |
| **Change Permission** | Admin only | Manager/Admin | Manager/Admin | Admin only | T076 route authorization |
| **Downgrade Approval** | N/A | No | Yes | Yes | T078 approval logic |
| **Audit Logging** | T030, T043 | T030, T043 | T030, T043 | T030, T043 | T074 CLASSIFY events |
| **Search Results** | All | Role-filtered | Role-filtered | Role-filtered | T059 permission filtering |
| **Reference Data** | T021 (seed) | T021 | T021 | T021 | T055 (list endpoint) |

---

### AuditLog Entity Architecture

| Component | Task(s) | Implementation Detail |
|---|---|---|
| **Table Definition** | T039 | Partitioned table (monthly partitions) with columns: id, event_type, actor_id, resource_type, resource_id, timestamp, metadata (JSONB), previous_hash, current_hash |
| **Event Types** | T030, T043 | CREATE, READ, UPDATE, DELETE, CLASSIFY, AUTH |
| **Checksum Chain** | T043, T095 | SHA-256(previous_hash \|\| current_data) → current_hash (option: HMAC-SHA-256 with external key); validates integrity |
| **Immutability** | T095 | REVOKE UPDATE, DELETE on audit_logs table via RLS/database permissions |
| **Partitioning** | T094 | Monthly partitions auto-created; old partitions archived/deleted after 1-year retention |
| **Query Interface** | T093, T097 | Query function with date range, actor, event_type, resource filters |
| **Integrity Verification** | T095, T096 | SQL function verify_audit_chain() checks checksum continuity |
| **API Access** | T098-T100 | GET /audit (query), POST /audit/verify-integrity (validate); Admin/Auditor only |
| **Performance Optimization** | T102 | Query optimization ensures <3s response for 90-day range (SC-010) |
| **Testing** | T113 | Audit trail immutability, integrity function, 100% event coverage |

---

### DocumentVersion Entity History Management

| Stage | Task(s) | Details |
|---|---|---|
| **Model** | T079 | SQLAlchemy ORM: document_id (FK), version_number, content_snapshot (encrypted), author_id (FK), change_description, created_at, classification_at_version, encryption_key_version |
| **Relationships** | T080 | CASCADE DELETE from Document; maintains referential integrity |
| **Version Creation** | T082 | Service function: create_version() snapshots encrypted content when document updated |
| **History Retrieval** | T083 | Service function: get_version_history(document_id) returns paginated list with metadata |
| **Specific Version Retrieval** | T084 | Service function: get_version(document_id, version_num) decrypts and returns content |
| **Restoration** | T085 | Service function: restore_version(document_id, version_num) makes version current (optional) |
| **Update Integration** | T086 | update_document() in DocumentService creates version before updating current |
| **API Endpoints** | T089, T090 | GET /documents/{id}/versions (list), GET /documents/{id}/versions/{ver} (retrieve) |
| **Audit Logging** | T092 | UPDATE events record old/new version numbers in audit log |
| **Testing** | T115 | Version snapshots match originals; all versions retrievable; cascade delete works |

---

## Success Criteria Validation Matrix

### Performance Criteria (Measurable, Time-Based)

| Criterion | Target | Measurement | Validation Task | Phase | Pass/Fail Definition |
|---|---|---|---|---|---|
| SC-001 | Create document <30s | Integration test timer | T052 | Phase 3 | Time from POST /documents to response < 30s |
| SC-002 | Search <2s (10k docs) | Load test with 10k documents | T068 | Phase 4 | Time from GET /search to response < 2s, 100 concurrent users |
| SC-007 | Classification change <5s | Integration test timer | T076 | Phase 5 | Time from PUT /documents/{id}/classification to response < 5s |
| SC-010 | Audit query <3s (90-day) | Historical data query | T102 | Phase 7 | Time from GET /audit with date range to response < 3s |

**All 4 performance criteria have explicit task-based validation** ✅

---

### Quality Criteria (Percentage/Coverage-Based)

| Criterion | Target | Measurement | Validation Task | Phase | Pass/Fail Definition |
|---|---|---|---|---|---|
| SC-003 | 100% audit coverage | Middleware intercept test | T030, T113 | Phase 2, 8 | All document operations logged; zero exceptions |
| SC-004 | 100% access control | Security test suite | T111 | Phase 8 | Unauthorized access attempts 100% denied |
| SC-005 | Immutable audit logs | Database permission test | T095, T113 | Phase 7, 8 | No UPDATE/DELETE allowed on audit_logs table |
| SC-008 | 100% version history | Unit test snapshots | T082, T115 | Phase 6, 8 | All version snapshots match originals |
| SC-009 | Zero bypass incidents | Penetration testing | T111 | Phase 8 | Zero successful bypass attempts in security tests |
| SC-012 | 100% events logged | Audit completeness test | T113 | Phase 8 | All required event types (CREATE, READ, UPDATE, DELETE, CLASSIFY, AUTH) logged |
| SC-013 | Access control verified | RBAC + classification test | T111 | Phase 8 | Role+classification checks pass all scenarios |

**All 7 quality criteria have explicit task-based validation** ✅

---

### Compliance/UX Criteria (Manual Verification)

| Criterion | Target | Verification Method | Validation | Notes |
|---|---|---|---|---|
| SC-006 | 85% first-attempt success | User testing/analytics | Manual | Requires real user data; tracked post-deployment |
| SC-011 | Quarterly compliance review | ISO 27001 audit checklist | Manual | Scheduled compliance review; not code-testable |

**Both manual criteria deferred to operational phase** ⚠️

---

## Constitution Principle Implementation Map

### Principle I: Security by Design

| Component | Task(s) | Implementation | Validation |
|---|---|---|---|
| **Encryption at Rest** | T020, T041, T042 | pgcrypto AES-256 per classification level | T112 (encryption correctness test) |
| **Encryption in Transit** | T009, T124 | TLS 1.3 via Caddy reverse proxy | T124 (testssl.sh verification) |
| **Authentication** | T028, T031 | JWT RS256 token validation | T110 (token validation tests) |
| **Authorization** | T029, T031 | RBAC + classification clearance checks | T111 (access control tests) |
| **Access Enforcement** | T037 | Row-Level Security (RLS) at database level | T111 (RLS bypass attempts fail) |
| **Audit Trail** | T030, T043 | Middleware intercepts all operations | T113 (100% coverage validation) |
| **Static Analysis** | T116 | Bandit security scanner in CI/CD | Zero critical findings required |
| **Dependency Scanning** | T117 | Safety tool for vulnerabilities | No high/critical vulnerabilities |

---

### Principle II: Classification-Based Access Control

| Component | Task(s) | Implementation | Validation |
|---|---|---|---|
| **Classification Model** | T035, T021 | 4 levels (Public, Internal, Confidential, Restricted) | T021 seed data verification |
| **RBAC Model** | T034, T029 | 5 roles (Admin, Manager, Editor, Viewer, Auditor) | T111 role hierarchy tests |
| **Access Decision Logic** | T029, T037, T059 | Evaluate role + classification for every operation | T111 (dual-check tests) |
| **Permission Matrix** | T029 | Admin=full, Manager=CRUD+classify, Editor=create+own, Viewer=read, Auditor=audit | Documentation in T031 |
| **Downgrade Approval** | T078 | Classification downgrade requires justification + Manager/Admin approval | T111 (approval workflow tests) |
| **API Enforcement** | T052-T054, T076 | Authorization checks in route handlers before business logic | T111 (unauthorized requests return 403) |

---

### Principle III: Auditability & Traceability

| Component | Task(s) | Implementation | Validation |
|---|---|---|---|
| **Event Capture** | T030, T043 | Middleware intercepts: CREATE, READ, UPDATE, DELETE, CLASSIFY, AUTH | T113 (event completeness) |
| **Immutability** | T095 | Database permissions: REVOKE UPDATE/DELETE on audit_logs | T113 (integrity verification) |
| **Tamper Detection** | T043, T095 | Checksum chain (previous_hash + current_hash) | T113 (chain validation) |
| **Retention Policy** | T094 | Monthly partitions; 1-year minimum retention; auto-archive | T026 (partition creation verified) |
| **Query Interface** | T093, T098 | Filtering by date range, actor, event type, resource | T102 (performance under 3s) |
| **Access Control** | T098, T100 | Admin/Auditor only; enforced via RLS + role check | T111 (unauthorized queries denied) |
| **Integrity Validation** | T095, T096 | SQL function verifies checksum chain continuity | T113 (chain integrity test) |

---

### Principle IV: Compliance First

| Component | Task(s) | Implementation | Validation |
|---|---|---|---|
| **ISO 27001 Mapping** | Plan.md | Controls A.5, A.8, A.9, A.12, A.18 mapped to FRs | Documentation complete |
| **Control A.5 (Access)** | T029, T034, T076 | RBAC + classification-based access | T111 tests verify enforcement |
| **Control A.8 (Classification)** | T035, T021, T076 | 4-level classification system + change management | T111 classification tests |
| **Control A.9 (User Access)** | T028, T029 | Authentication + authorization enforcement | T110, T111 security tests |
| **Control A.12 (Operational Security)** | T030, T043, T093 | Comprehensive audit logging + querying | T113 audit completeness |
| **Control A.18 (Compliance)** | T094, T098, T119 | Retention policies + audit trail evidence | T119 compliance checklist |
| **Quarterly Reviews** | – (manual) | Audit log data supports compliance reporting | Operational task (SC-011) |

---

### Principle V: Data Lifecycle Management

| Component | Task(s) | Implementation | Validation |
|---|---|---|---|
| **Retention Policy** | T036 | retention_policy_id field (nullable for MVP) | Documentation in T094 |
| **Soft-Delete** | T036 | status enum (active/deleted); deleted_at timestamp | T111 delete tests |
| **Automated Cleanup** | T094 (Phase 2 future) | Cron job to hard-delete after retention period | Phase 2 deferred |
| **Disposal Approval** | T086 | Manager/Admin role required for deletion | T111 authorization tests |
| **Backup Strategy** | T123 | Docker volume backups; pg_dump with GPG encryption | T123 backup/restore tests |
| **Audit Retention** | T094 | 1-year minimum; separate from document retention (3 years) | T026 partition verification |
| **Key Lifecycle** | T042 | encryption_key_version field for key rotation | Documentation in T122 |

---

### Principle VI: Secure Development Practices

| Component | Task(s) | Implementation | Validation |
|---|---|---|---|
| **Security Requirements** | Plan.md | Spec includes ISO 27001 control mapping + 28 FRs with security focus | Spec review complete |
| **Threat Modeling** | Plan.md | Risk management table identifies 6 risks with mitigations | Plan.md section "Risk Management" |
| **Secure SDLC** | T032 | GitHub Actions CI/CD with mandatory test/security checks | T032 workflow verification |
| **Static Analysis** | T116 | Bandit scans for security issues (target: zero critical) | T116 execution validates |
| **Dependency Scanning** | T117 | Safety checks for known vulnerabilities (no high/critical) | T117 execution validates |
| **Code Review Checklist** | T031 | Integration task documents security review requirements | T031 documentation |
| **Security Testing** | T110-T114 | Unit/integration/security/contract tests for all auth/authz/encryption/audit | 100+ security test cases |
| **Pre-Deployment Gates** | T032, T119 | Tests + Bandit + Safety must pass before deployment | CI/CD pipeline enforces |

---

## Cross-Phase Dependencies

### Blocking Dependencies (Sequential)

```
Phase 1 (Setup: T001-T011)
    ↓
Phase 2 (Foundation: T012-T032) ← BLOCKS all user stories
    ↓
├─ Phase 3 (US1: T033-T056)
├─ Phase 4 (US2: T057-T069)  ← Requires documents exist (from US1)
├─ Phase 5 (US3: T070-T078)  ← Requires documents exist (from US1)
└─ Phase 6 (US4: T079-T092)  ← Requires documents exist (from US1)
    ↓
Phase 7 (Audit: T093-T101)     ← Can run parallel to US2-US4
    ↓
Phase 8 (Testing: T102-T124)   ← Depends on all phases complete
```

---

### Parallel Opportunities Within Phases

**Phase 1 Setup**: T003, T004, T005, T006, T008, T009, T010, T011 (8 tasks can run in parallel)

**Phase 2 Foundation**: T022, T023, T024 (parallel model setup); T028, T029, T030 (parallel middleware)

**Phase 3 US1**: T033, T034, T035, T039 (parallel models); T047, T048, T049, T050, T051 (parallel schemas)

**Phase 4 US2**: Independent of US1 services after foundation

**Phase 8 Testing**: T103-T114 (all unit/integration/security tests can run in parallel)

---

## Task Count Summary by Category

### By Phase

| Phase | Name | Count | Blocking | Parallel Opportunities |
|---|---|---|---|---|
| 1 | Setup | 11 | No | 8 tasks |
| 2 | Foundation | 21 | YES (blocks all stories) | 6 tasks |
| 3 | US1: Create/Classify | 24 | No (depends on Phase 2) | 8 tasks |
| 4 | US2: Search/Retrieve | 13 | No (depends on Phase 2) | 2 tasks |
| 5 | US3: Update Classification | 9 | No (depends on Phase 2) | 1 task |
| 6 | US4: Version Control | 14 | No (depends on Phase 2) | 2 tasks |
| 7 | Audit System | 10 | No (parallel to US stories) | 0 tasks |
| 8 | Testing & Hardening | 22 | No (depends on features) | 12 tasks |
| **Total** | | **124** | | **43 tasks (35%)** |

---

### By Category

| Category | Count | Examples |
|---|---|---|
| **Models/Entities** | 12 | T033-T039, T079 (5 entities) |
| **Services** | 19 | T040-T043, T057-T060, T070-T085 (6 services) |
| **Middleware** | 4 | T027-T030, T031 (3 middleware components) |
| **Routes/API** | 12 | T052-T056, T065-T067, T076, T089-T090, T098-T101 (5 route modules) |
| **Schemas/Validation** | 6 | T047-T050, T064, T075, T087, T097 |
| **Database** | 7 | T017-T026 (migrations, seeding) |
| **Infrastructure** | 11 | T001-T016, T032 (setup, docker, config) |
| **Testing** | 22 | T103-T124 (unit, integration, security, performance) |
| **Scripts/Utilities** | 8 | T022, T023, T116, T117, T121-T124 |
| **Other** | 5 | T093-T096, T102 (audit queries, performance) |

---

## Recommended Execution Sequences

### MVP (Minimum Viable Product) - 56 Tasks, 4-5 Weeks

1. **Weeks 1-2: Setup + Foundation**
   - Phase 1 (T001-T011): 11 tasks
   - Phase 2 (T012-T032): 21 tasks
   - **Checkpoint**: Docker environment running, database schema ready, middleware integrated

2. **Week 3-4: User Story 1 (Create/Classify)**
   - Phase 3 (T033-T056): 24 tasks
   - **Checkpoint**: Create documents, verify encryption, check audit logs
   - **Deliverable**: MVP feature ready for demo

3. **Week 5+: Complete First Story**
   - Phase 8 partial (T103-T107): Testing + security validation
   - **Checkpoint**: Tests passing, Bandit/Safety clean, ready for deployment

---

### Full Feature - 124 Tasks, 12 Weeks

**Weeks 1-2**: Phase 1 + Phase 2 (Setup + Foundation)
**Weeks 3-4**: Phase 3 (US1: Create/Classify) + Phase 7 partial (audit models)
**Weeks 5-6**: Phase 4 (US2: Search/Retrieve)
**Weeks 7-8**: Phase 5 (US3: Update Classification) + Phase 6 partial (Version models)
**Weeks 9-10**: Phase 6 remaining (US4: Version Control)
**Weeks 11-12**: Phase 7 remaining (Audit queries/integrity) + Phase 8 (Testing & Hardening)

---

**End of Detailed Tables**
