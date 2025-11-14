# utils/mcp_client.py
import asyncio
from typing import Dict, Any, List, Optional
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

class MCPMux:
    def __init__(self):
        self._servers = {}
        self._tool_index = {}
        self._streams = {}  # Store streams to keep them alive

    async def connect_stdio(self, name: str, command: str, args: Optional[List[str]] = None, env: Optional[Dict[str,str]] = None):
        params = StdioServerParameters(command=command, args=args or [], env=env or {})

        # Use async context manager for stdio_client
        stdio = stdio_client(params)
        read, write = await stdio.__aenter__()

        # Store the context manager to keep streams alive
        self._streams[name] = stdio

        # Create session
        session = ClientSession(read, write)

        # Start session
        await session.__aenter__()

        # Initialize
        await session.initialize()

        # List tools
        tools_result = await session.list_tools()
        tools = tools_result.tools

        # Store session and tools
        self._servers[name] = {"session": session, "tools": {t.name: t for t in tools}}
        for t in tools:
            self._tool_index[t.name] = name
        return tools

    async def call(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        if tool_name not in self._tool_index:
            raise ValueError(f"Unknown tool: {tool_name}")
        server_name = self._tool_index[tool_name]
        session = self._servers[server_name]["session"]

        print(f"🔧 MCP call: {server_name}.{tool_name}({arguments})")
        res = await session.call_tool(tool_name, arguments=arguments)
        print(f"✅ MCP response type: {type(res)}, hasattr content: {hasattr(res, 'content')}")

        parts = []
        for c in res.content:
            if hasattr(c, "text") and c.text:
                parts.append(c.text)
            elif hasattr(c, "data"):
                parts.append(str(c.data))

        result = "\n".join(parts) if parts else "(no content)"
        print(f"📤 MCP result: {result[:200]}...")
        return result

    async def list_all_tools(self):
        out = {}
        for name, s in self._servers.items():
            out[name] = list(s["tools"].keys())
        return out

    async def close(self):
        for s in self._servers.values():
            await s["session"].__aexit__(None, None, None)

        for s in self._servers.values():
            await s["conn"].close()
