"""Test handle_call_tool for code coverage."""

import json
from pathlib import Path

import pytest
from mcp.types import CallToolRequest

from src.server import DiffChunkServer


class TestHandleCallTool:
    """Test handle_call_tool for coverage."""

    @pytest.fixture
    def server(self):
        return DiffChunkServer()

    @pytest.fixture
    def react_diff_file(self):
        diff_file = Path(__file__).parent / "test_data" / "react_18.0_to_18.3.diff"
        if not diff_file.exists():
            pytest.skip("React test diff not found")
        return str(diff_file)

    @pytest.mark.asyncio
    async def test_handle_call_tool_coverage(self, server, react_diff_file):
        """Test all paths in handle_call_tool for coverage."""
        handler = server.app.request_handlers[CallToolRequest]

        # Test load_diff
        request = CallToolRequest(
            method="tools/call",
            params={
                "name": "load_diff",
                "arguments": {"absolute_file_path": react_diff_file},
            },
        )
        result = await handler(request)
        data = json.loads(result.root.content[0].text)
        assert data["chunks"] > 0

        # Test list_chunks
        request = CallToolRequest(
            method="tools/call",
            params={
                "name": "list_chunks",
                "arguments": {"absolute_file_path": react_diff_file},
            },
        )
        result = await handler(request)
        chunks = json.loads(result.root.content[0].text)
        assert len(chunks) > 0

        # Test get_chunk
        request = CallToolRequest(
            method="tools/call",
            params={
                "name": "get_chunk",
                "arguments": {"absolute_file_path": react_diff_file, "chunk_number": 1},
            },
        )
        result = await handler(request)
        assert "=== Chunk 1 of" in result.root.content[0].text

        # Test find_chunks_for_files
        request = CallToolRequest(
            method="tools/call",
            params={
                "name": "find_chunks_for_files",
                "arguments": {"absolute_file_path": react_diff_file, "pattern": "*"},
            },
        )
        result = await handler(request)
        chunk_nums = json.loads(result.root.content[0].text)
        assert isinstance(chunk_nums, list)

        # Test unknown tool
        request = CallToolRequest(
            method="tools/call", params={"name": "unknown_tool", "arguments": {}}
        )
        result = await handler(request)
        assert "Unknown tool: unknown_tool" in result.root.content[0].text

        # Test None arguments (validation error from MCP layer)
        request = CallToolRequest(
            method="tools/call", params={"name": "load_diff", "arguments": None}
        )
        result = await handler(request)
        assert "Input validation error" in result.root.content[0].text
