import unittest

from video_atlas.workflows.canonical_atlas.execution_plan_builder import ExecutionPlanBuilderMixin


class _Builder(ExecutionPlanBuilderMixin):
    chunk_size_sec = 420
    chunk_overlap_sec = 24


class StrategyBuilderTest(unittest.TestCase):
    def test_construct_execution_plan_resolves_profile_and_runtime_controls(self) -> None:
        builder = _Builder()
        plan = builder._construct_execution_plan(
            {
                "planner_confidence": 0.9,
                "genres": ["sports_broadcast", "other"],
                "concise_description": "A professional sports broadcast with live gameplay and replay analysis.",
                "profile": "sports",
            },
            planner_reasoning_content="planner reasoning",
        )

        self.assertEqual(plan.planner_confidence, 0.9)
        self.assertEqual(plan.genres, ["sports_broadcast", "other"])
        self.assertEqual(
            plan.concise_description,
            "A professional sports broadcast with live gameplay and replay analysis.",
        )
        self.assertEqual(plan.profile_name, "sports")
        self.assertEqual(plan.profile.route, "multimodal")
        self.assertIn("match phases", plan.profile.segmentation_policy.lower())
        self.assertEqual(plan.chunk_size_sec, 420)
        self.assertEqual(plan.chunk_overlap_sec, 24)
        self.assertTrue(plan.profile.caption_policy)
        self.assertEqual(plan.planner_reasoning_content, "planner reasoning")

    def test_construct_execution_plan_falls_back_to_other_profile(self) -> None:
        builder = _Builder()
        plan = builder._construct_execution_plan({"profile": "does_not_exist"}, planner_reasoning_content="")

        self.assertEqual(plan.profile_name, "other")
        self.assertEqual(plan.profile.route, "multimodal")
        self.assertIn("coarse", plan.profile.segmentation_policy.lower())
        self.assertEqual(plan.genres, ["other"])
        self.assertEqual(plan.concise_description, "")

if __name__ == "__main__":
    unittest.main()
