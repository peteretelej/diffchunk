"""MCP server implementation for diffchunk."""

import json
from typing import Annotated, Optional

from mcp.server.fastmcp import FastMCP
from pydantic import Field

from .tools import DiffChunkTools

mcp = FastMCP("diffchunk")
tools = DiffChunkTools()


@mcp.resource("diffchunk://current")
def current_overview() -> str:
    """Overview of all currently loaded diff files."""
    return json.dumps(tools.get_current_overview(), indent=2)


@mcp.tool(annotations={"readOnlyHint": True}, structured_output=False)
def load_diff(
    absolute_file_path: Annotated[
        str, Field(description="Absolute path to the diff file to load")
    ],
    max_chunk_lines: Annotated[
        int, Field(description="Maximum lines per chunk")
    ] = 1000,
    skip_trivial: Annotated[
        bool, Field(description="Skip whitespace-only changes")
    ] = True,
    skip_generated: Annotated[
        bool, Field(description="Skip generated files and build artifacts")
    ] = True,
    include_patterns: Annotated[
        Optional[str],
        Field(description="Comma-separated glob patterns for files to include"),
    ] = None,
    exclude_patterns: Annotated[
        Optional[str],
        Field(description="Comma-separated glob patterns for files to exclude"),
    ] = None,
) -> str:
    """Parse and load a diff file with custom chunking settings. Use this tool ONLY when you need non-default settings (custom chunk sizes, filtering patterns). Otherwise, use list_chunks, get_chunk, or find_chunks_for_files which auto-load with optimal defaults. CRITICAL: You must use an absolute directory path - relative paths will fail. The diff file will be too large for direct reading, so you MUST use diffchunk tools for navigation. When using tracking documents for analysis, remember to clean up tracking state before presenting final results."""
    result = tools.load_diff(
        absolute_file_path=absolute_file_path,
        max_chunk_lines=max_chunk_lines,
        skip_trivial=skip_trivial,
        skip_generated=skip_generated,
        include_patterns=include_patterns,
        exclude_patterns=exclude_patterns,
    )
    return json.dumps(result, indent=2)


@mcp.tool(annotations={"readOnlyHint": True}, structured_output=False)
def list_chunks(
    absolute_file_path: Annotated[
        str, Field(description="Absolute path to the diff file")
    ],
) -> str:
    """Get an overview of all chunks in a diff file with file mappings and summaries. Auto-loads the diff file with optimal defaults if not already loaded. Use this as your first step to understand the scope and structure of changes before diving into specific chunks. CRITICAL: You must use an absolute directory path - relative paths will fail. DO NOT attempt to read the diff file directly as it will exceed context limits. This tool provides the roadmap for systematic chunk-by-chunk analysis. If using tracking documents to resume analysis, use this to orient yourself to remaining work."""
    result = tools.list_chunks(absolute_file_path=absolute_file_path)
    return json.dumps(result, indent=2)


@mcp.tool(annotations={"readOnlyHint": True}, structured_output=False)
def get_chunk(
    absolute_file_path: Annotated[
        str, Field(description="Absolute path to the diff file")
    ],
    chunk_number: Annotated[
        int, Field(description="The chunk number to retrieve (1-indexed)")
    ],
    include_context: Annotated[
        bool, Field(description="Include chunk header with metadata")
    ] = True,
) -> str:
    """Retrieve the actual content of a specific numbered chunk from a diff file. Auto-loads the diff file if not already loaded. Use this for systematic analysis of changes chunk-by-chunk, or to examine specific chunks identified via list_chunks or find_chunks_for_files. CRITICAL: You must use an absolute directory path - relative paths will fail. DO NOT read diff files directly - they exceed LLM context windows. This tool provides manageable portions of large diffs. Track your progress through chunks when doing comprehensive analysis and clean up tracking documents before final results."""
    result = tools.get_chunk(
        absolute_file_path=absolute_file_path,
        chunk_number=chunk_number,
        include_context=include_context,
    )
    return result


@mcp.tool(annotations={"readOnlyHint": True}, structured_output=False)
def find_chunks_for_files(
    absolute_file_path: Annotated[
        str, Field(description="Absolute path to the diff file")
    ],
    pattern: Annotated[
        str,
        Field(
            description="Glob pattern to match file paths (e.g., '*.py', '*test*', 'src/*')"
        ),
    ],
) -> str:
    """Locate chunks containing files that match a specific glob pattern. Auto-loads the diff file if not already loaded. Essential for targeted analysis when you need to focus on specific file types, directories, or naming patterns (e.g., '*.py' for Python files, '*test*' for test files, 'src/*' for source directory). Returns chunk numbers which you then examine using get_chunk. CRITICAL: You must use an absolute directory path - relative paths will fail. DO NOT attempt direct file reading. Use this for efficient navigation to relevant changes instead of processing entire large diffs sequentially."""
    result = tools.find_chunks_for_files(
        absolute_file_path=absolute_file_path,
        pattern=pattern,
    )
    return json.dumps(result)


@mcp.tool(annotations={"readOnlyHint": True}, structured_output=False)
def get_file_diff(
    absolute_file_path: Annotated[
        str, Field(description="Absolute path to the diff file")
    ],
    file_path: Annotated[
        str,
        Field(
            description="Exact file path or glob pattern matching a single file within the diff (e.g., 'src/main.py', '*.config')"
        ),
    ],
) -> str:
    """Extract the complete diff for a single file from a loaded diff. Returns the diff --git header and all hunks for that file. Use this when you need changes for one specific file without fetching the entire chunk. Auto-loads the diff file if not already loaded. Supports exact file paths or glob patterns that match exactly one file. Use list_chunks with file_details to see per-file line counts and decide whether to use this tool or get_chunk. CRITICAL: You must use an absolute directory path - relative paths will fail."""
    result = tools.get_file_diff(
        absolute_file_path=absolute_file_path,
        file_path=file_path,
    )
    return result
