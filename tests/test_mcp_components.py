"""Test MCP server components and functionality."""

from pathlib import Path

import pytest

from src.formatter import _format_annotated, _format_compact
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

    def test_format_raw_returns_identical_output(self, react_diff_file):
        """Test that format='raw' returns identical output to default (no format param)."""
        tools = DiffChunkTools()
        tools.load_diff(react_diff_file, max_chunk_lines=3000)

        # Get chunk with default behavior (no format param)
        default_output = tools.get_chunk(react_diff_file, 1, include_context=True)

        # Get chunk with explicit format="raw"
        raw_output = tools.get_chunk(
            react_diff_file, 1, include_context=True, format="raw"
        )

        assert default_output == raw_output

        # Also verify without context header
        default_no_ctx = tools.get_chunk(react_diff_file, 1, include_context=False)
        raw_no_ctx = tools.get_chunk(
            react_diff_file, 1, include_context=False, format="raw"
        )

        assert default_no_ctx == raw_no_ctx

    def test_format_invalid_raises_valueerror(self, react_diff_file):
        """Test that an invalid format string raises ValueError with helpful message."""
        tools = DiffChunkTools()
        tools.load_diff(react_diff_file, max_chunk_lines=3000)

        with pytest.raises(ValueError, match="Invalid format 'invalid'") as exc_info:
            tools.get_chunk(react_diff_file, 1, format="invalid")

        error_msg = str(exc_info.value)
        assert "'raw'" in error_msg
        assert "'annotated'" in error_msg
        assert "'compact'" in error_msg

    def test_format_annotated_and_compact_accepted(self, react_diff_file):
        """Test that annotated and compact format values are accepted without error."""
        tools = DiffChunkTools()
        tools.load_diff(react_diff_file, max_chunk_lines=3000)

        # These should not raise - they are valid modes (placeholders for now)
        annotated = tools.get_chunk(react_diff_file, 1, format="annotated")
        assert isinstance(annotated, str)
        assert len(annotated) > 0

        compact = tools.get_chunk(react_diff_file, 1, format="compact")
        assert isinstance(compact, str)
        assert len(compact) > 0


class TestAnnotatedFormat:
    """Tests for the annotated format output."""

    def test_multi_hunk_multi_file_annotated(self):
        """Multi-hunk, multi-file diff produces correct annotated output."""
        diff = (
            "diff --git a/src/auth.py b/src/auth.py\n"
            "index abc1234..def5678 100644\n"
            "--- a/src/auth.py\n"
            "+++ b/src/auth.py\n"
            "@@ -10,4 +10,5 @@ def authenticate\n"
            " unchanged\n"
            " also unchanged\n"
            "+new line\n"
            " trailing ctx\n"
            "@@ -30,3 +31,3 @@ def logout\n"
            " ctx\n"
            "-old removed\n"
            "+new replaced\n"
            " ctx end\n"
            "diff --git a/src/utils.py b/src/utils.py\n"
            "index 1111111..2222222 100644\n"
            "--- a/src/utils.py\n"
            "+++ b/src/utils.py\n"
            "@@ -1,3 +1,4 @@\n"
            " first\n"
            "+inserted\n"
            " second\n"
            " third\n"
        )
        result = _format_annotated(diff, ["src/auth.py", "src/utils.py"])

        # File headers
        assert "## File: 'src/auth.py'" in result
        assert "## File: 'src/utils.py'" in result

        # Hunk markers
        assert "__new hunk__" in result
        assert "__old hunk__" in result

        # Function context on hunk headers
        assert "__new hunk__ | def authenticate" in result
        assert "__old hunk__ | def logout" in result

        # Line numbers on __new hunk__ lines
        lines = result.split("\n")

        # Find a __new hunk__ added line - should have line number and + prefix
        new_hunk_added = [l for l in lines if "+" in l and "new line" in l]
        assert len(new_hunk_added) >= 1
        assert new_hunk_added[0].strip().startswith("12")  # line 10+2 context = 12

        # Find __old hunk__ removed line - should have - prefix, no line number
        old_hunk_removed = [l for l in lines if "-" in l and "old removed" in l]
        assert len(old_hunk_removed) >= 1
        # Old hunk lines have no numeric line numbers
        stripped = old_hunk_removed[0].strip()
        assert stripped.startswith("-")

    def test_new_file_no_old_hunks(self):
        """New file should produce __new hunk__ only, no __old hunk__."""
        diff = (
            "diff --git a/newfile.py b/newfile.py\n"
            "new file mode 100644\n"
            "index 0000000..abcdef1\n"
            "--- /dev/null\n"
            "+++ b/newfile.py\n"
            "@@ -0,0 +1,3 @@\n"
            "+line one\n"
            "+line two\n"
            "+line three\n"
        )
        result = _format_annotated(diff, ["newfile.py"])

        assert "## File: 'newfile.py'" in result
        assert "__new hunk__" in result
        assert "__old hunk__" not in result

        # All lines should be added with line numbers
        lines = result.split("\n")
        added_lines = [l for l in lines if "+" in l and "line" in l]
        assert len(added_lines) == 3

    def test_deleted_file_no_new_hunks(self):
        """Deleted file should produce __old hunk__ only, no __new hunk__."""
        diff = (
            "diff --git a/removed.py b/removed.py\n"
            "deleted file mode 100644\n"
            "index abcdef1..0000000\n"
            "--- a/removed.py\n"
            "+++ /dev/null\n"
            "@@ -1,3 +0,0 @@\n"
            "-line one\n"
            "-line two\n"
            "-line three\n"
        )
        result = _format_annotated(diff, ["removed.py"])

        assert "## File: 'removed.py'" in result
        assert "__old hunk__" in result
        assert "__new hunk__" not in result

        # All lines should be removed with - prefix
        lines = result.split("\n")
        removed_lines = [l for l in lines if "-" in l and "line" in l]
        assert len(removed_lines) == 3

    def test_hunk_no_function_context(self):
        """Hunk with bare @@ (no trailing function) omits the | part."""
        diff = (
            "diff --git a/plain.txt b/plain.txt\n"
            "index abc..def 100644\n"
            "--- a/plain.txt\n"
            "+++ b/plain.txt\n"
            "@@ -1,3 +1,4 @@\n"
            " existing\n"
            "+added\n"
            " more\n"
            " end\n"
        )
        result = _format_annotated(diff, ["plain.txt"])

        # Should have __new hunk__ without | part
        lines = result.split("\n")
        hunk_headers = [l for l in lines if l.startswith("__new hunk__")]
        assert len(hunk_headers) == 1
        assert "|" not in hunk_headers[0]

    def test_multiple_hunks_single_file(self):
        """Multiple hunks in a single file each get their own hunk markers."""
        diff = (
            "diff --git a/multi.py b/multi.py\n"
            "index abc..def 100644\n"
            "--- a/multi.py\n"
            "+++ b/multi.py\n"
            "@@ -5,3 +5,4 @@ def first_func\n"
            " ctx1\n"
            "+add1\n"
            " ctx2\n"
            " ctx3\n"
            "@@ -20,3 +21,4 @@ def second_func\n"
            " ctx4\n"
            "+add2\n"
            " ctx5\n"
            " ctx6\n"
        )
        result = _format_annotated(diff, ["multi.py"])

        # Should have exactly one file header
        assert result.count("## File: 'multi.py'") == 1

        # Should have two __new hunk__ sections
        lines = result.split("\n")
        new_hunk_headers = [l for l in lines if l.startswith("__new hunk__")]
        assert len(new_hunk_headers) == 2

        # Both should have function context
        assert "__new hunk__ | def first_func" in result
        assert "__new hunk__ | def second_func" in result

        # Verify line numbers are correct for each hunk
        # First hunk: starts at line 5, add1 should be at line 6
        add1_lines = [l for l in lines if "+add1" in l]
        assert any("6" in l for l in add1_lines)

        # Second hunk: starts at line 21, add2 should be at line 22
        add2_lines = [l for l in lines if "+add2" in l]
        assert any("22" in l for l in add2_lines)

    def test_annotated_via_tools_get_chunk(self):
        """Annotated format works end-to-end via DiffChunkTools.get_chunk."""
        test_data_dir = Path(__file__).parent / "test_data"
        react_diff = test_data_dir / "react_18.0_to_18.3.diff"
        if not react_diff.exists():
            pytest.skip("React test diff not found")

        tools = DiffChunkTools()
        tools.load_diff(str(react_diff), max_chunk_lines=3000)

        annotated = tools.get_chunk(str(react_diff), 1, format="annotated", include_context=False)

        # Should contain structural elements
        assert "## File:" in annotated
        assert "__new hunk__" in annotated

    def test_annotated_line_numbers_accuracy(self):
        """Verify line numbers are accurate for a known input."""
        diff = (
            "diff --git a/example.py b/example.py\n"
            "index abc..def 100644\n"
            "--- a/example.py\n"
            "+++ b/example.py\n"
            "@@ -45,5 +47,7 @@ def authenticate\n"
            " unchanged line\n"
            " unchanged line\n"
            "+new line added\n"
            "+another new line\n"
            " unchanged line\n"
            "-old line removed\n"
            " last line\n"
        )
        result = _format_annotated(diff, ["example.py"])
        lines = result.split("\n")

        # __new hunk__: context starts at new_line=47
        # Line 47: " unchanged line"
        # Line 48: " unchanged line"
        # Line 49: "+new line added"
        # Line 50: "+another new line"
        # Line 51: " unchanged line"
        # skip removed
        # Line 52: " last line"
        new_hunk_lines = []
        in_new = False
        for l in lines:
            if l.startswith("__new hunk__"):
                in_new = True
                continue
            if l.startswith("__old hunk__") or l.startswith("## File:"):
                in_new = False
                continue
            if in_new and l.strip():
                new_hunk_lines.append(l)

        assert len(new_hunk_lines) == 6
        assert new_hunk_lines[0].strip().startswith("47")
        assert new_hunk_lines[1].strip().startswith("48")
        assert "49" in new_hunk_lines[2] and "+new line added" in new_hunk_lines[2]
        assert "50" in new_hunk_lines[3] and "+another new line" in new_hunk_lines[3]
        assert new_hunk_lines[4].strip().startswith("51")
        assert new_hunk_lines[5].strip().startswith("52")


class TestCompactFormat:
    """Tests for the compact format output."""

    def test_compact_omits_removed_lines(self):
        """Compact output contains no removed lines (no - prefixed content lines)."""
        diff = (
            "diff --git a/src/auth.py b/src/auth.py\n"
            "index abc1234..def5678 100644\n"
            "--- a/src/auth.py\n"
            "+++ b/src/auth.py\n"
            "@@ -10,5 +10,5 @@ def authenticate\n"
            " unchanged\n"
            "-old line removed\n"
            "+new line added\n"
            " trailing ctx\n"
            " end\n"
        )
        result = _format_compact(diff, ["src/auth.py"])

        # Split into lines and check content lines (skip headers/markers)
        lines = result.split("\n")
        content_lines = [
            l for l in lines
            if not l.startswith("## File:") and not l.startswith("__")
            and l.strip()
        ]
        # No content line should have a - prefix (removed line format is "    -text")
        for line in content_lines:
            stripped = line.strip()
            assert not stripped.startswith("-"), (
                f"Found removed line in compact output: {line!r}"
            )

    def test_compact_no_old_hunk_sections(self):
        """No __old hunk__ sections appear in compact output."""
        diff = (
            "diff --git a/src/auth.py b/src/auth.py\n"
            "index abc1234..def5678 100644\n"
            "--- a/src/auth.py\n"
            "+++ b/src/auth.py\n"
            "@@ -10,4 +10,5 @@ def authenticate\n"
            " unchanged\n"
            " also unchanged\n"
            "+new line\n"
            " trailing ctx\n"
            "@@ -30,3 +31,3 @@ def logout\n"
            " ctx\n"
            "-old removed\n"
            "+new replaced\n"
            " ctx end\n"
        )
        result = _format_compact(diff, ["src/auth.py"])

        assert "__old hunk__" not in result
        assert "__new hunk__" in result

    def test_compact_line_numbers_and_plus_prefix(self):
        """Line numbers use new-file numbering, + prefixes on added lines."""
        diff = (
            "diff --git a/example.py b/example.py\n"
            "index abc..def 100644\n"
            "--- a/example.py\n"
            "+++ b/example.py\n"
            "@@ -45,5 +47,7 @@ def authenticate\n"
            " unchanged line\n"
            " unchanged line\n"
            "+new line added\n"
            "+another new line\n"
            " unchanged line\n"
            "-old line removed\n"
            " last line\n"
        )
        result = _format_compact(diff, ["example.py"])
        lines = result.split("\n")

        # Collect content lines (not headers/markers)
        content_lines = []
        in_hunk = False
        for l in lines:
            if l.startswith("__new hunk__"):
                in_hunk = True
                continue
            if l.startswith("## File:"):
                in_hunk = False
                continue
            if in_hunk and l.strip():
                content_lines.append(l)

        # Should have 6 lines: 2 context, 2 added, 1 context (skip removed), 1 context
        assert len(content_lines) == 6

        # Verify new-file line numbers
        assert content_lines[0].strip().startswith("47")  # first context
        assert content_lines[1].strip().startswith("48")  # second context
        assert "49" in content_lines[2] and "+new line added" in content_lines[2]
        assert "50" in content_lines[3] and "+another new line" in content_lines[3]
        assert content_lines[4].strip().startswith("51")  # context after adds
        # removed line is skipped, so next is "last line" at 52
        assert content_lines[5].strip().startswith("52")

    def test_compact_multi_file_multi_hunk(self):
        """Multi-file, multi-hunk content formatted correctly in compact mode."""
        diff = (
            "diff --git a/src/auth.py b/src/auth.py\n"
            "index abc1234..def5678 100644\n"
            "--- a/src/auth.py\n"
            "+++ b/src/auth.py\n"
            "@@ -10,4 +10,5 @@ def authenticate\n"
            " unchanged\n"
            " also unchanged\n"
            "+new line\n"
            " trailing ctx\n"
            "@@ -30,3 +31,3 @@ def logout\n"
            " ctx\n"
            "-old removed\n"
            "+new replaced\n"
            " ctx end\n"
            "diff --git a/src/utils.py b/src/utils.py\n"
            "index 1111111..2222222 100644\n"
            "--- a/src/utils.py\n"
            "+++ b/src/utils.py\n"
            "@@ -1,3 +1,4 @@\n"
            " first\n"
            "+inserted\n"
            " second\n"
            " third\n"
        )
        result = _format_compact(diff, ["src/auth.py", "src/utils.py"])

        # File headers present
        assert "## File: 'src/auth.py'" in result
        assert "## File: 'src/utils.py'" in result

        # __new hunk__ markers present with function context
        assert "__new hunk__ | def authenticate" in result
        assert "__new hunk__ | def logout" in result

        # No __old hunk__ sections
        assert "__old hunk__" not in result

        # Verify no removed lines in output content
        lines = result.split("\n")
        content_lines = [
            l for l in lines
            if not l.startswith("## File:") and not l.startswith("__")
            and l.strip()
        ]
        for line in content_lines:
            stripped = line.strip()
            assert not stripped.startswith("-"), (
                f"Found removed line in compact output: {line!r}"
            )

        # Should have three __new hunk__ markers total (2 for auth.py, 1 for utils.py)
        new_hunk_count = sum(1 for l in lines if l.startswith("__new hunk__"))
        assert new_hunk_count == 3

    def test_compact_deleted_file_no_output(self):
        """Deleted file (only removed lines) produces file header but no hunk content."""
        diff = (
            "diff --git a/removed.py b/removed.py\n"
            "deleted file mode 100644\n"
            "index abcdef1..0000000\n"
            "--- a/removed.py\n"
            "+++ /dev/null\n"
            "@@ -1,3 +0,0 @@\n"
            "-line one\n"
            "-line two\n"
            "-line three\n"
        )
        result = _format_compact(diff, ["removed.py"])

        assert "## File: 'removed.py'" in result
        # No hunk sections at all since there are no added/context lines
        assert "__new hunk__" not in result
        assert "__old hunk__" not in result

    def test_compact_new_file_all_added(self):
        """New file (only added lines) produces correct compact output."""
        diff = (
            "diff --git a/newfile.py b/newfile.py\n"
            "new file mode 100644\n"
            "index 0000000..abcdef1\n"
            "--- /dev/null\n"
            "+++ b/newfile.py\n"
            "@@ -0,0 +1,3 @@\n"
            "+line one\n"
            "+line two\n"
            "+line three\n"
        )
        result = _format_compact(diff, ["newfile.py"])

        assert "## File: 'newfile.py'" in result
        assert "__new hunk__" in result
        assert "__old hunk__" not in result

        # All lines should have + prefix and line numbers
        lines = result.split("\n")
        added_lines = [l for l in lines if "+" in l and "line" in l]
        assert len(added_lines) == 3

    def test_compact_via_tools_get_chunk(self):
        """Compact format works end-to-end via DiffChunkTools.get_chunk."""
        test_data_dir = Path(__file__).parent / "test_data"
        react_diff = test_data_dir / "react_18.0_to_18.3.diff"
        if not react_diff.exists():
            pytest.skip("React test diff not found")

        tools = DiffChunkTools()
        tools.load_diff(str(react_diff), max_chunk_lines=3000)

        compact = tools.get_chunk(
            str(react_diff), 1, format="compact", include_context=False
        )

        # Should contain structural elements
        assert "## File:" in compact
        assert "__new hunk__" in compact
        # Should NOT contain __old hunk__
        assert "__old hunk__" not in compact


class TestFilesExcludedCount:
    """Tests for files_excluded tracking in load_diff responses."""

    @pytest.fixture
    def test_data_dir(self):
        """Return path to test data directory."""
        return Path(__file__).parent / "test_data"

    @pytest.fixture
    def go_diff_file(self, test_data_dir):
        """Return path to Go test diff file."""
        diff_file = test_data_dir / "go_version_upgrade_1.22_to_1.23.diff"
        if not diff_file.exists():
            pytest.skip("Go test diff not found")
        return str(diff_file)

    @pytest.fixture
    def react_diff_file(self, test_data_dir):
        """Return path to React test diff file."""
        diff_file = test_data_dir / "react_18.0_to_18.3.diff"
        if not diff_file.exists():
            pytest.skip("React test diff not found")
        return str(diff_file)

    def test_files_excluded_with_exclude_patterns(self, go_diff_file):
        """Loading with exclude_patterns reports files_excluded > 0."""
        tools = DiffChunkTools()
        result = tools.load_diff(go_diff_file, exclude_patterns="*.md")

        assert "files_excluded" in result
        assert result["files_excluded"] > 0

    def test_files_excluded_zero_without_patterns(self, go_diff_file):
        """Loading without exclude_patterns reports files_excluded == 0."""
        tools = DiffChunkTools()
        result = tools.load_diff(go_diff_file)

        assert "files_excluded" in result
        assert result["files_excluded"] == 0

    def test_excluded_files_not_in_list_chunks(self, react_diff_file):
        """Files removed by exclude_patterns do not appear in list_chunks."""
        tools = DiffChunkTools()

        # Load with json files excluded
        result = tools.load_diff(react_diff_file, exclude_patterns="*.json")
        assert result["files_excluded"] > 0

        # Verify no .json files appear in chunk listings
        chunks = tools.list_chunks(react_diff_file)
        for chunk_info in chunks:
            for file_path in chunk_info["files"]:
                assert not file_path.endswith(".json"), (
                    f"Excluded file '{file_path}' found in list_chunks output"
                )
