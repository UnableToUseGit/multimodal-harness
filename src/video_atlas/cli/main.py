from __future__ import annotations

import argparse
import platform
import sys
from pathlib import Path
import shutil

from video_atlas.config import build_generator, build_transcriber, load_canonical_pipeline_config
from video_atlas.source_acquisition import (
    InvalidSourceUrlError,
    UnsupportedSourceError,
    acquire_from_url,
    create_acquisition_subdir,
    materialize_fetch_workspace,
)
from video_atlas.workflows.canonical_atlas_workflow import CanonicalAtlasWorkflow


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
    create_parser.add_argument("--url", required=True)
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
    output_dir = Path(args.output_dir)
    config = load_canonical_pipeline_config(args.config)
    acquisition_dir = create_acquisition_subdir(output_dir / ".acquisition")
    acquisition = acquire_from_url(
        args.url,
        acquisition_dir,
        prefer_youtube_subtitles=config.acquisition.prefer_youtube_subtitles,
        youtube_output_template=config.acquisition.youtube_output_template,
    )
    workflow = CanonicalAtlasWorkflow(
        planner=build_generator(config.planner),
        text_segmentor=build_generator(config.text_segmentor) if config.text_segmentor is not None else None,
        multimodal_segmentor=build_generator(config.multimodal_segmentor) if config.multimodal_segmentor is not None else None,
        structure_composer=build_generator(config.structure_composer) if config.structure_composer is not None else None,
        captioner=build_generator(config.captioner) if config.captioner is not None else None,
        transcriber=build_transcriber(config.transcriber),
        generate_subtitles_if_missing=config.runtime.generate_subtitles_if_missing,
        text_chunk_size_sec=config.runtime.text_chunk_size_sec,
        text_chunk_overlap_sec=config.runtime.text_chunk_overlap_sec,
        multimodal_chunk_size_sec=config.runtime.multimodal_chunk_size_sec,
        multimodal_chunk_overlap_sec=config.runtime.multimodal_chunk_overlap_sec,
        caption_with_subtitles=config.runtime.caption_with_subtitles,
    )
    workflow.create(
        output_dir=output_dir,
        source_video_path=acquisition.local_video_path,
        source_srt_file_path=acquisition.local_subtitles_path,
        structure_request=args.structure_request,
        verbose=False,
        source_info=acquisition.source_info,
        source_metadata=acquisition.source_metadata,
    )
    if acquisition_dir.exists():
        shutil.rmtree(acquisition_dir)
    return 0


def _run_fetch(args) -> int:
    output_dir = Path(args.output_dir)
    config = load_canonical_pipeline_config(args.config)
    acquisition_dir = create_acquisition_subdir(output_dir / ".acquisition")
    acquisition = acquire_from_url(
        args.url,
        acquisition_dir,
        prefer_youtube_subtitles=config.acquisition.prefer_youtube_subtitles,
        youtube_output_template=config.acquisition.youtube_output_template,
    )
    materialize_fetch_workspace(acquisition, output_dir)
    if acquisition_dir.exists():
        shutil.rmtree(acquisition_dir)
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
    except (InvalidSourceUrlError, UnsupportedSourceError) as exc:
        print(str(exc), file=sys.stderr)
        return 2

    parser.error(f"unknown command: {args.command}")
    return 2
