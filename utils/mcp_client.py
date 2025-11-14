# utils/mcp_client.py
import asyncio
from typing import Dict, Any, List, Optional
from mcp.client.stdio import StdioServerParameters, connect as mcp_connect
from mcp.types import Tool, CallToolRequest

class MCPMux:
    def __init__(self):
        self._servers = {}
        self._tool_index = {}

    async def connect_stdio(self, name: str, command: str, args: Optional[List[str]] = None, env: Optional[Dict[str,str]] = None):
        params = StdioServerParameters(command=command, args=args or [], env=env or {})
        conn = await mcp_connect(params)
        tools: List[Tool] = (await conn.list_tools()).tools
        self._servers[name] = {"conn": conn, "tools": {t.name: t for t in tools}}
        for t in tools:
            self._tool_index[t.name] = name
        return tools

    async def call(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        if tool_name not in self._tool_index:
            raise ValueError(f"Unknown tool: {tool_name}")
        server_name = self._tool_index[tool_name]
        conn = self._servers[server_name]["conn"]
        res = await conn.call_tool(CallToolRequest(name=tool_name, arguments=arguments))
        parts = []
        for c in res.content:
            if getattr(c, "text", None): parts.append(c.text)
            elif getattr(c, "json", None) is not None: parts.append(str(c.json))
        return "\n".join(parts) if parts else "(no content)"

    async def list_all_tools(self):
        out = {}
        for name, s in self._servers.items():
            out[name] = list(s["tools"].keys())
        return out

    async def close(self):
        for s in self._servers.values():
            await s["conn"].close()
