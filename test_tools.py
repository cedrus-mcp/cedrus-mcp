"""Test script to verify tool registration."""

import asyncio
from koala.server import mcp
from koala.tools import tools

async def main():
    tool_list = await mcp.list_tools()
    print(f"Number of tools registered: {len(tool_list)}")
    for tool in tool_list:
        print(f"  - {tool.name}")

if __name__ == "__main__":
    asyncio.run(main())
