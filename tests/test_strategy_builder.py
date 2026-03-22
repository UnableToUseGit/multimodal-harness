import unittest

from video_atlas.agents.canonical_atlas.execution_plan_builder import ExecutionPlanBuilderMixin


class _Builder(ExecutionPlanBuilderMixin):
    chunk_size_sec = 420
    chunk_overlap_sec = 24


class StrategyBuilderTest(unittest.TestCase):
    def test_construct_execution_plan_resolves_profiles_and_runtime_controls(self) -> None:
        builder = _Builder()
        plan = builder._construct_execution_plan(
            {
                "planner_confidence": 0.9,
                "genre_distribution": {"sports_event": 5, "gameplay": 3, "other": 1},
                "segmentation_profile": "esports_match_broadcast",
                "sampling_profile": "visual_detail",
            }
        )

        self.assertEqual(plan.planner_confidence, 0.9)
        self.assertEqual(plan.segmentation_specification.profile_name, "esports_match_broadcast")
        self.assertEqual(plan.caption_specification.profile_name, "esports_match_broadcast")
        self.assertEqual(plan.segmentation_specification.profile.signal_priority, "balanced")
        self.assertIn("on_screen_text_title_change", plan.segmentation_specification.profile.boundary_evidence_primary)
        self.assertEqual(plan.segmentation_specification.frame_sampling_profile.fps, 1.0)
        self.assertEqual(plan.segmentation_specification.frame_sampling_profile.max_resolution, 720)
        self.assertEqual(plan.caption_specification.frame_sampling_profile.fps, 1.0)
        self.assertEqual(plan.caption_specification.frame_sampling_profile.max_resolution, 720)
        self.assertEqual(plan.chunk_size_sec, 420)
        self.assertEqual(plan.chunk_overlap_sec, 24)
        self.assertTrue(plan.caption_specification.profile.caption_policy)
        self.assertEqual(plan.segmentation_specification.profile.target_segment_length_sec, (90, 240))

    def test_construct_execution_plan_falls_back_to_generic_profile(self) -> None:
        builder = _Builder()
        plan = builder._construct_execution_plan({"segmentation_profile": "does_not_exist"})

        self.assertEqual(plan.segmentation_specification.profile_name, "generic_longform_continuous")
        self.assertEqual(plan.caption_specification.profile_name, "generic_longform_continuous")
        self.assertEqual(plan.segmentation_specification.profile.signal_priority, "balanced")
        self.assertIn("self-contained coarse segments", plan.segmentation_specification.profile.segmentation_policy)

if __name__ == "__main__":
    unittest.main()
