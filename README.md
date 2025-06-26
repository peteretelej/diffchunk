# diffchunk

A Python CLI tool that breaks large diff files into manageable chunks for LLM analysis and code review.

## Problem

Large diff files (50k+ lines) exceed LLM context windows, making comprehensive code review impossible. Manual chunking loses context and file relationships.

## Solution

`diffchunk` intelligently splits large diffs while preserving context, filtering trivial changes, and maintaining file boundaries.

## Installation

### Prerequisites
- Python 3.8+
- [uv](https://docs.astral.sh/uv/) package manager

### Install uv (if not already installed)
```bash
# Windows
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### Install diffchunk
```bash
# Clone repository
git clone https://github.com/peteretelej/diffchunk.git
cd diffchunk

# Install with uv
uv sync
```

## Usage

### Basic Commands

#### Get diff metadata
```bash
uv run diffchunk large.diff
```
Output:
```
Total lines: 50,000
Files changed: 25
Total chunks: 10
Trivial changes: 150 (filtered)
```

#### Get specific chunk
```bash
uv run diffchunk large.diff --part 1
```
Output:
```
=== Chunk 1 of 10 ===
Files: src/main.py, src/utils.py (2 files)
Lines: 4,500

diff --git a/src/main.py b/src/main.py
index 1234567..abcdefg 100644
--- a/src/main.py
+++ b/src/main.py
[diff content...]
```

### Advanced Options

#### Skip trivial changes
```bash
uv run diffchunk large.diff --part 1 --skip-trivial
```

#### Custom chunk size
```bash
uv run diffchunk large.diff --part 1 --max-lines 2000
```

#### Filter by file types
```bash
uv run diffchunk large.diff --part 1 --include "*.py,*.js"
```

#### Show all available options
```bash
uv run diffchunk --help
```

## Examples

### Typical Workflow

1. **Analyze the diff**

```bash
uv run diffchunk my-feature.diff
# Output: Total lines: 15,000, Files changed: 8, Total chunks: 3
```

2. **Review each chunk**

```bash
uv run diffchunk my-feature.diff --part 1
# Review first chunk with LLM

uv run diffchunk my-feature.diff --part 2
# Review second chunk with LLM

uv run diffchunk my-feature.diff --part 3
# Review final chunk with LLM
```

### Generate diff from git
```bash
# Create a diff file
git diff main..feature-branch > feature.diff

# Analyze with diffchunk
uv run diffchunk feature.diff
```

## Features

- **Smart chunking**: Preserves file boundaries and context
- **Trivial filtering**: Skips whitespace-only and newline-only changes
- **Metadata extraction**: Shows total lines, files, and chunk count
- **Context preservation**: Maintains diff headers and file context
- **Memory efficient**: Streams large files without loading entirely into memory
- **Windows compatible**: Built and tested on Windows with uv

## Output Format

Each chunk includes:
- Chunk metadata (part X of Y)
- File list and line counts
- Complete diff headers
- Contextual diff content
- Summary statistics

## Supported Formats

- Git diff output (`git diff`)
- Unified diff format (`diff -u`)
- Multiple file changes in single diff
- Binary file change indicators

## Development

### Setup development environment
```bash
# Clone and setup
git clone https://github.com/peteretelej/diffchunk.git
cd diffchunk
uv sync --dev

# Run tests
uv run pytest

# Run linting
uv run ruff check
```

### Project Structure
```
diffchunk/
├── pyproject.toml          # uv configuration
├── src/diffchunk/          # Source code
├── tests/                  # Test files
└── docs/                   # Documentation
```

