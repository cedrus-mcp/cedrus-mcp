"""The MCP server: eight tools, two resources, and one map per session.

Built on `mcp.server.MCPServer` (SDK v2). The tool descriptions in this file are the
only instructions most models will ever read, so they are written for a small one:
short, concrete, and about the map rather than about the server.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from mcp.server import MCPServer
from mcp.server.mcpserver.context import Context
from mcp.server.mcpserver.exceptions import ResourceError, ToolError

from cedrus import tools
from cedrus.export import archive_path_for, save, to_json
from cedrus.model import MapError
from cedrus.render import DEFAULT_MAX_CHARS, render
from cedrus.result import Session, error

INSTRUCTIONS = """\
Build an argument map step by step.

1. Add the central claim with add_claim.
2. Respond to it with add_argument, choosing supports, attacks or undercuts.
3. Respond to claims and arguments already in the map the same way.
4. Call show() to see the whole map.

The server gives every claim and argument a permanent ID (C1, C2, … and A1, A2, …), so \
you can always refer back to one. Fix mistakes with edit, link, unlink or delete. \
To map another issue, call new_map(): it starts an empty map, and IDs begin again at C1.\
"""


@dataclass
class Settings:
    """What the operator chose on the command line. One set for the whole server."""

    max_chars: int = DEFAULT_MAX_CHARS
    hints: bool = False
    save_file: Path | None = None
    save_dir: Path | None = None


@dataclass
class App:
    """What the lifespan yields: the settings, and one map per MCP session.

    In SDK v2 the lifespan is entered **once for the whole server** and is shared by
    every session, so it cannot hold the map itself. It holds the registry instead, and
    a handler creates its own session's map on first use — which is what the v2 notes
    mean by "anything that acquired a per-connection resource there belongs in the
    handler body now".
    """

    settings: Settings = field(default_factory=Settings)
    sessions: dict[str, Session] = field(default_factory=dict)


#: One id for this process, used when there is no MCP session id to key on (stdio).
#: A uuid rather than a fixed word, so two stdio servers sharing a --save-dir cannot
#: overwrite each other's file.
STDIO_SESSION_ID = uuid.uuid4().hex

_app = App()


@asynccontextmanager
async def lifespan(server: MCPServer) -> AsyncIterator[App]:
    """Server-wide state. Entered once, shared by every session."""
    yield _app


mcp: MCPServer = MCPServer(
    "cedrus",
    instructions=INSTRUCTIONS,
    version="2.0.0dev",
    lifespan=lifespan,
)


def configure(settings: Settings) -> None:
    """Apply the command-line settings before the server starts."""
    _app.settings = settings


# ------------------------------------------------------------------- sessions


def _session(ctx: Context) -> Session:
    """The map for this MCP session, created on first use."""
    app = _app_of(ctx)
    key = _session_key(ctx)
    session = app.sessions.get(key)
    if session is None:
        session = Session(session_id=key, hints=app.settings.hints)
        app.sessions[key] = session
    return session


def _app_of(ctx: Context) -> App:
    """The lifespan value, falling back to the module's own for direct calls in tests."""
    app = ctx.request_context.lifespan_context
    return app if isinstance(app, App) else _app


def _session_key(ctx: Context) -> str:
    """What tells one MCP session from another.

    Streamable HTTP carries the session id in the `mcp-session-id` header, which the
    transport has already matched against a live session before a handler sees it.
    stdio carries no headers and serves exactly one session per process.
    """
    headers = ctx.headers
    if headers is None:
        return STDIO_SESSION_ID
    session_id = headers.get("mcp-session-id")
    if session_id:
        return session_id
    raise ToolError(
        "this request carries no MCP session id, so there is no session to hold a map. "
        "Run the server with a session (the default) rather than in stateless HTTP mode."
    )


def _save_path(session: Session) -> Path | None:
    if _app.settings.save_file is not None:
        return _app.settings.save_file
    if _app.settings.save_dir is not None:
        return _app.settings.save_dir / f"{session.session_id}.json"
    return None


def _changed(session: Session) -> None:
    """Called after every successful change: keep the files beside the agent current."""
    path = _save_path(session)
    if path is not None:
        save(session.amap, path, session.session_id)


def _archive(session: Session) -> None:
    """Keep a map that is about to be replaced, next to its live file, if maps are saved."""
    path = _save_path(session)
    if path is not None and session.amap.items:
        save(session.amap, archive_path_for(path), session.session_id)


def _run(session: Session, call: Any) -> str:
    """Turn a refused change into a tool error, leaving the map untouched."""
    try:
        result = call()
    except MapError as exc:
        raise ToolError(error(str(exc), session)) from None
    _changed(session)
    return str(result)


# ---------------------------------------------------------------------- tools


@mcp.tool()
def show(ctx: Context) -> str:
    """Show the whole argument map: its claims, its arguments and all relations.

    Call this whenever you need to see the current map. Its output replaces any
    earlier show output, so you only ever need the latest one.
    """
    session = _session(ctx)
    return tools.show(session, _app.settings.max_chars)


@mcp.tool()
def add_claim(label: str, text: str, ctx: Context) -> str:
    """Add a claim: the statement being debated, or a general principle arguments rely on.

    Add a claim first; arguments need something to respond to. A claim that responds to
    nothing is a root claim. To make a claim support or attack something, use link
    afterwards.

    Args:
        label: A short title of a few words, e.g. "Legalisation of soft drugs".
        text: The claim written out as one statement.

    Returns:
        The new ID (C1, C2, …) and the state of the map.
    """
    session = _session(ctx)
    return _run(session, lambda: tools.add_claim(session, label, text))


@mcp.tool()
def add_argument(target: str, relation: str, label: str, text: str, ctx: Context) -> str:
    """Add a new argument that responds to a claim or argument already in the map.

    Args:
        target: The ID the argument responds to, e.g. "C1" or "A7".
        relation: How it responds to the target. One of:
            "supports" - the argument gives a reason for the target;
            "attacks" - the argument gives a reason against the target;
            "undercuts" - the argument says the target's reasons do not lead to its
            conclusion, without denying that those reasons are true. The target of an
            undercut must be an argument, not a claim.
        label: A short title of a few words, e.g. "Tax revenue".
        text: The argument written out in full.

    Returns:
        The new ID (A1, A2, …) and the state of the map.
    """
    session = _session(ctx)
    return _run(session, lambda: tools.add_argument(session, target, relation, label, text))


@mcp.tool()
def link(source: str, relation: str, target: str, ctx: Context) -> str:
    """Relate two claims or arguments that are already in the map.

    Use this when one argument responds to more than one thing, or when a claim
    supports or attacks something. If the two are already related, this changes the
    relation to the new type.

    Args:
        source: The ID that does the supporting, attacking or undercutting.
        relation: "supports", "attacks" or "undercuts".
        target: The ID being responded to.
    """
    session = _session(ctx)
    return _run(session, lambda: tools.link(session, source, relation, target))


@mcp.tool()
def unlink(source: str, target: str, ctx: Context) -> str:
    """Remove the relation that goes from source to target.

    An argument must keep at least one target, so its last relation cannot be removed.
    A claim may lose all of its relations. To move an argument, link it to its new
    target first and unlink the old one afterwards.

    Args:
        source: The ID the relation starts at.
        target: The ID the relation points to.
    """
    session = _session(ctx)
    return _run(session, lambda: tools.unlink(session, source, target))


@mcp.tool()
def edit(id: str, ctx: Context, label: str = "", text: str = "") -> str:
    """Change the label and/or the text of a claim or an argument.

    The ID and every relation stay as they are.

    Args:
        id: The ID to change, e.g. "A7".
        label: A new short title. Leave empty to keep the current one.
        text: A new full text. Leave empty to keep the current one.
    """
    session = _session(ctx)
    return _run(session, lambda: tools.edit(session, id, label, text))


@mcp.tool()
def delete(id: str, ctx: Context, with_replies: bool = False) -> str:
    """Delete a claim or an argument, together with its relations.

    The ID is never given to a new item. If some arguments respond only to this one,
    the deletion is refused and they are named, because they would be left with nothing
    to respond to.

    Args:
        id: The ID to delete, e.g. "A7".
        with_replies: Set to true to delete those arguments as well.
    """
    session = _session(ctx)
    return _run(session, lambda: tools.delete(session, id, with_replies))


@mcp.tool()
def new_map(ctx: Context) -> str:
    """Start a new, empty argument map, e.g. to map a different issue.

    Only call this when you are done with the current map: it is cleared. IDs start
    again at C1 and A1, so IDs from the old map no longer apply.
    """
    session = _session(ctx)
    _archive(session)
    return _run(session, lambda: tools.new_map(session))


# ------------------------------------------------------------------ resources


@mcp.resource(
    "map://current",
    name="Current argument map",
    description="The full rendering of this session's map, with no size limit.",
    mime_type="text/plain",
)
def current_map_text() -> str:
    return render(_only_session().amap, max_chars=None)


@mcp.resource(
    "map://current.json",
    name="Current argument map (JSON)",
    description="This session's map as JSON, for the environment running the agent.",
    mime_type="application/json",
)
def current_map_json() -> str:
    session = _only_session()
    return to_json(session.amap, session.session_id)


def _only_session() -> Session:
    """The session these resources describe.

    The SDK does not inject a Context into a static resource, so this is unambiguous
    only while the server holds one session, which is the stdio case the resources are
    meant for. With several sessions, read the files written by --save-dir instead.
    """
    if not _app.sessions:
        return Session()
    if len(_app.sessions) > 1:
        raise ResourceError(
            "this server is holding several sessions, so map://current is ambiguous; "
            "use --save-dir and read the file for the session you want"
        )
    return next(iter(_app.sessions.values()))
