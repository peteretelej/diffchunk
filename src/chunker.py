"""Diff chunking functionality."""

from typing import List
from .models import DiffChunk, DiffSession
from .parser import DiffParser


class DiffChunker:
    """Chunks diff content into manageable pieces."""
    
    def __init__(self, max_chunk_lines: int = 4000):
        self.max_chunk_lines = max_chunk_lines
        self.parser = DiffParser()
    
    def chunk_diff(self, session: DiffSession, skip_trivial: bool = True, 
                   skip_generated: bool = True, include_patterns: List[str] = None,
                   exclude_patterns: List[str] = None) -> None:
        """Chunk a diff file into the session."""
        chunk_number = 1
        current_chunk_lines = 0
        current_chunk_content = []
        current_chunk_files = []
        
        try:
            file_changes = list(self.parser.parse_diff_file(session.file_path))
        except ValueError as e:
            raise ValueError(f"Failed to parse diff: {e}")
        
        if not file_changes:
            raise ValueError("No valid diff content found")
        
        for files, content in file_changes:
            # Apply filters
            if skip_trivial and self.parser.is_trivial_change(content):
                continue
            
            if skip_generated and self.parser.is_generated_file(files):
                continue
            
            if not self.parser.should_include_file(files, include_patterns, exclude_patterns):
                continue
            
            content_lines = self.parser.count_lines(content)
            
            # Check if we need to start a new chunk
            if (current_chunk_content and 
                current_chunk_lines + content_lines > self.max_chunk_lines):
                # Save current chunk
                self._save_chunk(session, chunk_number, current_chunk_content, 
                               current_chunk_files, current_chunk_lines)
                
                # Start new chunk
                chunk_number += 1
                current_chunk_content = []
                current_chunk_files = []
                current_chunk_lines = 0
            
            # Add to current chunk
            current_chunk_content.append(content)
            current_chunk_files.extend(files)
            current_chunk_lines += content_lines
        
        # Save final chunk if it has content
        if current_chunk_content:
            self._save_chunk(session, chunk_number, current_chunk_content,
                           current_chunk_files, current_chunk_lines)
        
        # Update session statistics
        session.update_stats()
        
        if not session.chunks:
            raise ValueError("No chunks created - all changes may have been filtered out")
    
    def _save_chunk(self, session: DiffSession, chunk_number: int, 
                   content_list: List[str], files: List[str], line_count: int) -> None:
        """Save a chunk to the session."""
        # Remove duplicates from files while preserving order
        unique_files = []
        seen = set()
        for file_path in files:
            if file_path not in seen:
                unique_files.append(file_path)
                seen.add(file_path)
        
        chunk = DiffChunk(
            number=chunk_number,
            content='\n\n'.join(content_list),
            files=unique_files,
            line_count=line_count
        )
        
        session.add_chunk(chunk)