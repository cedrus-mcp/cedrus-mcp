# Cedrus + OpenHands Evaluation Harness

This document summarizes how we plan to use OpenHands’ evaluation infrastructure (specifically the `OpenHands/benchmarks` repo) to evaluate the cedrus MCP server and related “thinking tools” on SWE-bench and GAIA.

The goal is to have a reproducible pipeline where we can toggle cedrus **on/off** with minimal configuration changes and compare performance and behaviour across benchmarks.

---

## 1. Upstream Baseline: OpenHands/benchmarks

We treat [`OpenHands/benchmarks`](https://github.com/OpenHands/benchmarks) as the upstream baseline.

Two benchmark families are especially relevant:

- **SWE-bench**: `benchmarks/swebench`
  - `run_infer.py` / `swebench-infer`:
    - Uses the OpenHands Software Agent SDK.
    - For each SWE-bench instance:
      - Prepares a containerized workspace (Docker or remote runtime).
      - Creates an `Agent` with `get_default_tools(...)` and a configured `LLM`.
      - Runs a `Conversation` over the repo snapshot.
      - Commits changes and extracts a `git diff` (`git_patch`).
      - Writes one JSONL record per instance, including:
        - `instance_id`
        - `test_result["git_patch"]`
        - `history` (full trajectory)
        - `metrics`
  - `eval_infer.py` / `swebench-eval`:
    - Converts OpenHands `output.jsonl` to standard SWE-bench prediction format:
      - `instance_id`
      - `model_patch`
      - `model_name_or_path`
    - Invokes the **official SWE-bench harness**:
      - `python -m swebench.harness.run_evaluation`
    - Produces standard SWE-bench metrics and a cost report.

- **GAIA**: `benchmarks/gaia`
  - `run_infer.py` / `gaia-infer`:
    - Uses the same `Evaluation` orchestrator pattern.
    - Creates an `Agent` with:
      - `get_default_tools(enable_browser=True)`
      - A configured `LLM`
      - **MCP integration via `mcp_config`**
        - e.g. Tavily’s search MCP server:
          ```python
          agent = Agent(
              llm=self.metadata.llm,
              tools=tools,
              system_prompt_kwargs={"cli_mode": True},
              mcp_config={
                  "mcpServers": {
                      "fetch": {"command": "uvx", "args": ["mcp-server-fetch"]},
                      "tavily": {
                          "command": "npx",
                          "args": ["-y", "tavily-mcp@0.2.1"],
                          "env": {"TAVILY_API_KEY": tavily_api_key},
                      },
                  }
              },
          )
          ```
    - Scores each instance according to the GAIA benchmark and writes JSONL outputs including:
      - `instance_id`
      - `test_result` (score, model_answer, ground_truth)
      - full `history` and `metrics`.

**Key takeaway:**  
- `benchmarks/swebench` already provides:
  - a robust SWE-bench runner,
  - official harness integration,
  - and full trajectory logging.
- `benchmarks/gaia` already demonstrates **MCP integration in an evaluation pipeline** through `mcp_config` on the SDK `Agent`.

These two together are an ideal base for cedrus.

---

## 2. Cedrus Integration Modes

We care about two complementary integration styles, matching our high-level requirements:

1. **Provider-centric integration**
   - Cedrus is folded into the **LLM provider** itself.
   - We run **our own OpenAI-compatible endpoint** that:
     - Orchestrates cedrus MCP calls internally.
     - Exposes a standard chat/completions API.
   - From OpenHands’ point of view:
     - It just sees a normal `LLM` with `model`, `base_url`, `api_key`.

2. **Agent-centric MCP integration**
   - Cedrus is exposed as an MCP server.
   - The OpenHands **Agent** connects to cedrus via `mcp_config` and sees its tools (e.g. `reasoning-graph_*`) explicitly.
   - This is the pattern already used in `benchmarks/gaia` with Tavily MCP.

We intend to support **both** for SWE-bench and GAIA, but with different tradeoffs:

- Provider-centric: minimal changes, but cedrus tool usage is opaque from the OpenHands side.
- Agent-centric: requires small code changes to the benchmark runners, but gives explicit tool call logging and clear “cedrus vs baseline” toggles.

---

## 3. Forking Strategy

We will **fork** `OpenHands/benchmarks` and treat that fork as the home for cedrus-specific evaluation logic.

### Rationale

- We need to modify the existing benchmarks to:
  - inject `mcp_config` into `Agent` construction (for cedrus MCP),
  - and add configuration knobs (flags/env) to toggle cedrus on/off.
- Re-implementing the whole evaluation harness in `cedrus-mcp` would duplicate a lot of logic that already exists and is battle-tested.
- A fork keeps changes:
  - version-controlled and reviewable,
  - easy to periodically rebase on upstream,
  - potentially upstreamable later as generic MCP hooks.

### Plan

- Fork `https://github.com/OpenHands/benchmarks` into the cedrus org or personal GitHub.
- Create a feature branch, e.g. `cedrus-experiments`.
- Keep changes **minimal, additive, and configuration-driven** so they can plausibly be upstreamed later.

---

## 4. Planned Changes in the Fork

### 4.1 SWE-bench (benchmarks/swebench)

Goal: support **baseline vs cedrus** runs with minimal config changes, while still using the official SWE-bench harness for scoring.

Planned changes:

1. **Add cedrus MCP configuration**
   - Extend the SWE-bench `Evaluation` metadata to carry either:
     - a simple boolean flag, e.g. `cedrus_enabled`, or
     - a generic `mcp_config_path` pointing to a JSON/YAML file describing MCP servers.
   - In `SWEBenchEvaluation.evaluate_instance`:
     - Build `mcp_config` when cedrus is enabled, following the GAIA pattern:
       ```python
       tools = get_default_tools(enable_browser=False)

       cedrus_mcp_config = None
       if self.metadata.details and self.metadata.details.get("cedrus_enabled"):
           cedrus_mcp_config = {
               "mcpServers": {
                   "cedrus": {
                       # one of:
                       # stdio:
                       "command": "cedrus-mcp-server",
                       "args": ["--port", "…"],
                       # or HTTP-based:
                       # "url": "https://cedrus-host/mcp",
                   }
               }
           }

       agent = Agent(
           llm=self.metadata.llm,
           tools=tools,
           system_prompt_kwargs={"cli_mode": True},
           mcp_config=cedrus_mcp_config,
           # optionally: filter_tools_regex to expose only cedrus reasoning tools
       )
       ```
   - This yields:
     - `baseline`: same pipeline, `mcp_config=None`.
     - `cedrus-on`: same pipeline, plus MCP tools from cedrus.

2. **LLM configuration**
   - Maintain separate `llm_config.json` files for:
     - Baseline (no cedrus; plain LLM).
     - Cedrus-augmented (either:
       - same LLM + cedrus MCP via `mcp_config`, or
       - a provider-centric cedrus-wrapped endpoint).
   - Ensure any differences other than cedrus are minimal (same model, temperature, prompts where possible).

3. **Evaluation & logging**
   - Keep using `swebench-eval` as-is:
     - Converts output JSONL to SWE-bench predictions.
     - Runs official `swebench.harness.run_evaluation`.
   - For cedrus experiments, add (in separate scripts or postprocessing):
     - Per-run JSON metadata summarizing:
       - dataset, split, model, agent config, `cedrus_enabled`.
       - SWE-bench resolution metrics (counts and rates).
     - Optional per-instance logs including:
       - `history` (trajectory),
       - cedrus-specific tool calls (if we decide to post-process `history`).

### 4.2 GAIA (benchmarks/gaia)

Goal: reuse GAIA as a **general reasoning benchmark** for cedrus and mirror the same baseline vs cedrus toggling patterns.

Planned changes:

1. **Generalize MCP configuration**
   - Replace hardcoded Tavily MCP config with a config-driven approach:
     - Either a dedicated `gaia_mcp_config.json`,
     - Or reuse the same `mcp_config_path` mechanism as SWE-bench.
   - Still support Tavily as the default, but allow adding a `cedrus` MCP server alongside or instead.

2. **Cedrus as MCP server**
   - Use the same pattern as SWE-bench for enabling cedrus:
     - When enabled, add a `cedrus` server to `mcp_config`.
     - Optionally filter tools to specific cedrus reasoning tools.

3. **Outputs**
   - Leave GAIA scoring and JSONL output format unchanged:
     - This keeps GAIA comparable to other runs in the OpenHands ecosystem.
   - Add high-level run metadata for cedrus vs baseline runs, similar to SWE-bench.

---

## 5. Baseline vs Cedrus Runs

For each benchmark (SWE-bench and GAIA) we will maintain at least two standardized run configurations:

1. **Baseline**
   - No cedrus MCP:
     - `mcp_config` is empty / disabled.
   - LLM pointing to a plain endpoint (e.g. Devstral via vLLM).
   - Same prompts, tools, and runtime limits as cedrus runs where possible.

2. **Cedrus-augmented**
   - **Agent-centric mode:**
     - Same LLM as baseline.
     - `mcp_config` includes cedrus MCP server.
     - Optional `filter_tools_regex` to expose only cedrus reasoning tools.
   - **(Optional) Provider-centric mode:**
     - LLM endpoint already wraps cedrus internally.
     - From the benchmark’s point of view, only `llm_config.json` changes.

Each run produces:

- Raw output JSONL (per-instance `git_patch` or GAIA score).
- Trajectories (`history`) and metrics (costs, tool usage).
- SWE-bench metrics via `swebench-eval` (for SWE-bench).
- GAIA accuracy via `gaia` scorer (for GAIA).

---

## 6. Open Questions / TODOs

- Decide how much of the cedrus integration should be **generic** and upstreamable:
  - e.g., “pass `mcp_config` via CLI/JSON in all benchmarks” vs “cedrus-only wiring.”
- Decide on the **canonical configuration format** for MCP:
  - Reuse the SDK’s native `mcp_config` dict format?
  - Or a small TOML/JSON file per experiment?
- Define a standard way to **log and persist reasoning graphs**:
  - Likely post-process cedrus MCP tool calls from `history` and fetch/store graphs per instance.

---

## 7. Summary

- `OpenHands/benchmarks` already provides:
  - A strong SWE-bench harness wrapper (SWE-bench + official eval).
  - A GAIA pipeline with MCP-based web tools.
- Forking `OpenHands/benchmarks` is the most practical approach:
  - The fork will host cedrus-specific configs and small code changes.
  - We keep changes minimal, config-driven, and potentially upstreamable.
- Immediate next steps:
  1. Fork `OpenHands/benchmarks` and create a `cedrus-experiments` branch.
  2. Add a cedrus MCP configuration path to:
     - `benchmarks/swebench/run_infer.py`
     - `benchmarks/gaia/run_infer.py`
  3. Define baseline and cedrus
