"""Test tool calls through the MCP protocol using FastMCP's in-memory client."""

import json
from pathlib import Path

import pytest
from mcp.shared.memory import create_connected_server_and_client_session

from src.server import mcp


@pytest.fixture
def react_diff_file():
    diff_file = Path(__file__).parent / "test_data" / "react_18.0_to_18.3.diff"
    if not diff_file.exists():
        pytest.skip("React test diff not found")
    return str(diff_file)


class TestToolCalls:
    """Test all tools through the real MCP protocol path."""

    @pytest.mark.asyncio
    async def test_list_tools_returns_five_tools(self):
        async with create_connected_server_and_client_session(mcp) as client:
            result = await client.list_tools()
            assert len(result.tools) == 5
            names = {t.name for t in result.tools}
            assert names == {
                "load_diff",
                "list_chunks",
                "get_chunk",
                "find_chunks_for_files",
                "get_file_diff",
            }

    @pytest.mark.asyncio
    async def test_all_tools_have_read_only_annotation(self):
        async with create_connected_server_and_client_session(mcp) as client:
            result = await client.list_tools()
            for tool in result.tools:
                assert tool.annotations is not None
                assert tool.annotations.readOnlyHint is True

    @pytest.mark.asyncio
    async def test_no_tool_has_output_schema(self):
        async with create_connected_server_and_client_session(mcp) as client:
            result = await client.list_tools()
            for tool in result.tools:
                assert tool.outputSchema is None, (
                    f"Tool {tool.name} has outputSchema (breaks Claude Code)"
                )

    @pytest.mark.asyncio
    async def test_load_diff(self, react_diff_file):
        async with create_connected_server_and_client_session(mcp) as client:
            result = await client.call_tool(
                "load_diff", {"absolute_file_path": react_diff_file}
            )
            assert not result.isError
            data = json.loads(result.content[0].text)
            assert data["chunks"] > 0
            assert data["files"] > 0

    @pytest.mark.asyncio
    async def test_list_chunks(self, react_diff_file):
        async with create_connected_server_and_client_session(mcp) as client:
            result = await client.call_tool(
                "list_chunks", {"absolute_file_path": react_diff_file}
            )
            assert not result.isError
            chunks = json.loads(result.content[0].text)
            assert len(chunks) > 0
            assert all("chunk" in c for c in chunks)

    @pytest.mark.asyncio
    async def test_get_chunk(self, react_diff_file):
        async with create_connected_server_and_client_session(mcp) as client:
            result = await client.call_tool(
                "get_chunk",
                {"absolute_file_path": react_diff_file, "chunk_number": 1},
            )
            assert not result.isError
            assert "=== Chunk 1 of" in result.content[0].text

    @pytest.mark.asyncio
    async def test_find_chunks_for_files(self, react_diff_file):
        async with create_connected_server_and_client_session(mcp) as client:
            result = await client.call_tool(
                "find_chunks_for_files",
                {"absolute_file_path": react_diff_file, "pattern": "*.js"},
            )
            assert not result.isError
            chunk_nums = json.loads(result.content[0].text)
            assert isinstance(chunk_nums, list)

    @pytest.mark.asyncio
    async def test_get_file_diff(self, react_diff_file):
        async with create_connected_server_and_client_session(mcp) as client:
            # First list chunks to find a file name
            list_result = await client.call_tool(
                "list_chunks", {"absolute_file_path": react_diff_file}
            )
            chunks = json.loads(list_result.content[0].text)
            file_name = chunks[0]["files"][0]

            result = await client.call_tool(
                "get_file_diff",
                {"absolute_file_path": react_diff_file, "file_path": file_name},
            )
            assert not result.isError
            assert "diff --git" in result.content[0].text

    @pytest.mark.asyncio
    async def test_invalid_chunk_returns_is_error(self, react_diff_file):
        async with create_connected_server_and_client_session(mcp) as client:
            result = await client.call_tool(
                "get_chunk",
                {"absolute_file_path": react_diff_file, "chunk_number": 99999},
            )
            assert result.isError
            assert "does not exist" in result.content[0].text
            assert "list_chunks" in result.content[0].text

    @pytest.mark.asyncio
    async def test_empty_pattern_returns_is_error(self, react_diff_file):
        async with create_connected_server_and_client_session(mcp) as client:
            result = await client.call_tool(
                "find_chunks_for_files",
                {"absolute_file_path": react_diff_file, "pattern": ""},
            )
            assert result.isError
            assert "non-empty string" in result.content[0].text

    @pytest.mark.asyncio
    async def test_file_not_found_returns_is_error(self):
        async with create_connected_server_and_client_session(mcp) as client:
            result = await client.call_tool(
                "load_diff", {"absolute_file_path": "/nonexistent/file.diff"}
            )
            assert result.isError
            text = result.content[0].text.lower()
            assert "not found" in text or "cannot access" in text
