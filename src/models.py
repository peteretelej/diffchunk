"""Data models for diffchunk MCP server."""

import fnmatch
from dataclasses import dataclass
from typing import Dict, List


@dataclass
class DiffStats:
    """Statistics about a loaded diff."""

    total_files: int
    total_lines: int
    chunks_count: int


@dataclass
class ChunkInfo:
    """Information about a diff chunk."""

    chunk_number: int
    files: List[str]
    line_count: int
    summary: str
    parent_file: str | None = None
    sub_chunk_index: int | None = None


@dataclass
class DiffChunk:
    """A chunk of diff content."""

    number: int
    content: str
    files: List[str]
    line_count: int
    parent_file: str | None = None
    sub_chunk_index: int | None = None


class DiffSession:
    """Manages a loaded diff file and its chunks."""

    def __init__(self, file_path: str):
        self.file_path = file_path
        self.chunks: List[DiffChunk] = []
        self.file_to_chunks: Dict[str, List[int]] = {}
        self.stats: DiffStats = DiffStats(0, 0, 0)

    def add_chunk(self, chunk: DiffChunk) -> None:
        """Add a chunk to the session."""
        self.chunks.append(chunk)
        for file_path in chunk.files:
            if file_path not in self.file_to_chunks:
                self.file_to_chunks[file_path] = []
            self.file_to_chunks[file_path].append(chunk.number)

    def get_chunk(self, chunk_number: int) -> DiffChunk | None:
        """Get a chunk by number (1-indexed)."""
        if 1 <= chunk_number <= len(self.chunks):
            return self.chunks[chunk_number - 1]
        return None

    def get_chunk_info(self, chunk_number: int) -> ChunkInfo | None:
        """Get chunk info by number (1-indexed)."""
        chunk = self.get_chunk(chunk_number)
        if chunk:
            # Create summary with parent file info if available
            if chunk.parent_file and chunk.sub_chunk_index is not None:
                summary = f"{chunk.parent_file} (part {chunk.sub_chunk_index}), {chunk.line_count} lines"
            else:
                summary = f"{len(chunk.files)} files, {chunk.line_count} lines"

            return ChunkInfo(
                chunk_number=chunk.number,
                files=chunk.files,
                line_count=chunk.line_count,
                summary=summary,
                parent_file=chunk.parent_file,
                sub_chunk_index=chunk.sub_chunk_index,
            )
        return None

    def list_chunk_infos(self) -> List[ChunkInfo]:
        """Get info for all chunks."""
        infos = []
        for i in range(len(self.chunks)):
            info = self.get_chunk_info(i + 1)
            if info:
                infos.append(info)
        return infos

    def find_chunks_for_files(self, pattern: str) -> List[int]:
        """Find chunk numbers containing files matching pattern."""
        matching_chunks = set()

        for file_path, chunk_numbers in self.file_to_chunks.items():
            if fnmatch.fnmatch(file_path, pattern):
                matching_chunks.update(chunk_numbers)

        return sorted(matching_chunks)

    def update_stats(self) -> None:
        """Update session statistics."""
        total_files = len(self.file_to_chunks)
        total_lines = sum(chunk.line_count for chunk in self.chunks)
        chunks_count = len(self.chunks)

        self.stats = DiffStats(
            total_files=total_files, total_lines=total_lines, chunks_count=chunks_count
        )
