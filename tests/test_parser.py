"""Tests for diff parser functionality."""

import pytest
from io import StringIO
from diffchunk.parser import DiffParser, FileChange


class TestDiffParser:
    """Test cases for DiffParser."""
    
    def test_parse_simple_diff(self):
        """Test parsing a simple diff."""
        diff_content = """diff --git a/test.py b/test.py
index 1234567..abcdefg 100644
--- a/test.py
+++ b/test.py
@@ -1,3 +1,4 @@
 def hello():
+    print("Hello, World!")
     return "hello"
 
"""
        
        parser = DiffParser()
        changes = parser.parse_stream(StringIO(diff_content))
        
        assert len(changes) == 1
        change = changes[0]
        assert change.old_path == "test.py"
        assert change.new_path == "test.py"
        assert not change.is_binary
        assert not change.is_new_file
        assert not change.is_deleted_file
        
        stats = parser.get_stats()
        assert stats.files_changed == 1
        assert stats.additions == 1
        assert stats.deletions == 0
    
    def test_parse_new_file(self):
        """Test parsing a new file diff."""
        diff_content = """diff --git a/new_file.py b/new_file.py
new file mode 100644
index 0000000..1234567
--- /dev/null
+++ b/new_file.py
@@ -0,0 +1,2 @@
+def new_function():
+    pass
"""
        
        parser = DiffParser()
        changes = parser.parse_stream(StringIO(diff_content))
        
        assert len(changes) == 1
        change = changes[0]
        assert change.is_new_file
        assert not change.is_deleted_file
        assert not change.is_binary
    
    def test_parse_binary_file(self):
        """Test parsing a binary file diff."""
        diff_content = """diff --git a/image.png b/image.png
index 1234567..abcdefg 100644
Binary files a/image.png and b/image.png differ
"""
        
        parser = DiffParser()
        changes = parser.parse_stream(StringIO(diff_content))
        
        assert len(changes) == 1
        change = changes[0]
        assert change.is_binary
    
    def test_parse_multiple_files(self):
        """Test parsing multiple files in one diff."""
        diff_content = """diff --git a/file1.py b/file1.py
index 1234567..abcdefg 100644
--- a/file1.py
+++ b/file1.py
@@ -1,2 +1,3 @@
 line1
+line2
 line3
diff --git a/file2.py b/file2.py
index 2345678..bcdefgh 100644
--- a/file2.py
+++ b/file2.py
@@ -1,2 +1,2 @@
-old_line
+new_line
 unchanged
"""
        
        parser = DiffParser()
        changes = parser.parse_stream(StringIO(diff_content))
        
        assert len(changes) == 2
        assert changes[0].old_path == "file1.py"
        assert changes[1].old_path == "file2.py"
        
        stats = parser.get_stats()
        assert stats.files_changed == 2
        assert stats.additions == 2
        assert stats.deletions == 1
    
    def test_empty_diff(self):
        """Test parsing an empty diff."""
        parser = DiffParser()
        changes = parser.parse_stream(StringIO(""))
        
        assert len(changes) == 0
        stats = parser.get_stats()
        assert stats.files_changed == 0
        assert stats.additions == 0
        assert stats.deletions == 0
