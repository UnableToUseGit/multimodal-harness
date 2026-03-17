from __future__ import annotations

import argparse
import platform
import sys


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="video-atlas",
        description="Development CLI for the VideoAtlas package.",
    )
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser(
        "info",
        help="Print package and runtime information.",
    )
    subparsers.add_parser(
        "check-import",
        help="Verify the package can be imported in the current environment.",
    )
    subparsers.add_parser(
        "config",
        help="Print the current VideoAtlas configuration state.",
    )
    return parser


def _print_info() -> int:
    import video_atlas

    print(f"video_atlas {video_atlas.__version__}")
    print(f"python {platform.python_version()}")
    print(f"executable {sys.executable}")
    return 0


def _check_import() -> int:
    import video_atlas

    print(f"import-ok {video_atlas.__version__}")
    return 0


def _print_config() -> int:
    from video_atlas.settings import get_settings

    settings = get_settings()
    print(f"configured {'yes' if settings.is_configured else 'no'}")
    print(f"api_base {settings.api_base or '<missing>'}")
    print(f"api_key {settings.masked_api_key}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    parser.add_argument(
        "--version",
        action="version",
        version="video-atlas 0.1.0",
    )
    args = parser.parse_args(argv)

    if args.command in (None, "info"):
        return _print_info()
    if args.command == "check-import":
        return _check_import()
    if args.command == "config":
        return _print_config()

    parser.error(f"unknown command: {args.command}")
    return 2
