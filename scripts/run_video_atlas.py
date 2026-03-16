#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run canonical VideoAtlas generation from a local input directory.")
    parser.add_argument("--input-path", required=True, help="Path to a directory containing one .mp4 and optional .srt.")
    parser.add_argument("--output-workspace", required=True, help="Path to the output canonical workspace.")
    parser.add_argument("--planner-model", required=True, help="Planner model name for the OpenAI-compatible API.")
    parser.add_argument("--segmentor-model", help="Segmentor model name for the OpenAI-compatible API. Defaults to planner model.")
    parser.add_argument("--planner-temperature", type=float, default=0.0, help="Planner sampling temperature.")
    parser.add_argument("--segmentor-temperature", type=float, default=0.0, help="Segmentor sampling temperature.")
    parser.add_argument("--planner-max-tokens", type=int, default=1600, help="Planner max tokens.")
    parser.add_argument("--segmentor-max-tokens", type=int, default=1600, help="Segmentor max tokens.")
    parser.add_argument("--caption-with-subtitles", action="store_true", help="Include subtitles in caption generation.")
    parser.add_argument("--verbose", action="store_true", help="Print progress information.")
    return parser


def main() -> int:
    args = build_parser().parse_args()

    from video_atlas.agents import VideoAtlasAgent
    from video_atlas.core import VideoAtlasTree
    from video_atlas.generators import OpenAICompatibleGenerator
    from video_atlas.workspaces import LocalWorkspace

    workspace = LocalWorkspace(
        root_path=Path(args.output_workspace),
        name="canonical_video_atlas_workspace",
        description="Canonical content-aware VideoAtlas workspace",
    )
    tree = VideoAtlasTree.create_empty(Path(workspace.root_path))
    planner = OpenAICompatibleGenerator(
        {
            "model_name": args.planner_model,
            "temperature": args.planner_temperature,
            "top_p": 1.0,
            "max_tokens": args.planner_max_tokens,
        }
    )
    segmentor = OpenAICompatibleGenerator(
        {
            "model_name": args.segmentor_model or args.planner_model,
            "temperature": args.segmentor_temperature,
            "top_p": 1.0,
            "max_tokens": args.segmentor_max_tokens,
        }
    )
    agent = VideoAtlasAgent(planner=planner, segmentor=segmentor, workspace=workspace, tree=tree)
    result = agent.add(
        input_path=args.input_path,
        verbose=args.verbose,
        caption_with_subtitles=args.caption_with_subtitles,
    )

    print(f"success={result.success}")
    print(f"segment_num={result.segment_num}")
    print(f"output_workspace={Path(args.output_workspace).resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
