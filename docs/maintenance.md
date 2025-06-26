# Maintenance Guide

## Publishing Releases

**Prerequisites:**
- GitHub repository secret `PYPI_API_TOKEN` configured
- Version updated in `pyproject.toml`

**Release Process:**
```bash
# 1. Update version in pyproject.toml (e.g., "0.1.1")
# 2. Commit changes
git add .
git commit -m "Prepare release v0.1.1"

# 3. Create and push tag
git tag v0.1.1
git push origin main
git push origin v0.1.1
```

GitHub Actions automatically:
- Runs tests and builds package
- Publishes to PyPI
- Creates GitHub release with artifacts

**Manual Testing (optional):**
```bash
# Test on TestPyPI first
uv publish --publish-url https://test.pypi.org/legacy/
# Username: __token__, Password: TestPyPI token

# Verify installation
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ diffchunk
diffchunk-mcp --version
```

## CI/CD Maintenance

### GitHub Actions Workflows

- **`ci.yml`**: Runs on all PRs and main branch pushes
- **`release.yml`**: Runs on version tags (v*)
- **`security.yml`**: Weekly security scans

### Secrets Management

Required GitHub repository secrets:
- `CODECOV_TOKEN`: For code coverage reporting
- `PYPI_API_TOKEN`: For automated PyPI publishing (when enabled)

### Badge Status

Monitor these badges for issues:
- CI status
- Code coverage
- PyPI version
- Security scans

## Version Management

### Versioning Strategy

Follow semantic versioning (semver):
- `MAJOR.MINOR.PATCH`
- `MAJOR`: Breaking changes
- `MINOR`: New features, backward compatible
- `PATCH`: Bug fixes, backward compatible

### Release Checklist

Before each release:

- [ ] All tests pass locally and in CI
- [ ] Code coverage is acceptable (>70%)
- [ ] Documentation is updated
- [ ] Version number bumped in `pyproject.toml`
- [ ] Manual testing completed
- [ ] Security scan passes

## Dependency Updates

### Regular Maintenance

Monthly dependency updates:

```bash
# Check for outdated dependencies
uv tree --outdated

# Update specific packages
uv add package@latest

# Update dev dependencies
uv add --dev package@latest

# Test after updates
uv run pytest
```

### Security Updates

Respond to security alerts immediately:

1. Review the security advisory
2. Update affected packages
3. Run full test suite
4. Create patch release if needed

## Performance Monitoring

### Key Metrics

Monitor these performance indicators:

- **Test execution time**: Should remain <30 seconds
- **Package build time**: Should remain <10 seconds
- **Large diff processing**: <10 seconds for 100k+ line diffs
- **Memory usage**: Reasonable for large diffs

### Benchmarking

Run performance tests with large diffs:

```bash
# Test with Go upgrade diff (~13MB)
uv run pytest tests/test_mcp_components.py::TestMCPComponents::test_large_diff_performance -v
```

## Documentation Maintenance

### Regular Updates

Keep these docs current:
- README.md usage examples
- API documentation
- Installation instructions
- MCP client configuration examples

### Version-Specific Updates

Update examples when:
- MCP protocol changes
- Python version requirements change
- Major feature additions
- Breaking API changes

## Support and Issues

### Issue Triage

Weekly review of GitHub issues:
- Label appropriately (bug, enhancement, question)
- Close duplicate issues  
- Request more information when needed
- Prioritize security-related issues

### Release Communication

For major releases:
- Update README.md with new features
- Consider blog post or announcement
- Update MCP client configuration examples
- Notify existing users of breaking changes

## Testing Before Publication

### Local Testing
```bash
# Build locally
uv build

# Test installation
pip install dist/diffchunk-*.whl

# Verify console script works
diffchunk-mcp --help

# Test MCP server functionality
uv run python -m src.main
```

### MCP Integration Testing
```bash
# Test MCP tools directly
uv run pytest tests/test_mcp_components.py -v

# Test with real diff files
uv run pytest tests/test_integration.py -v
```

## Project Structure Reference

```
diffchunk/
├── .github/workflows/      # CI/CD workflows
├── docs/                   # Documentation
├── src/                    # Source code
│   ├── __init__.py
│   ├── main.py            # CLI entry point
│   ├── server.py          # MCP server implementation
│   ├── tools.py           # MCP tool functions
│   ├── models.py          # Data models
│   ├── parser.py          # Diff parsing logic
│   └── chunker.py         # Chunking engine
├── tests/                 # Test files
│   ├── test_data/         # Real diff files for testing
│   ├── test_integration.py
│   └── test_mcp_components.py
├── pyproject.toml         # Package configuration
└── README.md              # User documentation
```