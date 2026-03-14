"""MCP tools implementation for diffchunk."""

import fnmatch
import hashlib
import logging
import os
import time
from typing import Dict, Any, List, Optional
from .models import DiffSession
from .chunker import DiffChunker

logger = logging.getLogger("diffchunk")


class DiffChunkTools:
    """MCP tools for diff chunk navigation."""

    def __init__(self):
        self.sessions: Dict[str, DiffSession] = {}  # file_key -> session
        self.chunker = DiffChunker()

    def _get_file_key(self, absolute_file_path: str) -> str:
        """Generate unique key from canonical path + content hash."""
        # Canonicalize the path
        canonical_path = os.path.realpath(os.path.expanduser(absolute_file_path))

        # Read file content and compute hash
        try:
            with open(canonical_path, "rb") as f:
                content_hash = hashlib.sha256(f.read()).hexdigest()[:16]  # Short hash
        except (OSError, IOError) as e:
            raise ValueError(f"Cannot access file {absolute_file_path}: {e}")

        return f"{canonical_path}#{content_hash}"

    def _ensure_loaded(self, absolute_file_path: str, **load_kwargs) -> str:
        """Ensure diff is loaded, return file key."""
        file_key = self._get_file_key(absolute_file_path)

        if file_key not in self.sessions:
            # Auto-load with provided or default settings
            self._load_diff_internal(absolute_file_path, **load_kwargs)
            file_key = self._get_file_key(absolute_file_path)  # Refresh after load

        return file_key

    def _load_diff_internal(
        self,
        absolute_file_path: str,
        max_chunk_lines: int = 1000,
        skip_trivial: bool = True,
        skip_generated: bool = True,
        include_patterns: Optional[str] = None,
        exclude_patterns: Optional[str] = None,
    ) -> DiffSession:
        """Internal method to load and parse a diff file."""
        # Validate inputs
        if (
            not absolute_file_path
            or not isinstance(absolute_file_path, str)
            or not absolute_file_path.strip()
        ):
            raise ValueError("absolute_file_path must be a non-empty string")

        if not isinstance(max_chunk_lines, int) or max_chunk_lines <= 0:
            raise ValueError("max_chunk_lines must be a positive integer")

        # Canonicalize path
        resolved_file_path = os.path.realpath(os.path.expanduser(absolute_file_path))

        # Validate file exists and is readable
        if os.path.exists(resolved_file_path) and not os.path.isfile(
            resolved_file_path
        ):
            raise ValueError(f"Path is not a file: {resolved_file_path}")

        if not os.path.exists(resolved_file_path):
            raise ValueError(
                f"Diff file not found: {absolute_file_path}. Verify the file exists and the path is absolute."
            )

        if not os.access(resolved_file_path, os.R_OK):
            raise ValueError(f"Cannot read file: {resolved_file_path}")

        # Parse patterns
        include_list = None
        exclude_list = None

        if include_patterns:
            include_list = [p.strip() for p in include_patterns.split(",") if p.strip()]

        if exclude_patterns:
            exclude_list = [p.strip() for p in exclude_patterns.split(",") if p.strip()]

        # Create new session
        session = DiffSession(resolved_file_path)

        # Chunk the diff
        start = time.monotonic()
        self.chunker.chunk_diff(
            session,
            max_chunk_lines=max_chunk_lines,
            skip_trivial=skip_trivial,
            skip_generated=skip_generated,
            include_patterns=include_list,
            exclude_patterns=exclude_list,
        )
        elapsed = time.monotonic() - start
        logger.info(
            "Parsed and chunked %s: %d chunks, %d files in %.2fs",
            absolute_file_path,
            session.stats.chunks_count,
            session.stats.total_files,
            elapsed,
        )

        # Store session
        file_key = self._get_file_key(absolute_file_path)
        self.sessions[file_key] = session

        return session

    def load_diff(
        self,
        absolute_file_path: str,
        max_chunk_lines: int = 1000,
        skip_trivial: bool = True,
        skip_generated: bool = True,
        include_patterns: Optional[str] = None,
        exclude_patterns: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Load and parse a diff file into chunks."""
        session = self._load_diff_internal(
            absolute_file_path=absolute_file_path,
            max_chunk_lines=max_chunk_lines,
            skip_trivial=skip_trivial,
            skip_generated=skip_generated,
            include_patterns=include_patterns,
            exclude_patterns=exclude_patterns,
        )

        # Return overview
        return {
            "chunks": session.stats.chunks_count,
            "files": session.stats.total_files,
            "total_lines": session.stats.total_lines,
            "file_path": absolute_file_path,
        }

    def list_chunks(self, absolute_file_path: str) -> List[Dict[str, Any]]:
        """List all chunks with their metadata."""
        file_key = self._ensure_loaded(absolute_file_path)
        session = self.sessions[file_key]

        chunk_infos = session.list_chunk_infos()

        return [
            {
                "chunk": info.chunk_number,
                "files": info.files,
                "file_details": info.file_details,
                "lines": info.line_count,
                "summary": info.summary,
                "parent_file": info.parent_file,
                "sub_chunk_index": info.sub_chunk_index,
            }
            for info in chunk_infos
        ]

    def get_chunk(
        self, absolute_file_path: str, chunk_number: int, include_context: bool = True
    ) -> str:
        """Get the content of a specific chunk."""
        file_key = self._ensure_loaded(absolute_file_path)
        session = self.sessions[file_key]

        if not isinstance(chunk_number, int) or chunk_number <= 0:
            raise ValueError("chunk_number must be a positive integer")

        chunk = session.get_chunk(chunk_number)
        if not chunk:
            total_chunks = len(session.chunks)
            raise ValueError(
                f"Chunk {chunk_number} does not exist. The diff has {total_chunks} chunks (1-{total_chunks}). Use list_chunks to see what each chunk contains."
            )

        if include_context:
            header = f"=== Chunk {chunk.number} of {len(session.chunks)} ===\n"
            header += f"Files: {', '.join(chunk.files)}\n"
            header += f"Lines: {chunk.line_count}\n"
            header += "=" * 50 + "\n"
            return header + chunk.content
        else:
            return chunk.content

    def find_chunks_for_files(self, absolute_file_path: str, pattern: str) -> List[int]:
        """Find chunks containing files matching the given pattern."""
        file_key = self._ensure_loaded(absolute_file_path)
        session = self.sessions[file_key]

        if not isinstance(pattern, str) or not pattern.strip():
            raise ValueError(
                "Pattern must be a non-empty string. Use '*' to match all files, '*.py' for Python files, or 'src/*' for a directory."
            )

        matching_chunks = session.find_chunks_for_files(pattern.strip())

        return matching_chunks

    def get_file_diff(self, absolute_file_path: str, file_path: str) -> str:
        """Extract the diff for a single file from a loaded diff."""
        file_key = self._ensure_loaded(absolute_file_path)
        session = self.sessions[file_key]

        if not isinstance(file_path, str) or not file_path.strip():
            raise ValueError("file_path must be a non-empty string")

        file_path = file_path.strip()
        all_files = list(session.file_to_chunks.keys())

        # Try exact match first, then glob matching (case-insensitive)
        matches = [f for f in all_files if f.lower() == file_path.lower()]
        if not matches:
            matches = [
                f for f in all_files if fnmatch.fnmatch(f.lower(), file_path.lower())
            ]

        if not matches:
            available = ", ".join(sorted(all_files)[:20])
            suffix = "..." if len(all_files) > 20 else ""
            raise ValueError(
                f"No file matching '{file_path}' found in diff. "
                f"Available files: {available}{suffix}. Use find_chunks_for_files to search by pattern."
            )

        if len(matches) > 1:
            matched_list = ", ".join(sorted(matches))
            raise ValueError(
                f"Pattern '{file_path}' matches {len(matches)} files: {matched_list}. "
                f"Use a more specific path or exact filename."
            )

        target_file = matches[0]

        # Re-parse the diff file and extract only the target file's content
        parts = []
        for files, content in self.chunker.parser.parse_diff_file(session.file_path):
            if target_file in files:
                parts.append(content)

        if not parts:
            raise ValueError(f"File '{target_file}' not found in diff content")

        return "\n\n".join(parts)

    def get_current_overview(self) -> Dict[str, Any]:
        """Get overview of all loaded diffs."""
        if not self.sessions:
            return {"loaded": False, "message": "No diffs currently loaded"}

        overviews = []
        for file_key, session in self.sessions.items():
            overviews.append(
                {
                    "file_path": session.file_path,
                    "chunks": session.stats.chunks_count,
                    "files": session.stats.total_files,
                    "total_lines": session.stats.total_lines,
                }
            )

        return {
            "loaded": True,
            "total_sessions": len(self.sessions),
            "sessions": overviews,
        }
