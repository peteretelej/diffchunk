"""diffchunk - A tool for chunking large diff files for LLM consumption."""

__version__ = "0.1.0"
__author__ = "Peter Etelej"

from .chunker import DiffChunker
from .filters import ChangeFilter
from .parser import DiffParser

__all__ = ["DiffParser", "DiffChunker", "ChangeFilter"]
