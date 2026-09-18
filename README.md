# CEDRUS

<!-- mcp-name: io.github.cedrus-mcp/cedrus-mcp -->

**Reasoning scaffolding that supercharges your small AI.**

CEDRUS gives a local model an argument map to think in: the model lays out claims and the
reasons for and against them, and the map keeps everything in place.

- **A scaffold, not a scratchpad.** The map records which reason answers which claim, so the
  model doesn't have to hold it in its head, and a small model can work through a debate
  that would otherwise swamp it.
- **Structure is checked for the model.** IDs, sides and placement are worked out by the
  server. A move that doesn't fit is refused with an explanation, so mistakes get fixed
  instead of piling up.
- **You see the reasoning.** Every step lands in a map you can read, question and extend:
  "add an objection to A3", "what supports A7?".
- **Local and private.** Made for small models on your own machine, with maps saved as
  plain text and JSON.

## What a map looks like

```
- C1 Legalisation of Soft Drugs
  - A1 Minimize destructive activity [con] — attacks C1
  - A2 No harm, no ban [pro] — supports C1
    - A3 Law must protect [con] — attacks A2
      - A4 Soft drugs are harmful [con] — supports A3 (also attacks A2, supports A1)
  - A5 Lifestyle decision [pro] — supports C1
    - A6 Moral leadership [con] — attacks A5
  - A7 Alcohol and tobacco analogy [pro] — supports C1
    - A8 Tobacco and alcohol more dangerous [pro] — supports A7
    - A9 Major differences [con] — attacks A7
    - A10 Poor reason [con] — undercuts A7
  - A11 Listen to society [pro] — supports C1
  - A12 Argument from addiction [con] — attacks C1
    - A13 Soft drugs are addictive [con] — supports A12
    - A14 Addiction no reason to ban [pro] — undercuts A12
  - A15 Slippery slope [con] — attacks C1
    - A16 Coffee houses [pro] — attacks A15
  - A19 Tax revenue [pro] — supports C1
```

This is the outline. The full view the model reads also has every claim and argument in
full, and notes which ones nothing has challenged yet.

## Quick start

### 1. Install uv

CEDRUS is started by [uv](https://docs.astral.sh/uv/), which downloads and runs it for you.

```bash
# macOS and Linux
curl -LsSf https://astral.sh/uv/install.sh | sh
```

```powershell
# Windows
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### 2. Add CEDRUS to your app

Each setup below saves your maps to `~/cedrus-maps`, a folder in your home directory. Use
any folder you like, or leave out `--save-dir` and its path if you don't want files.

Whichever app you use, the model has to support tool calling.

#### LM Studio

In the right sidebar, open the **Program** tab and choose **Install → Edit mcp.json**. Add
CEDRUS under `mcpServers`:

```json
{
  "mcpServers": {
    "cedrus": {
      "command": "uvx",
      "args": ["cedrus-mcp", "--save-dir", "~/cedrus-maps"]
    }
  }
}
```

#### Jan

Go to **Settings → MCP Servers**, click **+**, and fill in:

| Field | Value |
|---|---|
| Server Name | `cedrus` |
| Command | `uvx` |
| Arguments | `cedrus-mcp --save-dir ~/cedrus-maps` |

For a local model, turn on tool calling in the model's settings (the edit button under
**Model Capabilities**).

#### Goose

Run `goose configure`, choose **Add Extension → Command-line Extension**, name it
`cedrus`, and give the command `uvx cedrus-mcp --save-dir ~/cedrus-maps`. In Goose
Desktop, the same is under **Extensions → Add custom extension**.

Or add it to `~/.config/goose/config.yaml` (`%APPDATA%\Block\goose\config\config.yaml` on
Windows) yourself:

```yaml
extensions:
  cedrus:
    name: cedrus
    type: stdio
    cmd: uvx
    args: [cedrus-mcp, --save-dir, ~/cedrus-maps]
    enabled: true
    timeout: 300
```

Goose can run local models through Ollama, so this is also the way to use CEDRUS with
Ollama.

#### Other MCP clients

Any client that can start a local (stdio) MCP server works: the command is `uvx`, the
arguments are `cedrus-mcp` and any options below.

## Try it

> Map the debate on whether cities should ban cars from their centres. Start with the main
> claim, then add the strongest arguments on both sides.

> Now add an objection to the weakest pro argument.

> Which arguments has nobody challenged yet? Add a reply to one of them.

Whenever you want to see the whole map, ask the model to show it.

## Saving your maps

With `--save-dir DIR`, CEDRUS writes the map after every change to `DIR/<id>.txt`, the
readable view, and `DIR/<id>.json`. Each time your app starts CEDRUS, it gets a new `<id>`,
so earlier maps are kept. `--save-file PATH` writes to one fixed file instead, and a new
session overwrites it.

When the model starts a new map, the old one is kept beside the live file as `.1`, then
`.2`, and so on.

## What the model can do

| Tool | What it does |
|---|---|
| `show` | Print the whole map. |
| `add_claim` | Add a claim: the statement being debated, or a principle. |
| `add_argument` | Add an argument for or against something already in the map. |
| `link` | Relate two items already in the map, or change how they relate. |
| `unlink` | Remove one relation. |
| `edit` | Change a label or a text. |
| `delete` | Delete an item, optionally with the arguments that respond only to it. |
| `new_map` | Start over with an empty map, for another question. |

An argument can **support** or **attack** what it responds to, or **undercut** another
argument: grant its premises, but deny that they lead to its conclusion.

## Options

| Option | What it does |
|---|---|
| `--save-dir DIR` | Save each session's map in `DIR`. Also `CEDRUS_SAVE_DIR`. |
| `--save-file PATH` | Save the map to one file, `PATH` and `PATH` with `.txt`. Also `CEDRUS_SAVE_FILE`. |
| `--max-chars N` | Size limit for the map view, default 24000 (roughly 6k tokens). Larger maps are shown shortened. |
| `--hints` | Add a short hint to each tool result. |

Running over HTTP, from a checkout, or under the MCP inspector is covered in
[docs/ADVANCED.md](https://github.com/cedrus-mcp/cedrus-mcp/blob/main/docs/ADVANCED.md).

## More

- [docs/ADVANCED.md](https://github.com/cedrus-mcp/cedrus-mcp/blob/main/docs/ADVANCED.md):
  running from source, HTTP, the file format, context pruning, development.
- [docs/PLAN.md](https://github.com/cedrus-mcp/cedrus-mcp/blob/main/docs/PLAN.md): the
  design.
- Version 1 is a separate code base, tagged
  [`v1-final`](https://github.com/cedrus-mcp/cedrus-mcp/tree/v1-final).

## Licence

GNU Affero General Public License v3.0 or later. See
[LICENSE](https://github.com/cedrus-mcp/cedrus-mcp/blob/main/LICENSE).
