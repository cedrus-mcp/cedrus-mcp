# SWE-agent evaluations

This folder is reserved for experiments and notes around using the full SWE-agent framework as an evaluation harness.

## SWE-agent + SWE-bench evaluation pipeline (local harness)

Based on the upstream SWE-agent and SWE-bench documentation, a typical local evaluation loop looks like this:

1. **Run SWE-agent in batch mode on SWE-bench**
   - Use `sweagent run-batch` with the built-in SWE-bench instance source:
     - `--instances.type swe_bench`
     - `--instances.subset lite|verified|full|multimodal|...`
     - `--instances.split dev|test`
   - Configure the model and tools via a YAML config, e.g. `config/default.yaml`:
     - `agent.model.name` points to the underlying LLM (e.g. GPT-4o, Claude Sonnet, or an open-weights model served via vLLM).
     - `agent.bundles` lists tool bundles (bash, editors, file viewers, etc.).
   - Example (from docs, with SWE-bench Lite):

     ```bash
     sweagent run-batch \
       --config config/default.yaml \
       --agent.model.name gpt-4o \
       --agent.model.per_instance_cost_limit 2.00 \
       --instances.type swe_bench \
       --instances.subset lite \
       --instances.split dev \
       --instances.slice :3 \
       --instances.shuffle=True
     ```

   - Results: for each instance, SWE-agent writes a trajectory, and a global `preds.json` mapping `instance_id` → prediction (patch).

2. **Convert SWE-agent predictions to SWE-bench format**
   - SWE-agent's `preds.json` is a JSON object keyed by `instance_id`.
   - SWE-bench's local harness expects a list or JSONL of prediction objects, each with at least:
     - `instance_id`
     - `model_name_or_path`
     - `model_patch`
   - A minimal adapter (from the SWE-agent docs) converts `preds.json` into JSONL:

     ```python
     from pathlib import Path
     import json

     preds = json.loads(Path("preds.json").read_text())
     data = [{"instance_id": key, **value} for key, value in preds.items()]
     jsonl = [json.dumps(d) for d in data]
     Path("all_preds.jsonl").write_text("\n".join(jsonl))
     ```

3. **Run local SWE-bench harness**
   - Use the SWE-bench Python harness to evaluate predictions in Docker:

     ```bash
     python -m swebench.harness.run_evaluation \
       --dataset_name princeton-nlp/SWE-bench_Lite \
       --predictions_path path/to/all_preds.jsonl \
       --max_workers 8 \
       --run_id my_run_id
     ```

   - The harness sets up the appropriate SWE-bench container per instance, applies patches, runs tests, and reports resolution metrics.

## Why SWE-agent is interesting for cedrus MCP

SWE-agent is a good conceptual fit if we want to study "LM + tools" on SWE-bench:

- **Tool bundles**: tools are defined as bundles with `config.yaml` + `bin/` scripts. Each tool has:
  - a `signature` (how the LM should call it),
  - a `docstring` (when to use it), and
  - typed `arguments`.
- **State hooks**: a special `state_command` can run after each tool call to expose state (like current file, working directory) back into the prompt.
- **Batch mode**: `sweagent run-batch` already knows how to:
  - sample SWE-bench instances from Hugging Face (`--instances.type swe_bench`),
  - run many instances in parallel, and
  - write a SWE-bench-compatible `preds.json`.

For cedrus MCP, a natural idea would be:

- Implement a dedicated `tools/cedrus_reasoning/` bundle whose `bin/` scripts talk to the cedrus MCP server (over stdio or a local socket) and wrap operations like:
  - `cedrus_add_claim <label> <proposition>`
  - `cedrus_add_argument <label> <gist>`
  - `cedrus_connect <source> <target> <support|attack>`
  - `cedrus_show_graph`
- Add that bundle to an agent config and adjust templates so SWE-agent's LM knows how and when to use these commands.
- Compare with vs. without this bundle on SWE-bench (same model, same run config otherwise), evaluated via the local SWE-bench harness.

## Limitations for testing cedrus MCP

At the same time, some limitations make SWE-agent less ideal as the *primary* framework for testing the cedrus MCP server itself:

- **Tool protocol mismatch**
  - SWE-agent tools are shell executables with CLI signatures; they are *not* OpenAI-style function calls or MCP tools.
  - Cedrus MCP is designed to be used by an MCP client that speaks JSON-RPC over stdio; in SWE-agent, we would embed such a client *inside* tool scripts.
  - This tests cedrus as a library behind shell tools, not as a first-class MCP server integrated at the inference-provider level.

- **Agent vs. provider layering**
  - SWE-agent expects a plain chat model (no tool-calls), and performs its own tool parsing and execution.
  - For many MCP use-cases we care about, the more natural architecture is:
    - "client / provider" handles tool-calls and MCP,
    - the upstream agent (SWE-agent, mini-SWE-agent, copilot) just sees a smarter text-only model.
  - Using SWE-agent tools for cedrus therefore couples cedrus more tightly to SWE-agent's internal tool system than we might want for general benchmarking.

- **Complexity vs. minimality**
  - SWE-agent is powerful but comparatively heavy: many tools, sophisticated templates, and a rich configuration space.
  - For isolating cedrus MCP behaviour, a simpler custom harness (or a provider-centric MCP client) may make it easier to:
    - control prompts and tool exposure,
    - inspect and log MCP interactions directly, and
    - avoid confounding factors from SWE-agent's own tool logic.

## Takeaways

- SWE-agent provides a strong, configurable baseline for SWE-bench evaluations with tools, and could be used to test "cedrus as a SWE-agent tool" via a custom tool bundle.
- However, for testing cedrus MCP as a general-purpose MCP server (plugged into arbitrary clients), it may be more appropriate to:
  - place cedrus behind an inference provider or a custom evaluation harness, and
  - use SWE-agent/SWE-bench mostly as *one* downstream benchmark, rather than the core MCP integration surface.
