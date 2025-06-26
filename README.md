# diffchunk

[![CI](https://github.com/peteretelej/diffchunk/actions/workflows/ci.yml/badge.svg)](https://github.com/peteretelej/diffchunk/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/peteretelej/diffchunk/branch/main/graph/badge.svg)](https://codecov.io/gh/peteretelej/diffchunk)
[![PyPI version](https://badge.fury.io/py/diffchunk.svg)](https://badge.fury.io/py/diffchunk)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)

MCP server for navigating large diff files. Jump directly to relevant changes instead of processing entire diffs sequentially.

## Problem

Large diffs create analysis bottlenecks:

- Context limits: 50k+ line diffs exceed LLM context windows
- Token costs: Processing irrelevant changes wastes expensive tokens
- Poor targeting: Most diff content is unrelated to specific analysis goals
- Lost context: Manual splitting breaks file relationships and metadata

## Solution

MCP server with 4 diff navigation tools:

- `load_diff` - Parse diff file and get overview
- `list_chunks` - Show chunks with file mappings
- `get_chunk` - Retrieve specific chunk content
- `find_chunks_for_files` - Locate chunks by file patterns

Solution Design: [docs/design.md](docs/design.md)

## Installation

### Option 1: uvx (Recommended)

No installation required - runs directly:

```bash
uvx --from diffchunk diffchunk-mcp
```

### Option 2: PyPI

```bash
pip install diffchunk
```

## MCP Configuration

Add to your MCP client:

**uvx (recommended):**

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

**PyPI install:**

```json
{
  "mcpServers": {
    "diffchunk": {
      "command": "diffchunk-mcp"
    }
  }
}
```

## Quick Start

1. Generate diff file:

```bash
git diff main..feature-branch > /tmp/changes.diff
```

2. Load in LLM:

```
load_diff("/tmp/changes.diff", "/path/to/project")
→ {"chunks": 5, "files": 23, "total_lines": 8432}
```

3. Navigate and analyze:

```
list_chunks()
→ [{"chunk": 1, "files": ["api/auth.py", "models/user.py"], "lines": 1205}, ...]

find_chunks_for_files("*test*")
→ [2, 4]

get_chunk(1)
→ "=== Chunk 1 of 5 ===\ndiff --git a/api/auth.py..."
```

## Usage Examples

### Large Feature Review

```bash
git diff main..feature-auth > auth-changes.diff
```

```
load_diff("auth-changes.diff", "/path/to/project")
list_chunks()  # Overview of all changes
find_chunks_for_files("*controller*")  # API endpoints → [1, 3]
find_chunks_for_files("*test*")        # Tests → [2, 5]
get_chunk(1)   # Analyze API changes
```

### Targeted Analysis

```
# Focus on specific file types
find_chunks_for_files("*.py")       # Python code → [1, 3, 4]
find_chunks_for_files("*.json")     # Config files → [2]
find_chunks_for_files("src/core/*") # Core module → [1, 4]

# Skip to relevant sections
get_chunk(3)  # Direct access to specific changes
```

## Configuration Options

### load_diff Parameters

- `file_path`: Path to diff file (absolute or relative to working_directory) 
- `working_directory`: **Required**. Directory to resolve relative file paths from
- `max_chunk_lines`: Lines per chunk (default: 4000)
- `skip_trivial`: Skip whitespace-only changes (default: true)
- `skip_generated`: Skip build artifacts, lock files (default: true)
- `include_patterns`: Comma-separated file patterns to include
- `exclude_patterns`: Comma-separated file patterns to exclude

### Path Resolution

The MCP server requires a `working_directory` parameter to properly resolve file paths:

- **Absolute paths**: Used directly (e.g., `/home/user/project/changes.diff`)
- **Relative paths**: Resolved against `working_directory` (e.g., `changes.diff` + `/home/user/project/`)
- **Cross-platform**: Handles Windows (`C:\path`) and Unix (`/path`) formats automatically
- **Home directory**: Supports `~` expansion for both parameters

### Examples

**Absolute path:**
```
load_diff(
    "/home/user/project/changes.diff",
    "/home/user/project",
    max_chunk_lines=2000
)
```

**Relative path:**
```
load_diff(
    "changes.diff",
    "/home/user/project", 
    max_chunk_lines=2000
)
```

**Windows paths:**
```
load_diff(
    "changes.diff",
    "C:\\Users\\user\\project",
    max_chunk_lines=2000
)
```

**With filtering:**
```
load_diff(
    "/tmp/large.diff",
    "/path/to/project",
    max_chunk_lines=2000,
    include_patterns="*.py,*.js",
    exclude_patterns="*test*,*spec*"
)
```

**MCP Client Usage:**
When using with Cline or other MCP clients, ensure the client provides both parameters:
```json
{
  "file_path": "comparison_diff.patch",
  "working_directory": "/path/to/your/project"
}
```

## Supported Formats

- Git diff output (`git diff`, `git show`)
- Unified diff format (`diff -u`)
- Multiple files in single diff
- Binary file change indicators

## Performance

- Handles 100k+ line diffs in under 1 second
- Memory efficient streaming for large files
- File-based input avoids parameter size limits

## Benefits

- **Cost reduction**: Process only relevant changes, reduce token usage
- **Fast navigation**: Jump directly to files or areas of interest
- **Context preservation**: Maintain file relationships and diff metadata
- **Language agnostic**: Works with any codebase or diff format
- **Enterprise ready**: Handles large feature branches and refactoring diffs

## Development

### Quick Setup

```bash
# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh  # Linux/macOS
# OR: powershell -c "irm https://astral.sh/uv/install.ps1 | iex"  # Windows

# Clone and setup
git clone https://github.com/peteretelej/diffchunk.git
cd diffchunk
uv sync

# Run tests to verify setup
uv run pytest

# Start MCP server
uv run python -m src.main
```

### GitHub Direct Install

For development or latest features:

```bash
uvx --from git+https://github.com/peteretelej/diffchunk diffchunk-mcp
```

**MCP Configuration:**

```json
{
  "mcpServers": {
    "diffchunk": {
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/peteretelej/diffchunk",
        "diffchunk-mcp"
      ]
    }
  }
}
```

### Prerequisites

- Python 3.10+
- [uv](https://docs.astral.sh/uv/) package manager

### Detailed Setup

**Windows:**

```cmd
# Install uv
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# Clone and setup
git clone https://github.com/peteretelej/diffchunk.git
cd diffchunk
uv sync
```

**Linux/macOS:**

```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone and setup
git clone https://github.com/peteretelej/diffchunk.git
cd diffchunk
uv sync
```

### Running the MCP Server

```bash
uv run python -m src.main
```

### Testing

**Run all tests:**

```bash
uv run pytest
```

**Run specific test suites:**

```bash
# Integration tests with real diff files
uv run pytest tests/test_integration.py -v

# MCP component tests
uv run pytest tests/test_mcp_components.py -v
```

**Test with real data:**
The tests automatically use real diff files from `tests/test_data/`. To manually test:

```bash
# Create your own test diff
git diff HEAD~10..HEAD > test.diff

# Then use the MCP client to test load_diff tool
# (see MCP Integration Testing section below)
```

### Code Quality

**Formatting and linting:**

```bash
uv run ruff check
uv run ruff format
```

**Type checking:**

```bash
uv run mypy src/
```

### Project Structure

```
diffchunk/
├── src/
│   ├── __init__.py       # Package initialization
│   ├── main.py           # CLI entry point
│   ├── server.py         # MCP server implementation
│   ├── tools.py          # MCP tool functions
│   ├── models.py         # Data models
│   ├── parser.py         # Diff parsing logic
│   └── chunker.py        # Chunking engine
├── tests/
│   └── test_data/        # Real diff files for testing
├── docs/
│   └── designs/          # Implementation plans
├── pyproject.toml        # Project configuration
└── README.md
```

### MCP Integration Testing

1. **Start the server locally:**

   ```bash
   uv run python -m src.main
   ```

2. **Test with MCP client** (e.g., Claude Desktop):
   Add to your MCP client configuration (usually `~/.config/claude-desktop/claude_desktop_config.json`):

   ```json
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

3. **Verify server works:**

   ```bash
   # Create test diff
   git diff HEAD~5..HEAD > test.diff

   # Use MCP client or automated tests
   uv run pytest tests/test_mcp_components.py::TestMCPComponents::test_diffchunk_tools_complete_workflow -v
   ```

### Development Workflow

**Making changes:**

```bash
# Make code changes
# ...

# Run tests
uv run pytest

# Check code quality
uv run ruff check
uv run ruff format
uv run mypy src/

# Test MCP server manually (optional)
uv run python -m src.main
```

### Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make changes and test: `uv run pytest`
4. Check code quality: `uv run ruff check && uv run ruff format`
5. Submit pull request

### Troubleshooting

**Common issues:**

- **Import errors**: Ensure you're using `uv run` for all commands
- **File not found**: Verify both `file_path` and `working_directory` are correct
- **Path resolution errors**: Use absolute paths or double-check relative path + working directory
- **Permission errors**: Check file permissions for diff files and working directory access
- **Memory issues**: Use smaller `max_chunk_lines` for very large diffs

**Path troubleshooting:**
```bash
# Check if file exists from working directory
cd /your/working/directory
ls -la your-diff-file.diff

# Use absolute paths to avoid confusion
load_diff("/absolute/path/to/diff.patch", "/absolute/path/to/project")
```

# License

[MIT](./LICENSE)
