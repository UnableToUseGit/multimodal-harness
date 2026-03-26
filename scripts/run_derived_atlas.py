#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run derived VideoAtlas generation from a canonical workspace.")
    parser.add_argument("--config", default="configs/task_derivation/default.json", help="Path to the derived pipeline config JSON.")
    parser.add_argument("--source-workspace", required=True, help="Path to the source canonical workspace.")
    parser.add_argument("--output-workspace", required=True, help="Path to the output derived workspace.")
    parser.add_argument("--task-description", required=True, help="Task description used to derive a task-aware atlas.")
    parser.add_argument("--verbose", action="store_true", help="Override config and enable verbose logging.")
    return parser


def main() -> int:
    args = build_parser().parse_args()

    from video_atlas.agents import DerivedAtlasAgent
    from video_atlas.agents.task_derivation import load_canonical_workspace
    from video_atlas.config import build_generator, load_derived_pipeline_config
    from video_atlas.workspaces import LocalWorkspace

    config = load_derived_pipeline_config(args.config)
    canonical_atlas = load_canonical_workspace(args.source_workspace)
    workspace = LocalWorkspace(
        root_path=Path(args.output_workspace),
        name="derived_atlas_workspace",
        description="Task-aware derived VideoAtlas workspace",
    )
    planner = build_generator(config.planner)
    segmentor = build_generator(config.segmentor)
    captioner = build_generator(config.captioner)
    agent = DerivedAtlasAgent(
        planner=planner,
        segmentor=segmentor,
        captioner=captioner,
        workspace=workspace,
        num_workers=config.runtime.num_workers,
    )
    result = agent.add(
        task_request=args.task_description,
        canonical_atlas=canonical_atlas,
        verbose=(config.runtime.verbose or args.verbose),
    )

    print(f"success={result.success}")
    print(f"derived_segment_count={result.derived_segment_count}")
    print(f"output_workspace={Path(args.output_workspace).resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
