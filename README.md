<h1 align="center">🌳 Cedrus MCP Server</h1>

<p align="center">
  A <strong>thinking tool</strong> for scaffolding AI reasoning.
</p>

---

> [!WARNING]
>
> This MCP server is in early development. It's currently being tested and evaluated, and may be subject to major revisions or breaking changes.

Cedrus runs as a Model Context Protocol (MCP) server and gives AI agents tools and resources to <strong>externalize and structure their chain‑of‑thought reasoning</strong> as a <code>reasoning-graph</code>.

You can think of Cedrus as a text-based argument mapping tool tailored to AI agents. Cedrus helps agents to keep track of their evolving deliberation, offering tools to sketch, refine, and review complex and heterogenous argumentation.



## Why use Cedrus?

Most assistants already "think" internally, but that reasoning may be:
- **Invisible** – you only see the final answer.
- **Linear** – a very long paragraph, not a structured map.
- **Inconclusive** – the path from reasoning to answer is unclear.
- **Hard to critique** – you cannot easily see where a mistake enters.

Cedrus helps by:
- Turning chain‑of‑thought into a **graph of reasons**.
- Making it easier for AI assistants to **spot gaps, conflicts, and dangling assumptions**.
- Giving the assistant (and potentially the user) a **concrete structure** to inspect, revise, and build on.

It is especially useful for:
- AI agents that (regularly) face complex internal decisions.
- AI assistants that support debates, policy making, or strategic planning.
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

Once connected, Cedrus reshapes the assistant’s internal chain‑of‑thought into a recurring process:

1. The assistant begins in a **sketching** phase  
   - It turns key internal thoughts into candidate claims.  
   - It attaches quick arguments for and against those claims.

2. As the chain‑of‑thought deepens, the assistant **elaborates**  
   - It decomposes broad claims into more precise, smaller ones.  
   - It makes relations explicit: which reasons support or attack which points.

3. The assistant can then shift into a **critical / review** phase  
   - It surveys the emerging argument structure.  
   - It searches for contradictions, missing links, or weakly supported claims.  
   - It asks Cedrus to surface areas where more reasoning work is needed.

All of this remains part of the assistant’s chain‑of‑thought, but Cedrus organizes it as an explicit argument graph instead of a single, opaque text stream.



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
- There are tools for summaries and node details, so your agent can easily explore the map.

Once your client can connect to Cedrus with:

```bash
uvx git+https://github.com/logikon-ai/cedrus-mcp
```

let the assistant explore the available tools and use Cedrus as a **structured thinking surface** for its chain‑of‑thought.

## Evaluation (with MASLab)

See: https://github.com/cedrus-mcp/MASLab

&#x274C;

### AIME-2024 / devstral-small-2 (N=30)

| mas_method       | cedrus-mcp         |   score |   num_llm_calls |   prompt_tokens |   completion_tokens |   num_tool_calls |
|:-----------------|:-------------------|--------:|----------------:|----------------:|--------------------:|-----------------:|
| agentverse       | ✅ (all agents)    |   0.214 |             8.9 |           45130 |                6584 |                0 |
| agentverse       | ✅ (some agents)   |   0.333 |             8.3 |           42717 |                8077 |                0 |
| agentverse       | &#x274C;           |   0.357 |             6.7 |           31180 |                7807 |                0 |
| camel            | ✅                 |   0     |            13   |           90343 |                5354 |                0 |
| camel            | &#x274C;           |   0     |            12.9 |          127803 |                9469 |                0 |
| cot              | ✅                 |   0.3   |             1   |            1500 |                1801 |                0 |
| cot              | &#x274C;           |   0.5   |             1   |             116 |                4246 |                0 |
| dylan            | ✅                 |   0.333 |            10.9 |           84857 |               31227 |                0 |
| dylan            | &#x274C;           |   0.4   |            11   |           64907 |               34801 |                0 |
| llm_debate       | ✅                 |   0.5   |             7   |           47324 |               15125 |                0 |
| llm_debate       | &#x274C;           |   0.567 |             7   |           43309 |               17911 |                0 |
| mad              | ✅                 |   0.062 |             2   |           31542 |                3191 |                0 |
| mad              | &#x274C;           |   0.207 |             3.2 |           28543 |                7301 |                0 |
| mav              | ✅                 |   0.067 |            10   |           22772 |                2704 |                0 |
| mav              | &#x274C;           |   0.133 |            10   |           14332 |                8486 |                0 |
| self_consistency | ✅                 |   0.433 |             6   |           27963 |               19556 |                0 |
| self_consistency | &#x274C;           |   0.4   |             6   |           23079 |               22902 |                0 |

### AIME-2025 / devstral-small-2 (N=30)

| mas_method       | cedrus-mcp         |   score |   num_llm_calls |   prompt_tokens |   completion_tokens |   num_tool_calls |
|:-----------------|:-------------------|--------:|----------------:|----------------:|--------------------:|-----------------:|
| agentverse       | ✅ (all agents)    |   0.233 |            10.4 |           42942 |                6288 |                0 |
| agentverse       | ✅ (some agents)   |   0.276 |             8.7 |           35710 |                6624 |                0 |
| agentverse       | &#x274C;           |   0.233 |             8   |           29021 |                6838 |                0 |
| camel            | ✅                 |   0     |            13   |           85928 |                4626 |                0 |
| camel            | &#x274C;           |   0     |            13   |           64172 |                6008 |                0 |
| cot              | ✅                 |   0.1   |             1   |            1587 |                2102 |                0 |
| cot              | &#x274C;           |   0.267 |             1   |             203 |                4009 |                0 |
| dylan            | ✅                 |   0.267 |            10.8 |           77440 |               26974 |                0 |
| dylan            | &#x274C;           |   0.3   |            10.9 |           79759 |               33021 |                0 |
| llm_debate       | ✅                 |   0.3   |             7   |           50487 |               16439 |                0 |
| llm_debate       | &#x274C;           |   0.333 |             7   |           45480 |               18400 |                0 |
| mad              | ✅                 |   0.053 |             2.5 |           28071 |                3049 |                0 |
| mad              | &#x274C;           |   0.045 |             3.8 |           81026 |                7023 |                0 |
| mav              | ✅                 |   0.033 |            10   |           23346 |                2460 |                0 |
| mav              | &#x274C;           |   0.067 |            10   |           15044 |                8913 |                0 |
| self_consistency | ✅                 |   0.333 |             6   |           28113 |               19143 |                0 |
| self_consistency | &#x274C;           |   0.367 |             6   |           22985 |               22481 |                0 |

### APEX-SHORTLIST / devstral-small-2 (N=49)

| mas_method       | cedrus-mcp         |   score |   num_llm_calls |   prompt_tokens |   completion_tokens |   num_tool_calls |
|:-----------------|:-------------------|--------:|----------------:|----------------:|--------------------:|-----------------:|
| agentverse       | ✅ (all agents)    |   0.042 |            10.1 |           38069 |                5227 |                0 |
| agentverse       | ✅ (some agents)   |   0.061 |             8.8 |           32801 |                5771 |                0 |
| agentverse       | &#x274C;           |   0     |             9.8 |           30228 |                6993 |                0 |
| camel            | ✅                 |   0     |            13   |           65192 |                4502 |                0 |
| camel            | &#x274C;           |   0.02  |            13   |           54843 |                6147 |                0 |
| cot              | ✅                 |   0.041 |             1   |            1554 |                1793 |                0 |
| cot              | &#x274C;           |   0.077 |             1   |             170 |                3821 |                0 |
| dylan            | ✅                 |   0.02  |            11   |           63630 |               24650 |                0 |
| dylan            | &#x274C;           |   0.083 |            10.8 |           55554 |               30511 |                0 |
| llm_debate       | ✅                 |   0.102 |             7   |           42585 |               13549 |                0 |
| llm_debate       | &#x274C;           |   0.122 |             7   |           36477 |               14027 |                0 |
| mad              | ✅                 |   0     |             1   |            8797 |                1022 |                0 |
| mad              | &#x274C;           |   0     |             2.6 |           55690 |                4276 |                0 |
| mav              | ✅                 |   0     |             7.3 |           17339 |                2425 |                0 |
| mav              | &#x274C;           |   0.02  |            10   |           10386 |                5880 |                0 |
| self_consistency | ✅                 |   0.102 |             6   |           23725 |               14925 |                0 |
| self_consistency | &#x274C;           |   0.061 |             6   |           19783 |               19082 |                0 |

### AQUA-RAT / devstral-small-2 (N=254)

| mas_method       | cedrus-mcp         |   score |   num_llm_calls |   prompt_tokens |   completion_tokens |   num_tool_calls |
|:-----------------|:-------------------|--------:|----------------:|----------------:|--------------------:|-----------------:|
| agentverse       | ✅ (all agents)    |   0.856 |             8   |           24088 |                2615 |                0 |
| agentverse       | ✅ (some agents)   |   0.873 |             5.6 |           13323 |                2226 |                0 |
| agentverse       | &#x274C;           |   0.844 |             6.3 |           13276 |                2829 |                0 |
| camel            | ✅                 |   0.12  |            13   |           43762 |                3164 |                0 |
| camel            | &#x274C;           |   0.078 |            12.9 |           29989 |                4491 |                0 |
| cot              | ✅                 |   0.53  |             1   |            1492 |                 406 |                0 |
| cot              | &#x274C;           |   0.893 |             1   |             108 |                 923 |                0 |
| dylan            | ✅                 |   0.826 |            10.7 |           24699 |                6341 |                0 |
| dylan            | &#x274C;           |   0.753 |            10.6 |           13515 |                8372 |                0 |
| llm_debate       | ✅                 |   0.798 |             7   |           17296 |                3448 |                0 |
| llm_debate       | &#x274C;           |   0.864 |             7   |            8947 |                3441 |                0 |
| mad              | ✅                 |   0.276 |             1.7 |            6884 |                 664 |                0 |
| mad              | &#x274C;           |   0.207 |             3.5 |            9559 |                2263 |                0 |
| mav              | ✅                 |   0.827 |             7.2 |           15005 |                1821 |                0 |
| mav              | &#x274C;           |   0.484 |            10   |            5588 |                2760 |                0 |
| self_consistency | ✅                 |   0.776 |             6   |           11532 |                2952 |                0 |
| self_consistency | &#x274C;           |   0.907 |             6   |            4953 |                4451 |                0 |

### GPQA / devstral-small-2 (N=448)

| mas_method       | cedrus-mcp         |   score |   num_llm_calls |   prompt_tokens |   completion_tokens |   num_tool_calls |
|:-----------------|:-------------------|--------:|----------------:|----------------:|--------------------:|-----------------:|
| agentverse       | ✅ (all agents)    |   0.53  |             6.5 |           22675 |                2675 |                0 |
| agentverse       | ✅ (some agents)   |   0.556 |             5.5 |           16938 |                2850 |                0 |
| agentverse       | &#x274C;           |   0.525 |             6.3 |           16003 |                3524 |                0 |
| camel            | ✅                 |   0     |            13   |           49843 |                3838 |                0 |
| camel            | &#x274C;           |   0     |            13   |           34995 |                5401 |                0 |
| cot              | ✅                 |   0.388 |             1   |            1608 |                 746 |                0 |
| cot              | &#x274C;           |   0.467 |             1   |             224 |                1261 |                0 |
| dylan            | ✅                 |   0.557 |            10.9 |           32218 |               10345 |                0 |
| dylan            | &#x274C;           |   0.456 |            10.9 |           19818 |               12163 |                0 |
| llm_debate       | ✅                 |   0.522 |             7   |           22163 |                5491 |                0 |
| llm_debate       | &#x274C;           |   0.575 |             7   |           13185 |                5153 |                0 |
| mad              | ✅                 |   0.472 |             2.1 |           10478 |                1134 |                0 |
| mad              | &#x274C;           |   0.369 |             4   |           14498 |                3142 |                0 |
| mav_gpqa         | ✅                 |   0.358 |             4.8 |           11773 |                1483 |                0 |
| mav_gpqa         | &#x274C;           |   0.56  |            10   |           13337 |                4280 |                0 |
| self_consistency | ✅                 |   0.483 |             6   |           13748 |                4664 |                0 |
| self_consistency | &#x274C;           |   0.574 |             6   |            6180 |                5128 |                0 |

### GPQA-Diamond / devstral-small-2 (N=198)

| mas_method       | cedrus-mcp         |   score |   num_llm_calls |   prompt_tokens |   completion_tokens |   num_tool_calls |
|:-----------------|:-------------------|--------:|----------------:|----------------:|--------------------:|-----------------:|
| agentverse       | ✅ (all agents)    |   0.571 |             7.1 |           24918 |                3040 |                0 |
| agentverse       | ✅ (some agents)   |   0.611 |             5.7 |           17867 |                3071 |                0 |
| agentverse       | &#x274C;           |   0.545 |             6.5 |           15589 |                3380 |                0 |
| camel            | ✅                 |   0     |            12.9 |           48344 |                3650 |                0 |
| camel            | &#x274C;           |   0     |            13   |           46762 |                5939 |                0 |
| cot              | ✅                |   0.411 |             1   |            1616 |                 751 |                0 |
| cot              | &#x274C;           |   0.564 |             1   |             232 |                1247 |                0 |
| dylan            | ✅                 |   0.458 |            10.9 |           32119 |               10700 |                0 |
| dylan            | &#x274C;           |   0.417 |            10.9 |           20594 |               12548 |                0 |
| llm_debate       | ✅                 |   0.519 |             7   |           22661 |                5679 |                0 |
| llm_debate       | &#x274C;           |   0.619 |             7   |           13656 |                5263 |                0 |
| mad              | ✅                 |   0.407 |             2.1 |           11817 |                1321 |                0 |
| mad              | &#x274C;           |   0.509 |             4   |           15488 |                3195 |                0 |
| mav_gpqa         | ✅                 |   0.361 |             4.9 |           12381 |                1820 |                0 |
| mav_gpqa         | &#x274C;           |   0.596 |            10   |           14569 |                4938 |                0 |
| self_consistency | ✅                 |   0.565 |             6   |           14147 |                4988 |                0 |
| self_consistency | &#x274C;           |   0.639 |             6   |            6543 |                5439 |                0 |

### GSM-Hard / devstral-small-2 (N=500)

| mas_method       | cedrus-mcp              |   score |   num_llm_calls |   prompt_tokens |   completion_tokens |   num_tool_calls |
|:-----------------|:------------------------|--------:|----------------:|----------------:|--------------------:|-----------------:|
| agentverse_mgsm  | &#x274C;                |   0.552 |             7.2 |            9117 |                1920 |                0 |
| agentverse_mgsm  | ✅ (all agents)         |   0.719 |            10.3 |           28022 |                2665 |                0 |
| agentverse_mgsm  | ✅ (some agents)        |   0.582 |             6.9 |           12600 |                1674 |                0 |
| camel            | ✅                      |   0.017 |            12.9 |           39723 |                2825 |                0 |
| camel            | &#x274C;                |   0.035 |            13   |           19782 |                3225 |                0 |
| cot              | ✅                      |   0.163 |             1   |            1469 |                 265 |                0 |
| cot              | &#x274C;                |   0.685 |             1   |              85 |                 665 |                0 |
| dylan            | ✅                      |   0.615 |            10.6 |           22085 |                4771 |                0 |
| dylan            | &#x274C;                |   0.537 |            10.5 |            8331 |                5747 |                0 |
| llm_debate       | ✅                      |   0.62  |             7   |           15202 |                2644 |                0 |
| llm_debate       | &#x274C;                |   0.655 |             7   |            6782 |                2839 |                0 |
| mad              | ✅                      |   0.065 |             2.7 |            9115 |                 855 |                0 |
| mad              | &#x274C;                |   0.057 |             4.2 |           11284 |                2057 |                0 |
| mav              | ✅                      |   0.492 |             7.8 |           15595 |                1612 |                0 |
| mav              | &#x274C;                |   0.278 |            10   |            4382 |                1760 |                0 |
| self_consistency | ✅                      |   0.577 |             6   |           10637 |                2197 |                0 |
| self_consistency | &#x274C;                |   0.672 |             6   |            3075 |                2783 |                0 |

### GSM8K / devstral-small-2 (N=500)

| mas_method       | cedrus-mcp              |   score |   num_llm_calls |   prompt_tokens |   completion_tokens |   num_tool_calls |
|:-----------------|:------------------------|--------:|----------------:|----------------:|--------------------:|-----------------:|
| agentverse_mgsm  | &#x274C;                |   0.937 |             4.8 |            4467 |                 769 |                0 |
| agentverse_mgsm  | ✅ (all agents)         |   0.903 |             7.4 |           18185 |                1443 |                0 |
| agentverse_mgsm  | ✅ (some agents)        |   0.939 |             4.7 |            6875 |                 728 |                0 |
| camel            | ✅                      |   0     |            12.9 |           38057 |                2763 |                0 |
| camel            | &#x274C;                |   0.071 |            13   |           18880 |                2902 |                0 |
| cot              | ✅                      |   0.325 |             1   |            1465 |                 243 |                0 |
| cot              | &#x274C;                |   0.942 |             1   |              81 |                 354 |                0 |
| dylan            | ✅                      |   0.826 |            10.7 |           20876 |                3890 |                0 |
| dylan            | &#x274C;                |   0.855 |            10.6 |            6976 |                4219 |                0 |
| llm_debate       | ✅                      |   0.836 |             7   |           14027 |                1951 |                0 |
| llm_debate       | &#x274C;                |   0.941 |             7   |            4497 |                1798 |                0 |
| mad              | ✅                      |   0.075 |             2.5 |            7655 |                 666 |                0 |
| mad              | &#x274C;                |   0.08  |             4.3 |            7592 |                1575 |                0 |
| mav              | ✅                      |   0.717 |             6.8 |           13249 |                1255 |                0 |
| mav              | &#x274C;                |   0.417 |            10   |            3984 |                1491 |                0 |
| self_consistency | ✅                      |   0.858 |             6   |           10130 |                1652 |                0 |
| self_consistency | &#x274C;                |   0.954 |             6   |            2067 |                1735 |                0 |

### MATH / devstral-small-2 (N=198-500)

| mas_method       | cedrus-mcp         | score   |   num_llm_calls |   prompt_tokens |   completion_tokens |   num_tool_calls |
|:-----------------|:-------------------|:--------|----------------:|----------------:|--------------------:|-----------------:|
| agentverse       | ✅ (all agents)     | 0.806   |             6   |           19320 |                2151 |                0 |
| agentverse       | ✅ (some agents)   | 0.859   |             4.8 |           13325 |                2072 |                0 |
| agentverse       | &#x274C;           | 0.863   |             6   |           15225 |                3192 |                0 |
| camel            | ✅                 | 0.000   |            13   |           49548 |                3905 |                0 |
| camel            | &#x274C;           | 0.039   |            13   |           28855 |                4166 |                0 |
| cot              | ✅                 | 0.307   |             1   |            1472 |                 447 |                0 |
| cot              | &#x274C;           | 0.860   |             1   |              88 |                1456 |                0 |
| dylan_math       | &#x274C;           | 0.920   |             3.9 |           13484 |                4485 |                0 |
| dylan_math       | ✅                 | 0.742   |             5.8 |           26668 |                3892 |                0 |
| llm_debate       | ✅                 | 0.786   |             7   |           21442 |                5181 |                0 |
| llm_debate       | &#x274C;           | 0.926   |             7   |           15105 |                6113 |                0 |
| mad              | ✅                 | 0.186   |             1.4 |            5877 |                 747 |                0 |
| mad              | &#x274C;           |         |             0   |               0 |                   0 |                0 |
| mav_math         | ✅                 | 0.768   |             5.2 |           12940 |                1787 |                0 |
| mav_math         | &#x274C;           | 0.900   |            10   |           15233 |                4924 |                0 |
| self_consistency | ✅                 | 0.819   |             6   |           13510 |                5095 |                0 |
| self_consistency | &#x274C;           | 0.950   |             6   |            7296 |                7013 |                0 |

### MMLU / devstral-small-2 (N=500)

| mas_method       | cedrus-mcp         |   score |   num_llm_calls |   prompt_tokens |   completion_tokens |   num_tool_calls |
|:-----------------|:-------------------|--------:|----------------:|----------------:|--------------------:|-----------------:|
| agentverse       | ✅ (all agents)    |   0.786 |             4.9 |           12368 |                1084 |                0 |
| agentverse       | ✅ (some agents)   |   0.8   |             4.4 |           10156 |                1678 |                0 |
| agentverse       | &#x274C;           |   0.792 |             4.6 |            7119 |                1584 |                0 |
| camel            | ✅                 |   0.015 |            13   |           43383 |                3416 |                0 |
| camel            | &#x274C;           |   0.048 |            13   |           29886 |                4354 |                0 |
| cot              | ✅                 |   0.388 |             1   |            1534 |                 250 |                0 |
| cot              | &#x274C;           |   0.761 |             1   |             150 |                 455 |                0 |
| dylan_mmlu       | &#x274C;           |   0.302 |             8.7 |            1975 |                3459 |                0 |
| dylan_mmlu       | ✅                 |   0.185 |             8.8 |           14060 |                3026 |                0 |
| llm_debate       | ✅                 |   0.707 |             7   |           15708 |                2487 |                0 |
| llm_debate       | &#x274C;           |   0.823 |             7   |            5366 |                2005 |                0 |
| mad              | ✅                 |   0.338 |             2.7 |            9427 |                 869 |                0 |
| mad              | &#x274C;           |   0.265 |             4.1 |            9378 |                1808 |                0 |
| mav_mmlu         | ✅                 |   0.561 |             9.2 |           19100 |                1761 |                0 |
| mav_mmlu         | &#x274C;           |   0.794 |            10   |            6320 |                1421 |                0 |
| self_consistency | ✅                 |   0.646 |             6   |           10984 |                2095 |                0 |
| self_consistency | &#x274C;           |   0.806 |             6   |            2118 |                1411 |                0 |

### MMLU-Pro / devstral-small-2 (N=500)

| mas_method       | cedrus-mcp         |   score |   num_llm_calls |   prompt_tokens |   completion_tokens |   num_tool_calls |
|:-----------------|:-------------------|--------:|----------------:|----------------:|--------------------:|-----------------:|
| agentverse       | ✅ (all agents)    |   0.648 |             6.1 |           19575 |                2032 |                0 |
| agentverse       | ✅ (some agents)   |   0.698 |             4.9 |           13911 |                2216 |                0 |
| agentverse       | &#x274C;           |   0.738 |             5.8 |           14386 |                2975 |                0 |
| camel            | ✅                 |   0     |            13   |           45166 |                3599 |                0 |
| camel            | &#x274C;           |   0.018 |            13   |           29006 |                4379 |                0 |
| cot              | ✅                 |   0.379 |             1   |            1604 |                 482 |                0 |
| cot              | &#x274C;           |   0.765 |             1   |             220 |                 838 |                0 |
| llm_debate       | ✅                 |   0.624 |             7   |           19097 |                3717 |                0 |
| llm_debate       | &#x274C;           |   0.726 |             7   |            8864 |                3216 |                0 |
| mad              | ✅                 |   0.157 |             2.2 |            9101 |                 952 |                0 |
| mad              | &#x274C;           |   0.177 |             4.2 |           13723 |                2567 |                0 |
| self_consistency | ✅                 |   0.55  |             6   |           12471 |                3231 |                0 |
| self_consistency | &#x274C;           |   0.708 |             6   |            4134 |                3026 |                0 |

### MedMCQA / devstral-small-2 (N=500)

| mas_method       | cedrus-mcp         |   score |   num_llm_calls |   prompt_tokens |   completion_tokens |   num_tool_calls |
|:-----------------|:-------------------|--------:|----------------:|----------------:|--------------------:|-----------------:|
| agentverse       | ✅ (all agents)    |   0.729 |             5.4 |           13476 |                1243 |                0 |
| agentverse       | ✅ (some agents)   |   0.681 |             4.7 |            9457 |                1492 |                0 |
| agentverse       | &#x274C;           |   0.681 |             4.9 |            7998 |                1891 |                0 |
| camel            | ✅                 |   0     |            13   |           45758 |                3378 |                0 |
| camel            | &#x274C;           |   0     |            13   |           32389 |                5061 |                0 |
| cot              | ✅                 |   1     |             1   |            1461 |                 254 |                0 |
| cot              | &#x274C;           |   0.667 |             1   |              77 |                 379 |                0 |
| dylan            | ✅                 |   0.586 |            11   |           22807 |                4650 |                0 |
| dylan            | &#x274C;           |   0.593 |            10.9 |            8503 |                5160 |                0 |
| llm_debate       | ✅                 |   0.686 |             7   |           14176 |                2146 |                0 |
| llm_debate       | &#x274C;           |   0.717 |             7   |            4222 |                1809 |                0 |
| mad              | ✅                 |   0.217 |             2.2 |            7150 |                 604 |                0 |
| mad              | &#x274C;           |   0.231 |             4.5 |           10705 |                2120 |                0 |
| mav              | ✅                 |   0.577 |             8.5 |           15349 |                1387 |                0 |
| mav              | &#x274C;           |   0.618 |            10   |            4307 |                1930 |                0 |
| self_consistency | ✅                 |   0.603 |             6   |           10138 |                1751 |                0 |
| self_consistency | &#x274C;           |   0.648 |             6   |            1572 |                1310 |                0 |

### MedQA / devstral-small-2 (N=500)

| mas_method       | cedrus-mcp         |   score |   num_llm_calls |   prompt_tokens |   completion_tokens |   num_tool_calls |
|:-----------------|:-------------------|--------:|----------------:|----------------:|--------------------:|-----------------:|
| agentverse       | ✅ (all agents)    |   0.835 |             6.3 |           19557 |                2041 |                0 |
| agentverse       | ✅ (some agents)   |   0.714 |             4.7 |           11690 |                1938 |                0 |
| agentverse       | &#x274C;           |   0.682 |             5.1 |           10677 |                2392 |                0 |
| camel            | ✅                 |   0.017 |            13   |           42895 |                3360 |                0 |
| camel            | &#x274C;           |   0     |            13   |           35090 |                5456 |                0 |
| cot              | ✅                 |   0.454 |             1   |            1622 |                 474 |                0 |
| cot              | &#x274C;           |   0.89  |             1   |             238 |                 617 |                0 |
| dylan            | ✅                 |   0.765 |            11   |           27140 |                6797 |                0 |
| dylan            | &#x274C;           |   0.648 |            10.9 |           13233 |                7878 |                0 |
| llm_debate       | ✅                 |   0.703 |             7   |           18816 |                3688 |                0 |
| llm_debate       | &#x274C;           |   0.854 |             7   |            8476 |                3124 |                0 |
| mad              | ✅                 |   0.244 |             1.7 |            7254 |                 729 |                0 |
| mad              | &#x274C;           |   0.277 |             4   |           11026 |                2292 |                0 |
| mav              | ✅                 |   0.714 |             9.5 |           19422 |                2043 |                0 |
| mav              | &#x274C;           |   0.72  |            10   |            6622 |                2622 |                0 |
| self_consistency | ✅                 |   0.684 |             6   |           12240 |                2969 |                0 |
| self_consistency | &#x274C;           |   0.846 |             6   |            3563 |                2415 |                0 |

### SciBench / devstral-small-2 (N=499)

| mas_method       | cedrus-mcp         |   score |   num_llm_calls |   prompt_tokens |   completion_tokens |   num_tool_calls |
|:-----------------|:-------------------|--------:|----------------:|----------------:|--------------------:|-----------------:|
| agentverse       | ✅ (all agents)    |   0.553 |             6.2 |           23166 |                2815 |                0 |
| agentverse       | ✅ (some agents)   |   0.604 |             4.6 |           15432 |                2525 |                0 |
| agentverse       | &#x274C;           |   0.534 |             5.3 |           14242 |                3000 |                0 |
| camel            | ✅                 |   0     |            13   |           54846 |                4139 |                0 |
| camel            | &#x274C;           |   0     |            13   |           30521 |                4692 |                0 |
| cot              | ✅                 |   0.143 |             1   |            1491 |                 527 |                0 |
| cot              | &#x274C;           |   0.4   |             1   |             107 |                1223 |                0 |
| dylan            | ✅                 |   0.416 |            10.8 |           29558 |                9603 |                0 |
| dylan            | &#x274C;           |   0.353 |            10.8 |           16729 |               11466 |                0 |
| llm_debate       | ✅                 |   0.415 |             7   |           20569 |                5305 |                0 |
| llm_debate       | &#x274C;           |   0.51  |             7   |           12640 |                5708 |                0 |
| mad              | ✅                 |   0.017 |             1.5 |            6955 |                 831 |                0 |
| mad              | &#x274C;           |   0.058 |             2.5 |           10966 |                2526 |                0 |
| mav              | ✅                 |   0.349 |             6.2 |           13621 |                1705 |                0 |
| mav              | &#x274C;           |   0.253 |            10   |            7673 |                4377 |                0 |
| self_consistency | ✅                 |   0.433 |             6   |           13145 |                4879 |                0 |
| self_consistency | &#x274C;           |   0.467 |             6   |            5519 |                5456 |                0 |
