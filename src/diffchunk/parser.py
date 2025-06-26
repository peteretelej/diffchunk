"""Diff parsing functionality."""

import re
from dataclasses import dataclass
from typing import List, Optional, TextIO


@dataclass
class FileChange:
    """Represents a single file change in a diff."""
    old_path: str
    new_path: str
    old_start: int
    old_count: int
    new_start: int
    new_count: int
    lines: List[str]
    is_binary: bool = False
    is_new_file: bool = False
    is_deleted_file: bool = False


@dataclass
class DiffStats:
    """Statistics about a diff file."""
    total_lines: int
    files_changed: int
    additions: int
    deletions: int
    binary_files: int
    trivial_changes: int


class DiffParser:
    """Parser for unified diff format."""

    # Regex patterns for diff parsing
    FILE_HEADER_PATTERN = re.compile(r'^diff --git a/(.*) b/(.*)$')
    OLD_FILE_PATTERN = re.compile(r'^--- (.*)$')
    NEW_FILE_PATTERN = re.compile(r'^\+\+\+ (.*)$')
    HUNK_HEADER_PATTERN = re.compile(r'^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@.*$')
    BINARY_PATTERN = re.compile(r'^Binary files? .* differ$')
    NEW_FILE_MODE_PATTERN = re.compile(r'^new file mode \d+$')
    DELETED_FILE_MODE_PATTERN = re.compile(r'^deleted file mode \d+$')

    def __init__(self) -> None:
        self.file_changes: List[FileChange] = []
        self.stats = DiffStats(0, 0, 0, 0, 0, 0)

    def parse_file(self, file_path: str) -> List[FileChange]:
        """Parse a diff file and return list of file changes."""
        with open(file_path, encoding='utf-8', errors='ignore') as f:
            return self.parse_stream(f)

    def parse_stream(self, stream: TextIO) -> List[FileChange]:
        """Parse a diff from a stream."""
        self.file_changes = []
        self.stats = DiffStats(0, 0, 0, 0, 0, 0)

        lines = stream.readlines()
        self.stats.total_lines = len(lines)

        i = 0
        while i < len(lines):
            line = lines[i].rstrip('\n\r')

            # Look for file header
            match = self.FILE_HEADER_PATTERN.match(line)
            if match:
                old_path, new_path = match.groups()
                i, file_change = self._parse_file_change(lines, i, old_path, new_path)
                if file_change:
                    self.file_changes.append(file_change)
                    self.stats.files_changed += 1
                    if file_change.is_binary:
                        self.stats.binary_files += 1
            else:
                i += 1

        # Calculate addition/deletion stats
        for change in self.file_changes:
            for line in change.lines:
                if line.startswith('+') and not line.startswith('+++'):
                    self.stats.additions += 1
                elif line.startswith('-') and not line.startswith('---'):
                    self.stats.deletions += 1

        return self.file_changes

    def _parse_file_change(self, lines: List[str], start_idx: int, old_path: str, new_path: str) -> tuple[int, Optional[FileChange]]:
        """Parse a single file change starting from the given index."""
        i = start_idx + 1
        file_lines: List[str] = [lines[start_idx].rstrip('\n\r')]

        is_binary = False
        is_new_file = False
        is_deleted_file = False
        old_start = new_start = 0
        old_count = new_count = 0

        # Parse file metadata
        while i < len(lines):
            line = lines[i].rstrip('\n\r')
            file_lines.append(line)

            if self.BINARY_PATTERN.match(line):
                is_binary = True
                i += 1
                break
            elif self.NEW_FILE_MODE_PATTERN.match(line):
                is_new_file = True
            elif self.DELETED_FILE_MODE_PATTERN.match(line):
                is_deleted_file = True
            elif self.OLD_FILE_PATTERN.match(line):
                pass  # Skip old file line
            elif self.NEW_FILE_PATTERN.match(line):
                pass  # Skip new file line
            elif self.HUNK_HEADER_PATTERN.match(line):
                # Start of hunk, parse hunks
                i, hunk_lines = self._parse_hunks(lines, i)
                file_lines.extend(hunk_lines)
                break
            elif line.startswith('diff --git'):
                # Next file, back up one line
                i -= 1
                break

            i += 1

        # Extract hunk info from first hunk if available
        for line in file_lines:
            match = self.HUNK_HEADER_PATTERN.match(line)
            if match:
                old_start = int(match.group(1))
                old_count = int(match.group(2)) if match.group(2) else 1
                new_start = int(match.group(3))
                new_count = int(match.group(4)) if match.group(4) else 1
                break

        file_change = FileChange(
            old_path=old_path,
            new_path=new_path,
            old_start=old_start,
            old_count=old_count,
            new_start=new_start,
            new_count=new_count,
            lines=file_lines,
            is_binary=is_binary,
            is_new_file=is_new_file,
            is_deleted_file=is_deleted_file
        )

        return i, file_change

    def _parse_hunks(self, lines: List[str], start_idx: int) -> tuple[int, List[str]]:
        """Parse all hunks for a file."""
        hunk_lines: List[str] = []
        i = start_idx

        while i < len(lines):
            line = lines[i].rstrip('\n\r')

            if self.HUNK_HEADER_PATTERN.match(line):
                # Start of a hunk
                hunk_lines.append(line)
                i += 1

                # Parse hunk content
                while i < len(lines):
                    line = lines[i].rstrip('\n\r')

                    if (line.startswith(' ') or line.startswith('+') or
                        line.startswith('-') or line.startswith('\\')):
                        hunk_lines.append(line)
                        i += 1
                    else:
                        # End of hunk
                        break
            elif line.startswith('diff --git'):
                # Next file
                break
            else:
                i += 1

        return i, hunk_lines

    def get_stats(self) -> DiffStats:
        """Get statistics about the parsed diff."""
        return self.stats

    def get_file_changes(self) -> List[FileChange]:
        """Get list of file changes."""
        return self.file_changes
