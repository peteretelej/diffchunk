# diffchunk Design Document

## Overview

**diffchunk** is a Python CLI tool that enables Large Language Models (LLMs) to consume and analyze large diff files by breaking them into manageable, contextual chunks. The tool addresses the common problem where diff files exceed LLM context windows, making comprehensive code review impossible.

## Problem Statement

- Large diff files (50k+ LOC) cannot fit in LLM context windows
- Manual chunking loses important context and file relationships
- Trivial changes (whitespace, newlines) add noise without value
- Need systematic way to review all changes sequentially

## Solution Architecture

### Core Components

#### 1. DiffParser (`parser.py`)
- Parse unified diff format
- Extract file-level metadata
- Identify change types (additions, deletions, modifications)
- Calculate statistics (total lines, affected files)

#### 2. DiffChunker (`chunker.py`)
- Split large diffs into logical parts
- Preserve file boundaries and context
- Maintain header information for each chunk
- Support configurable chunk sizes

#### 3. ChangeFilter (`filters.py`)
- Skip trivial changes (whitespace-only, newline-only)
- Filter based on change significance
- Configurable filtering rules

#### 4. CLI Interface (`cli.py`)
- Command-line argument parsing
- Progress tracking and user feedback
- Output formatting for LLM consumption

### Data Flow

```
Large Diff File → DiffParser → ChangeFilter → DiffChunker → Formatted Output
```

## Command Interface

### Basic Usage
```bash
# Get diff metadata
diffchunk.py large.diff
# Output: Total lines: 50000, Files changed: 25, Chunks available: 10

# Get specific chunk
diffchunk.py large.diff --part 1
# Output: Formatted diff chunk with context
```

### Advanced Options
```bash
# Skip trivial changes
diffchunk.py large.diff --part 1 --skip-trivial

# Custom chunk size
diffchunk.py large.diff --part 1 --max-lines 2000

# Show only specific file types
diffchunk.py large.diff --part 1 --include "*.py,*.js"
```

## Technical Specifications

### Input Format
- Standard unified diff format (`git diff`, `diff -u`)
- Support for multiple file changes in single diff
- Handle binary file indicators

### Output Format
- Preserve diff headers and context
- Add chunk metadata (part X of Y)
- Include file summaries for context
- Format optimized for LLM consumption

### Chunking Strategy
1. **File-boundary chunking**: Split at file boundaries when possible
2. **Line-limit chunking**: Split within files if they exceed limits
3. **Context preservation**: Maintain sufficient context lines
4. **Header inclusion**: Include relevant file headers in each chunk

### Filtering Rules
- Skip changes with only whitespace modifications
- Skip single newline additions/removals
- Skip changes in generated files (configurable patterns)
- Preserve significant formatting changes

## Implementation Details

### Dependencies
- Python 3.8+
- No external dependencies for core functionality
- Optional: `rich` for enhanced CLI output

### Error Handling
- Graceful handling of malformed diff files
- Clear error messages for invalid inputs
- Fallback strategies for edge cases

### Performance Considerations
- Stream processing for large files
- Memory-efficient chunking
- Lazy loading of diff content

## File Structure

```
diffchunk/
├── pyproject.toml          # uv project configuration
├── README.md              # User documentation
├── docs/
│   └── design.md          # This document
├── src/
│   └── diffchunk/
│       ├── __init__.py    # Package initialization
│       ├── cli.py         # Command-line interface
│       ├── parser.py      # Diff parsing logic
│       ├── chunker.py     # Chunking algorithms
│       └── filters.py     # Change filtering
└── tests/
    ├── __init__.py
    ├── test_parser.py     # Parser tests
    ├── test_chunker.py    # Chunker tests
    └── fixtures/          # Test diff files
```

## Future Enhancements

### Phase 2 Features
- Interactive mode for chunk navigation
- Integration with popular diff tools
- Custom output formats (JSON, XML)
- Diff comparison and merging capabilities

### Phase 3 Features
- Web interface for diff visualization
- API for programmatic access
- Plugin system for custom filters
- Integration with code review tools

## Success Metrics

- Ability to process diffs up to 100k+ LOC
- Chunk sizes suitable for common LLM context windows (4k-32k tokens)
- Filtering reduces noise by 30-50% in typical diffs
- Processing time under 5 seconds for 50k LOC diffs
