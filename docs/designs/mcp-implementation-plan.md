# diffchunk MCP Server Implementation Plan

## Overview
Complete rewrite of diffchunk as an MCP server following the new design specification. The implementation will be built from scratch with a focus on simplicity, clarity, and performance.

## Architecture Summary
```
MCP Client → MCP Server → DiffSession → DiffParser → Chunks
                ↓
        [load_diff, list_chunks, get_chunk, find_chunks_for_files]
```

## Core Components

### 1. Data Models (`src/models.py`)
```python
@dataclass
class DiffStats:
    total_files: int
    total_lines: int 
    chunks_count: int
    
@dataclass  
class ChunkInfo:
    chunk_number: int
    files: List[str]
    line_count: int
    summary: str
    
@dataclass
class DiffChunk:
    number: int
    content: str
    files: List[str]
    line_count: int
    
class DiffSession:
    file_path: str
    chunks: List[DiffChunk]
    file_to_chunks: Dict[str, List[int]]
    stats: DiffStats
```

### 2. Diff Parser (`src/parser.py`)
- Parse unified diff format
- Extract file changes and metadata
- Handle binary files and special cases
- Filter trivial/generated files

### 3. Chunking Engine (`src/chunker.py`)
- Split diffs into manageable chunks
- Respect file boundaries when possible
- Maintain context and headers
- Build file-to-chunk index

### 4. MCP Tools (`src/tools.py`)
- `load_diff`: Parse and initialize session
- `list_chunks`: Return chunk summaries
- `get_chunk`: Retrieve specific chunk content
- `find_chunks_for_files`: Pattern-based chunk lookup

### 5. MCP Server (`src/server.py`)
- MCP protocol implementation
- Tool registration and routing
- Error handling and validation
- Session state management

### 6. Entry Point (`src/main.py`)
- CLI interface for MCP server
- Configuration handling
- Logging setup

## Implementation Steps

### Phase 1: Core Foundation
1. **Project Structure Setup**
   - Remove existing `src/` directory
   - Create new directory structure
   - Set up `pyproject.toml` with MCP dependencies

2. **Data Models**
   - Implement core dataclasses
   - Add validation and helper methods
   - Type hints throughout

### Phase 2: Diff Processing
3. **Diff Parser**
   - Unified diff format parsing
   - File change extraction
   - Binary file handling
   - Metadata preservation

4. **Chunking Engine**
   - File boundary detection
   - Size-based splitting with max_chunk_lines
   - Context preservation
   - Index building

### Phase 3: MCP Integration  
5. **MCP Tools Implementation**
   - Tool function definitions
   - Parameter validation
   - Error handling
   - Response formatting

6. **MCP Server Setup**
   - Protocol handler
   - Tool registration
   - Session management
   - Resource definitions

### Phase 4: Packaging & CLI
7. **Entry Point & CLI**
   - Command-line interface
   - Configuration options
   - Logging setup

8. **Package Configuration**
   - `pyproject.toml` with proper dependencies
   - Entry point definitions
   - Metadata and versioning

## File Structure
```
src/
├── __init__.py
├── main.py          # CLI entry point
├── server.py        # MCP server implementation  
├── tools.py         # MCP tool functions
├── models.py        # Data models
├── parser.py        # Diff parsing logic
├── chunker.py       # Chunking engine
└── utils.py         # Utilities and helpers
```

## Dependencies
- `mcp` - MCP server SDK
- `click` - CLI interface
- `fnmatch` - Pattern matching for file filters
- Standard library only for core logic

## Key Design Principles
1. **Simplicity**: Clear, readable code without unnecessary abstractions
2. **Performance**: Stream processing, lazy loading, efficient indexing
3. **Robustness**: Graceful error handling, input validation
4. **Stateless**: Single diff per session, no persistent storage
5. **Standards**: Follow MCP protocol, unified diff format

## Testing Strategy
- Unit tests for parser and chunker
- Integration tests for MCP tools
- Performance tests with large diffs
- Error case coverage

## Error Handling
- File not found/readable
- Invalid diff format
- Malformed patterns
- Chunk index out of bounds
- Memory/size limits

## Performance Targets
- <1 second for 100k+ line diffs
- Memory usage proportional to active chunks
- Lazy chunk loading
- Efficient pattern matching

## Configuration Options
- `max_chunk_lines`: Default 4000
- `skip_trivial`: Default true
- `skip_generated`: Default true  
- `include_patterns`: Optional file filters
- `exclude_patterns`: Optional file filters