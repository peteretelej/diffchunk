# Maintaining diffchunk

Documentation for maintainers on publishing, releases, and development.

## PyPI Publishing

### Initial Setup
1. Create PyPI account at https://pypi.org
2. Generate API token in account settings
3. Store token securely

### Publishing Process
```bash
# Update version in pyproject.toml
# Commit changes
git tag v0.1.0
git push origin v0.1.0

# Build and publish
uv build
uv publish --token <your-pypi-token>
```

### Version Management
- Use semantic versioning: MAJOR.MINOR.PATCH
- Update version in `pyproject.toml` before each release
- Tag releases in git for traceability
- Each PyPI upload requires a unique version number

### Testing Before Publication
```bash
# Build locally
uv build

# Test installation
pip install dist/diffchunk-*.whl

# Verify console script works
diffchunk-mcp --help

# Test MCP server functionality
python -c "from diffchunk.mcp_server import main; main()"
```

## MCP Registry Submission

### Requirements
- Package published to PyPI
- Working MCP server implementation
- Clear documentation and examples
- Stable API interface

### Submission Process
1. Fork the MCP registry repository
2. Add server definition following registry format
3. Include installation and configuration instructions
4. Submit pull request with server details

### Registry Entry Format
```json
{
  "name": "diffchunk",
  "description": "Navigate large diff files intelligently",
  "repository": "https://github.com/peteretelej/diffchunk",
  "installation": {
    "pip": "diffchunk"
  },
  "configuration": {
    "command": "diffchunk-mcp"
  }
}
```

## Development Setup

### Local Development
```bash
git clone https://github.com/peteretelej/diffchunk.git
cd diffchunk
uv sync --dev

# Run tests
uv run pytest

# Run linting
uv run ruff check

# Test MCP server locally
uv run python -m diffchunk.mcp_server
```

### Testing Changes
```bash
# Install in development mode
uv sync

# Test console script
uv run diffchunk-mcp

# Test with actual MCP client
# Update MCP client config to use local path
```

## Release Checklist

### Pre-Release
- [ ] Update version in `pyproject.toml`
- [ ] Update CHANGELOG.md with new features/fixes
- [ ] Run full test suite: `uv run pytest`
- [ ] Test MCP server functionality manually
- [ ] Verify console script works: `diffchunk-mcp --help`

### Release
- [ ] Commit version changes
- [ ] Create and push git tag: `git tag v0.1.0 && git push origin v0.1.0`
- [ ] Build package: `uv build`
- [ ] Publish to PyPI: `uv publish --token <token>`
- [ ] Verify PyPI upload successful
- [ ] Test installation from PyPI: `pip install diffchunk`

### Post-Release
- [ ] Update README.md if needed
- [ ] Announce release in relevant communities
- [ ] Monitor for issues and user feedback

## Project Structure

```
diffchunk/
├── pyproject.toml          # Package configuration
├── README.md              # User documentation
├── docs/
│   ├── design.md          # Technical design
│   └── designs/
│       └── maintaining.md # This file
├── src/
│   └── diffchunk/
│       ├── __init__.py
│       ├── mcp_server.py  # MCP server implementation
│       ├── parser.py      # Diff parsing
│       ├── chunker.py     # Chunking logic
│       └── filters.py     # Filtering logic
└── tests/
    └── test_*.py          # Test files
```

## Dependencies

### Runtime Dependencies
- `mcp[cli]`: MCP Python SDK for server implementation
- Python 3.8+ compatibility

### Development Dependencies
- `pytest`: Testing framework
- `ruff`: Linting and formatting
- `mypy`: Type checking (optional)

## Troubleshooting

### Common Issues
- **Import errors**: Ensure package is properly installed with `uv sync`
- **Console script not found**: Verify `pyproject.toml` has correct entry point
- **MCP server not responding**: Check server logs for startup errors
- **PyPI upload fails**: Verify API token and version number is unique

### Debug MCP Server
```bash
# Run server with debug output
python -m diffchunk.mcp_server --debug

# Test server manually
echo '{"jsonrpc": "2.0", "id": 1, "method": "initialize"}' | python -m diffchunk.mcp_server
```