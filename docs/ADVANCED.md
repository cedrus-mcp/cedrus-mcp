# CEDRUS in depth

For running CEDRUS from source, embedding it in a harness, or working on it. Setting it up
in a chat app is covered in the [README](https://github.com/cedrus-mcp/cedrus-mcp/blob/main/README.md).

## Design in brief

The agent sees one text view of an argument map and eight tools that change it. The tool
list never changes, every parameter is a flat string, and the server works out everything
that can be worked out — IDs, sides, depth, placement — so the model never has to.

Version 2 is a rewrite from an empty tree and shares no code with version 1, which is
tagged [`v1-final`](https://github.com/cedrus-mcp/cedrus-mcp/tree/v1-final). The design is written up in
[docs/PLAN.md](https://github.com/cedrus-mcp/cedrus-mcp/blob/main/docs/PLAN.md), and the view it aims at in
[docs/ARGUMENT_MAP_RENDERING.md](https://github.com/cedrus-mcp/cedrus-mcp/blob/main/docs/ARGUMENT_MAP_RENDERING.md).

## Running it

From PyPI, without a checkout:

```bash
uvx cedrus-mcp
uvx cedrus-mcp --save-dir /tmp/maps          # flags pass through
uvx cedrus-mcp@2.0.0                         # pin a release where a run must be reproducible
```

`pip install cedrus-mcp` installs the same server as the `cedrus` command.

Unreleased code runs straight from GitHub; this follows the default branch, so pin a tag —
`…/cedrus-mcp@<tag>` — wherever a run has to stay reproducible:

```bash
uvx git+https://github.com/cedrus-mcp/cedrus-mcp
```

From a checkout:

```bash
uv run cedrus                                  # stdio, for an MCP client
uv run cedrus --save-file /tmp/map.json        # stdio, and keep the map on disk
uv run cedrus --http --save-dir /tmp/maps      # streamable HTTP, one file per session
```

`uv run cedrus` finds the project through the working directory, so it only works **from
the repository**. Anything that spawns the server from somewhere else — an MCP client, the
inspector — has to say where the project is:

```bash
uv run --directory /path/to/cedrus-mcp cedrus
```

| Flag | What it does |
|---|---|
| `--http` | Serve over streamable HTTP instead of stdio. |
| `--host`, `--port` | Where to bind under `--http`. Default `127.0.0.1:8000`. |
| `--save-file PATH` | Write the map to `PATH` and `PATH` with `.txt` after every change. |
| `--save-dir DIR` | The same, as `DIR/<session-id>.json` and `.txt`, for several sessions. |
| `--max-chars N` | Size limit for `show()` output. Default 24000, roughly 6k tokens. |
| `--hints` | Add one short `Hint:` line to tool results. Off by default. |

`CEDRUS_SAVE_FILE` and `CEDRUS_SAVE_DIR` do the same as the two save flags; a flag wins
over the environment.

When saving is on, `new_map()` first keeps the old map beside the live file, as
`<name>.1.json` and `<name>.1.txt`, then `.2`, and so on. The agent is not told.

To try it by hand. The inspector's **web** mode forwards everything after the command
unchanged, so the server's own flags work there:

```bash
npx @modelcontextprotocol/inspector@latest \
  uv run --directory /path/to/cedrus-mcp cedrus --save-file /tmp/m.json
```

Its **`--cli`** mode does not: it parses every `--flag` itself, so `--directory` and
`--save-file` are swallowed before the server sees them — `--directory` going missing is
what produces `error: Failed to spawn: cedrus`. Use the inspector's own `--cwd`, and pass
the save path as an environment variable:

```bash
npx @modelcontextprotocol/inspector@latest --cli \
  uv run cedrus --cwd /path/to/cedrus-mcp -e CEDRUS_SAVE_FILE=/tmp/m.json \
  --method tools/list
```

In an MCP client's config, either form works:

```json
{
  "mcpServers": {
    "cedrus": {
      "command": "uvx",
      "args": ["cedrus-mcp", "--save-dir", "/tmp/maps"]
    },
    "cedrus-local": {
      "command": "uv",
      "args": ["run", "--directory", "/path/to/cedrus-mcp", "cedrus",
               "--save-file", "/tmp/m.json"]
    }
  }
}
```

## The eight tools

| Tool | What it does |
|---|---|
| `show()` | Print the whole map. No parameters. |
| `add_claim(label, text)` | Add a claim: the statement being debated, or a principle. |
| `add_argument(target, relation, label, text)` | Add an argument that responds to something. |
| `link(source, relation, target)` | Relate two items already in the map, or change how they relate. |
| `unlink(source, target)` | Remove one relation. |
| `edit(id, label, text)` | Change a label and/or a text. |
| `delete(id, with_replies)` | Delete an item and its relations. |
| `new_map()` | Start over with an empty map, e.g. for another issue. |

`relation` is `supports`, `attacks` or `undercuts`. An undercut says the target's reasons
do not lead to its conclusion without denying that they are true, so its target must be an
argument, not a claim.

### What the server guarantees

- **IDs are permanent.** `C1`, `C2`, … for claims and `A1`, `A2`, … for arguments. A
  deleted ID is never given to a new item.
- **Every argument has at least one target**, so no argument is ever left dangling.
- **Every root is a claim.** A claim that responds to nothing is a root claim; a claim may
  also support or attack things, which is how a shared principle is modelled.
- **No cycles, no self-relations, one relation per pair.** Linking a pair twice changes the
  type rather than adding a second relation.
- **A refused call changes nothing** and says so.

### A short session

```
add_claim(label="Legalisation of soft drugs", text="Soft drugs should be legal.")
→ OK: Added C1 "Legalisation of soft drugs". It is a root claim, so nothing is above it.
  Map v1: 1 claim, 0 arguments, 0 relations.

add_argument(target="C1", relation="supports", label="Tax revenue",
             text="Excise duty on a legal market raises money.")
→ OK: Added A1 "Tax revenue" [pro]. It supports C1 "Legalisation of soft drugs" (under C1).
  Map v2: 1 claim, 1 argument, 1 relation.

add_argument(target="C1", relation="undercuts", label="Bad undercut", text="…")
→ Error executing tool add_argument: "undercuts" needs an argument as its target, but C1
  is a claim. … To give a reason against C1, use "attacks".
  Nothing was changed (map v2).
```

Input is read loosely and reported strictly: `a7`, `[A7]` and `A7 Alcohol and tobacco
analogy` all mean `A7`, `attack` means `attacks`, and an ID that does not exist produces a
message naming the nearest ones that do.

## Context pruning

`show()` always prints the entire map, and its output is written to be thrown away:

- **Each `show` result replaces the ones before it.** Keeping only the latest is safe and
  is what the server assumes. Nothing in a result refers back to an earlier one.
- **Results of the other six tools are two or three lines** and make sense on their own.
- **Every result carries the version**, as `Map v12`, and says how far the map has moved
  since the last `show()` the model saw — so a stale picture announces itself.
- **`show()` shrinks in fixed steps** when it would exceed `--max-chars`: first Part 3
  goes, then Part 2's texts are cut to first sentences, then Part 2 goes. The outline and
  the claims always survive, and every relation stays visible in the outline.

The server cannot prune a client's context, so this is a contract the host has to keep.

## How the environment reads the map

The agent has no save or export tool, because saving is not its job. Whatever runs it
reads the map in either of two ways.

**Files**, written after every successful change and replaced atomically, so a reader never
sees half a file:

- `--save-file /tmp/map.json` writes `/tmp/map.json` and `/tmp/map.txt`.
- `--save-dir /tmp/maps` writes `/tmp/maps/<session-id>.json` and `.txt`.

The `.txt` file is the full rendering with no size limit. The JSON is stable in key order:

```json
{"format": "cedrus2-map/1", "session_id": "…", "version": 15,
 "claims":    [{"id": "C1", "label": "…", "text": "…", "seq": 1}],
 "arguments": [{"id": "A1", "label": "…", "text": "…", "seq": 2}],
 "relations": [{"source": "A1", "type": "attacks", "target": "C1", "seq": 3}],
 "deleted_ids": ["A17", "A18"],
 "derived": {"roots": ["C1"], "sides": {"A1": "con"}, "unchallenged": ["A4"]}}
```

`derived` is a convenience; it is not needed to rebuild the map, and
`cedrus.export.from_json` ignores it.

**Resources**, for a harness that holds the client session: `map://current` (the full
rendering) and `map://current.json`. The SDK does not give a static resource access to the
connection, so these describe the server's one session — right for stdio. With several
HTTP sessions, use `--save-dir` and read the file for the session you want.

### One map per session

Under `--http` each MCP session gets its own map, and nothing is shared between them
except the settings. The server keeps the maps in the lifespan value, keyed by the
`mcp-session-id` header the transport has already validated; stdio has no header and
serves one session per process. `tests/test_e2e_http.py` holds that behaviour down.

Because the SDK gives a handler no signal that a session has ended, a map stays in memory
until the process stops. That suits a per-run server; a long-lived shared one would want
eviction.

## Development

```bash
uv sync
uv run pytest
uv run ruff check src tests
```

The layout follows the map from data to protocol: `model.py` holds the map and its rules,
`derive.py` computes everything not stored, `render.py` writes the view, `parse.py` and
`result.py` handle what the model types and reads, `tools.py` is the eight tools as plain
functions, and `server.py` is the only file that imports the MCP SDK.

`tests/golden/soft_drugs.txt` is the expected rendering of the example map;
[tests/golden/README.md](https://github.com/cedrus-mcp/cedrus-mcp/blob/main/tests/golden/README.md) says how it differs from the hand-written
design target and how to regenerate it.
