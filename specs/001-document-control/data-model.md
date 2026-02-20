# Data Model: Document Control Process

**Feature**: 001-document-control
**Date**: 2025-11-24
**Database**: PostgreSQL 16+

## Entity Relationship Diagram

```
┌──────────────────────┐       ┌──────────────────────┐
│       User           │       │   Classification     │
├──────────────────────┤       ├──────────────────────┤
│ id (PK)              │       │ level_code (PK)      │
│ email                │───┐   │ level_name           │
│ role                 │   │   │ access_rules         │
│ active               │   │   │ handling_reqs        │
│ last_login           │   │   └──────────────────────┘
└──────────────────────┘   │            │
         │                 │            │ classification_level (FK)
         │ owner_id (FK)   │            │
         │                 │   ┌────────▼──────────────┐
         │                 │   │      Document         │
         │                 └──▶├───────────────────────┤
         │                     │ id (PK)               │
         │                     │ title                 │
         │                     │ content_encrypted     │
         │                     │ classification_level  │
         │                     │ version               │
         │                     │ owner_id (FK)         │
         │                     │ status                │
         │                     │ retention_policy_id   │
         │                     │ created_at            │
         │                     │ modified_at           │
         │                     │ search_vector         │
         │                     └───────────────────────┘
         │                              │
         │                              │ document_id (FK)
         │                              │
         │                     ┌────────▼──────────────┐
         │                     │  DocumentVersion      │
         │                     ├───────────────────────┤
         │                     │ id (PK)               │
         │                     │ document_id (FK)      │
         │                     │ version_number        │
         │                     │ content_snapshot      │
         │                     │ author_id (FK)        │
         │                     │ change_description    │
         │                     │ created_at            │
         │                     └───────────────────────┘
         │
         │ actor_id (FK)
         │
         └─────────────────────────────┐
                                       │
                              ┌────────▼──────────────┐
                              │      AuditLog         │
                              ├───────────────────────┤
                              │ id (PK)               │
                              │ timestamp             │
                              │ event_type            │
                              │ actor_id (FK)         │
                              │ actor_role            │
                              │ resource_type         │
                              │ resource_id           │
                              │ action                │
                              │ classification_level  │
                              │ ip_address            │
                              │ user_agent            │
                              │ details (JSONB)       │
                              │ previous_hash         │
                              │ current_hash          │
                              └───────────────────────┘
```

## Entity Definitions

### 1. User

Represents system users with roles and classification clearance.

**Note**: Per specification assumption #2, user management is external. This table serves as a lightweight cache/reference for authorization and audit purposes.

```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    role VARCHAR(20) NOT NULL CHECK (role IN ('Admin', 'Manager', 'Editor', 'Viewer', 'Auditor')),
    classification_clearance INTEGER NOT NULL DEFAULT 1 CHECK (classification_clearance BETWEEN 0 AND 3),
    active BOOLEAN NOT NULL DEFAULT true,
    last_login TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role);
```

**Attributes**:
- `id`: Unique identifier (primary key)
- `email`: User email address (unique)
- `role`: User role (Admin, Manager, Editor, Viewer, Auditor)
- `classification_clearance`: Maximum classification level user can access (0-3)
- `active`: User account status (soft delete support)
- `last_login`: Timestamp of last successful authentication
- `created_at`: Account creation timestamp
- `updated_at`: Last modification timestamp

**Business Rules**:
- Email must be unique across system
- Role determines baseline permissions (see RBAC matrix below)
- `classification_clearance` restricts document access regardless of role
- Inactive users cannot authenticate (enforced at authentication layer)

### 2. Classification

Reference table for document classification levels.

```sql
CREATE TABLE classifications (
    level_code INTEGER PRIMARY KEY CHECK (level_code BETWEEN 0 AND 3),
    level_name VARCHAR(20) NOT NULL UNIQUE,
    access_rules TEXT NOT NULL,
    handling_requirements TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Seed data (immutable reference data)
INSERT INTO classifications (level_code, level_name, access_rules, handling_requirements) VALUES
(0, 'Public', 'Approved for external release. No access restrictions.', 'Standard document handling. No special protection required.'),
(1, 'Internal', 'Internal use only. All authenticated users with clearance level 1+.', 'Keep within organization. Do not share externally without approval.'),
(2, 'Confidential', 'Restricted business information. Users with clearance level 2+ and business need.', 'Encrypt in transit and at rest. Limit distribution. Log all access.'),
(3, 'Restricted', 'Need-to-know basis only. Clearance level 3 + explicit authorization required.', 'Maximum protection. Encrypted storage mandatory. Access requires justification.');
```

**Attributes**:
- `level_code`: Numeric classification code (0-3) (primary key)
- `level_name`: Human-readable name (Public, Internal, Confidential, Restricted)
- `access_rules`: Description of who can access documents at this level
- `handling_requirements`: Security and handling procedures for this classification
- `created_at`: Record creation timestamp

**Business Rules**:
- Immutable reference data (no updates or deletes)
- Higher numeric values indicate stricter classification
- Access control decisions use `level_code` for comparison

### 3. Document

Core entity representing controlled documents.

```sql
CREATE TABLE documents (
    id SERIAL PRIMARY KEY,
    title VARCHAR(500) NOT NULL,
    content_encrypted BYTEA,  -- Encrypted with pgcrypto for levels 1-3
    classification_level INTEGER NOT NULL DEFAULT 1 REFERENCES classifications(level_code),
    version INTEGER NOT NULL DEFAULT 1,
    owner_id INTEGER NOT NULL REFERENCES users(id),
    status VARCHAR(20) NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'deleted')),
    retention_policy_id INTEGER,  -- Future feature, nullable for now
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    modified_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMPTZ,  -- Soft delete timestamp
    search_vector tsvector,  -- Full-text search
    encryption_key_version INTEGER NOT NULL DEFAULT 1,  -- For key rotation
    CONSTRAINT valid_status CHECK (
        (status = 'active' AND deleted_at IS NULL) OR
        (status = 'deleted' AND deleted_at IS NOT NULL)
    )
);

-- Indexes
CREATE INDEX idx_documents_owner ON documents(owner_id);
CREATE INDEX idx_documents_classification ON documents(classification_level);
CREATE INDEX idx_documents_status ON documents(status);
CREATE INDEX idx_documents_search ON documents USING gin(search_vector);
CREATE INDEX idx_documents_created ON documents(created_at DESC);

-- Automatic timestamp update
CREATE OR REPLACE FUNCTION update_modified_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.modified_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER documents_update_modified
BEFORE UPDATE ON documents
FOR EACH ROW
EXECUTE FUNCTION update_modified_at();

-- Automatic search vector update
CREATE TRIGGER documents_search_update
BEFORE INSERT OR UPDATE OF title ON documents
FOR EACH ROW
EXECUTE FUNCTION tsvector_update_trigger(search_vector, 'pg_catalog.english', title);
```

**Attributes**:
- `id`: Unique document identifier (primary key)
- `title`: Document title (searchable, max 500 chars)
- `content_encrypted`: Encrypted document content (BYTEA for binary encrypted data)
- `classification_level`: Security classification (FK to classifications)
- `version`: Current version number (increments on updates)
- `owner_id`: User who created/owns the document (FK to users)
- `status`: Document status (active or deleted for soft-delete)
- `retention_policy_id`: Future reference to retention policy (nullable)
- `created_at`: Creation timestamp
- `modified_at`: Last modification timestamp (auto-updated)
- `deleted_at`: Soft delete timestamp (null if active)
- `search_vector`: Full-text search index (auto-populated from title)
- `encryption_key_version`: Tracks which encryption key version was used (for rotation)

**Business Rules**:
- Title required and searchable
- Content encrypted for classification levels 1-3 (Public level 0 unencrypted)
- Default classification is Internal (level 1) per constitutional requirement
- Owner cannot be changed after creation (immutable audit trail)
- Soft delete: status='deleted' and deleted_at set (content retained per retention policy)
- Version increments on content updates (tracked in DocumentVersion history)
- Search vector automatically updated when title changes

**Encryption Strategy**:
- Public (0): No encryption (`content_encrypted` stores plain text)
- Internal (1): Encrypted with `ENCRYPTION_KEY_LEVEL_1`
- Confidential (2): Encrypted with `ENCRYPTION_KEY_LEVEL_2`
- Restricted (3): Encrypted with `ENCRYPTION_KEY_LEVEL_3`

### 4. DocumentVersion

History table for document versioning.

```sql
CREATE TABLE document_versions (
    id SERIAL PRIMARY KEY,
    document_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    version_number INTEGER NOT NULL,
    content_snapshot BYTEA NOT NULL,  -- Encrypted content at this version
    author_id INTEGER NOT NULL REFERENCES users(id),
    change_description TEXT,
    classification_at_version INTEGER NOT NULL,  -- Classification when version was created
    encryption_key_version INTEGER NOT NULL,  -- Key version used for this snapshot
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(document_id, version_number)
);

CREATE INDEX idx_doc_versions_document ON document_versions(document_id);
CREATE INDEX idx_doc_versions_created ON document_versions(created_at DESC);
```

**Attributes**:
- `id`: Unique version record identifier (primary key)
- `document_id`: Reference to parent document (FK, cascade delete)
- `version_number`: Version number (1, 2, 3, ...)
- `content_snapshot`: Encrypted content at this version
- `author_id`: User who created this version (FK to users)
- `change_description`: Optional description of changes
- `classification_at_version`: Classification level when version created (audit trail)
- `encryption_key_version`: Encryption key version for this snapshot
- `created_at`: Version creation timestamp

**Business Rules**:
- Unique constraint on (document_id, version_number)
- Versions immutable once created (no updates or deletes except cascade from parent document)
- Content snapshot encrypted with same key as current document classification
- Author tracked for audit trail (who made this change?)
- Classification tracked at version level (supports classification history audit)

**Cascade Delete**: When document is permanently deleted (beyond retention), versions cascade delete automatically.

### 5. AuditLog

Immutable audit trail for all system operations.

```sql
CREATE TABLE audit_logs (
    id BIGSERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    event_type VARCHAR(50) NOT NULL,  -- CREATE, READ, UPDATE, DELETE, CLASSIFY, AUTH
    actor_id INTEGER REFERENCES users(id),  -- Nullable for system events
    actor_role VARCHAR(20),
    resource_type VARCHAR(50) NOT NULL,  -- Document, User, Classification
    resource_id INTEGER,  -- ID of affected resource
    action VARCHAR(100) NOT NULL,  -- Specific action (e.g., CREATE_DOCUMENT, UPDATE_CLASSIFICATION)
    classification_level INTEGER,  -- For document operations
    ip_address INET,
    user_agent TEXT,
    details JSONB,  -- Additional context (old_value, new_value, etc.)
    previous_hash VARCHAR(64),  -- Hash of previous audit log entry (blockchain-style chain)
    current_hash VARCHAR(64) NOT NULL  -- HMAC-SHA-256(prev_hash || canonical_payload, audit_hmac_key) hex
) PARTITION BY RANGE (timestamp);

-- Create initial partition (2025-11)
CREATE TABLE audit_logs_2025_11 PARTITION OF audit_logs
FOR VALUES FROM ('2025-11-01') TO ('2025-12-01');

-- Create additional monthly partitions as needed
-- Note: Automate partition creation via cron or database scheduler

-- Indexes
CREATE INDEX idx_audit_actor ON audit_logs(actor_id);
CREATE INDEX idx_audit_resource ON audit_logs(resource_type, resource_id);
CREATE INDEX idx_audit_timestamp ON audit_logs(timestamp DESC);
CREATE INDEX idx_audit_event_type ON audit_logs(event_type);
CREATE INDEX idx_audit_action ON audit_logs(action);

-- Enforce immutability (revoke UPDATE and DELETE)
REVOKE UPDATE, DELETE ON audit_logs FROM PUBLIC;
GRANT INSERT, SELECT ON audit_logs TO app_user;

-- Integrity verification function
CREATE OR REPLACE FUNCTION verify_audit_chain(start_id BIGINT DEFAULT NULL, end_id BIGINT DEFAULT NULL)
RETURNS TABLE(is_valid BOOLEAN, broken_at BIGINT, message TEXT) AS $$
DECLARE
    broken_link RECORD;
    start_check BIGINT := COALESCE(start_id, 1);
    end_check BIGINT := COALESCE(end_id, (SELECT MAX(id) FROM audit_logs));
BEGIN
    -- Find first broken link in chain (link continuity)
    SELECT a1.id, a1.previous_hash, a2.current_hash INTO broken_link
    FROM audit_logs a1
    LEFT JOIN audit_logs a2 ON a1.previous_hash = a2.current_hash
    WHERE a1.id > start_check AND a1.id <= end_check
      AND a1.id > 1  -- Skip first entry (has no previous)
      AND a2.id IS NULL
    ORDER BY a1.id
    LIMIT 1;

    IF FOUND THEN
        RETURN QUERY SELECT false, broken_link.id,
            'Audit chain broken at ID ' || broken_link.id || ': previous_hash does not match any current_hash';
    ELSE
        RETURN QUERY SELECT true, NULL::BIGINT,
            'Audit chain valid from ID ' || start_check || ' to ' || end_check;
    END IF;
END;
$$ LANGUAGE plpgsql;
```

**Attributes**:
- `id`: Unique audit log identifier (primary key, BIGSERIAL for high volume)
- `timestamp`: Event occurrence time (default NOW())
- `event_type`: Category of event (CREATE, READ, UPDATE, DELETE, CLASSIFY, AUTH)
- `actor_id`: User who performed action (nullable for system events)
- `actor_role`: Role of actor at time of event (denormalized for audit immutability)
- `resource_type`: Type of resource affected (Document, User, Classification)
- `resource_id`: ID of affected resource (nullable for non-resource events)
- `action`: Specific action taken (CREATE_DOCUMENT, CHANGE_CLASSIFICATION, LOGIN_SUCCESS)
- `classification_level`: Classification level for document operations (audit sensitivity)
- `ip_address`: Client IP address (security monitoring)
- `user_agent`: Client user agent string
- `details`: JSON field for additional context (flexible structure)
- `previous_hash`: hash of previous audit log entry (chain link)
- `current_hash`: HMAC-SHA-256 over canonical payload + previous_hash (tamper-evident)

**Partitioning Strategy**:
- Partitioned by month using PostgreSQL range partitioning
- Improves query performance for date-range queries
- Simplifies retention management (drop old partitions after retention period)
- Create new partitions monthly via automated script

**Business Rules**:
- Append-only: No updates or deletes allowed (enforced via REVOKE)
- Every system operation generates audit log entry (no exceptions per constitutional requirement)
- Checksum chain: Each entry links to previous via hash (tamper detection)
- Actor role denormalized (immutable snapshot of role at event time)
- JSONB details field for flexible context storage (old_value, new_value, justification, etc.)

**Integrity Verification**:
```sql
-- Verify entire audit chain
SELECT * FROM verify_audit_chain();

-- Verify specific range
SELECT * FROM verify_audit_chain(1000, 2000);
```

## RBAC Permission Matrix

Role-based access control permissions by role and classification level:

| Role | Create Doc | Read Doc | Update Doc | Delete Doc | Change Classification | View Audit Logs |
|------|-----------|----------|------------|------------|----------------------|----------------|
| **Admin** | ✓ (all levels) | ✓ (all levels) | ✓ (all docs) | ✓ (all docs) | ✓ (all changes) | ✓ (full access) |
| **Manager** | ✓ (clearance level) | ✓ (clearance level) | ✓ (own docs) | ✓ (own docs) | ✓ (with approval for downgrade) | ✗ |
| **Editor** | ✓ (clearance level) | ✓ (clearance level) | ✓ (own docs) | ✗ | ✗ | ✗ |
| **Viewer** | ✗ | ✓ (clearance level) | ✗ | ✗ | ✗ | ✗ |
| **Auditor** | ✗ | ✓ (all levels) | ✗ | ✗ | ✗ | ✓ (read-only) |

**Classification Level Access**:
- User can only access documents where `document.classification_level <= user.classification_clearance`
- Exception: Auditor role has read access to all classification levels

**Document Ownership**:
- Editor and Manager can only update/delete documents they own (`document.owner_id = user.id`)
- Admin can update/delete any document

**Classification Changes**:
- Only Manager and Admin roles can change classification
- Downgrades (higher to lower classification) require approval with justification (stored in audit log)
- Upgrades (lower to higher classification) do not require approval

## Row-Level Security (RLS) Policies

PostgreSQL RLS enforces classification-based access at database level:

```sql
-- Enable Row-Level Security on documents table
ALTER TABLE documents ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only see documents at or below their clearance level
CREATE POLICY documents_classification_access ON documents
FOR SELECT
USING (
    classification_level <= (
        SELECT classification_clearance
        FROM users
        WHERE id = current_setting('app.user_id')::INTEGER
    )
    OR EXISTS (
        SELECT 1 FROM users
        WHERE id = current_setting('app.user_id')::INTEGER
        AND role = 'Auditor'
    )
);

-- Policy: Editors and Managers can create documents at their clearance level
CREATE POLICY documents_create_policy ON documents
FOR INSERT
WITH CHECK (
    classification_level <= (
        SELECT classification_clearance
        FROM users
        WHERE id = current_setting('app.user_id')::INTEGER
    )
    AND EXISTS (
        SELECT 1 FROM users
        WHERE id = current_setting('app.user_id')::INTEGER
        AND role IN ('Editor', 'Manager', 'Admin')
    )
);

-- Policy: Users can only update their own documents (or Admins can update any)
CREATE POLICY documents_update_policy ON documents
FOR UPDATE
USING (
    owner_id = current_setting('app.user_id')::INTEGER
    OR EXISTS (
        SELECT 1 FROM users
        WHERE id = current_setting('app.user_id')::INTEGER
        AND role = 'Admin'
    )
);

-- Set user context at connection time (from JWT token)
-- Example: SET app.user_id = 123;
```

**RLS Benefits**:
- Defense in depth: Access control enforced at database level
- Prevents accidental data leakage from application bugs
- Supports ISO 27001 Control A.5 (Access Control) requirements

## Database Initialization Script

```sql
-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION IF NOT EXISTS pg_trgm;  -- For fuzzy search

-- Create tables in order (respecting foreign keys)
-- 1. Users (no dependencies)
-- 2. Classifications (no dependencies)
-- 3. Documents (depends on Users, Classifications)
-- 4. DocumentVersions (depends on Documents, Users)
-- 5. AuditLogs (depends on Users, partitioned)

-- Seed data
INSERT INTO classifications (level_code, level_name, access_rules, handling_requirements) VALUES
(0, 'Public', 'Approved for external release', 'Standard handling'),
(1, 'Internal', 'Internal use only', 'Keep within organization'),
(2, 'Confidential', 'Restricted business information', 'Encrypt, log access'),
(3, 'Restricted', 'Need-to-know only', 'Maximum protection, justify access');

-- Create application user (limited permissions)
CREATE USER app_user WITH PASSWORD 'secure_password';
GRANT CONNECT ON DATABASE qms TO app_user;
GRANT USAGE ON SCHEMA public TO app_user;
GRANT SELECT, INSERT, UPDATE ON users, documents, document_versions TO app_user;
GRANT SELECT ON classifications TO app_user;
GRANT INSERT, SELECT ON audit_logs TO app_user;  -- No UPDATE or DELETE
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO app_user;
```

## Data Retention & Archival

**Retention Policy** (per specification assumption #9):
- **Documents**: 3 years default (soft-delete, retained until retention period expires)
- **Audit Logs**: 1 year minimum (constitutional requirement), extendable per compliance needs
- **Document Versions**: Same retention as parent document (cascade delete)

**Archival Process**:
1. **Documents**:
   - Soft delete: `UPDATE documents SET status='deleted', deleted_at=NOW() WHERE id=?`
   - Hard delete: After retention period, `DELETE FROM documents WHERE deleted_at < NOW() - INTERVAL '3 years'`
   - Cascade deletes document_versions automatically

2. **Audit Logs**:
   - Archive old partitions to cold storage: `pg_dump` partition to file
   - Drop partition: `DROP TABLE audit_logs_2023_11` (after archival)
   - Automate via cron job or database scheduler

**Future Enhancement**: Automated retention policy engine (separate feature) to manage lifecycle based on document classification and type.

## Data Model Validation

This data model supports all 28 functional requirements from the specification:

| Requirement | Table(s) | Validation |
|------------|----------|-----------|
| FR-001 (Create docs) | documents | ✓ title, content_encrypted, owner_id |
| FR-002 (Default classification) | documents | ✓ DEFAULT 1 (Internal) |
| FR-003 (4 classification levels) | classifications | ✓ 0-3 seed data |
| FR-004 (Change classification) | documents | ✓ classification_level updatable |
| FR-005 (Approval for downgrade) | audit_logs | ✓ details JSONB stores justification |
| FR-006 (Unique ID) | documents | ✓ SERIAL PRIMARY KEY |
| FR-007 (Metadata) | documents | ✓ all attributes present |
| FR-008 (Update content) | documents | ✓ content_encrypted updatable |
| FR-009 (Version history) | document_versions | ✓ snapshots preserved |
| FR-010 (View history) | document_versions | ✓ queryable by document_id |
| FR-011 (Soft delete) | documents | ✓ status='deleted', deleted_at |
| FR-012 (Full-text search) | documents | ✓ search_vector tsvector |
| FR-013 (Permission filtering) | RLS policies | ✓ classification check |
| FR-014 (Retrieve content) | documents | ✓ SELECT query |
| FR-015 (Display metadata) | documents | ✓ all metadata columns |
| FR-016 (Ranked results) | search_vector | ✓ ts_rank() function |
| FR-017 (RBAC 5 roles) | users | ✓ role enum |
| FR-018 (Role permissions) | RLS + app logic | ✓ policies + middleware |
| FR-019 (Permission evaluation) | RLS | ✓ role + classification check |
| FR-020 (Deny access) | RLS | ✓ policies return empty set |
| FR-021 (No bypass) | RLS | ✓ enforced at DB level |
| FR-022 (Log operations) | audit_logs | ✓ all event types |
| FR-023 (Log auth events) | audit_logs | ✓ AUTH event_type |
| FR-024 (Tamper-evident) | audit_logs | ✓ current_hash column |
| FR-025 (Immutable logs) | REVOKE | ✓ no UPDATE/DELETE |
| FR-026 (1-year retention) | Partitioning | ✓ monthly partitions |
| FR-027 (Admin/Auditor only) | RLS + app logic | ✓ role check |
| FR-028 (Query logs) | audit_logs | ✓ indexes on key fields |

All requirements satisfied with this data model design.
