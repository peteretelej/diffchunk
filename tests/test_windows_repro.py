"""Test to reproduce Windows "No valid diff content found" issue."""

import pytest
from pathlib import Path

from src.tools import DiffChunkTools


class TestWindowsEncoding:
    """Test Windows encoding issues that cause 'No valid diff content found'."""

    @pytest.fixture
    def test_data_dir(self):
        return Path(__file__).parent / "test_data"

    @pytest.fixture
    def tools(self):
        return DiffChunkTools()

    def test_encoding_scenarios_work_with_fix(self, tools, test_data_dir):
        """Test that encoding scenarios work with the fix."""
        working_files = [
            "minimal_working.diff",  # UTF-8 baseline
            "minimal_windows.diff",  # Windows \r\n line endings
            "minimal_bom.diff",  # UTF-8 BOM (now handled)
            "minimal_latin1.diff",  # Latin-1 encoding (now handled)
        ]

        for filename in working_files:
            result = tools.load_diff(
                str(test_data_dir / filename), max_chunk_lines=1000
            )
            assert result["chunks"] > 0, f"{filename} should work with fix"
            assert result["files"] > 0, f"{filename} should have files"
