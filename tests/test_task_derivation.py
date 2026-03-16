import json
import tempfile
import unittest
from pathlib import Path

from video_atlas.agents.task_derivation.loader import load_canonical_atlas
from video_atlas.agents.task_derivation_agent import TaskDerivationAgent
from video_atlas.workspaces import LocalWorkspace


class _FakeGenerator:
    def __init__(self, payload: dict):
        self.payload = payload

    def generate_single(self, prompt=None, messages=None, schema=None, extra_params=None):
        return {
            "text": json.dumps(self.payload),
            "json": self.payload,
            "response": {"usage": {"total_tokens": 42}},
        }


def _write_segment(segment_dir: Path, seg_id: str, title: str, summary: str, detail: str, start: float, end: float) -> None:
    segment_dir.mkdir(parents=True, exist_ok=True)
    segment_dir.joinpath("README.md").write_text(
        "\n".join(
            [
                "# Segment Context",
                "",
                f"**SegID**: {seg_id}",
                f"**Start Time**: {start}",
                f"**End Time**: {end}",
                f"**Duration**: {end - start}",
                f"**Title**: {title}",
                f"**Summary**: {summary}",
                f"**Detail Description**: {detail}",
            ]
        ),
        encoding="utf-8",
    )
    segment_dir.joinpath("SUBTITLES.md").write_text("subtitles", encoding="utf-8")
    segment_dir.joinpath("video_clip.mp4").write_text("fake clip", encoding="utf-8")


class TaskDerivationTest(unittest.TestCase):
    def test_loader_reads_canonical_workspace(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            root.joinpath("README.md").write_text("# Canonical Atlas", encoding="utf-8")
            root.joinpath("video.mp4").write_text("fake video", encoding="utf-8")
            _write_segment(root / "segments" / "seg0001-opening", "seg_0001", "Opening", "Setup", "Opening detail", 0.0, 10.0)

            atlas = load_canonical_atlas(root)

        self.assertEqual(len(atlas.segments), 1)
        self.assertEqual(atlas.segments[0].source_segment_id, "seg_0001")
        self.assertEqual(atlas.segments[0].seg_title, "Opening")

    def test_task_derivation_agent_writes_derived_workspace(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            source_root = root / "source"
            target_root = root / "derived"
            source_root.mkdir()
            source_root.joinpath("README.md").write_text("# Match Overview", encoding="utf-8")
            source_root.joinpath("video.mp4").write_text("fake video", encoding="utf-8")
            _write_segment(source_root / "segments" / "seg0001-opening", "seg_0001", "Opening rally", "Teams feel each other out", "Long midfield exchange", 0.0, 20.0)
            _write_segment(source_root / "segments" / "seg0002-goal", "seg_0002", "Goal sequence", "A decisive goal is scored", "Fast break and finish", 20.0, 35.0)

            generator = _FakeGenerator(
                {
                    "task_title": "Match Highlights",
                    "task_abstract": "A highlight-focused view of the most decisive events.",
                    "selection_strategy": "Keep only decisive moments for a concise recap.",
                    "derived_segments": [
                        {
                            "source_segment_id": "seg_0001",
                            "source_folder": "seg0001-opening",
                            "relevance_score": 0.1,
                            "action": "drop",
                            "derived_title": "Opening rally",
                            "derived_summary": "Low-priority setup.",
                            "order": 0,
                            "rationale": "Setup is not important for a highlights-only task.",
                        },
                        {
                            "source_segment_id": "seg_0002",
                            "source_folder": "seg0002-goal",
                            "relevance_score": 0.95,
                            "action": "keep",
                            "derived_title": "Winning goal",
                            "derived_summary": "The decisive scoring play.",
                            "order": 1,
                            "rationale": "This is the core highlight event.",
                        },
                    ],
                }
            )
            workspace = LocalWorkspace(root_path=target_root, name="task_derivation_workspace", description="Derived task-aware atlas")
            agent = TaskDerivationAgent(generator=generator, workspace=workspace)

            result = agent.add(source_workspace=source_root, task_description="Create a highlights-only match recap.")

            self.assertTrue(result.success)
            self.assertEqual(result.derived_segment_num, 1)
            self.assertTrue((target_root / "README.md").exists())
            self.assertTrue((target_root / "TASK.md").exists())
            self.assertTrue((target_root / "derivation.json").exists())
            self.assertTrue((target_root / "segments" / "task_seg_0001-Winning_goal" / "README.md").exists())
            self.assertTrue((target_root / "segments" / "task_seg_0001-Winning_goal" / "SOURCE_MAP.json").exists())
            source_map = json.loads((target_root / "segments" / "task_seg_0001-Winning_goal" / "SOURCE_MAP.json").read_text(encoding="utf-8"))
            self.assertEqual(source_map["source_segment_ids"], ["seg_0002"])


if __name__ == "__main__":
    unittest.main()
