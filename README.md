# diffchunk

[![CI](https://github.com/peteretelej/diffchunk/actions/workflows/ci.yml/badge.svg)](https://github.com/peteretelej/diffchunk/actions/workflows/ci.yml)
[![PyPI version](https://img.shields.io/pypi/v/diffchunk.svg)](https://pypi.org/project/diffchunk/)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)

MCP server that enables LLMs to navigate large diff files efficiently. Instead of reading entire diffs sequentially, LLMs can jump directly to relevant changes using pattern-based navigation.

## Problem

Large diffs exceed LLM context limits and waste tokens on irrelevant changes. A 50k+ line diff can't be processed directly and manual splitting loses file relationships.

## Solution

MCP server with 5 navigation tools:

- `load_diff` - Parse diff file with custom settings (optional)
- `list_chunks` - Show chunk overview with file mappings and per-file line counts (auto-loads)
- `get_chunk` - Retrieve specific chunk content (auto-loads)
- `find_chunks_for_files` - Locate chunks by file patterns (auto-loads)
- `get_file_diff` - Extract the complete diff for a single file (auto-loads)

## Setup

**Prerequisite:** Install [uv](https://docs.astral.sh/uv/getting-started/installation/) (an extremely fast Python package manager) which provides the `uvx` command.

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

Your AI assistant can now handle massive changesets that previously caused failures in Cline, Roocode, Cursor, and other tools.

### Using with AI Assistant

Once configured, your AI assistant can analyze large commits, branches, or diffs using diffchunk.

Here are some example use cases:

**Branch comparisons:**

- _"Review all changes in develop not in the main branch for any bugs"_
- _"Tell me about all the changes I have yet to merge"_
- _"What new features were added to the staging branch?"_
- _"Summarize all changes to this repo in the last 2 weeks"_

**Code review:**

- _"Use diffchunk to check my feature branch for security vulnerabilities"_
- _"Use diffchunk to find any breaking changes before I merge to production"_
- _"Use diffchunk to review this large refactor for potential issues"_

**Change analysis:**

- _"Use diffchunk to show me all database migrations that need to be run"_
- _"Use diffchunk to find what API changes might affect our mobile app"_
- _"Use diffchunk to analyze all new dependencies added recently"_

**Direct file analysis:**

- _"Use diffchunk to analyze the diff at /tmp/changes.diff and find any bugs"_
- _"Create a diff of my uncommitted changes and review it"_
- _"Compare my local branch with origin and highlight conflicts"_

### Tip: AI Assistant Rules

Add to your AI assistant's custom instructions for automatic usage:

```
When reviewing large changesets or git commits, use diffchunk to handle large diff files.
Create temporary diff files and tracking files as needed and clean up after analysis.
```

## How It Works

When you ask your AI assistant to analyze changes, it uses diffchunk's tools strategically:

1. **Creates the diff file** (e.g., `git diff main..develop > /tmp/changes.diff`) based on your question
2. **Uses `list_chunks`** to get an overview of the diff structure and total scope, including per-file line counts via `file_details`
3. **Uses `find_chunks_for_files`** to locate relevant sections when you ask about specific file types
4. **Uses `get_file_diff`** to fetch the complete diff for one specific file without loading an entire chunk
5. **Uses `get_chunk`** to examine specific sections without loading the entire diff into context
6. **Tracks progress systematically** through large changesets, analyzing chunk by chunk
7. **Cleans up temporary files** after completing the analysis

This lets your AI assistant handle massive diffs that would normally crash other tools, while providing thorough analysis without losing context.

### Tool Usage Patterns

**Overview first:**

```python
list_chunks("/tmp/changes.diff")
# -> 5 chunks across 12 files, 3,847 total lines, ~15,420 tokens
# Each chunk includes token_count and file_details with per-file line counts
# Response includes total_token_count for context-budget planning
```

**Target specific files:**

```python
find_chunks_for_files("/tmp/changes.diff", "*.py")
# → [1, 3, 5] - Python file chunks

get_chunk("/tmp/changes.diff", 1)
# → Content of first Python chunk
```

**Single-file diff:**

```python
get_file_diff("/tmp/changes.diff", "src/main.py")
# → Complete diff for src/main.py (header + all hunks)

# Glob patterns work when they match exactly one file
get_file_diff("/tmp/changes.diff", "*.config")
# → Complete diff for the single matching config file
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
    exclude_patterns="*test*",
    context_lines=2
)
```

### Format Options

Use the `format` parameter on `get_chunk` to transform output for LLM consumption:

```python
# Default - raw diff output
get_chunk("/tmp/changes.diff", 1, format="raw")

# Annotated - structured with line numbers, file headers, hunk separation
get_chunk("/tmp/changes.diff", 1, format="annotated")

# Compact - token-efficient, only new hunks (context + added lines)
get_chunk("/tmp/changes.diff", 1, format="compact")
```

**Annotated format** adds `## File:` headers, `__new hunk__`/`__old hunk__` sections with new-file line numbers, and function context from `@@` headers.

**Compact format** shows only what was added or kept, omitting removed lines and `__old hunk__` sections entirely. Useful when you only need to see the final state.

### Context Reduction

Use `context_lines` on `load_diff` to reduce context lines per hunk at load time:

```python
# Keep only 2 lines of context around each change
load_diff("/tmp/large.diff", context_lines=2)

# Keep only changes, no context
load_diff("/tmp/large.diff", context_lines=0)
```

This composes with `format` - context is reduced at load time, then formatting is applied at display time.

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
- [Contributing](CONTRIBUTING.md) - Contributing guidelines and development setup

## License

[MIT](./LICENSE)
