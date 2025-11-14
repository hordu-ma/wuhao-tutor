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

```
API Layer → Service Layer → Repository Layer → Model Layer
```

**Key Services**:

- `BailianService`: AI service integration
- `LearningService`: Q&A business logic (2400+ lines)
- `MistakeService`: Mistake notebook (1260+ lines)
- `KnowledgeGraphService`, `AnalyticsService`, `AuthService`

**Core Infrastructure** (`src/core/`): config, database, security, monitoring, performance, exceptions

⚠️ **See `.github/copilot-instructions.md` for detailed architecture rules and constraints.**

### Database

- **Development**: SQLite (local file)
- **Production**: PostgreSQL 14+ (Alibaba Cloud RDS)
- **ORM**: SQLAlchemy 2.x async (`asyncpg` / `aiosqlite`)
- **Migrations**: Alembic (`make db-migrate` → `make db-init`)
- **Cache**: Redis 6+ (rate limiting, tokens, sessions)

### AI Service Integration

**Alibaba Cloud Bailian** (阿里云百炼):

- Service: `BailianService` (Q&A, homework correction, knowledge extraction)
- Model: Qwen (Tongyi Qianwen)
- Config: 120s timeout, 3 retries, SSE streaming
- Env: `BAILIAN_API_KEY=sk-xxx`, `BAILIAN_APPLICATION_ID=xxx`

⚠️ Always use `BailianService` wrapper, never direct HTTP calls.

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

- **Type annotations**: Required (mypy strict)
- **Exception handling**: Specific exceptions only (see `.github/copilot-instructions.md` for exceptions)
- **Function length**: ≤ 60 lines
- **Docstrings**: Google style
- **Async**: All I/O must use `async/await`

### Patterns

- **Repository**: Extend `BaseRepository[ModelType]`, encapsulate data access
- **Service**: Handle business logic, transactions, multi-repository coordination
- **Model**: Inherit from `BaseModel` (UUID + timestamps)

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

### Rate Limiting

- IP: 100/min | User: 50/min | AI: 20/min | Login: 10/min

### Authentication

- JWT: Access Token (8d) + Refresh Token (30d)
- Password: bcrypt (12 rounds)
- Storage: Redis

### Monitoring

- Slow queries: >1.0s logged
- N+1 detection enabled
- Metrics: response time, error rate, resources

## Environment Configuration

**Environments**: Dev (SQLite) | Test (In-memory SQLite) | Prod (PostgreSQL + Redis)

**Key Variables** (`.env`): See `.github/copilot-instructions.md` for complete list

- `BAILIAN_API_KEY=sk-xxx` (must start with `sk-` in prod)
- `BAILIAN_APPLICATION_ID=xxx`
- `SECRET_KEY=xxx` (change for prod)
- `DATABASE_URL=postgresql+asyncpg://...` (prod only)

## Production Deployment

**Process**: `./scripts/deploy.sh` → Verify: `curl https://horsduroot.com/health`

**Structure**: Backend (`/opt/wuhao-tutor`) | Frontend (`/var/www/html`) | Logs (`/var/log/wuhao-tutor`)

**Critical Rules**: See `.github/copilot-instructions.md` for detailed deployment guidelines

## Testing Strategy

- **Unit**: Mock external dependencies, test business logic
- **Integration**: Full request/response cycle, test database
- **Performance**: `make test-performance`

## Important Constraints

See `.github/copilot-instructions.md` for detailed constraints:

- Strict 4-layer architecture (no layer skipping)
- Full async/await for I/O
- Type annotations required (mypy strict)
- Environment variables only (no hardcoded values)
- Alembic for all database changes

## Common Pitfalls

⚠️ See `.github/copilot-instructions.md` for complete list. Key pitfalls:

- ❌ Layer skipping (API → Repository)
- ❌ Sync code in async context
- ❌ Generic exception handling
- ❌ Hardcoded secrets

## Key Files Reference

- Architecture: Read `.github/copilot-instructions.md` for detailed guidelines
- Development status: `DEVELOPMENT_STATUS.md`
- Changelog: `CHANGELOG.md`
- API docs: `docs/api/` directory
- Database schema: `docs/database/` directory
