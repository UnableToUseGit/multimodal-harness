from __future__ import annotations

import argparse
import platform
import sys

from video_atlas.application import create_canonical_from_local, create_canonical_from_url, acquire_from_url
from video_atlas.config import load_canonical_pipeline_config
from video_atlas.source_acquisition import InvalidSourceUrlError, UnsupportedSourceError


class CliUsageError(ValueError):
    pass


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

    create_parser = subparsers.add_parser(
        "create",
        help="Create a canonical atlas.",
    )
    create_parser.add_argument("--url")
    create_parser.add_argument("--video-file")
    create_parser.add_argument("--audio-file")
    create_parser.add_argument("--subtitle-file")
    create_parser.add_argument("--metadata-file")
    create_parser.add_argument("--output-dir", required=True)
    create_parser.add_argument("--config", default="configs/canonical/default.json")
    create_parser.add_argument("--structure-request", default="")

    fetch_parser = subparsers.add_parser(
        "fetch",
        help="Fetch source assets without generating an atlas.",
    )
    fetch_parser.add_argument("--url", required=True)
    fetch_parser.add_argument("--output-dir", required=True)
    fetch_parser.add_argument("--config", default="configs/canonical/default.json")
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


def _run_canonical_create(args) -> int:
    config = load_canonical_pipeline_config(args.config)
    local_inputs = [args.video_file, args.audio_file, args.subtitle_file, args.metadata_file]
    if args.url:
        if any(item is not None for item in local_inputs):
            raise CliUsageError("create accepts either --url or local file inputs, not both")
        create_canonical_from_url(
            args.url,
            args.output_dir,
            config,
            structure_request=args.structure_request,
        )
        return 0

    if args.video_file is None and args.audio_file is None and args.subtitle_file is None:
        raise CliUsageError("create requires --url or at least one of --video-file/--audio-file/--subtitle-file")

    create_canonical_from_local(
        args.output_dir,
        config,
        video_file=args.video_file,
        audio_file=args.audio_file,
        subtitle_file=args.subtitle_file,
        metadata_file=args.metadata_file,
        structure_request=args.structure_request,
    )
    return 0


def _run_fetch(args) -> int:
    config = load_canonical_pipeline_config(args.config)
    acquire_from_url(
        args.url,
        args.output_dir,
        prefer_youtube_subtitles=config.acquisition.prefer_youtube_subtitles,
        youtube_output_template=config.acquisition.youtube_output_template,
    )
    
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
    try:
        if args.command == "create":
            return _run_canonical_create(args)
        if args.command == "fetch":
            return _run_fetch(args)
    except (CliUsageError, InvalidSourceUrlError, UnsupportedSourceError) as exc:
        print(str(exc), file=sys.stderr)
        return 2

    parser.error(f"unknown command: {args.command}")
    return 2
