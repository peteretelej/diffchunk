"""MCP tools implementation for diffchunk."""

import os
from typing import Dict, Any, List, Optional
from .models import DiffSession
from .chunker import DiffChunker


class DiffChunkTools:
    """MCP tools for diff chunk navigation."""
    
    def __init__(self):
        self.current_session: Optional[DiffSession] = None
        self.chunker = DiffChunker()
    
    def load_diff(self, file_path: str, max_chunk_lines: int = 4000,
                  skip_trivial: bool = True, skip_generated: bool = True,
                  include_patterns: Optional[str] = None,
                  exclude_patterns: Optional[str] = None) -> Dict[str, Any]:
        """Load and parse a diff file into chunks."""
        # Validate inputs
        if not file_path or not isinstance(file_path, str):
            raise ValueError("file_path must be a non-empty string")
        
        if not isinstance(max_chunk_lines, int) or max_chunk_lines <= 0:
            raise ValueError("max_chunk_lines must be a positive integer")
        
        # Validate file exists and is readable
        if not os.path.exists(file_path):
            raise ValueError(f"Diff file not found: {file_path}")
        
        if not os.path.isfile(file_path):
            raise ValueError(f"Path is not a file: {file_path}")
        
        if not os.access(file_path, os.R_OK):
            raise ValueError(f"Cannot read file: {file_path}")
        
        # Parse patterns
        include_list = None
        exclude_list = None
        
        if include_patterns:
            include_list = [p.strip() for p in include_patterns.split(',') if p.strip()]
        
        if exclude_patterns:
            exclude_list = [p.strip() for p in exclude_patterns.split(',') if p.strip()]
        
        # Create new session
        self.current_session = DiffSession(file_path)
        
        # Configure chunker
        self.chunker.max_chunk_lines = max_chunk_lines
        
        try:
            # Chunk the diff
            self.chunker.chunk_diff(
                self.current_session,
                skip_trivial=skip_trivial,
                skip_generated=skip_generated,
                include_patterns=include_list,
                exclude_patterns=exclude_list
            )
        except ValueError as e:
            self.current_session = None
            raise e
        
        # Return overview
        return {
            "chunks": self.current_session.stats.chunks_count,
            "files": self.current_session.stats.total_files,
            "total_lines": self.current_session.stats.total_lines,
            "file_path": file_path
        }
    
    def list_chunks(self) -> List[Dict[str, Any]]:
        """List all chunks with their metadata."""
        if not self.current_session:
            raise ValueError("No diff loaded. Use load_diff() first.")
        
        chunk_infos = self.current_session.list_chunk_infos()
        
        return [
            {
                "chunk": info.chunk_number,
                "files": info.files,
                "lines": info.line_count,
                "summary": info.summary
            }
            for info in chunk_infos
        ]
    
    def get_chunk(self, chunk_number: int, include_context: bool = True) -> str:
        """Get the content of a specific chunk."""
        if not self.current_session:
            raise ValueError("No diff loaded. Use load_diff() first.")
        
        if not isinstance(chunk_number, int) or chunk_number <= 0:
            raise ValueError("chunk_number must be a positive integer")
        
        chunk = self.current_session.get_chunk(chunk_number)
        if not chunk:
            total_chunks = len(self.current_session.chunks)
            raise ValueError(f"Chunk {chunk_number} not found. Available chunks: 1-{total_chunks}")
        
        if include_context:
            header = f"=== Chunk {chunk.number} of {len(self.current_session.chunks)} ===\n"
            header += f"Files: {', '.join(chunk.files)}\n"
            header += f"Lines: {chunk.line_count}\n"
            header += "=" * 50 + "\n"
            return header + chunk.content
        else:
            return chunk.content
    
    def find_chunks_for_files(self, pattern: str) -> List[int]:
        """Find chunks containing files matching the given pattern."""
        if not self.current_session:
            raise ValueError("No diff loaded. Use load_diff() first.")
        
        if not isinstance(pattern, str) or not pattern.strip():
            raise ValueError("Pattern must be a non-empty string")
        
        matching_chunks = self.current_session.find_chunks_for_files(pattern.strip())
        
        return matching_chunks
    
    def get_current_overview(self) -> Dict[str, Any]:
        """Get overview of currently loaded diff."""
        if not self.current_session:
            return {"loaded": False, "message": "No diff currently loaded"}
        
        return {
            "loaded": True,
            "file_path": self.current_session.file_path,
            "chunks": self.current_session.stats.chunks_count,
            "files": self.current_session.stats.total_files,
            "total_lines": self.current_session.stats.total_lines
        }