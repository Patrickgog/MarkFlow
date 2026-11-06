"""Punto de entrada del servidor MCP: `python -m interfaces.mcp`."""

from interfaces.mcp.servidor_mcp import principal

raise SystemExit(principal())
