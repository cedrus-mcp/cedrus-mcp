"""Integration tests for MCP server lifecycle management."""

import pytest
from pathlib import Path
from _pytest.monkeypatch import MonkeyPatch
from koala.server import app_lifespan, mcp
from koala.graph.argument_map import ArgumentMap
from koala.graph.persistence import save_graph
from koala.models import ClaimNode, Proposition


@pytest.mark.asyncio
async def test_server_lifespan_creates_new_graph(temp_data_file: Path, monkeypatch: MonkeyPatch) -> None:
    """Test that server creates new graph when data file doesn't exist."""
    from koala.config.settings import settings
    monkeypatch.setattr(settings, "data_file", temp_data_file)
    
    async with app_lifespan(mcp) as ctx:
        assert isinstance(ctx.arg_map, ArgumentMap)
        assert ctx.mode == "sketch"
        assert len(ctx.arg_map.argument_graph.nodes) == 0


@pytest.mark.asyncio
async def test_server_lifespan_loads_existing_graph(temp_data_file: Path, sample_arg_map: ArgumentMap, monkeypatch: MonkeyPatch) -> None:
    """Test that server loads existing graph on startup (persistence is stub)."""
    from koala.config.settings import settings
    
    # Save sample graph
    save_graph(sample_arg_map, temp_data_file)
    monkeypatch.setattr(settings, "data_file", temp_data_file)
    
    async with app_lifespan(mcp) as ctx:
        # load_graph is a stub that returns empty graph
        assert len(ctx.arg_map.argument_graph.nodes) == 0


@pytest.mark.asyncio
async def test_server_lifespan_saves_on_shutdown(temp_data_file: Path, monkeypatch: MonkeyPatch) -> None:
    """Test that server saves graph on shutdown (persistence is stub)."""
    from koala.config.settings import settings
    monkeypatch.setattr(settings, "data_file", temp_data_file)
    
    async with app_lifespan(mcp) as ctx:
        # Add a node during lifespan
        prop = Proposition(content="Test claim")
        ctx.arg_map.add_proposition(prop)
        claim = ClaimNode(label="TEST", proposition_id=prop.id)
        ctx.arg_map.add_claim(claim)
    
    # save_graph is a stub, so file won't be created
    assert not temp_data_file.exists()
