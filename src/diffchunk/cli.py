"""Command-line interface for diffchunk."""

import argparse
import sys
from pathlib import Path
from typing import Optional

from .chunker import DiffChunker
from .filters import ChangeFilter
from .parser import DiffParser


def create_parser() -> argparse.ArgumentParser:
    """Create command-line argument parser."""
    parser = argparse.ArgumentParser(
        prog="diffchunk",
        description="Break large diff files into manageable chunks for LLM analysis",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  diffchunk large.diff                    # Show diff metadata
  diffchunk large.diff --part 1           # Show first chunk
  diffchunk large.diff --part 2 --skip-trivial  # Show second chunk, skip trivial changes
  diffchunk large.diff --max-lines 2000   # Use custom chunk size
        """
    )

    parser.add_argument(
        "diff_file",
        help="Path to the diff file to process"
    )

    parser.add_argument(
        "--part",
        type=int,
        metavar="N",
        help="Show specific chunk number (1-based)"
    )

    parser.add_argument(
        "--max-lines",
        type=int,
        default=5000,
        metavar="N",
        help="Maximum lines per chunk (default: 5000)"
    )

    parser.add_argument(
        "--skip-trivial",
        action="store_true",
        help="Skip trivial changes (whitespace, newlines)"
    )

    parser.add_argument(
        "--skip-generated",
        action="store_true",
        default=True,
        help="Skip generated files (default: True)"
    )

    parser.add_argument(
        "--include",
        metavar="PATTERNS",
        help="Include only files matching patterns (comma-separated, e.g., '*.py,*.js')"
    )

    parser.add_argument(
        "--exclude",
        metavar="PATTERNS",
        help="Exclude files matching patterns (comma-separated)"
    )

    parser.add_argument(
        "--no-metadata",
        action="store_true",
        help="Don't include chunk metadata in output"
    )

    parser.add_argument(
        "--stats",
        action="store_true",
        help="Show detailed statistics about chunks"
    )

    parser.add_argument(
        "--list-chunks",
        action="store_true",
        help="List all chunks with summaries"
    )

    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s 0.1.0"
    )

    return parser


def filter_by_patterns(file_changes, include_patterns: Optional[str], exclude_patterns: Optional[str]):
    """Filter file changes by include/exclude patterns."""
    if not include_patterns and not exclude_patterns:
        return file_changes

    import fnmatch

    filtered_changes = []

    for change in file_changes:
        file_path = change.new_path

        # Check exclude patterns first
        if exclude_patterns:
            excluded = False
            for pattern in exclude_patterns.split(','):
                if fnmatch.fnmatch(file_path, pattern.strip()):
                    excluded = True
                    break
            if excluded:
                continue

        # Check include patterns
        if include_patterns:
            included = False
            for pattern in include_patterns.split(','):
                if fnmatch.fnmatch(file_path, pattern.strip()):
                    included = True
                    break
            if not included:
                continue

        filtered_changes.append(change)

    return filtered_changes


def format_stats(stats, chunker_stats=None):
    """Format statistics for display."""
    lines = []
    lines.append(f"Total lines: {stats.total_lines:,}")
    lines.append(f"Files changed: {stats.files_changed}")
    lines.append(f"Additions: +{stats.additions}")
    lines.append(f"Deletions: -{stats.deletions}")

    if stats.binary_files > 0:
        lines.append(f"Binary files: {stats.binary_files}")

    if stats.trivial_changes > 0:
        lines.append(f"Trivial changes: {stats.trivial_changes} (filtered)")

    if chunker_stats:
        lines.append(f"Total chunks: {chunker_stats['total_chunks']}")
        if chunker_stats['total_chunks'] > 1:
            lines.append(f"Avg lines per chunk: {chunker_stats['avg_lines_per_chunk']}")

    return "\n".join(lines)


def format_chunk_list(chunks):
    """Format chunk list for display."""
    lines = []
    lines.append(f"Available chunks ({len(chunks)} total):")
    lines.append("")

    for chunk in chunks:
        lines.append(f"  Chunk {chunk.chunk_number}: {chunk.summary}")
        lines.append(f"    Lines: {chunk.line_count:,}, Files: {chunk.file_count}")

    return "\n".join(lines)


def main() -> int:
    """Main entry point."""
    parser = create_parser()
    args = parser.parse_args()

    # Check if diff file exists
    diff_path = Path(args.diff_file)
    if not diff_path.exists():
        print(f"Error: Diff file '{args.diff_file}' not found", file=sys.stderr)
        return 1

    try:
        # Parse the diff file
        diff_parser = DiffParser()
        file_changes = diff_parser.parse_file(str(diff_path))
        stats = diff_parser.get_stats()

        if not file_changes:
            print("No changes found in diff file")
            return 0

        # Apply file pattern filters
        file_changes = filter_by_patterns(file_changes, args.include, args.exclude)

        if not file_changes:
            print("No files match the specified patterns")
            return 0

        # Apply change filters
        change_filter = ChangeFilter(
            skip_trivial=args.skip_trivial,
            skip_generated=args.skip_generated
        )
        filtered_changes = change_filter.filter_changes(file_changes)
        stats.trivial_changes = change_filter.get_trivial_count()

        if not filtered_changes:
            print("No significant changes found after filtering")
            return 0

        # Create chunks
        chunker = DiffChunker(
            max_lines=args.max_lines,
            prefer_file_boundaries=True
        )
        chunks = chunker.chunk_changes(filtered_changes)
        chunker_stats = chunker.get_chunk_stats()

        # Handle different output modes
        if args.list_chunks:
            print(format_chunk_list(chunks))
            return 0

        if args.part is not None:
            # Show specific chunk
            chunk = chunker.get_chunk(args.part)
            if not chunk:
                print(f"Error: Chunk {args.part} not found. Available chunks: 1-{len(chunks)}", file=sys.stderr)
                return 1

            output = chunker.format_chunk(chunk, include_metadata=not args.no_metadata)
            print(output)
            return 0

        # Show metadata and statistics
        print(format_stats(stats, chunker_stats))

        if args.stats and chunker_stats:
            print("\nDetailed chunk statistics:")
            print(f"  Total chunks: {chunker_stats['total_chunks']}")
            print(f"  Total lines: {chunker_stats['total_lines']:,}")
            print(f"  Total files: {chunker_stats['total_files']}")
            print(f"  Average lines per chunk: {chunker_stats['avg_lines_per_chunk']}")
            print(f"  Max lines per chunk: {chunker_stats['max_lines_per_chunk']:,}")
            print(f"  Min lines per chunk: {chunker_stats['min_lines_per_chunk']:,}")

        if len(chunks) > 1:
            print(f"\nUse --part N to view specific chunks (1-{len(chunks)})")
            print("Use --list-chunks to see chunk summaries")

        return 0

    except FileNotFoundError:
        print(f"Error: Could not read diff file '{args.diff_file}'", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error processing diff file: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
