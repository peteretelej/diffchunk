"""Test MCP server components and functionality."""

from pathlib import Path

import pytest

from src.server import DiffChunkServer
from src.tools import DiffChunkTools


class TestMCPComponents:
    """Test MCP server components directly."""

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

    @pytest.fixture
    def go_diff_file(self, test_data_dir):
        """Return path to Go test diff file."""
        diff_file = test_data_dir / "go_version_upgrade_1.22_to_1.23.diff"
        if not diff_file.exists():
            pytest.skip("Go test diff not found")
        return str(diff_file)

    def test_diffchunk_tools_complete_workflow(self, react_diff_file):
        """Test complete workflow with DiffChunkTools."""
        tools = DiffChunkTools()

        # 1. Load diff (optional - for custom settings)
        result = tools.load_diff(react_diff_file, max_chunk_lines=3000)
        assert result["chunks"] > 0
        assert result["files"] > 0
        assert result["file_path"] == react_diff_file
        total_chunks = result["chunks"]

        # 2. List chunks (auto-loads if needed)
        chunks = tools.list_chunks(react_diff_file)
        assert len(chunks) == total_chunks
        assert all("chunk" in chunk for chunk in chunks)
        assert all("files" in chunk for chunk in chunks)
        assert all("lines" in chunk for chunk in chunks)
        assert all("summary" in chunk for chunk in chunks)

        # 3. Get chunk content
        chunk_content = tools.get_chunk(react_diff_file, 1)
        assert isinstance(chunk_content, str)
        assert len(chunk_content) > 0
        assert "=== Chunk 1 of" in chunk_content
        assert "diff --git" in chunk_content

        # Get chunk without context
        chunk_no_context = tools.get_chunk(react_diff_file, 1, include_context=False)
        assert isinstance(chunk_no_context, str)
        assert "=== Chunk 1 of" not in chunk_no_context
        assert len(chunk_no_context) < len(chunk_content)

        # 4. Find chunks by pattern
        js_chunks = tools.find_chunks_for_files(react_diff_file, "*.js")
        json_chunks = tools.find_chunks_for_files(react_diff_file, "*.json")
        all_chunks = tools.find_chunks_for_files(react_diff_file, "*")

        assert isinstance(js_chunks, list)
        assert isinstance(json_chunks, list)
        assert isinstance(all_chunks, list)

        # All chunk numbers should be valid
        for chunk_list in [js_chunks, json_chunks, all_chunks]:
            for chunk_num in chunk_list:
                assert isinstance(chunk_num, int)
                assert 1 <= chunk_num <= total_chunks

        # 5. Test overview functionality
        overview = tools.get_current_overview()
        assert overview["loaded"] is True
        assert overview["total_sessions"] >= 1
        # Find our file in the sessions
        session_found = any(
            s["file_path"] == react_diff_file for s in overview["sessions"]
        )
        assert session_found

    def test_diffchunk_tools_auto_loading(self, react_diff_file):
        """Test auto-loading functionality."""
        tools = DiffChunkTools()

        # Test that tools auto-load when called without explicit load_diff
        chunks = tools.list_chunks(react_diff_file)
        assert len(chunks) > 0

        # Should work for other tools too
        chunk_content = tools.get_chunk(react_diff_file, 1)
        assert len(chunk_content) > 0

        js_chunks = tools.find_chunks_for_files(react_diff_file, "*.js")
        assert isinstance(js_chunks, list)

    def test_diffchunk_tools_error_handling(self):
        """Test error handling in DiffChunkTools."""
        tools = DiffChunkTools()

        # Test with invalid file paths
        with pytest.raises(ValueError, match="Cannot access file"):
            tools.list_chunks("/nonexistent/file.diff")

        with pytest.raises(ValueError, match="Cannot access file"):
            tools.get_chunk("/nonexistent/file.diff", 1)

        with pytest.raises(ValueError, match="Cannot access file"):
            tools.find_chunks_for_files("/nonexistent/file.diff", "*.py")

        # Test invalid file
        with pytest.raises(ValueError, match="not found"):
            tools.load_diff("/nonexistent/file.diff")

        # Test invalid parameters
        with pytest.raises(ValueError, match="must be a non-empty string"):
            tools.load_diff("")

        with pytest.raises(ValueError, match="must be a positive integer"):
            tools.load_diff("some_file.diff", max_chunk_lines=0)

    def test_diffchunk_tools_validation(self, react_diff_file):
        """Test input validation in DiffChunkTools."""
        tools = DiffChunkTools()

        # Test invalid chunk numbers
        with pytest.raises(ValueError, match="must be a positive integer"):
            tools.get_chunk(react_diff_file, 0)

        with pytest.raises(ValueError, match="must be a positive integer"):
            tools.get_chunk(react_diff_file, -1)

        with pytest.raises(ValueError, match="must be a positive integer"):
            tools.get_chunk(react_diff_file, "not_a_number")  # type: ignore

        # Test invalid patterns
        with pytest.raises(ValueError, match="must be a non-empty string"):
            tools.find_chunks_for_files(react_diff_file, "")

        with pytest.raises(ValueError, match="must be a non-empty string"):
            tools.find_chunks_for_files(react_diff_file, "   ")

    def test_diffchunk_tools_multi_file_support(self, react_diff_file, go_diff_file):
        """Test multiple diff files can be loaded simultaneously."""
        tools = DiffChunkTools()

        # Load two different diff files
        react_result = tools.load_diff(react_diff_file, max_chunk_lines=2000)
        go_result = tools.load_diff(go_diff_file, max_chunk_lines=1500)

        # Both should be loaded with different stats
        assert react_result["chunks"] > 0
        assert go_result["chunks"] > 0
        assert react_result["file_path"] == react_diff_file
        assert go_result["file_path"] == go_diff_file

        # Should be able to work with both files independently
        react_chunks = tools.list_chunks(react_diff_file)
        go_chunks = tools.list_chunks(go_diff_file)

        assert len(react_chunks) == react_result["chunks"]
        assert len(go_chunks) == go_result["chunks"]

        # Get chunks from both files
        react_chunk1 = tools.get_chunk(react_diff_file, 1)
        go_chunk1 = tools.get_chunk(go_diff_file, 1)

        assert react_chunk1 != go_chunk1  # Should be different content
        assert "=== Chunk 1 of" in react_chunk1
        assert "=== Chunk 1 of" in go_chunk1

        # Overview should show both sessions
        overview = tools.get_current_overview()
        assert overview["loaded"] is True
        assert overview["total_sessions"] >= 2

        file_paths = [s["file_path"] for s in overview["sessions"]]
        assert react_diff_file in file_paths
        assert go_diff_file in file_paths

    def test_mcp_server_creation(self):
        """Test MCP server can be created successfully."""
        server = DiffChunkServer()

        # Verify server has the expected attributes
        assert server.app is not None
        assert server.tools is not None
        assert isinstance(server.tools, DiffChunkTools)

    def test_mcp_server_tools_registration(self):
        """Test that MCP server has tools registered."""
        server = DiffChunkServer()

        # The server should have handlers set up
        # This is a basic smoke test to ensure the server initializes
        assert hasattr(server, "app")
        assert hasattr(server, "tools")
        assert hasattr(server, "_setup_handlers")

    def test_filtering_and_chunking_options(self, go_diff_file):
        """Test different filtering and chunking options."""
        tools = DiffChunkTools()

        # Test with different chunk sizes
        result_small = tools.load_diff(go_diff_file, max_chunk_lines=1000)
        result_large = tools.load_diff(go_diff_file, max_chunk_lines=8000)

        # Smaller chunks should generally create more chunks
        assert result_small["chunks"] >= result_large["chunks"]

        # Test with filtering disabled
        result_no_filter = tools.load_diff(
            go_diff_file,
            max_chunk_lines=5000,
            skip_trivial=False,
            skip_generated=False,
        )

        result_filtered = tools.load_diff(
            go_diff_file,
            max_chunk_lines=5000,
            skip_trivial=True,
            skip_generated=True,
        )

        # Filtered version should have fewer or equal files
        assert result_filtered["files"] <= result_no_filter["files"]

    def test_pattern_matching_functionality(self, react_diff_file):
        """Test pattern matching works correctly."""
        tools = DiffChunkTools()
        tools.load_diff(react_diff_file, max_chunk_lines=2000)

        # Test various patterns
        patterns_to_test = [
            "*.js",
            "*.json",
            "*package*",
            "src/*",
            "*.md",
            "*test*",
            "*",
        ]

        for pattern in patterns_to_test:
            chunks = tools.find_chunks_for_files(react_diff_file, pattern)
            assert isinstance(chunks, list)

            # All returned chunk numbers should be valid
            for chunk_num in chunks:
                assert isinstance(chunk_num, int)
                assert chunk_num >= 1

                # Verify we can actually get this chunk
                chunk_content = tools.get_chunk(react_diff_file, chunk_num)
                assert isinstance(chunk_content, str)
                assert len(chunk_content) > 0

    def test_chunk_content_structure(self, react_diff_file):
        """Test that chunk content has the expected structure."""
        tools = DiffChunkTools()
        tools.load_diff(react_diff_file, max_chunk_lines=3000)

        chunks = tools.list_chunks(react_diff_file)

        for i, chunk_info in enumerate(chunks, 1):
            # Test chunk info structure
            assert chunk_info["chunk"] == i
            assert isinstance(chunk_info["files"], list)
            assert len(chunk_info["files"]) > 0
            assert isinstance(chunk_info["lines"], int)
            assert chunk_info["lines"] > 0
            assert isinstance(chunk_info["summary"], str)
            assert len(chunk_info["summary"]) > 0

            # Test chunk content
            content_with_context = tools.get_chunk(
                react_diff_file, i, include_context=True
            )
            content_without_context = tools.get_chunk(
                react_diff_file, i, include_context=False
            )

            # With context should be longer
            assert len(content_with_context) > len(content_without_context)

            # With context should include header
            assert f"=== Chunk {i} of" in content_with_context
            assert "Files:" in content_with_context
            assert "Lines:" in content_with_context

            # Without context should not include header
            assert f"=== Chunk {i} of" not in content_without_context

    def test_large_diff_performance(self, go_diff_file):
        """Test performance with large diff files."""
        import time

        tools = DiffChunkTools()

        # Measure load time
        start_time = time.time()
        result = tools.load_diff(go_diff_file, max_chunk_lines=5000)
        load_time = time.time() - start_time

        # Should handle large diff quickly (within 10 seconds)
        assert load_time < 10.0, f"Load took too long: {load_time}s"

        # Should create reasonable number of chunks
        assert result["chunks"] > 5
        assert result["files"] > 50
        assert result["total_lines"] > 1000

        # Measure navigation time
        start_time = time.time()
        chunks = tools.list_chunks(go_diff_file)
        list_time = time.time() - start_time

        assert list_time < 2.0, f"List chunks took too long: {list_time}s"
        assert len(chunks) == result["chunks"]

        # Measure chunk retrieval time
        start_time = time.time()
        content = tools.get_chunk(go_diff_file, 1)
        get_time = time.time() - start_time

        assert get_time < 1.0, f"Get chunk took too long: {get_time}s"
        assert len(content) > 0
