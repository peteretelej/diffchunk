"""MCP server error handling tests using FastMCP's in-memory client."""

import json
from pathlib import Path

import pytest
from mcp.shared.memory import create_connected_server_and_client_session
from mcp.types import AnyUrl

from src.server import mcp


@pytest.fixture
def react_diff_file():
    diff_file = Path(__file__).parent / "test_data" / "react_18.0_to_18.3.diff"
    if not diff_file.exists():
        pytest.skip("React test diff not found")
    return str(diff_file)


class TestServerErrorHandling:
    """Test error handling through the real MCP protocol path."""

    @pytest.mark.asyncio
    async def test_list_resources(self):
        async with create_connected_server_and_client_session(mcp) as client:
            result = await client.list_resources()
            assert len(result.resources) == 1
            assert str(result.resources[0].uri) == "diffchunk://current"

    @pytest.mark.asyncio
    async def test_read_resource_current_overview(self, react_diff_file):
        async with create_connected_server_and_client_session(mcp) as client:
            # Load a diff first
            await client.call_tool(
                "load_diff", {"absolute_file_path": react_diff_file}
            )

            result = await client.read_resource(AnyUrl("diffchunk://current"))
            overview = json.loads(result.contents[0].text)
            assert overview["loaded"] is True
            assert overview["total_sessions"] >= 1

    @pytest.mark.asyncio
    async def test_get_chunk_invalid_number_is_error(self, react_diff_file):
        async with create_connected_server_and_client_session(mcp) as client:
            result = await client.call_tool(
                "get_chunk",
                {"absolute_file_path": react_diff_file, "chunk_number": 0},
            )
            assert result.isError

    @pytest.mark.asyncio
    async def test_get_file_diff_no_match_is_error(self, react_diff_file):
        async with create_connected_server_and_client_session(mcp) as client:
            result = await client.call_tool(
                "get_file_diff",
                {
                    "absolute_file_path": react_diff_file,
                    "file_path": "nonexistent_file_xyz.py",
                },
            )
            assert result.isError
            assert "No file matching" in result.content[0].text

    @pytest.mark.asyncio
    async def test_load_diff_nonexistent_file_is_error(self):
        async with create_connected_server_and_client_session(mcp) as client:
            result = await client.call_tool(
                "load_diff",
                {"absolute_file_path": "/nonexistent/path/file.diff"},
            )
            assert result.isError
