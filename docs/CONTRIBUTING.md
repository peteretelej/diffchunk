# Contributing to diffchunk

## Setup

```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh  # Linux/macOS
# OR: powershell -c "irm https://astral.sh/uv/install.ps1 | iex"  # Windows

# Clone and setup
git clone https://github.com/peteretelej/diffchunk.git
cd diffchunk
uv sync

# Verify setup
uv run pytest
```

## Development

### Code Quality

```bash
# Run tests
uv run pytest

# Format and lint
uv run ruff check
uv run ruff format

# Type check
uv run mypy src/

# Setup pre-push hook
cp scripts/pre-push .git/hooks/pre-push
chmod +x .git/hooks/pre-push
```

### Testing

```bash
# All tests
uv run pytest

# Specific suites
uv run pytest tests/test_integration.py -v
uv run pytest tests/test_mcp_components.py -v

# MCP server
uv run python -m src.main
```

### MCP Integration Testing

```json
// Add to ~/.config/claude-desktop/claude_desktop_config.json
{
  "mcpServers": {
    "diffchunk-dev": {
      "command": "uv",
      "args": ["run", "python", "-m", "src.main"],
      "cwd": "/absolute/path/to/diffchunk"
    }
  }
}
```

## Releases

### Process

```bash
# 1. Update version in pyproject.toml
# 2. Commit and tag
git add .
git commit -m "Prepare release v0.1.1"
git tag v0.1.1
git push origin main v0.1.1
```

GitHub Actions automatically builds and publishes to PyPI.

### Checklist

- [ ] Tests pass
- [ ] Version updated in `pyproject.toml`
- [ ] Documentation updated

## Maintenance

### Dependencies

```bash
# Monthly updates
uv tree --outdated
uv add package@latest

# Security updates (immediate)
uv add vulnerable-package@latest
uv run pytest
```

### Performance Monitoring

- Test execution: <30 seconds
- Large diff processing: <10 seconds for 100k+ lines
- Memory usage: reasonable for large diffs

### CI/CD

**Workflows:**
- `ci.yml` - Tests on PRs and main
- `release.yml` - Publishes on version tags
- `security.yml` - Weekly security scans

**Required Secrets:**
- `CODECOV_TOKEN` - Code coverage
- `PYPI_API_TOKEN` - PyPI publishing

## Project Structure

```
src/
├── main.py           # CLI entry point
├── server.py         # MCP server
├── tools.py          # MCP tools
├── models.py         # Data models
├── parser.py         # Diff parsing
└── chunker.py        # Chunking logic

tests/
├── test_data/        # Real diff files
├── test_integration.py
└── test_mcp_components.py
```

## Contributing Workflow

1. Fork repository
2. Create feature branch: `git checkout -b feature-name`
3. Make changes and test: `uv run pytest`
4. Check quality: `uv run ruff check && uv run ruff format`
5. Submit pull request

## Troubleshooting

**Common Issues:**
- Use `uv run` for all commands
- Verify absolute file paths exist
- Check file permissions for diff files

**Path Issues:**
```bash
# Check file exists
ls -la /path/to/file.diff

# Use absolute paths
list_chunks("/absolute/path.diff")  # ✓
list_chunks("./relative.diff")      # ✗
```