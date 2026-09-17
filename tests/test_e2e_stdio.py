"""The server as a client actually meets it: a real process, over stdio."""

import json
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

REPO = Path(__file__).resolve().parent.parent

TOOL_NAMES = ["show", "add_claim", "add_argument", "link", "unlink", "edit", "delete"]


def text_of(result: Any) -> str:
    return "".join(block.text for block in result.content if block.type == "text")


def server(save_file: Path | None = None) -> StdioServerParameters:
    args = ["run", "python", "-m", "cedrus"]
    if save_file is not None:
        args += ["--save-file", str(save_file)]
    return StdioServerParameters(command="uv", args=args, cwd=str(REPO))


@asynccontextmanager
async def connected(save_file: Path | None = None) -> AsyncIterator[tuple[ClientSession, Any]]:
    """A running server, an initialized client, and what `initialize` returned."""
    async with (
        stdio_client(server(save_file)) as (read, write),
        ClientSession(read, write) as client,
    ):
        info = await client.initialize()
        yield client, info


async def test_the_server_introduces_itself_with_seven_tools() -> None:
    async with connected() as (client, info):
        assert info.server_info.name == "cedrus"
        assert info.instructions is not None
        assert "add_claim" in info.instructions

        assert [tool.name for tool in (await client.list_tools()).tools] == TOOL_NAMES

        # Every tool takes flat strings, so nothing nested reaches a small model.
        for tool in (await client.list_tools()).tools:
            for schema in tool.input_schema.get("properties", {}).values():
                assert schema.get("type") in {"string", "boolean"}, (tool.name, schema)


async def test_a_whole_session_over_stdio(tmp_path: Path) -> None:
    saved = tmp_path / "map.json"
    async with connected(saved) as (client, _):
        empty = await client.call_tool("show", {})
        assert text_of(empty).startswith("The map is empty.")

        added = await client.call_tool(
            "add_claim",
            {"label": "Legalisation of Soft Drugs", "text": "Soft drugs should be legal."},
        )
        assert added.is_error is not True
        assert text_of(added).startswith('OK: Added C1 "Legalisation of Soft Drugs".')

        await client.call_tool(
            "add_argument",
            {
                "target": "C1",
                "relation": "supports",
                "label": "Tax revenue",
                "text": "Excise duty on a legal market raises money.",
            },
        )
        attack = await client.call_tool(
            "add_argument",
            {
                "target": "c1",  # lower case on purpose
                "relation": "attack",  # singular on purpose
                "label": "Slippery slope",
                "text": "Soft drugs lead on to harder ones.",
            },
        )
        assert '"Slippery slope" [con]' in text_of(attack)

        # The tool list is still the same one, after every kind of call.
        assert [tool.name for tool in (await client.list_tools()).tools] == TOOL_NAMES

        body = text_of(await client.call_tool("show", {}))
        assert "- A1 Tax revenue [pro] — supports C1" in body
        assert "- A2 Slippery slope [con] — attacks C1" in body

        # The two resources agree with the files on disk.
        resources = [str(r.uri) for r in (await client.list_resources()).resources]
        assert "map://current" in resources
        assert "map://current.json" in resources

        as_json = await client.read_resource("map://current.json")  # type: ignore[arg-type]
        from_resource = json.loads(as_json.contents[0].text)  # type: ignore[union-attr]
        assert from_resource == json.loads(saved.read_text())
        assert from_resource["version"] == 3
        assert [c["id"] for c in from_resource["arguments"]] == ["A1", "A2"]

        as_text = await client.read_resource("map://current")  # type: ignore[arg-type]
        assert as_text.contents[0].text == saved.with_suffix(".txt").read_text()  # type: ignore[union-attr]


async def test_a_refusal_is_an_error_result_that_changed_nothing() -> None:
    async with connected() as (client, _):
        await client.call_tool("add_claim", {"label": "Root", "text": "A statement."})

        refused = await client.call_tool(
            "add_argument",
            {
                "target": "C1",
                "relation": "undercuts",
                "label": "Bad undercut",
                "text": "Undercuts need an argument.",
            },
        )
        message = text_of(refused)
        assert refused.is_error is True
        # The SDK's own prefix is the error marker; we add none of our own.
        assert message.startswith("Error executing tool add_argument: ")
        assert "ERROR:" not in message
        assert "but C1 is a claim" in message
        assert message.endswith("Nothing was changed (map v1).")

        unknown = await client.call_tool("delete", {"id": "A9"})
        assert unknown.is_error is True
        # Too small a map for a near miss, so it names what is really there.
        assert '"A9" does not exist. The map has: C1.' in text_of(unknown)

        # Neither refusal reached the map.
        assert "Map v1. 1 claim, 0 arguments, 0 relations." in text_of(
            await client.call_tool("show", {})
        )


async def test_the_saved_file_keeps_up_with_every_change(tmp_path: Path) -> None:
    saved = tmp_path / "map.json"
    async with connected(saved) as (client, _):
        await client.call_tool("add_claim", {"label": "Root", "text": "A statement."})
        assert json.loads(saved.read_text())["version"] == 1

        for index in range(3):
            await client.call_tool(
                "add_argument",
                {
                    "target": "C1",
                    "relation": "supports",
                    "label": f"Reason {index}",
                    "text": "Text.",
                },
            )
            assert json.loads(saved.read_text())["version"] == index + 2

        saved_text = saved.with_suffix(".txt").read_text()
        assert saved_text.startswith("ARGUMENT MAP: Root")
        assert "## Part 3" in saved_text
