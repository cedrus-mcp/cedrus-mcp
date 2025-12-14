# Agent-Centric MCP Server Design Guidelines

## Overview

KOALA is an **agent-centric** MCP server where tools are primarily used by an LLM during reasoning, rather than providing results for direct human consumption. This document outlines design principles and best practices for building MCP servers optimized for LLM agents.

## Agent-Centric vs User-Centric

### Agent-Centric (KOALA's Case)
- **Primary User**: LLM reasoning system
- **Tools**: Reasoning instruments for the agent
- **Output**: Structured data optimized for machine parsing
- **Workflow**: Multi-step agent reasoning processes
- **Validation**: Machine-readable with corrective actions

### User-Centric (Traditional)
- **Primary User**: Human via UI
- **Tools**: Actions with human-readable results
- **Output**: Formatted text for display
- **Workflow**: Direct user commands
- **Validation**: Human-readable error messages

## Core Design Principles

### 1. Structured Output First

**Principle**: Use Pydantic models and structured data extensively.

```python
from pydantic import BaseModel, Field
from typing import Literal

class ToolResult(BaseModel):
    """Base result with LLM guidance"""
    status: Literal["success", "error", "warning"]
    message: str = Field(description="Human-readable summary")
    data: dict = Field(description="Structured data for LLM")
    next_actions: list[dict] = Field(
        default_factory=list,
        description="Suggested next tool calls"
    )

class ClaimResult(ToolResult):
    """Result of claim creation"""
    claim_id: str
    needs_grounding: bool = False
    validation_issues: list[str] = Field(default_factory=list)

@mcp.tool()
def new_claim(
    label: str,
    proposition: str,
    supports: str | None = None
) -> ClaimResult:
    """Returns structured data optimized for LLM reasoning"""
    # LLM can easily parse and act on structured results
    return ClaimResult(
        status="success",
        message=f"Created claim '{label}'",
        claim_id=claim_id,
        needs_grounding=bool(supports),
        data={"label": label, "proposition_id": prop_id},
        next_actions=[
            {
                "tool": "define_equivalence",
                "reason": "Ground support relation",
                "required": True,
                "params": {"prop1": "...", "prop2": "..."}
            }
        ]
    )
```

**Benefits**:
- LLM can reliably parse responses
- Type-safe data exchange
- Automatic schema generation
- Clear documentation of data structure

### 2. Tool Chaining Guidance

**Principle**: Tools should explicitly guide the LLM's next steps.

```python
class ValidationResult(BaseModel):
    """Validation results that guide corrective actions"""
    status: Literal["pass", "fail", "warning"]
    issues: list[dict] = Field(default_factory=list)
    grounding_errors: list[str] = Field(default_factory=list)
    connectivity_problems: list[str] = Field(default_factory=list)
    # Explicit guidance for LLM
    suggestions: list[dict] = Field(
        default_factory=list,
        description="Actionable suggestions with tool calls"
    )

@mcp.tool()
def run_checks(scope: str = "all") -> ValidationResult:
    """Returns structured validation with corrective actions"""
    return ValidationResult(
        status="warning",
        grounding_errors=[
            "Argument 'arg1' attacks 'claim2' but no negation defined"
        ],
        suggestions=[
            {
                "issue": "missing_negation",
                "severity": "high",
                "node": "arg1",
                "corrective_action": {
                    "tool": "define_negation",
                    "params": {
                        "prop1": "arg1.conclusion",
                        "prop2": "claim2.proposition"
                    },
                    "reason": "Establish dialectical grounding for attack relation"
                }
            }
        ]
    )
```

**Pattern**: Each tool result includes:
- Current state/status
- What was done
- What should be done next
- Why it should be done

### 3. Granular, Composable Tools

**Principle**: Small, single-purpose tools that LLMs can easily compose.

```python
# ✅ GOOD: Granular, composable
@mcp.tool()
def add_premise(argument_label: str, premise: str, position: int | None = None) -> dict:
    """Add a single premise to an argument"""
    arg_map.add_premise(argument_label, premise, position)
    return {
        "status": "success",
        "premise_added": premise,
        "current_premises": get_premises(argument_label),
        "next_actions": [
            {"tool": "add_premise", "reason": "Add more premises if needed"},
            {"tool": "set_conclusion", "reason": "Define the conclusion"}
        ]
    }

@mcp.tool()
def set_conclusion(argument_label: str, conclusion: str) -> dict:
    """Set the conclusion of an argument"""
    arg_map.set_conclusion(argument_label, conclusion)
    return {
        "status": "success",
        "conclusion": conclusion,
        "next_actions": [
            {
                "tool": "define_equivalence",
                "reason": "Ground support relation if this argument supports another",
                "condition": "if argument supports another node"
            }
        ]
    }

@mcp.tool()
def define_equivalence(prop1: str, prop2: str) -> dict:
    """Define logical equivalence between two propositions"""
    relation_id = create_equivalence(prop1, prop2)
    return {
        "status": "success",
        "relation_id": relation_id,
        "props": [prop1, prop2],
        "next_actions": [
            {
                "tool": "run_checks",
                "params": {"concern": "grounding"},
                "reason": "Verify grounding is complete"
            }
        ]
    }

# ❌ AVOID: Monolithic, complex
@mcp.tool()
def create_complete_argument(
    label: str,
    gist: str,
    premises: list[str],
    conclusion: str,
    supports: str | None,
    target_premise_idx: int | None,
    equivalences: list[tuple[str, str]] | None,
    # ... 10 more parameters
) -> dict:
    """Too complex - LLM will make mistakes with 10+ parameters"""
    pass
```

**Guidelines**:
- Each tool does ONE thing well
- Tools can be chained naturally
- Minimize required parameters (< 5 ideal)
- Provide clear default values
- Return what to do next

### 4. Audience Annotations

**Principle**: Separate content for LLM reasoning vs human display.

```python
from mcp.types import CallToolResult, TextContent, Annotation

@mcp.tool()
def run_checks(ctx: Context) -> CallToolResult:
    """Validation with audience-specific content"""
    
    checks = perform_comprehensive_checks()
    
    return CallToolResult(
        content=[
            # Brief message for human
            TextContent(
                type="text",
                text=f"✓ Checks complete: {checks['summary']}",
                annotations=Annotation(
                    audience=["user"],  # Human sees this
                    priority=0.3
                )
            ),
            # Detailed analysis for LLM
            TextContent(
                type="text",
                text=json.dumps({
                    "validation_results": checks,
                    "issues_by_severity": group_by_severity(checks),
                    "corrective_actions": generate_fixes(checks),
                    "graph_health_metrics": calculate_metrics(checks)
                }, indent=2),
                annotations=Annotation(
                    audience=["assistant"],  # LLM processes this
                    priority=1.0
                )
            )
        ],
        # Structured content for easy LLM parsing
        structuredContent={
            "status": checks["status"],
            "issues": checks["issues"],
            "suggestions": checks["suggestions"]
        }
    )
```

**Use Cases**:
- `audience=["user"]`: Short status messages, summaries
- `audience=["assistant"]`: Detailed data, reasoning information
- `audience=["user", "assistant"]`: Both need to see this

### 5. Machine-Readable Errors

**Principle**: Errors should enable LLM auto-correction.

```python
@mcp.tool()
def new_support(
    from_label: str,
    to_label: str,
    target_premise_idx: int | None = None
) -> CallToolResult:
    """Create support relation with actionable error messages"""
    
    # Validate source node exists
    if from_label not in graph:
        similar = find_similar_labels(from_label)
        return CallToolResult(
            content=[TextContent(
                type="text",
                text=json.dumps({
                    "error_type": "node_not_found",
                    "error_code": "E001",
                    "node": from_label,
                    "message": f"Node '{from_label}' does not exist",
                    "available_nodes": list(graph.nodes())[:10],
                    "similar_nodes": similar,
                    "corrective_actions": [
                        {
                            "action": "use_existing",
                            "tool": "new_support",
                            "params": {
                                "from_label": similar[0],
                                "to_label": to_label
                            },
                            "reason": f"Use existing similar node '{similar[0]}'"
                        },
                        {
                            "action": "create_new",
                            "tool": "new_claim" if is_claim_like(from_label) else "new_argument",
                            "params": {"label": from_label},
                            "reason": f"Create the missing node first"
                        }
                    ]
                })
            )],
            isError=True
        )
    
    # Validate target node exists
    if to_label not in graph:
        return CallToolResult(
            content=[TextContent(
                type="text",
                text=json.dumps({
                    "error_type": "node_not_found",
                    "error_code": "E001",
                    "node": to_label,
                    "corrective_actions": [/* ... */]
                })
            )],
            isError=True
        )
    
    # Validate target is an argument if premise_idx specified
    if target_premise_idx is not None:
        if graph.nodes[to_label]["_type"] != "argument":
            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text=json.dumps({
                        "error_type": "invalid_target_type",
                        "error_code": "E002",
                        "message": "target_premise_idx only valid for argument targets",
                        "node": to_label,
                        "node_type": graph.nodes[to_label]["_type"],
                        "corrective_actions": [
                            {
                                "action": "remove_parameter",
                                "tool": "new_support",
                                "params": {
                                    "from_label": from_label,
                                    "to_label": to_label
                                    # Note: target_premise_idx removed
                                },
                                "reason": "Remove target_premise_idx for claim targets"
                            }
                        ]
                    })
                )],
                isError=True
            )
    
    # Success case
    relation_id = create_support_relation(from_label, to_label, target_premise_idx)
    return CallToolResult(
        content=[TextContent(
            type="text",
            text=f"Created support: {from_label} → {to_label}"
        )],
        structuredContent={
            "relation_id": relation_id,
            "from": from_label,
            "to": to_label,
            "needs_grounding": True,
            "next_actions": [
                {
                    "tool": "define_equivalence",
                    "required": True,
                    "reason": "Establish logical grounding"
                }
            ]
        }
    )
```

**Error Structure**:
```typescript
{
  error_type: string,          // Machine-readable category
  error_code: string,           // Unique identifier
  message: string,              // Human-readable description
  context: {...},               // Relevant data
  corrective_actions: [         // How to fix
    {
      action: string,
      tool: string,
      params: {...},
      reason: string
    }
  ]
}
```

### 6. Resources as LLM Knowledge Base

**Principle**: Resources provide dense, structured knowledge for LLM reasoning.

```python
@mcp.resource("argmap://llm/context")
def get_llm_context(ctx: Context) -> str:
    """Optimized graph representation for LLM reasoning"""
    arg_map = ctx.request_context.lifespan_context.arg_map
    
    return json.dumps({
        "graph_summary": {
            "node_count": arg_map.graph.number_of_nodes(),
            "edge_count": arg_map.graph.number_of_edges(),
            "component_count": nx.number_weakly_connected_components(arg_map.graph),
            "density": nx.density(arg_map.graph)
        },
        "node_index": {
            node_id: {
                "label": arg_map.graph.nodes[node_id]["label"],
                "type": arg_map.graph.nodes[node_id]["_type"],
                "in_degree": arg_map.graph.in_degree(node_id),
                "out_degree": arg_map.graph.out_degree(node_id),
                "needs_review": arg_map.graph.nodes[node_id].get("needs_review_flag", False)
            }
            for node_id in arg_map.graph.nodes()
        },
        "active_issues": {
            "ungrounded_relations": get_ungrounded_relations(),
            "nodes_needing_review": get_nodes_for_review(),
            "disconnected_components": list(nx.weakly_connected_components(arg_map.graph))
        },
        "navigation_hints": {
            "central_nodes": get_central_nodes(k=5),
            "root_nodes": get_root_nodes(),
            "leaf_nodes": get_leaf_nodes()
        },
        "recent_changes": get_recent_modifications()
    }, indent=2)

@mcp.resource("argmap://node/{label}/detailed")
def get_node_detailed(label: str, ctx: Context) -> str:
    """Comprehensive node data for LLM reasoning"""
    arg_map = ctx.request_context.lifespan_context.arg_map
    
    node_data = dict(arg_map.graph.nodes[label])
    
    return json.dumps({
        "node": node_data,
        "proposition": arg_map.propositions.get(node_data.get("proposition")),
        "premises": [
            arg_map.propositions[p] 
            for p in node_data.get("premises", [])
        ] if node_data.get("_type") == "argument" else None,
        "incoming_relations": [
            {
                "from": u,
                "type": arg_map.graph.edges[u, label]["relation_type"],
                "grounding": get_grounding(u, label)
            }
            for u in arg_map.graph.predecessors(label)
        ],
        "outgoing_relations": [
            {
                "to": v,
                "type": arg_map.graph.edges[label, v]["relation_type"],
                "grounding": get_grounding(label, v)
            }
            for v in arg_map.graph.successors(label)
        ],
        "validation_status": validate_node(label),
        "dialectical_context": get_dialectical_context(label)
    }, indent=2)

@mcp.resource("argmap://validation/current")
def get_current_validation(ctx: Context) -> str:
    """Current validation state for LLM reasoning"""
    validation = run_all_checks()
    
    return json.dumps({
        "timestamp": datetime.now().isoformat(),
        "overall_status": validation["status"],
        "issues_by_type": {
            "grounding": validation["grounding_issues"],
            "connectivity": validation["connectivity_issues"],
            "completeness": validation["completeness_issues"],
            "consistency": validation["consistency_issues"]
        },
        "issues_by_severity": {
            "critical": [i for i in validation["all_issues"] if i["severity"] == "critical"],
            "warning": [i for i in validation["all_issues"] if i["severity"] == "warning"],
            "info": [i for i in validation["all_issues"] if i["severity"] == "info"]
        },
        "prioritized_fixes": prioritize_issues(validation["all_issues"]),
        "health_metrics": calculate_health_metrics(validation)
    }, indent=2)
```

**Resource Design Guidelines**:
- Dense, structured JSON for LLM parsing
- Include navigation hints (where to look next)
- Provide context (related nodes, validation state)
- Cache expensive computations
- Update notifications when state changes

### 7. Prompts as Reasoning Templates

**Principle**: Prompts teach the LLM how to use your tools effectively.

```python
@mcp.prompt()
def create_grounded_support() -> str:
    """Multi-step reasoning template for proper support creation"""
    return """Create a properly grounded support relation between two nodes.

REASONING PROCESS:
1. Identify the supporting node (source) and supported node (target)
2. Load both nodes to understand their propositional content
3. Determine the target premise in the supported node
4. Create the dialectical support relation
5. Establish logical grounding by EITHER:
   a) Defining equivalence between source conclusion and target premise, OR
   b) Adding source conclusion as new premise to target
6. Validate the grounding is complete

TOOLS TO USE IN SEQUENCE:
1. Read resources:
   - argmap://node/{source}
   - argmap://node/{target}
2. Call: new_support(from_label=source, to_label=target, target_premise_idx=X)
3. Call: define_equivalence(prop1=source.conclusion, prop2=target.premise)
   OR add_premise(argument_label=target, premise=source.conclusion)
4. Call: run_checks(scope="relation", focus=[source, target])
5. If validation fails:
   - Analyze the error structure
   - Follow corrective_actions from the error
   - Retry validation

CRITICAL REQUIREMENTS:
- Support must be logically grounded (step 5 is mandatory)
- Always validate after grounding (step 6)
- Fix issues before proceeding
- Document your reasoning at each step

EXPECTED OUTCOME:
- Support relation exists in graph
- Logical grounding is established (equivalence or premise addition)
- Validation passes with no grounding errors"""

@mcp.prompt()
def systematic_map_improvement() -> str:
    """Template for systematic argument map enhancement"""
    return """Systematically improve the argument map quality.

REASONING STRATEGY:

Phase 1: ASSESS
1. Load: argmap://llm/context
2. Load: argmap://validation/current
3. Analyze:
   - What are the critical issues?
   - What are the patterns in warnings?
   - Which areas need most work?

Phase 2: PRIORITIZE
1. Group issues by:
   - Severity (critical > warning > info)
   - Type (grounding > connectivity > completeness)
   - Impact (central nodes > peripheral nodes)
2. Create work queue ordered by priority

Phase 3: EXECUTE
For each issue in priority order:
1. Understand the issue context
2. Load relevant resources
3. Apply corrective action from error.corrective_actions
4. Validate the fix
5. Move to next issue

Phase 4: VERIFY
1. Run: run_checks(scope="all")
2. Compare before/after metrics
3. Ensure no regressions
4. Document improvements

TOOLS STRATEGY:
- Use validation tools to guide work
- Follow next_actions from tool results
- Validate after each significant change
- Leverage corrective_actions from errors

METRICS TO TRACK:
- Number of issues resolved
- Number of new issues introduced
- Overall validation status
- Graph health metrics

Continue until validation status is "pass" or no more improvements possible."""

@mcp.prompt()
def guided_argument_construction(
    conclusion: str,
    argument_type: str = "deductive"
) -> list[base.Message]:
    """Interactive workflow for argument construction"""
    return [
        base.UserMessage(
            f"I want to construct a {argument_type} argument with conclusion: {conclusion}"
        ),
        base.AssistantMessage(
            f"I'll guide you through constructing a well-formed {argument_type} argument. "
            "Let's work step-by-step."
        ),
        base.UserMessage(
            f"""Please help me build this argument:

STEP 1 - Structure:
- Create the argument node with new_argument tool
- Use a descriptive label
- Write a clear gist summarizing the reasoning

STEP 2 - Premises:
- What premises are needed to support '{conclusion}'?
- Add each premise with add_premise tool
- For {argument_type} arguments, ensure premises entail conclusion

STEP 3 - Conclusion:
- Set the conclusion with set_conclusion tool
- Ensure it matches: {conclusion}

STEP 4 - Integration:
- If this argument supports/attacks another claim, create that relation
- Establish logical grounding (equivalence/negation)

STEP 5 - Validation:
- Run checks on the completed argument
- Address any issues found

Let's start with Step 1. Suggest a good label and gist for this argument."""
        )
    ]

@mcp.prompt()
def explore_dialectical_structure(node_label: str, depth: int = 2) -> str:
    """Template for understanding debate structure"""
    return f"""Explore and map the dialectical structure around '{node_label}'.

EXPLORATION STRATEGY:

1. CENTER NODE:
   - Load: argmap://node/{node_label}/detailed
   - Understand the claim/argument
   - Note its propositional content

2. IMMEDIATE CONTEXT (depth 1):
   - What supports this node? (incoming support edges)
   - What attacks this node? (incoming attack edges)
   - What does this node support? (outgoing support edges)
   - What does this node attack? (outgoing attack edges)
   - Load each connected node's details

3. EXTENDED CONTEXT (depth {depth}):
   - For each connected node, repeat step 2
   - Build a tree of dialectical relations
   - Identify key points of contention

4. ANALYSIS:
   - Where is the debate strongest? (most supported/attacked)
   - Where are gaps? (missing attacks/support)
   - What are the dialectical patterns?
   - Which nodes are most central to the debate?

5. SYNTHESIS:
   - Summarize the dialectical structure
   - Identify strengths and weaknesses
   - Suggest areas for development

TOOLS TO USE:
- argmap://node/{{label}}/detailed for each node
- argmap://llm/context for overall structure
- Traverse the graph systematically
- Track visited nodes to avoid cycles

OUTPUT FORMAT:
- Dialectical tree structure
- Analysis of debate quality
- Suggestions for improvement"""
```

**Prompt Design Guidelines**:
- Clear step-by-step reasoning process
- Explicit tool call sequences
- Explain WHY each step is needed
- Provide decision criteria
- Include validation loops
- Set clear success criteria

## Implementation Patterns

### Pattern 1: Tool Result Factory

```python
from typing import TypeVar, Generic
from pydantic import BaseModel

T = TypeVar('T')

class ActionableResult(BaseModel, Generic[T]):
    """Generic result with next actions"""
    status: Literal["success", "error", "warning"]
    message: str
    data: T
    next_actions: list[dict] = Field(default_factory=list)
    validation_issues: list[dict] = Field(default_factory=list)

def create_result(
    data: T,
    message: str,
    status: str = "success",
    next_actions: list[dict] | None = None,
    issues: list[dict] | None = None
) -> ActionableResult[T]:
    """Factory for creating consistent tool results"""
    return ActionableResult(
        status=status,
        message=message,
        data=data,
        next_actions=next_actions or [],
        validation_issues=issues or []
    )
```

### Pattern 2: Error Builder

```python
class ErrorBuilder:
    """Builder for machine-readable errors"""
    
    def __init__(self, error_type: str, error_code: str):
        self.error = {
            "error_type": error_type,
            "error_code": error_code,
            "message": "",
            "context": {},
            "corrective_actions": []
        }
    
    def message(self, msg: str) -> 'ErrorBuilder':
        self.error["message"] = msg
        return self
    
    def context(self, **kwargs) -> 'ErrorBuilder':
        self.error["context"].update(kwargs)
        return self
    
    def suggest_action(
        self,
        tool: str,
        params: dict,
        reason: str,
        action_type: str = "fix"
    ) -> 'ErrorBuilder':
        self.error["corrective_actions"].append({
            "action": action_type,
            "tool": tool,
            "params": params,
            "reason": reason
        })
        return self
    
    def build(self) -> CallToolResult:
        return CallToolResult(
            content=[TextContent(
                type="text",
                text=json.dumps(self.error, indent=2)
            )],
            isError=True
        )

# Usage
if node not in graph:
    return (ErrorBuilder("node_not_found", "E001")
        .message(f"Node '{node}' does not exist")
        .context(node=node, available=list(graph.nodes())[:10])
        .suggest_action(
            tool="new_claim",
            params={"label": node},
            reason="Create the missing node"
        )
        .build())
```

### Pattern 3: Validation Pipeline

```python
class ValidationPipeline:
    """Chainable validation with actionable results"""
    
    def __init__(self):
        self.issues = []
        self.suggestions = []
    
    def check(
        self,
        condition: bool,
        issue_type: str,
        severity: str,
        message: str,
        fix: dict | None = None
    ) -> 'ValidationPipeline':
        """Add a validation check"""
        if not condition:
            issue = {
                "type": issue_type,
                "severity": severity,
                "message": message
            }
            self.issues.append(issue)
            
            if fix:
                self.suggestions.append({
                    "issue": issue,
                    "corrective_action": fix
                })
        return self
    
    def result(self) -> ValidationResult:
        """Build final validation result"""
        return ValidationResult(
            status="pass" if not self.issues else "fail",
            issues=self.issues,
            suggestions=self.suggestions
        )

# Usage
def validate_support_relation(from_node, to_node):
    return (ValidationPipeline()
        .check(
            from_node in graph,
            "missing_node",
            "critical",
            f"Source node '{from_node}' not found",
            fix={"tool": "new_claim", "params": {"label": from_node}}
        )
        .check(
            to_node in graph,
            "missing_node",
            "critical",
            f"Target node '{to_node}' not found",
            fix={"tool": "new_argument", "params": {"label": to_node}}
        )
        .check(
            has_grounding(from_node, to_node),
            "missing_grounding",
            "high",
            "Support relation lacks logical grounding",
            fix={
                "tool": "define_equivalence",
                "params": {
                    "prop1": f"{from_node}.conclusion",
                    "prop2": f"{to_node}.target_premise"
                }
            }
        )
        .result())
```

### Pattern 4: Resource Caching

```python
from functools import lru_cache
from datetime import datetime, timedelta

class ResourceCache:
    """Cache expensive resource computations"""
    
    def __init__(self, ttl_seconds: int = 60):
        self.cache = {}
        self.ttl = timedelta(seconds=ttl_seconds)
    
    def get_or_compute(self, key: str, compute_fn):
        """Get cached value or compute and cache"""
        now = datetime.now()
        
        if key in self.cache:
            value, timestamp = self.cache[key]
            if now - timestamp < self.ttl:
                return value
        
        value = compute_fn()
        self.cache[key] = (value, now)
        return value
    
    def invalidate(self, pattern: str | None = None):
        """Invalidate cache entries"""
        if pattern is None:
            self.cache.clear()
        else:
            self.cache = {
                k: v for k, v in self.cache.items()
                if pattern not in k
            }

cache = ResourceCache()

@mcp.resource("argmap://analysis/expensive")
def expensive_analysis(ctx: Context) -> str:
    """Cached expensive computation"""
    return cache.get_or_compute(
        "analysis",
        lambda: perform_expensive_analysis()
    )

@mcp.tool()
async def modify_graph(ctx: Context):
    """Modification that invalidates cache"""
    # ... modify graph
    cache.invalidate("analysis")  # Invalidate cached analysis
    await ctx.session.send_resource_updated("argmap://analysis/expensive")
```

## Best Practices Summary

### ✅ DO

1. **Return structured data** using Pydantic models
2. **Include next_actions** in every tool result
3. **Provide corrective_actions** in all errors
4. **Use audience annotations** to separate LLM/human content
5. **Design granular tools** (< 5 parameters ideal)
6. **Cache expensive resources** and invalidate on changes
7. **Validate inputs** and return actionable errors
8. **Guide the LLM** with clear reasoning templates in prompts
9. **Notify on changes** using resource update notifications
10. **Document workflows** in prompt templates

### ❌ DON'T

1. **Don't create monolithic tools** with 10+ parameters
2. **Don't return plain strings** when structured data would work
3. **Don't hide errors** - expose them with corrective actions
4. **Don't assume context** - LLM needs explicit state in resources
5. **Don't skip next_actions** - always guide the next step
6. **Don't ignore validation** - validate and suggest fixes
7. **Don't forget notifications** - tell clients when resources change
8. **Don't write prompts like docs** - write them as reasoning guides
9. **Don't skip audience tags** - separate LLM and human content
10. **Don't make tools stateful** - use resources to expose state

## Example: Complete Tool Implementation

```python
from mcp.server.fastmcp import FastMCP, Context
from pydantic import BaseModel, Field
from typing import Literal
import json

mcp = FastMCP("KOALA")

# ===== RESULT MODELS =====

class ToolResult(BaseModel):
    status: Literal["success", "error", "warning"]
    message: str
    data: dict
    next_actions: list[dict] = Field(default_factory=list)
    validation_issues: list[dict] = Field(default_factory=list)

# ===== TOOL IMPLEMENTATION =====

@mcp.tool()
def new_claim(
    label: str,
    proposition: str,
    supports: str | None = None,
    attacked_by: str | None = None,
    ctx: Context | None = None
) -> ToolResult:
    """
    Create a new claim node with optional dialectical relations.
    
    This tool creates a claim and guides the LLM through establishing
    proper logical grounding if dialectical relations are created.
    """
    arg_map = ctx.request_context.lifespan_context.arg_map
    
    # Validate inputs
    if label in arg_map.graph:
        return ErrorBuilder("duplicate_label", "E003")
            .message(f"Node '{label}' already exists")
            .context(label=label, existing_type=arg_map.graph.nodes[label]["_type"])
            .suggest_action(
                tool="new_claim",
                params={"label": f"{label}_2", "proposition": proposition},
                reason="Use a different label"
            )
            .suggest_action(
                tool="update_node",
                params={"label": label, "proposition": proposition},
                reason="Update the existing node instead"
            )
            .build()
    
    if supports and supports not in arg_map.graph:
        return ErrorBuilder("node_not_found", "E001")
            .message(f"Target node '{supports}' does not exist")
            .context(supports=supports)
            .suggest_action(
                tool="new_claim",
                params={"label": label, "proposition": proposition},
                reason="Create claim without support relation first"
            )
            .build()
    
    # Create proposition
    prop_id = f"prop_{len(arg_map.propositions)}"
    arg_map.propositions[prop_id] = {
        "_id": prop_id,
        "_type": "proposition",
        "content": proposition
    }
    
    # Create claim node
    arg_map.graph.add_node(
        label,
        _type="claim",
        _id=label,
        label=label,
        proposition=prop_id
    )
    
    # Build next actions
    next_actions = []
    needs_grounding = False
    
    # Handle support relation
    if supports:
        arg_map.graph.add_edge(
            label,
            supports,
            _type="dialectical_relation",
            relation_type="support"
        )
        needs_grounding = True
        
        target_node = arg_map.graph.nodes[supports]
        target_prop = (
            target_node.get("proposition")
            if target_node["_type"] == "claim"
            else target_node.get("conclusion")
        )
        
        next_actions.append({
            "tool": "define_equivalence",
            "priority": "required",
            "params": {
                "prop1": prop_id,
                "prop2": target_prop
            },
            "reason": "Establish logical grounding for support relation",
            "alternative": {
                "tool": "add_premise",
                "params": {
                    "argument_label": supports,
                    "premise": proposition
                },
                "reason": "Alternative: add as premise instead of equivalence"
            }
        })
    
    # Handle attack relation
    if attacked_by:
        if attacked_by not in arg_map.graph:
            validation_issues = [{
                "type": "invalid_relation",
                "severity": "warning",
                "message": f"Attacker '{attacked_by}' does not exist yet"
            }]
        else:
            arg_map.graph.add_edge(
                attacked_by,
                label,
                _type="dialectical_relation",
                relation_type="attack"
            )
            needs_grounding = True
    
    # Always suggest validation
    next_actions.append({
        "tool": "run_checks",
        "priority": "recommended",
        "params": {
            "scope": label,
            "concern": "grounding" if needs_grounding else "general"
        },
        "reason": "Validate the new claim"
    })
    
    # Suggest further development
    next_actions.extend([
        {
            "tool": "create_supporting_argument",
            "priority": "optional",
            "params": {"claim_label": label},
            "reason": "Develop support for this claim"
        },
        {
            "tool": "consider_objections",
            "priority": "optional",
            "params": {"claim_label": label},
            "reason": "Identify potential attacks"
        }
    ])
    
    return ToolResult(
        status="success",
        message=f"Created claim '{label}'",
        data={
            "claim_id": label,
            "proposition_id": prop_id,
            "has_support_relation": bool(supports),
            "has_attack_relation": bool(attacked_by),
            "needs_grounding": needs_grounding
        },
        next_actions=next_actions,
        validation_issues=validation_issues if attacked_by and attacked_by not in arg_map.graph else []
    )
```

## Conclusion

Agent-centric MCP server design prioritizes **machine-readable structured data**, **explicit workflow guidance**, and **actionable error messages** over human-friendly text output. This enables LLM agents to:

1. **Reliably parse** tool results
2. **Understand** what to do next
3. **Self-correct** when errors occur
4. **Compose** complex workflows from simple tools
5. **Reason effectively** about the domain

The key is treating the LLM as a **reasoning partner** rather than an end user, providing the structured information and guidance it needs to accomplish complex tasks autonomously.
