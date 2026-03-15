"""Tests for get_file_diff tool and per-file line counts in list_chunks."""

import tempfile
import os

import pytest
from pathlib import Path

from src.tools import DiffChunkTools


def _write_diff(content: str) -> str:
    """Write diff content to a temp file and return the path."""
    fd, path = tempfile.mkstemp(suffix=".diff")
    with os.fdopen(fd, "w") as f:
        f.write(content)
    return path


MULTI_FILE_DIFF = """\
diff --git a/src/main.py b/src/main.py
index 1234567..abcdefg 100644
--- a/src/main.py
+++ b/src/main.py
@@ -1,3 +1,4 @@
 import os
+import sys

 def main():
@@ -10,3 +11,5 @@
     print("hello")
+    print("world")
+    return 0
diff --git a/src/utils.py b/src/utils.py
index 2345678..bcdefgh 100644
--- a/src/utils.py
+++ b/src/utils.py
@@ -1,2 +1,3 @@
 def helper():
+    pass
     return True
diff --git a/tests/test_main.py b/tests/test_main.py
index 3456789..cdefghi 100644
--- a/tests/test_main.py
+++ b/tests/test_main.py
@@ -1,4 +1,6 @@
 import pytest
+from src.main import main

 def test_main():
+    assert main() == 0
     pass
"""

SINGLE_FILE_DIFF = """\
diff --git a/only_file.txt b/only_file.txt
index 1234567..abcdefg 100644
--- a/only_file.txt
+++ b/only_file.txt
@@ -1,2 +1,3 @@
 line 1
+line 2
 line 3
"""


class TestGetFileDiff:
    """Tests for the get_file_diff tool."""

    @pytest.fixture
    def tools(self):
        return DiffChunkTools()

    @pytest.fixture
    def multi_file_diff_path(self):
        path = _write_diff(MULTI_FILE_DIFF)
        yield path
        os.unlink(path)

    @pytest.fixture
    def single_file_diff_path(self):
        path = _write_diff(SINGLE_FILE_DIFF)
        yield path
        os.unlink(path)

    def test_exact_file_path(self, tools, multi_file_diff_path):
        """get_file_diff with exact file path returns only that file's hunks."""
        result = tools.get_file_diff(multi_file_diff_path, "src/utils.py")

        assert "diff --git a/src/utils.py b/src/utils.py" in result
        assert "def helper():" in result
        assert "+    pass" in result
        # Should NOT contain other files
        assert "src/main.py" not in result
        assert "tests/test_main.py" not in result

    def test_exact_file_path_with_multiple_hunks(self, tools, multi_file_diff_path):
        """get_file_diff returns all hunks for a file with multiple hunks."""
        result = tools.get_file_diff(multi_file_diff_path, "src/main.py")

        assert "diff --git a/src/main.py b/src/main.py" in result
        assert "+import sys" in result
        assert '+    print("world")' in result
        assert "+    return 0" in result

    def test_glob_pattern_single_match(self, tools, multi_file_diff_path):
        """get_file_diff with glob pattern matching one file works."""
        result = tools.get_file_diff(multi_file_diff_path, "*utils*")

        assert "diff --git a/src/utils.py b/src/utils.py" in result
        assert "+    pass" in result

    def test_glob_pattern_zero_matches(self, tools, multi_file_diff_path):
        """get_file_diff with zero matches raises error."""
        with pytest.raises(ValueError, match="No file matching"):
            tools.get_file_diff(multi_file_diff_path, "nonexistent.py")

    def test_glob_pattern_multiple_matches(self, tools, multi_file_diff_path):
        """get_file_diff with multiple matches raises error."""
        with pytest.raises(ValueError, match="matches \\d+ files"):
            tools.get_file_diff(multi_file_diff_path, "src/*")

    def test_auto_loads_if_not_loaded(self, tools, multi_file_diff_path):
        """get_file_diff auto-loads if not already loaded."""
        # Don't call load_diff first
        result = tools.get_file_diff(multi_file_diff_path, "src/utils.py")

        assert "diff --git a/src/utils.py b/src/utils.py" in result
        assert "+    pass" in result

    def test_error_lists_available_files(self, tools, multi_file_diff_path):
        """Error message includes available files as a hint."""
        with pytest.raises(ValueError, match="Available files:") as exc_info:
            tools.get_file_diff(multi_file_diff_path, "nonexistent.py")

        error_msg = str(exc_info.value)
        assert "src/main.py" in error_msg or "src/utils.py" in error_msg

    def test_empty_file_path_raises(self, tools, multi_file_diff_path):
        """Empty file_path raises ValueError."""
        with pytest.raises(ValueError, match="non-empty string"):
            tools.get_file_diff(multi_file_diff_path, "")

    def test_single_file_diff(self, tools, single_file_diff_path):
        """get_file_diff works with a diff containing only one file."""
        result = tools.get_file_diff(single_file_diff_path, "only_file.txt")

        assert "diff --git a/only_file.txt b/only_file.txt" in result
        assert "+line 2" in result


class TestFileDetailsInListChunks:
    """Tests for per-file line counts in list_chunks."""

    @pytest.fixture
    def tools(self):
        return DiffChunkTools()

    @pytest.fixture
    def multi_file_diff_path(self):
        path = _write_diff(MULTI_FILE_DIFF)
        yield path
        os.unlink(path)

    def test_list_chunks_includes_file_details(self, tools, multi_file_diff_path):
        """list_chunks includes file_details with per-file line counts."""
        tools.load_diff(multi_file_diff_path)
        chunks = tools.list_chunks(multi_file_diff_path)

        for chunk in chunks:
            assert "file_details" in chunk
            assert isinstance(chunk["file_details"], list)

            # Each entry should have path and lines
            for detail in chunk["file_details"]:
                assert "path" in detail
                assert "lines" in detail
                assert isinstance(detail["path"], str)
                assert isinstance(detail["lines"], int)
                assert detail["lines"] > 0

    def test_list_chunks_still_has_files_list(self, tools, multi_file_diff_path):
        """list_chunks still includes files as flat string list (backward compat)."""
        tools.load_diff(multi_file_diff_path)
        chunks = tools.list_chunks(multi_file_diff_path)

        for chunk in chunks:
            assert "files" in chunk
            assert isinstance(chunk["files"], list)
            for f in chunk["files"]:
                assert isinstance(f, str)

    def test_file_details_paths_match_files_list(self, tools, multi_file_diff_path):
        """file_details paths should correspond to the files in the chunk."""
        tools.load_diff(multi_file_diff_path)
        chunks = tools.list_chunks(multi_file_diff_path)

        for chunk in chunks:
            detail_paths = {d["path"] for d in chunk["file_details"]}
            files_set = set(chunk["files"])
            # Every file_details path should be in the files list
            assert detail_paths.issubset(files_set)

    def test_file_details_line_counts_sum(self, tools, multi_file_diff_path):
        """Sum of per-file line counts should approximate the chunk total."""
        tools.load_diff(multi_file_diff_path)
        chunks = tools.list_chunks(multi_file_diff_path)

        for chunk in chunks:
            detail_total = sum(d["lines"] for d in chunk["file_details"])
            # The per-file counts should sum to the chunk line count
            assert detail_total == chunk["lines"]


class TestFileDetailsWithRealData:
    """Test per-file line counts with real diff files."""

    @pytest.fixture
    def test_data_dir(self):
        return Path(__file__).parent / "test_data"

    @pytest.fixture
    def tools(self):
        return DiffChunkTools()

    def test_real_diff_file_details(self, tools, test_data_dir):
        """Per-file line counts work with real diff files."""
        diff_file = test_data_dir / "react_18.0_to_18.3.diff"
        if not diff_file.exists():
            pytest.skip("React test diff not found")

        tools.load_diff(str(diff_file), max_chunk_lines=2000)
        chunks = tools.list_chunks(str(diff_file))

        assert len(chunks) > 0
        for chunk in chunks:
            assert "file_details" in chunk
            # All chunks should have file_details populated
            if chunk["files"]:
                assert len(chunk["file_details"]) > 0

    def test_large_file_split_has_file_details(self, tools, test_data_dir):
        """Per-file line counts correct for chunks from large file splits."""
        diff_file = test_data_dir / "go_version_upgrade_1.22_to_1.23.diff"
        if not diff_file.exists():
            pytest.skip("Go test diff not found")

        # Use small chunk size to force splits
        tools.load_diff(str(diff_file), max_chunk_lines=500)
        chunks = tools.list_chunks(str(diff_file))

        sub_chunks = [c for c in chunks if c["sub_chunk_index"] is not None]
        if sub_chunks:
            for chunk in sub_chunks:
                assert "file_details" in chunk
                assert len(chunk["file_details"]) > 0
                for detail in chunk["file_details"]:
                    assert detail["lines"] > 0
