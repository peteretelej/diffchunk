"""Chunk content formatting for different output modes."""

import re
from dataclasses import dataclass
from typing import List, Optional

from .models import FormatMode


@dataclass
class HunkLine:
    """A single line within a diff hunk."""

    type: str  # "context", "added", "removed"
    text: str  # Line content without +/- prefix
    old_line: Optional[int]  # Line number in old file
    new_line: Optional[int]  # Line number in new file


@dataclass
class Hunk:
    """A parsed diff hunk with line-level detail."""

    lines: List[HunkLine]
    function_context: Optional[str]  # From @@ trailing text


@dataclass
class FileSection:
    """A file's diff content split into hunks."""

    path: str
    hunks: List[Hunk]


# Regex for @@ header: @@ -old_start[,old_count] +new_start[,new_count] @@ [context]
_HUNK_HEADER_RE = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@(.*)$")


def _parse_hunk_header(line: str) -> Optional[tuple]:
    """Parse an @@ header line into (old_start, new_start, function_context).

    Returns None if the line is not a valid hunk header.
    """
    m = _HUNK_HEADER_RE.match(line)
    if not m:
        return None
    old_start = int(m.group(1))
    new_start = int(m.group(3))
    trailing = m.group(5).strip()
    func_ctx = trailing if trailing else None
    return old_start, new_start, func_ctx


def _parse_file_sections(content: str) -> List[FileSection]:
    """Split chunk content into file sections and their hunks."""
    sections: List[FileSection] = []
    # Strip trailing newline to avoid spurious empty context line at end
    lines = content.rstrip("\n").split("\n")

    current_path: Optional[str] = None
    current_hunks: List[Hunk] = []
    current_hunk_lines: List[HunkLine] = []
    current_func_ctx: Optional[str] = None
    old_line = 0
    new_line = 0
    in_hunk = False  # True after we've seen a @@ header for the current file

    def _flush_hunk():
        nonlocal current_hunk_lines, current_func_ctx, in_hunk
        if current_hunk_lines:
            current_hunks.append(
                Hunk(lines=current_hunk_lines, function_context=current_func_ctx)
            )
            current_hunk_lines = []
        current_func_ctx = None
        in_hunk = False

    def _flush_file():
        nonlocal current_path, current_hunks, in_hunk
        _flush_hunk()
        if current_path is not None and current_hunks:
            sections.append(FileSection(path=current_path, hunks=current_hunks))
        current_hunks = []
        in_hunk = False

    for line in lines:
        # Detect file boundary
        if line.startswith("diff --git "):
            _flush_file()
            # Extract b/ path
            parts = line.split(" b/", 1)
            if len(parts) == 2:
                current_path = parts[1]
            else:
                current_path = line  # fallback
            continue

        # Detect hunk header
        parsed = _parse_hunk_header(line)
        if parsed is not None:
            _flush_hunk()
            old_line, new_line, current_func_ctx = parsed[0], parsed[1], parsed[2]
            in_hunk = True
            continue

        # Skip diff metadata lines (---, +++, index, mode, etc.) before first hunk
        if current_path is not None and not in_hunk:
            # These are file-level metadata lines, skip them
            continue

        # Only process diff content lines when we're inside a hunk
        if not in_hunk or current_path is None:
            continue

        # Parse diff content lines
        if line.startswith("+"):
            text = line[1:]
            current_hunk_lines.append(
                HunkLine(type="added", text=text, old_line=None, new_line=new_line)
            )
            new_line += 1
        elif line.startswith("-"):
            text = line[1:]
            current_hunk_lines.append(
                HunkLine(type="removed", text=text, old_line=old_line, new_line=None)
            )
            old_line += 1
        elif line.startswith(" "):
            # Context line (starts with space)
            text = line[1:]
            current_hunk_lines.append(
                HunkLine(
                    type="context", text=text, old_line=old_line, new_line=new_line
                )
            )
            old_line += 1
            new_line += 1
        elif line.startswith("\\"):
            # "\ No newline at end of file" - skip
            continue

    _flush_file()
    return sections


def _build_new_hunk(hunk: Hunk) -> List[str]:
    """Build __new hunk__ lines: context + added, with new-file line numbers."""
    result = []
    for hl in hunk.lines:
        if hl.type == "removed":
            continue
        if hl.type == "added":
            result.append(f"{hl.new_line:>4} +{hl.text}")
        else:  # context
            result.append(f"{hl.new_line:>4}  {hl.text}")
    return result


def _build_old_hunk(hunk: Hunk) -> List[str]:
    """Build __old hunk__ lines: context + removed, no line numbers."""
    result = []
    for hl in hunk.lines:
        if hl.type == "added":
            continue
        if hl.type == "removed":
            result.append(f"    -{hl.text}")
        else:  # context
            result.append(f"     {hl.text}")
    return result


def _hunk_header(label: str, func_ctx: Optional[str]) -> str:
    """Build a hunk header like '__new hunk__ | func' or just '__new hunk__'."""
    if func_ctx:
        return f"{label} | {func_ctx}"
    return label


def _has_removed_lines(hunk: Hunk) -> bool:
    """Check if a hunk contains any removed lines."""
    return any(hl.type == "removed" for hl in hunk.lines)


def _has_added_or_context_lines(hunk: Hunk) -> bool:
    """Check if a hunk has added or context lines (for __new hunk__)."""
    return any(hl.type in ("added", "context") for hl in hunk.lines)


def _format_annotated(content: str, chunk_files: List[str]) -> str:
    """Format chunk content into annotated format with line numbers and hunk separation."""
    sections = _parse_file_sections(content)

    if not sections:
        # No parseable diff content, return as-is
        return content

    output_parts: List[str] = []

    for section in sections:
        output_parts.append(f"## File: '{section.path}'")

        for hunk in section.hunks:
            # __new hunk__ section (skip if no added/context lines, e.g. deleted file)
            if _has_added_or_context_lines(hunk):
                output_parts.append(_hunk_header("__new hunk__", hunk.function_context))
                output_parts.extend(_build_new_hunk(hunk))

            # __old hunk__ section (only if there are removed lines)
            if _has_removed_lines(hunk):
                output_parts.append(_hunk_header("__old hunk__", hunk.function_context))
                output_parts.extend(_build_old_hunk(hunk))

    return "\n".join(output_parts)


def format_chunk(content: str, mode: FormatMode, chunk_files: List[str]) -> str:
    """Format chunk content according to the specified mode.

    Args:
        content: Raw diff chunk content.
        mode: The format mode to apply.
        chunk_files: List of file paths in this chunk.

    Returns:
        Formatted content string.
    """
    if mode == FormatMode.RAW:
        return content
    if mode == FormatMode.ANNOTATED:
        return _format_annotated(content, chunk_files)
    if mode == FormatMode.COMPACT:
        return content  # Placeholder - implemented in Phase 3
    return content
