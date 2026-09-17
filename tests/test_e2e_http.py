"""Two HTTP sessions must not share a map.

This is the part of §9 with the most to lose: the map lives on the connection, reached
through an attribute the SDK does not advertise. If that ever stops being per-session,
two agents would quietly edit one map, and only this test would notice.
"""

import json
import socket
import subprocess
import time
from collections.abc import AsyncIterator, Iterator
from contextlib import asynccontextmanager, closing
from pathlib import Path
from typing import Any

import pytest
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

REPO = Path(__file__).resolve().parent.parent
STARTUP_TIMEOUT = 30.0


def free_port() -> int:
    with closing(socket.socket()) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


@pytest.fixture
def http_server(tmp_path: Path) -> Iterator[tuple[str, Path]]:
    """A real `cedrus --http` process, writing one file per session."""
    maps = tmp_path / "maps"
    port = free_port()
    process = subprocess.Popen(
        [
            "uv",
            "run",
            "cedrus",
            "--http",
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
            "--save-dir",
            str(maps),
        ],
        cwd=REPO,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        deadline = time.monotonic() + STARTUP_TIMEOUT
        while time.monotonic() < deadline:
            if process.poll() is not None:
                pytest.fail(f"cedrus --http exited with {process.returncode}")
            with closing(socket.socket()) as probe:
                if probe.connect_ex(("127.0.0.1", port)) == 0:
                    break
            time.sleep(0.1)
        else:
            pytest.fail("cedrus --http did not start in time")
        yield f"http://127.0.0.1:{port}/mcp", maps
    finally:
        process.terminate()
        process.wait(timeout=10)


@asynccontextmanager
async def connected(url: str) -> AsyncIterator[ClientSession]:
    async with (
        streamable_http_client(url) as (read, write),
        ClientSession(read, write) as client,
    ):
        await client.initialize()
        yield client


def text_of(result: Any) -> str:
    return "".join(block.text for block in result.content if block.type == "text")


async def test_each_http_session_gets_its_own_map(
    http_server: tuple[str, Path],
) -> None:
    url, maps = http_server

    for label in ("Debate one", "Debate two"):
        async with connected(url) as client:
            added = await client.call_tool(
                "add_claim", {"label": label, "text": f"The statement of {label}."}
            )
            # A shared map would have made the second one C2.
            assert text_of(added).startswith(f'OK: Added C1 "{label}".')

            view = text_of(await client.call_tool("show", {}))
            assert f"ARGUMENT MAP: {label}" in view
            assert "1 claim, 0 arguments, 0 relations." in view

    saved = sorted(maps.glob("*.json"))
    assert len(saved) == 2, "each session should have written its own file"

    labels = set()
    for path in saved:
        data = json.loads(path.read_text())
        # The file is named after the session, and says so inside as well.
        assert data["session_id"] == path.stem
        assert len(data["claims"]) == 1
        labels.add(data["claims"][0]["label"])
        assert path.with_suffix(".txt").exists()

    assert labels == {"Debate one", "Debate two"}
