# diffchunk MCP Server Design

## Overview

MCP server that chunks large diff files for efficient LLM navigation. Uses file-based state management with auto-loading tools.

## Architecture

```
Diff File → Canonicalize Path → Hash Content → Cache Check → Parse → Filter → Chunk → Index → Tools
```

## Tools

### load_diff (Optional)

```python
def load_diff(
    absolute_file_path: str,
    max_chunk_lines: int = 1000,
    skip_trivial: bool = True,
    skip_generated: bool = True,
    include_patterns: Optional[str] = None,
    exclude_patterns: Optional[str] = None,
) -> Dict[str, Any]
```

**Returns:** `{"chunks": int, "files": int, "total_lines": int, "file_path": str}`

### list_chunks (Auto-loading)

```python
def list_chunks(absolute_file_path: str) -> List[Dict[str, Any]]
```

**Returns:** Array of chunk metadata with files, line counts, summaries

### get_chunk (Auto-loading)

```python
def get_chunk(
    absolute_file_path: str, 
    chunk_number: int, 
    include_context: bool = True
) -> str
```

**Returns:** Formatted diff chunk content

### find_chunks_for_files (Auto-loading)

```python
def find_chunks_for_files(absolute_file_path: str, pattern: str) -> List[int]
```

**Returns:** Array of chunk numbers matching glob pattern

### get_current_overview

```python
def get_current_overview() -> Dict[str, Any]
```

**Returns:** Overview of all loaded diff sessions

## Data Models

```python
@dataclass
class DiffChunk:
    number: int
    content: str
    files: List[str]
    line_count: int
    parent_file: str | None = None        # For large file sub-chunks
    sub_chunk_index: int | None = None    # Sub-chunk position

@dataclass
class ChunkInfo:
    chunk_number: int
    files: List[str]
    line_count: int
    summary: str
    parent_file: str | None = None
    sub_chunk_index: int | None = None

@dataclass 
class DiffSession:
    file_path: str
    chunks: List[DiffChunk]
    file_to_chunks: Dict[str, List[int]]  # file_path -> chunk_numbers
    stats: DiffStats

@dataclass
class DiffStats:
    total_files: int
    total_lines: int
    chunks_count: int
```

## Implementation Details

### State Management

- **File Key:** `canonical_path + "#" + content_hash[:16]`
- **Sessions:** `Dict[file_key, DiffSession]`
- **Auto-loading:** Tools load diff files on first access
- **Change Detection:** SHA-256 content hashing triggers reload

### Chunking Strategy

1. **Target Size:** 80% of `max_chunk_lines` (default 1000) for buffer
2. **Boundaries:** Prefer file boundaries, split at hunk headers if needed
3. **Large Files:** Split at `@@ ... @@` hunk boundaries
4. **Sub-chunks:** Track parent file and index for oversized files
5. **Context:** Preserve diff headers in each chunk

### Path Handling

- **Required:** Absolute paths only
- **Canonicalization:** `os.path.realpath()` for unique keys
- **Cross-platform:** Windows and Unix path support
- **Home expansion:** `~` supported

### Error Handling

- File existence validation
- Diff format verification
- Graceful handling of malformed sections
- Clear error messages for invalid patterns

## Project Structure

```
src/
├── main.py           # CLI entry point
├── server.py         # MCP server (DiffChunkServer)
├── tools.py          # MCP tools (DiffChunkTools)
├── models.py         # Data models
├── parser.py         # Diff parsing (DiffParser)
└── chunker.py        # Chunking logic (DiffChunker)
```

## Resources

- `diffchunk://current` - Overview of loaded diffs via MCP resource protocol

## Performance

- Target: <1 second for 100k+ line diffs
- Memory efficient streaming
- Lazy chunk loading
- File-based input (no parameter size limits)