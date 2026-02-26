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


### cedrus-mcp Configurations

* ✅✋⏭️: cedrus-mcp server available for **all agents**, system prompt instructs to make **discretionay use** 
* ✅☝️⏭️: cedrus-mcp server available for **selected agents**, system prompt instructs to make **discretionay use** 
* ✅✋⏩️: cedrus-mcp server available for **all agents**, system prompt instructs to **always use** argument mapping
* ✅☝️⏩️: cedrus-mcp server available for **selected agents**, system prompt instructs to **always use** argument mapping
* ✅⏭️: cedrus-mcp server available, system prompt instructs to make **discretionay use** 
* ✅⏩️: cedrus-mcp server available, system prompt instructs to **always use** argument mapping
* &#x274C;: no cedrus-mcp server available for any agents


### AIME-2024 / devstral-small-2 (N=30)

| mas_method       | cedrus-mcp             |   score |   num_llm_calls |   prompt_tokens |   completion_tokens |   num_tool_calls |
|:-----------------|:-----------------------|--------:|----------------:|----------------:|--------------------:|-----------------:|
| agentverse       | ✅✋⏭️                |   0.300 |             8.3 |           43376 |                6386 |              2.2 |
| agentverse       | ✅✋⏩️                |   0.200 |             9.7 |           53042 |                7156 |              3   |
| agentverse       | ✅☝️⏭️                |   0.345 |             7.6 |           35650 |                6664 |              0   |
| agentverse       | ✅☝️⏩️                |   0.429 |             7.6 |           36394 |                6488 |              0   |
| agentverse       | &#x274C;               |   0.357 |             6.7 |           31180 |                7807 |              0   |
| camel            | ✅⏭️                  |   0.000 |            13   |          103826 |                5887 |              2.5 |
| camel            | ✅⏩️                  |   0.000 |            13   |           98208 |                5635 |              2.5 |
| camel            | &#x274C;               |   0.000 |            12.9 |          127803 |                9469 |              0   |
| cot              | ✅⏭️                  |   0.300 |             1   |            4392 |                2255 |              2.1 |
| cot              | ✅⏩️                  |   0.133 |             1   |           10024 |                1931 |              6.3 |
| cot              | &#x274C;               |   0.500 |             1   |             116 |                4246 |              0   |
| dylan            | ✅⏭️                  |   0.448 |            10.6 |           83330 |               29112 |              7.6 |
| dylan            | ✅⏩️                  |   0.379 |            10.6 |          109558 |               29086 |             14.4 |
| dylan            | &#x274C;               |   0.400 |            11   |           64907 |               34801 |              0   |
| llm_debate       | ✅⏭️                  |   0.467 |             7   |           51143 |               16763 |              0.5 |
| llm_debate       | ✅⏩️                  |   0.367 |             7   |           56492 |               16498 |              4.6 |
| llm_debate       | &#x274C;               |   0.567 |             7   |           43309 |               17911 |              0   |
| mad              | ✅⏭️                  |   0.000 |             2.1 |           44162 |                3860 |              1   |
| mad              | ✅⏩️                  |   0.364 |             1.3 |            9114 |                1663 |              2.7 |
| mad              | &#x274C;               |   0.207 |             3.2 |           28543 |                7301 |              0   |
| mav              | ✅⏭️                  |   0.231 |             8.7 |           63134 |                5427 |             31.9 |
| mav              | ✅⏩️                  |   0.148 |             9   |          101573 |                7459 |             81.7 |
| mav              | &#x274C;               |   0.133 |            10   |           14332 |                8486 |              0   |
| self_consistency | ✅⏭️                  |   0.467 |             6   |           27678 |               19293 |              0   |
| self_consistency | ✅⏩️                  |   0.467 |             6   |           29928 |               17616 |              3.1 |
| self_consistency | &#x274C;               |   0.400 |             6   |           23079 |               22902 |              0   |

### AIME-2025 / devstral-small-2 (N=30)

| mas_method       | cedrus-mcp             |   score |   num_llm_calls |   prompt_tokens |   completion_tokens |   num_tool_calls |
|:-----------------|:-----------------------|--------:|----------------:|----------------:|--------------------:|-----------------:|
| agentverse       | ✅✋⏭️                |   0.214 |             9.2 |           41361 |                5810 |              1   |
| agentverse       | ✅✋⏩️                |   0.148 |             8.6 |           46358 |                5415 |              3.4 |
| agentverse       | ✅☝️⏭️                |   0.214 |             8.7 |           38884 |                6939 |              0   |
| agentverse       | ✅☝️⏩️                |   0.276 |             7.2 |           33818 |                6359 |              0   |
| agentverse       | &#x274C;               |   0.233 |             8   |           29021 |                6838 |              0   |
| camel            | ✅⏭️                  |   0.000 |            13   |           84265 |                4778 |              2.1 |
| camel            | ✅⏩️                  |   0.000 |            13   |           80218 |                5072 |              2.2 |
| camel            | &#x274C;               |   0.000 |            13   |           64172 |                6008 |              0   |
| cot              | ✅⏭️                  |   0.133 |             1   |            5937 |                2223 |              2.2 |
| cot              | ✅⏩️                  |   0.100 |             1   |            9280 |                2493 |              4.7 |
| cot              | &#x274C;               |   0.267 |             1   |             203 |                4009 |              0   |
| dylan            | ✅⏭️                  |   0.200 |            10.9 |           97043 |               29451 |             11.4 |
| dylan            | ✅⏩️                  |   0.276 |            10.6 |          113387 |               27367 |             16.7 |
| dylan            | &#x274C;               |   0.300 |            10.9 |           79759 |               33021 |              0   |
| llm_debate       | ✅⏭️                  |   0.300 |             7   |           50199 |               16517 |              0.8 |
| llm_debate       | ✅⏩️                  |   0.370 |             6.3 |           54405 |               14188 |              4.6 |
| llm_debate       | &#x274C;               |   0.333 |             7   |           45480 |               18400 |              0   |
| mad              | ✅⏭️                  |   0.000 |             2.6 |           40025 |                3980 |              1.3 |
| mad              | ✅⏩️                  |   0.000 |             2.4 |           37855 |                3560 |              1.9 |
| mad              | &#x274C;               |   0.045 |             3.8 |           81026 |                7023 |              0   |
| mav              | ✅⏭️                  |   0.148 |             9   |           85771 |                5640 |             51.4 |
| mav              | ✅⏩️                  |   0.130 |             7.7 |           81313 |                4751 |             64   |
| mav              | &#x274C;               |   0.067 |            10   |           15044 |                8913 |              0   |
| self_consistency | ✅⏭️                  |   0.300 |             6   |           27648 |               18538 |              0   |
| self_consistency | ✅⏩️                  |   0.300 |             6   |           25806 |               15841 |              1   |
| self_consistency | &#x274C;               |   0.367 |             6   |           22985 |               22481 |              0   |

### APEX-SHORTLIST / devstral-small-2 (N=49)

| mas_method       | cedrus-mcp             |   score |   num_llm_calls |   prompt_tokens |   completion_tokens |   num_tool_calls |
|:-----------------|:-----------------------|--------:|----------------:|----------------:|--------------------:|-----------------:|
| agentverse       | ✅✋⏭️                |   0.061 |             9.5 |           37133 |                4745 |              0.7 |
| agentverse       | ✅✋⏩️                |   0.022 |             8.3 |           34282 |                4446 |              5.9 |
| agentverse       | ✅☝️⏭️                |   0.042 |             8.7 |           31781 |                5415 |              0.5 |
| agentverse       | ✅☝️⏩️                |   0.061 |             8.9 |           33064 |                5671 |              0   |
| agentverse       | &#x274C;               |   0.000 |             9.8 |           30228 |                6993 |              0   |
| camel            | ✅⏭️                  |   0.000 |            12.5 |           80141 |                5036 |              2.5 |
| camel            | ✅⏩️                  |   0.000 |            11.4 |           78440 |                4214 |              4.8 |
| camel            | &#x274C;               |   0.020 |            13   |           54843 |                6147 |              0   |
| cot              | ✅⏭️                  |   0.061 |             1   |            3651 |                2368 |              1.1 |
| cot              | ✅⏩️                  |   0.082 |             1   |            7691 |                1648 |              3.9 |
| cot              | &#x274C;               |   0.077 |             1   |             170 |                3821 |              0   |
| dylan            | ✅⏭️                  |   0.021 |            10.4 |           65278 |               22654 |              6.9 |
| dylan            | ✅⏩️                  |   0.062 |            10.7 |           85219 |               23197 |             12.1 |
| dylan            | &#x274C;               |   0.083 |            10.8 |           55554 |               30511 |              0   |
| llm_debate       | ✅⏭️                  |   0.082 |             7   |           44026 |               14007 |              0.9 |
| llm_debate       | ✅⏩️                  |   0.042 |             6.9 |           45430 |               14026 |              2   |
| llm_debate       | &#x274C;               |   0.122 |             7   |           36477 |               14027 |              0   |
| mad              | ✅⏭️                  |   0.000 |             1.2 |           21315 |                1922 |              1.2 |
| mad              | ✅⏩️                  |   0.000 |             0.9 |           11320 |                 864 |              1.1 |
| mad              | &#x274C;               |   0.000 |             2.6 |           55690 |                4276 |              0   |
| mav              | ✅⏭️                  |   0.156 |             9.2 |           77391 |                4732 |             40.3 |
| mav              | ✅⏩️                  |   0.087 |             9.4 |           80777 |                4906 |             63.3 |
| mav              | &#x274C;               |   0.020 |            10   |           10386 |                5880 |              0   |
| self_consistency | ✅⏭️                  |   0.122 |             6   |           23399 |               14830 |              0   |
| self_consistency | ✅⏩️                  |   0.082 |             6   |           24643 |               11013 |              2.5 |
| self_consistency | &#x274C;               |   0.061 |             6   |           19783 |               19082 |              0   |

### AQUA-RAT / devstral-small-2 (N=254)

| mas_method       | cedrus-mcp             |   score |   num_llm_calls |   prompt_tokens |   completion_tokens |   num_tool_calls |
|:-----------------|:-----------------------|--------:|----------------:|----------------:|--------------------:|-----------------:|
| agentverse       | ✅✋⏭️                |   0.83  |             5.8 |           22963 |                1941 |              4.8 |
| agentverse       | ✅✋⏩️                |   0.818 |             5.5 |           35931 |                2005 |             13.4 |
| agentverse       | ✅☝️⏭️                |   0.824 |             5.6 |           14090 |                2379 |              0.1 |
| agentverse       | ✅☝️⏩️                |   0.867 |             5.6 |           15050 |                2311 |              0.6 |
| agentverse       | &#x274C;               |   0.844 |             6.3 |           13276 |                2829 |              0   |
| camel            | ✅⏭️                  |   0.115 |            12.5 |           69870 |                4268 |             14.6 |
| camel            | ✅⏩️                  |   0.077 |            11.9 |           70841 |                4102 |             16.7 |
| camel            | &#x274C;               |   0.078 |            12.9 |           29989 |                4491 |              0   |
| cot              | ✅⏭️                  |   0.821 |             1   |            9437 |                 657 |              6.3 |
| cot              | ✅⏩️                  |   0.840 |             1   |           16032 |                 739 |             10.5 |
| cot              | &#x274C;               |   0.893 |             1   |             108 |                 923 |              0   |
| dylan            | ✅⏭️                  |   0.763 |            10.6 |           38639 |                6583 |             11.2 |
| dylan            | ✅⏩️                  |   0.840 |            10.4 |           49080 |                6504 |             18.8 |
| dylan            | &#x274C;               |   0.753 |            10.6 |           13515 |                8372 |              0   |
| llm_debate       | ✅⏭️                  |   0.887 |             7   |           24169 |                3445 |              5.6 |
| llm_debate       | ✅⏩️                  |   0.899 |             6.9 |           38845 |                3738 |             18.1 |
| llm_debate       | &#x274C;               |   0.864 |             7   |            8947 |                3441 |              0   |
| mad              | ✅⏭️                  |   0.204 |             2.4 |           20227 |                1145 |              6.7 |
| mad              | ✅⏩️                  |   0.327 |             2.5 |           27378 |                1294 |             11   |
| mad              | &#x274C;               |   0.207 |             3.5 |            9559 |                2263 |              0   |
| mav              | ✅⏭️                  |   0.861 |            10   |           29522 |                2760 |             10.5 |
| mav              | ✅⏩️                  |   0.814 |             9.9 |           59323 |                3524 |             48.2 |
| mav              | &#x274C;               |   0.484 |            10   |            5588 |                2760 |              0   |
| self_consistency | ✅⏭️                  |   0.897 |             6   |           18606 |                3062 |              5.9 |
| self_consistency | ✅⏩️                  |   0.880 |             6   |           29743 |                3104 |             14   |
| self_consistency | &#x274C;               |   0.907 |             6   |            4953 |                4451 |              0   |

### GPQA / devstral-small-2 (N=448)

| mas_method       | cedrus-mcp             |   score |   num_llm_calls |   prompt_tokens |   completion_tokens |   num_tool_calls |
|:-----------------|:-----------------------|--------:|----------------:|----------------:|--------------------:|-----------------:|
| agentverse       | ✅✋⏭️                |   0.537 |             6.4 |           24580 |                2691 |              1.3 |
| agentverse       | ✅✋⏩️                |   0.487 |             6.2 |           38969 |                2731 |             10   |
| agentverse       | ✅☝️⏭️                |   0.536 |             5.8 |           18219 |                3136 |              0   |
| agentverse       | ✅☝️⏩️                |   0.519 |             5.9 |           18761 |                3134 |              0.3 |
| agentverse       | &#x274C;               |   0.525 |             6.3 |           16003 |                3524 |              0   |
| camel            | ✅⏭️                  |   0.000 |            12.2 |           66733 |                4265 |              8.9 |
| camel            | ✅⏩️                  |   0.000 |            11.6 |           67547 |                4073 |             11.1 |
| camel            | &#x274C;               |   0.000 |            13   |           34995 |                5401 |              0   |
| cot              | ✅⏭️                  |   0.557 |             1   |            7470 |                1044 |              4.7 |
| cot              | ✅⏩️                  |   0.556 |             1   |           13741 |                1078 |             10   |
| cot              | &#x274C;               |   0.467 |             1   |             224 |                1261 |              0   |
| dylan            | ✅⏭️                  |   0.475 |            10.8 |           48438 |               10575 |             10.9 |
| dylan            | ✅⏩️                  |   0.508 |            10.6 |           61422 |               10413 |             19.5 |
| dylan            | &#x274C;               |   0.456 |            10.9 |           19818 |               12163 |              0   |
| llm_debate       | ✅⏭️                  |   0.549 |             7   |           32218 |                5649 |              7.6 |
| llm_debate       | ✅⏩️                  |   0.525 |             6.9 |           53663 |                5794 |             23.1 |
| llm_debate       | &#x274C;               |   0.575 |             7   |           13185 |                5153 |              0   |
| mad              | ✅⏭️                  |   0.419 |             2.3 |           19098 |                1617 |              3.2 |
| mad              | ✅⏩️                  |   0.432 |             2.3 |           26282 |                1636 |              8.9 |
| mad              | &#x274C;               |   0.369 |             4   |           14498 |                3142 |              0   |
| mav_gpqa         | ✅⏭️                  |   0.510 |             9.9 |           80537 |                5181 |             51.9 |
| mav_gpqa         | ✅⏩️                  |   0.504 |             9.8 |          111760 |                6265 |             91.1 |
| mav_gpqa         | &#x274C;               |   0.560 |            10   |           13337 |                4280 |              0   |
| self_consistency | ✅⏭️                  |   0.649 |             6   |           21241 |                4877 |              5.4 |
| self_consistency | ✅⏩️                  |   0.573 |             6   |           38815 |                5244 |             19.4 |
| self_consistency | &#x274C;               |   0.574 |             6   |            6180 |                5128 |              0   |

### GPQA-Diamond / devstral-small-2 (N=198)

| mas_method       | cedrus-mcp             |   score |   num_llm_calls |   prompt_tokens |   completion_tokens |   num_tool_calls |
|:-----------------|:-----------------------|--------:|----------------:|----------------:|--------------------:|-----------------:|
| agentverse       | ✅✋⏭️                |   0.571 |             6.4 |           26282 |                2772 |              2   |
| agentverse       | ✅✋⏩️                |   0.574 |             6.4 |           39419 |                2704 |              9.5 |
| agentverse       | ✅☝️⏭️                |   0.550 |             5.6 |           16989 |                2964 |              0   |
| agentverse       | ✅☝️⏩️                |   0.464 |             6.1 |           18429 |                3040 |              0.1 |
| agentverse       | &#x274C;               |   0.545 |             6.5 |           15589 |                3380 |              0   |
| camel            | ✅⏭️                  |   0.000 |            12.3 |           72381 |                4439 |              9.5 |
| camel            | ✅⏩️                  |   0.000 |            11.9 |           78075 |                4227 |             13   |
| camel            | &#x274C;               |   0.000 |            13   |           46762 |                5939 |              0   |
| cot              | ✅⏭️                  |   0.437 |             1   |            6624 |                1003 |              4.3 |
| cot              | ✅⏩️                  |   0.600 |             1   |           13271 |                1089 |              9.8 |
| cot              | &#x274C;               |   0.564 |             1   |             232 |                1247 |              0   |
| dylan            | ✅⏭️                  |   0.556 |            10.8 |           45243 |               10595 |              9.4 |
| dylan            | ✅⏩️                  |   0.533 |            10.8 |           61351 |               11066 |             19.3 |
| dylan            | &#x274C;               |   0.417 |            10.9 |           20594 |               12548 |              0   |
| llm_debate       | ✅⏭️                  |   0.598 |             6.9 |           32136 |                5523 |              6.7 |
| llm_debate       | ✅⏩️                  |   0.614 |             6.9 |           57384 |                6243 |             23.9 |
| llm_debate       | &#x274C;               |   0.619 |             7   |           13656 |                5263 |              0   |
| mad              | ✅⏭️                  |   0.382 |             2.3 |           18310 |                1578 |              3.4 |
| mad              | ✅⏩️                  |   0.272 |             2.4 |           27731 |                1689 |              8.3 |
| mad              | &#x274C;               |   0.509 |             4   |           15488 |                3195 |              0   |
| mav_gpqa         | ✅⏭️                  |   0.556 |            10   |           69137 |                5713 |             41.2 |
| mav_gpqa         | ✅⏩️                  |   0.524 |             9.5 |          117189 |                5726 |             95.5 |
| mav_gpqa         | &#x274C;               |   0.596 |            10   |           14569 |                4938 |              0   |
| self_consistency | ✅⏭️                  |   0.518 |             6   |           20015 |                4981 |              4.3 |
| self_consistency | ✅⏩️                  |   0.604 |             6   |           37878 |                5186 |             17.4 |
| self_consistency | &#x274C;               |   0.639 |             6   |            6543 |                5439 |              0   |

### GSM-Hard / devstral-small-2 (N=500)

| mas_method       | mas_config                  |   score |   num_llm_calls |   prompt_tokens |   completion_tokens |   num_tool_calls |
|:-----------------|:----------------------------|--------:|----------------:|----------------:|--------------------:|-----------------:|
| agentverse_mgsm  | &#x274C;                    |   0.552 |             7.2 |            9117 |                1920 |              0   |
| agentverse_mgsm  | ✅✋⏭️                     |   0.719 |            10.3 |           28022 |                2665 |              0   |
| agentverse_mgsm  | ✅✋⏩️                     |   0.597 |             6.5 |           49439 |                2233 |             22.2 |
| agentverse_mgsm  | ✅☝️⏭️                     |   0.582 |             6.9 |           12600 |                1674 |              0   |
| agentverse_mgsm  | ✅☝️⏩️                     |   0.592 |             7.3 |           13012 |                1774 |              0   |
| camel            | ✅⏭️                       |   0.016 |            12.6 |           51121 |                3284 |             10   |
| camel            | ✅⏩️                       |   0.016 |            12.2 |           59462 |                3464 |             14.3 |
| camel            | &#x274C;                    |   0.035 |            13   |           19782 |                3225 |              0   |
| cot              | ✅⏭️                       |   0.659 |             1   |           14237 |                 623 |             10.2 |
| cot              | ✅⏩️                       |   0.550 |             1   |           18318 |                 696 |             12.8 |
| cot              | &#x274C;                    |   0.685 |             1   |              85 |                 665 |              0   |
| dylan            | ✅⏭️                       |   0.656 |            10.6 |           44598 |                5310 |             18.3 |
| dylan            | ✅⏩️                       |   0.558 |            10.6 |           52630 |                5256 |             25.5 |
| dylan            | &#x274C;                    |   0.537 |            10.5 |            8331 |                5747 |              0   |
| llm_debate       | ✅⏭️                       |   0.665 |             7   |           23456 |                2796 |              7.4 |
| llm_debate       | ✅⏩️                       |   0.667 |             7   |           39696 |                3094 |             21.1 |
| llm_debate       | &#x274C;                    |   0.655 |             7   |            6782 |                2839 |              0   |
| mad              | ✅⏭️                       |   0.056 |             3.3 |           25329 |                1422 |              9.1 |
| mad              | ✅⏩️                       |   0.076 |             3.6 |           35374 |                1758 |             15.3 |
| mad              | &#x274C;                    |   0.057 |             4.2 |           11284 |                2057 |              0   |
| mav              | ✅⏭️                       |   0.561 |            10   |           38229 |                2888 |             21.5 |
| mav              | ✅⏩️                       |   0.584 |            10   |           87233 |                3810 |             70.6 |
| mav              | &#x274C;                    |   0.278 |            10   |            4382 |                1760 |              0   |
| self_consistency | ✅⏭️                       |   0.674 |             6   |           22293 |                2391 |              9.8 |
| self_consistency | ✅⏩️                       |   0.697 |             6   |           41514 |                2726 |             25.3 |
| self_consistency | &#x274C;                    |   0.672 |             6   |            3075 |                2783 |              0   |

### GSM8K / devstral-small-2 (N=103-500)

| mas_method       | mas_config                  | score   |   num_llm_calls |   prompt_tokens |   completion_tokens |   num_tool_calls |
|:-----------------|:----------------------------|:--------|----------------:|----------------:|--------------------:|-----------------:|
| agentverse_mgsm  | &#x274C;                    | 0.937   |             4.8 |            4467 |                 769 |              0   |
| agentverse_mgsm  | ✅✋⏭️                     | 0.903   |             7.4 |           18185 |                1443 |              0   |
| agentverse_mgsm  | ✅✋⏩️                     | 0.975   |             4.6 |           31971 |                1273 |             17   |
| agentverse_mgsm  | ✅☝️⏭️                     | 0.939   |             4.7 |            6875 |                 728 |              0   |
| agentverse_mgsm  | ✅☝️⏩️                     | 0.939   |             4.7 |            7336 |                 699 |              0   |
| camel            | ✅⏭️                       | 0.035   |            12.5 |           49678 |                3080 |              8.7 |
| camel            | ✅⏩️                       | 0.000   |            11.9 |           54135 |                3102 |             13.6 |
| camel            | &#x274C;                    | 0.071   |            13   |           18880 |                2902 |              0   |
| cot              | ✅⏭️                       | 0.935   |             1   |           13818 |                 551 |             10.7 |
| cot              | ✅⏩️                       | 0.960   |             1   |           17897 |                 621 |             13.2 |
| cot              | &#x274C;                    | 0.942   |             1   |              81 |                 354 |              0   |
| dylan            | ✅⏭️                       | 0.873   |            10.5 |           40701 |                4185 |             16.4 |
| dylan            | ✅⏩️                       | 0.812   |            10.5 |           45689 |                4208 |             21.4 |
| dylan            | &#x274C;                    | 0.855   |            10.6 |            6976 |                4219 |              0   |
| llm_debate       | ✅⏭️                       | 0.925   |             7   |           23506 |                2158 |              8   |
| llm_debate       | ✅⏩️                       | 0.947   |             7   |           37745 |                2503 |             21.8 |
| llm_debate       | &#x274C;                    | 0.941   |             7   |            4497 |                1798 |              0   |
| mad              | ✅⏭️                       |         |             0   |               0 |                   0 |              0   |
| mad              | ✅⏩️                       |         |             0   |               0 |                   0 |              0   |
| mad              | &#x274C;                    | 0.080   |             4.3 |            7592 |                1575 |              0   |
| mav              | ✅⏭️                       | 0.888   |            10   |           33158 |                2094 |             17.8 |
| mav              | ✅⏩️                       | 0.862   |            10   |           64535 |                2881 |             53.8 |
| mav              | nan                         | 0.417   |            10   |            3984 |                1491 |              0   |
| self_consistency | ✅⏭️                       | 0.927   |             6   |           22910 |                1834 |             10.3 |
| self_consistency | ✅⏩️                       | 0.937   |             6   |           35729 |                2078 |             21.8 |
| self_consistency | nan                         | 0.954   |             6   |            2067 |                1735 |              0   |

### MATH / devstral-small-2 (N=198-500)

| mas_method       | cedrus-mcp             | score   |   num_llm_calls |   prompt_tokens |   completion_tokens |   num_tool_calls |
|:-----------------|:-----------------------|:--------|----------------:|----------------:|--------------------:|-----------------:|
| agentverse       | ✅✋⏭️                | 0.791   |             5.3 |           19833 |                1988 |              1.3 |
| agentverse       | ✅✋⏩️                | 0.859   |             5.7 |           31183 |                2201 |              6.6 |
| agentverse       | ✅☝️⏭️                | 0.826   |             4.8 |           13228 |                2045 |              0   |
| agentverse       | ✅☝️⏩️                | 0.886   |             5.1 |           15144 |                2299 |              0.5 |
| agentverse       | &#x274C;               | 0.863   |             6   |           15225 |                3192 |              0   |
| camel            | ✅⏭️                  | 0.020   |            12.6 |           54577 |                3954 |              3   |
| camel            | ✅⏩️                  | 0.019   |            12.4 |           55285 |                3814 |              4.2 |
| camel            | &#x274C;               | 0.039   |            13   |           28855 |                4166 |              0   |
| cot              | ✅⏭️                  | 0.755   |             1   |            9093 |                 880 |              5.3 |
| cot              | ✅⏩️                  | 0.616   |             1   |           12019 |                 792 |              7.5 |
| cot              | &#x274C;               | 0.860   |             1   |              88 |                1456 |              0   |
| dylan_math       | &#x274C;               | 0.920   |             3.9 |           13484 |                4485 |              0   |
| dylan_math       | ✅⏭️                  | 0.742   |             5.8 |           26668 |                3892 |              0   |
| dylan_math       | ✅⏩️                  | 0.855   |             4.3 |           41180 |                3579 |             11.9 |
| llm_debate       | ✅⏭️                  | 0.911   |             7   |           27033 |                5221 |              4.4 |
| llm_debate       | ✅⏩️                  | 0.895   |             6.9 |           38376 |                5184 |             14   |
| llm_debate       | &#x274C;               | 0.926   |             7   |           15105 |                6113 |              0   |
| mad              | ✅⏭️                  | 0.118   |             1.3 |            8834 |                 714 |              2.2 |
| mad              | ✅⏩️                  |         |             0   |               0 |                   0 |              0   |
| mad              | &#x274C;               |         |             0   |               0 |                   0 |              0   |
| mav_math         | ✅⏭️                  | 0.867   |             8.7 |           73627 |                4705 |             42.9 |
| mav_math         | ✅⏩️                  | 0.842   |             8.5 |           73411 |                4114 |             47.3 |
| mav_math         | &#x274C;               | 0.900   |            10   |           15233 |                4924 |              0   |
| self_consistency | ✅⏭️                  | 0.837   |             6   |           18609 |                5137 |              3.6 |
| self_consistency | ✅⏩️                  | 0.834   |             6   |           29457 |                4724 |             11.9 |
| self_consistency | &#x274C;               | 0.950   |             6   |            7296 |                7013 |              0   |

### MMLU / devstral-small-2 (N=500)

| mas_method       | cedrus-mcp             |   score |   num_llm_calls |   prompt_tokens |   completion_tokens |   num_tool_calls |
|:-----------------|:-----------------------|--------:|----------------:|----------------:|--------------------:|-----------------:|
| agentverse       | ✅✋⏭️                |   0.777 |             4.4 |           12966 |                1010 |              1.1 |
| agentverse       | ✅✋⏩️                |   0.781 |             4.6 |           25444 |                1362 |              9.7 |
| agentverse       | ✅☝️⏭️                |   0.753 |             4.4 |           10268 |                1724 |              0   |
| agentverse       | ✅☝️⏩️                |   0.753 |             4.4 |            9996 |                1641 |              0.2 |
| agentverse       | &#x274C;               |   0.792 |             4.6 |            7119 |                1584 |              0   |
| camel            | ✅⏭️                  |   0.015 |            12.5 |           61093 |                3917 |              9.6 |
| camel            | ✅⏩️                  |   0.03  |            12.1 |           63193 |                3789 |             11.8 |
| camel            | &#x274C;               |   0.048 |            13   |           29886 |                4354 |              0   |
| cot              | ✅⏭️                  |   0.779 |             1   |           11220 |                 598 |              8.3 |
| cot              | ✅⏩️                  |   0.772 |             1   |           15361 |                 671 |             11.5 |
| cot              | &#x274C;               |   0.761 |             1   |             150 |                 455 |              0   |
| dylan_mmlu       | &#x274C;               |   0.302 |             8.7 |            1975 |                3459 |              0   |
| dylan_mmlu       | ✅⏭️                  |   0.185 |             8.8 |           14060 |                3026 |              0   |
| dylan_mmlu       | ✅⏩️                  |   0.246 |             8.3 |           43948 |                3593 |             26.1 |
| llm_debate       | ✅⏭️                  |   0.812 |             7   |           28236 |                2786 |             12.9 |
| llm_debate       | ✅⏩️                  |   0.84  |             7   |           56486 |                3430 |             38.6 |
| llm_debate       | &#x274C;               |   0.823 |             7   |            5366 |                2005 |              0   |
| mad              | ✅⏭️                  |   0.298 |             3   |           20100 |                1191 |              6.7 |
| mad              | ✅⏩️                  |   0.305 |             3   |           27745 |                1363 |             11.9 |
| mad              | &#x274C;               |   0.265 |             4.1 |            9378 |                1808 |              0   |
| mav_mmlu         | ✅⏭️                  |   0.809 |            10   |           51451 |                3149 |             35.5 |
| mav_mmlu         | ✅⏩️                  |   0.805 |             9.9 |           75202 |                3626 |             69.7 |
| mav_mmlu         | &#x274C;               |   0.794 |            10   |            6320 |                1421 |              0   |
| self_consistency | ✅⏭️                  |   0.81  |             6   |           28220 |                2502 |             15.5 |
| self_consistency | ✅⏩️                  |   0.791 |             6   |           58488 |                3243 |             39.8 |
| self_consistency | &#x274C;               |   0.806 |             6   |            2118 |                1411 |              0   |

### MMLU-Pro / devstral-small-2 (N=500)

| mas_method       | cedrus-mcp             |   score |   num_llm_calls |   prompt_tokens |   completion_tokens |   num_tool_calls |
|:-----------------|:-----------------------|--------:|----------------:|----------------:|--------------------:|-----------------:|
| agentverse       | ✅✋⏭️                |   0.584 |             5.6 |           20457 |                1958 |              1.3 |
| agentverse       | ✅✋⏩️                |   0.678 |             5.3 |           32669 |                1942 |              8.5 |
| agentverse       | ✅☝️⏭️                |   0.844 |             5   |           13809 |                2216 |              0   |
| agentverse       | ✅☝️⏩️                |   0.723 |             5.1 |           16024 |                2482 |              0.4 |
| agentverse       | &#x274C;               |   0.738 |             5.8 |           14386 |                2975 |              0   |
| camel            | ✅⏭️                  |   0.000 |            12.6 |           63624 |                3927 |             10.7 |
| camel            | ✅⏩️                  |   0.000 |            11.8 |           65533 |                4097 |             12.1 |
| camel            | &#x274C;               |   0.018 |            13   |           29006 |                4379 |              0   |
| cot              | ✅⏭️                  |   0.694 |             1   |           11917 |                 864 |              7.6 |
| cot              | ✅⏩️                  |   0.659 |             1   |           18858 |                 930 |             12.9 |
| cot              | &#x274C;               |   0.765 |             1   |             220 |                 838 |              0   |
| llm_debate       | ✅⏭️                  |   0.781 |             7   |           31452 |                3977 |             10.1 |
| llm_debate       | ✅⏩️                  |   0.748 |             6.9 |           62955 |                4538 |             35.6 |
| llm_debate       | &#x274C;               |   0.726 |             7   |            8864 |                3216 |              0   |
| mad              | ✅⏭️                  |   0.200 |             2.9 |           19844 |                1516 |              5.1 |
| mad              | ✅⏩️                  |   0.156 |             2.7 |           27423 |                1467 |              9.8 |
| mad              | &#x274C;               |   0.177 |             4.2 |           13723 |                2567 |              0   |
| self_consistency | ✅⏭️                  |   0.72  |             6   |           30385 |                3771 |             14.3 |
| self_consistency | ✅⏩️                  |   0.686 |             6   |           59506 |                4378 |             37.3 |
| self_consistency | &#x274C;               |   0.708 |             6   |            4134 |                3026 |              0   |

### MedMCQA / devstral-small-2 (N=500)

| mas_method       | cedrus-mcp             |   score |   num_llm_calls |   prompt_tokens |   completion_tokens |   num_tool_calls |
|:-----------------|:-----------------------|--------:|----------------:|----------------:|--------------------:|-----------------:|
| agentverse       | ✅✋⏭️                |   0.676 |             4.7 |           14057 |                1091 |              1.6 |
| agentverse       | ✅✋⏩️                |   0.591 |             4.8 |           32557 |                1459 |             14.2 |
| agentverse       | ✅☝️⏭️                |   0.671 |             4.9 |           11880 |                2138 |              0   |
| agentverse       | ✅☝️⏩️                |   0.707 |             4.6 |           10885 |                1874 |              0.1 |
| agentverse       | &#x274C;               |   0.681 |             4.9 |            7998 |                1891 |              0   |
| camel            | ✅⏭️                  |   0.015 |            12.2 |           73567 |                4486 |             16.3 |
| camel            | ✅⏩️                  |   0.000 |            12   |           67433 |                3884 |             15.6 |
| camel            | &#x274C;               |   0.000 |            13   |           32389 |                5061 |              0   |
| cot              | ✅⏭️                  |   0.708 |             1   |            9929 |                 515 |              6.6 |
| cot              | ✅⏩️                  |   0.653 |             1   |           15083 |                 622 |             11.1 |
| cot              | &#x274C;               |   0.667 |             1   |              77 |                 379 |              0   |
| dylan            | ✅⏭️                  |   0.654 |            10.8 |           40467 |                4982 |             14.3 |
| dylan            | ✅⏩️                  |   0.542 |            10.7 |           47899 |                5026 |             20.7 |
| dylan            | &#x274C;               |   0.593 |            10.9 |            8503 |                5160 |              0   |
| llm_debate       | ✅⏭️                  |   0.713 |             7   |           25254 |                2403 |             11.4 |
| llm_debate       | ✅⏩️                  |   0.722 |             7   |           49220 |                3103 |             34.9 |
| llm_debate       | &#x274C;               |   0.717 |             7   |            4222 |                1809 |              0   |
| mad              | ✅⏭️                  |   0.209 |             2.9 |           20452 |                1121 |              6.5 |
| mad              | ✅⏩️                  |   0.206 |             2.9 |           28133 |                1302 |             12.6 |
| mad              | &#x274C;               |   0.231 |             4.5 |           10705 |                2120 |              0   |
| mav              | ✅⏭️                  |   0.597 |            10   |           28087 |                2141 |             12.1 |
| mav              | ✅⏩️                  |   0.591 |            10   |           61854 |                3192 |             60.1 |
| mav              | &#x274C;               |   0.618 |            10   |            4307 |                1930 |              0   |
| self_consistency | ✅⏭️                  |   0.683 |             6   |           23402 |                2046 |             12.3 |
| self_consistency | ✅⏩️                  |   0.701 |             6   |           44884 |                2644 |             31   |
| self_consistency | &#x274C;               |   0.648 |             6   |            1572 |                1310 |              0   |

### MedQA / devstral-small-2 (N=500)

| mas_method       | cedrus-mcp             |   score |   num_llm_calls |   prompt_tokens |   completion_tokens |   num_tool_calls |
|:-----------------|:-----------------------|--------:|----------------:|----------------:|--------------------:|-----------------:|
| agentverse       | ✅✋⏭️                |   0.806 |             4.7 |           22408 |                1546 |              8.4 |
| agentverse       | ✅✋⏩️                |   0.833 |             4.6 |           39382 |                1998 |             23.2 |
| agentverse       | ✅☝️⏭️                |   0.722 |             4.5 |           11220 |                1770 |              0   |
| agentverse       | ✅☝️⏩️                |   0.772 |             4.5 |           10981 |                1701 |              0.2 |
| agentverse       | &#x274C;               |   0.682 |             5.1 |           10677 |                2392 |              0   |
| camel            | ✅⏭️                  |   0.000 |            12.3 |           63333 |                4314 |             10.4 |
| camel            | ✅⏩️                  |   0.000 |            11.8 |           59167 |                3757 |             11   |
| camel            | &#x274C;               |   0.000 |            13   |           35090 |                5456 |              0   |
| cot              | ✅⏭️                  |   0.839 |             1   |           16549 |                 872 |             13.3 |
| cot              | ✅⏩️                  |   0.804 |             1   |           23474 |                 984 |             18.3 |
| cot              | &#x274C;               |   0.89  |             1   |             238 |                 617 |              0   |
| dylan            | ✅⏭️                  |   0.646 |            11   |           51767 |                7171 |             18.9 |
| dylan            | ✅⏩️                  |   0.793 |            10.9 |           62841 |                7177 |             28.8 |
| dylan            | &#x274C;               |   0.648 |            10.9 |           13233 |                7878 |              0   |
| llm_debate       | ✅⏭️                  |   0.796 |             7   |           34239 |                4085 |             16   |
| llm_debate       | ✅⏩️                  |   0.863 |             6.9 |           98648 |                5236 |             69.7 |
| llm_debate       | &#x274C;               |   0.854 |             7   |            8476 |                3124 |              0   |
| mad              | ✅⏭️                  |   0.213 |             2.4 |           19513 |                1225 |              7.3 |
| mad              | ✅⏩️                  |   0.246 |             2.2 |           28097 |                1337 |             14.9 |
| mad              | &#x274C;               |   0.277 |             4   |           11026 |                2292 |              0   |
| mav              | ✅⏭️                  |   0.714 |            10   |           54207 |                3233 |             43.2 |
| mav              | ✅⏩️                  |   0.746 |            10   |           90835 |                4838 |             91   |
| mav              | &#x274C;               |   0.720 |            10   |            6622 |                2622 |              0   |
| self_consistency | ✅⏭️                  |   0.862 |             6   |           37056 |                3582 |             21.8 |
| self_consistency | ✅⏩️                  |   0.829 |             6   |          109720 |                5121 |             79.9 |
| self_consistency | &#x274C;               |   0.846 |             6   |            3563 |                2415 |              0   |

### SciBench / devstral-small-2 (N=499)

| mas_method       | cedrus-mcp             |   score |   num_llm_calls |   prompt_tokens |   completion_tokens |   num_tool_calls |
|:-----------------|:-----------------------|--------:|----------------:|----------------:|--------------------:|-----------------:|
| agentverse       | ✅✋⏭️                |   0.405 |             5.1 |           21110 |                2124 |              1.4 |
| agentverse       | ✅✋⏩️                |   0.397 |             6   |           37558 |                2737 |              9.2 |
| agentverse       | ✅☝️⏭️                |   0.400 |             4.5 |           14329 |                2323 |              0   |
| agentverse       | ✅☝️⏩️                |   0.379 |             4.6 |           15590 |                2423 |              0.8 |
| agentverse       | &#x274C;               |   0.534 |             5.3 |           14242 |                3000 |              0   |
| camel            | ✅⏭️                  |   0.000 |            12.8 |           60760 |                4329 |              4.7 |
| camel            | ✅⏩️                  |   0.000 |            12.3 |           64671 |                4338 |              8.2 |
| camel            | &#x274C;               |   0.000 |            13   |           30521 |                4692 |              0   |
| cot              | ✅⏭️                  |   0.440 |             1   |            8162 |                 916 |              5.1 |
| cot              | ✅⏩️                  |   0.363 |             1   |           12832 |                 932 |              8.4 |
| cot              | &#x274C;               |   0.400 |             1   |             107 |                1223 |              0   |
| dylan            | ✅⏭️                  |   0.438 |            10.8 |           50154 |               10042 |             13.9 |
| dylan            | ✅⏩️                  |   0.352 |            10.6 |           54069 |                9943 |             18.6 |
| dylan            | &#x274C;               |   0.353 |            10.8 |           16729 |               11466 |              0   |
| llm_debate       | ✅⏭️                  |   0.460 |             7   |           27692 |                5519 |              5.2 |
| llm_debate       | ✅⏩️                  |   0.433 |             6.9 |           45597 |                5711 |             17.1 |
| llm_debate       | &#x274C;               |   0.51  |             7   |           12640 |                5708 |              0   |
| mad              | ✅⏭️                  |   0.039 |             1.8 |           14475 |                1219 |              3.1 |
| mad              | ✅⏩️                  |   0.054 |             1.7 |           14358 |                1138 |              3.2 |
| mad              | &#x274C;               |   0.058 |             2.5 |           10966 |                2526 |              0   |
| mav              | ✅⏭️                  |   0.359 |             9.3 |           57132 |                4890 |             36.6 |
| mav              | ✅⏩️                  |   0.410 |             8.3 |           73616 |                3905 |             56.8 |
| mav              | &#x274C;               |   0.253 |            10   |            7673 |                4377 |              0   |
| self_consistency | ✅⏭️                  |   0.494 |             6   |           17243 |                4912 |              2.9 |
| self_consistency | ✅⏩️                  |   0.482 |             6   |           29699 |                5057 |             10.8 |
| self_consistency | &#x274C;               |   0.467 |             6   |            5519 |                5456 |              0   |
