# diffchunk

MCP server for navigating large diff files. Jump directly to relevant changes instead of processing entire diffs sequentially.

## Problem

Large diffs create analysis bottlenecks:
- Context limits: 50k+ line diffs exceed LLM context windows
- Token costs: Processing irrelevant changes wastes expensive tokens
- Poor targeting: Most diff content is unrelated to specific analysis goals
- Lost context: Manual splitting breaks file relationships and metadata

## Solution

MCP server with 4 navigation tools:
- `load_diff` - Parse diff file and get overview
- `list_chunks` - Show chunks with file mappings
- `get_chunk` - Retrieve specific chunk content
- `find_chunks_for_files` - Locate chunks by file patterns

## Installation

### Option 1: PyPI (Recommended)
```bash
pip install diffchunk
```

### Option 2: uvx (No Installation)
```bash
uvx --from diffchunk diffchunk-mcp
```

### Option 3: GitHub Direct
```bash
uvx --from git+https://github.com/peteretelej/diffchunk diffchunk-mcp
```

## MCP Configuration

Add to your MCP client:

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

**uvx install:**
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

**GitHub direct:**
```json
{
  "mcpServers": {
    "diffchunk": {
      "command": "uvx", 
      "args": ["--from", "git+https://github.com/peteretelej/diffchunk", "diffchunk-mcp"]
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
load_diff("/tmp/changes.diff")
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
load_diff("auth-changes.diff")
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
- `max_chunk_lines`: Lines per chunk (default: 4000)
- `skip_trivial`: Skip whitespace-only changes (default: true)
- `skip_generated`: Skip build artifacts, lock files (default: true)
- `include_patterns`: Comma-separated file patterns to include
- `exclude_patterns`: Comma-separated file patterns to exclude

### Example
```
load_diff(
    "/tmp/large.diff",
    max_chunk_lines=2000,
    include_patterns="*.py,*.js",
    exclude_patterns="*test*,*spec*"
)
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

### Prerequisites

- Python 3.10+
- [uv](https://docs.astral.sh/uv/) package manager

### Local Setup

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
uv run src/main.py
```

### Testing

**Run tests:**
```bash
uv run pytest
```

**Test with real data:**
```bash
# Load test diff file
echo 'load_diff("tests/test_data/go_version_upgrade_1.22_to_1.23.diff")' | uv run src/main.py

# Or create your own test diff
git diff HEAD~10..HEAD > test.diff
echo 'load_diff("test.diff")' | uv run src/main.py
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

1. **Start the server:**
   ```bash
   uv run src/main.py
   ```

2. **Test with MCP client** (e.g., Claude Desktop):
   Add to MCP configuration:
   ```json
   {
     "mcpServers": {
       "diffchunk-dev": {
         "command": "uv",
         "args": ["run", "src/main.py"],
         "cwd": "/path/to/diffchunk"
       }
     }
   }
   ```

3. **Manual testing:**
   ```bash
   # Create test diff
   git diff HEAD~5..HEAD > test.diff
   
   # Test server
   echo '{"method": "tools/call", "params": {"name": "load_diff", "arguments": {"file_path": "test.diff"}}}' | uv run src/main.py
   ```

### Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make changes and test: `uv run pytest`
4. Format code: `uv run ruff format`
5. Submit pull request

### Troubleshooting

**Common issues:**

- **Import errors**: Ensure you're using `uv run` for all commands
- **File not found**: Use absolute paths for diff files or ensure correct working directory
- **Permission errors**: Check file permissions for diff files
- **Memory issues**: Use smaller `max_chunk_lines` for very large diffs