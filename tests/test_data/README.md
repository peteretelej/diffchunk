# Test Data Sources

This directory contains real diff files from popular open-source projects for testing diffchunk functionality.

## Files

### `go_version_upgrade_1.22_to_1.23.diff` (~13MB)
- **Source**: golang/go repository
- **Command**: `git diff go1.22.0..go1.23.0`
- **Description**: Large diff showing Go language version upgrade from 1.22 to 1.23
- **License**: BSD-3-Clause (Go project)
- **Use case**: Testing large diff handling, performance, chunking across many files

### `dotnet_core_8_to_9.diff` (~12MB)  
- **Source**: dotnet/core repository
- **Command**: `git diff v8.0.0..v9.0.0`
- **Description**: Major .NET Core version upgrade diff
- **License**: MIT
- **Use case**: Testing C#/.NET ecosystem diffs, large refactoring patterns

### `react_18.0_to_18.3.diff` (~2.1MB)
- **Source**: facebook/react repository  
- **Command**: `git diff v18.0.0..v18.3.0`
- **Description**: React library updates and bug fixes
- **License**: MIT
- **Use case**: Testing JavaScript/JSX files, medium-sized diffs, build system changes

## Test Scenarios

These diffs provide realistic test data for:

1. **Large file handling** - Multi-megabyte diffs with thousands of files
2. **Language diversity** - Go, C#, JavaScript, TypeScript, JSON, Markdown
3. **Change types** - Version upgrades, feature additions, refactoring, build changes
4. **File patterns** - Generated files, test files, documentation, source code
5. **Chunking edge cases** - Very large files, binary files, trivial changes

## Usage in Tests

```python
# Example test usage
def test_large_diff_chunking():
    session = DiffSession("tests/test_data/go_version_upgrade_1.22_to_1.23.diff")
    chunker = DiffChunker(max_chunk_lines=5000)
    chunker.chunk_diff(session)
    
    assert session.stats.chunks_count > 10
    assert session.stats.total_files > 100
```

## Regenerating Test Data

To update test data with newer versions:

```bash
# Go updates
cd /path/to/go
git diff go1.23.0..go1.24.0 > /path/to/diffchunk/tests/test_data/go_version_upgrade_1.23_to_1.24.diff

# .NET updates  
cd /path/to/core
git diff v9.0.0..v10.0.0 > /path/to/diffchunk/tests/test_data/dotnet_core_9_to_10.diff

# React updates
cd /path/to/react
git diff v18.3.0..v19.0.0 > /path/to/diffchunk/tests/test_data/react_18.3_to_19.0.diff
```

## License Compliance

All test data is derived from projects with permissive licenses (MIT, BSD-3-Clause) that allow redistribution for testing purposes. The diff files contain only changes/patches, not complete source code.