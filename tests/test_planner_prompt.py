import unittest


class PlannerPromptTest(unittest.TestCase):
    def test_planner_prompt_is_exported_with_minimal_output_contract(self) -> None:
        from video_atlas.prompts import PLANNER_PROMPT

        user_prompt = PLANNER_PROMPT["USER"]

        self.assertIn('"planner_confidence": 0.0', user_prompt)
        self.assertIn('"genre_distribution"', user_prompt)
        self.assertIn('"segmentation_profile"', user_prompt)
        self.assertIn('"sampling_profile"', user_prompt)
        self.assertNotIn('"use_subtitles"', user_prompt)
        self.assertNotIn('"segmentation":', user_prompt)
        self.assertNotIn('"title":', user_prompt)
        self.assertNotIn('"description":', user_prompt)


if __name__ == "__main__":
    unittest.main()
