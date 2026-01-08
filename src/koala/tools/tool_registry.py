"""Dynamic tool registry for mode-aware MCP server.

This module implements a tool variant system that allows the MCP server to expose
different tool signatures based on the current editing mode (sketch, elaborate, review).

Architecture:
    The registry system consists of two main components:
    
    - **ToolVariant**: Represents a mode-specific version of a tool, allowing the
      same tool name to have different function signatures in different modes.
    
    - **ToolRegistry**: Central registry managing all tool variants, providing
      lookup methods for determining which tools should be available in each mode.

Key Concepts:
    **Tool Variants**: Multiple implementations of the same tool with different
    signatures for different modes. For example:
    
    - ``add_argument_sketch(label, gist)`` for sketch mode
    - ``add_argument_elaborate(label, gist, premises, conclusion, tags)`` for elaborate mode
    
    Both variants register under the name "add_argument" but are swapped
    dynamically when the mode changes.
    
    **Dynamic Swapping**: When the user switches modes (e.g., from sketch to elaborate),
    the system:
    
    1. Removes tools exclusive to the old mode
    2. Adds tools exclusive to the new mode
    3. Swaps variants for tools that exist in both modes
    4. Sends ``tools/list_changed`` notification to the client

Usage Example:
    Register a tool variant::
    
        TOOL_REGISTRY.register_variant(ToolVariant(
            fn=my_tool_sketch,
            name="my_tool",
            internal_name="my_tool_sketch",
            modes=["sketch"],
            description="Simplified version for sketch mode"
        ))
    
    Query tools for a mode::
    
        sketch_tools = TOOL_REGISTRY.get_all_tools_for_mode("sketch")
    
    Get specific variant::
    
        variant = TOOL_REGISTRY.get_variant_for_mode("my_tool", "sketch")

MCP Protocol Integration:
    When mode changes, the server sends a ``tools/list_changed`` notification
    to inform clients that they should refresh their tool list. Clients that
    don't support this notification will see stale tools until they manually refresh.

See Also:
    - :mod:`koala.tools.tools`: Tool implementations and registration
    - :mod:`koala.server`: Initial tool registration at startup
    - `MCP Specification <https://modelcontextprotocol.io/>`_: Protocol details
"""

from dataclasses import dataclass, field
from typing import Any, Callable

from koala.models.base import Mode


@dataclass
class ToolVariant:
    """A mode-specific variant of an MCP tool.
    
    Represents a single implementation of a tool that should be available in
    specific modes. Multiple variants can exist for the same tool name,
    allowing different function signatures in different modes.
    
    This enables the server to provide mode-appropriate interfaces: simple
    parameters in sketch mode, detailed parameters in elaborate mode.
    
    Attributes:
        fn: The function implementing this tool variant.
        name: External name exposed to MCP clients (e.g., 'add_argument').
        internal_name: Internal identifier for this variant (e.g., 'add_argument_sketch').
        modes: List of modes where this variant is available.
        description: Optional description override for this variant.
        metadata: Additional kwargs passed to ``mcp.add_tool()``.
    
    Examples:
        Simple tool available in one mode::
        
            variant = ToolVariant(
                fn=validate_graph,
                name="validate",
                internal_name="validate",
                modes=["review"],
                description="Check argument map for issues"
            )
        
        Tool with mode-specific signatures::
        
            # Sketch mode variant - simple parameters
            sketch_variant = ToolVariant(
                fn=add_claim_sketch,
                name="add_claim",  # Same external name
                internal_name="add_claim_sketch",
                modes=["sketch"]
            )
            
            # Elaborate mode variant - full parameters
            elaborate_variant = ToolVariant(
                fn=add_claim_elaborate,
                name="add_claim",  # Same external name
                internal_name="add_claim_elaborate",
                modes=["elaborate"]
            )
    
    Notes:
        - Multiple variants with the same ``name`` but different ``modes`` enable
          dynamic signature switching.
        - The ``internal_name`` must be unique across all variants.
        - When mode changes, the registry swaps variants with matching names.
    """
    
    fn: Callable[..., Any]
    """The function implementing this tool variant."""
    
    name: str
    """External tool name exposed to clients (e.g., 'add_argument')."""
    
    internal_name: str
    """Internal identifier for this variant (e.g., 'add_argument_sketch')."""
    
    modes: list[Mode]
    """List of modes where this tool variant is available."""
    
    description: str | None = None
    """Optional description override for this variant."""
    
    metadata: dict[str, Any] = field(default_factory=dict)
    """Additional metadata for tool registration."""


class ToolRegistry:
    """Central registry for mode-aware tool variants.
    
    Manages the mapping between tool names, modes, and their implementations.
    Provides lookup methods for determining which tools should be available
    in each mode and facilitates dynamic tool swapping during mode transitions.
    
    The registry maintains an internal mapping from tool names to lists of
    mode-specific variants. During mode switches, it calculates the difference
    between old and new tool sets to determine which tools to add/remove.
    
    Internal Structure:
        ``_variants``: ``dict[str, list[ToolVariant]]``
            Maps tool names to lists of mode-specific variants.
            
            Example::
            
                {
                    "add_argument": [sketch_variant, elaborate_variant],
                    "validate": [review_variant],
                    "instructions": [shared_variant]  # Available in all modes
                }
    
    Thread Safety:
        This implementation is not thread-safe. In the current architecture,
        all tool operations occur on the main event loop, so this is acceptable.
    
    Usage Pattern:
        At module initialization::
        
            registry = ToolRegistry()
            registry.register_variant(sketch_tool)
            registry.register_variant(elaborate_tool)
        
        At server startup::
        
            for variant in registry.get_all_tools_for_mode("sketch"):
                mcp.add_tool(variant.fn, name=variant.name, ...)
        
        During mode switch::
        
            old_tools = registry.get_tool_names_for_mode(old_mode)
            new_tools = registry.get_tool_names_for_mode(new_mode)
            tools_to_remove = old_tools - new_tools
            tools_to_add = new_tools - old_tools
    """
    
    def __init__(self) -> None:
        self._variants: dict[str, list[ToolVariant]] = {}
        """Map from tool name to list of variants."""
        
    def register_variant(self, variant: ToolVariant) -> None:
        """Register a mode-specific tool variant.
        
        Adds a tool variant to the registry. Multiple variants can be registered
        for the same tool name if they target different modes.
        
        Args:
            variant: The tool variant to register.
        
        Example:
            Register variants for different modes::
            
                # Sketch mode variant
                registry.register_variant(ToolVariant(
                    fn=add_claim_sketch,
                    name="add_claim",
                    internal_name="add_claim_sketch",
                    modes=["sketch"]
                ))
                
                # Elaborate mode variant (same name, different function)
                registry.register_variant(ToolVariant(
                    fn=add_claim_elaborate,
                    name="add_claim",
                    internal_name="add_claim_elaborate",
                    modes=["elaborate"]
                ))
        """
        if variant.name not in self._variants:
            self._variants[variant.name] = []
        self._variants[variant.name].append(variant)
        
    def get_variant_for_mode(self, tool_name: str, mode: Mode) -> ToolVariant | None:
        """Get the appropriate variant of a tool for a specific mode.
        
        Searches registered variants for the given tool name and returns the
        variant that is available in the specified mode. If multiple variants
        match (which shouldn't happen with proper registration), returns the
        first match.
        
        Args:
            tool_name: External name of the tool (e.g., "add_argument").
            mode: The mode to get the variant for ("sketch", "elaborate", or "review").
        
        Returns:
            The matching tool variant, or ``None`` if the tool is not
            available in this mode.
        
        Example::
        
            # Get the sketch variant of add_argument
            variant = registry.get_variant_for_mode("add_argument", "sketch")
            if variant:
                # variant.fn will be add_argument_sketch
                mcp.add_tool(variant.fn, name=variant.name)
        """
        variants = self._variants.get(tool_name, [])
        for variant in variants:
            if mode in variant.modes:
                return variant
        return None
    
    def get_all_tools_for_mode(self, mode: Mode) -> list[ToolVariant]:
        """Get all tool variants available in a specific mode.
        
        Returns a list of all tool variants that should be registered
        when the server is in the specified mode. This includes both
        mode-specific tools and shared tools available in all modes.
        
        Args:
            mode: The mode to get tools for ("sketch", "elaborate", or "review").
        
        Returns:
            List of all tool variants available in the mode.
        
        Example::
        
            # Get all tools for sketch mode
            sketch_tools = registry.get_all_tools_for_mode("sketch")
            for variant in sketch_tools:
                mcp.add_tool(variant.fn, name=variant.name, ...)
            
            # Typical sketch mode tools:
            # - add_claim_sketch
            # - add_argument_sketch
            # - connect_sketch
            # - remove
            # - instructions, inspect_graph, etc. (shared)
        """
        tools = []
        for variants in self._variants.values():
            for variant in variants:
                if mode in variant.modes:
                    tools.append(variant)
        return tools
    
    def get_tool_names_for_mode(self, mode: Mode) -> set[str]:
        """Get the set of tool names available in a specific mode.
        
        Returns just the external tool names (not the full variants) available
        in the specified mode. Useful for calculating the difference between
        modes during mode switches.
        
        Args:
            mode: The mode to get tool names for ("sketch", "elaborate", or "review").
        
        Returns:
            Set of external tool names available in the mode.
        
        Example::
        
            # Calculate tools to add/remove when switching modes
            old_tools = registry.get_tool_names_for_mode("sketch")
            new_tools = registry.get_tool_names_for_mode("elaborate")
            
            tools_to_remove = old_tools - new_tools
            # Usually empty, elaborate includes most sketch tools
            
            tools_to_add = new_tools - old_tools
            # Typically: {"edit", "inspect_node"}
        """
        return {variant.name for variant in self.get_all_tools_for_mode(mode)}


# Global registry instance
TOOL_REGISTRY = ToolRegistry()
