# Evaluation pipeline requirements

This document captures the high-level requirements and preferences we have discussed for evaluating the cedrus MCP server and related "thinking tools" across agent frameworks.

It is intended as a checklist/reference when assessing the fit of different AI agent SDKs (SWE-agent, mini-SWE-agent, custom harnesses, others).

## Core goals

- **Test cedrus as an MCP server**
  - Focus on `reasoning-graph` and similar MCP tools as first-class capabilities.
  - Evaluate how much they improve agent performance and behaviour, not just whether they can be wired in.

- **Use existing benchmarks and harnesses**
  - Start with SWE-bench (especially SWE-bench Lite / Verified) and its official evaluation harness.
  - Prefer local, reproducible evaluation over remote/hosted services.

- **Compare with vs. without cedrus**
  - For a given agent framework + model + benchmark configuration, run at least two conditions:
    - Baseline: no cedrus tools available.
    - Cedrus-augmented: cedrus MCP tools available, minimal changes otherwise.
  - Ensure differences are attributable primarily to cedrus, not unrelated config changes.

## Benchmark and evaluation requirements

- **SWE-bench integration**
  - Ability to run the agent on SWE-bench instances in batch mode.
  - Clear mapping from agent outputs to SWE-bench prediction format:
    - `instance_id`, `model_patch`, `model_name_or_path`.
  - Support for using the official SWE-bench harness locally:
    - `python -m swebench.harness.run_evaluation` with configurable `dataset_name`, `predictions_path`, `max_workers`, `run_id`.

- **Local evaluation preference**
  - Default to evaluating with the local SWE-bench harness (Docker-based), rather than relying solely on hosted services (e.g. sb-cli).
  - Hosted evaluation can still be used as a secondary check, but should not be required.

- **Result logging and comparison**
  - For each run, capture at least:
    - Benchmark subset/split, agent config, model name, cedrus on/off.
    - SWE-bench metrics: resolution rate, number of resolved/failed instances.
  - Make it easy to compare runs (e.g., structured JSON outputs plus human-readable summaries).

## Agent / SDK requirements

- **Minimal changes for baseline vs. cedrus runs**
  - Ideally, turning cedrus on/off is controlled via configuration (YAML, flags) rather than code changes:
    - e.g., adding/removing a tool bundle,
    - switching model endpoint (cedrus-augmented provider vs. plain provider),
    - or toggling a system/instance template section.
  - Avoid forking or heavily modifying the agent SDK just to integrate cedrus.

- **Tool integration options**

  We care about two complementary integration styles:

  1. **Provider-centric MCP**
     - The agent sees a plain chat model; the inference provider:
       - runs an MCP client for cedrus,
       - orchestrates tool-calls internally (looping with the LLM),
       - returns a single text response per agent step.
     - Requirements:
       - Ability to plug in a custom "model" endpoint into the agent SDK.
       - Freedom to control system prompts and context passed to the model.

  2. **Agent-centric tools**
     - The agent SDK exposes a tool abstraction (commands, functions, bundles).
     - Cedrus is integrated as one or more tools whose implementations speak MCP internally.
     - Requirements:
       - Tool definition mechanism (signatures + documentation visible to the LLM).
       - Ability to add custom tools without patching the SDK core.

  We may use one or both styles depending on the SDK.

- **Model flexibility**
  - Prefer support for open-weight models (e.g. devstral) served via vLLM or similar.
  - SDK should allow configuring custom endpoints (OpenAI-compatible or otherwise) so we can:
    - run open-weight models locally,
    - optionally wrap them with cedrus-aware providers.

- **Transparency and logging**
  - Access to full trajectories (prompts, model outputs, tool calls) for debugging and analysis.
  - For cedrus experiments:
    - Ability to log when and how cedrus tools were called (arguments, outputs),
    - and, ideally, to persist the resulting reasoning graph per instance.

## Non-goals / deprioritized aspects (for now)

- Building or depending on heavy frontends/UI for agents.
- Highly specialized, benchmark-specific agent logic that cannot generalize beyond SWE-bench.
- Deep customization of the agent control flow that complicates comparisons across frameworks.

## Summary

When considering an agent SDK or framework for cedrus evaluations, check:

1. Can it run on SWE-bench (Lite/Verified) and produce patches that the SWE-bench harness can evaluate locally?
2. Can we run the same agent+model configuration with and without cedrus, changing as little as possible (ideally only config)?
3. Does it support either:
   - a provider-centric MCP integration, or
   - a tool abstraction where cedrus can be wrapped cleanly as a tool bundle?
4. Does it play well with open-weight models (e.g. devstral via vLLM) and give us full access to trajectories and logs?

This checklist should serve as the reference point when exploring SWE-agent, mini-SWE-agent, or any other agent SDK as candidates for cedrus MCP evaluation pipelines.
