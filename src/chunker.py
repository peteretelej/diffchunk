"""Diff chunking functionality."""

import re
from typing import List, Tuple
from .models import DiffChunk, DiffSession
from .parser import DiffParser


class DiffChunker:
    """Chunks diff content into manageable pieces."""

    def __init__(self, max_chunk_lines: int = 1000):
        self.max_chunk_lines = max_chunk_lines
        self.parser = DiffParser()

    def chunk_diff(
        self,
        session: DiffSession,
        skip_trivial: bool = True,
        skip_generated: bool = True,
        include_patterns: List[str] | None = None,
        exclude_patterns: List[str] | None = None,
    ) -> None:
        """Chunk a diff file into the session."""
        chunk_number = 1
        current_chunk_lines = 0
        current_chunk_content: List[str] = []
        current_chunk_files: List[str] = []

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

            if not self.parser.should_include_file(
                files, include_patterns, exclude_patterns
            ):
                continue

            content_lines = self.parser.count_lines(content)

            # Check if this file needs to be split
            if content_lines > self.max_chunk_lines:
                # Save current chunk if it has content
                if current_chunk_content:
                    self._save_chunk(
                        session,
                        chunk_number,
                        current_chunk_content,
                        current_chunk_files,
                        current_chunk_lines,
                    )
                    chunk_number += 1
                    current_chunk_content = []
                    current_chunk_files = []
                    current_chunk_lines = 0

                # Split the large file
                file_chunks = self._split_large_file(files, content, content_lines)
                parent_file = files[0] if len(files) == 1 else f"{len(files)} files"

                for sub_index, (sub_files, sub_content, sub_lines) in enumerate(
                    file_chunks, 1
                ):
                    self._save_chunk(
                        session,
                        chunk_number,
                        [sub_content],
                        sub_files,
                        sub_lines,
                        parent_file=parent_file,
                        sub_chunk_index=sub_index if len(file_chunks) > 1 else None,
                    )
                    chunk_number += 1
            else:
                # Check if we need to start a new chunk
                if (
                    current_chunk_content
                    and current_chunk_lines + content_lines > self.max_chunk_lines
                ):
                    # Save current chunk
                    self._save_chunk(
                        session,
                        chunk_number,
                        current_chunk_content,
                        current_chunk_files,
                        current_chunk_lines,
                    )

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
            self._save_chunk(
                session,
                chunk_number,
                current_chunk_content,
                current_chunk_files,
                current_chunk_lines,
            )

        # Update session statistics
        session.update_stats()

        if not session.chunks:
            raise ValueError(
                "No chunks created - all changes may have been filtered out"
            )

    def _save_chunk(
        self,
        session: DiffSession,
        chunk_number: int,
        content_list: List[str],
        files: List[str],
        line_count: int,
        parent_file: str | None = None,
        sub_chunk_index: int | None = None,
    ) -> None:
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
            content="\n\n".join(content_list),
            files=unique_files,
            line_count=line_count,
            parent_file=parent_file,
            sub_chunk_index=sub_chunk_index,
        )

        session.add_chunk(chunk)

    def _split_large_file(
        self, files: List[str], content: str, file_line_count: int
    ) -> List[Tuple[List[str], str, int]]:
        """Split a large file's diff content at hunk boundaries."""
        if file_line_count <= self.max_chunk_lines:
            return [(files, content, file_line_count)]

        # Pattern to match hunk headers like @@ -1,4 +1,6 @@
        hunk_pattern = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@.*$")

        lines = content.split("\n")
        chunks = []
        current_chunk_lines: List[str] = []
        current_chunk_line_count = 0

        # Keep track of file header (diff --git, index, +++, ---)
        file_header_lines = []
        in_header = True

        # Be very aggressive about staying under the limit
        target_chunk_size = max(
            self.max_chunk_lines * 0.8, 200
        )  # 80% of limit or 200 lines minimum

        for i, line in enumerate(lines):
            if in_header:
                # Collect file header lines until we reach the first hunk
                if hunk_pattern.match(line):
                    in_header = False
                else:
                    file_header_lines.append(line)
                    continue

            # Check if this is a hunk header and we should split
            is_hunk_header = hunk_pattern.match(line)
            total_size = current_chunk_line_count + len(file_header_lines)

            # Much more aggressive splitting criteria
            should_split = (
                is_hunk_header
                and current_chunk_lines
                and total_size >= target_chunk_size
            )

            if should_split:
                # Save current chunk
                chunk_content = "\n".join(file_header_lines + current_chunk_lines)
                actual_lines = len(
                    [
                        line
                        for line in (file_header_lines + current_chunk_lines)
                        if line.strip()
                    ]
                )
                chunks.append((files, chunk_content, actual_lines))

                # Start new chunk with file header
                current_chunk_lines = []
                current_chunk_line_count = 0

            current_chunk_lines.append(line)
            if line.strip():  # Count non-empty lines
                current_chunk_line_count += 1

            # STRICT enforcement: split immediately if we exceed limit
            if (
                current_chunk_line_count + len(file_header_lines)
                >= self.max_chunk_lines
            ):
                # Find the last hunk header in current chunk to split there
                last_hunk_idx = None
                for j in range(len(current_chunk_lines) - 1, -1, -1):
                    if hunk_pattern.match(current_chunk_lines[j]):
                        last_hunk_idx = j
                        break

                if last_hunk_idx is not None and last_hunk_idx > 0:
                    # Split at the last hunk boundary
                    split_content = current_chunk_lines[:last_hunk_idx]
                    chunk_content = "\n".join(file_header_lines + split_content)
                    actual_lines = len(
                        [
                            line
                            for line in (file_header_lines + split_content)
                            if line.strip()
                        ]
                    )
                    chunks.append((files, chunk_content, actual_lines))

                    # Continue with remaining content
                    current_chunk_lines = current_chunk_lines[last_hunk_idx:]
                    current_chunk_line_count = len(
                        [line for line in current_chunk_lines if line.strip()]
                    )
                else:
                    # No hunk boundary found, force split anyway
                    chunk_content = "\n".join(file_header_lines + current_chunk_lines)
                    actual_lines = len(
                        [
                            line
                            for line in (file_header_lines + current_chunk_lines)
                            if line.strip()
                        ]
                    )
                    chunks.append((files, chunk_content, actual_lines))

                    # Start fresh
                    current_chunk_lines = []
                    current_chunk_line_count = 0

        # Save final chunk
        if current_chunk_lines:
            chunk_content = "\n".join(file_header_lines + current_chunk_lines)
            actual_lines = len(
                [
                    line
                    for line in (file_header_lines + current_chunk_lines)
                    if line.strip()
                ]
            )
            chunks.append((files, chunk_content, actual_lines))

        return chunks if chunks else [(files, content, file_line_count)]
