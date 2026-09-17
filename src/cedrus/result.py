"""Every tool result, in the same shape (§2 of the plan, "Rules for results").

A result stands on its own. It never refers back to an earlier result, so a host may
drop older ones from the context without leaving the model with a dangling reference.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from cedrus.model import ArgMap
from cedrus.render import counts


@dataclass
class Session:
    """One MCP session: one map, and what the model has been shown of it."""

    amap: ArgMap = field(default_factory=ArgMap)
    session_id: str = ""
    last_shown: int | None = None
    hints: bool = False

    def mark_shown(self) -> None:
        self.last_shown = self.amap.version


def ok(headline: str, session: Session, notes: str = "", hint: str = "") -> str:
    """`OK:` line, status line, and at most one `Hint:` line."""
    first = f"OK: {headline}"
    if notes:
        first = f"{first} {notes}"
    lines = [first, _status(session)]
    if hint and session.hints:
        lines.append(f"Hint: {hint}")
    return "\n".join(lines)


def error(message: str, session: Session) -> str:
    """The refusal, and the reassurance that the map is untouched.

    No `ERROR:` of our own: the SDK puts every `ToolError` behind
    `Error executing tool <name>: `, which is the marker the model reads, and a second
    one would only be noise.
    """
    return f"{message}\nNothing was changed (map v{session.amap.version})."


def _status(session: Session) -> str:
    amap = session.amap
    line = f"Map v{amap.version}: {counts(amap)}."
    stale = _staleness(session)
    return f"{line} {stale}" if stale else line


def _staleness(session: Session) -> str:
    """How far the map has moved since the model last looked at it."""
    if session.last_shown is None:
        return ""  # nothing has been shown, so nothing can be out of date
    behind = session.amap.version - session.last_shown
    if behind <= 0:
        return ""
    times = "once" if behind == 1 else f"{behind} times"
    return f"The map changed {times} since your last show()."
