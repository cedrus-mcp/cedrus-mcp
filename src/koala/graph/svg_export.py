"""SVG export for argument maps using GraphViz."""

from __future__ import annotations

import subprocess
import textwrap
from typing import Literal

import graphviz  # type: ignore[import-untyped]
import networkx as nx
from mcp.server.fastmcp.utilities.logging import get_logger
from unidecode import unidecode

from koala.graph.argument_map import ArgumentMap
from koala.models.base import NodeLabel
from koala.models.nodes import ArgumentNode, ClaimNode

logger = get_logger("koala.svg_export")

# Constants
_ARROWWIDTH = "2"
_MAX_TEXT_WIDTH = 40  # characters per line for text wrapping

# Node template constants
_CLAIM_NODE_TEMPLATE = """<
    <TABLE BORDER="4" COLOR="{bgcolor}" CELLPADDING="2" CELLSPACING="2"
    BGCOLOR="white" STYLE="rounded" ALIGN="center">
    <TR><TD BORDER="0"><FONT FACE="Arial, Helvetica, sans-serif"
    POINT-SIZE="12.0"><B>{label}</B></FONT></TD></TR>
    <TR><TD BORDER="0"><FONT FACE="Arial, Helvetica, sans-serif"
    POINT-SIZE="10.0">{text}</FONT></TD></TR>
    </TABLE>
    >"""

_ARGUMENT_NODE_TEMPLATE = """<
    <TABLE BORDER="4" COLOR="{bgcolor}" CELLPADDING="2" CELLSPACING="2"
    BGCOLOR="{bgcolor}" STYLE="rounded" ALIGN="center">
    <TR><TD BORDER="0"><FONT FACE="Arial, Helvetica, sans-serif"
    POINT-SIZE="12.0"><B>{label}</B></FONT></TD></TR>
    <TR><TD BORDER="0"><FONT FACE="Arial, Helvetica, sans-serif"
    POINT-SIZE="10.0">{text}</FONT></TD></TR>
    </TABLE>
    >"""


def export_svg(
    arg_map: ArgumentMap,
    *,
    layout_direction: Literal["BT", "TB", "LR", "RL"] = "BT",
    tag_colors: dict[str, str] | None = None,
    include_review_flags: bool = False,
) -> str:
    """
    Export ArgumentMap to SVG via GraphViz.
    
    Parameters
    ----------
    arg_map : ArgumentMap
        The argument map to export
    layout_direction : {"BT", "TB", "LR", "RL"}, default "BT"
        Graph layout direction:
        - "BT": Bottom to top (central claims at bottom)
        - "TB": Top to bottom
        - "LR": Left to right
        - "RL": Right to left
    tag_colors : dict[str, str] | None
        Mapping of tag names to hex colors for argument nodes.
        Example: {"critical": "#FF6B6B", "supporting": "#51CF66"}
        Untagged arguments use default light blue.
    include_review_flags : bool, default False
        If True, highlight nodes with needs_review_flag with red borders
        
    Returns
    -------
    str
        SVG markup as string
        
    Raises
    ------
    RuntimeError
        If graphviz system package is not installed
        
    Examples
    --------
    >>> svg_string = export_svg(arg_map)
    >>> with open("map.svg", "w") as f:
    ...     f.write(svg_string)
    """
    _check_graphviz_installed()
    
    # Default tag colors
    if tag_colors is None:
        tag_colors = {}
    
    # Preprocess the argument graph
    processed_graph = _preprocess_argument_graph(arg_map, tag_colors, include_review_flags)
    
    # Create graphviz Digraph
    dot = _create_graphviz_graph(layout_direction)
    
    # Get root nodes for subgraph grouping
    roots = arg_map.list_roots()
    
    # Add root nodes to a subgraph (same rank)
    if roots:
        subgraph = graphviz.Digraph(name="central_claims")
        subgraph.attr(rank="sink")
        for root_label in roots:
            if root_label in processed_graph.nodes:
                node_data = processed_graph.nodes[root_label]
                subgraph.node(root_label, label=node_data["label"])
        dot.subgraph(subgraph)
    
    # Add non-root nodes
    for node_label, node_data in processed_graph.nodes.items():
        if node_label not in roots:
            dot.node(node_label, label=node_data["label"])
    
    # Add edges
    for from_label, to_label, edge_data in processed_graph.edges(data=True):
        dot.edge(
            from_label,
            to_label,
            color=edge_data["color"],
            penwidth=edge_data["penwidth"],
        )
    
    # Render to SVG
    svg_string = dot.pipe(encoding='utf-8', format='svg')
    
    return str(svg_string)


def _preprocess_argument_graph(
    arg_map: ArgumentMap,
    tag_colors: dict[str, str],
    include_review_flags: bool,
) -> nx.DiGraph[NodeLabel]:
    """
    Convert ArgumentMap to preprocessed NetworkX DiGraph.
    
    This step makes a deep copy and preprocesses all node and edge attributes
    before passing to GraphViz, similar to logikon's approach.
    """
    G: nx.DiGraph[NodeLabel] = nx.DiGraph()
    
    # Process nodes
    for node_label in arg_map.argument_graph.nodes():
        node = arg_map.get_node(node_label)
        
        if isinstance(node, ClaimNode):
            label = _create_claim_label(node, arg_map, include_review_flags)
        elif isinstance(node, ArgumentNode):
            label = _create_argument_label(node, arg_map, tag_colors, include_review_flags)
        else:
            logger.warning(f"Unknown node type for {node_label}")
            continue
        
        G.add_node(node_label, label=label)
    
    # Process edges
    for from_label, to_label in arg_map.argument_graph.edges():
        relation = arg_map.get_dialectic_relation(from_label, to_label)
        
        if relation:
            edge_color = "darkgreen" if relation.relation_type == "support" else "red"
            G.add_edge(
                from_label,
                to_label,
                color=edge_color,
                penwidth=_ARROWWIDTH,
            )
    
    return G


def _create_graphviz_graph(layout_direction: str) -> graphviz.Digraph:
    """Create and configure GraphViz Digraph object."""
    dot = graphviz.Digraph(
        name="koala_argument_map",
        comment="Created with KOALA MCP Server",
        graph_attr={
            "format": "svg",
            "rankdir": layout_direction,
            "ratio": "compress",
            "orientation": "portrait",
            "bgcolor": "transparent",
            "splines": "ortho",  # Orthogonal edge routing
            "nodesep": "0.5",
            "ranksep": "0.75",
        },
        node_attr={
            "shape": "none",  # We use HTML tables
            "margin": "0",
        },
        edge_attr={
            "penwidth": _ARROWWIDTH,
        }
    )
    return dot


def _create_claim_label(
    node: ClaimNode,
    arg_map: ArgumentMap,
    include_review_flags: bool,
) -> str:
    """Create HTML label for a claim node."""
    
    # Get proposition content
    prop = arg_map.get_proposition(node.proposition_id)
    text = prop.content if prop else "[No proposition]"
    
    # Preprocess and wrap text
    text = _preprocess_text(text)
    text = _wrap_text(text, _MAX_TEXT_WIDTH)
    
    # Determine border color
    if include_review_flags and node.needs_review_flag:
        border_color = "#FF0000"  # Red for review
    else:
        border_color = "#000000"  # Black border
    
    # Format label
    label_text = _preprocess_text(node.label)
    
    # Create HTML label
    html_label = _CLAIM_NODE_TEMPLATE.format(
        label=label_text,
        text=text,
        bgcolor=border_color
    )
    
    return html_label


def _create_argument_label(
    node: ArgumentNode,
    arg_map: ArgumentMap,
    tag_colors: dict[str, str],
    include_review_flags: bool,
) -> str:
    """Create HTML label for an argument node."""
    
    # Get gist
    text = node.gist if node.gist else "[No gist]"
    text = _preprocess_text(text)
    text = _wrap_text(text, _MAX_TEXT_WIDTH)
    
    # Determine background color based on tags
    bgcolor = _get_argument_color(node, tag_colors)
        
    # Format label
    label_text = _preprocess_text(node.label)
    
    # Create HTML label
    html_label = _ARGUMENT_NODE_TEMPLATE.format(
        label=label_text,
        text=text,
        bgcolor=bgcolor
    )
    
    return html_label


def _get_argument_color(node: ArgumentNode, tag_colors: dict[str, str]) -> str:
    """Get background color for argument node based on tags."""
    
    # Check if node has any tags with specified colors
    for tag in node.tags:
        if tag in tag_colors:
            return tag_colors[tag]
    
    # Default: light blue
    return "#B3E5FC"


def _preprocess_text(text: str) -> str:
    """Preprocess text for GraphViz HTML labels."""
    
    # Convert unicode to ASCII
    text = unidecode(text)
    
    # Escape special HTML/GraphViz characters
    text = text.replace("&", "+")  # & causes issues
    text = text.replace("<", "&lt;")
    text = text.replace(">", "&gt;")
    
    # Handle colons (can cause issues in GraphViz)
    if ":" in text:
        text = text.replace(":", " --")
    
    return text


def _wrap_text(text: str, width: int) -> str:
    """Wrap text to specified width for display."""
    lines = textwrap.wrap(text, width=width, break_long_words=False)
    return "<BR/>".join(lines)  # HTML line break for GraphViz


def _check_graphviz_installed() -> None:
    """Check if GraphViz is installed on the system."""
    try:
        subprocess.run(
            ["dot", "-V"],
            check=True,
            capture_output=True,
            text=True
        )
    except (subprocess.CalledProcessError, FileNotFoundError) as err:
        logger.error("GraphViz 'dot' command not found")
        msg = (
            "GraphViz is not installed or not in PATH. "
            "Please install GraphViz:\n"
            "  macOS: brew install graphviz\n"
            "  Ubuntu/Debian: sudo apt-get install graphviz\n"
            "  Windows: Download from https://graphviz.org/download/"
        )
        raise RuntimeError(msg) from err
