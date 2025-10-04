# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

---

## Project Overview

**五好伴学 (Wuhao Tutor)** - A modern AI-powered K12 education platform featuring homework grading, learning Q&A, and analytics using Alibaba Cloud Bailian AI services.

- **Current Status**: Phase 4 (Production Deployment Optimization)
- **Backend**: 100% complete, production-ready
- **Frontend**: 95% complete (Vue3 Web + WeChat Miniprogram)
- **Tech Stack**: Python 3.11+ FastAPI + Vue 3 TypeScript + PostgreSQL + Redis

---

## Essential Development Commands

### Environment Setup
```bash
# Install dependencies using uv (NOT pip or poetry)
uv sync

# Environment diagnostics (run this first when debugging)
uv run python scripts/diagnose.py

# Copy and configure environment variables
cp .env.dev .env  # or .env.prod for production
```

### Starting Development Environment
```bash
# Start both frontend and backend (RECOMMENDED)
./scripts/start-dev.sh

# Check service status
./scripts/status-dev.sh
./scripts/status-dev.sh --verbose  # detailed info

# Stop all services
./scripts/stop-dev.sh
./scripts/stop-dev.sh --clean-logs  # also clean logs
```

**Important**: The startup scripts handle port allocation, dependency installation, and health checks automatically. Always prefer these scripts over manual `uvicorn` or `vite` commands.

### Code Quality (Must Pass Before Commit)
```bash
# Format code (Black + isort)
make format

# Type checking (mypy strict mode)
make type-check

# Linting (flake8 + Black + isort checks)
make lint

# Pre-commit check (format + lint + type-check + tests)
make pre-commit  # MUST PASS before committing
```

### Testing
```bash
# Run all tests
make test
uv run pytest tests/ -v

# Run specific test categories
make test-unit           # Unit tests only
make test-integration    # Integration tests only

# Coverage report
make test-coverage
uv run pytest --cov=src --cov-report=html --cov-report=term-missing

# Run a single test file
uv run pytest tests/unit/test_specific.py -v

# Run tests matching a pattern
uv run pytest tests/ -k "test_homework" -v
```

### Database Management
```bash
# Apply migrations
make db-upgrade
uv run alembic upgrade head

# Generate new migration (after modifying models)
make db-migrate
# This prompts for description, then runs: alembic revision --autogenerate

# Rollback one migration
make db-downgrade
uv run alembic downgrade -1

# Reset database (DANGEROUS - prompts for confirmation)
make db-reset

# Database management script (comprehensive tool)
uv run python scripts/manage_db.py --help
```

### Quick Reference
```bash
# Start development
./scripts/start-dev.sh

# Develop, test, iterate...

# Pre-commit checks
make pre-commit  # MUST pass

# Commit
git add .
git commit -m "feat: description"
```

---

## Architecture Overview

### Layered Design (Strict Separation of Concerns)

The application follows a 4-layer architecture with strict boundaries:

```
┌────────────────────────────────────────────────┐
│  API Layer (src/api/v1/)                       │
│  - Route handlers                              │
│  - Request validation (Pydantic)               │
│  - Response wrapping                           │
│  - Dependency injection                        │
│  ❌ NO business logic or direct DB access      │
└────────────────┬───────────────────────────────┘
                 ↓
┌────────────────────────────────────────────────┐
│  Service Layer (src/services/)                 │
│  - Business logic orchestration                │
│  - Transaction management                      │
│  - AI service integration (BailianService)     │
│  - Multi-repository composition                │
│  ❌ NO direct SQL or ORM usage                 │
└────────────────┬───────────────────────────────┘
                 ↓
┌────────────────────────────────────────────────┐
│  Repository Layer (src/repositories/)          │
│  - Generic CRUD (BaseRepository[Model])        │
│  - Complex queries and aggregations            │
│  - Data access abstraction                     │
│  ❌ NO business rules or logic                 │
└────────────────┬───────────────────────────────┘
                 ↓
┌────────────────────────────────────────────────┐
│  Model Layer (src/models/)                     │
│  - SQLAlchemy 2.x ORM models (async)           │
│  - Database schema definitions                 │
│  - Relationships and constraints               │
│  ❌ NO business logic                          │
└────────────────────────────────────────────────┘
```

**Critical Rule**: Never bypass layers (e.g., API directly calling Repository). This breaks the abstraction and makes testing/maintenance harder.

### Middleware Stack (Execution Order)

Middleware is executed from outer to inner for requests, and inner to outer for responses:

```
1. PerformanceMonitoringMiddleware  ← Tracks request timing
2. SecurityHeadersMiddleware         ← Adds CSP, HSTS, etc.
3. RateLimitMiddleware              ← IP/user/AI rate limiting
4. CORSMiddleware                   ← Cross-origin handling
5. TrustedHostMiddleware            ← Host validation (prod)
6. LoggingMiddleware                ← Request/response logging
7. FastAPI internal routing         ← Route matching and execution
```

**Important**: Modifications to `src/core/` (config, database, monitoring, security, performance) require understanding the entire middleware chain, as changes can cascade through multiple layers.

### Core Infrastructure (src/core/)

- **config.py**: Pydantic Settings with environment validation. All configuration is type-safe and environment-aware (dev/prod).
- **database.py**: Async SQLAlchemy 2.x session factory. Connection pooling with automatic cleanup.
- **monitoring.py**: Custom metrics collection (request timing, slow queries, percentiles). Background cleanup tasks.
- **security.py**: Multi-dimensional rate limiting (token bucket + sliding window per IP/user/AI service/login attempts).
- **performance.py**: SQLAlchemy query listener for N+1 detection, slow query logging, and caching infrastructure.
- **logging.py**: Structured logging with `structlog`. All logs are JSON-formatted in production.

### AI Service Integration

All AI functionality goes through a unified service wrapper:

- **Location**: `src/services/bailian_service.py`
- **Purpose**: Encapsulates Alibaba Cloud Bailian AI agent calls
- **Features**:
  - Unified request/response models
  - Timeout control (30s default)
  - Retry logic with exponential backoff
  - Error normalization
  - Request logging for debugging

**Integration Points**:
- Homework grading: OCR + AI evaluation
- Learning Q&A: Contextual conversation
- Analytics: Knowledge point analysis

**Important**: Never call external AI APIs directly. Always use `BailianService` for consistency, monitoring, and error handling.

### Multi-Frontend Architecture

The backend serves multiple client types through a unified `/api/v1/` REST interface:

1. **Vue3 Web Frontend** (`frontend/`)
   - TypeScript + Composition API
   - Element Plus + Tailwind CSS
   - Vite dev server (port 5173)
   - Pinia for state management

2. **WeChat Miniprogram** (`miniprogram/`)
   - Vanilla JS with TypeScript declarations
   - Custom network layer (`miniprogram/utils/request.js`)
   - Shares same API endpoints

**API Response Format** (consistent across all clients):
```json
{
  "success": true,
  "data": { ... },
  "message": "OK"
}
```

**Error Format**:
```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "User-friendly description"
  }
}
```

---

## Key Development Patterns

### Repository Pattern with Generics

All repositories extend `BaseRepository[ModelType]` for type-safe CRUD:

```python
from src.repositories.base_repository import BaseRepository
from src.models.homework import HomeworkModel

class HomeworkRepository(BaseRepository[HomeworkModel]):
    async def find_by_student_id(
        self, 
        student_id: UUID
    ) -> List[HomeworkModel]:
        # Complex queries live here, not in services
        pass
```

**Key Points**:
- Generic typing ensures compile-time type safety
- All repositories are async
- Complex queries and aggregations belong in repositories
- Business logic stays in services

### Service Layer Composition

Services orchestrate multiple repositories and handle business logic:

```python
class HomeworkService:
    def __init__(
        self,
        homework_repo: HomeworkRepository,
        user_repo: UserRepository,
        bailian_service: BailianService,
    ):
        self.homework_repo = homework_repo
        self.user_repo = user_repo
        self.bailian_service = bailian_service
    
    async def grade_homework(
        self, 
        submission_id: UUID
    ) -> HomeworkCorrectionResponse:
        # 1. Fetch data (repository)
        # 2. Validate business rules (service)
        # 3. Call AI (BailianService)
        # 4. Persist results (repository)
        # 5. Return response (schema)
        pass
```

**Key Points**:
- Services never construct SQL directly
- Use dependency injection for repositories
- Handle transaction boundaries (commit/rollback)
- Convert between ORM models and Pydantic schemas

### Error Handling (Specific Exceptions Only)

```python
from src.core.exceptions import (
    HomeworkNotFoundError,
    ValidationError,
    AIServiceError
)

# ✅ CORRECT: Specific exception
try:
    result = await ai_service.grade(homework)
except AIServiceError as e:
    logger.error("AI grading failed", error=str(e))
    raise

# ❌ WRONG: Bare except
try:
    result = await ai_service.grade(homework)
except:  # Don't do this!
    pass
```

**Custom Exceptions** are defined in `src/core/exceptions.py` and mapped to appropriate HTTP status codes.

### Async/Await Throughout

- **Database**: All SQLAlchemy operations use async sessions
- **HTTP calls**: Use `httpx.AsyncClient` for external APIs
- **AI services**: All BailianService methods are async
- **Repository/Service**: All public methods are async

```python
# Session management
async with get_async_session() as session:
    repo = HomeworkRepository(session)
    result = await repo.get_by_id(homework_id)
```

---

## Critical Development Scripts

### scripts/diagnose.py
**Purpose**: Environment validation and diagnostics
**When to use**: 
- First thing when encountering any environment issues
- Before starting development
- After dependency updates

**What it checks**:
- Python version (≥ 3.11)
- uv installation and version
- Database connectivity
- Redis availability (optional)
- Environment variables
- File permissions

### scripts/start-dev.sh
**Purpose**: Start complete development environment
**Features**:
- Auto-installs dependencies if missing
- Intelligent port allocation (avoids conflicts)
- Starts both frontend (5173) and backend (8000)
- Health checks after startup
- Saves PIDs to `.dev-pids/` for management

**Logs**: 
- Frontend: `.dev-pids/frontend.log`
- Backend: `.dev-pids/backend.log`

### scripts/stop-dev.sh
**Purpose**: Gracefully stop all development services
**Options**:
- `--clean-logs`: Remove log files
- `--force`: Kill processes immediately

### scripts/status-dev.sh
**Purpose**: Check service health and performance
**Options**:
- `--verbose`: Show detailed process info (CPU, memory)
- `--watch`: Continuous monitoring (updates every 5s)

### scripts/manage_db.py
**Purpose**: Comprehensive database management
**Features**:
- Backup with rotation
- Restore from backup
- Generate sample data
- Schema inspection
- Performance analysis

**Usage**: `uv run python scripts/manage_db.py --help`

---

## Important Conventions

### Type Annotations (Mandatory)

All functions must have complete type annotations:

```python
# ✅ CORRECT
async def get_homework(
    homework_id: UUID,
    session: AsyncSession,
) -> HomeworkModel:
    """Fetch homework by ID."""
    pass

# ❌ WRONG: Missing types
async def get_homework(homework_id, session):
    pass
```

**Enforcement**: `mypy` in strict mode catches violations. `make type-check` must pass before commit.

### Function Length and Complexity

- **Max 60 lines** per function
- **Single responsibility** - one function, one purpose
- Complex functions should be broken into smaller helper functions

### Naming Conventions

- **Variables/Functions**: `snake_case` (e.g., `user_service`, `get_homework`)
- **Classes**: `PascalCase` (e.g., `HomeworkService`, `UserRepository`)
- **Constants**: `UPPER_SNAKE_CASE` (e.g., `DEFAULT_PAGE_SIZE`, `MAX_RETRIES`)
- **Private methods**: Prefix with `_` (e.g., `_validate_input`)

### Git Commit Format

```bash
<type>(<scope>): <description>

# Types:
feat     # New feature
fix      # Bug fix
docs     # Documentation
refactor # Code refactoring
test     # Testing
chore    # Maintenance

# Examples:
feat(homework): add AI-powered grading with explanations
fix(auth): correct JWT token expiration handling
docs(api): update homework endpoints documentation
refactor(repos): extract common query logic to base repository
```

### API Endpoint Design

- **List**: `GET /api/v1/resources`
- **Create**: `POST /api/v1/resources`
- **Detail**: `GET /api/v1/resources/{id}`
- **Update**: `PUT /api/v1/resources/{id}`
- **Delete**: `DELETE /api/v1/resources/{id}`

**Versioning**: All endpoints are under `/api/v1/` for future compatibility.

---

## Common Pitfalls

### 1. Don't Use `pip` or `poetry`
This project uses `uv` for package management. Always use:
- `uv sync` to install/update dependencies
- `uv run <command>` to execute Python scripts
- `uv add <package>` to add new dependencies

**Why**: `uv` is significantly faster and handles lock files more reliably.

### 2. Don't Skip Pre-Commit Checks
Running `make pre-commit` is not optional. It ensures:
- Code is properly formatted (Black, isort)
- Type checking passes (mypy)
- Tests pass
- No lint violations

**CI will fail** if pre-commit checks don't pass locally.

### 3. Don't Modify src/core/ Without Understanding Impact
Changes to core infrastructure (config, database, monitoring, security) affect:
- Middleware execution order
- Global error handling
- Performance monitoring
- Rate limiting

**Always**: Review `src/main.py` to understand the middleware stack before modifying core components.

### 4. Don't Call Repositories from API Layer
The API layer should only:
- Parse requests
- Call services
- Format responses

**Wrong**:
```python
@router.get("/homework/{id}")
async def get_homework(id: UUID, session: AsyncSession):
    repo = HomeworkRepository(session)
    return await repo.get_by_id(id)  # Bypasses service layer!
```

**Correct**:
```python
@router.get("/homework/{id}")
async def get_homework(
    id: UUID, 
    service: HomeworkService = Depends(get_homework_service)
):
    return await service.get_homework(id)
```

### 5. Don't Use scripts/start-dev.sh in Production
The development scripts are for local development only. Production uses:
- Docker containers
- `docker-compose.yml` for orchestration
- Environment-specific configs (`.env.prod`)

---

## Testing Strategy

### Test Organization

```
tests/
├── unit/          # Fast, isolated tests (services, repositories)
├── integration/   # API endpoint tests with test database
└── performance/   # Load testing and benchmarks
```

### Running Tests

```bash
# All tests
make test

# Specific category
make test-unit
make test-integration

# Single test file
uv run pytest tests/unit/test_homework_service.py -v

# Tests matching pattern
uv run pytest tests/ -k "homework" -v

# With coverage
make test-coverage
```

### Test Database

Integration tests use a separate test database (automatically created):
- SQLite for local testing (fast, no setup)
- PostgreSQL for CI/CD (production-like)

**Fixture**: `tests/conftest.py` provides `test_db` fixture with automatic cleanup.

---

## Performance Targets

Monitor these via `/api/v1/health/performance`:

- **API Response Time**: P95 < 200ms
- **Database Queries**: P95 < 50ms  
- **AI Service Calls**: P95 < 3s

**Slow Query Logging**: Queries >500ms are automatically logged with full SQL and execution plan.

---

## Key Documentation Files

- **AI-CONTEXT.md**: Quick reference for AI assistants (comprehensive)
- **docs/architecture/overview.md**: Detailed system architecture and design decisions
- **docs/guide/development.md**: Complete development workflow guide
- **docs/api/**: API endpoint specifications and examples
- **.github/copilot-instructions.md**: GitHub Copilot-specific guidance

---

## When Things Break

1. **Run diagnostics**: `uv run python scripts/diagnose.py`
2. **Check service status**: `./scripts/status-dev.sh --verbose`
3. **Review logs**: 
   - Backend: `tail -f .dev-pids/backend.log`
   - Frontend: `tail -f .dev-pids/frontend.log`
4. **Check port conflicts**: `lsof -i :8000` (backend) or `lsof -i :5173` (frontend)
5. **Force cleanup**: `./scripts/stop-dev.sh --force`
6. **Restart fresh**: `./scripts/restart-dev.sh`

**Still stuck?** Check project issues or refer to `docs/history/` for past solutions.

---

## Project-Specific Notes

### uv Package Manager
This project uses `uv` instead of pip/poetry/pipenv. All Python commands should be prefixed with `uv run`:

```bash
uv run python script.py
uv run pytest tests/
uv run alembic upgrade head
```

### Database Migrations
After modifying any model in `src/models/`:
1. Generate migration: `make db-migrate`
2. Review generated file in `alembic/versions/`
3. Apply migration: `make db-upgrade`

**Never** manually edit migration files unless absolutely necessary.

### Environment Variables
Multiple environment files exist:
- `.env.dev` - Development (SQLite, debug enabled)
- `.env.prod` - Production (PostgreSQL, optimized)
- `.env.docker.production` - Docker production config

**Copy the appropriate one** to `.env` before starting.

### Secrets Management
- Never commit `.env` files
- Production secrets go in `secrets/` directory (gitignored)
- Use `scripts/env_manager.py` for safe secret management

---

**Last Updated**: 2025-10-04  
**Maintained By**: Liguo Ma <maliguo@outlook.com>
