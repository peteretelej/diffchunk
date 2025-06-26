"""Diff file parsing functionality."""

import fnmatch
import re
from typing import List, Tuple, Iterator


class DiffParser:
    """Parser for unified diff files."""

    def __init__(self):
        self.file_header_pattern = re.compile(r"^diff --git a/(.*) b/(.*)$")
        self.index_pattern = re.compile(r"^index [a-f0-9]+\.\.[a-f0-9]+")
        self.file_mode_pattern = re.compile(r"^(new|deleted) file mode")
        self.binary_pattern = re.compile(r"^Binary files .* differ$")
        self.hunk_header_pattern = re.compile(
            r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@"
        )

    def parse_diff_file(self, file_path: str) -> Iterator[Tuple[List[str], str]]:
        """Parse a diff file and yield (files, content) tuples."""
        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                lines = f.readlines()
        except (IOError, OSError) as e:
            raise ValueError(f"Cannot read diff file {file_path}: {e}")

        if not lines:
            return

        current_files: List[str] = []
        current_content: List[str] = []

        for line in lines:
            line = line.rstrip("\n\r")

            if self.file_header_pattern.match(line):
                if current_content and current_files:
                    yield current_files, "\n".join(current_content)

                match = self.file_header_pattern.match(line)
                if match:
                    file_a, file_b = match.groups()
                    current_files = [file_a] if file_a == file_b else [file_a, file_b]
                    current_content = [line]
            else:
                current_content.append(line)

        if current_content and current_files:
            yield current_files, "\n".join(current_content)

    def is_trivial_change(self, content: str) -> bool:
        """Check if change is trivial (whitespace only)."""
        lines = content.split("\n")
        meaningful_changes = []

        for line in lines:
            # Skip metadata lines
            if (
                line.startswith("diff ")
                or line.startswith("index ")
                or line.startswith("+++")
                or line.startswith("---")
                or self.hunk_header_pattern.match(line)
            ):
                continue

            # Check actual changes
            if line.startswith(("+", "-")) and not line.startswith(("+++", "---")):
                stripped = line[1:].strip()
                if stripped:  # Non-empty after removing +/- and whitespace
                    meaningful_changes.append(line)

        return len(meaningful_changes) == 0

    def is_generated_file(self, files: List[str]) -> bool:
        """Check if files are likely generated/build artifacts."""
        generated_patterns = [
            ".lock",
            ".min.js",
            ".min.css",
            ".map",
            "package-lock.json",
            "yarn.lock",
            "Pipfile.lock",
            ".pyc",
            ".pyo",
            "__pycache__",
            "node_modules/",
            "dist/",
            "build/",
            ".git/",
            ".DS_Store",
            "Thumbs.db",
        ]

        for file_path in files:
            file_lower = file_path.lower()
            for pattern in generated_patterns:
                if pattern in file_lower:
                    return True
        return False

    def should_include_file(
        self,
        files: List[str],
        include_patterns: List[str] | None = None,
        exclude_patterns: List[str] | None = None,
    ) -> bool:
        """Check if files should be included based on patterns."""

        # Check exclude patterns first
        if exclude_patterns:
            for file_path in files:
                for pattern in exclude_patterns:
                    if fnmatch.fnmatch(file_path, pattern):
                        return False

        # Check include patterns
        if include_patterns:
            for file_path in files:
                for pattern in include_patterns:
                    if fnmatch.fnmatch(file_path, pattern):
                        return True
            return False  # No matches found

        return True  # Include by default if no patterns specified

    def count_lines(self, content: str) -> int:
        """Count meaningful lines in diff content."""
        return len([line for line in content.split("\n") if line.strip()])
