"""Integration tests using real diff files from test_data."""

import pytest
from pathlib import Path

from src.tools import DiffChunkTools


class TestIntegrationWithRealData:
    """Test diffchunk functionality with real diff files."""
    
    @pytest.fixture
    def test_data_dir(self):
        """Return path to test data directory."""
        return Path(__file__).parent / "test_data"
    
    @pytest.fixture
    def tools(self):
        """Return DiffChunkTools instance."""
        return DiffChunkTools()
    
    def test_load_go_diff(self, tools, test_data_dir):
        """Test loading the large Go version upgrade diff."""
        diff_file = test_data_dir / "go_version_upgrade_1.22_to_1.23.diff"
        
        if not diff_file.exists():
            pytest.skip("Go test diff not found")
        
        result = tools.load_diff(str(diff_file), max_chunk_lines=5000)
        
        # Verify basic stats
        assert result["chunks"] > 0
        assert result["files"] > 0
        assert result["total_lines"] > 1000
        assert result["file_path"] == str(diff_file)
        
        # Should have multiple chunks due to large size
        assert result["chunks"] > 5
    
    def test_load_react_diff(self, tools, test_data_dir):
        """Test loading the React diff."""
        diff_file = test_data_dir / "react_18.0_to_18.3.diff"
        
        if not diff_file.exists():
            pytest.skip("React test diff not found")
        
        result = tools.load_diff(str(diff_file), max_chunk_lines=3000)
        
        # Verify basic stats
        assert result["chunks"] > 0
        assert result["files"] > 0
        assert result["file_path"] == str(diff_file)
    
    def test_load_dotnet_diff(self, tools, test_data_dir):
        """Test loading the .NET Core diff."""
        diff_file = test_data_dir / "dotnet_core_8_to_9.diff"
        
        if not diff_file.exists():
            pytest.skip(".NET test diff not found")
        
        result = tools.load_diff(str(diff_file), max_chunk_lines=4000)
        
        # Verify basic stats
        assert result["chunks"] > 0
        assert result["files"] > 0
        assert result["file_path"] == str(diff_file)
    
    def test_list_chunks_functionality(self, tools, test_data_dir):
        """Test list_chunks with real data."""
        diff_file = test_data_dir / "react_18.0_to_18.3.diff"
        
        if not diff_file.exists():
            pytest.skip("React test diff not found")
        
        # Load diff
        tools.load_diff(str(diff_file), max_chunk_lines=2000)
        
        # List chunks
        chunks = tools.list_chunks()
        
        assert len(chunks) > 0
        
        # Verify chunk structure
        for chunk in chunks:
            assert "chunk" in chunk
            assert "files" in chunk
            assert "lines" in chunk
            assert "summary" in chunk
            
            assert isinstance(chunk["chunk"], int)
            assert isinstance(chunk["files"], list)
            assert isinstance(chunk["lines"], int)
            assert isinstance(chunk["summary"], str)
            
            assert chunk["chunk"] > 0
            assert len(chunk["files"]) > 0
            assert chunk["lines"] > 0
    
    def test_get_chunk_functionality(self, tools, test_data_dir):
        """Test get_chunk with real data."""
        diff_file = test_data_dir / "react_18.0_to_18.3.diff"
        
        if not diff_file.exists():
            pytest.skip("React test diff not found")
        
        # Load diff
        result = tools.load_diff(str(diff_file), max_chunk_lines=3000)
        chunk_count = result["chunks"]
        
        # Get first chunk
        chunk_content = tools.get_chunk(1)
        
        assert isinstance(chunk_content, str)
        assert len(chunk_content) > 0
        assert "=== Chunk 1 of" in chunk_content
        assert "diff --git" in chunk_content
        
        # Get chunk without context
        chunk_content_no_context = tools.get_chunk(1, include_context=False)
        assert isinstance(chunk_content_no_context, str)
        assert "=== Chunk 1 of" not in chunk_content_no_context
        assert len(chunk_content_no_context) < len(chunk_content)
        
        # Test invalid chunk number
        with pytest.raises(ValueError, match="Chunk .* not found"):
            tools.get_chunk(chunk_count + 1)
    
    def test_find_chunks_for_files(self, tools, test_data_dir):
        """Test find_chunks_for_files with real data."""
        diff_file = test_data_dir / "react_18.0_to_18.3.diff"
        
        if not diff_file.exists():
            pytest.skip("React test diff not found")
        
        # Load diff
        tools.load_diff(str(diff_file), max_chunk_lines=2000)
        
        # Test common patterns
        js_chunks = tools.find_chunks_for_files("*.js")
        json_chunks = tools.find_chunks_for_files("*.json")
        package_chunks = tools.find_chunks_for_files("*package*")
        
        # Results should be lists of integers
        assert isinstance(js_chunks, list)
        assert isinstance(json_chunks, list)
        assert isinstance(package_chunks, list)
        
        # Should find some JavaScript files in React
        assert len(js_chunks) > 0 or len(json_chunks) > 0
        
        # All chunk numbers should be valid
        for chunk_num in js_chunks + json_chunks + package_chunks:
            assert isinstance(chunk_num, int)
            assert chunk_num > 0
    
    def test_filtering_options(self, tools, test_data_dir):
        """Test different filtering options."""
        diff_file = test_data_dir / "go_version_upgrade_1.22_to_1.23.diff"
        
        if not diff_file.exists():
            pytest.skip("Go test diff not found")
        
        # Load with different filtering options
        result_no_filter = tools.load_diff(
            str(diff_file), 
            max_chunk_lines=6000,
            skip_trivial=False,
            skip_generated=False
        )
        
        result_filtered = tools.load_diff(
            str(diff_file),
            max_chunk_lines=6000, 
            skip_trivial=True,
            skip_generated=True
        )
        
        # Filtered version should have fewer or equal files
        assert result_filtered["files"] <= result_no_filter["files"]
    
    def test_no_diff_loaded_errors(self, tools):
        """Test error handling when no diff is loaded."""
        # These should all raise ValueError
        with pytest.raises(ValueError, match="No diff loaded"):
            tools.list_chunks()
        
        with pytest.raises(ValueError, match="No diff loaded"):
            tools.get_chunk(1)
        
        with pytest.raises(ValueError, match="No diff loaded"):
            tools.find_chunks_for_files("*.py")
    
    def test_invalid_file_errors(self, tools):
        """Test error handling for invalid files."""
        # Non-existent file
        with pytest.raises(ValueError, match="not found"):
            tools.load_diff("/nonexistent/file.diff")
        
        # Directory instead of file
        with pytest.raises(ValueError, match="not a file"):
            tools.load_diff("/tmp")
    
    def test_chunk_size_consistency(self, tools, test_data_dir):
        """Test that chunk sizes are respected reasonably."""
        diff_file = test_data_dir / "react_18.0_to_18.3.diff"
        
        if not diff_file.exists():
            pytest.skip("React test diff not found")
        
        # Load with small chunk size
        result_small = tools.load_diff(str(diff_file), max_chunk_lines=500)
        chunks_small = tools.list_chunks()
        
        # Load with large chunk size
        result_large = tools.load_diff(str(diff_file), max_chunk_lines=5000)
        chunks_large = tools.list_chunks()
        
        # Smaller chunks should create more chunks (usually)
        # Note: This might not always be true due to file boundaries
        assert result_small["chunks"] >= result_large["chunks"]
        
        # At least verify we got some chunks
        assert len(chunks_small) > 0
        assert len(chunks_large) > 0
        
        # Verify chunks contain reasonable data
        for chunk in chunks_small + chunks_large:
            assert chunk["lines"] > 0
            assert len(chunk["files"]) > 0