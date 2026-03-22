#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run canonical VideoAtlas generation from a local input directory.")
    parser.add_argument("--config", default="configs/canonical/default.json", help="Path to the canonical pipeline config JSON.")
    parser.add_argument("--input-path", required=True, help="Path to a directory containing one .mp4 and optional .srt.")
    parser.add_argument("--output-workspace", required=True, help="Path to the output canonical workspace.")
    parser.add_argument("--verbose", action="store_true", help="Override config and enable verbose logging.")
    parser.add_argument("--disable-auto-subtitles", action="store_true", help="Override config and disable automatic subtitle generation.")
    return parser


def main() -> int:
    args = build_parser().parse_args()

    from video_atlas.agents import CanonicalVideoAtlasAgent
    from video_atlas.config import build_generator, build_transcriber, load_canonical_pipeline_config
    from video_atlas.workspaces import LocalWorkspace

    config = load_canonical_pipeline_config(args.config)
    workspace = LocalWorkspace(
        root_path=Path(args.output_workspace),
        name="canonical_atlas_workspace",
        description="Canonical content-aware VideoAtlas workspace",
    )
    planner = build_generator(config.planner)
    segmentor = build_generator(config.segmentor)
    captioner = build_generator(config.captioner) if config.captioner is not None else None
    transcriber = build_transcriber(config.transcriber)
    agent = CanonicalVideoAtlasAgent(
        planner=planner,
        segmentor=segmentor,
        captioner=captioner,
        transcriber=transcriber,
        generate_subtitles_if_missing=(config.runtime.generate_subtitles_if_missing and not args.disable_auto_subtitles),
        chunk_size_sec=config.runtime.chunk_size_sec,
        chunk_overlap_sec=config.runtime.chunk_overlap_sec,
        workspace=workspace,
        caption_with_subtitles=config.runtime.caption_with_subtitles,
    )
    result = agent.add(
        input_path=args.input_path,
        verbose=(config.runtime.verbose or args.verbose)
    )

    print(f"success={result.success}")
    print(f"segment_num={result.segment_num}")
    print(f"output_workspace={Path(args.output_workspace).resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
