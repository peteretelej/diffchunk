"""Change filtering functionality."""

import re
from typing import List

from .parser import FileChange


class ChangeFilter:
    """Filter for removing trivial changes from diffs."""

    # Patterns for trivial changes
    WHITESPACE_ONLY_PATTERN = re.compile(r'^[+-]\s*$')
    NEWLINE_ONLY_PATTERN = re.compile(r'^[+-]$')
    TRAILING_WHITESPACE_PATTERN = re.compile(r'^([+-])(.*)(\s+)$')

    # Common generated file patterns
    GENERATED_FILE_PATTERNS = [
        r'.*\.min\.(js|css)$',
        r'.*\.bundle\.(js|css)$',
        r'.*\.generated\.(js|ts|py|cs)$',
        r'.*\.g\.(cs|vb)$',
        r'.*\.designer\.(cs|vb)$',
        r'package-lock\.json$',
        r'yarn\.lock$',
        r'Pipfile\.lock$',
        r'poetry\.lock$',
        r'.*\.pyc$',
        r'.*\.pyo$',
        r'.*\.pyd$',
        r'__pycache__/.*',
        r'\.vs/.*',
        r'\.vscode/.*',
        r'node_modules/.*',
        r'bin/.*',
        r'obj/.*',
        r'dist/.*',
        r'build/.*',
    ]

    def __init__(self, skip_trivial: bool = True, skip_generated: bool = True) -> None:
        self.skip_trivial = skip_trivial
        self.skip_generated = skip_generated
        self.generated_patterns = [re.compile(pattern) for pattern in self.GENERATED_FILE_PATTERNS]
        self.trivial_count = 0

    def filter_changes(self, file_changes: List[FileChange]) -> List[FileChange]:
        """Filter file changes based on configured rules."""
        filtered_changes = []
        self.trivial_count = 0

        for change in file_changes:
            if self._should_skip_file(change):
                self.trivial_count += 1
                continue

            if self.skip_trivial:
                filtered_lines = self._filter_trivial_lines(change.lines)
                if not self._has_significant_changes(filtered_lines):
                    self.trivial_count += 1
                    continue

                # Create new change with filtered lines
                filtered_change = FileChange(
                    old_path=change.old_path,
                    new_path=change.new_path,
                    old_start=change.old_start,
                    old_count=change.old_count,
                    new_start=change.new_start,
                    new_count=change.new_count,
                    lines=filtered_lines,
                    is_binary=change.is_binary,
                    is_new_file=change.is_new_file,
                    is_deleted_file=change.is_deleted_file
                )
                filtered_changes.append(filtered_change)
            else:
                filtered_changes.append(change)

        return filtered_changes

    def _should_skip_file(self, change: FileChange) -> bool:
        """Check if entire file should be skipped."""
        if not self.skip_generated:
            return False

        # Check if file matches generated patterns
        for pattern in self.generated_patterns:
            if pattern.match(change.new_path) or pattern.match(change.old_path):
                return True

        return False

    def _filter_trivial_lines(self, lines: List[str]) -> List[str]:
        """Filter out trivial lines from diff content."""
        filtered_lines = []

        for line in lines:
            if self._is_trivial_line(line):
                continue
            filtered_lines.append(line)

        return filtered_lines

    def _is_trivial_line(self, line: str) -> bool:
        """Check if a single line is trivial."""
        # Skip non-change lines (headers, context, etc.)
        if not (line.startswith('+') or line.startswith('-')):
            return False

        # Skip file headers
        if line.startswith('+++') or line.startswith('---'):
            return False

        # Check for whitespace-only changes
        if self.WHITESPACE_ONLY_PATTERN.match(line):
            return True

        # Check for newline-only changes
        if self.NEWLINE_ONLY_PATTERN.match(line):
            return True

        # Check for trailing whitespace changes
        if self._is_trailing_whitespace_change(line):
            return True

        return False

    def _is_trailing_whitespace_change(self, line: str) -> bool:
        """Check if line is only a trailing whitespace change."""
        match = self.TRAILING_WHITESPACE_PATTERN.match(line)
        if not match:
            return False

        prefix, content, whitespace = match.groups()

        # If the content is empty and only whitespace differs, it's trivial
        return len(content.strip()) == 0

    def _has_significant_changes(self, lines: List[str]) -> bool:
        """Check if filtered lines contain significant changes."""
        change_lines = 0

        for line in lines:
            if line.startswith('+') and not line.startswith('+++'):
                change_lines += 1
            elif line.startswith('-') and not line.startswith('---'):
                change_lines += 1

        # Consider it significant if there are any actual content changes
        return change_lines > 0

    def get_trivial_count(self) -> int:
        """Get count of filtered trivial changes."""
        return self.trivial_count

    def is_significant_change(self, old_line: str, new_line: str) -> bool:
        """Check if change between two lines is significant."""
        # Remove leading/trailing whitespace for comparison
        old_stripped = old_line.strip()
        new_stripped = new_line.strip()

        # If content is the same after stripping, it's just whitespace
        if old_stripped == new_stripped:
            return False

        # If one is empty and other is whitespace, it's trivial
        if not old_stripped and not new_stripped:
            return False

        return True

    def add_custom_pattern(self, pattern: str) -> None:
        """Add custom pattern for generated files."""
        self.generated_patterns.append(re.compile(pattern))

    def get_generated_patterns(self) -> List[str]:
        """Get list of generated file patterns."""
        return self.GENERATED_FILE_PATTERNS.copy()
