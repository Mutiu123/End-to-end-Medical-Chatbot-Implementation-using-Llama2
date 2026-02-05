# Contributing to Medical Chatbot API

Thank you for your interest in contributing to the Medical Chatbot API project. This document provides guidelines and instructions for contributing.

## Table of Contents

1. [Code of Conduct](#code-of-conduct)
2. [Getting Started](#getting-started)
3. [Development Setup](#development-setup)
4. [Development Workflow](#development-workflow)
5. [Code Standards](#code-standards)
6. [Testing Guidelines](#testing-guidelines)
7. [Pull Request Process](#pull-request-process)
8. [Issue Guidelines](#issue-guidelines)

## Code of Conduct

This project adheres to a code of conduct. By participating, you are expected to uphold this code. Please report unacceptable behavior to the project maintainers.

## Getting Started

### Prerequisites

- Python 3.11 or higher
- Docker and Docker Compose
- Git
- MongoDB (local or Docker)
- Pinecone account (for vector database)

### Fork and Clone

1. Fork the repository on GitHub
2. Clone your fork locally:

```bash
git clone https://github.com/YOUR_USERNAME/End-to-end-Medical-Chatbot-Implementation-using-Llama2.git
cd End-to-end-Medical-Chatbot-Implementation-using-Llama2
```

3. Add the upstream repository:

```bash
git remote add upstream https://github.com/Mutiu123/End-to-end-Medical-Chatbot-Implementation-using-Llama2.git
```

## Development Setup

### 1. Create Virtual Environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/macOS
source venv/bin/activate
```

### 2. Install Dependencies

```bash
# Install production dependencies
pip install -r requirements.txt

# Install development dependencies
pip install -r requirements-dev.txt
```

### 3. Set Up Environment Variables

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your configuration
# At minimum, set:
# - SECRET_KEY (generate a secure random string)
# - PINECONE_API_KEY
# - MONGODB_URI
```

### 4. Install Pre-commit Hooks

```bash
pre-commit install
```

### 5. Start Development Services

```bash
# Using Docker Compose
docker-compose up -d mongodb

# Or run MongoDB locally
```

### 6. Run the Application

```bash
# Development mode with hot-reload
uvicorn app.main:app --reload --port 8080

# Or using Docker
docker-compose up app
```

## Development Workflow

### 1. Create a Feature Branch

```bash
# Sync with upstream
git fetch upstream
git checkout main
git merge upstream/main

# Create feature branch
git checkout -b feature/your-feature-name
```

### 2. Make Your Changes

- Write clean, documented code
- Follow the code standards (see below)
- Add tests for new functionality
- Update documentation as needed

### 3. Run Quality Checks

```bash
# Format code
black app/ tests/
isort app/ tests/

# Run linters
flake8 app/ tests/
mypy app/
pylint app/

# Run tests
pytest tests/ -v --cov=app --cov-report=term-missing
```

### 4. Commit Your Changes

```bash
# Stage changes
git add .

# Commit with descriptive message
git commit -m "feat: add user authentication endpoint"
```

Follow conventional commit format:
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation changes
- `style:` - Code style changes (formatting)
- `refactor:` - Code refactoring
- `test:` - Adding or updating tests
- `chore:` - Maintenance tasks

### 5. Push and Create Pull Request

```bash
git push origin feature/your-feature-name
```

Then create a Pull Request on GitHub.

## Code Standards

### Python Style Guide

We follow PEP 8 with some modifications:

- Maximum line length: 100 characters
- Use double quotes for strings
- Use type hints for all function parameters and return values

### Code Formatting

We use the following tools:

- **Black**: Code formatter (line length: 100)
- **isort**: Import sorter
- **flake8**: Linter
- **mypy**: Static type checker
- **pylint**: Code analysis

### Documentation

- All public functions must have docstrings (Google style)
- Complex logic should have inline comments
- Update README.md for user-facing changes
- Update API documentation for endpoint changes

### Example Function

```python
from typing import Optional

def process_query(
    query: str,
    session_id: Optional[str] = None,
    max_tokens: int = 512,
) -> dict:
    """
    Process a chat query and return the response.

    Args:
        query: The user's question or message.
        session_id: Optional session identifier for context.
        max_tokens: Maximum tokens in the response.

    Returns:
        Dictionary containing the response and metadata.

    Raises:
        ValidationError: If the query is empty or too long.
        LLMError: If the language model fails to respond.
    """
    # Implementation here
    pass
```

## Testing Guidelines

### Test Structure

```
tests/
    __init__.py
    conftest.py           # Shared fixtures
    test_config.py        # Configuration tests
    test_security.py      # Security module tests
    test_exceptions.py    # Exception tests
    test_schemas.py       # Pydantic schema tests
    test_api_endpoints.py # API integration tests
```

### Writing Tests

1. Use descriptive test names
2. One assertion per test when possible
3. Use fixtures for common setup
4. Mock external dependencies
5. Test both success and failure cases

### Example Test

```python
import pytest
from app.core.security import SecurityUtils


class TestPasswordHashing:
    """Test cases for password hashing."""

    def test_hash_password_returns_different_value(self):
        """Test that hashing produces a different value than input."""
        password = "TestPassword123!"
        hashed = SecurityUtils.hash_password(password)

        assert hashed != password

    def test_verify_password_correct(self):
        """Test that correct password verifies successfully."""
        password = "TestPassword123!"
        hashed = SecurityUtils.hash_password(password)

        assert SecurityUtils.verify_password(password, hashed) is True

    def test_verify_password_incorrect(self):
        """Test that incorrect password fails verification."""
        password = "TestPassword123!"
        hashed = SecurityUtils.hash_password(password)

        assert SecurityUtils.verify_password("WrongPassword", hashed) is False
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_security.py

# Run specific test class
pytest tests/test_security.py::TestPasswordHashing

# Run with verbose output
pytest -v

# Run in parallel
pytest -n auto
```

## Pull Request Process

### Before Submitting

1. Ensure all tests pass
2. Run all linters without errors
3. Update documentation if needed
4. Add tests for new functionality
5. Rebase on latest main branch

### PR Description Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
Describe testing done

## Checklist
- [ ] Code follows style guidelines
- [ ] Tests added/updated
- [ ] Documentation updated
- [ ] All checks pass
```

### Review Process

1. Automated checks must pass
2. At least one maintainer review required
3. Address review comments promptly
4. Squash commits before merge if requested

## Issue Guidelines

### Bug Reports

Include:
- Clear description of the bug
- Steps to reproduce
- Expected vs actual behavior
- Environment details (OS, Python version, etc.)
- Error messages or logs

### Feature Requests

Include:
- Clear description of the feature
- Use case and motivation
- Proposed implementation (optional)
- Alternatives considered

### Questions

- Check existing documentation first
- Search existing issues
- Provide context about what you're trying to achieve

## Getting Help

- Check the documentation
- Search existing issues
- Create a new issue with the question label
- Join community discussions

Thank you for contributing!
