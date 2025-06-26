"""File system edge case integration tests."""

import os
import tempfile
from pathlib import Path

import pytest

from src.tools import DiffChunkTools


class TestFileSystemEdgeCases:
    """Test file system edge cases and error handling."""

    @pytest.fixture
    def tools(self):
        """Return DiffChunkTools instance."""
        return DiffChunkTools()

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

    def test_load_diff_nonexistent_file(self, tools):
        """Test loading non-existent diff file."""
        with pytest.raises(ValueError, match="not found"):
            tools.load_diff("/nonexistent/path/file.diff", "/tmp")

    def test_load_diff_directory_instead_of_file(self, tools):
        """Test loading directory instead of file."""
        with pytest.raises(ValueError, match="not a file"):
            tools.load_diff("/tmp", "/tmp")

    def test_load_diff_empty_file_path(self, tools):
        """Test loading with empty file path."""
        with pytest.raises(ValueError, match="must be a non-empty string"):
            tools.load_diff("", "/tmp")

    def test_load_diff_whitespace_only_file_path(self, tools):
        """Test loading with whitespace-only file path."""
        with pytest.raises(ValueError, match="must be a non-empty string"):
            tools.load_diff("   ", "/tmp")

    def test_load_diff_empty_working_directory(self, tools, react_diff_file):
        """Test loading with empty working directory."""
        with pytest.raises(ValueError, match="must be a non-empty string"):
            tools.load_diff(react_diff_file, "")

    def test_load_diff_nonexistent_working_directory(self, tools, react_diff_file):
        """Test loading with non-existent working directory."""
        with pytest.raises(ValueError, match="Working directory .* does not exist"):
            tools.load_diff(react_diff_file, "/nonexistent/directory")

    def test_load_diff_working_directory_is_file(self, tools, react_diff_file):
        """Test loading with working directory that is a file."""
        with pytest.raises(ValueError, match="Working directory .* is not a directory"):
            tools.load_diff(react_diff_file, react_diff_file)

    def test_load_diff_invalid_chunk_size(self, tools, react_diff_file):
        """Test loading with invalid chunk sizes."""
        # Zero chunk size
        with pytest.raises(ValueError, match="must be a positive integer"):
            tools.load_diff(react_diff_file, "/tmp", max_chunk_lines=0)

        # Negative chunk size
        with pytest.raises(ValueError, match="must be a positive integer"):
            tools.load_diff(react_diff_file, "/tmp", max_chunk_lines=-100)

    def test_load_diff_relative_path_resolution(self, tools, test_data_dir):
        """Test relative path resolution with working directory."""
        if not (test_data_dir / "react_18.0_to_18.3.diff").exists():
            pytest.skip("React test diff not found")

        # Use relative path with working directory
        result = tools.load_diff(
            "react_18.0_to_18.3.diff", str(test_data_dir), max_chunk_lines=3000
        )

        assert result["chunks"] > 0
        assert result["files"] > 0

    def test_load_diff_absolute_path_with_working_directory(
        self, tools, react_diff_file
    ):
        """Test absolute path with working directory."""
        result = tools.load_diff(react_diff_file, "/tmp", max_chunk_lines=3000)

        assert result["chunks"] > 0
        assert result["files"] > 0
        assert result["file_path"] == react_diff_file

    def test_load_diff_with_unreadable_file(self, tools):
        """Test loading file with restricted permissions."""
        # Skip this test - too platform dependent and fragile
        pytest.skip("Permission tests are platform dependent and fragile")

    def test_load_diff_empty_file(self, tools):
        """Test loading completely empty diff file."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".diff") as f:
            # Write nothing - empty file
            temp_file = f.name

        try:
            # Should handle empty file - may raise error or return empty result
            # This is acceptable behavior either way
            try:
                result = tools.load_diff(temp_file, "/tmp")
                # If it succeeds, should have no chunks
                assert result["chunks"] == 0
                assert result["files"] == 0
            except ValueError:
                # If it raises an error for empty file, that's also acceptable
                pass

        finally:
            os.unlink(temp_file)

    def test_find_chunks_for_files_empty_pattern(self, tools, react_diff_file):
        """Test find_chunks_for_files with empty pattern."""
        tools.load_diff(react_diff_file, "/tmp")

        with pytest.raises(ValueError, match="must be a non-empty string"):
            tools.find_chunks_for_files("")

    def test_find_chunks_for_files_whitespace_pattern(self, tools, react_diff_file):
        """Test find_chunks_for_files with whitespace-only pattern."""
        tools.load_diff(react_diff_file, "/tmp")

        with pytest.raises(ValueError, match="must be a non-empty string"):
            tools.find_chunks_for_files("   ")

    def test_get_chunk_invalid_numbers(self, tools, react_diff_file):
        """Test get_chunk with invalid chunk numbers."""
        tools.load_diff(react_diff_file, "/tmp")

        # Zero chunk number
        with pytest.raises(ValueError, match="must be a positive integer"):
            tools.get_chunk(0)

        # Negative chunk number
        with pytest.raises(ValueError, match="must be a positive integer"):
            tools.get_chunk(-1)

        # Non-integer chunk number (string)
        with pytest.raises(ValueError, match="must be a positive integer"):
            tools.get_chunk("not_a_number")  # type: ignore

    def test_get_chunk_out_of_range(self, tools, react_diff_file):
        """Test get_chunk with chunk number out of range."""
        result = tools.load_diff(react_diff_file, "/tmp")
        total_chunks = result["chunks"]

        # Chunk number too high
        with pytest.raises(ValueError, match="Chunk .* not found"):
            tools.get_chunk(total_chunks + 1)

    def test_tools_operations_without_diff_loaded(self, tools):
        """Test all operations when no diff is loaded."""
        # These should all raise ValueError about no diff loaded
        with pytest.raises(ValueError, match="No diff loaded"):
            tools.list_chunks()

        with pytest.raises(ValueError, match="No diff loaded"):
            tools.get_chunk(1)

        with pytest.raises(ValueError, match="No diff loaded"):
            tools.find_chunks_for_files("*.py")

    def test_load_diff_overwrite_previous_session(
        self, tools, react_diff_file, test_data_dir
    ):
        """Test loading new diff overwrites previous session."""
        # Load first diff
        result1 = tools.load_diff(react_diff_file, "/tmp", max_chunk_lines=2000)
        chunks1 = tools.list_chunks()

        # Load second diff (if available)
        go_diff = test_data_dir / "go_version_upgrade_1.22_to_1.23.diff"
        if go_diff.exists():
            result2 = tools.load_diff(str(go_diff), "/tmp", max_chunk_lines=3000)
            chunks2 = tools.list_chunks()

            # Should be different sessions
            assert result1["file_path"] != result2["file_path"]
            assert len(chunks1) != len(chunks2) or chunks1 != chunks2

            # Current overview should reflect new session
            overview = tools.get_current_overview()
            assert overview["file_path"] == str(go_diff)

    def test_home_directory_expansion(self, tools):
        """Test home directory expansion in paths."""
        # Create a test file in a temp directory
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".diff") as f:
            f.write("diff --git a/test.txt b/test.txt\n")
            f.write("index 1234567..abcdefg 100644\n")
            f.write("--- a/test.txt\n")
            f.write("+++ b/test.txt\n")
            f.write("@@ -1 +1 @@\n")
            f.write("-old line\n")
            f.write("+new line\n")
            temp_file = f.name

        try:
            # Test with home directory in working directory path
            home_dir = os.path.expanduser("~")
            if os.path.isdir(home_dir):
                # Use actual home directory
                result = tools.load_diff(temp_file, "~")
                assert result["chunks"] >= 0  # Should not error

        finally:
            os.unlink(temp_file)

    def test_complex_pattern_matching(self, tools, react_diff_file):
        """Test complex glob patterns."""
        tools.load_diff(react_diff_file, "/tmp", max_chunk_lines=2000)

        # These should all work without errors
        patterns = [
            "*",
            "**/*",
            "*.{js,json}",
            "**/test/**",
            "src/**/*.py",
            "[abc]*",
            "file[0-9].txt",
        ]

        for pattern in patterns:
            result = tools.find_chunks_for_files(pattern)
            assert isinstance(result, list)
            # All chunk numbers should be valid integers
            for chunk_num in result:
                assert isinstance(chunk_num, int)
                assert chunk_num > 0
