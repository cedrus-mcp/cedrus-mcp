"""Entry point.

cedrus                                  # stdio, for an MCP client
cedrus --save-file /tmp/map.json        # stdio, and keep the map on disk
cedrus --http --save-dir /tmp/maps      # streamable HTTP, one file per session
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from cedrus.render import DEFAULT_MAX_CHARS
from cedrus.server import Settings, configure, mcp


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="cedrus", description="CEDRUS argument-mapping MCP server"
    )
    parser.add_argument(
        "--http",
        action="store_true",
        help="serve over streamable HTTP instead of stdio",
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="address to bind when serving over HTTP (default: 127.0.0.1)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        metavar="N",
        help="port to bind when serving over HTTP (default: 8000)",
    )
    parser.add_argument(
        "--hints",
        action="store_true",
        help="add one short Hint line to tool results",
    )
    parser.add_argument(
        "--max-chars",
        type=int,
        default=DEFAULT_MAX_CHARS,
        metavar="N",
        help=f"size limit for show() output (default: {DEFAULT_MAX_CHARS})",
    )
    parser.add_argument(
        "--save-file",
        type=_user_path,
        metavar="PATH",
        help="write the map to PATH (JSON) and to the matching .txt after every change; "
        "for stdio, which serves one session (env: CEDRUS_SAVE_FILE)",
    )
    parser.add_argument(
        "--save-dir",
        type=_user_path,
        metavar="DIR",
        help="write DIR/<session-id>.json and .txt after every change; "
        "for HTTP, which serves several sessions (env: CEDRUS_SAVE_DIR)",
    )
    return parser


def settings_from(args: argparse.Namespace, environ: dict[str, str] | None = None) -> Settings:
    """Command line first, environment second, defaults last."""
    env = environ if environ is not None else dict(os.environ)
    save_file = args.save_file or _path(env.get("CEDRUS_SAVE_FILE"))
    save_dir = args.save_dir or _path(env.get("CEDRUS_SAVE_DIR"))
    if args.max_chars < 1:
        raise SystemExit("--max-chars must be a positive number of characters")
    return Settings(
        max_chars=args.max_chars,
        hints=args.hints,
        save_file=save_file,
        save_dir=save_dir,
    )


def _path(value: str | None) -> Path | None:
    return _user_path(value) if value else None


def _user_path(value: str) -> Path:
    """A path with `~` expanded: MCP clients start the server without a shell to do it."""
    return Path(value).expanduser()


def main() -> None:
    args = build_parser().parse_args()
    configure(settings_from(args))
    try:
        if args.http:
            mcp.run(transport="streamable-http", host=args.host, port=args.port)
        else:
            mcp.run(transport="stdio")
    except KeyboardInterrupt:
        sys.exit(0)


if __name__ == "__main__":
    main()
