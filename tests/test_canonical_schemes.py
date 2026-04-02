import unittest


class CanonicalSchemesTest(unittest.TestCase):
    def test_atlas_domain_models_are_available_from_schemas(self) -> None:
        from video_atlas.schemas import (
            AtlasSegment,
            AtlasUnit,
            CanonicalAtlas,
            CanonicalCompositionResult,
            CanonicalExecutionPlan,
        )

        unit = AtlasUnit(
            unit_id="unit_0001",
            title="Opening Unit",
            start_time=0.0,
            end_time=5.0,
            summary="Setup",
            caption="Opening caption",
            subtitles_text="hello",
            folder_name="unit0001-opening-unit",
        )

        segment = AtlasSegment(
            segment_id="seg_0001",
            unit_ids=["unit_0001"],
            title="Opening",
            start_time=0.0,
            end_time=10.0,
            summary="Setup",
            composition_rationale="Merged as one introductory block.",
            folder_name="seg0001-opening",
        )
        composition = CanonicalCompositionResult(
            title="Atlas",
            abstract="Overview",
            segments=[segment],
            composition_rationale="Two-stage composition result",
        )
        atlas = CanonicalAtlas(
            title="Atlas",
            duration=10.0,
            abstract="Overview",
            segments=[segment],
            execution_plan=CanonicalExecutionPlan(),
            atlas_dir="/tmp/example",
            relative_video_path="video.mp4",
            units=[unit],
        )

        self.assertEqual(unit.unit_id, "unit_0001")
        self.assertEqual(atlas.segments[0].segment_id, "seg_0001")
        self.assertEqual(atlas.segments[0].title, "Opening")
        self.assertEqual(atlas.units[0].unit_id, "unit_0001")
        self.assertEqual(composition.segments[0].unit_ids, ["unit_0001"])

    def test_canonical_execution_plan_is_available_from_schemas(self) -> None:
        from video_atlas.schemas.canonical_registry import (
            DEFAULT_PROFILE,
            PROFILES,
        )
        from video_atlas.schemas.canonical_atlas import CanonicalExecutionPlan

        plan = CanonicalExecutionPlan()

        self.assertEqual(plan.genres, ["other"])
        self.assertEqual(plan.concise_description, "")
        self.assertEqual(plan.planner_confidence, 0.25)
        self.assertEqual(plan.profile_name, DEFAULT_PROFILE)
        self.assertEqual(plan.profile, PROFILES[DEFAULT_PROFILE])
        self.assertTrue(plan.profile.caption_policy)
        self.assertEqual(DEFAULT_PROFILE, "other")
        self.assertEqual(plan.chunk_size_sec, 600)
        self.assertEqual(plan.chunk_overlap_sec, 20)
        self.assertEqual(plan.output_language, "en")

    def test_canonical_atlas_module_stays_dataclass_focused(self) -> None:
        import video_atlas.schemas.canonical_atlas as module

        self.assertFalse(hasattr(module, "PROFILES"))
        self.assertFalse(hasattr(module, "resolve_profile"))

    def test_execution_plan_is_available_from_schemas_package(self) -> None:
        from video_atlas.schemas import CanonicalExecutionPlan

        plan = CanonicalExecutionPlan()

        self.assertEqual(plan.genres, ["other"])

    def test_runtime_only_window_types_are_not_exposed_from_schemas(self) -> None:
        with self.assertRaises(ImportError):
            from video_atlas.schemas import DetectionWindowSpec  # noqa: F401

    def test_sports_and_movie_profiles_are_registered(self) -> None:
        from video_atlas.schemas.canonical_registry import (
            PROFILES,
            resolve_profile,
        )

        self.assertIn("sports", PROFILES)
        self.assertIn("movie", PROFILES)

        sports_name, sports_profile = resolve_profile("sports")
        movie_name, movie_profile = resolve_profile("movie")

        self.assertEqual(sports_name, "sports")
        self.assertEqual(movie_name, "movie")
        self.assertEqual(sports_profile.route, "multimodal")
        self.assertEqual(movie_profile.route, "multimodal")
        self.assertTrue(sports_profile.segmentation_policy)
        self.assertTrue(movie_profile.segmentation_policy)
        self.assertTrue(sports_profile.caption_policy)
        self.assertTrue(movie_profile.caption_policy)

    def test_lecture_podcast_and_explanatory_commentary_profiles_are_registered(self) -> None:
        from video_atlas.schemas.canonical_registry import (
            PROFILES,
            resolve_profile,
        )

        for profile_name in ("lecture", "podcast", "explanatory_commentary"):
            self.assertIn(profile_name, PROFILES)

            resolved_name, profile = resolve_profile(profile_name)

            self.assertEqual(resolved_name, profile_name)
            self.assertEqual(profile.route, "text_first")
            self.assertTrue(profile.segmentation_policy)
            self.assertTrue(profile.caption_policy)


if __name__ == "__main__":
    unittest.main()
