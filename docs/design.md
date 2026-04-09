# diffchunk MCP Server Design

## Overview

MCP server that chunks large diff files for efficient LLM navigation. Uses file-based state management with auto-loading tools.

## Architecture

```
Diff File → Canonicalize Path → Hash Content → Cache Check → Parse → Filter → Chunk → Index → Tools
```

The server uses FastMCP with module-level `@mcp.tool()` decorated sync functions (not a class). Resources use `@mcp.resource()`. Error handling is automatic: `ValueError` raised in any tool function is caught by FastMCP and returned as `CallToolResult(isError=True)`. All tools have `annotations={"readOnlyHint": True}` and `structured_output=False` (to prevent `outputSchema` generation).

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
    context_lines: Optional[int] = None,
) -> Dict[str, Any]
```

**Returns:** `{"chunks": int, "files": int, "total_lines": int, "file_path": str, "files_excluded": int}`

### list_chunks (Auto-loading)

```python
def list_chunks(absolute_file_path: str) -> Dict[str, Any]
```

**Returns:** Dictionary with `chunks` (array of chunk metadata with files, line counts, token counts, summaries, and `file_details`) and `total_token_count` (sum of all chunk token counts)

```json
{
  "chunks": [
    {
      "chunk": 1,
      "files": ["src/main.py", "src/utils.py"],
      "file_details": [
        {"path": "src/main.py", "lines": 120},
        {"path": "src/utils.py", "lines": 45}
      ],
      "lines": 165,
      "token_count": 412,
      "summary": "2 files, 165 lines"
    }
  ],
  "total_token_count": 412
}
```

### get_chunk (Auto-loading)

```python
def get_chunk(
    absolute_file_path: str, 
    chunk_number: int, 
    include_context: bool = True,
    format: str = "raw",
) -> str
```

**Returns:** Formatted diff chunk content

### find_chunks_for_files (Auto-loading)

```python
def find_chunks_for_files(absolute_file_path: str, pattern: str) -> List[int]
```

**Returns:** Array of chunk numbers matching glob pattern

### get_file_diff (Auto-loading)

```python
def get_file_diff(absolute_file_path: str, file_path: str) -> str
```

**Parameters:**
- `file_path` – Exact path or glob pattern that matches exactly one file in the diff. Must be a non-empty, non-whitespace string.

**Returns:** Formatted string with the `diff --git` header and all hunks for the specified file.
Raises `ValueError` if `file_path` is empty or whitespace-only, or if the pattern matches zero or more than one file.

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
    file_line_counts: Dict[str, int] = field(default_factory=dict)  # Per-file line counts

@dataclass
class ChunkInfo:
    chunk_number: int
    files: List[str]
    line_count: int
    summary: str
    token_count: int = 0                                        # Estimated token count (len(content) // 4)
    parent_file: str | None = None
    sub_chunk_index: int | None = None
    file_details: List[Dict[str, Any]] = field(default_factory=list)  # [{"path": str, "lines": int}]

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
- Actionable error messages that guide LLMs to self-correct
- `ValueError` automatically surfaces as `isError=True` through FastMCP

## Project Structure

```
src/
├── main.py           # CLI entry point
├── server.py         # MCP server (FastMCP module-level tools)
├── tools.py          # MCP tools (DiffChunkTools)
├── models.py         # Data models (DiffStats, FormatMode, etc.)
├── parser.py         # Diff parsing (DiffParser) and context reduction
├── chunker.py        # Chunking logic (DiffChunker)
└── formatter.py      # Output formatting (annotated, compact)
```

## Resources

- `diffchunk://current` - Overview of loaded diffs via `@mcp.resource("diffchunk://current")` decorator

### File Matching

- Pattern matching (glob) is case-insensitive, matching macOS/Windows filesystem behavior
- Both `find_chunks_for_files` and `get_file_diff` use case-insensitive comparison

## Format Options

### FormatMode Enum

```python
class FormatMode(str, Enum):
    RAW = "raw"          # Default - unmodified diff output
    ANNOTATED = "annotated"  # Structured with line numbers and hunk separation
    COMPACT = "compact"      # Token-efficient, new hunks only
```

`FormatMode` inherits from `str, Enum` so values compare directly with strings.

### `format` Parameter on `get_chunk`

The `format` parameter is a display-time parameter on `get_chunk`. It transforms output for rendering but stored data always remains raw.

```python
def get_chunk(
    absolute_file_path: str,
    chunk_number: int,
    include_context: bool = True,
    format: str = "raw",
) -> str
```

- `"raw"` (default) - returns the original diff content, identical to pre-feature behavior
- `"annotated"` - structured output with `## File:` headers, `__new hunk__`/`__old hunk__` separation, new-file line numbers, and function context from `@@` headers
- `"compact"` - token-efficient output showing only new hunks (context + added lines), omitting removed lines and `__old hunk__` sections

Invalid format values raise `ValueError` listing valid options.

### `context_lines` Parameter on `load_diff`

A load-time parameter that reduces context lines per hunk before chunking. Implemented via `DiffParser.reduce_context()`.

```python
def load_diff(
    absolute_file_path: str,
    ...,
    context_lines: Optional[int] = None,
) -> Dict[str, Any]
```

- `None` (default) - keeps all context lines from the original diff
- `0` - keeps only added/removed lines, no context
- `N` - keeps up to N context lines before and after each change

Overlapping context windows between nearby changes preserve shared context lines. Hunk headers are recalculated after reduction. Negative values raise `ValueError`.

### `files_excluded` in `DiffStats`

```python
@dataclass
class DiffStats:
    total_files: int
    total_lines: int
    chunks_count: int
    files_excluded: int = 0
```

When `exclude_patterns` is used with `load_diff`, the `files_excluded` count reports how many files were removed by the patterns. This count is included in the `load_diff` response.

### Feature Composition

`format` and `context_lines` compose correctly: `context_lines` reduces context at load time (stored in the session), then `format` transforms the already-reduced content at display time. Both can be used alongside `exclude_patterns`.

## Performance

- Target: <1 second for 100k+ line diffs
- Memory efficient streaming
- Lazy chunk loading
- File-based input (no parameter size limits)