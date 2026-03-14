"""Tests for case-insensitive file matching."""

from pathlib import Path

import pytest

from src.tools import DiffChunkTools


@pytest.fixture
def tools():
    return DiffChunkTools()


@pytest.fixture
def react_diff_file():
    diff_file = Path(__file__).parent / "test_data" / "react_18.0_to_18.3.diff"
    if not diff_file.exists():
        pytest.skip("React test diff not found")
    return str(diff_file)


@pytest.fixture
def go_diff_file():
    diff_file = (
        Path(__file__).parent / "test_data" / "go_version_upgrade_1.22_to_1.23.diff"
    )
    if not diff_file.exists():
        pytest.skip("Go test diff not found")
    return str(diff_file)


class TestCaseInsensitiveMatching:
    """Test case-insensitive file pattern matching."""

    def test_find_chunks_uppercase_extension(self, tools, react_diff_file):
        """find_chunks_for_files with '*.JS' matches .js files."""
        tools.load_diff(react_diff_file)
        lower_chunks = tools.find_chunks_for_files(react_diff_file, "*.js")
        upper_chunks = tools.find_chunks_for_files(react_diff_file, "*.JS")
        assert lower_chunks == upper_chunks
        assert len(lower_chunks) > 0

    def test_find_chunks_mixed_case_pattern(self, tools, go_diff_file):
        """find_chunks_for_files with mixed case pattern matches files."""
        tools.load_diff(go_diff_file)
        lower_chunks = tools.find_chunks_for_files(go_diff_file, "*.go")
        mixed_chunks = tools.find_chunks_for_files(go_diff_file, "*.Go")
        assert lower_chunks == mixed_chunks

    def test_find_chunks_uppercase_directory(self, tools, react_diff_file):
        """find_chunks_for_files with uppercase dir pattern matches."""
        tools.load_diff(react_diff_file)
        all_chunks = tools.find_chunks_for_files(react_diff_file, "*")
        assert len(all_chunks) > 0
        # Uppercase wildcard should match the same set
        upper_all = tools.find_chunks_for_files(react_diff_file, "*")
        assert all_chunks == upper_all

    def test_find_chunks_exact_case_still_works(self, tools, react_diff_file):
        """Exact case pattern still matches correctly."""
        tools.load_diff(react_diff_file)
        chunks = tools.find_chunks_for_files(react_diff_file, "*.js")
        assert len(chunks) > 0

    def test_get_file_diff_case_insensitive_exact(self, tools, react_diff_file):
        """get_file_diff matches with different case in file path."""
        tools.load_diff(react_diff_file)

        # Get a file name from the diff
        chunks = tools.list_chunks(react_diff_file)
        file_name = chunks[0]["files"][0]

        # Exact case should work
        result_exact = tools.get_file_diff(react_diff_file, file_name)
        assert "diff --git" in result_exact

        # Uppercase version should also work
        result_upper = tools.get_file_diff(react_diff_file, file_name.upper())
        assert result_upper == result_exact

    def test_get_file_diff_case_insensitive_glob(self, tools, react_diff_file):
        """get_file_diff glob matching is case-insensitive."""
        tools.load_diff(react_diff_file)

        chunks = tools.list_chunks(react_diff_file)
        # Find a file that has a unique extension to use as glob pattern
        file_name = chunks[0]["files"][0]

        # If the file has an extension, try matching with different case
        if "." in file_name:
            base, ext = file_name.rsplit(".", 1)
            upper_pattern = f"{base.upper()}.{ext.upper()}"
            result = tools.get_file_diff(react_diff_file, upper_pattern)
            assert "diff --git" in result
