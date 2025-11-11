# AGENTS.md

This file provides guidance to Qoder (qoder.com) when working with code in this repository.

## Project Overview

**五好伴学 (Wuhao Tutor)** - K12 AI-powered learning platform with homework Q&A, mistake notebook, knowledge graph, and learning analytics.

- **Tech Stack**: FastAPI + Vue3 + WeChat MiniProgram + PostgreSQL + Redis + Alibaba Cloud Bailian AI
- **Production**: https://www.horsduroot.com (121.199.173.244)
- **Version**: v0.1.0
- **Python**: 3.11+
- **Multi-platform**: Web frontend + WeChat MiniProgram (both in production)

## Common Commands

### Development

```bash
# Backend development
make dev                    # Start backend server (port 8000)
uv run python src/main.py   # Alternative backend start
./scripts/start-dev.sh      # Start both frontend and backend

# Frontend development
cd frontend && npm run dev  # Start frontend (port 5173)

# Database migrations
make db-init                # Apply all migrations
make db-migrate             # Create new migration (prompts for description)
make db-upgrade             # Apply migrations
make db-downgrade           # Rollback one migration
make db-reset               # DANGEROUS: Reset entire database
```

### Code Quality

```bash
# Linting and formatting
make lint                   # Run flake8 + black + isort checks
make format                 # Format code with black + isort
make type-check             # Run mypy type checking
make check-all              # Run all checks (lint + type-check)

# Frontend quality
cd frontend && npm run lint        # ESLint
cd frontend && npm run type-check  # vue-tsc
cd frontend && npm run format      # Prettier
```

### Testing

```bash
# Backend tests
make test                   # Run all tests
make test-unit              # Unit tests only
make test-integration       # Integration tests only
make test-coverage          # Generate coverage report (see htmlcov/)

# Frontend tests
cd frontend && npm run test          # Run vitest
cd frontend && npm run test:coverage # With coverage
```

### Deployment

```bash
./scripts/deploy.sh         # Production deployment (builds frontend + deploys backend)
journalctl -u wuhao-tutor.service -f  # View production logs
```

## Architecture

### Four-Layer Strict Separation

The backend follows a strict 4-layer architecture. **NEVER skip layers** (e.g., API → Repository).

```
API Layer → Service Layer → Repository Layer → Model Layer
```

**Rules**:
- **API Layer** (`src/api/v1/endpoints/`): HTTP request handling, parameter validation, response formatting (19 files, 50+ endpoints)
- **Service Layer** (`src/services/`): Business logic, transaction management, multi-repository coordination
  - `BailianService` (1000+ lines): AI service integration
  - `LearningService` (2400+ lines): Q&A business logic
  - `MistakeService` (1260+ lines): Mistake notebook
  - `KnowledgeGraphService`, `AnalyticsService`, `AuthService`, etc.
- **Repository Layer** (`src/repositories/`): Data access, complex queries, data transformation
  - All repositories extend `BaseRepository[ModelType]` generic
- **Model Layer** (`src/models/`): Database models (11 models), all inherit from `BaseModel` with UUID + timestamps

### Core Infrastructure (`src/core/`)

- `config.py`: Pydantic Settings v2 for environment config
- `database.py`: SQLAlchemy 2.x async engine + connection pooling
- `security.py`: JWT auth + multi-layer rate limiting (Token Bucket + Sliding Window)
- `monitoring.py`: Performance metrics collection (response time, error rate)
- `performance.py`: Slow query listener (>1.0s) + N+1 detection
- `exceptions.py`: Unified exception hierarchy (20+ types)

**DO NOT modify core infrastructure** unless you fully understand the implications.

### Database

- **Development**: SQLite (local file)
- **Production**: PostgreSQL 14+ (Alibaba Cloud RDS)
- **ORM**: SQLAlchemy 2.x with async support (`asyncpg` for PostgreSQL, `aiosqlite` for SQLite)
- **Migrations**: Alembic (~15 migration files in `alembic/versions/`)
- **Cache**: Redis 6+ for rate limiting, refresh tokens, session cache

**Migration Workflow**:
1. Modify model in `src/models/`
2. Run `make db-migrate` (generates migration with description prompt)
3. Review generated migration in `alembic/versions/`
4. Run `make db-init` to apply
5. Test rollback with `make db-downgrade`

### AI Service Integration

**Alibaba Cloud Bailian** (阿里云百炼):
- **Service**: `BailianService` (`src/services/bailian_service.py`)
- **Model**: Qwen (Tongyi Qianwen) large language model
- **Features**: Learning Q&A, homework correction, knowledge extraction
- **Timeout**: 120s (supports image OCR)
- **Retry**: 3 attempts with exponential backoff
- **Streaming**: Server-Sent Events (SSE) for real-time responses

**Environment Variables** (`.env`):
- `BAILIAN_API_KEY=sk-xxx` (MUST start with `sk-` in production)
- `BAILIAN_APPLICATION_ID=xxx`

**DO NOT**:
- Make direct HTTP calls to AI services (always use `BailianService`)
- Skip retry logic or timeout configuration

### Frontend Architecture

**Web Frontend** (`frontend/`):
- **Framework**: Vue 3.4+ (Composition API) + TypeScript 5.6+
- **UI Library**: Element Plus 2.5+
- **Build Tool**: Vite 5+
- **State Management**: Pinia 2.1+
- **Router**: Vue Router 4.x
- **HTTP Client**: Axios 1.6+
- **Math Rendering**: KaTeX 0.16+ (LaTeX formulas)
- **Markdown**: marked 16.x + highlight.js
- **Charts**: ECharts 6.0 + vue-echarts

**WeChat MiniProgram** (`miniprogram/`):
- **Language**: Native JavaScript + TypeScript declarations
- **Framework**: WeChat MiniProgram native API
- **UI**: WeChat native components + custom components
- **Network**: Custom request wrapper (`utils/request.js`)
- **API**: Connects to production environment (horsduroot.com)
- **Pages**: 15+ pages (learning, mistakes, profile, analysis)

## Development Best Practices

### Code Style

- **Type annotations**: Required for all functions (mypy strict mode)
- **Exception handling**: Use specific exceptions (NEVER `except:` or `except Exception:`)
- **Function length**: ≤ 60 lines, single responsibility
- **Docstrings**: Google style for complex logic
- **Async**: All I/O operations must use `async/await`

**Example** (reference `src/services/mistake_service.py`):

```python
async def create_mistake(
    self, db: AsyncSession, user_id: UUID
) -> MistakeDetailResponse:
    """
    Create a new mistake record.
    
    Args:
        db: Database session
        user_id: User UUID
        
    Returns:
        Created mistake detail
        
    Raises:
        ServiceError: If creation fails
    """
    try:
        # Implementation...
    except SpecificError as e:  # Specific exception
        raise ServiceError(f"Failed to create mistake: {e}")
```

### Repository Pattern

All repositories must:
- Extend `BaseRepository[ModelType]` generic
- Encapsulate data access logic
- Use SQLAlchemy async API (`select()`, `update()`, `delete()`)
- Handle database errors appropriately

### Service Layer Transactions

Services handle transactions and business logic:
- Use `async with db.begin()` for explicit transactions
- Coordinate multiple repositories
- Implement business rules and validation

### Model Standards

All models must:
- Inherit from `BaseModel` (provides UUID `id`, `created_at`, `updated_at`)
- Use SQLAlchemy 2.x declarative style
- Include proper relationships with lazy loading
- Define indexes for frequently queried columns

## Security & Performance

### Rate Limiting (Multi-Layer)

- **IP Level**: 100 requests/minute (Token Bucket) - DDoS protection
- **User Level**: 50 requests/minute (Token Bucket) - abuse prevention
- **AI Service**: 20 requests/minute (Sliding Window) - cost control
- **Login Endpoint**: 10 requests/minute (Token Bucket) - brute force protection

### Authentication

- **JWT**: Access Token (8 days) + Refresh Token (30 days)
- **Password**: bcrypt with 12 rounds
- **Token Storage**: Refresh tokens in Redis
- **Auto-renewal**: Access token refresh mechanism

### Middleware Stack (Execution Order)

1. `PerformanceMonitoringMiddleware` - metrics collection
2. `SecurityHeadersMiddleware` - CSP, HSTS, X-Frame-Options
3. `RateLimitMiddleware` - rate limiting
4. `CORSMiddleware` - CORS handling
5. `TrustedHostMiddleware` - host validation
6. `LoggingMiddleware` - request/response logging

### Performance Monitoring

- **Slow queries**: Automatically logged if >1.0s
- **N+1 detection**: Warns about N+1 query patterns
- **Metrics collection**: Response time, error rate, system resources
- **System monitoring**: CPU, memory, disk usage

## Environment Configuration

**Environments**:
- **Dev**: SQLite local database
- **Test**: In-memory SQLite
- **Prod**: PostgreSQL + Redis

**Critical Environment Variables** (`.env`):
```bash
# Required in production
BAILIAN_API_KEY=sk-xxx              # Must start with sk-
BAILIAN_APPLICATION_ID=xxx
SQLALCHEMY_DATABASE_URI=xxx
SECRET_KEY=xxx                      # Must be changed for production
REDIS_HOST=localhost                # Optional in dev

# Database
DATABASE_URL=postgresql+asyncpg://user:pass@host/db  # Production

# Security
ACCESS_TOKEN_EXPIRE_DAYS=8
REFRESH_TOKEN_EXPIRE_DAYS=30
```

## Production Deployment

**Deployment Process**:
1. Run `./scripts/deploy.sh` (builds frontend locally, deploys to server)
2. Verify: `curl https://horsduroot.com/health`
3. Check logs: `journalctl -u wuhao-tutor.service -f`

**Deployment Structure**:
- Backend: `/opt/wuhao-tutor`
- Frontend: `/var/www/html`
- Logs: `/var/log/wuhao-tutor`
- Config: `/opt/wuhao-tutor/.env.production`

**Critical Deployment Rules**:
- ❌ **NEVER** use `start-dev.sh` in production → use `deploy.sh`
- ❌ **NEVER** skip Alembic migrations → run `make db-migrate` + `make db-init`
- ❌ **NEVER** hardcode secrets → use environment variables
- ✅ **ALWAYS** test migrations locally before deploying
- ✅ **ALWAYS** run lint + type-check before deploying

## Testing Strategy

**Unit Tests**: Services and Repositories
- Mock external dependencies (AI services, Redis)
- Test business logic in isolation
- Use `MockBailianService` for AI service testing

**Integration Tests**: API endpoints
- Test full request/response cycle
- Use test database (in-memory SQLite)
- Verify authentication and authorization

**Performance Tests**: Load testing
- Available via `make test-performance`
- Monitor response times and resource usage

## Important Constraints

1. **Strict Layering**: API → Service → Repository → Model (no layer skipping)
2. **Async Everywhere**: All I/O operations must use `async/await`
3. **Type Safety**: Full type annotations + mypy strict checking
4. **Configuration Externalization**: Environment variables only, no hardcoded values
5. **Database Changes**: Always use Alembic migrations (never direct schema changes)

## Common Pitfalls

❌ **API directly calling Repository** → Must go through Service layer
❌ **Sync code in async context** → Use `async/await` for all I/O
❌ **Generic exception handling** → Use specific exception types
❌ **Skipping migrations** → Always generate and review migrations
❌ **Hardcoded API keys** → Use environment variables
❌ **Missing type annotations** → mypy will fail
❌ **Long functions (>60 lines)** → Break into smaller functions

## Key Files Reference

- Architecture: Read `.github/copilot-instructions.md` for detailed guidelines
- Development status: `DEVELOPMENT_STATUS.md`
- Changelog: `CHANGELOG.md`
- API docs: `docs/api/` directory
- Database schema: `docs/database/` directory
