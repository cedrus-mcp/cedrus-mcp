<h1 align="center">🌳 Cedrus MCP Server</h1>

<p align="center">
  A <strong>thinking tool</strong> for scaffolding AI reasoning.
</p>

---

Cedrus runs as a Model Context Protocol (MCP) server and gives AI agents tools and resources to <strong>externalize and structure their chain‑of‑thought reasoning</strong> as a <code>reasoning-graph</code>.

You can think of Cedrus as a text-based argument mapping tool tailored to AI agents. Cedrus helps agents to keep track of their evolving deliberation, offering tools to sketch, refine, and review complex and heterogenous argumentation.



## Why use Cedrus?

Most assistants already "think" internally, but that reasoning is:
- **Invisible** – you only see the final answer.
- **Linear** – a long paragraph, not a structured map.
- **Hard to critique** – you cannot easily see where a mistake enters.

Cedrus helps by:
- Turning chain‑of‑thought into a **graph of reasons**.
- Making it easier for AI assistants to **spot gaps, conflicts, and dangling assumptions**.
- Giving the assistant (and potentially the user) a **shared structure** to inspect, revise, and build on.

It is especially useful for:
- Debates, policy analysis, and complex decisions.
- Explanations where you want to see the **shape of the reasons**, not just the conclusion.



## Quick Start

You can run Cedrus directly from GitHub using [`uvx`](https://github.com/astral-sh/uv):

```bash
uvx git+https://github.com/logikon-ai/cedrus-mcp --http
```

This will:
- Download and run the Cedrus MCP server.
- Use **streamable-http** to talk to your MCP client.

Usually you do **not** run this by hand; instead your MCP‑aware app (editor / assistant / tool host) runs this command under the hood when it needs Cedrus.



## Using Cedrus in an MCP client

To use Cedrus as a thinking tool, your MCP‑capable client needs to know two things:

1. **What command to run**
   - Use the same command as above (without `--http`):
     ```bash
     uvx git+https://github.com/logikon-ai/cedrus-mcp
     ```

2. **That this command is an MCP server over stdio**
   - In most tools this is the default when you add a "custom MCP server".

The exact UI depends on your client. Look for options like:
- "Add MCP server"
- "Add tool server"
- "Custom MCP command"

When asked for the command, paste:

```bash
uvx git+https://github.com/logikon-ai/cedrus-mcp
```

After that, your client should be able to:
- List **Cedrus tools**.
- Call tools to add claims and arguments.
- Connect them with support / attack links.
- Ask Cedrus for **instructions** and **summaries** of the current reasoning map.

You do **not** need to know the underlying Python or MCP details to do this.



## How Cedrus shapes chain‑of‑thought

Once connected, a typical pattern looks like this:

1. The assistant starts in a **sketching** mode
   - It turns key thoughts into claims.
   - It adds quick arguments for and against.

2. As the conversation goes deeper, the assistant **elaborates**
   - It breaks big claims into smaller ones.
   - It makes relations explicit (which reasons support or attack which points).

3. At any time, you can switch into a more **critical / review** mode
   - Ask for an overview of the map.
   - Look for contradictions, missing links, or weakly supported claims.
   - Ask Cedrus to highlight where more work is needed.

All of this happens through MCP tools that your client can show as buttons, menus, or commands. You and the assistant share the same structured argument map instead of a hidden chain‑of‑thought.



## Configs

You can limit the size of the map or turn on extra checks:

```bash
CEDRUS_MAX_NODES=300 \
uvx git+https://github.com/logikon-ai/cedrus-mcp
```

These are optional and safe to ignore when you are just getting started.



## Learning from inside the tool

Cedrus is designed so that most of the detailed guidance lives **inside** the server:

- There are tools that explain what other tools do.
- There are tools that describe the current mode (sketch, elaborate, review) and suggest next steps.
- There are tools for summaries and node details, so you can explore the map without reading raw data.

Once your client can connect to Cedrus with:

```bash
uvx git+https://github.com/logikon-ai/cedrus-mcp
```

let the assistant explore the available tools and use Cedrus as a **structured thinking surface** for its chain‑of‑thought.
