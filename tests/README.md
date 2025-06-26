# Tests

## Test Suites

### `test_integration.py`
Tests core diffchunk functionality with real diff files:
- Loading and parsing diffs
- Chunking and navigation
- Filtering options
- Error handling

### `test_mcp_components.py` 
Tests MCP server components and tools:
- Complete workflow testing
- Input validation
- Server creation and registration
- Performance with large diffs

## Test Data

Real diff files from open-source projects in `test_data/`:

| File | Source | Size | Description |
|------|--------|------|-------------|
| `go_version_upgrade_1.22_to_1.23.diff` | golang/go | ~13MB | Go 1.22→1.23 upgrade (large diff testing) |
| `dotnet_core_8_to_9.diff` | dotnet/core | ~12MB | .NET Core 8→9 upgrade (C# ecosystem) |
| `react_18.0_to_18.3.diff` | facebook/react | ~2.1MB | React 18.0→18.3 updates (JS/JSX files) |

Generated with:
```bash
git diff go1.22.0..go1.23.0 > go_version_upgrade_1.22_to_1.23.diff
git diff v8.0.0..v9.0.0 > dotnet_core_8_to_9.diff  
git diff v18.0.0..v18.3.0 > react_18.0_to_18.3.diff
```

## Running Tests

```bash
# All tests
uv run pytest

# Specific suite
uv run pytest tests/test_integration.py -v
uv run pytest tests/test_mcp_components.py -v

# Single test
uv run pytest tests/test_mcp_components.py::TestMCPComponents::test_diffchunk_tools_complete_workflow -v
```