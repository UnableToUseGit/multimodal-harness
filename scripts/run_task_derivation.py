#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from video_atlas.agents import TaskDerivationAgent
from video_atlas.workspaces import LocalWorkspace


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run task-aware atlas derivation from a canonical workspace.")
    parser.add_argument("--source-workspace", required=True, help="Path to an existing canonical VideoAtlas workspace.")
    parser.add_argument("--output-workspace", required=True, help="Path to the output task-aware workspace.")
    parser.add_argument("--task-description", required=True, help="Task description used to derive a task-aware atlas.")
    parser.add_argument("--model", required=True, help="Model name for the OpenAI-compatible API.")
    parser.add_argument("--temperature", type=float, default=0.0, help="Sampling temperature.")
    parser.add_argument("--top-p", type=float, default=1.0, help="Top-p sampling.")
    parser.add_argument("--max-tokens", type=int, default=6400, help="Maximum completion tokens.")
    parser.add_argument("--verbose", action="store_true", help="Print progress information.")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    from video_atlas.generators import OpenAICompatibleGenerator

    workspace = LocalWorkspace(
        root_path=Path(args.output_workspace),
        name="task_derivation_workspace",
        description="Task-aware workspace derived from a canonical VideoAtlas workspace",
    )
    generator = OpenAICompatibleGenerator(
        {
            "model_name": args.model,
            "temperature": args.temperature,
            "top_p": args.top_p,
            "max_tokens": args.max_tokens,
        }
    )
    agent = TaskDerivationAgent(generator=generator, workspace=workspace)
    result = agent.add(
        source_workspace=args.source_workspace,
        task_description=args.task_description,
        verbose=args.verbose,
    )

    print(f"success={result.success}")
    print(f"task_title={result.task_title}")
    print(f"derived_segment_num={result.derived_segment_num}")
    print(f"output_workspace={Path(args.output_workspace).resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
