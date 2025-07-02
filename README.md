# diffchunk

[![CI](https://github.com/peteretelej/diffchunk/actions/workflows/ci.yml/badge.svg)](https://github.com/peteretelej/diffchunk/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/peteretelej/diffchunk/branch/main/graph/badge.svg)](https://codecov.io/gh/peteretelej/diffchunk)
[![PyPI version](https://img.shields.io/pypi/v/diffchunk.svg)](https://pypi.org/project/diffchunk/)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)

MCP server that enables LLMs to navigate large diff files efficiently. Instead of reading entire diffs sequentially, LLMs can jump directly to relevant changes using pattern-based navigation.

## Problem

Large diffs exceed LLM context limits and waste tokens on irrelevant changes. A 50k+ line diff can't be processed directly and manual splitting loses file relationships.

## Solution

MCP server with 4 navigation tools:

- `load_diff` - Parse diff file with custom settings (optional)
- `list_chunks` - Show chunk overview with file mappings (auto-loads)
- `get_chunk` - Retrieve specific chunk content (auto-loads)  
- `find_chunks_for_files` - Locate chunks by file patterns (auto-loads)

## Setup

Add to your MCP client configuration:

```json
{
  "mcpServers": {
    "diffchunk": {
      "command": "uvx",
      "args": ["--from", "diffchunk", "diffchunk-mcp"]
    }
  }
}
```

## Usage

### Basic Workflow

```bash
# Generate diff file
git diff main..feature-branch > /tmp/changes.diff
```

```
# LLM analyzes using diffchunk tools
Use diffchunk to analyze the diff at /tmp/changes.diff and find any bugs.
```

### Tracking Analysis Progress

For large diffs requiring systematic analysis, LLMs can maintain tracking documents to resume work:

```
# Initial analysis with tracking
Use diffchunk to analyze /tmp/large-feature.diff. Create a tracking document 
to monitor progress through all chunks, then provide final summary.

# LLM maintains internal tracking:
# - Chunk 1/15: API endpoints - ANALYZED
# - Chunk 2/15: Database models - ANALYZED  
# - Chunk 3/15: Tests - IN PROGRESS
# - Chunks 4-15: PENDING

# Clean up tracking before final results
```

The tracking document concept allows LLMs to:
- Resume analysis where they left off
- Ensure comprehensive coverage of large diffs
- Maintain context across multiple chunks
- Provide complete analysis results

### Tool Usage Patterns

**Overview first:**
```python
list_chunks("/tmp/changes.diff")
# → 5 chunks across 12 files, 3,847 total lines
```

**Target specific files:**
```python
find_chunks_for_files("/tmp/changes.diff", "*.py")
# → [1, 3, 5] - Python file chunks

get_chunk("/tmp/changes.diff", 1)
# → Content of first Python chunk
```

**Systematic analysis:**
```python
# Process each chunk in sequence
get_chunk("/tmp/changes.diff", 1)
get_chunk("/tmp/changes.diff", 2)
# ... continue through all chunks
```

## Configuration

### Path Requirements

- **Absolute paths only**: `/home/user/project/changes.diff`
- **Cross-platform**: Windows (`C:\path`) and Unix (`/path`) 
- **Home expansion**: `~/project/changes.diff`

### Auto-Loading Defaults

Tools auto-load with optimized settings:
- `max_chunk_lines`: 1000
- `skip_trivial`: true (whitespace-only)
- `skip_generated`: true (lock files, build artifacts)

### Custom Settings

Use `load_diff` for non-default behavior:

```python
load_diff(
    "/tmp/large.diff",
    max_chunk_lines=2000,
    include_patterns="*.py,*.js",
    exclude_patterns="*test*"
)
```

## Supported Formats

- Git diff output (`git diff`, `git show`)
- Unified diff format (`diff -u`)
- Multiple files in single diff
- Binary file change indicators

## Performance

- Efficiently handles 100k+ line diffs
- Memory efficient streaming
- Auto-reload on file changes

## Documentation

- [Design](docs/design.md) - Architecture and implementation details
- [Contributing](docs/CONTRIBUTING.md) - Development setup and workflows

## License

[MIT](./LICENSE)