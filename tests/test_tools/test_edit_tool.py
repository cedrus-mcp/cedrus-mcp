"""Unit tests for edit tool."""

import pytest
from unittest.mock import Mock
from cedrus.tools.tools import add_claim_elaborate, add_argument_elaborate, edit
from cedrus.server import AppContext
from cedrus.graph.argument_map import ArgumentMap


@pytest.fixture
def tool_context(empty_arg_map: ArgumentMap) -> Mock:
    """Create mock context for tool testing in elaborate mode."""
    ctx = Mock()
    ctx.request_context.lifespan_context = AppContext(
        arg_map=empty_arg_map,
        mode="elaborate"  # edit is only available in elaborate mode
    )
    return ctx


async def test_edit_claim_proposition(tool_context: Mock) -> None:
    """Test editing a claim's proposition."""
    # Add a claim
    await add_claim_elaborate(label="C1", ctx=tool_context, proposition="Original")
    
    # Edit it
    result = edit(
        label="C1",
        field="proposition",
        ctx=tool_context,
        edit_options={"new_value": "Updated"}
    )
    
    assert not result.isError
    arg_map = tool_context.request_context.lifespan_context.arg_map
    node = arg_map.get_node("C1")
    prop = arg_map.get_proposition(node.proposition_id)
    assert prop.content == "Updated"


async def test_edit_argument_gist(tool_context: Mock) -> None:
    """Test editing an argument's gist."""
    # Add an argument
    await add_argument_elaborate(
        label="A1",
        ctx=tool_context,
        gist="Original gist"
    )
    
    # Edit it
    result = edit(
        label="A1",
        field="gist",
        ctx=tool_context,
        edit_options={"new_value": "Updated gist"}
    )
    
    assert not result.isError
    arg_map = tool_context.request_context.lifespan_context.arg_map
    node = arg_map.get_node("A1")
    assert node.gist == "Updated gist"


async def test_edit_argument_conclusion(tool_context: Mock) -> None:
    """Test editing an argument's conclusion."""
    # Add an argument
    await add_argument_elaborate(
        label="A1",
        ctx=tool_context,
        gist="Argument",
    )
    
    # Edit conclusion
    result = edit(
        label="A1",
        field="conclusion",
        ctx=tool_context,
        edit_options={"new_value": "New conclusion"}
    )
    
    assert not result.isError
    arg_map = tool_context.request_context.lifespan_context.arg_map
    node = arg_map.get_node("A1")
    # conclusion is a proposition ID string
    prop = arg_map.get_proposition(node.conclusion)
    assert prop is not None
    assert prop.content == "New conclusion"


def test_edit_nonexistent_node_fails(tool_context: Mock) -> None:
    """Test editing a non-existent node raises KeyError."""
    result = edit(
            label="NONEXISTENT",
            field="proposition",
            ctx=tool_context,
            edit_options={"new_value": "Test"}
        )
    assert result.structuredContent is not None
    assert result.structuredContent["status"] == "failure"


async def test_edit_tags(tool_context: Mock) -> None:
    """Test editing tags on a node."""
    # Add a claim
    await add_claim_elaborate(label="C1", ctx=tool_context, proposition="Test")
    
    # Add a tag
    result = edit(
        label="C1",
        field="tags",
        ctx=tool_context,
        edit_options={"new_value": "important"}
    )
    
    assert not result.isError


async def test_edit_metadata(tool_context: Mock) -> None:
    """Test editing metadata on a node."""
    # Add a claim
    await add_claim_elaborate(label="C1", ctx=tool_context, proposition="Test")
    
    # Add metadata
    result = edit(
        label="C1",
        field="metadata",
        ctx=tool_context,
        edit_options={"key": "source", "new_value": "paper.pdf"}
    )
    
    assert not result.isError


async def test_edit_premises_add_new(tool_context: Mock) -> None:
    """Test adding a new premise to an argument."""
    # Add an argument
    await add_argument_elaborate(
        label="A1",
        ctx=tool_context,
        gist="Test argument",
        premises=["First premise"],
        conclusion="Conclusion"
    )
    
    # Add a new premise
    result = edit(
        label="A1",
        field="premises",
        ctx=tool_context,
        edit_options={"new_value": "Second premise"}
    )
    
    assert not result.isError
    arg_map = tool_context.request_context.lifespan_context.arg_map
    node = arg_map.get_node("A1")
    premise_contents = [arg_map.get_proposition(pid).content for pid in node.premises]
    assert "First premise" in premise_contents
    assert "Second premise" in premise_contents
    assert len(premise_contents) == 2


async def test_edit_premises_remove_existing(tool_context: Mock) -> None:
    """Test removing an existing premise from an argument."""
    # Add an argument with two premises
    await add_argument_elaborate(
        label="A1",
        ctx=tool_context,
        gist="Test argument",
        premises=["First premise", "Second premise"],
        conclusion="Conclusion"
    )
    
    # Remove the first premise
    result = edit(
        label="A1",
        field="premises",
        ctx=tool_context,
        edit_options={"old_value": "First premise"}
    )
    
    assert not result.isError
    arg_map = tool_context.request_context.lifespan_context.arg_map
    node = arg_map.get_node("A1")
    premise_contents = [arg_map.get_proposition(pid).content for pid in node.premises]
    assert "First premise" not in premise_contents
    assert "Second premise" in premise_contents
    assert len(premise_contents) == 1


async def test_edit_premises_update_existing(tool_context: Mock) -> None:
    """Test updating an existing premise content."""
    # Add an argument
    await add_argument_elaborate(
        label="A1",
        ctx=tool_context,
        gist="Test argument",
        premises=["Original premise"],
        conclusion="Conclusion"
    )
    
    # Update the premise
    result = edit(
        label="A1",
        field="premises",
        ctx=tool_context,
        edit_options={"old_value": "Original premise", "new_value": "Updated premise"}
    )
    
    assert not result.isError
    arg_map = tool_context.request_context.lifespan_context.arg_map
    node = arg_map.get_node("A1")
    premise_contents = [arg_map.get_proposition(pid).content for pid in node.premises]
    assert "Original premise" not in premise_contents
    assert "Updated premise" in premise_contents
    assert len(premise_contents) == 1


async def test_edit_premises_neither_old_nor_new_fails(tool_context: Mock) -> None:
    """Test that providing neither old_value nor new_value fails."""
    # Add an argument
    await add_argument_elaborate(
        label="A1",
        ctx=tool_context,
        gist="Test argument",
        premises=["First premise"],
        conclusion="Conclusion"
    )
    
    # Try to edit without providing values
    result = edit(
        label="A1",
        field="premises",
        ctx=tool_context,
        edit_options={}
    )

    assert result.isError or (
        result.structuredContent is not None
        and result.structuredContent["status"] == "failure"
    )


async def test_edit_premises_nonexistent_old_value_fails(tool_context: Mock) -> None:
    """Test that trying to update a non-existent premise fails."""
    # Add an argument
    await add_argument_elaborate(
        label="A1",
        ctx=tool_context,
        gist="Test argument",
        premises=["First premise"],
        conclusion="Conclusion"
    )
    
    # Try to update a premise that doesn't exist
    result = edit(
        label="A1",
        field="premises",
        ctx=tool_context,
        edit_options={"old_value": "Nonexistent premise", "new_value": "New content"}
    )

    assert result.structuredContent is not None
    assert result.structuredContent["status"] == "failure"


async def test_edit_premises_empty_new_value_fails(tool_context: Mock) -> None:
    """Test that adding an empty premise fails."""
    # Add an argument
    await add_argument_elaborate(
        label="A1",
        ctx=tool_context,
        gist="Test argument",
        premises=["First premise"],
        conclusion="Conclusion"
    )
    
    # Try to add an empty premise
    result = edit(
        label="A1",
        field="premises",
        ctx=tool_context,
        edit_options={"new_value": ""}
    )

    assert result.structuredContent is not None
    assert result.structuredContent["status"] == "failure"
