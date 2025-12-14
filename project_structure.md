# KOALA Project Structure

## Recommended Directory Layout

```
koala/
├── src/
│   └── koala/
│       ├── __init__.py
│       ├── server.py              # Main MCP server entry point
│       │
│       ├── models/                # Pydantic models & data structures
│       │   ├── __init__.py
│       │   ├── nodes.py           # ClaimNode, ArgumentNode
│       │   ├── propositions.py    # Proposition model
│       │   └── relations.py       # DialecticalRelation, LogicalRelation
│       │
│       ├── graph/                 # Graph/knowledge base management
│       │   ├── __init__.py
│       │   ├── argument_map.py    # ArgumentMap class (NetworkX wrapper)
│       │   ├── persistence.py     # Save/load functionality
│       │   └── query.py           # Graph query utilities
│       │
│       ├── tools/                 # MCP tools organized by category
│       │   ├── __init__.py
│       │   ├── authoring.py       # new_claim, new_argument, new_support, etc.
│       │   ├── editing.py         # update_node, delete, etc.
│       │   ├── validation.py      # run_checks, next_issue
│       │   └── visualization.py   # svg_argument_map
│       │
│       ├── resources/             # MCP resources
│       │   ├── __init__.py
│       │   ├── graph_views.py     # summary, nodes, claims, arguments
│       │   ├── node_details.py    # detailed node information
│       │   └── validation_cache.py # cached validation results
│       │
│       ├── prompts/               # MCP prompts
│       │   ├── __init__.py
│       │   ├── reconstruction.py  # kickoff_reconstruction_project
│       │   ├── debate.py          # kickoff_debate_generation
│       │   └── analysis.py        # analyze_argument, check_grounding, etc.
│       │
│       ├── validation/            # Validation & checking logic
│       │   ├── __init__.py
│       │   ├── connectivity.py    # Connectivity checks
│       │   ├── completeness.py    # Completeness checks
│       │   ├── consistency.py     # Consistency checks
│       │   └── pipeline.py        # ValidationPipeline class
│       │
│       ├── utils/                 # Shared utilities
│       │   ├── __init__.py
│       │   ├── errors.py          # ErrorBuilder class
│       │   ├── cache.py           # ResourceCache class
│       │   ├── ids.py             # ID generation
│       │   └── timestamps.py      # Timestamp utilities
│       │
│       └── config/                # Configuration
│           ├── __init__.py
│           └── settings.py        # App settings
│
├── tests/                         # Test suite
│   ├── __init__.py
│   ├── conftest.py                # Pytest fixtures
│   ├── test_models/
│   ├── test_graph/
│   ├── test_tools/
│   ├── test_resources/
│   ├── test_validation/
│   └── integration/
│
├── examples/                      # Example argument maps
│   ├── simple_debate.json
│   └── reconstructed_paper.json
│
├── docs/                          # Documentation
│   ├── design_doc.md
│   ├── agent_centric_design.md
│   └── api_reference.md
│
├── pyproject.toml                 # Project metadata & dependencies
├── README.md
└── .gitignore
```

## Key Design Principles

### 1. Separation of Concerns

Each directory has a clear responsibility:
- **models/**: Pure data structures (no business logic)
- **graph/**: Graph management and persistence
- **tools/**: MCP tool implementations
- **resources/**: MCP resource implementations
- **prompts/**: MCP prompt templates
- **validation/**: All validation logic isolated
- **utils/**: Shared utilities

### 2. Tool Organization

Tools are grouped by functional category:

```python
# src/koala/tools/authoring.py
"""Authoring tools for creating new nodes and relations."""

from koala.models.results import ClaimResult, ArgumentResult
from koala.models.nodes import ClaimNode, ArgumentNode
from koala.utils.errors import ErrorBuilder
from koala.validation.pipeline import ValidationPipeline

def new_claim(
    label: str,
    proposition: str,
    supports: str | None = None,
    ctx: Context | None = None
) -> ClaimResult:
    """Create a new claim node."""
    # Implementation

def new_argument(
    label: str,
    gist: str,
    supports: str | None = None,
    ctx: Context | None = None
) -> ArgumentResult:
    """Create a new argument node."""
    # Implementation

def new_support(
    from_label: str,
    to_label: str,
    target_premise_idx: int | None = None,
    ctx: Context | None = None
) -> ToolResult:
    """Create a support relation."""
    # Implementation
```

### 3. Shared Models

All Pydantic models in one place:

```python
# src/koala/models/results.py
"""Result models for tool responses."""

from pydantic import BaseModel, Field
from typing import Literal

class ToolResult(BaseModel):
    """Base result for all tools."""
    status: Literal["success", "error", "warning"]
    message: str
    data: dict
    next_actions: list[dict] = Field(default_factory=list)
    validation_issues: list[dict] = Field(default_factory=list)

class ClaimResult(ToolResult):
    """Result of claim creation."""
    claim_id: str
    needs_grounding: bool = False

class ArgumentResult(ToolResult):
    """Result of argument creation."""
    argument_id: str
    needs_premises: bool = True
    needs_conclusion: bool = True

class ValidationResult(BaseModel):
    """Result of validation checks."""
    status: Literal["pass", "fail", "warning"]
    issues: list[dict] = Field(default_factory=list)
    suggestions: list[dict] = Field(default_factory=list)
    metrics: dict = Field(default_factory=dict)
```

```python
# src/koala/models/nodes.py
"""Node models for argument map."""

from pydantic import BaseModel, Field
from typing import Literal
from datetime import datetime

class ClaimNode(BaseModel):
    """Claim node in argument map."""
    _type: Literal["claim"] = "claim"
    _id: str
    _created_at: datetime = Field(default_factory=datetime.now)
    _last_modified: datetime = Field(default_factory=datetime.now)
    label: str
    proposition: str
    tags: list[str] = Field(default_factory=list)
    needs_review_flag: bool = False
    missing_support_flag: bool = False
    missing_attack_flag: bool = False

class ArgumentNode(BaseModel):
    """Argument node in argument map."""
    _type: Literal["argument"] = "argument"
    _id: str
    _created_at: datetime = Field(default_factory=datetime.now)
    _last_modified: datetime = Field(default_factory=datetime.now)
    label: str
    gist: str = ""
    premises: list[str] = Field(default_factory=list)
    conclusion: str = ""
    tags: list[str] = Field(default_factory=list)
    needs_review_flag: bool = False
```

### 4. Graph Abstraction

Encapsulate NetworkX in a clean interface:

```python
# src/koala/graph/argument_map.py
"""Argument map graph implementation."""

import networkx as nx
from typing import Dict, List, Optional
from koala.models.nodes import ClaimNode, ArgumentNode
from koala.models.propositions import Proposition
from koala.models.relations import DialecticalRelation, LogicalRelation

class ArgumentMap:
    """NetworkX-based argument map."""
    
    def __init__(self):
        self.graph = nx.DiGraph()
        self.propositions: Dict[str, Proposition] = {}
        self.logical_relations: Dict[str, LogicalRelation] = {}
    
    # === Node Operations ===
    
    def add_claim(self, node: ClaimNode) -> None:
        """Add a claim node to the graph."""
        self.graph.add_node(
            node.label,
            **node.model_dump()
        )
    
    def add_argument(self, node: ArgumentNode) -> None:
        """Add an argument node to the graph."""
        self.graph.add_node(
            node.label,
            **node.model_dump()
        )
    
    def get_node(self, label: str) -> ClaimNode | ArgumentNode:
        """Get a node by label."""
        data = dict(self.graph.nodes[label])
        if data["_type"] == "claim":
            return ClaimNode(**data)
        return ArgumentNode(**data)
    
    def update_node(self, label: str, **updates) -> None:
        """Update node attributes."""
        for key, value in updates.items():
            self.graph.nodes[label][key] = value
        self.graph.nodes[label]["_last_modified"] = datetime.now()
    
    def delete_node(self, label: str) -> None:
        """Delete a node and its relations."""
        self.graph.remove_node(label)
    
    # === Relation Operations ===
    
    def add_support(
        self,
        from_label: str,
        to_label: str,
        target_premise: Optional[str] = None
    ) -> str:
        """Add a support relation."""
        relation = DialecticalRelation(
            _id=f"support_{from_label}_{to_label}",
            relation_type="support",
            from_node=from_label,
            to_node=to_label,
            target_premise=target_premise
        )
        self.graph.add_edge(
            from_label,
            to_label,
            **relation.model_dump()
        )
        return relation._id
    
    def add_attack(
        self,
        from_label: str,
        to_label: str,
        target_premise: Optional[str] = None
    ) -> str:
        """Add an attack relation."""
        relation = DialecticalRelation(
            _id=f"attack_{from_label}_{to_label}",
            relation_type="attack",
            from_node=from_label,
            to_node=to_label,
            target_premise=target_premise
        )
        self.graph.add_edge(
            from_label,
            to_label,
            **relation.model_dump()
        )
        return relation._id
    
    # === Proposition Operations ===
    
    def add_proposition(self, prop: Proposition) -> None:
        """Add a proposition."""
        self.propositions[prop._id] = prop
    
    # === Logical Relation Operations ===
    
    def add_equivalence(self, prop1: str, prop2: str) -> str:
        """Add an equivalence relation."""
        relation = LogicalRelation(
            _id=f"equiv_{prop1}_{prop2}",
            relation_type="equivalence",
            pair=[prop1, prop2]
        )
        self.logical_relations[relation._id] = relation
        return relation._id
    
    def add_negation(self, prop1: str, prop2: str) -> str:
        """Add a negation relation."""
        relation = LogicalRelation(
            _id=f"neg_{prop1}_{prop2}",
            relation_type="negation",
            pair=[prop1, prop2]
        )
        self.logical_relations[relation._id] = relation
        return relation._id
    
    # === Query Operations ===
    
    def list_claims(self) -> List[ClaimNode]:
        """Get all claim nodes."""
        return [
            ClaimNode(**dict(self.graph.nodes[n]))
            for n in self.graph.nodes()
            if self.graph.nodes[n]["_type"] == "claim"
        ]
    
    def list_arguments(self) -> List[ArgumentNode]:
        """Get all argument nodes."""
        return [
            ArgumentNode(**dict(self.graph.nodes[n]))
            for n in self.graph.nodes()
            if self.graph.nodes[n]["_type"] == "argument"
        ]
    
    def get_supporters(self, label: str) -> List[str]:
        """Get nodes that support this node."""
        return [
            u for u in self.graph.predecessors(label)
            if self.graph.edges[u, label]["relation_type"] == "support"
        ]
    
    def get_attackers(self, label: str) -> List[str]:
        """Get nodes that attack this node."""
        return [
            u for u in self.graph.predecessors(label)
            if self.graph.edges[u, label]["relation_type"] == "attack"
        ]
    
    # === Analytics ===
    
    def get_central_nodes(self, k: int = 5) -> List[tuple[str, float]]:
        """Get most central nodes by degree centrality."""
        centrality = nx.degree_centrality(self.graph)
        return sorted(
            centrality.items(),
            key=lambda x: x[1],
            reverse=True
        )[:k]
    
    def get_connected_components(self) -> int:
        """Get number of weakly connected components."""
        return nx.number_weakly_connected_components(self.graph)
    
    # === Serialization ===
    
    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            "graph": nx.node_link_data(self.graph),
            "propositions": {
                k: v.model_dump() for k, v in self.propositions.items()
            },
            "logical_relations": {
                k: v.model_dump() for k, v in self.logical_relations.items()
            }
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'ArgumentMap':
        """Deserialize from dictionary."""
        map = cls()
        map.graph = nx.node_link_graph(data["graph"])
        map.propositions = {
            k: Proposition(**v) for k, v in data["propositions"].items()
        }
        map.logical_relations = {
            k: LogicalRelation(**v) for k, v in data["logical_relations"].items()
        }
        return map
```

### 5. Main Server Setup

Clean server initialization:

```python
# src/koala/server.py
"""KOALA MCP server main entry point."""

from mcp.server.fastmcp import FastMCP, Context
from contextlib import asynccontextmanager
from dataclasses import dataclass
import json

from koala.graph.argument_map import ArgumentMap
from koala.graph.persistence import load_map, save_map
from koala.utils.cache import ResourceCache

# Import all tools
from koala.tools.authoring import (
    new_claim, new_argument, new_support, new_attack
)
from koala.tools.editing import (
    update_node, delete_node, delete_relation
)
from koala.tools.validation import (
    run_checks, next_issue
)
from koala.tools.visualization import (
    svg_argument_map
)

# Import all resources
from koala.resources.graph_views import (
    get_summary, get_nodes, get_claims, get_arguments
)
from koala.resources.node_details import (
    get_node_details, get_node_context
)

# Import all prompts
from koala.prompts.reconstruction import (
    kickoff_reconstruction_project
)
from koala.prompts.debate import (
    kickoff_debate_generation
)
from koala.prompts.analysis import (
    analyze_argument, check_grounding
)

# === Application Context ===

@dataclass
class AppContext:
    """Application state."""
    arg_map: ArgumentMap
    cache: ResourceCache

@asynccontextmanager
async def app_lifespan(server: FastMCP):
    """Manage application lifecycle."""
    # Load argument map
    try:
        arg_map = load_map("argument_map.json")
    except FileNotFoundError:
        arg_map = ArgumentMap()
    
    cache = ResourceCache(ttl_seconds=60)
    
    try:
        yield AppContext(arg_map=arg_map, cache=cache)
    finally:
        # Save on shutdown
        save_map(arg_map, "argument_map.json")

# === Server Initialization ===

mcp = FastMCP(
    "KOALA Argument Mapper",
    lifespan=app_lifespan,
    stateless_http=False  # Stateful server
)

# === Register Tools ===

# Authoring
mcp.tool()(new_claim)
mcp.tool()(new_argument)
mcp.tool()(new_support)
mcp.tool()(new_attack)

# Editing
mcp.tool()(update_node)
mcp.tool()(delete_node)
mcp.tool()(delete_relation)

# Validation
mcp.tool()(run_checks)
mcp.tool()(next_issue)

# Visualization
mcp.tool()(svg_argument_map)

# === Register Resources ===

mcp.resource("argmap://summary")(get_summary)
mcp.resource("argmap://nodes")(get_nodes)
mcp.resource("argmap://claims")(get_claims)
mcp.resource("argmap://arguments")(get_arguments)
mcp.resource("argmap://node/{label}")(get_node_details)
mcp.resource("argmap://context/{label}")(get_node_context)

# === Register Prompts ===

mcp.prompt()(kickoff_reconstruction_project)
mcp.prompt()(kickoff_debate_generation)
mcp.prompt()(analyze_argument)
mcp.prompt()(check_grounding)

# === Entry Point ===

def main():
    """Run the server."""
    mcp.run(transport="stdio")

if __name__ == "__main__":
    main()
```

## Example Tool Implementation

```python
# src/koala/tools/authoring.py
"""Authoring tools for creating nodes and relations."""

from mcp.server.fastmcp import Context
from koala.models.results import ClaimResult, ToolResult
from koala.models.nodes import ClaimNode
from koala.models.propositions import Proposition
from koala.utils.errors import ErrorBuilder
from koala.utils.ids import generate_id

def new_claim(
    label: str,
    proposition: str,
    supports: str | None = None,
    attacked_by: str | None = None,
    ctx: Context | None = None
) -> ClaimResult:
    """
    Create a new claim node with optional dialectical relations.
    
    Args:
        label: Unique identifier for the claim
        proposition: Propositional content of the claim
        supports: Label of node this claim supports (creates support relation)
        attacked_by: Label of node that attacks this claim (creates attack relation)
        ctx: MCP context (auto-injected)
    
    Returns:
        ClaimResult with status, data, and next_actions
    """
    arg_map = ctx.request_context.lifespan_context.arg_map
    
    # Validate: label must be unique
    if label in arg_map.graph:
        return ErrorBuilder("duplicate_label", "E001")
            .message(f"Node '{label}' already exists")
            .context(label=label, existing_type=arg_map.graph.nodes[label]["_type"])
            .suggest_action(
                tool="new_claim",
                params={"label": f"{label}_v2", "proposition": proposition},
                reason="Use a different label"
            )
            .build()
    
    # Validate: supports target must exist
    if supports and supports not in arg_map.graph:
        return ErrorBuilder("node_not_found", "E002")
            .message(f"Target node '{supports}' does not exist")
            .context(target=supports)
            .suggest_action(
                tool="new_claim",
                params={"label": label, "proposition": proposition},
                reason="Create claim first, add support later"
            )
            .build()
    
    # Create proposition
    prop_id = generate_id("prop")
    prop = Proposition(
        _id=prop_id,
        content=proposition
    )
    arg_map.add_proposition(prop)
    
    # Create claim node
    claim = ClaimNode(
        _id=label,
        label=label,
        proposition=prop_id
    )
    arg_map.add_claim(claim)
    
    # Build next actions
    next_actions = []
    needs_grounding = False
    
    # Add support relation if requested
    if supports:
        arg_map.add_support(label, supports)
        needs_grounding = True
        
        target_node = arg_map.get_node(supports)
        target_prop = (
            target_node.proposition
            if isinstance(target_node, ClaimNode)
            else target_node.conclusion
        )
        
        next_actions.append({
            "tool": "define_equivalence",
            "priority": "required",
            "params": {
                "prop1": prop_id,
                "prop2": target_prop
            },
            "reason": "Establish logical grounding for support relation"
        })
    
    # Add validation step
    next_actions.append({
        "tool": "run_checks",
        "priority": "recommended",
        "params": {
            "scope": label,
            "concern": "grounding" if needs_grounding else "general"
        },
        "reason": "Validate the new claim"
    })
    
    # Notify subscribers
    await ctx.session.send_resource_updated("argmap://summary")
    await ctx.session.send_resource_list_changed()
    
    return ClaimResult(
        status="success",
        message=f"Created claim '{label}'",
        claim_id=label,
        needs_grounding=needs_grounding,
        data={
            "label": label,
            "proposition_id": prop_id,
            "has_support_relation": bool(supports)
        },
        next_actions=next_actions
    )
```

## Testing Structure

```python
# tests/conftest.py
"""Pytest fixtures for testing."""

import pytest
from koala.graph.argument_map import ArgumentMap
from koala.models.nodes import ClaimNode, ArgumentNode
from koala.models.propositions import Proposition

@pytest.fixture
def empty_map():
    """Empty argument map."""
    return ArgumentMap()

@pytest.fixture
def simple_map():
    """Simple argument map with a few nodes."""
    map = ArgumentMap()
    
    # Add propositions
    p1 = Proposition(_id="p1", content="Climate change is real")
    p2 = Proposition(_id="p2", content="Global temperatures are rising")
    map.add_proposition(p1)
    map.add_proposition(p2)
    
    # Add claims
    c1 = ClaimNode(_id="c1", label="climate-claim", proposition="p1")
    c2 = ClaimNode(_id="c2", label="temp-claim", proposition="p2")
    map.add_claim(c1)
    map.add_claim(c2)
    
    # Add support relation
    map.add_support("c2", "c1")
    
    return map
```

```python
# tests/test_tools/test_authoring.py
"""Tests for authoring tools."""

import pytest
from koala.tools.authoring import new_claim
from koala.models.results import ClaimResult

def test_new_claim_creates_node(empty_map, mock_context):
    """Test that new_claim creates a claim node."""
    mock_context.request_context.lifespan_context.arg_map = empty_map
    
    result = new_claim(
        label="test-claim",
        proposition="Test proposition",
        ctx=mock_context
    )
    
    assert isinstance(result, ClaimResult)
    assert result.status == "success"
    assert result.claim_id == "test-claim"
    assert "test-claim" in empty_map.graph
    assert len(empty_map.propositions) == 1

def test_new_claim_duplicate_label(simple_map, mock_context):
    """Test that duplicate label returns error."""
    mock_context.request_context.lifespan_context.arg_map = simple_map
    
    result = new_claim(
        label="climate-claim",  # Already exists
        proposition="Duplicate",
        ctx=mock_context
    )
    
    assert result.isError
    # Check error structure
```

## Configuration File

```toml
# pyproject.toml
[project]
name = "koala"
version = "0.1.0"
description = "KOALA - Agent-centric MCP server for informal argument mapping"
authors = [
    {name = "Your Name", email = "your.email@example.com"}
]
readme = "README.md"
requires-python = ">=3.11"
dependencies = [
    "mcp>=1.2.0",
    "networkx>=3.0",
    "pydantic>=2.0",
    "matplotlib>=3.7",  # For visualization
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0",
    "pytest-asyncio>=0.21",
    "pytest-cov>=4.0",
    "black>=23.0",
    "ruff>=0.1",
    "mypy>=1.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/koala"]

[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"

[tool.black]
line-length = 100
target-version = ["py311"]

[tool.ruff]
line-length = 100
target-version = "py311"

[tool.mypy]
python_version = "3.11"
strict = true
```

## Benefits of This Structure

1. **Clear Separation**: Each component has its own directory
2. **Easy Testing**: Each module can be tested independently
3. **Type Safety**: Pydantic models throughout
4. **Extensibility**: Easy to add new tools/resources/prompts
5. **Maintainability**: Related code is grouped together
6. **Reusability**: Utilities and models are shared
7. **Clean Imports**: Clear import paths
8. **Documentation**: Structure is self-documenting

## Next Steps

1. Start with core models (`models/`)
2. Build graph abstraction (`graph/`)
3. Implement basic tools (`tools/authoring.py`)
4. Add resources (`resources/`)
5. Create prompts (`prompts/`)
6. Add validation logic (`validation/`)
7. Wire everything in `server.py`
8. Write tests

This structure will scale well from initial prototype to full implementation while keeping the codebase clean and maintainable.
