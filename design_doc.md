# KOALA Informal Argument Mapping MCP Server Design Document

## Overview


```python
# RESOURCES - for LLM context/understanding
- argmap://summary                    # describe_argument_map
- argmap://node/{label}               # node details  
- argmap://nodes                      # list all nodes
- argmap://claims                     # list claims only
- argmap://arguments                  # list arguments only
- argmap://argdownmap                 # argdown* representation of map
- argmap://context/{label}/{depth}    # get local context of node 
- argmap://relations/{from}/{to}      # get specific relation
- argmap://checks                     # validation results (cached)

# TOOLS - for modifications
- new_claim()
- new_argument()  
- new_support()
- new_attack()
- delete()
- update_node()
- run_checks()        # expensive computation
- svg_argument_map()  # generates new visualization
- next_issue()        # guides llm to next problem
- review_pending()

# PROMPTS - for guided workflows
- kickoff_reconstruction_project(source_text: str)
- kickoff_debate_generation(topic: str)
```




## Prompts 

```python
@mcp.prompt()
def analyze_argument(argument_label: str) -> str:
    """Generate prompt to analyze argument strength"""
```


## Tools and resources

### Retrieval Resources

Basic retrieval as resources: argument map structure, node details

```python 
@mcp.resource("argmap://summary")
def get_summary(ctx: Context) -> str:
    """Dynamic resource - reads current state from NetworkX graph"""
    arg_map = ctx.request_context.lifespan_context.arg_map
    
    # This data changes every time someone modifies the map!
    return json.dumps({
        "nodes": arg_map.graph.number_of_nodes(),
        "edges": arg_map.graph.number_of_edges(),
        "last_modified": datetime.now().isoformat()
    })

@mcp.resource("argmap://node/{label}")
def get_node_details(label: str, ctx: Context) -> str:
    """Dynamic resource - reads specific node from graph"""
    arg_map = ctx.request_context.lifespan_context.arg_map
    
    node_data = arg_map.graph.nodes[label]
    return json.dumps(node_data)

# ✅ These should be resources - they read from the graph
@mcp.resource("argmap://summary")
def describe_argument_map() -> str:
    """Read-only view of map structure"""

@mcp.resource("argmap://node/{label}")  
def get_node_details(label: str) -> str:
    """Read-only view of specific node"""

@mcp.resource("argmap://nodes")
def list_all_nodes(ctx: Context) -> str:
    """Read-only list of all nodes"""
    arg_map = ctx.request_context.lifespan_context.arg_map
    nodes = [
        {"label": n, "type": arg_map.graph.nodes[n]["_type"]}
        for n in arg_map.graph.nodes()
    ]
    return json.dumps(nodes)

# For search/filtering, resources can accept parameters via URI templates
@mcp.resource("argmap://search/{node_type}")
def search_nodes(node_type: str, ctx: Context) -> str:
    """Search for nodes by type"""
    arg_map = ctx.request_context.lifespan_context.arg_map
    filtered = [
        n for n in arg_map.graph.nodes()
        if arg_map.graph.nodes[n].get("_type") == node_type
    ]
    return json.dumps(filtered)
```

`describe_argument_map()`: Create summary, including most central nodes, number of unconnected components etc.
`guided_argument_map_tour()`

`summarize_last_edits()`
`list_pending_reviews()`: Lists all arguments that require review, e.g. because they have been automatically modified.

```python
@mcp.tool()
def search_nodes(
    node_type: Literal["argument", "claim", "root", "all"] = "all",
    filter_criteria: dict | None = None
) -> list[Node]:
    """Search for nodes in the argument map"""
```

`pprint_argument`
    * print_argument_details
`pprint_argument_map`
    * print_global_argument_map_global
    * print_argument_map_local
    * print_argument_map_component

`visualize_argument_map()`: Generates an SVG & png visualization of the argument map. (Using MCP's ImageContent type for returning visualizations)

`list_equivalences`
`list_negations`

Very handy: notifications:

```python
@mcp.tool()
async def new_claim(label: str, ctx: Context):
    # ... create claim
    
    # Notify subscribers that resources changed
    await ctx.session.send_resource_updated("argmap://summary")
    await ctx.session.send_resource_list_changed()
```



### Evaluation Tools

`run_checks()`: Runs all checks on the argument map and returns a report.
    * on argument, component, subgraph only
    * mark_for_review
    * fix: e.g. cleanup, delete propositions not referenced in any node

with progress:

```python
@mcp.tool()
async def run_checks(ctx: Context) -> str:
    await ctx.report_progress(0.0, 1.0, "Starting checks...")
    # ... run checks
    await ctx.report_progress(0.5, 1.0, "Checking grounding...")
    # ... 
    await ctx.report_progress(1.0, 1.0, "Complete")
```


`next_issue()`: Identifies the next issue in the argument map that requires attention.
    * concern: dialectic grounding, string similarity, connectivity, missing gists




### Authoring Tools


```python 
def new_claim(
    label: str,
    supports: str | None = None,
    supported_by: str | None = None,
    attacked_by: str | None = None,
    attacks: str | None = None,
    target_premise_idx: int | None = None,
    force: bool = True,
    **kwargs,
) -> str:
    """
    Initializes claim creation process.

    This methods initializes and guides the client model through the process of creating a new claim in the argument map.

    Args:
        label: A string identifier for the claim
        supports: Label of the claim/argument this claim supports. If provided, a corresponding relation will be created.
        supported_by: Label of the claim/argument that supports this claim. If provided, a corresponding relation will be created.
        attacks: Label of the claim/argument this claim attacks. If provided, a corresponding relation will be created.
        attacked_by: Label of the claim/argument that attacks this claim. If provided, a corresponding relation will be created.
        target_premise_idx: If creating a dialectical relation, the index of the target premise in the supported/attacked argument.
        force: If True, forces creation even if some checks fail.
        **kwargs: Additional keyword arguments for claim configuration

    Workflow:
        Checks if enough information is provided to create the claim and any necessary dialectical relations.
        If not enough information is provided, don't create claim but suggests more specific command; otherwise create the claim.
        After creating the supporting claim, the following steps are suggested:
        1. Add a descriptive label for better identification
        2. Add one or more propositions to establish the claim foundation

    Returns:
        Status report and tool call suggestions for next steps (including using isError: true in tool results for validation failures, and notifications for setting needs_review_flag)
    """
```


```python
def new_argument(
    label: str,
    supports: str | None = None,
    supported_by: str | None = None,
    attacked_by: str | None = None,
    attacks: str | None = None,
    target_premise_idx: int | None = None,
    force: bool = True,
    **kwargs,
) -> str:
    """
    Initializes argument creation process.

    This methods initializes and guides the client model through the process of creating a new argument in the argument map.

    Args:
        label: A string identifier for the argument
        supports: Label of the claim/argument this argument supports. If provided, a corresponding relation will be created.
        supported_by: Label of the claim/argument that supports this argument. If provided, a corresponding relation will be created.
        attacks: Label of the claim/argument this argument attacks. If provided, a corresponding relation will be created.
        attacked_by: Label of the claim/argument that attacks this argument. If provided, a corresponding relation will be created.
        target_premise_idx: If creating a dialectical relation, the index of the target premise in the supported/attacked argument.
        **kwargs: Additional keyword arguments for argument configuration
        force: If True, forces creation even if some checks fail.

    Workflow:
        Checks if enough information is provided to create the argument and any necessary dialectical relations.
        If not enough information is provided, don't create argument but suggests more specific command; otherwise create the argument.
        After creating the (supporting/attacking) argument, the following steps are suggested:
        1. Add a gist (summary) to clarify the argument's main point
        2. Add a descriptive label for better identification
        3. Add one or more premises to establish the argument foundation
        4. Add a conclusion by either:
        - Selecting an existing target premise from the supported argument
        - Adding the conclusion as a new target premise in the supported argument

    Returns:
        Status report and tool call suggestions for next steps
    """
```

```python
def new_support(
    from_label: str,
    to_label: str,
    target_premise_idx: int | None = None,
    grounding: Literal["replace_conclusion", "define_equivalence", "add_premise"] | None = None,
    force: bool = True,
    **kwargs,
)
    """
    Initializes support relation creation process.
    """
```

```python
def new_attack(
    from_label: str,
    to_label: str,
    target_premise_idx: int | None = None,
    grounding: Literal["replace_conclusion", "define_negation", "add_premise"] | None = None,
    force: bool = True,
    **kwargs,
)
    """
    Initializes attack relation creation process.
    """
```

`delete(label: str)`: Deletes the specified node (claim or argument) and all associated relations and propositions if not referenced elsewhere.
    * delete adjacent relations
    * delete_proposition if not referenced elsewhere

`delete_relation(from_label: str, to_label: str, remove_target_premise: bool = False, remove_grounding_relation: bool = False)`: Deletes the specified dialectical relation, optionally:
        * delete underlying logical_relation
        * remove premise from target argument


### Updating Tools

`update`
    * update(label, field, new_value)
    * ...


### Context-Sensitive Editing Tools* (implement in v0.2.0)

`start_editing_argument`: opens editing context for given argument.

`start_editing_claim`: opens editing context for given claim.

`start_editing_dialectical_relation`: opens editing context for given dialectical relation.
    * delete_relation
        * delete_logical_relation
        * remove_premise_from_argument
    * replace_target_node
    * replace_source_node

`stop_editing()`: closes current editing context.


#### In-Context Tools* (implement in v0.2.0)

* edit_gist(new_gist: str)
* edit_label(new_label: str)
* add_premise(content: str)
* edit_premise(idx: int, new_content: str)
* reorder_premises(new_order: List[int])
* delete_premise(idx: int)
* edit_conclusion(new_conclusion: str)
* ...
* support()

* delete()




### Workflow Control Tools (?)

`undo()`


### Version Control Tools (implement in v0.2.0)

`tag_checkpoint()`
`list_checkpoints()`
`revert_to_checkpoint()`


### Utils 

`clear_grounding()`: removes all grounding logical relations (equivalence/negation) from the argument map.


## Argument Map Model

Use networkx DiGraph as base structure. 

### Claim Node

```json
{
    "_type": "claim",
    "_id": "unique-identifier",
    "_created_at": "2024-06-01T12:00:00Z",
    "_last_modified": "2024-06-01T12:00:00Z",
    "label": "Claim Label",
    "proposition": "proposition-id",
    "tags": ["tag1", "tag2"],
    "needs_review_flag": "",
    "missing_support_flag": "",
    "missing_attack_flag": "",
    "metadata:confidence": 0.85,
    "metadata:source": "Source information",
    },
}
```

```python
from pydantic import BaseModel

class ClaimNode(BaseModel):
    _type: Literal["claim"]
    _id: str
    label: str
    proposition: str
    # ... rest of fields

    def __repr__(self) -> str:
        return f"ClaimNode(label={self.label}, proposition={self.proposition})"

@mcp.tool()
def new_claim(...) -> ClaimNode:  # OR str:
    """Returns the created claim as structured data"""
    return ClaimNode(...) # OR repr(ClaimNode(...))
```

### Argument Node

```json
{
    "_type": "argument",
    "_id": "unique-identifier",
    "_created_at": "2024-06-01T12:00:00Z",
    "_last_modified": "2024-06-01T12:00:00Z",
    "label": "Argument Label",
    "gist": "A brief summary of the argument.",
    "premises": ["proposition-id-1", "proposition-id-2"],
    "conclusion": "proposition-id-3",
    "tags": ["tag1", "tag2"],
    "needs_review_flag": "",
    "missing_support_flag": "",
    "missing_attack_flag": "",
    "metadata:strength": 0.75,
    "metadata:source": "Source information"
}
```


### Proposition

```json
{
    "_type": "proposition",
    "_id": "unique-identifier",
    "_created_at": "2024-06-01T12:00:00Z",
    "_last_modified": "2024-06-01T12:00:00Z",
    "content": "The content of the proposition.",
    "metadata:confidence": 0.85,
    "metadata:source": "Source information"
}
```

### Dialectical Relation

```json
{
    "_type": "dialectical_relation",
    "_id": "unique-identifier",
    "_created_at": "2024-06-01T12:00:00Z",
    "_last_modified": "2024-06-01T12:00:00Z",
    "relation_type": "attack" | "support",
    "from": "node-id-1",
    "to": "node-id-2",
    "target_premise": "proposition-id",
    "metadata:strength": 0.6,
    "metadata:source": "Source information"
}
```

### Logical Relation

```json
{
    "_type": "logical_relation",
    "_id": "unique-identifier",
    "_created_at": "2024-06-01T12:00:00Z",
    "_last_modified": "2024-06-01T12:00:00Z",
    "relation_type": "equivalence" | "negation",
    "pair": ["proposition-id-1", "proposition-id-2"],
    "metadata:source": "Source information"
}
```

## Checks

### Connectivity

Number of connected components

### Grounding

A dialectic relation is grounded if it supervenes on the logical relations between the propositions involved.

### Completeness

Dialectic relations are complete if every relation that arises from logical relations between the propositions involved is declared.

### Consistency

All declared logical relations are consistent. I.e., if p negates q, then p and q are not equivalent.



## Modes

### Exploring

### Sketching

### Grounding

### Consolidating



## Related MCP Servers

* https://github.com/modelcontextprotocol/servers/tree/HEAD/src/memory
* https://github.com/modelcontextprotocol/servers/tree/b7e1cf3a79d421a70abe67876863430a9c049158/src/sequentialthinking