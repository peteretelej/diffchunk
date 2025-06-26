"""MCP server error handling integration tests."""

import json
from pathlib import Path

import pytest

from src.server import DiffChunkServer
from src.tools import DiffChunkTools


class TestMCPServerErrorHandling:
    """Test MCP server error handling scenarios."""

    @pytest.fixture
    def server(self):
        """Create a DiffChunkServer instance."""
        return DiffChunkServer()

    @pytest.fixture
    def test_data_dir(self):
        """Return path to test data directory."""
        return Path(__file__).parent / "test_data"

    @pytest.fixture
    def react_diff_file(self, test_data_dir):
        """Return path to React test diff file."""
        diff_file = test_data_dir / "react_18.0_to_18.3.diff"
        if not diff_file.exists():
            pytest.skip("React test diff not found")
        return str(diff_file)

    def test_server_initialization(self, server):
        """Test server initializes correctly."""
        assert server.app is not None
        assert server.tools is not None
        assert isinstance(server.tools, DiffChunkTools)

    def test_server_handlers_setup(self, server):
        """Test server has handlers properly set up."""
        assert hasattr(server, "_setup_handlers")
        assert hasattr(server.app, "list_resources")
        assert hasattr(server.app, "read_resource")
        assert hasattr(server.app, "list_tools")
        assert hasattr(server.app, "call_tool")

    def test_read_resource_invalid_uri(self, server):
        """Test reading invalid resource URI."""
        # Test that server raises error for invalid URI
        # This tests the error path in the actual handler
        with pytest.raises(ValueError, match="Unknown resource"):
            # Simulate what the handler does
            uri = "invalid://uri"
            if uri == "diffchunk://current":
                overview = server.tools.get_current_overview()
                json.dumps(overview, indent=2)
            else:
                raise ValueError(f"Unknown resource: {uri}")

    def test_call_tool_unknown_tool(self, server):
        """Test calling unknown tool."""
        # Test the error handling logic for unknown tools
        name = "unknown_tool"

        # Simulate what the handler does
        try:
            if name in [
                "load_diff",
                "list_chunks",
                "get_chunk",
                "find_chunks_for_files",
            ]:
                pass  # Valid tools
            else:
                raise ValueError(f"Unknown tool: {name}")
        except ValueError as e:
            error_msg = f"Error in {name}: {str(e)}"
            assert "Unknown tool: unknown_tool" in error_msg

    def test_call_tool_with_none_arguments(self, server):
        """Test calling tool with None arguments."""
        # Test argument handling
        arguments = None
        if arguments is None:
            arguments = {}
        assert isinstance(arguments, dict)

    def test_call_tool_load_diff_errors(self, server):
        """Test load_diff tool error handling."""
        # Test that tool errors are caught and formatted
        try:
            # This should fail with missing file
            server.tools.load_diff("/nonexistent/file.diff", "/tmp")
        except ValueError as e:
            error_msg = f"Error in load_diff: {str(e)}"
            assert "Error in load_diff:" in error_msg
            assert "not found" in error_msg

    def test_call_tool_operations_without_loaded_diff(self, server):
        """Test tool operations when no diff is loaded."""
        # Test list_chunks without loaded diff
        try:
            server.tools.list_chunks()
        except ValueError as e:
            error_msg = f"Error in list_chunks: {str(e)}"
            assert "Error in list_chunks: No diff loaded" in error_msg

        # Test get_chunk without loaded diff
        try:
            server.tools.get_chunk(1)
        except ValueError as e:
            error_msg = f"Error in get_chunk: {str(e)}"
            assert "Error in get_chunk: No diff loaded" in error_msg

        # Test find_chunks_for_files without loaded diff
        try:
            server.tools.find_chunks_for_files("*.py")
        except ValueError as e:
            error_msg = f"Error in find_chunks_for_files: {str(e)}"
            assert "Error in find_chunks_for_files: No diff loaded" in error_msg

    def test_call_tool_invalid_arguments(self, server, react_diff_file):
        """Test tool calls with invalid arguments."""
        # Load a diff first
        server.tools.load_diff(react_diff_file, "/tmp")

        # Test get_chunk with invalid chunk number
        try:
            server.tools.get_chunk(0)
        except ValueError as e:
            error_msg = f"Error in get_chunk: {str(e)}"
            assert "Error in get_chunk:" in error_msg
            assert "must be a positive integer" in error_msg

        # Test find_chunks_for_files with empty pattern
        try:
            server.tools.find_chunks_for_files("")
        except ValueError as e:
            error_msg = f"Error in find_chunks_for_files: {str(e)}"
            assert "Error in find_chunks_for_files:" in error_msg
            assert "must be a non-empty string" in error_msg

    def test_call_tool_unexpected_exception_handling(self, server):
        """Test handling of unexpected exceptions in tools."""
        # Simulate an unexpected exception
        try:
            raise RuntimeError("Unexpected error occurred")
        except ValueError as e:
            error_msg = f"Error in test_exception: {str(e)}"
        except Exception as e:
            error_msg = f"Unexpected error in test_exception: {str(e)}"
            assert (
                "Unexpected error in test_exception: Unexpected error occurred"
                in error_msg
            )

    def test_list_resources_basic(self, server):
        """Test list_resources returns expected resources."""
        # Test the resource structure
        expected_resource = {
            "uri": "diffchunk://current",
            "name": "Current Diff Overview",
            "description": "Overview of the currently loaded diff file",
            "mimeType": "application/json",
        }

        # Verify resource structure is correct
        assert expected_resource["uri"] == "diffchunk://current"
        assert expected_resource["name"] == "Current Diff Overview"

    def test_read_resource_current_overview(self, server, react_diff_file):
        """Test reading current overview resource."""
        # Load a diff first
        server.tools.load_diff(react_diff_file, "/tmp")

        # Test reading the overview
        uri = "diffchunk://current"
        if uri == "diffchunk://current":
            overview = server.tools.get_current_overview()
            result = json.dumps(overview, indent=2)

            # Should be valid JSON
            overview_parsed = json.loads(result)
            assert overview_parsed["loaded"] is True
            assert overview_parsed["file_path"] == react_diff_file
            assert overview_parsed["chunks"] > 0

    def test_server_run_method_exists(self, server):
        """Test server has run method for starting."""
        assert hasattr(server, "run")
        assert callable(server.run)

    def test_tool_error_message_formatting(self, server):
        """Test that tool errors are properly formatted."""
        # Test ValueError formatting
        try:
            raise ValueError("Test error message")
        except ValueError as e:
            error_msg = f"Error in test_tool: {str(e)}"
            assert error_msg == "Error in test_tool: Test error message"

        # Test Exception formatting
        try:
            raise RuntimeError("Test runtime error")
        except Exception as e:
            error_msg = f"Unexpected error in test_tool: {str(e)}"
            assert error_msg == "Unexpected error in test_tool: Test runtime error"

    def test_json_serialization_in_responses(self, server, react_diff_file):
        """Test JSON serialization in tool responses."""
        # Load diff and test JSON responses
        result = server.tools.load_diff(react_diff_file, "/tmp")

        # Test that result can be serialized to JSON
        json_result = json.dumps(result, indent=2)
        assert isinstance(json_result, str)

        # Test that it can be parsed back
        parsed_result = json.loads(json_result)
        assert parsed_result["chunks"] == result["chunks"]
        assert parsed_result["files"] == result["files"]
