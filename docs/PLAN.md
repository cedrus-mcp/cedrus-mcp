# Cedrus v2: a minimal argument-mapping MCP server for small language models

## Context
Cedrus v1 (in `cedrus-mcp/src/cedrus/`) has problems that hurt small open-weight models most:
- **Mode switching changes the tool list.** When a mode changes, tools are added and removed on the one server instance that all sessions share (`tools/impl/meta.py:47-88`). The same tool name also takes different parameters in different modes.
- **The data model is heavy.** Nodes are keyed by labels the model chooses, and arguments carry premise and proposition structure.
- **Next-step suggestions are noisy.** There are up to 8 per call, they contain placeholders that small models copy literally, and some name tools the current mode does not have.
- **Undercuts are not supported.**

v2 starts over on an **empty `v2` branch** of the same repository (`cedrus-mcp/`), created with `git checkout --orphan v2` followed by removing every file. Nothing is shared between the two branches. v1 is tagged **`v1-final`**, so its files can be read with `git show v1-final:<path>` — which keeps working after v2 replaces the tree on `main`. The package keeps the name `cedrus` and the command stays `cedrus`, at version 2.0.0dev.

v2 has a small, fixed set of tools built around one text view of the map, shown in `ARGUMENT_MAP_RENDERING.md` (next to this file, in `docs/`).

Design principles:
1. **Seven tools, never changed during a session, with flat string parameters.**
2. **The server assigns IDs, and they never change.**
3. **Every root is a claim.** An argument always has a target, so the tools cannot create a dangling argument.
4. **The model never enters derived information.** Side, depth, parent and challenge status are all computed.
5. **Every result stands alone.** A tool result makes sense even after earlier results have been removed from the context.
6. **`show()` always renders the whole map.** It assumes the host drops earlier `show` results from the context (see §4).
7. **The agent never saves or exports.** The environment it runs in reads the map directly (see §5).

This document covers the tool layer, the rendering and access for the environment. Other v2 topics can be added later.

---

## 1. Data model

### Items
| Item | ID | Fields |
|---|---|---|
| Claim | `C1`, `C2`, … | `label` (one line), `text` (the statement) |
| Argument | `A1`, `A2`, … | `label` (one line), `text` (the argument written out) |
| Relation | source → target | `type` ∈ {`supports`, `attacks`, `undercuts`} |

- Either end of a relation can be a claim or an argument.
- Claims and arguments each have their own counter.
- IDs are never reused. Deleted IDs are recorded in `deleted_ids` so the view can list them.
- The server also keeps a map `version`, which increases by 1 on every successful change, and a creation sequence number for every item and relation.

### Rules the server enforces
1. **Every argument has at least one target** (claim or argument), so an argument is never a root.
2. **A claim may have targets or none.**
   - A claim with no outgoing relation is a **root claim**.
   - A claim can also support or attack other items. Example: a claim stating a principle that several arguments rely on.
3. **At most one relation per source–target pair.** A second `link` between the same pair changes the type of the existing relation.
4. **No self-links and no cycles.**
   - Together with rule 1, this means every non-empty map has at least one root, and every root is a claim.
5. **`undercuts` needs an argument as its target.** It attacks the step from an argument's reasons to its conclusion, which a claim does not have.

### Derived values (computed on every read, never stored)
- **Roots:** the root claims, in creation order.
- **Primary target:** a non-root item's oldest remaining outgoing relation. It decides where the item sits in the outline ("under X").
- **Depth:** the number of steps along primary targets up to a root.
- **Children of X:** the items whose primary target is X, ordered by creation. These are arguments, and also claims that are not roots.
- **Unchallenged:** an argument or non-root claim with no incoming relations.
- **Side (`[pro]`/`[con]`) is shown only when the map has exactly one root claim.**
  - The root claim itself is pro.
  - An outgoing `supports` relation gives the item its target's side.
  - `attacks` and `undercuts` give it the opposite side.
  - If an item's relations point to different sides, it is shown as `[mixed]`, and `show()` lists it under a warning.
  - With zero root claims, or two or more, no side tags are shown, and the header says why.

---

## 2. The tools (eight, fixed for the whole session)

### Shared input handling
- **IDs are matched loosely.** Case, brackets and a trailing label are ignored: `a7`, `[A7]` and `A7 Alcohol and tobacco analogy` all resolve to `A7`.
  - For an unknown ID, the error names the closest existing IDs, matched on ID and on label (rapidfuzz).
- **Relation names are matched loosely.** `support`/`supports`, `attack`/`attacks` and `undercut`/`undercuts` are accepted in any case. Any other value gets an error that lists the three valid names.
- **Labels:** one line, 1–80 characters.
  - Longer labels are cut, and the result warns about it.
  - A label that another item already uses produces a warning, not an error.
- **Text:** 1–3000 characters, and must not be empty.

### Tool descriptions (shown to the model as written)

**`show()`**
> Show the whole argument map: its claims, its arguments and all relations. Call this whenever you need to see the current map. Its output replaces any earlier `show` output.

**`add_claim(label, text)`**
> Add a claim: the statement being debated, or a general principle that arguments can rely on. Returns its ID (C1, C2, …). Add a claim first. To make a claim support or attack something, use `link` afterwards.

**`add_argument(target, relation, label, text)`**
> Add a new argument that responds to an existing claim or argument.
> - `target`: the ID the argument responds to, e.g. "C1" or "A7".
> - `relation`: one of the following:
>   - `supports`: the argument gives a reason for the target.
>   - `attacks`: the argument gives a reason against the target.
>   - `undercuts`: the argument says the target's reasons do not lead to its conclusion. The target must be an argument.
> - `label`: a short title of a few words.
> - `text`: the argument written out in full.
>
> Returns the new ID (A1, A2, …).

**`link(source, relation, target)`**
> Add a relation from an existing claim or argument to another existing claim or argument, for items that respond to more than one item or for a claim that supports or attacks something. If the two are already related, this changes the relation type.

**`unlink(source, target)`**
> Remove the relation from source to target. An argument must keep at least one target, so its last relation cannot be removed. A claim can lose all its relations. To move an argument, link it to the new target first, then unlink the old one.

**`edit(id, label="", text="")`**
> Change the label and/or text of a claim or argument. Leave a field empty to keep it. The ID and the relations stay the same.

**`delete(id, with_replies=false)`**
> Delete a claim or argument together with its relations. The ID is never reused. If some arguments respond only to this item, deletion is refused and they are listed, unless `with_replies=true`, in which case they are deleted too.

**`new_map()`**
> Start a new, empty argument map, e.g. to map a different issue. Only call this when you are done with the current map: it is cleared. IDs start again at C1 and A1.

With saving on, the server first writes the old map to the first free `<name>.<n>.json`/`.txt` beside the live file. The result never mentions this.

### Rules for results (`result.py`)
Every result is plain text. On error, the result has `isError=true` and nothing in the map is changed.

**Successful result:**
```
OK: Added A20 "Tax evasion" [con]. It attacks A19 "Tax revenue" (under A19).
Map v15: 1 root claim, 18 arguments, 20 relations. The map changed 3 times since your last show().
```

**Error result** (the `Error executing tool …` prefix is the SDK's, see §9):
```
Error executing tool add_argument: "A21" does not exist. Did you mean A2 "No harm, no ban" or A12 "Argument from addiction"?
Nothing was changed (map v15).
```

- **A success starts with `OK:`; a refusal is an `is_error` result** and carries the SDK's own prefix instead of one of ours. The first line names the item's ID and label, and its side if one is shown.
- **The second line gives the version, the counts and a staleness note.** The note appears only when the map changed since the last `show()`.
- **Error messages never contain made-up placeholders.**
  - An error may include a corrected call, but only one built from the model's own arguments and IDs that actually exist, e.g. `add_argument(target="A7", relation="undercuts", …)`.
  - The claim-as-target case is an exception to repeating the model's arguments: an `undercuts` aimed at a claim cannot be fixed by changing the relation alone, so the error explains this and suggests `attacks`.
- **An optional third line gives at most one `Hint:`.**
  - Hints are off by default and switched on with the server flag `--hints`.
  - Hints are built from the real map, e.g. "A20 has no replies yet."
  - Hints never name a tool that does not exist.

### Server instructions (MCP `instructions` field, about 5 lines)
> Build an argument map step by step. Order of work:
> 1. Add the central claim with `add_claim`.
> 2. Respond to it with `add_argument`, choosing `supports`, `attacks` or `undercuts`.
> 3. Respond to existing claims and arguments the same way.
> 4. Call `show()` to see the whole map.
>
> IDs never change, so you can always refer to them. Fix mistakes with `edit`, `link`/`unlink` or `delete`.

---

## 3. What `show()` prints

It follows `ARGUMENT_MAP_RENDERING.md` exactly, and everything in it is generated.

1. **Header**
   - The title comes from the root claim's label (one root claim) or reads "N root claims" (several).
   - It includes `Map vN` and the counts.
   - It explains the three relation types and the "X → R Y" / "Y ← R X" arrows.
   - It includes the note on what `[pro]`/`[con]` means, or, when there isn't exactly one root claim, a line saying why no side tags appear.
   - It explains the ordering and IDs, and what "under X" means.
2. **Generated notes**
   - Items with more than one target, e.g. "A4 has more than one target: it also attacks A2 and supports A1."
   - Items with a `[mixed]` side, if any.
   - The list of unchallenged items.
   - The list of deleted IDs.
3. **`## Outline`**
   - Each root claim, then a depth-first walk over children in creation order.
   - Line format: `- A4 Label [con] — supports A3 (also attacks A2, supports A1)`.
   - A non-root claim appears under its primary target like any other item.
4. **`## Part 1: Claims`**: the ID, label and full text of every claim, including non-root claims.
5. **`## Part 2: Arguments (full text)`**: in outline order.
6. **`## Part 3: Dialectical structure`**
   - One block per item: `ID Label [side] | root claim / depth N | under X | unchallenged`.
   - Below it, the outgoing `→` lines, then the incoming `←` lines.
7. **Empty map:** a single line: "The map is empty. Start with add_claim(label, text)."

### Size limit
The server flag `--max-chars` sets the limit; the default is 24000 (about 6k tokens). If the output is too long, the server shortens it in steps and stops at the first one that fits:
1. **Drop Part 3.** The header says: "Part 3 omitted (map too large); relations are shown in the outline."
2. **Shorten each text in Part 2** to its first sentence, at most 160 characters, and add "…".
3. **Drop Part 2.** Only the outline and the claims remain.

The call stays `show()` with no parameters.

---

## 4. Pruning and staleness
- **The server remembers which version the last `show()` displayed.** When the map has changed since then, every other tool's result says how many times (see §2).
- **Documentation for people who run agents** (README section "Context pruning"):
  - Each `show` result replaces the ones before it, so it is safe to keep only the latest.
  - Results of edit tools are short and make sense on their own.

---

## 5. How the environment reads the map
The agent has no save or export tool. Whatever runs it (an eval harness, an app) gets the map in either of two ways. Neither one adds a tool.

1. **Files written after every change**
   - `--save-file PATH` (for stdio, one session): after each successful change the server writes `PATH` (JSON) and `PATH` with `.txt` in place of `.json` (the `show()` text without the size limit).
   - `--save-dir DIR` (for HTTP, several sessions): the same two files as `DIR/<session-id>.json` and `.txt`. The session ID is a UUID created when the session starts and is also stored inside the JSON.
   - Both settings can also come from environment variables: `CEDRUS_SAVE_FILE` and `CEDRUS_SAVE_DIR`.
   - Files are replaced atomically (write to a temporary file, then rename), so a reader never sees half a file.
2. **MCP resources**, for environments that hold the client session:
   - `map://current` returns the full rendering as text, without the size limit.
   - `map://current.json` returns the JSON.

JSON format (`export.py`, with a stable key order):
```json
{"format": "cedrus2-map/1", "session_id": "...", "version": 15,
 "claims":    [{"id": "C1", "label": "...", "text": "...", "seq": 1}],
 "arguments": [{"id": "A1", "label": "...", "text": "...", "seq": 2}],
 "relations": [{"source": "A1", "type": "attacks", "target": "C1", "seq": 3}],
 "deleted_ids": ["A17", "A18"],
 "derived": {"roots": ["C1"], "sides": {"A1": "con"}, "unchallenged": ["A4"]}}
```
- The `derived` block is included for convenience only and is not needed to rebuild the map.
- A `from_json` function also exists, so tests and harnesses can rebuild a map and compare maps. There is no tool for it.

---

## 6. Layout of the `v2` branch (package `cedrus`, version 2.0.0dev)
```
cedrus-mcp/               # same repository, branch v2, starting from an empty tree
  pyproject.toml          # name=cedrus, version 2.0.0dev; script cedrus=cedrus.__main__:main
                          # deps: mcp>=2.2 (official SDK, MCPServer), pydantic, rapidfuzz
                          # dev: pytest, pytest-asyncio (asyncio_mode=auto), ruff, mypy
  README.md  .gitignore  docs/PLAN.md   # this plan, copied onto the branch
  docs/ARGUMENT_MAP_RENDERING.md        # the hand-written design target for the view
  src/cedrus/
    __main__.py           # stdio by default; --http, --hints, --max-chars, --save-file, --save-dir
    server.py             # MCPServer; the lifespan holds one Session (map, last_shown) per MCP
                          # session, keyed by the mcp-session-id header (see §9);
                          # registers 8 tools + 2 resources; calls the file writer after each change
    model.py              # ArgMap: items, relations, counters, deleted_ids, version; changes + rule checks; raises MapError(msg)
    derive.py             # roots, primary target, depth, children, sides, unchallenged, multi-target notes
    render.py             # show() text + size-limit steps
    export.py             # to_json / from_json; atomic file writer
    parse.py              # loose matching of IDs and relation names; "did you mean" (rapidfuzz)
    result.py             # OK/ERROR/status/hint lines → CallToolResult
    tools.py              # 7 thin wrappers: parse → model → result
  tests/
    fixtures/soft_drugs.py         # builds the example map with tool calls (creates and deletes A17, A18)
    golden/soft_drugs.txt          # expected show() output
    golden/README.md               # how it differs from ARGUMENT_MAP_RENDERING.md, and how to regenerate it
    test_model.py  test_derive.py  test_render.py  test_export.py
    test_parse.py  test_tools.py   test_main.py    test_e2e_stdio.py
```

### Patterns to look up in v1 (read with `git show v1-final:<path>`, then write fresh code)
- **One map per session:** v1 used the lifespan (`src/cedrus/server.py:27`). That no longer holds in SDK v2 — see §9. v2 has no mode switching, so the shared-tool-list bug cannot occur.
- **Tool tests with a mocked context:** `tests/test_tools/test_add_tool.py:23-50`.
- **Real end-to-end test over stdio:** `tests/integration/test_true_e2e.py` (`stdio_client` + `ClientSession`).
- **"Did you mean" with rapidfuzz:** `most_similar_labels` in `src/cedrus/backend/graph/argument_map.py`.
- **Depth-first walk that tracks visited nodes:** `_render_node_recursive` in `src/cedrus/backend/graph/rendering.py:37`. v2 walks primary-target children instead of edge types.
- **Project settings worth carrying over:** v1's `pyproject.toml` (hatchling, Python ≥3.11, pytest with `asyncio_mode = "auto"`), minus its dependencies on networkx, matplotlib and graphviz. The AGPL `LICENSE` comes over unchanged.

networkx is not needed. The graph is small, and cycle checks are a plain depth-first search.

---

## 7. Build order
0. Create the branch: `git checkout --orphan v2`, remove every file from the index and the working tree, then add `pyproject.toml`, `.gitignore` and `docs/PLAN.md`. (The `uv.lock` change on `main` stays untouched.) Nothing is committed until you ask.
1. `model.py` with the rules in §1, and `test_model.py` covering every rule and every refusal.
2. `derive.py`, including side derivation for one root claim, several root claims, non-root claims and `[mixed]`.
3. `render.py`, with the soft-drugs golden test and the size-limit steps.
4. `export.py`, with a JSON round trip and atomic writes.
5. `parse.py` and `result.py`: loose matching, "did you mean" and the message formats.
6. `tools.py` and `server.py` with the 8 tools, 2 resources and the file writer, plus `test_tools.py` (mocked context).
7. `__main__.py`, `test_e2e_stdio.py`, and a README covering the tools, a sample session, context pruning and access for the environment.

---

## 8. How to check the work
- `uv run pytest` passes, including these tests:
  - **Golden test:** the fixture builds the soft-drugs map with real tool calls, deletes A17 and A18, and `show()` then matches `tests/golden/soft_drugs.txt`.
  - **Non-root claim test:** add C2 as a principle and link it with `supports` to A5 and A11.
    - C2 appears under A5 in the outline.
    - The header still counts 1 root claim, and side tags stay on.
    - C2 gets a side.
  - **Refusal tests:**
    - an `undercuts` aimed at a claim;
    - an unlink that would leave an argument with no target;
    - a relation that would create a cycle;
    - a delete that would leave replies with no target;
    - an unknown ID, which must produce a "did you mean" answer.
  - **Side tests:**
    - side tags appear with one root claim and disappear with two;
    - an item whose relations point to both sides shows as `[mixed]`.
  - **Size-limit test:** a map built to be too large goes through the shortening steps in order.
  - **Export tests:** a JSON round trip gives back an equal map, and `--save-file` has written the latest version after each change.
- **End-to-end test over stdio:**
  - The tool list has 8 tools and does not change.
  - Reading `map://current.json` returns the same map as the saved file.
- **Manual check:** run `npx @modelcontextprotocol/inspector uv run cedrus --save-file /tmp/m.json`, build a 3-argument map, and watch the file update after each change.

---

## 9. Decisions taken while building this

Four things in §1–§8 did not survive contact with the SDK or the rendering. They are
recorded here rather than edited away, so the reasoning stays visible.

### The SDK is v2, and `FastMCP` is gone
`mcp` resolves to 2.x, where `FastMCP` was renamed `MCPServer` and the 1.x import raises on
sight. v2 builds on `MCPServer` rather than pinning `mcp<2`, because a rewrite should not
start on a superseded API. The decorators, the lifespan and `run(transport=…)` all carry
over; two things do not.

### The lifespan holds a registry of maps, keyed by the MCP session id
In SDK v2 the lifespan is entered **once for the whole server** and shared by every HTTP
session, so it cannot hold the map. It holds the registry instead, and a handler creates
its own session's map on first use — what the v2 release notes mean by "anything that
acquired a per-connection resource there belongs in the handler body now".

The key is the MCP session id, taken from the `mcp-session-id` request header via the
documented `ctx.headers`. The transport has already matched that header against a live
session before a handler sees it, so it cannot be spoofed into another session's map.
stdio carries no headers and serves one session per process, so it uses a per-process
uuid; a request that is neither (stateless HTTP) is refused, because there is no session
for a map to belong to.

Two alternatives were measured and rejected:
- **`Connection.state`** is per-connection scratch space and would be the natural home,
  but the SDK exposes no connection on a handler's `Context`; reaching it means
  `ctx.request_context.session._connection`, a private attribute.
- **`ctx.session`** is not per-session at all. It is a **fresh `ServerSession` object per
  request** — verified by probe — so it cannot key anything.

The cost of the documented route is that nothing tells a handler a session has ended, so
the registry grows until the process stops. `Connection.state` would have been freed with
the connection. For an agent run on stdio, or a per-run HTTP server, a `Session` is a few
kilobytes and the process is short-lived; a long-running shared HTTP server would want
eviction.

This also limits the resources of §5. A **static** resource gets no `Context` at all
(`Context injection for static resources is not supported`), so `map://current` and
`map://current.json` describe the server's single session. That is right for stdio, which
is what they are for; with several HTTP sessions they refuse, and `--save-dir` is the way in.

### Errors carry the SDK's marker, not ours
Every `ToolError` reaches the client as `Error executing tool <name>: <message>` with
`is_error=true`. The prefix is unconditional, so the planned `ERROR:` would have made two
markers on one line. Refusals therefore add no marker of their own: the SDK's prefix names
the failure *and* the tool that failed, and the second line still reads
`Nothing was changed (map vN).`

### The view says `[con]`, not `#con`
`ARGUMENT_MAP_RENDERING.md` uses `#pro`/`#con`. The renderer uses `[pro]`/`[con]`, because
`#` opens a heading in Markdown and `[mixed]` has to fit the same shape. `central claim`
became `root claim` for the same kind of reason: a map may have several roots, and then
none of them is central. `tests/golden/README.md` lists every difference between the
generated file and the hand-written one.
