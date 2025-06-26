# PyPI Publishing Guide

## Pre-Publishing Checklist

### Package Quality
```bash
# 1. All tests pass
uv run pytest
# Expected: 19/19 tests passing

# 2. Code quality checks
uv run ruff check
uv run ruff format --check
uv run mypy src/

# 3. Build verification
rm -rf dist/  # Clean previous builds
uv build     # Creates both .whl and .tar.gz
ls dist/      # Should show both diffchunk-0.1.0-py3-none-any.whl and diffchunk-0.1.0.tar.gz

# 4. Local installation test
pip install dist/diffchunk-*.whl
diffchunk-mcp --help     # Should show help message
diffchunk-mcp --version  # Should show version number
```

### Metadata Completeness
Verify `pyproject.toml` contains:
- [ ] Clear description
- [ ] Author information
- [ ] Python version requirements
- [ ] All dependencies listed
- [ ] Entry points configured
- [ ] Classifiers for discoverability

## PyPI Account Setup

### 1. Create Account
- Go to https://pypi.org/account/register/
- Use a strong password
- Verify email address

### 2. Enable 2FA (Required)
```bash
# Install authenticator app (Google Authenticator, Authy, etc.)
# PyPI → Account Settings → Add 2FA
# Save recovery codes securely
```

### 3. Create API Token
```bash
# PyPI → Account Settings → API tokens → Add API token
# Scope: "Entire account" (for first publication)
# Name: "diffchunk-publishing"
# Copy token (starts with pypi-)
```

## Enhanced Package Metadata

### Recommended pyproject.toml additions:
```toml
[project]
name = "diffchunk"
version = "0.1.0"
description = "MCP server for navigating large diff files with intelligent chunking"
readme = "README.md"
requires-python = ">=3.10"
license = {text = "MIT"}
keywords = ["mcp", "diff", "parsing", "llm", "ai-tools"]
authors = [
    {name = "Peter Etelej", email = "peter@etelej.com"}
]
maintainers = [
    {name = "Peter Etelej", email = "peter@etelej.com"}
]
classifiers = [
    "Development Status :: 4 - Beta",
    "Intended Audience :: Developers",
    "Topic :: Software Development :: Libraries :: Python Modules",
    "Topic :: Text Processing",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Operating System :: OS Independent",
]

[project.urls]
Homepage = "https://github.com/peteretelej/diffchunk"
Repository = "https://github.com/peteretelej/diffchunk.git"
Issues = "https://github.com/peteretelej/diffchunk/issues"
Documentation = "https://github.com/peteretelej/diffchunk#readme"
```

## Testing Workflow

### 1. Test on TestPyPI
```bash
# Build package
uv build

# Upload to TestPyPI
uv publish --repository testpypi
# Enter API token when prompted (use TestPyPI token)

# Test installation
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ diffchunk

# Verify functionality
diffchunk-mcp --help
python -c "from src.tools import DiffChunkTools; print('Import successful')"
```

### 2. TestPyPI API Token
```bash
# Create separate token for TestPyPI at https://test.pypi.org/
# Scope: "Entire account"
# Use this token for testing uploads
```

## Publishing Process

### 1. Final Preparation
```bash
# Update version in pyproject.toml if needed
# Commit all changes
git add .
git commit -m "Prepare v0.1.0 release"

# Clean previous builds
rm -rf dist/
```

### 2. Build and Publish
```bash
# Build package
uv build

# Verify build contents
tar -tzf dist/diffchunk-*.tar.gz | head -20
unzip -l dist/diffchunk-*.whl

# Publish to PyPI
uv publish
# Enter your PyPI API token

# Verify upload
pip install diffchunk
diffchunk-mcp --help
```

### 3. Create Git Tag
```bash
git tag v0.1.0
git push origin v0.1.0
# This triggers GitHub release workflow
```

## Security Best Practices

### API Token Management
```bash
# Create project-scoped tokens after first upload
# PyPI → Your projects → diffchunk → Settings → API tokens
# Scope: "Project: diffchunk"
# Store in password manager, not in code
```

### Environment Setup
```bash
# Option 1: Use uv's built-in token storage
uv publish  # Prompts for token, stores securely

# Option 2: Environment variable (CI/CD)
export UV_PUBLISH_TOKEN="pypi-..."
uv publish

# Option 3: .pypirc file (not recommended for tokens)
# Use only for repository URLs
```

### Supply Chain Security
```bash
# Regular dependency audits
uv add --dev safety
uv run safety check

# Monitor for vulnerabilities
# GitHub Dependabot alerts (already configured)
# PyPI security notifications
```

## Post-Release Verification

### 1. Installation Testing
```bash
# Test fresh installation
pip install diffchunk

# Test different installation methods
pip install diffchunk[dev]  # If optional dependencies added
uvx --from diffchunk diffchunk-mcp
```

### 2. Monitoring
- **PyPI project page**: https://pypi.org/project/diffchunk/
- **Download statistics**: PyPI project stats
- **GitHub releases**: Automatic from CI/CD
- **Issue tracking**: GitHub issues

### 3. Documentation Updates
```bash
# Update README installation instructions
# Verify badge URLs work
# Update MCP client examples
```

## Version Management

### Semantic Versioning
- `0.1.0` → `0.1.1`: Bug fixes
- `0.1.0` → `0.2.0`: New features, backward compatible
- `0.1.0` → `1.0.0`: Major release, potential breaking changes

### Release Process
```bash
# 1. Update version in pyproject.toml
# 2. Update CHANGELOG.md if exists
# 3. Commit changes
# 4. Run quality checks
# 5. Build and test
# 6. Publish to PyPI
# 7. Tag release
# 8. Push tag (triggers GitHub release)
```

## Troubleshooting

### Common Errors
```bash
# Error: Package already exists
# Solution: Increment version number in pyproject.toml

# Error: Invalid token
# Solution: Regenerate API token, check scopes

# Error: File already exists
# Solution: Clean dist/ directory, rebuild

# Error: Metadata validation failed
# Solution: Check pyproject.toml syntax, required fields
```

### Build Issues
```bash
# Debug build contents
uv build --verbose

# Check package structure
python -m zipfile -l dist/diffchunk-*.whl

# Validate metadata
pip install twine
twine check dist/*
```

### Installation Verification
```bash
# Test in clean environment
python -m venv test_env
source test_env/bin/activate
pip install diffchunk
diffchunk-mcp --help
deactivate
rm -rf test_env
```

## Advanced Configuration

### Trusted Publishing (Future)
```bash
# GitHub → PyPI trusted publishing
# More secure than API tokens
# Configure after first manual upload
# See: https://docs.pypi.org/trusted-publishers/
```

### Multiple Package Variants
```bash
# Optional dependencies (future consideration)
[project.optional-dependencies]
dev = ["pytest", "ruff", "mypy"]
docs = ["sphinx", "sphinx-rtd-theme"]
```

### Build Optimization
```bash
# Exclude test files from distribution
[tool.hatch.build.targets.wheel]
packages = ["src"]
exclude = ["tests/", "docs/", ".github/"]
```