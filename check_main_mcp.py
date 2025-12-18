"""Check mcp instance when server.py is __main__."""

if __name__ == "__main__":
    print("Running as __main__...")
    print(f"__name__ = {__name__}")
    
    # Import mcp from koala.server (as tools.py does)
    from koala.server import mcp as module_mcp
    print(f"mcp from koala.server module: {id(module_mcp)}")
    
    # Now check this module's mcp
    import sys
    this_module = sys.modules[__name__]
    if hasattr(this_module, 'mcp'):
        print(f"mcp in __main__: {id(this_module.mcp)}")
        print(f"Same instance? {module_mcp is this_module.mcp}")
    
    # List tools from module_mcp
    import asyncio
    tools = asyncio.run(module_mcp.list_tools())
    print(f"\nTools registered in module_mcp: {[t.name for t in tools]}")
