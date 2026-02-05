# Medical Chatbot API

A production-ready, enterprise-grade Medical Chatbot API built with FastAPI, LangChain, and Llama 2. This application uses Retrieval-Augmented Generation (RAG) to provide accurate medical information based on a curated knowledge base.

## Table of Contents

1. [Features](#features)
2. [Architecture](#architecture)
3. [Prerequisites](#prerequisites)
4. [Quick Start](#quick-start)
5. [Installation](#installation)
6. [Configuration](#configuration)
7. [Running the Application](#running-the-application)
8. [API Documentation](#api-documentation)
9. [Docker Deployment](#docker-deployment)
10. [Kubernetes Deployment](#kubernetes-deployment)
11. [Testing](#testing)
12. [Monitoring](#monitoring)
13. [Security](#security)
14. [Contributing](#contributing)
15. [License](#license)

## Features

### Core Functionality

- Medical question-answering using Llama 2 LLM
- RAG (Retrieval-Augmented Generation) architecture
- Vector search using Pinecone
- Conversation history tracking
- Session management

### Security (8+ Components)

- JWT authentication with access and refresh tokens
- Token bucket rate limiting algorithm
- Pydantic v2 input validation
- CORS with restrictive origin configuration
- Environment-based secret management
- Input sanitization (XSS, SQL injection, command injection prevention)
- Global exception handling with proper HTTP status codes
- Non-root container execution

### Monitoring and Observability (7+ Components)

- Prometheus metrics collection (15+ metric types)
- Structured JSON logging with custom formatter
- Request tracking with unique request IDs
- Performance tracking (latency histograms)
- Health check endpoints (liveness, readiness, comprehensive)
- Audit logging for predictions and security events
- Grafana dashboard integration support

### Testing and Code Quality (6+ Components)

- Pytest framework with 25+ test cases
- Unit tests for utilities, exceptions, schemas
- Integration tests for all API endpoints
- Black code formatter
- Flake8, MyPy, Pylint linting
- Pre-commit hooks for automated quality checks

### Configuration Management (4+ Components)

- Centralized Pydantic Settings class
- Type-safe configuration with validation
- Environment-specific configs (dev, staging, production)
- Comprehensive .env.example template

### Database (3+ Components)

- MongoDB with async motor driver
- Connection pooling (min 10, max 50 connections)
- Singleton pattern for shared connections
- Health checks and graceful closure

### Deployment (5+ Components)

- Multi-stage production Dockerfile
- Development Dockerfile with hot-reload
- Docker Compose for full stack
- Kubernetes manifests (Deployment, Service, HPA, NetworkPolicy, Ingress)
- GitHub Actions CI/CD pipeline

## Architecture

```
+------------------+     +------------------+     +------------------+
|                  |     |                  |     |                  |
|   Client/User    +---->+   FastAPI App    +---->+   MongoDB        |
|                  |     |                  |     |                  |
+------------------+     +--------+---------+     +------------------+
                                  |
                                  |
                         +--------v---------+
                         |                  |
                         |   LangChain      |
                         |   + Llama 2      |
                         |                  |
                         +--------+---------+
                                  |
                                  |
                         +--------v---------+
                         |                  |
                         |   Pinecone       |
                         |   Vector DB      |
                         |                  |
                         +------------------+
```

### Project Structure

```
medical-chatbot/
|-- app/
|   |-- __init__.py
|   |-- main.py                 # FastAPI application entry point
|   |-- api/
|   |   |-- __init__.py
|   |   |-- dependencies.py     # Dependency injection
|   |   |-- schemas.py          # Pydantic models
|   |   |-- routes/
|   |       |-- __init__.py
|   |       |-- auth.py         # Authentication endpoints
|   |       |-- chat.py         # Chat endpoints
|   |       |-- health.py       # Health check endpoints
|   |-- core/
|   |   |-- __init__.py
|   |   |-- config.py           # Configuration management
|   |   |-- exceptions.py       # Custom exceptions
|   |   |-- logging.py          # Structured logging
|   |   |-- metrics.py          # Prometheus metrics
|   |   |-- security.py         # Security utilities
|   |-- db/
|   |   |-- __init__.py
|   |   |-- mongodb.py          # MongoDB connection
|   |-- middleware/
|   |   |-- __init__.py
|   |   |-- request_handler.py  # Request middleware
|   |-- services/
|       |-- __init__.py
|       |-- chatbot.py          # Chatbot service
|-- tests/
|   |-- __init__.py
|   |-- conftest.py             # Test fixtures
|   |-- test_*.py               # Test modules
|-- k8s/                        # Kubernetes manifests
|-- prometheus/                 # Prometheus configuration
|-- grafana/                    # Grafana dashboards
|-- scripts/                    # Utility scripts
|-- Dockerfile                  # Production Dockerfile
|-- Dockerfile.dev              # Development Dockerfile
|-- docker-compose.yml          # Development stack
|-- docker-compose.prod.yml     # Production stack
|-- requirements.txt            # Production dependencies
|-- requirements-dev.txt        # Development dependencies
|-- requirements-prod.txt       # Optimized production deps
|-- pyproject.toml              # Project configuration
|-- .env.example                # Environment template
|-- README.md                   # This file
|-- CONTRIBUTING.md             # Contribution guidelines
|-- DEPLOYMENT.md               # Deployment guide
|-- PRODUCTION_READY.md         # Production checklist
```

## Demo

![Screenshot demo1](https://github.com/Mutiu123/End-to-end-Medical-Chatbot-Implementation-using-Llama2/blob/main/demo/demo1.png)

![Screenshot demo2](https://github.com/Mutiu123/End-to-end-Medical-Chatbot-Implementation-using-Llama2/blob/main/demo/demo2.png)

![Screenshot demo3](https://github.com/Mutiu123/End-to-end-Medical-Chatbot-Implementation-using-Llama2/blob/main/demo/demo3.png)


## Prerequisites

- Python 3.11 or higher
- Docker and Docker Compose (for containerized deployment)
- MongoDB 7.0+ (local or MongoDB Atlas)
- Pinecone account and API key
- Llama 2 model file (llama-2-7b-chat.ggmlv3.q4_0.bin)

## Quick Start

### Using Docker Compose (Recommended)

```bash
# Clone the repository
git clone https://github.com/Mutiu123/End-to-end-Medical-Chatbot-Implementation-using-Llama2.git
cd End-to-end-Medical-Chatbot-Implementation-using-Llama2

# Copy environment template
cp .env.example .env

# Edit .env with your configuration (especially PINECONE_API_KEY)

# Download the Llama 2 model
mkdir -p model
# Download llama-2-7b-chat.ggmlv3.q4_0.bin from HuggingFace to model/

# Start the application
docker-compose up -d

# Access the API
curl http://localhost:8080/api/v1/health
```

## Installation

### Local Development Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/macOS
# or
venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install

# Copy and configure environment
cp .env.example .env
# Edit .env with your settings
```

### Download the LLM Model

Download the Llama 2 model from HuggingFace:

```bash
mkdir -p model
cd model
# Download from: https://huggingface.co/TheBloke/Llama-2-7B-Chat-GGML/tree/main
# File: llama-2-7b-chat.ggmlv3.q4_0.bin
```

### Initialize Vector Store

```bash
python store_index.py
```

## Configuration

### Environment Variables

Create a `.env` file based on `.env.example`:

```ini
# Application
ENVIRONMENT=development
DEBUG=true
SECRET_KEY=your-secure-secret-key

# MongoDB
MONGODB_URI=mongodb://localhost:27017
MONGODB_DATABASE=medical_chatbot

# Pinecone
PINECONE_API_KEY=your-pinecone-api-key
PINECONE_ENVIRONMENT=your-pinecone-environment

# LLM
LLM_MODEL_PATH=model/llama-2-7b-chat.ggmlv3.q4_0.bin

# See .env.example for all options
```

### Configuration Classes

The application uses Pydantic Settings for type-safe configuration:

- `DevelopmentSettings` - Debug enabled, verbose logging
- `StagingSettings` - Production-like with more logging
- `ProductionSettings` - Optimized for production

## Running the Application

### Development Mode

```bash
# With hot-reload
uvicorn app.main:app --reload --port 8080

# Or using the main module
python -m app.main
```

### Production Mode

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8080 --workers 4
```

### Using Docker

```bash
# Development
docker-compose up -d

# Production
docker-compose -f docker-compose.prod.yml up -d
```

## API Documentation

### Base URL

```
http://localhost:8080/api/v1
```

### Endpoints

#### Health Checks

```bash
# Liveness probe
GET /api/v1/live

# Readiness probe
GET /api/v1/ready

# Comprehensive health
GET /api/v1/health

# Prometheus metrics
GET /api/v1/metrics
```

#### Authentication

```bash
# Register
POST /api/v1/auth/register
{
  "username": "johndoe",
  "email": "john@example.com",
  "password": "SecurePass123!"
}

# Login
POST /api/v1/auth/login
{
  "username": "johndoe",
  "password": "SecurePass123!"
}

# Refresh token
POST /api/v1/auth/refresh
{
  "refresh_token": "your-refresh-token"
}

# Get current user
GET /api/v1/auth/me
Authorization: Bearer <access_token>
```

#### Chat

```bash
# Send query
POST /api/v1/chat/query
{
  "query": "What are the symptoms of diabetes?",
  "session_id": "optional-session-id",
  "include_sources": true
}

# Get conversation history
GET /api/v1/chat/history/{session_id}

# Delete conversation
DELETE /api/v1/chat/history/{session_id}
```

### OpenAPI Documentation

When running in development mode, access interactive documentation:

- Swagger UI: http://localhost:8080/docs
- ReDoc: http://localhost:8080/redoc

## Docker Deployment

### Build Images

```bash
# Production image
docker build -t medical-chatbot:latest .

# Development image
docker build -f Dockerfile.dev -t medical-chatbot:dev .
```

### Run with Docker Compose

```bash
# Start all services (app, MongoDB, Prometheus, Grafana)
docker-compose up -d

# View logs
docker-compose logs -f app

# Stop services
docker-compose down
```

### Services

| Service | Port | Description |
|---------|------|-------------|
| app | 8080 | Medical Chatbot API |
| mongodb | 27017 | MongoDB database |
| prometheus | 9090 | Metrics collection |
| grafana | 3000 | Dashboards |

## Kubernetes Deployment

### Prerequisites

- kubectl configured
- Kubernetes cluster (local or cloud)

### Deploy

```bash
# Create namespace
kubectl apply -f k8s/namespace.yaml

# Create secrets (edit first!)
kubectl apply -f k8s/secret.yaml

# Deploy all resources
kubectl apply -f k8s/

# Verify deployment
kubectl get pods -n medical-chatbot
kubectl get svc -n medical-chatbot
```

### Components

- **Deployment**: 3 replicas with rolling updates
- **Service**: ClusterIP for internal access
- **HPA**: Auto-scaling (3-10 replicas)
- **Ingress**: External access with TLS
- **NetworkPolicy**: Network segmentation

## Testing

### Run Tests

```bash
# All tests
pytest

# With coverage
pytest --cov=app --cov-report=html

# Specific test file
pytest tests/test_security.py -v

# Run in parallel
pytest -n auto
```

### Test Categories

- `test_config.py` - Configuration tests
- `test_security.py` - Security module tests
- `test_exceptions.py` - Exception handling tests
- `test_schemas.py` - Pydantic schema tests
- `test_api_endpoints.py` - API integration tests

## Monitoring

### Prometheus Metrics

Access metrics at `/api/v1/metrics`:

- `medical_chatbot_requests_total` - Request counter
- `medical_chatbot_request_latency_seconds` - Latency histogram
- `medical_chatbot_llm_inference_latency_seconds` - LLM latency
- `medical_chatbot_db_connections` - Database connections
- `medical_chatbot_chat_queries_total` - Chat queries

### Grafana Dashboards

Access Grafana at http://localhost:3000 (admin/admin):

1. Import dashboards from `grafana/dashboards/`
2. Configure Prometheus data source

### Health Checks

```bash
# Quick health check
curl http://localhost:8080/api/v1/live

# Detailed health check
curl http://localhost:8080/api/v1/health | jq
```

## Security

### Features

- JWT authentication with RS256/HS256
- Password hashing with bcrypt (12 rounds)
- Rate limiting (token bucket algorithm)
- Input validation and sanitization
- CORS configuration
- Security headers
- Non-root container execution

### Best Practices

1. Use strong SECRET_KEY (32+ characters)
2. Enable HTTPS in production
3. Configure restrictive CORS origins
4. Enable rate limiting
5. Regular security updates
6. Audit logging enabled

See [PRODUCTION_READY.md](PRODUCTION_READY.md) for complete security checklist.

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for:

- Development setup
- Code standards
- Testing guidelines
- Pull request process

## Deployment Guide

For detailed deployment instructions, see [DEPLOYMENT.md](DEPLOYMENT.md):

- Local development
- Docker deployment
- Kubernetes deployment
- AWS EKS deployment
- Configuration management

## Technical Documentation

For in-depth architecture documentation and visual diagrams, see the [docs/tutorial](docs/tutorial/) folder:

| Document | Description |
|----------|-------------|
| [PROJECT_STAR_METHOD.md](docs/tutorial/PROJECT_STAR_METHOD.md) | Complete project description using STAR method with detailed actions and results |
| [PROJECT_ARCHITECTURE.md](docs/tutorial/PROJECT_ARCHITECTURE.md) | Visual system architecture diagrams showing all layers and components |
| [WORKFLOW_DIAGRAMS.md](docs/tutorial/WORKFLOW_DIAGRAMS.md) | Detailed workflow diagrams for RAG pipeline, authentication, rate limiting |
| [ARCHITECTURE_EXPLAINED.md](docs/tutorial/ARCHITECTURE_EXPLAINED.md) | Narrative explanation of all architectural decisions and justifications |

These documents explain:
- Why I chose RAG over fine-tuning for medical accuracy
- How the token bucket rate limiting algorithm works
- Why FastAPI over Flask for async support
- The reasoning behind MongoDB connection pooling settings
- Trade-offs made for production readiness

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [LangChain](https://github.com/langchain-ai/langchain) - LLM orchestration
- [FastAPI](https://fastapi.tiangolo.com/) - Web framework
- [Pinecone](https://www.pinecone.io/) - Vector database
- [Meta Llama 2](https://ai.meta.com/llama/) - Language model

## Support

- Create an issue for bug reports
- Check existing issues before creating new ones
- See [CONTRIBUTING.md](CONTRIBUTING.md) for contribution guidelines

---

Built with care for healthcare professionals and patients.
