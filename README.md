# HandyMan Backend API

A FastAPI-based backend for the HandyMan gig economy platform providing on-demand home services.

## Features

- **RESTful API** with FastAPI
- **PostgreSQL + PostGIS** for geospatial queries
- **AI-Powered Services** for job matching and pricing
- **JWT Authentication** for secure access
- **WebSocket Support** for real-time updates
- **Comprehensive Test Suite** with pytest

## Tech Stack

- **Framework**: FastAPI 0.109.0
- **Database**: PostgreSQL with PostGIS extension
- **ORM**: SQLAlchemy 2.0
- **Authentication**: JWT (python-jose)
- **AI/ML**: PyTorch, OpenAI, OpenCV
- **Testing**: pytest with coverage

## Prerequisites

- Python 3.11+
- PostgreSQL 14+ with PostGIS extension
- Redis (optional, for caching)

## Installation

### 1. Clone and Setup

```bash
cd handyman-backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
pip install -r requirements-test.txt  # For testing
```

### 3. Database Setup

```bash
# Install PostgreSQL and PostGIS
brew install postgresql postgis  # macOS
# or
sudo apt-get install postgresql postgis  # Ubuntu

# Create database
createdb handyman_db
psql handyman_db -c "CREATE EXTENSION postgis;"

# Run migrations
alembic upgrade head
```

### 4. Environment Configuration

```bash
cp .env.example .env
# Edit .env with your configuration
```

Required environment variables:
```
DATABASE_URL=postgresql://user:password@localhost/handyman_db
SECRET_KEY=your-secret-key-here
OPENAI_API_KEY=your-openai-key
```

### 5. Start Server

```bash
# Development
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Production
uvicorn app.main:app --workers 4 --host 0.0.0.0 --port 8000
```

## API Documentation

Once running, access:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

## Testing

### Run All Tests

```bash
pytest
```

### Run with Coverage

```bash
pytest --cov=app --cov-report=html
```

### Run Specific Test File

```bash
pytest tests/test_auth.py -v
```

### Run Tests in Parallel

```bash
pip install pytest-xdist
pytest -n auto
```

## Project Structure

```
handyman-backend/
├── app/
│   ├── main.py              # FastAPI app entry point
│   ├── config.py            # Configuration settings
│   ├── database.py          # Database connection
│   ├── api/                 # API endpoints
│   │   ├── auth.py         # Authentication routes
│   │   ├── jobs.py         # Job management routes
│   │   ├── providers.py    # Provider routes
│   │   └── locations.py    # Location/search routes
│   ├── services/            # Business logic
│   │   ├── auth_service.py
│   │   ├── job_service.py
│   │   └── matching_service.py
│   ├── ai/                  # AI/ML modules
│   │   ├── cv_module.py    # Computer vision
│   │   ├── llm_parser.py   # LLM integration
│   │   └── pricing_agent.py
│   ├── schemas/             # Pydantic models
│   └── models/              # SQLAlchemy models
├── tests/                   # Test suite
│   ├── conftest.py         # Test fixtures
│   ├── test_main.py
│   ├── test_auth.py
│   ├── test_jobs.py
│   └── test_providers.py
├── alembic/                 # Database migrations
├── requirements.txt
├── requirements-test.txt
└── pytest.ini

```

## API Endpoints

### Authentication
- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/login` - Login and get JWT token
- `GET /api/v1/auth/me` - Get current user info

### Jobs
- `POST /api/v1/jobs` - Create new job
- `GET /api/v1/jobs` - List jobs (with filters)
- `GET /api/v1/jobs/{id}` - Get job details
- `PATCH /api/v1/jobs/{id}` - Update job
- `DELETE /api/v1/jobs/{id}` - Delete job
- `GET /api/v1/jobs/search` - Search jobs by location

### Providers
- `POST /api/v1/providers/profile` - Create provider profile
- `GET /api/v1/providers/me` - Get provider profile
- `PATCH /api/v1/providers/me` - Update provider profile
- `GET /api/v1/providers/available-jobs` - Get nearby jobs
- `POST /api/v1/providers/jobs/{id}/accept` - Accept job
- `POST /api/v1/providers/jobs/{id}/complete` - Complete job

## Development

### Code Style

```bash
# Format code
black app tests

# Lint
flake8 app tests

# Type check
mypy app
```

### Database Migrations

```bash
# Create new migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

## Deployment

See [DEPLOYMENT.md](../DEPLOYMENT.md) for detailed deployment instructions to various platforms.

### Quick Deploy Options

1. **Render** (Free tier available)
2. **Railway** (Free tier with credit)
3. **Fly.io** (Free tier available)
4. **Heroku** (Free tier discontinued, paid plans available)

## Performance

- **Database Connection Pooling**: Configured via SQLAlchemy
- **Redis Caching**: Optional for frequently accessed data
- **Async Operations**: All database operations use asyncio
- **Rate Limiting**: Implement with slowapi (optional)

## Security

- JWT token authentication
- Password hashing with Argon2
- CORS configuration
- SQL injection prevention via ORM
- Input validation with Pydantic

## Monitoring

Add optional monitoring with:
- **Sentry**: Error tracking
- **Prometheus**: Metrics
- **Grafana**: Dashboards

## Contributing

1. Create feature branch
2. Write tests for new features
3. Ensure tests pass: `pytest`
4. Check coverage: `pytest --cov=app`
5. Submit pull request

## License

MIT License

## Support

For issues and questions, please open an issue on GitHub.
