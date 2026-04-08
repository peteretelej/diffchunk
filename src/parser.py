"""Diff file parsing functionality."""

import fnmatch
import logging
import re
from typing import List, Tuple, Iterator

logger = logging.getLogger("diffchunk")


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
        lines = self._read_diff_file(file_path)

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

    def _read_diff_file(self, file_path: str) -> List[str]:
        """Read diff file with encoding detection."""
        import chardet

        # Detect encoding from sample
        with open(file_path, "rb") as f:
            sample = f.read(8192)
        result = chardet.detect(sample)

        # Use detected encoding if confident, otherwise UTF-8
        encoding = (
            result.get("encoding") if result.get("confidence", 0) > 0.7 else "utf-8"
        )
        logger.debug(
            "Detected encoding %s (confidence %.1f) for %s",
            encoding,
            result.get("confidence", 0),
            file_path,
        )

        try:
            with open(file_path, "r", encoding=encoding) as f:
                content = f.read()
        except UnicodeDecodeError:
            # Fallback with error replacement
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()

        # Strip BOM if present
        if content.startswith("\ufeff"):
            content = content[1:]

        return content.splitlines(keepends=True)

    @staticmethod
    def reduce_context(content: str, context_lines: int) -> str:
        """Reduce context lines in a diff file section to the specified count.

        Args:
            content: Raw diff content for a single file section (including diff --git header).
            context_lines: Number of context lines to keep around each change.

        Returns:
            Modified diff content with reduced context.
        """
        lines = content.rstrip("\n").split("\n")

        hunk_header_re = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@(.*)$")

        # Separate file header from hunks
        header_lines: list[str] = []
        hunks: list[tuple[str, list[str]]] = []  # (hunk_header, body_lines)

        in_hunk = False
        current_hunk_header = ""
        current_hunk_body: list[str] = []

        for line in lines:
            if hunk_header_re.match(line):
                # Save previous hunk if any
                if in_hunk:
                    hunks.append((current_hunk_header, current_hunk_body))
                in_hunk = True
                current_hunk_header = line
                current_hunk_body = []
            elif in_hunk:
                current_hunk_body.append(line)
            else:
                header_lines.append(line)

        # Save last hunk
        if in_hunk:
            hunks.append((current_hunk_header, current_hunk_body))

        if not hunks:
            return content

        # Process each hunk: classify lines and mark which to keep
        # First, collect all classified lines across all hunks for potential merging
        classified_hunks: list[
            tuple[str, list[tuple[str, str]]]
        ] = []  # (header, [(type, text)])

        for hunk_header, body in hunks:
            classified: list[tuple[str, str]] = []
            for line in body:
                if line.startswith("+") and not line.startswith("+++"):
                    classified.append(("add", line))
                elif line.startswith("-") and not line.startswith("---"):
                    classified.append(("remove", line))
                elif line == "\\ No newline at end of file":
                    classified.append(("meta", line))
                else:
                    classified.append(("context", line))
            classified_hunks.append((hunk_header, classified))

        # Process each hunk: mark context lines within distance of changes
        reduced_hunks: list[tuple[str, list[tuple[str, str, bool]]]] = []

        for hunk_header, classified in classified_hunks:
            # Find indices of change lines (add/remove)
            change_indices: set[int] = set()
            for i, (line_type, _) in enumerate(classified):
                if line_type in ("add", "remove"):
                    change_indices.add(i)

            # Mark context lines within context_lines distance of any change
            keep: set[int] = set()
            for idx in change_indices:
                keep.add(idx)
                for d in range(1, context_lines + 1):
                    if idx - d >= 0:
                        keep.add(idx - d)
                    if idx + d < len(classified):
                        keep.add(idx + d)

            # Also keep meta lines adjacent to kept lines
            for i, (line_type, _) in enumerate(classified):
                if line_type == "meta":
                    # Keep if adjacent to a kept line
                    if (i - 1 in keep) or (i + 1 in keep):
                        keep.add(i)

            marked = [
                (line_type, text, i in keep)
                for i, (line_type, text) in enumerate(classified)
            ]
            reduced_hunks.append((hunk_header, marked))

        # Build output hunks with only kept lines, recalculating headers
        output_hunks: list[str] = []

        for hunk_header, marked in reduced_hunks:
            m = hunk_header_re.match(hunk_header)
            if not m:
                continue
            orig_old_start = int(m.group(1))
            orig_new_start = int(m.group(3))
            trailing_context = m.group(5)  # e.g. " def authenticate"

            # Filter to kept lines only
            kept_lines = [(lt, text) for lt, text, keep_flag in marked if keep_flag]

            if not kept_lines:
                continue

            # Walk all marked lines, track old/new position,
            # for kept lines record their position.
            positions: list[
                tuple[str, str, int, int]
            ] = []  # (type, text, old_pos, new_pos)

            old_pos = orig_old_start
            new_pos = orig_new_start

            for line_type, text, keep_flag in marked:
                if keep_flag:
                    positions.append((line_type, text, old_pos, new_pos))
                # Advance positions
                if line_type == "context":
                    old_pos += 1
                    new_pos += 1
                elif line_type == "add":
                    new_pos += 1
                elif line_type == "remove":
                    old_pos += 1
                # meta lines don't advance positions

            if not positions:
                continue

            # Split positions into contiguous sub-hunks.
            # Two consecutive kept lines are "contiguous" if there are no gaps
            # (no dropped context lines between them).
            # We detect gaps by checking if position jumps.
            sub_hunks: list[list[tuple[str, str, int, int]]] = []
            current_sub: list[tuple[str, str, int, int]] = [positions[0]]

            for i in range(1, len(positions)):
                prev_type, _, prev_old, prev_new = positions[i - 1]
                curr_type, _, curr_old, curr_new = positions[i]

                # Expected next positions
                exp_old = prev_old + (1 if prev_type in ("context", "remove") else 0)
                exp_new = prev_new + (1 if prev_type in ("context", "add") else 0)

                if curr_old == exp_old and curr_new == exp_new:
                    current_sub.append(positions[i])
                else:
                    sub_hunks.append(current_sub)
                    current_sub = [positions[i]]

            sub_hunks.append(current_sub)

            # Generate hunk output for each sub-hunk
            for sub in sub_hunks:
                sub_old_start = sub[0][2]
                sub_new_start = sub[0][3]

                sub_old_count = sum(
                    1 for lt, _, _, _ in sub if lt in ("context", "remove")
                )
                sub_new_count = sum(
                    1 for lt, _, _, _ in sub if lt in ("context", "add")
                )

                # Build header - use trailing context from the original header
                # only for the first sub-hunk
                ctx_text = trailing_context if sub is sub_hunks[0] else ""
                new_header = f"@@ -{sub_old_start},{sub_old_count} +{sub_new_start},{sub_new_count} @@{ctx_text}"

                hunk_lines = [new_header]
                for lt, text, _, _ in sub:
                    if lt != "meta":
                        hunk_lines.append(text)
                    else:
                        hunk_lines.append(text)
                output_hunks.append("\n".join(hunk_lines))

        if not output_hunks:
            # No hunks survived - return just the header
            return "\n".join(header_lines)

        return "\n".join(header_lines) + "\n" + "\n".join(output_hunks)

    def count_lines(self, content: str) -> int:
        """Count meaningful lines in diff content."""
        return len([line for line in content.split("\n") if line.strip()])
