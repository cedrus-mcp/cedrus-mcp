"""Command line and environment (§5 of the plan)."""

from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
from mcp.server.mcpserver.exceptions import ToolError

from cedrus.__main__ import build_parser, settings_from
from cedrus.render import DEFAULT_MAX_CHARS
from cedrus.server import STDIO_SESSION_ID, _session_key


def settings(argv: list[str], env: dict[str, str] | None = None):
    return settings_from(build_parser().parse_args(argv), env or {})


def test_defaults_are_stdio_without_saving() -> None:
    s = settings([])
    assert s.max_chars == DEFAULT_MAX_CHARS
    assert s.hints is False
    assert s.save_file is None
    assert s.save_dir is None


def test_http_binds_to_localhost_by_default() -> None:
    args = build_parser().parse_args([])
    assert (args.host, args.port) == ("127.0.0.1", 8000)
    assert build_parser().parse_args(["--port", "9001"]).port == 9001


def test_flags_are_read() -> None:
    s = settings(["--hints", "--max-chars", "8000", "--save-file", "/tmp/m.json"])
    assert s.hints is True
    assert s.max_chars == 8000
    assert s.save_file == Path("/tmp/m.json")


def test_the_environment_supplies_the_save_paths() -> None:
    s = settings([], {"CEDRUS_SAVE_FILE": "/tmp/m.json", "CEDRUS_SAVE_DIR": "/tmp/maps"})
    assert s.save_file == Path("/tmp/m.json")
    assert s.save_dir == Path("/tmp/maps")


def test_a_flag_beats_the_environment() -> None:
    s = settings(["--save-file", "/tmp/flag.json"], {"CEDRUS_SAVE_FILE": "/tmp/env.json"})
    assert s.save_file == Path("/tmp/flag.json")


def test_an_empty_environment_variable_is_ignored() -> None:
    assert settings([], {"CEDRUS_SAVE_FILE": ""}).save_file is None


def test_a_useless_size_limit_is_refused() -> None:
    with pytest.raises(SystemExit, match="--max-chars"):
        settings(["--max-chars", "0"])


# --------------------------------------------------------------- session keys
#
# What tells one MCP session from another. The real thing is exercised over HTTP in
# test_e2e_http.py; these pin the rule itself, including the case no transport produces.


def request_with(headers: dict[str, str] | None) -> Any:
    """The only part of a Context that `_session_key` looks at."""
    return SimpleNamespace(headers=headers)


def test_stdio_has_no_headers_and_gets_one_key_per_process() -> None:
    assert _session_key(request_with(None)) == STDIO_SESSION_ID
    assert len(STDIO_SESSION_ID) == 32  # a uuid, so two stdio servers cannot collide


def test_http_is_keyed_by_the_mcp_session_id_header() -> None:
    headers = {"mcp-session-id": "abc123", "host": "127.0.0.1"}
    assert _session_key(request_with(headers)) == "abc123"


def test_a_request_without_a_session_is_refused() -> None:
    # Stateless HTTP: no session id, so there is nothing for a map to belong to.
    with pytest.raises(ToolError, match="no MCP session id"):
        _session_key(request_with({"host": "127.0.0.1"}))
