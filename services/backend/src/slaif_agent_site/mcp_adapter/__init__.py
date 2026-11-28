"""MCP adapter: one capability-bound read-only discovery tool."""

from .app import create_app, run_mcp_process

__all__ = ["create_app", "run_mcp_process"]
