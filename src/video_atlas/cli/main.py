from __future__ import annotations

import argparse
import platform
import shutil
import sys
import time

from video_atlas.application import create_canonical_from_local, create_canonical_from_url
from video_atlas.config import load_canonical_pipeline_config
from video_atlas.settings import ENV_API_BASE, ENV_API_KEY, get_settings
from video_atlas.skill_install import install_skill, uninstall_skill
from video_atlas.source_acquisition import InvalidSourceUrlError, UnsupportedSourceError


class CliUsageError(ValueError):
    pass


def _print_progress(message: str) -> None:
    print(message)


def _print_create_summary(atlas, cost_time: float) -> None:
    print("Done")
    print(f"atlas_dir: {atlas.atlas_dir}")
    print(f"title: {atlas.title}")
    print(f"output_language: {atlas.execution_plan.output_language}")
    print(f"segments: {len(atlas.segments)}")
    print(f"cost_time: {cost_time:.2f}s")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="mm-harness",
        description="CLI for the MM Harness package.",
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
        help="Print the current MM Harness configuration state.",
    )
    subparsers.add_parser(
        "doctor",
        help="Check whether the current environment is ready to run MM Harness.",
    )
    subparsers.add_parser(
        "install",
        help="Install MM Harness assets for agent use.",
    )
    skill_parser = subparsers.add_parser(
        "skill",
        help="Manage MM Harness skill registration.",
    )
    skill_group = skill_parser.add_mutually_exclusive_group(required=True)
    skill_group.add_argument("--install", action="store_true", help="Install SKILL.md into the detected skill directory.")
    skill_group.add_argument("--uninstall", action="store_true", help="Remove SKILL.md from detected skill directories.")

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
    create_parser.add_argument("--structure-request", default="")
    return parser


def _print_info() -> int:
    import video_atlas

    print("MM Harness")
    print(f"version      {video_atlas.__version__}")
    print(f"python       {platform.python_version()}")
    print(f"executable   {sys.executable}")
    return 0


def _check_import() -> int:
    import video_atlas

    print(f"import-ok {video_atlas.__version__}")
    return 0


def _print_config() -> int:
    settings = get_settings()
    print(f"configured {'yes' if settings.is_configured else 'no'}")
    print(f"api_base {settings.api_base or '<missing>'}")
    print(f"api_key {settings.masked_api_key}")
    return 0


def _doctor_check(label: str, ok: bool, detail: str) -> bool:
    level = "OK" if ok else "FAIL"
    print(f"{level:<5} {label:<22} {detail}")
    return ok


def _doctor_warn(label: str, detail: str) -> None:
    print(f"{'WARN':<5} {label:<22} {detail}")


def _run_doctor() -> int:
    import os
    import video_atlas

    all_required_ok = True
    settings = get_settings()

    ffmpeg_path = shutil.which("ffmpeg")
    ytdlp_path = shutil.which("yt-dlp")
    deno_path = shutil.which("deno")

    print("MM Harness Doctor")
    print("")
    print("Required")
    all_required_ok &= _doctor_check("import", True, f"video_atlas {video_atlas.__version__}")
    all_required_ok &= _doctor_check(
        "ffmpeg",
        ffmpeg_path is not None,
        "found" if ffmpeg_path else "missing; install ffmpeg before running create",
    )
    all_required_ok &= _doctor_check(
        "yt-dlp",
        ytdlp_path is not None,
        "found" if ytdlp_path else "missing; install yt-dlp for YouTube URL support",
    )
    all_required_ok &= _doctor_check(
        "deno",
        deno_path is not None,
        "found" if deno_path else "missing; install deno for reliable YouTube extraction",
    )
    all_required_ok &= _doctor_check(
        ENV_API_BASE,
        bool(settings.api_base),
        "configured" if settings.api_base else "missing; export LLM_API_BASE_URL",
    )
    all_required_ok &= _doctor_check(
        ENV_API_KEY,
        bool(settings.api_key),
        "configured" if settings.api_key else "missing; export LLM_API_KEY",
    )
    groq_key = os.environ.get("GROQ_API_KEY", "").strip()
    all_required_ok &= _doctor_check(
        "GROQ_API_KEY",
        bool(groq_key),
        "configured" if groq_key else "missing; export GROQ_API_KEY for transcription",
    )

    print("")
    print("Optional")
    youtube_cookie_file = os.environ.get("YOUTUBE_COOKIES_FILE", "").strip()
    youtube_cookies_from_browser = os.environ.get("YOUTUBE_COOKIES_FROM_BROWSER", "").strip()
    if youtube_cookie_file or youtube_cookies_from_browser:
        _doctor_warn("youtube-cookies", "configured")
    else:
        _doctor_warn(
            "youtube-cookies",
            "not configured; set YOUTUBE_COOKIES_FILE or YOUTUBE_COOKIES_FROM_BROWSER when YouTube requires authenticated access",
        )

    if not all_required_ok:
        print("")
        print("Hints")
        if not ffmpeg_path:
            print("- install ffmpeg and ensure it is on PATH")
        if not ytdlp_path:
            print("- install yt-dlp and ensure it is on PATH")
        if not deno_path:
            print("- install deno for more reliable YouTube extraction")
        if not settings.api_base:
            print("- export LLM_API_BASE_URL=...")
        if not settings.api_key:
            print("- export LLM_API_KEY=...")
        if not groq_key:
            print("- export GROQ_API_KEY=...")

    return 0 if all_required_ok else 2


def _run_install() -> int:
    print("Installing MM Harness assets...")
    result = install_skill()
    print("Done")
    print(f"skill_dir: {result.target_dir}")
    return 0


def _run_skill(args) -> int:
    if args.install:
        result = install_skill()
        print("Done")
        print(f"skill_dir: {result.target_dir}")
        return 0
    result = uninstall_skill()
    print("Done")
    print(f"removed: {len(result.removed_paths)}")
    return 0


def _run_canonical_create(args) -> int:
    config = load_canonical_pipeline_config("configs/canonical/default.json")
    local_inputs = [args.video_file, args.audio_file, args.subtitle_file, args.metadata_file]
    print("Creating canonical atlas...")
    started_at = time.time()
    if args.url:
        if any(item is not None for item in local_inputs):
            raise CliUsageError("create accepts either --url or local file inputs, not both")
        atlas, _ = create_canonical_from_url(
            args.url,
            args.output_dir,
            config,
            structure_request=args.structure_request,
            on_progress=_print_progress,
        )
        _print_create_summary(atlas, time.time() - started_at)
        return 0

    if args.video_file is None and args.audio_file is None and args.subtitle_file is None:
        raise CliUsageError("create requires --url or at least one of --video-file/--audio-file/--subtitle-file")

    atlas, _ = create_canonical_from_local(
        args.output_dir,
        config,
        video_file=args.video_file,
        audio_file=args.audio_file,
        subtitle_file=args.subtitle_file,
        metadata_file=args.metadata_file,
        structure_request=args.structure_request,
        on_progress=_print_progress,
    )
    _print_create_summary(atlas, time.time() - started_at)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    parser.add_argument(
        "--version",
        action="version",
        version="mm-harness 0.1.0",
    )
    args = parser.parse_args(argv)

    if args.command in (None, "info"):
        return _print_info()
    if args.command == "check-import":
        return _check_import()
    if args.command == "config":
        return _print_config()
    if args.command == "doctor":
        return _run_doctor()
    if args.command == "install":
        return _run_install()
    if args.command == "skill":
        return _run_skill(args)
    try:
        if args.command == "create":
            return _run_canonical_create(args)
    except (CliUsageError, InvalidSourceUrlError, UnsupportedSourceError) as exc:
        print(str(exc), file=sys.stderr)
        return 2

    parser.error(f"unknown command: {args.command}")
    return 2
