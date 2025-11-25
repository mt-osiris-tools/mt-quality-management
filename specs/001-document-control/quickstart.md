# Quick Start Guide: Document Control Process

**Feature**: 001-document-control
**Last Updated**: 2025-11-24
**Target Audience**: Developers, QA Engineers, DevOps

## Prerequisites

- **Python**: 3.11 or higher
- **PostgreSQL**: 16 or higher
- **Docker**: 24.0+ (optional but recommended)
- **Git**: For version control

## Local Development Setup

### 1. Clone Repository and Setup Branch

```bash
# Clone repository
git clone <repository-url>
cd mt-quality-management

# Checkout feature branch
git checkout 001-document-control

# Create Python virtual environment
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install Dependencies

```bash
# Install Python dependencies
pip install -r requirements.txt

# Install development dependencies (testing, linting)
pip install -r requirements-dev.txt
```

**Key Dependencies**:
- `fastapi[all]`: Web framework (includes uvicorn server)
- `sqlalchemy`: ORM for database interactions
- `psycopg2-binary`: PostgreSQL driver
- `python-jose[cryptography]`: JWT authentication
- `pydantic`: Data validation
- `structlog`: Structured logging
- `pytest`: Testing framework
- `bandit`: Security static analysis

### 3. Database Setup

#### Option A: Docker (Recommended)

```bash
# Start PostgreSQL via Docker Compose
docker-compose up -d postgres

# Database will be available at:
# Host: localhost
# Port: 5432
# Database: qms
# User: qms_user
# Password: (set in .env file)
```

#### Option B: Local PostgreSQL

```bash
# Install PostgreSQL 16
# macOS: brew install postgresql@16
# Ubuntu: sudo apt install postgresql-16

# Start PostgreSQL service
# macOS: brew services start postgresql@16
# Ubuntu: sudo systemctl start postgresql

# Create database and user
psql postgres
CREATE DATABASE qms;
CREATE USER qms_user WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE qms TO qms_user;
\q
```

### 4. Environment Configuration

Create `.env` file in project root:

```env
# Database
DATABASE_URL=postgresql://qms_user:secure_password@localhost:5432/qms

# Encryption Keys (AES-256, 32 bytes each, base64 encoded)
# Generate with: python -c "import secrets; print(secrets.token_urlsafe(32))"
ENCRYPTION_KEY_LEVEL_1=<generate-key-1>
ENCRYPTION_KEY_LEVEL_2=<generate-key-2>
ENCRYPTION_KEY_LEVEL_3=<generate-key-3>

# JWT Authentication (RS256 public key from external IdP)
JWT_PUBLIC_KEY=<public-key-pem>
JWT_ALGORITHM=RS256

# Application
APP_ENV=development
LOG_LEVEL=INFO

# CORS (development only)
CORS_ORIGINS=http://localhost:3000,http://localhost:8000
```

**Generate Encryption Keys**:
```bash
# Generate three separate 256-bit keys
python -c "import secrets; [print(f'ENCRYPTION_KEY_LEVEL_{i}={secrets.token_urlsafe(32)}') for i in range(1,4)]"
```

### 5. Database Migrations

```bash
# Initialize database schema
alembic upgrade head

# Seed reference data (classifications)
python scripts/seed_data.py

# Verify database setup
python scripts/verify_db.py
```

### 6. Run Application

```bash
# Start FastAPI development server
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Application available at:
# API: http://localhost:8000
# Interactive API docs: http://localhost:8000/docs
# OpenAPI spec: http://localhost:8000/openapi.json
```

## Project Structure

```
mt-quality-management/
├── .env                    # Environment variables (gitignored)
├── .env.example            # Example environment file
├── requirements.txt        # Python dependencies
├── requirements-dev.txt    # Development dependencies
├── docker-compose.yml      # Docker services
├── Dockerfile              # Application container
├── alembic.ini             # Database migration config
├── pytest.ini              # Test configuration
├── main.py                 # FastAPI application entry point
│
├── src/
│   ├── __init__.py
│   ├── models/             # SQLAlchemy models
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── document.py
│   │   ├── classification.py
│   │   ├── document_version.py
│   │   └── audit_log.py
│   ├── services/           # Business logic
│   │   ├── __init__.py
│   │   ├── document_service.py
│   │   ├── search_service.py
│   │   ├── audit_service.py
│   │   ├── encryption_service.py
│   │   └── classification_service.py
│   ├── middleware/         # Security middleware
│   │   ├── __init__.py
│   │   ├── authentication.py
│   │   ├── authorization.py
│   │   └── audit_logging.py
│   ├── routes/             # API endpoints
│   │   ├── __init__.py
│   │   ├── documents.py
│   │   ├── search.py
│   │   ├── versions.py
│   │   ├── classifications.py
│   │   └── audit.py
│   ├── schemas/            # Pydantic schemas
│   │   ├── __init__.py
│   │   ├── document.py
│   │   ├── user.py
│   │   └── audit.py
│   └── utils/              # Helper utilities
│       ├── __init__.py
│       ├── config.py
│       ├── database.py
│       └── security.py
│
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── security/
│   ├── contract/
│   └── conftest.py         # Shared test fixtures
│
├── scripts/
│   ├── seed_data.py        # Database seeding
│   ├── verify_db.py        # Database verification
│   └── generate_keys.py    # Encryption key generation
│
└── docs/
    └── isms/               # ISO 27001 documentation
```

## Testing

### Run All Tests

```bash
# Run full test suite
pytest

# Run with coverage report
pytest --cov=src --cov-report=html

# View coverage report
open htmlcov/index.html  # macOS
# Or: xdg-open htmlcov/index.html  # Linux
```

### Run Specific Test Types

```bash
# Unit tests only
pytest tests/unit

# Integration tests
pytest tests/integration

# Security tests
pytest tests/security -m security

# Contract tests (API schema validation)
pytest tests/contract
```

### Security Testing

```bash
# Static security analysis
bandit -r src/ -f json -o bandit-report.json

# Dependency vulnerability scanning
safety check

# Combined security test suite
pytest tests/security -m security && bandit -r src/ && safety check
```

## Common Development Tasks

### Create New Document (via API)

```bash
# Get JWT token from external IdP (development mock)
export TOKEN="<your-jwt-token>"

# Create document
curl -X POST http://localhost:8000/api/v1/documents \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Test Document",
    "content": "This is test content",
    "classification_level": 1
  }'
```

### Search Documents

```bash
curl -X GET "http://localhost:8000/api/v1/search?q=test" \
  -H "Authorization: Bearer $TOKEN"
```

### View Audit Logs (Admin/Auditor only)

```bash
curl -X GET "http://localhost:8000/api/v1/audit?start_date=2025-11-01T00:00:00Z&end_date=2025-11-30T23:59:59Z" \
  -H "Authorization: Bearer $TOKEN"
```

### Verify Audit Trail Integrity

```bash
curl -X POST http://localhost:8000/api/v1/audit/verify-integrity \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{}'
```

## Database Operations

### Create Migration

```bash
# Generate new migration from model changes
alembic revision --autogenerate -m "Add new field to documents"

# Review generated migration in alembic/versions/
# Edit if necessary, then apply
alembic upgrade head
```

### Rollback Migration

```bash
# Rollback one migration
alembic downgrade -1

# Rollback to specific version
alembic downgrade <revision_id>

# View migration history
alembic history
```

### Backup Database

```bash
# Full backup
pg_dump -U qms_user -d qms > backup-$(date +%Y%m%d).sql

# Backup with encryption
pg_dump -U qms_user -d qms | gpg --encrypt --recipient qms-backup@example.com > backup-$(date +%Y%m%d).sql.gpg

# Restore from backup
psql -U qms_user -d qms < backup-20251124.sql
```

## Docker Deployment

### Development Environment

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f api

# Stop services
docker-compose down

# Rebuild after code changes
docker-compose up -d --build api
```

### Production Deployment

```bash
# Build production image
docker build -t qms-api:v1.0.0 .

# Scan for vulnerabilities
docker scout cves qms-api:v1.0.0

# Run production stack
docker-compose -f docker-compose.prod.yml up -d

# Zero-downtime update
docker-compose -f docker-compose.prod.yml up -d --no-deps --build api
```

## Troubleshooting

### Database Connection Issues

```bash
# Test database connection
psql -U qms_user -d qms -h localhost -p 5432

# Check PostgreSQL is running
# macOS: brew services list
# Ubuntu: sudo systemctl status postgresql

# View Docker container logs
docker-compose logs postgres
```

### Encryption Key Issues

```bash
# Verify keys are set
python -c "import os; print('Level 1:', bool(os.getenv('ENCRYPTION_KEY_LEVEL_1')))"

# Test encryption/decryption
python scripts/test_encryption.py
```

### JWT Authentication Issues

```bash
# Decode JWT token (without verification)
python -c "
import sys, json, base64
token = sys.argv[1].split('.')[1]
padding = '=' * (4 - len(token) % 4)
print(json.dumps(json.loads(base64.urlsafe_b64decode(token + padding)), indent=2))
" "<your-token>"

# Verify token includes required claims: sub, email, role, classification_clearance
```

### Test Failures

```bash
# Run tests with verbose output
pytest -vv

# Run specific test
pytest tests/unit/test_document_service.py::test_create_document -vv

# Show print statements in tests
pytest -s

# Run tests in parallel (faster)
pytest -n auto
```

## IDE Setup

### VS Code

Install recommended extensions:
- Python (Microsoft)
- Pylance
- Python Test Explorer
- Docker
- REST Client

Workspace settings (`.vscode/settings.json`):
```json
{
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": false,
  "python.linting.banditEnabled": true,
  "python.testing.pytestEnabled": true,
  "python.testing.pytestArgs": ["tests"],
  "python.formatting.provider": "black"
}
```

### PyCharm

1. Configure Python interpreter: venv/bin/python
2. Enable pytest as test runner
3. Configure database connection (PostgreSQL)
4. Install Docker plugin

## Performance Monitoring

### Local Performance Testing

```bash
# Install load testing tool
pip install locust

# Run load test
locust -f tests/performance/locustfile.py --host=http://localhost:8000

# Access load test UI at http://localhost:8089
```

### Database Query Performance

```bash
# Enable query logging
# Add to postgresql.conf:
# log_statement = 'all'
# log_duration = on

# View slow queries
psql -U qms_user -d qms -c "SELECT * FROM pg_stat_statements ORDER BY mean_exec_time DESC LIMIT 10;"
```

## Security Checklist

Before committing code:

- [ ] No hardcoded secrets (keys, passwords, tokens)
- [ ] All API endpoints require authentication
- [ ] Authorization checks on protected resources
- [ ] Input validation on all external input
- [ ] Audit logging for all operations
- [ ] Tests pass: `pytest tests/security -m security`
- [ ] Static analysis clean: `bandit -r src/`
- [ ] No vulnerable dependencies: `safety check`
- [ ] Encryption keys in .env (not committed)
- [ ] SQL queries use parameterization (no string interpolation)

## Next Steps

After completing local setup:

1. **Review API Documentation**: http://localhost:8000/docs
2. **Run Security Tests**: `pytest tests/security`
3. **Check Compliance**: Review ISO 27001 control implementation in `docs/isms/`
4. **Implement First User Story**: Start with US1 (Create and Classify Documents)
5. **Write Tests First**: Follow TDD approach per constitution

## Resources

- **API Documentation**: `specs/001-document-control/contracts/api-specification.yaml`
- **Data Model**: `specs/001-document-control/data-model.md`
- **Research**: `specs/001-document-control/research.md`
- **Implementation Plan**: `specs/001-document-control/plan.md`
- **Constitution**: `.specify/memory/constitution.md`
- **FastAPI Docs**: https://fastapi.tiangolo.com/
- **SQLAlchemy Docs**: https://docs.sqlalchemy.org/
- **PostgreSQL Docs**: https://www.postgresql.org/docs/16/

## Support

For issues or questions:
- Check troubleshooting section above
- Review implementation plan for architectural decisions
- Consult data model for entity relationships
- Check API specification for endpoint details
