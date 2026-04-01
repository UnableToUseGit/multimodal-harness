#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any

from video_atlas.config import (
    build_generator,
    build_transcriber,
    load_canonical_pipeline_config,
    load_derived_pipeline_config,
)
from video_atlas.workflows import CanonicalAtlasWorkflow, DerivedAtlasWorkflow
from video_atlas.workflows.derived_atlas.loader import load_canonical_workspace


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run canonical and derived atlas evaluation cases from a JSON config.")
    parser.add_argument("--config", required=True, help="Path to the evaluation config JSON.")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose workflow logging.")
    return parser


def _read_json(path: str | Path) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def _resolve_path(path_str: str | None) -> Path | None:
    if path_str is None:
        return None
    return Path(path_str).expanduser().resolve()


def _run_case(case_config: dict[str, Any], verbose: bool = False) -> dict[str, Any]:
    case_name = case_config["case_name"]
    case_video_path = _resolve_path(case_config["case_video_path"])
    case_srt_file_path = _resolve_path(case_config.get("case_str_file_path"))
    case_task_request_path = _resolve_path(case_config["case_task_request_path"])
    structure_request = case_config.get("structure_request")
    canonical_config_path = _resolve_path(case_config["canonical_atlas_workflow_config"])
    derived_config_path = _resolve_path(case_config["derived_atlas_workflow_config"])
    case_output_dir = _resolve_path(case_config["case_output_dir"])

    if case_output_dir is None:
        raise ValueError(f"Case '{case_name}' is missing case_output_dir")
    if case_video_path is None or case_task_request_path is None:
        raise ValueError(f"Case '{case_name}' is missing required input paths")

    canonical_output_dir = case_output_dir / "canonical_atlas"
    derived_output_dir = case_output_dir / "derived_atlas"
    should_generate_canonical_atlas = bool(case_config.get("should_generate_canonical_atlas", True))
    should_generate_derived_atlas = bool(case_config.get("should_generate_derived_atlas", True))

    result = {
        "case_name": case_name,
        "case_video_path": str(case_video_path),
        "case_srt_file_path": str(case_srt_file_path) if case_srt_file_path is not None else None,
        "case_task_request_path": str(case_task_request_path),
        "structure_request": structure_request,
        "should_generate_canonical_atlas": should_generate_canonical_atlas,
        "should_generate_derived_atlas": should_generate_derived_atlas,
        "canonical_output_dir": str(canonical_output_dir.resolve()),
        "derived_output_dir": str(derived_output_dir.resolve()),
        "canonical_success": None,
        "derived_success": None,
        "canonical_duration_sec": None,
        "derived_duration_sec": None,
        "error": None,
    }

    try:
        if should_generate_canonical_atlas:
            canonical_config = load_canonical_pipeline_config(canonical_config_path)
            canonical_workflow = CanonicalAtlasWorkflow(
                planner=build_generator(canonical_config.planner),
                text_segmentor=build_generator(canonical_config.text_segmentor or canonical_config.segmentor),
                multimodal_segmentor=build_generator(
                    canonical_config.multimodal_segmentor or canonical_config.segmentor
                ),
                structure_composer=build_generator(canonical_config.structure_composer or canonical_config.planner),
                captioner=build_generator(canonical_config.captioner) if canonical_config.captioner is not None else None,
                transcriber=build_transcriber(canonical_config.transcriber),
                generate_subtitles_if_missing=canonical_config.runtime.generate_subtitles_if_missing,
                text_chunk_size_sec=canonical_config.runtime.text_chunk_size_sec,
                text_chunk_overlap_sec=canonical_config.runtime.text_chunk_overlap_sec,
                multimodal_chunk_size_sec=canonical_config.runtime.multimodal_chunk_size_sec,
                multimodal_chunk_overlap_sec=canonical_config.runtime.multimodal_chunk_overlap_sec,
                caption_with_subtitles=canonical_config.runtime.caption_with_subtitles,
            )
            started_at = time.perf_counter()
            _, cost_time_info = canonical_workflow.create(
                output_dir=canonical_output_dir,
                source_video_path=case_video_path,
                source_srt_file_path=case_srt_file_path,
                structure_request=structure_request,
                verbose=(canonical_config.runtime.verbose or verbose),
            )
            result["canonical_duration_sec"] = {"total_cost_time": round(time.perf_counter() - started_at, 3), **cost_time_info}
            result["canonical_success"] = True

        if should_generate_derived_atlas:
            if not canonical_output_dir.exists():
                raise FileNotFoundError(
                    f"Canonical atlas directory does not exist for case '{case_name}': {canonical_output_dir}"
                )

            task_request = case_task_request_path.read_text(encoding="utf-8").strip()
            canonical_atlas = load_canonical_workspace(canonical_output_dir)
            derived_config = load_derived_pipeline_config(derived_config_path)
            derived_workflow = DerivedAtlasWorkflow(
                planner=build_generator(derived_config.planner),
                segmentor=build_generator(derived_config.segmentor),
                captioner=build_generator(derived_config.captioner),
                num_workers=derived_config.runtime.num_workers,
            )
            started_at = time.perf_counter()
            derived_workflow.create(
                task_request=task_request,
                canonical_atlas=canonical_atlas,
                output_dir=derived_output_dir,
                verbose=(derived_config.runtime.verbose or verbose),
            )
            result["derived_duration_sec"] = round(time.perf_counter() - started_at, 3)
            result["derived_success"] = True
    except Exception as exc:  # noqa: BLE001
        result["error"] = f"{type(exc).__name__}: {exc}"

    return result


def run_evaluation(config_path: str | Path, verbose: bool = False) -> dict[str, Any]:
    config_path = _resolve_path(config_path)
    raw_config = _read_json(config_path)
    results_save_dir = _resolve_path(raw_config["results_save_dir"])
    if results_save_dir is None:
        raise ValueError("results_save_dir is required")
    results_save_dir.mkdir(parents=True, exist_ok=True)

    cases_summary: list[dict[str, Any]] = []
    for case_config in raw_config.get("evaluation_cases", []):
        case_name = case_config["case_name"]
        case_output_dir = results_save_dir / case_name
        case_output_dir.mkdir(parents=True, exist_ok=True)
        case_config = dict(case_config)
        case_config["case_output_dir"] = str(case_output_dir)
        cases_summary.append(_run_case(case_config, verbose=verbose))

    summary = {
        "config_path": str(config_path),
        "results_save_dir": str(results_save_dir),
        "cases": cases_summary,
    }
    summary_path = results_save_dir / "summary.json"
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    return summary


def main() -> int:
    args = build_parser().parse_args()
    summary = run_evaluation(args.config, verbose=args.verbose)
    print(f"results_save_dir={summary['results_save_dir']}")
    print(f"case_count={len(summary['cases'])}")
    print(f"summary_path={Path(summary['results_save_dir']) / 'summary.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
