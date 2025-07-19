"""Test encoding support for diff files."""

import pytest
from pathlib import Path

from src.tools import DiffChunkTools


class TestEncodings:
    """Test encoding detection and parsing."""

    @pytest.fixture
    def test_data_dir(self):
        return Path(__file__).parent / "test_data"

    @pytest.fixture
    def tools(self):
        return DiffChunkTools()

    def test_encoding_support(self, tools, test_data_dir):
        """Test that various encodings are supported."""
        test_files = [
            "minimal_working.diff",  # UTF-8
            "minimal_windows.diff",  # Windows line endings
            "minimal_bom.diff",  # UTF-8 BOM
            "minimal_latin1.diff",  # Latin-1
        ]

        for filename in test_files:
            result = tools.load_diff(str(test_data_dir / filename))
            assert result["chunks"] > 0, f"{filename} should parse successfully"
            assert result["files"] > 0, f"{filename} should contain files"

    def test_encoding_detection(self, tools, tmp_path):
        """Test encoding detection with UTF-16."""
        # Create a minimal UTF-16 diff file
        content = """diff --git a/test.txt b/test.txt
index 1234567..abcdefg 100644
--- a/test.txt
+++ b/test.txt
@@ -1 +1 @@
-old line
+new line
"""
        utf16_file = tmp_path / "test_utf16.diff"
        utf16_file.write_text(content, encoding="utf-16")

        result = tools.load_diff(str(utf16_file))
        assert result["chunks"] > 0
        assert result["files"] > 0

    def test_empty_diff_error(self, tools, tmp_path):
        """Test error message for empty diff files."""
        empty_file = tmp_path / "empty.diff"
        empty_file.write_text("")

        with pytest.raises(
            ValueError, match="Diff file parsed successfully but contains no changes"
        ):
            tools.load_diff(str(empty_file))
