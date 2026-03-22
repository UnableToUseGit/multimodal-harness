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

    def test_boundary_detection_prompt_mentions_last_detection_point(self) -> None:
        from video_atlas.prompts import BOUNDARY_DETECTION_PROMPT

        self.assertIn("last detection point", BOUNDARY_DETECTION_PROMPT["SYSTEM"].lower())
        self.assertIn("Video category:", BOUNDARY_DETECTION_PROMPT["USER"])
        self.assertIn("{last_detection_point}", BOUNDARY_DETECTION_PROMPT["USER"])

    def test_caption_generation_prompt_uses_summary_caption_confidence_contract(self) -> None:
        from video_atlas.prompts import CAPTION_GENERATION_PROMPT

        system_prompt = CAPTION_GENERATION_PROMPT["SYSTEM"]

        self.assertIn("Role:", system_prompt)
        self.assertIn("Goal:", system_prompt)
        self.assertIn("Input:", system_prompt)
        self.assertIn("Guidelines:", system_prompt)
        self.assertIn("Output format:", system_prompt)
        self.assertIn('"summary": "<1 sentence summary>"', system_prompt)
        self.assertIn('"caption": "<4-8 sentence paragraph>"', system_prompt)
        self.assertNotIn('"slots"', system_prompt)
        self.assertNotIn("final_caption", system_prompt)
        self.assertNotIn("slots_weight", system_prompt)
        self.assertNotIn("follow strictly", system_prompt.lower())
        self.assertNotIn("hard rules", system_prompt.lower())

    def test_video_global_prompt_uses_structured_role_goal_style(self) -> None:
        from video_atlas.prompts import VIDEO_GLOBAL_PROMPT

        system_prompt = VIDEO_GLOBAL_PROMPT["SYSTEM"]
        self.assertIn("Role:", system_prompt)
        self.assertIn("Goal:", system_prompt)
        self.assertIn("Input:", system_prompt)
        self.assertIn("Guidelines:", system_prompt)
        self.assertIn("Output format:", system_prompt)
        self.assertIn('"segment_titles"', system_prompt)
        self.assertNotIn("hard rules", system_prompt.lower())

if __name__ == "__main__":
    unittest.main()
