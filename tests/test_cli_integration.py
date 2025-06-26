"""CLI integration tests for main.py entry point."""

import subprocess
import sys
import time

import pytest


class TestCLIIntegration:
    """Test CLI entry point functionality."""

    def test_cli_help_display(self):
        """Test CLI displays help correctly."""
        result = subprocess.run(
            [sys.executable, "-m", "src.main", "--help"],
            capture_output=True,
            text=True,
            timeout=10,
        )

        assert result.returncode == 0
        assert "diffchunk MCP server" in result.stdout
        assert "Examples:" in result.stdout
        assert "MCP Client Configuration:" in result.stdout

    def test_cli_version_display(self):
        """Test CLI displays version correctly."""
        result = subprocess.run(
            [sys.executable, "-m", "src.main", "--version"],
            capture_output=True,
            text=True,
            timeout=10,
        )

        assert result.returncode == 0
        assert "diffchunk" in result.stdout

    def test_cli_invalid_arguments(self):
        """Test CLI handles invalid arguments gracefully."""
        result = subprocess.run(
            [sys.executable, "-m", "src.main", "--invalid-arg"],
            capture_output=True,
            text=True,
            timeout=10,
        )

        assert result.returncode != 0
        assert "unrecognized arguments" in result.stderr

    def test_cli_server_startup_basic(self):
        """Test CLI server can start without immediate errors."""
        # Start server in background
        process = subprocess.Popen(
            [sys.executable, "-m", "src.main"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            stdin=subprocess.PIPE,
            text=True,
        )

        try:
            # Give it a moment to start and check stderr for startup messages
            time.sleep(1)

            # The process should still be running (waiting for MCP input)
            return_code = process.poll()
            if return_code is not None:
                # Process exited, get output to understand why
                stdout, stderr = process.communicate(timeout=1)
                pytest.fail(
                    f"Server exited with code {return_code}. stderr: {stderr}, stdout: {stdout}"
                )

            # Server should be running and waiting for input
            assert process.poll() is None, (
                "Server should be running and waiting for input"
            )

        finally:
            # Clean shutdown
            process.terminate()
            try:
                process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()

    def test_cli_keyboard_interrupt_handling(self):
        """Test CLI handles KeyboardInterrupt gracefully."""
        process = subprocess.Popen(
            [sys.executable, "-m", "src.main"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            stdin=subprocess.PIPE,
            text=True,
        )

        try:
            # Give it a moment to start
            time.sleep(1)

            # Send interrupt signal
            process.send_signal(subprocess.signal.SIGINT)

            # Wait for graceful shutdown
            stdout, stderr = process.communicate(timeout=3)

            # Should exit cleanly with code 0 (KeyboardInterrupt exits with 0)
            assert process.returncode == 0
            assert "Server shutdown requested" in stderr

        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()
            pytest.fail("Server did not shutdown gracefully on KeyboardInterrupt")

    def test_cli_server_startup_messages(self):
        """Test CLI displays expected startup messages."""
        process = subprocess.Popen(
            [sys.executable, "-m", "src.main"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            stdin=subprocess.PIPE,
            text=True,
        )

        try:
            # Let it start and produce some output
            time.sleep(1)

            # Terminate and get output
            process.terminate()
            stdout, stderr = process.communicate(timeout=3)

            # Check startup messages
            assert "Starting diffchunk MCP server" in stderr
            assert "Server ready - waiting for MCP client connection" in stderr

        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()

    def test_cli_module_import_success(self):
        """Test that the main module can be imported without errors."""
        result = subprocess.run(
            [
                sys.executable,
                "-c",
                "from src.main import main; print('Import successful')",
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )

        assert result.returncode == 0
        assert "Import successful" in result.stdout
