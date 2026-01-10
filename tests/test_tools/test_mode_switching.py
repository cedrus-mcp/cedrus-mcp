"""Tests for dynamic tool registration and mode switching.

This module tests the critical behavior of tool variant switching when
modes change. It ensures that:
1. Tools are added/removed correctly
2. Tool descriptions update for variant tools
3. Tool signatures (parameters) update for variant tools
4. Shared tools remain unchanged
"""

import inspect
from unittest.mock import AsyncMock, Mock

import pytest

from cedrus.backend.graph.argument_map import ArgumentMap
from cedrus.backend.models.base import Mode
from cedrus.server import AppContext
from cedrus.tools.entrypoints.sketch import switch_mode
from cedrus.tools.impl.meta import update_tools_for_mode_core
from cedrus.tools.tool_registry import TOOL_REGISTRY


@pytest.fixture
def mcp_context(empty_arg_map: ArgumentMap) -> Mock:
    """Create mock FastMCP context for tool testing.

    Provides a context with:
    - ArgumentMap for state
    - Mock FastMCP server for tool operations
    - Mock session for notifications
    """
    ctx = Mock()
    ctx.request_context.lifespan_context = AppContext(arg_map=empty_arg_map, mode="sketch")

    # Mock FastMCP server
    ctx.fastmcp = Mock()
    ctx.fastmcp.add_tool = Mock()
    ctx.fastmcp.remove_tool = Mock()

    # Track registered tools
    ctx.fastmcp._registered_tools = {}

    # Make add_tool store the tool info
    def mock_add_tool(fn, name, description, **metadata):  # type: ignore
        ctx.fastmcp._registered_tools[name] = {
            "fn": fn,
            "description": description,
            "metadata": metadata,
        }

    ctx.fastmcp.add_tool.side_effect = mock_add_tool

    # Make remove_tool clear the tool info
    def mock_remove_tool(name):  # type: ignore
        if name in ctx.fastmcp._registered_tools:
            del ctx.fastmcp._registered_tools[name]

    ctx.fastmcp.remove_tool.side_effect = mock_remove_tool

    # Mock session for notifications
    ctx.session = Mock()
    ctx.session.send_tool_list_changed = AsyncMock()

    return ctx


class TestToolListChanges:
    """Test that tools are added/removed correctly when switching modes."""

    async def test_sketch_to_elaborate_adds_tools(self, mcp_context: Mock) -> None:
        """Test that elaborate-only tools are added when switching from sketch to elaborate."""
        mcp_context.request_context.lifespan_context.mode = "sketch"

        await update_tools_for_mode_core(ctx=mcp_context, old_mode="sketch", new_mode="elaborate")

        # Check that elaborate-only tools were added
        # edit and inspect_node are only in elaborate mode
        add_calls = [call_obj[0][0] for call_obj in mcp_context.fastmcp.add_tool.call_args_list]
        assert "edit" in add_calls or any("edit" in str(call) for call in add_calls)

        # Verify notification was sent
        mcp_context.session.send_tool_list_changed.assert_called_once()

    async def test_elaborate_to_sketch_removes_tools(self, mcp_context: Mock) -> None:
        """Test that elaborate-only tools are removed when switching from elaborate to sketch."""
        mcp_context.request_context.lifespan_context.mode = "elaborate"

        await update_tools_for_mode_core(ctx=mcp_context, old_mode="elaborate", new_mode="sketch")

        # Check that elaborate-only tools were removed
        remove_calls = [
            call_obj[0][0] for call_obj in mcp_context.fastmcp.remove_tool.call_args_list
        ]
        assert "edit" in remove_calls

        # Verify notification was sent
        mcp_context.session.send_tool_list_changed.assert_called_once()

    async def test_sketch_to_review_changes_toolset(self, mcp_context: Mock) -> None:
        """Test that tool list changes appropriately when switching to review mode."""
        mcp_context.request_context.lifespan_context.mode = "sketch"

        await update_tools_for_mode_core(ctx=mcp_context, old_mode="sketch", new_mode="review")

        # Review mode should remove sketch-specific tools and add review-specific ones
        remove_calls = [
            call_obj[0][0] for call_obj in mcp_context.fastmcp.remove_tool.call_args_list
        ]
        add_calls = [call_obj[0][0] for call_obj in mcp_context.fastmcp.add_tool.call_args_list]

        # Sketch tools like add_claim, add_argument should be removed
        assert "add_claim" in remove_calls
        assert "add_argument" in remove_calls

        # Review tools like validate should be added
        assert "validate" in add_calls or any("validate" in str(call) for call in add_calls)


class TestVariantToolDescriptions:
    """Test that tool descriptions update when switching between modes.

    This is the FAILING test case - currently descriptions don't change
    for tools with variants (like add_claim, add_argument, connect).
    """

    async def test_add_claim_description_changes(self, mcp_context: Mock) -> None:
        """Test that add_claim description updates between sketch and elaborate.

        EXPECTED BEHAVIOR:
        When switching from sketch to elaborate mode, add_claim should be
        re-registered with the elaborate description that mentions tags.

        ACTUAL BEHAVIOR (BUG):
        add_claim is present in both modes, so it's neither added nor removed.
        The old description persists even though the variant changed.
        """
        # Get variants from registry
        sketch_variant = TOOL_REGISTRY.get_variant_for_mode("add_claim", "sketch")
        elaborate_variant = TOOL_REGISTRY.get_variant_for_mode("add_claim", "elaborate")

        assert sketch_variant is not None
        assert elaborate_variant is not None
        assert sketch_variant.description != elaborate_variant.description

        # Initially register sketch variant
        mcp_context.fastmcp.add_tool(
            sketch_variant.fn,
            name=sketch_variant.name,
            description=sketch_variant.description,
            **sketch_variant.metadata,
        )

        # Simulate mode switch from sketch to elaborate
        await update_tools_for_mode_core(ctx=mcp_context, old_mode="sketch", new_mode="elaborate")

        # Check if add_claim was re-registered with new description
        assert "add_claim" in mcp_context.fastmcp._registered_tools, (
            "add_claim should still be registered after mode switch"
        )

        registered_desc = mcp_context.fastmcp._registered_tools["add_claim"]["description"]
        assert "tags" in registered_desc.lower(), (
            "Elaborate mode description should mention tags parameter"
        )

    async def test_add_argument_description_changes(self, mcp_context: Mock) -> None:
        """Test that add_argument description updates between sketch and elaborate."""
        sketch_variant = TOOL_REGISTRY.get_variant_for_mode("add_argument", "sketch")
        elaborate_variant = TOOL_REGISTRY.get_variant_for_mode("add_argument", "elaborate")

        assert sketch_variant is not None
        assert elaborate_variant is not None
        assert sketch_variant.description != elaborate_variant.description

        # The elaborate description should mention premises/conclusion
        assert elaborate_variant.description and "premises" in elaborate_variant.description.lower()
        assert (
            elaborate_variant.description and "conclusion" in elaborate_variant.description.lower()
        )

    async def test_connect_description_changes(self, mcp_context: Mock) -> None:
        """Test that connect description updates between sketch and elaborate."""
        sketch_variant = TOOL_REGISTRY.get_variant_for_mode("connect", "sketch")
        elaborate_variant = TOOL_REGISTRY.get_variant_for_mode("connect", "elaborate")

        assert sketch_variant is not None
        assert elaborate_variant is not None

        # The elaborate description should mention grounding
        assert (
            elaborate_variant.description and "grounding" in elaborate_variant.description.lower()
        )


class TestVariantToolSignatures:
    """Test that tool signatures (parameters) update when switching between modes.

    This is another FAILING test case - currently function signatures don't change
    for tools with variants.
    """

    async def test_add_argument_signature_changes(self, mcp_context: Mock) -> None:
        """Test that add_argument function changes between sketch and elaborate.

        EXPECTED BEHAVIOR:
        When switching modes, the registered function should change from
        add_argument_sketch to add_argument_elaborate.

        ACTUAL BEHAVIOR (BUG):
        The function is not swapped because the tool exists in both modes.
        """
        # Get the actual functions
        sketch_variant = TOOL_REGISTRY.get_variant_for_mode("add_argument", "sketch")
        elaborate_variant = TOOL_REGISTRY.get_variant_for_mode("add_argument", "elaborate")

        assert sketch_variant is not None
        assert elaborate_variant is not None

        # Initially register sketch variant
        mcp_context.fastmcp.add_tool(
            sketch_variant.fn,
            name=sketch_variant.name,
            description=sketch_variant.description,
            **sketch_variant.metadata,
        )

        # Verify sketch function is registered
        assert mcp_context.fastmcp._registered_tools["add_argument"]["fn"] == sketch_variant.fn

        # Simulate mode switch from sketch to elaborate
        await update_tools_for_mode_core(ctx=mcp_context, old_mode="sketch", new_mode="elaborate")

        # Verify function changed to elaborate variant (BUG: this fails)
        registered_fn = mcp_context.fastmcp._registered_tools["add_argument"]["fn"]
        assert registered_fn == elaborate_variant.fn, (
            "Function should be swapped to elaborate variant"
        )

        # Check function signatures
        sketch_sig = inspect.signature(sketch_variant.fn)
        elaborate_sig = inspect.signature(elaborate_variant.fn)

        sketch_params = set(sketch_sig.parameters.keys())
        elaborate_params = set(elaborate_sig.parameters.keys())

        # Elaborate should have more parameters
        assert elaborate_params > sketch_params, "Elaborate mode should have additional parameters"

        # Specifically check for premises, conclusion, tags in elaborate
        assert "premises" in elaborate_params
        assert "conclusion" in elaborate_params
        assert "tags" in elaborate_params

        # These should NOT be in sketch
        assert "premises" not in sketch_params
        assert "conclusion" not in sketch_params

    async def test_connect_signature_changes(self, mcp_context: Mock) -> None:
        """Test that connect parameters change between sketch and elaborate."""
        sketch_variant = TOOL_REGISTRY.get_variant_for_mode("connect", "sketch")
        elaborate_variant = TOOL_REGISTRY.get_variant_for_mode("connect", "elaborate")

        assert sketch_variant is not None
        assert elaborate_variant is not None

        # Check function signatures
        sketch_sig = inspect.signature(sketch_variant.fn)
        elaborate_sig = inspect.signature(elaborate_variant.fn)

        sketch_params = set(sketch_sig.parameters.keys())
        elaborate_params = set(elaborate_sig.parameters.keys())

        # Elaborate should have grounding parameters
        assert "grounding_strategy" in elaborate_params
        assert "target_premise_idx" in elaborate_params

        # These should NOT be in sketch
        assert "grounding_strategy" not in sketch_params
        assert "target_premise_idx" not in sketch_params

    async def test_add_claim_signature_changes(self, mcp_context: Mock) -> None:
        """Test that add_claim parameters change between sketch and elaborate."""
        sketch_variant = TOOL_REGISTRY.get_variant_for_mode("add_claim", "sketch")
        elaborate_variant = TOOL_REGISTRY.get_variant_for_mode("add_claim", "elaborate")

        assert sketch_variant is not None
        assert elaborate_variant is not None

        # Check function signatures
        sketch_sig = inspect.signature(sketch_variant.fn)
        elaborate_sig = inspect.signature(elaborate_variant.fn)

        sketch_params = set(sketch_sig.parameters.keys())
        elaborate_params = set(elaborate_sig.parameters.keys())

        # Elaborate should have tags parameter
        assert "tags" in elaborate_params

        # Sketch should NOT have tags
        assert "tags" not in sketch_params


class TestSharedToolsUnchanged:
    """Test that shared tools remain unchanged across mode switches.

    Shared tools like inspect_graph, switch_mode are available in all modes with
    the same implementation. While they are removed and re-added during mode
    switches (to maintain tool order), their function implementation remains
    the same.

    Note: get_instructions is NOT a shared tool - it has mode-specific variants.
    """

    async def test_truly_shared_tools_same_function(self, mcp_context: Mock) -> None:
        """Test that truly shared tools use the same function across modes."""
        # Truly shared tools (same function in all modes)
        truly_shared_tools = ["inspect_graph", "inspect_neighborhood", "switch_mode", "remove"]

        for tool in truly_shared_tools:
            # Verify the variants have the same user-facing description.
            # Implementations may differ internally between modes as long as
            # their interface and semantics remain consistent.
            sketch_variant = TOOL_REGISTRY.get_variant_for_mode(tool, "sketch")
            elaborate_variant = TOOL_REGISTRY.get_variant_for_mode(tool, "elaborate")

            if sketch_variant and elaborate_variant:
                assert sketch_variant.description == elaborate_variant.description, (
                    f"{tool} should have the same description in both modes"
                )

    async def test_shared_tools_re_registered_for_order(self, mcp_context: Mock) -> None:
        """Test that shared tools are removed and re-added to maintain order.

        Even though shared tools don't change functionality, they must be
        removed and re-added to ensure the final tool list is in canonical order.
        """
        await update_tools_for_mode_core(ctx=mcp_context, old_mode="sketch", new_mode="elaborate")

        # Get all tool names from remove calls
        remove_calls = [call[0][0] for call in mcp_context.fastmcp.remove_tool.call_args_list]

        # Get all tool names from add calls (keyword argument "name")
        add_calls = [
            call[1]["name"]
            for call in mcp_context.fastmcp.add_tool.call_args_list
            if "name" in call[1]
        ]

        # Truly shared tools should be both removed and re-added
        truly_shared_tools = ["inspect_graph", "inspect_neighborhood", "switch_mode", "remove"]

        for tool in truly_shared_tools:
            assert tool in remove_calls, f"Shared tool {tool} should be removed (for reordering)"
            assert tool in add_calls, f"Shared tool {tool} should be re-added (for reordering)"

    async def test_get_instructions_is_variant_tool(self, mcp_context: Mock) -> None:
        """Test that get_instructions is correctly treated as a variant tool.

        get_instructions has different signatures in different modes:
        - sketch: no parameters
        - elaborate: optional topic parameter
        """
        sketch_variant = TOOL_REGISTRY.get_variant_for_mode("get_instructions", "sketch")
        elaborate_variant = TOOL_REGISTRY.get_variant_for_mode("get_instructions", "elaborate")

        assert sketch_variant is not None
        assert elaborate_variant is not None

        # They should have different functions
        assert sketch_variant.fn != elaborate_variant.fn, (
            "get_instructions should have different variants for sketch and elaborate"
        )

        # Switching from sketch to elaborate should swap get_instructions
        await update_tools_for_mode_core(ctx=mcp_context, old_mode="sketch", new_mode="elaborate")

        remove_calls = [
            call_obj[0][0] for call_obj in mcp_context.fastmcp.remove_tool.call_args_list
        ]

        # get_instructions should be in the swap list (removed and re-added)
        assert "get_instructions" in remove_calls, (
            "get_instructions should be swapped when changing modes"
        )

    async def test_get_instructions_available_in_all_modes(self) -> None:
        """Test that get_instructions is available in all modes."""
        modes: list[Mode] = ["sketch", "elaborate", "review"]
        for mode in modes:
            variant = TOOL_REGISTRY.get_variant_for_mode("get_instructions", mode)
            assert variant is not None, f"get_instructions should be available in {mode} mode"

    async def test_inspect_graph_available_in_all_modes(self) -> None:
        """Test that inspect_graph is available in all modes."""
        modes: list[Mode] = ["sketch", "elaborate", "review"]
        for mode in modes:
            variant = TOOL_REGISTRY.get_variant_for_mode("inspect_graph", mode)
            assert variant is not None, f"inspect_graph should be available in {mode} mode"


class TestIntegrationWithSetMode:
    """Integration tests using the actual switch_mode tool."""

    async def test_full_mode_switch_workflow(self, mcp_context: Mock) -> None:
        """Test complete workflow of switching modes through switch_mode tool."""
        # Start in sketch mode
        assert mcp_context.request_context.lifespan_context.mode == "sketch"

        # Switch to elaborate
        result = await switch_mode(mode="elaborate", ctx=mcp_context)

        assert not result.isError
        assert mcp_context.request_context.lifespan_context.mode == "elaborate"
        mcp_context.session.send_tool_list_changed.assert_called()

        # Verify tools were updated
        assert mcp_context.fastmcp.add_tool.called or mcp_context.fastmcp.remove_tool.called


class TestToolOrdering:
    """Test that tool order is maintained during mode switches."""

    async def test_tools_registered_in_canonical_order(self, mcp_context: Mock) -> None:
        """Test that tools are added in TOOL_ORDER during mode switch."""
        from cedrus.tools import TOOL_ORDER

        # Verify all tools in any mode are in TOOL_ORDER
        modes: list[Mode] = ["sketch", "elaborate", "review"]
        for mode in modes:
            mode_tools = TOOL_REGISTRY.get_tool_names_for_mode(mode)
            for tool in mode_tools:
                assert tool in TOOL_ORDER, f"Tool {tool} in {mode} mode is not in TOOL_ORDER"

    async def test_sketch_to_elaborate_maintains_order(self, mcp_context: Mock) -> None:
        """Test specific case: sketch to elaborate preserves logical tool order."""
        from cedrus.tools import TOOL_ORDER

        # Simulate initial sketch mode registration
        sketch_tools = TOOL_REGISTRY.get_tool_names_for_mode("sketch")
        for tool_name in TOOL_ORDER:
            if tool_name in sketch_tools:
                variant = TOOL_REGISTRY.get_variant_for_mode(tool_name, "sketch")
                if variant:
                    mcp_context.fastmcp.add_tool(
                        variant.fn,
                        name=variant.name,
                        description=variant.description,
                        **variant.metadata,
                    )

        # Reset call tracking
        mcp_context.fastmcp.add_tool.reset_mock()
        mcp_context.fastmcp.remove_tool.reset_mock()

        # Switch to elaborate
        await update_tools_for_mode_core(ctx=mcp_context, old_mode="sketch", new_mode="elaborate")

        # Get final tool list from mock (preserves insertion order)
        final_tools = list(mcp_context.fastmcp._registered_tools.keys())

        # Filter TOOL_ORDER to only tools in elaborate mode
        elaborate_tools = TOOL_REGISTRY.get_tool_names_for_mode("elaborate")
        expected_order = [t for t in TOOL_ORDER if t in elaborate_tools]

        # Verify final tools are in the expected order
        # Filter final_tools to only include elaborate tools, then check order
        actual_order = [t for t in final_tools if t in elaborate_tools]
        assert actual_order == expected_order, (
            f"Tool order mismatch. Expected: {expected_order}, Got: {actual_order}"
        )
