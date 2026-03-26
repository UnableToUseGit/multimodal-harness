from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


class _FakeCanonicalWorkflow:
    calls: list[dict] = []

    def __init__(self, **kwargs):
        self.kwargs = kwargs

    def create(self, output_dir: Path, source_video_path: Path, source_srt_file_path: Path | None = None, verbose: bool = False):
        self.__class__.calls.append(
            {
                "output_dir": output_dir,
                "source_video_path": source_video_path,
                "source_srt_file_path": source_srt_file_path,
                "verbose": verbose,
            }
        )
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / "README.md").write_text("canonical", encoding="utf-8")
        return type(
            "FakeCanonicalAtlas",
            (),
            {
                "atlas_dir": output_dir,
                "relative_video_path": Path(source_video_path.name),
            },
        )()


class _FakeDerivedWorkflow:
    calls: list[dict] = []

    def __init__(self, **kwargs):
        self.kwargs = kwargs

    def create(self, task_request: str, canonical_atlas, output_dir: Path, verbose: bool = False):
        self.__class__.calls.append(
            {
                "task_request": task_request,
                "canonical_atlas": canonical_atlas,
                "output_dir": output_dir,
                "verbose": verbose,
            }
        )
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / "README.md").write_text("derived", encoding="utf-8")
        return type("FakeDerivedAtlas", (), {"atlas_dir": output_dir})()


class EvaluationScriptTest(unittest.TestCase):
    def test_run_evaluation_writes_case_outputs_and_summary(self) -> None:
        from scripts.run_evaluation import run_evaluation

        _FakeCanonicalWorkflow.calls = []
        _FakeDerivedWorkflow.calls = []

        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            inputs_dir = root / "inputs" / "case_001"
            inputs_dir.mkdir(parents=True, exist_ok=True)
            video_path = inputs_dir / "video.mp4"
            srt_path = inputs_dir / "subtitles.srt"
            task_path = inputs_dir / "task_request.txt"
            video_path.write_text("video", encoding="utf-8")
            srt_path.write_text("srt", encoding="utf-8")
            task_path.write_text("find opening", encoding="utf-8")

            results_dir = root / "outputs"
            config_path = root / "evaluation.json"
            config_path.write_text(
                json.dumps(
                    {
                        "results_save_dir": str(results_dir),
                        "evaluation_cases": [
                            {
                                "case_name": "case_001",
                                "case_video_path": str(video_path),
                                "case_str_file_path": str(srt_path),
                                "case_task_request_path": str(task_path),
                                "canonical_atlas_workflow_config": "configs/canonical/default.json",
                                "derived_atlas_workflow_config": "configs/derivation/default.json",
                            }
                        ],
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            fake_times = iter([100.0, 112.5, 200.0, 206.0])
            with patch("scripts.run_evaluation.load_canonical_pipeline_config", return_value=type("Cfg", (), {"planner": object(), "segmentor": object(), "captioner": object(), "transcriber": object(), "runtime": type("Runtime", (), {"generate_subtitles_if_missing": True, "chunk_size_sec": 600, "chunk_overlap_sec": 20, "caption_with_subtitles": True, "verbose": False})()})()), \
                patch("scripts.run_evaluation.load_derived_pipeline_config", return_value=type("Cfg", (), {"planner": object(), "segmentor": object(), "captioner": object(), "runtime": type("Runtime", (), {"num_workers": 2, "verbose": False})()})()), \
                patch("scripts.run_evaluation.build_generator", side_effect=lambda config: config), \
                patch("scripts.run_evaluation.build_transcriber", side_effect=lambda config: config), \
                patch("scripts.run_evaluation.load_canonical_workspace", side_effect=lambda path: type("LoadedCanonicalAtlas", (), {"atlas_dir": Path(path), "relative_video_path": Path(video_path.name)})()), \
                patch("scripts.run_evaluation.CanonicalAtlasWorkflow", _FakeCanonicalWorkflow), \
                patch("scripts.run_evaluation.DerivedAtlasWorkflow", _FakeDerivedWorkflow), \
                patch("scripts.run_evaluation.time.perf_counter", side_effect=lambda: next(fake_times)):
                summary = run_evaluation(config_path)

            case_dir = results_dir / "case_001"
            canonical_dir = case_dir / "canonical_atlas"
            derived_dir = case_dir / "derived_atlas"
            summary_path = results_dir / "summary.json"

            self.assertEqual(len(summary["cases"]), 1)
            case_summary = summary["cases"][0]
            self.assertEqual(case_summary["case_name"], "case_001")
            self.assertTrue(case_summary["canonical_success"])
            self.assertTrue(case_summary["derived_success"])
            self.assertAlmostEqual(case_summary["canonical_duration_sec"], 12.5)
            self.assertAlmostEqual(case_summary["derived_duration_sec"], 6.0)
            self.assertEqual(Path(case_summary["canonical_output_dir"]), canonical_dir.resolve())
            self.assertEqual(Path(case_summary["derived_output_dir"]), derived_dir.resolve())
            self.assertIsNone(case_summary["error"])
            self.assertTrue((canonical_dir / "README.md").exists())
            self.assertTrue((derived_dir / "README.md").exists())
            self.assertTrue(summary_path.exists())

            persisted_summary = json.loads(summary_path.read_text(encoding="utf-8"))
            self.assertEqual(persisted_summary["cases"][0]["case_name"], "case_001")
            self.assertEqual(_FakeCanonicalWorkflow.calls[0]["source_srt_file_path"], srt_path)
            self.assertEqual(_FakeDerivedWorkflow.calls[0]["task_request"], "find opening")


if __name__ == "__main__":
    unittest.main()
