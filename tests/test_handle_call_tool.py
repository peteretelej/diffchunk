"""Test handle_call_tool - DEPRECATED.

These tests tested the manual handle_call_tool dispatcher from the old
DiffChunkServer class, which was replaced by FastMCP in the MCP modernization.
Phase 3 will recreate equivalent tests using FastMCP's in-memory client.

This file is scheduled for deletion (see _docs/mcp-modernization/.orchestration-deferred-actions.md).
"""

import pytest

pytestmark = pytest.mark.skip(
    reason="DiffChunkServer replaced by FastMCP; tests to be rewritten in Phase 3"
)
