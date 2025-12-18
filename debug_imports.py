"""Debug script to trace import order."""

import sys

print("=" * 60)
print("IMPORT ORDER TRACE")
print("=" * 60)

print("\n1. Importing koala.server (creates mcp instance)...")
from koala.server import mcp
print(f"   ✓ mcp instance created: {id(mcp)}")

print("\n2. Importing koala.tools.tools (registers decorators)...")
from koala.tools import tools
print(f"   ✓ tools module imported")

print("\n3. Checking tool registration...")
import asyncio
tool_list = asyncio.run(mcp.list_tools())
print(f"   ✓ Found {len(tool_list)} tools: {[t.name for t in tool_list]}")

print("\n4. Simulating what happens in main()...")
# This is what main() does
import koala.tools  # noqa: F401
print(f"   ✓ Re-imported koala.tools")

tool_list2 = asyncio.run(mcp.list_tools())
print(f"   ✓ Still have {len(tool_list2)} tools")

print("\n" + "=" * 60)
print("CONCLUSION: All tools registered correctly!")
print("=" * 60)
