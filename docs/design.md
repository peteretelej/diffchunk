# diffchunk MCP Server Design

## Overview

diffchunk is an MCP server that breaks large diff files into navigable chunks. LLMs can locate specific changes by file patterns and analyze diffs that exceed context window limits.

## Problem

Large diffs present multiple issues:

- **Context limits**: 50k+ line diffs exceed LLM context windows (Claude: 200k tokens ≈ 40k lines)
- **Cost**: Large contexts consume expensive tokens unnecessarily
- **Relevance**: Most diff content is irrelevant to specific analysis tasks
- **Lost context**: Blind chunking breaks file relationships and diff metadata
- **Manual overhead**: Hand-splitting diffs is time-consuming and error-prone

## Solution

Path-based navigation system with auto-loading MCP tools:

1. **load_diff** - Parse diff file with custom settings (optional)
2. **list_chunks** - Get chunk summaries with file mappings (auto-loads)
3. **get_chunk** - Retrieve specific chunk content (auto-loads)
4. **find_chunks_for_files** - Locate chunks by file patterns (auto-loads)

## Project Structure

```
diffchunk/
├── src/                    # MCP server implementation
│   ├── main.py            # CLI entry point
│   ├── server.py          # MCP server
│   ├── tools.py           # MCP tools (load_diff, get_chunk, etc)
│   ├── models.py          # Data models (DiffSession, DiffChunk)
│   ├── parser.py          # Diff parsing logic
│   └── chunker.py         # Chunking engine
├── tests/                 # Test suites with real diff files
├── docs/
│   ├── design.md          # This design document
│   └── maintenance.md     # Publishing and CI/CD guide
└── README.md              # Installation and usage
```

**Key files**: `README.md` for users, `docs/maintenance.md` for maintainers, this design doc (docs/design.md) for implementation details.

## API

### Tools

#### load_diff (Optional)

```python
def load_diff(
    absolute_file_path: str,
    max_chunk_lines: int = 4000,
    skip_trivial: bool = True,
    skip_generated: bool = True,
    include_patterns: str = None,
    exclude_patterns: str = None
) -> dict
```

**Parameters:**
- `absolute_file_path`: Absolute path to diff file
- `max_chunk_lines`: Maximum lines per chunk (default: 4000)
- `skip_trivial`: Skip whitespace-only changes (default: true)
- `skip_generated`: Skip build artifacts, lock files (default: true)
- `include_patterns`: Comma-separated file patterns to include
- `exclude_patterns`: Comma-separated file patterns to exclude

Returns: Overview with total chunks, file count, basic statistics

#### list_chunks (Auto-Loading)

```python
def list_chunks(absolute_file_path: str) -> list
```

**Parameters:**
- `absolute_file_path`: Absolute path to diff file

Returns: Array of chunk info with file names, line counts, summaries

#### get_chunk (Auto-Loading)

```python
def get_chunk(absolute_file_path: str, chunk_number: int, include_context: bool = True) -> str
```

**Parameters:**
- `absolute_file_path`: Absolute path to diff file
- `chunk_number`: Chunk number to retrieve (1-indexed)
- `include_context`: Include chunk header with metadata

Returns: Formatted diff chunk content

#### find_chunks_for_files (Auto-Loading)

```python
def find_chunks_for_files(absolute_file_path: str, pattern: str) -> list
```

**Parameters:**
- `absolute_file_path`: Absolute path to diff file
- `pattern`: Glob pattern to match file paths

Returns: Array of chunk numbers containing files matching pattern

### Resources

- `diffchunk://current` - Overview of loaded diff

## Implementation

### Architecture

```
Diff File → Canonicalize Path → Hash Content → Cache Check → Parse → Filter → Chunk → Index → Navigation API
```

### Path-Based State Management

- **File Key**: `canonical_path + content_hash` for unique identification
- **Auto-Loading**: Tools automatically load diff files as needed
- **Change Detection**: Modified files trigger automatic reload via content hashing
- **Multi-File Support**: Each diff file maintains separate session state

### Chunking Strategy

- Prefer file boundaries to maintain context
- Respect max_chunk_lines limit (default 4000)
- Track file-to-chunk mapping for navigation
- Preserve diff headers and context lines

### Storage

- **Path-based sessions**: `Dict[file_key, DiffSession]`
- **Content hashing**: SHA-256 for file change detection
- **Cross-platform paths**: `os.path.realpath()` for canonical paths
- **In-memory chunk index**: File pattern matching via glob patterns

### Core Classes

```python
class DiffChunkTools:
    sessions: Dict[str, DiffSession]  # file_key -> session
    
    def _get_file_key(self, absolute_file_path: str) -> str:
        """Generate unique key from canonical path + content hash."""
        
    def _ensure_loaded(self, absolute_file_path: str, **kwargs) -> str:
        """Auto-load diff if not cached, return file key."""

class DiffSession:
    file_path: str
    chunks: List[DiffChunk]
    file_to_chunks: Dict[str, List[int]]
    stats: DiffStats

class ChunkInfo:
    chunk_number: int
    files: List[str]
    line_count: int
    summary: str
```

## Usage Examples

### Auto-Loading Navigation

```python
# Any tool can be called first - they auto-load with defaults
list_chunks("/tmp/feature.diff")  # Auto-loads and shows all chunks
get_chunk("/tmp/feature.diff", 1)  # Auto-loads and gets first chunk

# load_diff only needed for custom settings
load_diff("/tmp/feature.diff", max_chunk_lines=2000)
```

### Pattern-Based Navigation

```python
# All tools auto-load if needed
find_chunks_for_files("/tmp/feature.diff", "*.py")        # Python files → [1, 3, 5]
find_chunks_for_files("/tmp/feature.diff", "*test*")      # Test files → [2, 6]
find_chunks_for_files("/tmp/feature.diff", "src/*")       # Source directory → [1, 3, 4]
```

### Multi-File Usage

```python
# Each file maintains separate state
list_chunks("/tmp/feature-auth.diff")     # Auth feature changes
list_chunks("/tmp/feature-ui.diff")       # UI feature changes
get_chunk("/tmp/feature-auth.diff", 1)    # First chunk of auth changes
```

## Configuration

### Required Parameters

- `absolute_file_path`: **Required**. Absolute path to diff file for all tools.

### Auto-Loading Defaults

When tools auto-load diffs, they use these defaults:
- `max_chunk_lines`: 4000 (LLM context optimized)
- `skip_trivial`: true (skip whitespace-only changes)
- `skip_generated`: true (skip lock files, build artifacts)
- `include_patterns`: none (include all files)
- `exclude_patterns`: none (exclude no files)

### Explicit Control via load_diff

Use `load_diff` for custom settings:
- `max_chunk_lines`: Custom chunk size
- `skip_trivial`: Control whitespace handling
- `skip_generated`: Control generated file handling
- `include_patterns`: Comma-separated glob patterns to include
- `exclude_patterns`: Comma-separated glob patterns to exclude

### Path Resolution

The server handles paths as follows:
1. All paths must be absolute (no relative path support)
2. Paths are canonicalized using `os.path.realpath()`
3. Cross-platform compatibility (Windows/Unix)
4. User home directory expansion (`~`) is supported
5. Content hashing detects file changes for cache invalidation

## Performance

- Target: <1 second navigation for 100k+ line diffs
- Memory efficient: stream processing, lazy chunk loading
- File-based input eliminates parameter size limits

## Error Handling

- Validate file existence and readability
- Verify diff format before processing
- Graceful degradation for malformed sections
- Clear error messages for invalid patterns

## Benefits

- **Auto-Loading**: Seamless UX with no session management complexity
- **Multi-File Support**: Each diff file maintains separate state
- **Change Detection**: Automatic reload when files are modified
- **Direct Navigation**: Jump to relevant changes by file pattern
- **Context Preservation**: Maintain file relationships and diff metadata
- **Scale**: Handle enterprise-size diffs efficiently
- **Integration**: Works with existing git/diff workflows
- **Language Agnostic**: No assumptions about code structure or language
- **Cross-Platform**: Robust path handling for Windows/Unix systems
