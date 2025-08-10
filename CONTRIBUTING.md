# Contributing to STL 311+

Thank you for your interest in contributing to STL 311+! This document provides guidelines for contributing to this enhanced citizen engagement platform.

## 🤝 How to Contribute

### Reporting Bugs

1. **Check existing issues** to avoid duplicates
2. **Use the bug report template** when creating new issues
3. **Include specific details**:
   - Steps to reproduce the issue
   - Expected vs. actual behavior
   - Environment details (OS, browser, Docker version)
   - Screenshots or error messages if applicable

### Suggesting Features

1. **Check existing feature requests** to avoid duplicates
2. **Use the feature request template**
3. **Describe the problem** your feature would solve
4. **Explain the proposed solution** with examples
5. **Consider the impact** on existing functionality

### Code Contributions

#### Prerequisites
- Python 3.9+
- Docker and Docker Compose
- Git knowledge
- Familiarity with Flask, SQLAlchemy, and PostGIS

#### Development Workflow

1. **Fork the repository**
```bash
git clone https://github.com/yourusername/stl311_plus.git
cd stl311_plus
```

2. **Create a feature branch**
```bash
git checkout -b feature/your-feature-name
```

3. **Set up development environment**
```bash
# Copy environment template
cp env.example .env

# Start development environment
docker-compose up -d

# Install dependencies for local development
pip install -r requirements.txt
```

4. **Make your changes**
   - Follow the existing code style
   - Add docstrings to new functions
   - Include type hints where appropriate
   - Update relevant documentation

5. **Add tests**
```bash
# Add tests in the tests/ directory
# Run existing tests to ensure nothing breaks
python -m pytest tests/
```

6. **Test your changes**
```bash
# Test with Docker
docker-compose down
docker-compose up -d
# Verify functionality in browser

# Test API endpoints
# Test database migrations if applicable
```

7. **Commit your changes**
```bash
git add .
git commit -m "Add feature: brief description of your changes"
```

8. **Push to your fork**
```bash
git push origin feature/your-feature-name
```

9. **Create a Pull Request**
   - Use the pull request template
   - Reference related issues
   - Describe what changes were made
   - Include screenshots for UI changes

## 📝 Code Standards

### Python Code Style
- Follow **PEP 8** style guidelines
- Use **Black** for code formatting (optional but recommended)
- Maximum line length: **88 characters**
- Use **descriptive variable names**
- Add **docstrings** for all functions and classes

### Database Changes
- Always create **migration scripts** for schema changes
- Test migrations with existing data
- Include **rollback procedures**
- Update model documentation

### Frontend Code
- Follow **consistent indentation** (2 spaces for HTML/CSS/JS)
- Use **semantic HTML elements**
- Ensure **accessibility** considerations
- Test on **multiple screen sizes**

### Documentation
- Update **README.md** for user-facing changes
- Add **inline comments** for complex logic
- Update **API documentation** for new endpoints
- Include **examples** in documentation

## 🧪 Testing Guidelines

### Required Tests
- **API endpoint tests** for new routes
- **Database model tests** for new fields/relationships
- **Integration tests** for complex workflows
- **Frontend tests** for user interactions (when applicable)

### Test Structure
```python
def test_function_name():
    """Test description explaining what is being tested."""
    # Arrange - Set up test data
    # Act - Execute the function being tested
    # Assert - Verify the results
```

### Running Tests
```bash
# Run all tests
python -m pytest tests/ -v

# Run specific test file
python -m pytest tests/test_api.py -v

# Run tests with coverage
python -m pytest tests/ --cov=app --cov-report=html
```

## 📚 Documentation Guidelines

### Commit Messages
Use **conventional commits** format:
```
type(scope): brief description

Longer description if needed

Closes #issue-number
```

**Types**: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

**Examples**:
- `feat(api): add request tracking endpoint`
- `fix(db): resolve migration issue with attachments table`
- `docs(readme): update installation instructions`

### Pull Request Template
```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Tests pass locally
- [ ] New tests added
- [ ] Manual testing completed

## Checklist
- [ ] Code follows style guidelines
- [ ] Documentation updated
- [ ] No sensitive data in commits
```

## 🐛 Debugging Guidelines

### Common Issues
1. **Port conflicts**: Check if ports 5000, 5433, 8080 are available
2. **Database connection**: Verify PostgreSQL container is running
3. **Template changes not showing**: Rebuild Docker container
4. **GeoServer publishing fails**: Check GeoServer admin interface

### Debug Tools
```bash
# View container logs
docker-compose logs flask_app
docker-compose logs postgres
docker-compose logs geoserver

# Access container shell
docker exec -it stl311_flask /bin/bash
docker exec -it stl311_postgres psql -U postgres -d stl311_db

# Check service health
curl http://localhost:5000/api/health
```

## 🚀 Deployment Considerations

### Environment Variables
- Never commit sensitive data (API keys, passwords)
- Use `.env` files for local development
- Document required environment variables

### Docker Best Practices
- Keep images lightweight
- Use multi-stage builds when appropriate
- Pin dependency versions
- Include health checks

### Database Migrations
- Test migrations on sample data
- Include rollback procedures
- Document breaking changes
- Coordinate with deployment team

## 📞 Getting Help

- **Questions**: Open a discussion in GitHub Discussions
- **Bugs**: Create an issue with detailed information
- **Features**: Start with a discussion before implementing
- **Security**: Report security issues privately

## 📜 License

By contributing to STL 311+, you agree that your contributions will be licensed under the MIT License.

---

Thank you for helping make STL 311+ better for St. Louis citizens! 🏛️✨
