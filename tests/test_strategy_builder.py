import unittest

from video_atlas.agents.video_atlas.strategy_builder import StrategyBuilderMixin


class _Builder(StrategyBuilderMixin):
    pass


class StrategyBuilderTest(unittest.TestCase):
    def test_build_spec_resolves_profile_and_runtime_controls(self) -> None:
        builder = _Builder()
        spec = builder._build_spec_from_strategy_pkg(
            {
                "genre_distribution": {"sports_event": 5, "gameplay": 3, "other": 1},
                "segmentation_profile": "esports_match_broadcast",
                "segmentation": {
                    "sampling_profile": "visual_detail",
                    "use_subtitles": "true",
                    "policy_notes": "Prefer stable gameplay phases over kill-by-kill cuts.",
                },
                "description": {
                    "sampling_profile": "language_lean",
                },
                "title": {"notes": "Use stable phase names."},
            }
        )

        self.assertEqual(spec.segment_spec.segmentation_profile, "esports_match_broadcast")
        self.assertEqual(spec.segment_spec.signal_priority, "balanced")
        self.assertIn("on_screen_text_title_change", spec.segment_spec.boundary_evidence_primary)
        self.assertIn("Prefer stable gameplay phases", spec.segment_spec.segmentation_policy)
        self.assertEqual(spec.segmentation_sampling.fps, 1.0)
        self.assertEqual(spec.segmentation_sampling.max_resolution, 720)
        self.assertEqual(spec.description_sampling.fps, 0.25)
        self.assertEqual(spec.boundary_postprocess_spec.target_segment_length_sec, [90, 240])
        self.assertEqual(spec.title_spec.notes, "Use stable phase names.")
        self.assertEqual(spec.title_spec.segmentation_profile, "esports_match_broadcast")

    def test_build_spec_falls_back_to_generic_profile(self) -> None:
        builder = _Builder()
        spec = builder._build_spec_from_strategy_pkg({"segmentation_profile": "does_not_exist"})

        self.assertEqual(spec.segment_spec.segmentation_profile, "generic_longform_continuous")
        self.assertEqual(spec.segment_spec.signal_priority, "balanced")
        self.assertIn("self-contained coarse segments", spec.segment_spec.segmentation_policy)

    def test_revise_segmentation_info_normalizes_boundary_candidates(self) -> None:
        builder = _Builder()
        revised = builder.revise_segmentation_info(
            [
                {
                    "timestamp": 12,
                    "title_hint": "Opening topic",
                    "boundary_rationale": "topic shift",
                    "evidence": ["topic_shift_in_subtitles", "not_allowed"],
                    "confidence": 0.7,
                },
                {"timestamp": 12, "title_hint": "duplicate"},
                {"timestamp": 5},
            ],
            chunk_start_time=10,
            chunk_end_time=20,
        )

        self.assertEqual(len(revised), 1)
        self.assertEqual(revised[0].timestamp, 12)
        self.assertEqual(revised[0].title_hint, "Opening topic")
        self.assertEqual(revised[0].evidence, ["topic_shift_in_subtitles"])


if __name__ == "__main__":
    unittest.main()
