"""MCP server implementation for diffchunk."""

from mcp.server import InitializationOptions, NotificationOptions
from mcp.server import Server
from mcp.types import Resource, Tool, TextContent
import json
from typing import Any, Sequence

from .tools import DiffChunkTools


class DiffChunkServer:
    """MCP server for diffchunk functionality."""

    def __init__(self):
        self.app = Server("diffchunk")
        self.tools = DiffChunkTools()
        self._setup_handlers()

    def _setup_handlers(self):
        """Set up MCP handlers."""

        @self.app.list_resources()
        async def handle_list_resources() -> list[Resource]:
            """List available resources."""
            return [
                Resource(
                    uri="diffchunk://current",  # type: ignore
                    name="Current Diff Overview",
                    description="Overview of all currently loaded diff files",
                    mimeType="application/json",
                )
            ]

        @self.app.read_resource()
        async def handle_read_resource(uri: str) -> str:
            """Read a resource."""
            if uri == "diffchunk://current":
                overview = self.tools.get_current_overview()
                return json.dumps(overview, indent=2)
            else:
                raise ValueError(f"Unknown resource: {uri}")

        @self.app.list_tools()
        async def handle_list_tools() -> list[Tool]:
            """List available tools."""
            return [
                Tool(
                    name="load_diff",
                    description="Load and parse a diff file into navigable chunks with custom settings",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "absolute_file_path": {
                                "type": "string",
                                "description": "Absolute path to the diff file to load",
                            },
                            "max_chunk_lines": {
                                "type": "integer",
                                "description": "Maximum lines per chunk",
                                "default": 4000,
                            },
                            "skip_trivial": {
                                "type": "boolean",
                                "description": "Skip whitespace-only changes",
                                "default": True,
                            },
                            "skip_generated": {
                                "type": "boolean",
                                "description": "Skip generated files and build artifacts",
                                "default": True,
                            },
                            "include_patterns": {
                                "type": "string",
                                "description": "Comma-separated glob patterns for files to include",
                            },
                            "exclude_patterns": {
                                "type": "string",
                                "description": "Comma-separated glob patterns for files to exclude",
                            },
                        },
                        "required": ["absolute_file_path"],
                    },
                ),
                Tool(
                    name="list_chunks",
                    description="List all chunks with file information and summaries (auto-loads if needed)",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "absolute_file_path": {
                                "type": "string",
                                "description": "Absolute path to the diff file",
                            },
                        },
                        "required": ["absolute_file_path"],
                    },
                ),
                Tool(
                    name="get_chunk",
                    description="Get the content of a specific chunk (auto-loads if needed)",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "absolute_file_path": {
                                "type": "string",
                                "description": "Absolute path to the diff file",
                            },
                            "chunk_number": {
                                "type": "integer",
                                "description": "The chunk number to retrieve (1-indexed)",
                            },
                            "include_context": {
                                "type": "boolean",
                                "description": "Include chunk header with metadata",
                                "default": True,
                            },
                        },
                        "required": ["absolute_file_path", "chunk_number"],
                    },
                ),
                Tool(
                    name="find_chunks_for_files",
                    description="Find chunks containing files matching a pattern (auto-loads if needed)",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "absolute_file_path": {
                                "type": "string",
                                "description": "Absolute path to the diff file",
                            },
                            "pattern": {
                                "type": "string",
                                "description": "Glob pattern to match file paths (e.g., '*.py', '*test*', 'src/*')",
                            },
                        },
                        "required": ["absolute_file_path", "pattern"],
                    },
                ),
            ]

        @self.app.call_tool()
        async def handle_call_tool(
            name: str, arguments: dict[str, Any] | None
        ) -> Sequence[TextContent]:
            """Handle tool calls."""
            if arguments is None:
                arguments = {}

            try:
                if name == "load_diff":
                    result = self.tools.load_diff(**arguments)
                    return [TextContent(type="text", text=json.dumps(result, indent=2))]

                elif name == "list_chunks":
                    result = self.tools.list_chunks(**arguments)
                    return [TextContent(type="text", text=json.dumps(result, indent=2))]

                elif name == "get_chunk":
                    result = self.tools.get_chunk(**arguments)
                    return [TextContent(type="text", text=result)]

                elif name == "find_chunks_for_files":
                    result = self.tools.find_chunks_for_files(**arguments)
                    return [TextContent(type="text", text=json.dumps(result))]

                else:
                    raise ValueError(f"Unknown tool: {name}")

            except ValueError as e:
                error_msg = f"Error in {name}: {str(e)}"
                return [TextContent(type="text", text=error_msg)]
            except Exception as e:
                error_msg = f"Unexpected error in {name}: {str(e)}"
                return [TextContent(type="text", text=error_msg)]

    async def run(self):
        """Run the MCP server."""
        # Import here to avoid issues with event loop
        from mcp.server.stdio import stdio_server

        async with stdio_server() as (read_stream, write_stream):
            await self.app.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="diffchunk",
                    server_version="0.1.3",
                    capabilities=self.app.get_capabilities(
                        notification_options=NotificationOptions(),
                        experimental_capabilities={},
                    ),
                ),
            )
