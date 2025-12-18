"""Test to check for __main__ vs module import issue."""

import sys

print("Testing __main__ issue...")
print(f"When importing koala.server, what's the module name?")

# This simulates what happens when tools.py imports
from koala.server import mcp as server_mcp
print(f"  koala.server.mcp id: {id(server_mcp)}")

# Now check if server.py thinks it has the same mcp when run as __main__
print(f"\nNow checking __main__ scenario...")

# Run server as __main__ and check mcp id
import subprocess
result = subprocess.run(
    ['uv', 'run', 'python', '-c', 
     'import sys; sys.path.insert(0, "src"); '
     'import koala.server; '
     'print(f"mcp id when imported as module: {id(koala.server.mcp)}"); '
     'exec(open("src/koala/server.py").read()); '
     'print(f"mcp id in __main__ context: {id(mcp)}")'],
    capture_output=True,
    text=True,
    cwd='/Users/ggbetz/git/koala'
)
print(result.stdout)
if result.stderr:
    print("STDERR:", result.stderr)
