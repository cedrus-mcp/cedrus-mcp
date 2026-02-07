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

## Evaluation (cedrus `v0.1.0`)

See: https://github.com/cedrus-mcp/MASLab

### AIME-2024 / devstral-small-2 (N=30)

| mas_method       | cedrus-mcp         |   score |   num_llm_calls |   prompt_tokens |   completion_tokens |
|:-----------------|:-------------------|--------:|----------------:|----------------:|--------------------:|
| agentverse       | ✅ (all agents)    |   0.214 |             8.9 |           45130 |                6584 |
| agentverse       | ✅ (some agents)   |   0.333 |             8.3 |           42717 |                8077 |
| agentverse       | &#x274C;           |   0.357 |             6.7 |           31180 |                7807 |
| camel            | ✅                 |   0     |            13   |           90343 |                5354 |
| camel            | &#x274C;           |   0     |            12.9 |          127803 |                9469 |
| cot              | ✅                 |   0.3   |             1   |            1500 |                1801 |
| cot              | &#x274C;           |   0.5   |             1   |             116 |                4246 |
| dylan            | ✅                 |   0.333 |            10.9 |           84857 |               31227 |
| dylan            | &#x274C;           |   0.4   |            11   |           64907 |               34801 |
| llm_debate       | ✅                 |   0.5   |             7   |           47324 |               15125 |
| llm_debate       | &#x274C;           |   0.567 |             7   |           43309 |               17911 |
| mad              | ✅                 |   0.062 |             2   |           31542 |                3191 |
| mad              | &#x274C;           |   0.207 |             3.2 |           28543 |                7301 |
| mav              | ✅                 |   0.067 |            10   |           22772 |                2704 |
| mav              | &#x274C;           |   0.133 |            10   |           14332 |                8486 |
| self_consistency | ✅                 |   0.433 |             6   |           27963 |               19556 |
| self_consistency | &#x274C;           |   0.4   |             6   |           23079 |               22902 |

### AIME-2025 / devstral-small-2 (N=30)

| mas_method       | cedrus-mcp         |   score |   num_llm_calls |   prompt_tokens |   completion_tokens |
|:-----------------|:-------------------|--------:|----------------:|----------------:|--------------------:|
| agentverse       | ✅ (all agents)    |   0.233 |            10.4 |           42942 |                6288 |
| agentverse       | ✅ (some agents)   |   0.276 |             8.7 |           35710 |                6624 |
| agentverse       | &#x274C;           |   0.233 |             8   |           29021 |                6838 |
| camel            | ✅                 |   0     |            13   |           85928 |                4626 |
| camel            | &#x274C;           |   0     |            13   |           64172 |                6008 |
| cot              | ✅                 |   0.1   |             1   |            1587 |                2102 |
| cot              | &#x274C;           |   0.267 |             1   |             203 |                4009 |
| dylan            | ✅                 |   0.267 |            10.8 |           77440 |               26974 |
| dylan            | &#x274C;           |   0.3   |            10.9 |           79759 |               33021 |
| llm_debate       | ✅                 |   0.3   |             7   |           50487 |               16439 |
| llm_debate       | &#x274C;           |   0.333 |             7   |           45480 |               18400 |
| mad              | ✅                 |   0.053 |             2.5 |           28071 |                3049 |
| mad              | &#x274C;           |   0.045 |             3.8 |           81026 |                7023 |
| mav              | ✅                 |   0.033 |            10   |           23346 |                2460 |
| mav              | &#x274C;           |   0.067 |            10   |           15044 |                8913 |
| self_consistency | ✅                 |   0.333 |             6   |           28113 |               19143 |
| self_consistency | &#x274C;           |   0.367 |             6   |           22985 |               22481 |

### APEX-SHORTLIST / devstral-small-2 (N=49)

| mas_method       | cedrus-mcp         |   score |   num_llm_calls |   prompt_tokens |   completion_tokens |
|:-----------------|:-------------------|--------:|----------------:|----------------:|--------------------:|
| agentverse       | ✅ (all agents)    |   0.042 |            10.1 |           38069 |                5227 |
| agentverse       | ✅ (some agents)   |   0.061 |             8.8 |           32801 |                5771 |
| agentverse       | &#x274C;           |   0     |             9.8 |           30228 |                6993 |
| camel            | ✅                 |   0     |            13   |           65192 |                4502 |
| camel            | &#x274C;           |   0.02  |            13   |           54843 |                6147 |
| cot              | ✅                 |   0.041 |             1   |            1554 |                1793 |
| cot              | &#x274C;           |   0.077 |             1   |             170 |                3821 |
| dylan            | ✅                 |   0.02  |            11   |           63630 |               24650 |
| dylan            | &#x274C;           |   0.083 |            10.8 |           55554 |               30511 |
| llm_debate       | ✅                 |   0.102 |             7   |           42585 |               13549 |
| llm_debate       | &#x274C;           |   0.122 |             7   |           36477 |               14027 |
| mad              | ✅                 |   0     |             1   |            8797 |                1022 |
| mad              | &#x274C;           |   0     |             2.6 |           55690 |                4276 |
| mav              | ✅                 |   0     |             7.3 |           17339 |                2425 |
| mav              | &#x274C;           |   0.02  |            10   |           10386 |                5880 |
| self_consistency | ✅                 |   0.102 |             6   |           23725 |               14925 |
| self_consistency | &#x274C;           |   0.061 |             6   |           19783 |               19082 |

### AQUA-RAT / devstral-small-2 (N=254)

| mas_method       | cedrus-mcp         |   score |   num_llm_calls |   prompt_tokens |   completion_tokens |
|:-----------------|:-------------------|--------:|----------------:|----------------:|--------------------:|
| agentverse       | ✅ (all agents)    |   0.856 |             8   |           24088 |                2615 |
| agentverse       | ✅ (some agents)   |   0.873 |             5.6 |           13323 |                2226 |
| agentverse       | &#x274C;           |   0.844 |             6.3 |           13276 |                2829 |
| camel            | ✅                 |   0.12  |            13   |           43762 |                3164 |
| camel            | &#x274C;           |   0.078 |            12.9 |           29989 |                4491 |
| cot              | ✅                 |   0.53  |             1   |            1492 |                 406 |
| cot              | &#x274C;           |   0.893 |             1   |             108 |                 923 |
| dylan            | ✅                 |   0.826 |            10.7 |           24699 |                6341 |
| dylan            | &#x274C;           |   0.753 |            10.6 |           13515 |                8372 |
| llm_debate       | ✅                 |   0.798 |             7   |           17296 |                3448 |
| llm_debate       | &#x274C;           |   0.864 |             7   |            8947 |                3441 |
| mad              | ✅                 |   0.276 |             1.7 |            6884 |                 664 |
| mad              | &#x274C;           |   0.207 |             3.5 |            9559 |                2263 |
| mav              | ✅                 |   0.827 |             7.2 |           15005 |                1821 |
| mav              | &#x274C;           |   0.484 |            10   |            5588 |                2760 |
| self_consistency | ✅                 |   0.776 |             6   |           11532 |                2952 |
| self_consistency | &#x274C;           |   0.907 |             6   |            4953 |                4451 |

### GPQA / devstral-small-2 (N=448)

| mas_method       | cedrus-mcp         |   score |   num_llm_calls |   prompt_tokens |   completion_tokens |
|:-----------------|:-------------------|--------:|----------------:|----------------:|--------------------:|
| agentverse       | ✅ (all agents)    |   0.53  |             6.5 |           22675 |                2675 |
| agentverse       | ✅ (some agents)   |   0.556 |             5.5 |           16938 |                2850 |
| agentverse       | &#x274C;           |   0.525 |             6.3 |           16003 |                3524 |
| camel            | ✅                 |   0     |            13   |           49843 |                3838 |
| camel            | &#x274C;           |   0     |            13   |           34995 |                5401 |
| cot              | ✅                 |   0.388 |             1   |            1608 |                 746 |
| cot              | &#x274C;           |   0.467 |             1   |             224 |                1261 |
| dylan            | ✅                 |   0.557 |            10.9 |           32218 |               10345 |
| dylan            | &#x274C;           |   0.456 |            10.9 |           19818 |               12163 |
| llm_debate       | ✅                 |   0.522 |             7   |           22163 |                5491 |
| llm_debate       | &#x274C;           |   0.575 |             7   |           13185 |                5153 |
| mad              | ✅                 |   0.472 |             2.1 |           10478 |                1134 |
| mad              | &#x274C;           |   0.369 |             4   |           14498 |                3142 |
| mav_gpqa         | ✅                 |   0.358 |             4.8 |           11773 |                1483 |
| mav_gpqa         | &#x274C;           |   0.56  |            10   |           13337 |                4280 |
| self_consistency | ✅                 |   0.483 |             6   |           13748 |                4664 |
| self_consistency | &#x274C;           |   0.574 |             6   |            6180 |                5128 |

### GPQA-Diamond / devstral-small-2 (N=198)

| mas_method       | cedrus-mcp         |   score |   num_llm_calls |   prompt_tokens |   completion_tokens |
|:-----------------|:-------------------|--------:|----------------:|----------------:|--------------------:|
| agentverse       | ✅ (all agents)    |   0.571 |             7.1 |           24918 |                3040 |
| agentverse       | ✅ (some agents)   |   0.611 |             5.7 |           17867 |                3071 |
| agentverse       | &#x274C;           |   0.545 |             6.5 |           15589 |                3380 |
| camel            | ✅                 |   0     |            12.9 |           48344 |                3650 |
| camel            | &#x274C;           |   0     |            13   |           46762 |                5939 |
| cot              | ✅                |   0.411 |             1   |            1616 |                 751 |
| cot              | &#x274C;           |   0.564 |             1   |             232 |                1247 |
| dylan            | ✅                 |   0.458 |            10.9 |           32119 |               10700 |
| dylan            | &#x274C;           |   0.417 |            10.9 |           20594 |               12548 |
| llm_debate       | ✅                 |   0.519 |             7   |           22661 |                5679 |
| llm_debate       | &#x274C;           |   0.619 |             7   |           13656 |                5263 |
| mad              | ✅                 |   0.407 |             2.1 |           11817 |                1321 |
| mad              | &#x274C;           |   0.509 |             4   |           15488 |                3195 |
| mav_gpqa         | ✅                 |   0.361 |             4.9 |           12381 |                1820 |
| mav_gpqa         | &#x274C;           |   0.596 |            10   |           14569 |                4938 |
| self_consistency | ✅                 |   0.565 |             6   |           14147 |                4988 |
| self_consistency | &#x274C;           |   0.639 |             6   |            6543 |                5439 |

### GSM-Hard / devstral-small-2 (N=500)

| mas_method       | cedrus-mcp              |   score |   num_llm_calls |   prompt_tokens |   completion_tokens |
|:-----------------|:------------------------|--------:|----------------:|----------------:|--------------------:|
| agentverse_mgsm  | &#x274C;                |   0.552 |             7.2 |            9117 |                1920 |
| agentverse_mgsm  | ✅ (all agents)         |   0.719 |            10.3 |           28022 |                2665 |
| agentverse_mgsm  | ✅ (some agents)        |   0.582 |             6.9 |           12600 |                1674 |
| camel            | ✅                      |   0.017 |            12.9 |           39723 |                2825 |
| camel            | &#x274C;                |   0.035 |            13   |           19782 |                3225 |
| cot              | ✅                      |   0.163 |             1   |            1469 |                 265 |
| cot              | &#x274C;                |   0.685 |             1   |              85 |                 665 |
| dylan            | ✅                      |   0.615 |            10.6 |           22085 |                4771 |
| dylan            | &#x274C;                |   0.537 |            10.5 |            8331 |                5747 |
| llm_debate       | ✅                      |   0.62  |             7   |           15202 |                2644 |
| llm_debate       | &#x274C;                |   0.655 |             7   |            6782 |                2839 |
| mad              | ✅                      |   0.065 |             2.7 |            9115 |                 855 |
| mad              | &#x274C;                |   0.057 |             4.2 |           11284 |                2057 |
| mav              | ✅                      |   0.492 |             7.8 |           15595 |                1612 |
| mav              | &#x274C;                |   0.278 |            10   |            4382 |                1760 |
| self_consistency | ✅                      |   0.577 |             6   |           10637 |                2197 |
| self_consistency | &#x274C;                |   0.672 |             6   |            3075 |                2783 |

### GSM8K / devstral-small-2 (N=500)

| mas_method       | cedrus-mcp              |   score |   num_llm_calls |   prompt_tokens |   completion_tokens |
|:-----------------|:------------------------|--------:|----------------:|----------------:|--------------------:|
| agentverse_mgsm  | &#x274C;                |   0.937 |             4.8 |            4467 |                 769 |
| agentverse_mgsm  | ✅ (all agents)         |   0.903 |             7.4 |           18185 |                1443 |
| agentverse_mgsm  | ✅ (some agents)        |   0.939 |             4.7 |            6875 |                 728 |
| camel            | ✅                      |   0     |            12.9 |           38057 |                2763 |
| camel            | &#x274C;                |   0.071 |            13   |           18880 |                2902 |
| cot              | ✅                      |   0.325 |             1   |            1465 |                 243 |
| cot              | &#x274C;                |   0.942 |             1   |              81 |                 354 |
| dylan            | ✅                      |   0.826 |            10.7 |           20876 |                3890 |
| dylan            | &#x274C;                |   0.855 |            10.6 |            6976 |                4219 |
| llm_debate       | ✅                      |   0.836 |             7   |           14027 |                1951 |
| llm_debate       | &#x274C;                |   0.941 |             7   |            4497 |                1798 |
| mad              | ✅                      |   0.075 |             2.5 |            7655 |                 666 |
| mad              | &#x274C;                |   0.08  |             4.3 |            7592 |                1575 |
| mav              | ✅                      |   0.717 |             6.8 |           13249 |                1255 |
| mav              | &#x274C;                |   0.417 |            10   |            3984 |                1491 |
| self_consistency | ✅                      |   0.858 |             6   |           10130 |                1652 |
| self_consistency | &#x274C;                |   0.954 |             6   |            2067 |                1735 |

### MATH / devstral-small-2 (N=198-500)

| mas_method       | cedrus-mcp         | score   |   num_llm_calls |   prompt_tokens |   completion_tokens |
|:-----------------|:-------------------|:--------|----------------:|----------------:|--------------------:|
| agentverse       | ✅ (all agents)     | 0.806   |             6   |           19320 |                2151 |
| agentverse       | ✅ (some agents)   | 0.859   |             4.8 |           13325 |                2072 |
| agentverse       | &#x274C;           | 0.863   |             6   |           15225 |                3192 |
| camel            | ✅                 | 0.000   |            13   |           49548 |                3905 |
| camel            | &#x274C;           | 0.039   |            13   |           28855 |                4166 |
| cot              | ✅                 | 0.307   |             1   |            1472 |                 447 |
| cot              | &#x274C;           | 0.860   |             1   |              88 |                1456 |
| dylan_math       | &#x274C;           | 0.920   |             3.9 |           13484 |                4485 |
| dylan_math       | ✅                 | 0.742   |             5.8 |           26668 |                3892 |
| llm_debate       | ✅                 | 0.786   |             7   |           21442 |                5181 |
| llm_debate       | &#x274C;           | 0.926   |             7   |           15105 |                6113 |
| mad              | ✅                 | 0.186   |             1.4 |            5877 |                 747 |
| mad              | &#x274C;           |         |             0   |               0 |                   0 |
| mav_math         | ✅                 | 0.768   |             5.2 |           12940 |                1787 |
| mav_math         | &#x274C;           | 0.900   |            10   |           15233 |                4924 |
| self_consistency | ✅                 | 0.819   |             6   |           13510 |                5095 |
| self_consistency | &#x274C;           | 0.950   |             6   |            7296 |                7013 |

### MMLU / devstral-small-2 (N=500)

| mas_method       | cedrus-mcp         |   score |   num_llm_calls |   prompt_tokens |   completion_tokens |
|:-----------------|:-------------------|--------:|----------------:|----------------:|--------------------:|
| agentverse       | ✅ (all agents)    |   0.786 |             4.9 |           12368 |                1084 |
| agentverse       | ✅ (some agents)   |   0.8   |             4.4 |           10156 |                1678 |
| agentverse       | &#x274C;           |   0.792 |             4.6 |            7119 |                1584 |
| camel            | ✅                 |   0.015 |            13   |           43383 |                3416 |
| camel            | &#x274C;           |   0.048 |            13   |           29886 |                4354 |
| cot              | ✅                 |   0.388 |             1   |            1534 |                 250 |
| cot              | &#x274C;           |   0.761 |             1   |             150 |                 455 |
| dylan_mmlu       | &#x274C;           |   0.302 |             8.7 |            1975 |                3459 |
| dylan_mmlu       | ✅                 |   0.185 |             8.8 |           14060 |                3026 |
| llm_debate       | ✅                 |   0.707 |             7   |           15708 |                2487 |
| llm_debate       | &#x274C;           |   0.823 |             7   |            5366 |                2005 |
| mad              | ✅                 |   0.338 |             2.7 |            9427 |                 869 |
| mad              | &#x274C;           |   0.265 |             4.1 |            9378 |                1808 |
| mav_mmlu         | ✅                 |   0.561 |             9.2 |           19100 |                1761 |
| mav_mmlu         | &#x274C;           |   0.794 |            10   |            6320 |                1421 |
| self_consistency | ✅                 |   0.646 |             6   |           10984 |                2095 |
| self_consistency | &#x274C;           |   0.806 |             6   |            2118 |                1411 |

### MMLU-Pro / devstral-small-2 (N=500)

| mas_method       | cedrus-mcp         |   score |   num_llm_calls |   prompt_tokens |   completion_tokens |
|:-----------------|:-------------------|--------:|----------------:|----------------:|--------------------:|
| agentverse       | ✅ (all agents)    |   0.648 |             6.1 |           19575 |                2032 |
| agentverse       | ✅ (some agents)   |   0.698 |             4.9 |           13911 |                2216 |
| agentverse       | &#x274C;           |   0.738 |             5.8 |           14386 |                2975 |
| camel            | ✅                 |   0     |            13   |           45166 |                3599 |
| camel            | &#x274C;           |   0.018 |            13   |           29006 |                4379 |
| cot              | ✅                 |   0.379 |             1   |            1604 |                 482 |
| cot              | &#x274C;           |   0.765 |             1   |             220 |                 838 |
| llm_debate       | ✅                 |   0.624 |             7   |           19097 |                3717 |
| llm_debate       | &#x274C;           |   0.726 |             7   |            8864 |                3216 |
| mad              | ✅                 |   0.157 |             2.2 |            9101 |                 952 |
| mad              | &#x274C;           |   0.177 |             4.2 |           13723 |                2567 |
| self_consistency | ✅                 |   0.55  |             6   |           12471 |                3231 |
| self_consistency | &#x274C;           |   0.708 |             6   |            4134 |                3026 |

### MedMCQA / devstral-small-2 (N=500)

| mas_method       | cedrus-mcp         |   score |   num_llm_calls |   prompt_tokens |   completion_tokens |
|:-----------------|:-------------------|--------:|----------------:|----------------:|--------------------:|
| agentverse       | ✅ (all agents)    |   0.729 |             5.4 |           13476 |                1243 |
| agentverse       | ✅ (some agents)   |   0.681 |             4.7 |            9457 |                1492 |
| agentverse       | &#x274C;           |   0.681 |             4.9 |            7998 |                1891 |
| camel            | ✅                 |   0     |            13   |           45758 |                3378 |
| camel            | &#x274C;           |   0     |            13   |           32389 |                5061 |
| cot              | ✅                 |   1     |             1   |            1461 |                 254 |
| cot              | &#x274C;           |   0.667 |             1   |              77 |                 379 |
| dylan            | ✅                 |   0.586 |            11   |           22807 |                4650 |
| dylan            | &#x274C;           |   0.593 |            10.9 |            8503 |                5160 |
| llm_debate       | ✅                 |   0.686 |             7   |           14176 |                2146 |
| llm_debate       | &#x274C;           |   0.717 |             7   |            4222 |                1809 |
| mad              | ✅                 |   0.217 |             2.2 |            7150 |                 604 |
| mad              | &#x274C;           |   0.231 |             4.5 |           10705 |                2120 |
| mav              | ✅                 |   0.577 |             8.5 |           15349 |                1387 |
| mav              | &#x274C;           |   0.618 |            10   |            4307 |                1930 |
| self_consistency | ✅                 |   0.603 |             6   |           10138 |                1751 |
| self_consistency | &#x274C;           |   0.648 |             6   |            1572 |                1310 |

### MedQA / devstral-small-2 (N=500)

| mas_method       | cedrus-mcp         |   score |   num_llm_calls |   prompt_tokens |   completion_tokens |
|:-----------------|:-------------------|--------:|----------------:|----------------:|--------------------:|
| agentverse       | ✅ (all agents)    |   0.835 |             6.3 |           19557 |                2041 |
| agentverse       | ✅ (some agents)   |   0.714 |             4.7 |           11690 |                1938 |
| agentverse       | &#x274C;           |   0.682 |             5.1 |           10677 |                2392 |
| camel            | ✅                 |   0.017 |            13   |           42895 |                3360 |
| camel            | &#x274C;           |   0     |            13   |           35090 |                5456 |
| cot              | ✅                 |   0.454 |             1   |            1622 |                 474 |
| cot              | &#x274C;           |   0.89  |             1   |             238 |                 617 |
| dylan            | ✅                 |   0.765 |            11   |           27140 |                6797 |
| dylan            | &#x274C;           |   0.648 |            10.9 |           13233 |                7878 |
| llm_debate       | ✅                 |   0.703 |             7   |           18816 |                3688 |
| llm_debate       | &#x274C;           |   0.854 |             7   |            8476 |                3124 |
| mad              | ✅                 |   0.244 |             1.7 |            7254 |                 729 |
| mad              | &#x274C;           |   0.277 |             4   |           11026 |                2292 |
| mav              | ✅                 |   0.714 |             9.5 |           19422 |                2043 |
| mav              | &#x274C;           |   0.72  |            10   |            6622 |                2622 |
| self_consistency | ✅                 |   0.684 |             6   |           12240 |                2969 |
| self_consistency | &#x274C;           |   0.846 |             6   |            3563 |                2415 |

### SciBench / devstral-small-2 (N=499)

| mas_method       | cedrus-mcp         |   score |   num_llm_calls |   prompt_tokens |   completion_tokens |
|:-----------------|:-------------------|--------:|----------------:|----------------:|--------------------:|
| agentverse       | ✅ (all agents)    |   0.553 |             6.2 |           23166 |                2815 |
| agentverse       | ✅ (some agents)   |   0.604 |             4.6 |           15432 |                2525 |
| agentverse       | &#x274C;           |   0.534 |             5.3 |           14242 |                3000 |
| camel            | ✅                 |   0     |            13   |           54846 |                4139 |
| camel            | &#x274C;           |   0     |            13   |           30521 |                4692 |
| cot              | ✅                 |   0.143 |             1   |            1491 |                 527 |
| cot              | &#x274C;           |   0.4   |             1   |             107 |                1223 |
| dylan            | ✅                 |   0.416 |            10.8 |           29558 |                9603 |
| dylan            | &#x274C;           |   0.353 |            10.8 |           16729 |               11466 |
| llm_debate       | ✅                 |   0.415 |             7   |           20569 |                5305 |
| llm_debate       | &#x274C;           |   0.51  |             7   |           12640 |                5708 |
| mad              | ✅                 |   0.017 |             1.5 |            6955 |                 831 |
| mad              | &#x274C;           |   0.058 |             2.5 |           10966 |                2526 |
| mav              | ✅                 |   0.349 |             6.2 |           13621 |                1705 |
| mav              | &#x274C;           |   0.253 |            10   |            7673 |                4377 |
| self_consistency | ✅                 |   0.433 |             6   |           13145 |                4879 |
| self_consistency | &#x274C;           |   0.467 |             6   |            5519 |                5456 |
