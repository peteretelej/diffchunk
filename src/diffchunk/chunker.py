"""Diff chunking functionality."""

from dataclasses import dataclass
from typing import List, Optional

from .parser import FileChange


@dataclass
class DiffChunk:
    """Represents a chunk of a diff."""
    chunk_number: int
    total_chunks: int
    file_changes: List[FileChange]
    line_count: int
    file_count: int
    summary: str


class DiffChunker:
    """Chunks large diffs into manageable parts."""

    def __init__(self, max_lines: int = 5000, prefer_file_boundaries: bool = True) -> None:
        self.max_lines = max_lines
        self.prefer_file_boundaries = prefer_file_boundaries
        self.chunks: List[DiffChunk] = []

    def chunk_changes(self, file_changes: List[FileChange]) -> List[DiffChunk]:
        """Split file changes into chunks."""
        if not file_changes:
            return []

        self.chunks = []

        if self.prefer_file_boundaries:
            self._chunk_by_file_boundaries(file_changes)
        else:
            self._chunk_by_line_count(file_changes)

        return self.chunks

    def _chunk_by_file_boundaries(self, file_changes: List[FileChange]) -> None:
        """Chunk by keeping files together when possible."""
        current_chunk_files: List[FileChange] = []
        current_line_count = 0

        for file_change in file_changes:
            file_line_count = len(file_change.lines)

            # If adding this file would exceed max_lines and we have files in current chunk
            if (current_line_count + file_line_count > self.max_lines and
                current_chunk_files):

                # Finalize current chunk
                self._add_chunk(current_chunk_files, current_line_count)
                current_chunk_files = []
                current_line_count = 0

            # If single file exceeds max_lines, split it
            if file_line_count > self.max_lines:
                # Add any pending files first
                if current_chunk_files:
                    self._add_chunk(current_chunk_files, current_line_count)
                    current_chunk_files = []
                    current_line_count = 0

                # Split large file into multiple chunks
                self._split_large_file(file_change)
            else:
                # Add file to current chunk
                current_chunk_files.append(file_change)
                current_line_count += file_line_count

        # Add remaining files as final chunk
        if current_chunk_files:
            self._add_chunk(current_chunk_files, current_line_count)

    def _chunk_by_line_count(self, file_changes: List[FileChange]) -> None:
        """Chunk strictly by line count, potentially splitting files."""
        current_chunk_files: List[FileChange] = []
        current_line_count = 0

        for file_change in file_changes:
            remaining_lines = file_change.lines[:]

            while remaining_lines:
                # Calculate how many lines we can take
                available_space = self.max_lines - current_line_count

                if available_space <= 0:
                    # Current chunk is full, start new one
                    if current_chunk_files:
                        self._add_chunk(current_chunk_files, current_line_count)
                    current_chunk_files = []
                    current_line_count = 0
                    available_space = self.max_lines

                # Take lines up to available space
                lines_to_take = min(len(remaining_lines), available_space)
                chunk_lines = remaining_lines[:lines_to_take]
                remaining_lines = remaining_lines[lines_to_take:]

                # Create partial file change
                partial_change = FileChange(
                    old_path=file_change.old_path,
                    new_path=file_change.new_path,
                    old_start=file_change.old_start,
                    old_count=file_change.old_count,
                    new_start=file_change.new_start,
                    new_count=file_change.new_count,
                    lines=chunk_lines,
                    is_binary=file_change.is_binary,
                    is_new_file=file_change.is_new_file,
                    is_deleted_file=file_change.is_deleted_file
                )

                current_chunk_files.append(partial_change)
                current_line_count += len(chunk_lines)

        # Add final chunk
        if current_chunk_files:
            self._add_chunk(current_chunk_files, current_line_count)

    def _split_large_file(self, file_change: FileChange) -> None:
        """Split a large file into multiple chunks."""
        lines = file_change.lines
        header_lines = []
        content_lines = []

        # Separate header lines from content
        for line in lines:
            if (line.startswith('diff --git') or
                line.startswith('index ') or
                line.startswith('---') or
                line.startswith('+++') or
                line.startswith('new file mode') or
                line.startswith('deleted file mode') or
                line.startswith('Binary files')):
                header_lines.append(line)
            else:
                content_lines.append(line)

        # Split content into chunks
        chunk_size = self.max_lines - len(header_lines)
        if chunk_size <= 0:
            chunk_size = self.max_lines // 2  # Fallback

        for i in range(0, len(content_lines), chunk_size):
            chunk_content = content_lines[i:i + chunk_size]
            chunk_lines = header_lines + chunk_content

            partial_change = FileChange(
                old_path=file_change.old_path,
                new_path=file_change.new_path,
                old_start=file_change.old_start,
                old_count=file_change.old_count,
                new_start=file_change.new_start,
                new_count=file_change.new_count,
                lines=chunk_lines,
                is_binary=file_change.is_binary,
                is_new_file=file_change.is_new_file,
                is_deleted_file=file_change.is_deleted_file
            )

            self._add_chunk([partial_change], len(chunk_lines))

    def _add_chunk(self, file_changes: List[FileChange], line_count: int) -> None:
        """Add a chunk to the list."""
        file_paths = []
        for change in file_changes:
            if change.new_path not in file_paths:
                file_paths.append(change.new_path)

        summary = self._generate_summary(file_changes, file_paths)

        chunk = DiffChunk(
            chunk_number=len(self.chunks) + 1,
            total_chunks=0,  # Will be updated later
            file_changes=file_changes,
            line_count=line_count,
            file_count=len(file_paths),
            summary=summary
        )

        self.chunks.append(chunk)

    def _generate_summary(self, file_changes: List[FileChange], file_paths: List[str]) -> str:
        """Generate a summary for the chunk."""
        if len(file_paths) == 1:
            return f"Changes to {file_paths[0]}"
        elif len(file_paths) <= 3:
            return f"Changes to {', '.join(file_paths)}"
        else:
            return f"Changes to {file_paths[0]}, {file_paths[1]} and {len(file_paths) - 2} other files"

    def get_chunk(self, chunk_number: int) -> Optional[DiffChunk]:
        """Get a specific chunk by number."""
        if 1 <= chunk_number <= len(self.chunks):
            chunk = self.chunks[chunk_number - 1]
            # Update total chunks
            chunk.total_chunks = len(self.chunks)
            return chunk
        return None

    def get_all_chunks(self) -> List[DiffChunk]:
        """Get all chunks with updated total counts."""
        total_chunks = len(self.chunks)
        for chunk in self.chunks:
            chunk.total_chunks = total_chunks
        return self.chunks

    def get_chunk_count(self) -> int:
        """Get total number of chunks."""
        return len(self.chunks)

    def format_chunk(self, chunk: DiffChunk, include_metadata: bool = True) -> str:
        """Format a chunk for output."""
        lines = []

        if include_metadata:
            lines.append(f"=== Chunk {chunk.chunk_number} of {chunk.total_chunks} ===")
            lines.append(f"Files: {chunk.summary} ({chunk.file_count} files)")
            lines.append(f"Lines: {chunk.line_count:,}")
            lines.append("")

        # Add all file changes
        for file_change in chunk.file_changes:
            lines.extend(file_change.lines)
            lines.append("")  # Add blank line between files

        return "\n".join(lines)

    def get_chunk_stats(self) -> dict:
        """Get statistics about the chunks."""
        if not self.chunks:
            return {}

        total_lines = sum(chunk.line_count for chunk in self.chunks)
        total_files = sum(chunk.file_count for chunk in self.chunks)
        avg_lines = total_lines / len(self.chunks)

        return {
            "total_chunks": len(self.chunks),
            "total_lines": total_lines,
            "total_files": total_files,
            "avg_lines_per_chunk": round(avg_lines, 1),
            "max_lines_per_chunk": max(chunk.line_count for chunk in self.chunks),
            "min_lines_per_chunk": min(chunk.line_count for chunk in self.chunks),
        }
