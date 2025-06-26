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

File-based navigation system with four MCP tools:

1. **load_diff** - Parse diff file, return chunk overview
2. **list_chunks** - Get chunk summaries with file mappings
3. **get_chunk** - Retrieve specific chunk content
4. **find_chunks_for_files** - Locate chunks by file patterns

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

#### load_diff

```python
def load_diff(
    file_path: str,
    max_chunk_lines: int = 4000,
    skip_trivial: bool = True,
    skip_generated: bool = True,
    include_patterns: str = None,
    exclude_patterns: str = None
) -> dict
```

Returns: Overview with total chunks, file count, basic statistics

#### list_chunks

```python
def list_chunks() -> list
```

Returns: Array of chunk info with file names, line counts, summaries

#### get_chunk

```python
def get_chunk(chunk_number: int, include_context: bool = True) -> str
```

Returns: Formatted diff chunk content

#### find_chunks_for_files

```python
def find_chunks_for_files(pattern: str) -> list
```

Returns: Array of chunk numbers containing files matching pattern

### Resources

- `diffchunk://current` - Overview of loaded diff

## Implementation

### Architecture

```
Diff File → Parse → Filter → Chunk → Index → Navigation API
```

### Chunking Strategy

- Prefer file boundaries to maintain context
- Respect max_chunk_lines limit (default 4000)
- Track file-to-chunk mapping for navigation
- Preserve diff headers and context lines

### Storage

- Single diff per session (stateless)
- In-memory chunk index
- File pattern matching via glob patterns

### Core Classes

```python
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

### Basic Navigation

```python
load_diff("/tmp/feature.diff")
list_chunks()  # See all chunks with file info
get_chunk(1)   # Analyze first chunk
```

### Pattern-Based Navigation

```python
find_chunks_for_files("*.py")        # Python files → [1, 3, 5]
find_chunks_for_files("*test*")      # Test files → [2, 6]
find_chunks_for_files("src/*")       # Source directory → [1, 3, 4]
```

## Configuration

### Filtering Options

- `skip_trivial`: Skip whitespace-only changes (default: true)
- `skip_generated`: Skip lock files, build artifacts (default: true)
- `include_patterns`: Comma-separated glob patterns
- `exclude_patterns`: Comma-separated glob patterns

### Defaults

- Chunk size: 4000 lines (LLM context optimized)
- File boundary preference over line limits
- Preserve diff context and headers

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

- **Direct Navigation**: Jump to relevant changes by file pattern
- **Context Preservation**: Maintain file relationships and diff metadata
- **Scale**: Handle enterprise-size diffs efficiently
- **Integration**: Works with existing git/diff workflows
- **Language Agnostic**: No assumptions about code structure or language
