import unittest


class CanonicalSchemesTest(unittest.TestCase):
    def test_canonical_execution_plan_is_available_from_schemas(self) -> None:
        from video_atlas.schemas.canonical_video_atlas import (
            CAPTION_PROFILES,
            CanonicalExecutionPlan,
            DEFAULT_CAPTION_PROFILE,
            DEFAULT_SEGMENTATION_PROFILE,
            SEGMENTATION_PROFILES,
        )

        plan = CanonicalExecutionPlan()

        self.assertEqual(plan.genre_distribution, {"other": 1.0})
        self.assertEqual(plan.planner_confidence, 0.25)
        self.assertEqual(
            plan.segmentation_specification.profile,
            SEGMENTATION_PROFILES[DEFAULT_SEGMENTATION_PROFILE],
        )
        self.assertEqual(
            plan.caption_specification.profile,
            CAPTION_PROFILES[DEFAULT_CAPTION_PROFILE],
        )
        self.assertGreater(plan.caption_specification.profile.slots_weight["core_events"], 0.0)
        self.assertEqual(DEFAULT_SEGMENTATION_PROFILE, "generic_longform_continuous")
        self.assertEqual(plan.chunk_size_sec, 600)
        self.assertEqual(plan.chunk_overlap_sec, 20)

    def test_execution_plan_is_available_from_schemas_package(self) -> None:
        from video_atlas.schemas import CanonicalExecutionPlan

        plan = CanonicalExecutionPlan()

        self.assertEqual(plan.genre_distribution, {"other": 1.0})

    def test_runtime_only_window_types_are_not_exposed_from_schemas(self) -> None:
        with self.assertRaises(ImportError):
            from video_atlas.schemas import DetectionWindowSpec  # noqa: F401


if __name__ == "__main__":
    unittest.main()
