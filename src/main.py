"""Main entry point for diffchunk MCP server."""

import asyncio
import sys
from .server import DiffChunkServer


def main():
    """Main entry point for the MCP server."""
    try:
        server = DiffChunkServer()
        asyncio.run(server.run())
    except KeyboardInterrupt:
        sys.exit(0)
    except Exception as e:
        print(f"Error starting diffchunk MCP server: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()