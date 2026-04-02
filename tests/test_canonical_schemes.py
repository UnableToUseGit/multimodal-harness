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
            CAPTION_PROFILES,
            DEFAULT_CAPTION_PROFILE,
            DEFAULT_SEGMENTATION_PROFILE,
            SEGMENTATION_PROFILES,
        )
        from video_atlas.schemas.canonical_atlas import CanonicalExecutionPlan

        plan = CanonicalExecutionPlan()

        self.assertEqual(plan.genres, ["other"])
        self.assertEqual(plan.concise_description, "")
        self.assertEqual(plan.planner_confidence, 0.25)
        self.assertEqual(
            plan.segmentation_specification.profile,
            SEGMENTATION_PROFILES[DEFAULT_SEGMENTATION_PROFILE],
        )
        self.assertEqual(
            plan.caption_specification.profile,
            CAPTION_PROFILES[DEFAULT_CAPTION_PROFILE],
        )
        self.assertTrue(plan.caption_specification.profile.caption_policy)
        self.assertEqual(DEFAULT_SEGMENTATION_PROFILE, "generic_longform_continuous")
        self.assertEqual(plan.chunk_size_sec, 600)
        self.assertEqual(plan.chunk_overlap_sec, 20)

    def test_canonical_atlas_module_stays_dataclass_focused(self) -> None:
        import video_atlas.schemas.canonical_atlas as module

        self.assertFalse(hasattr(module, "SEGMENTATION_PROFILES"))
        self.assertFalse(hasattr(module, "CAPTION_PROFILES"))
        self.assertFalse(hasattr(module, "resolve_segmentation_profile"))

    def test_execution_plan_is_available_from_schemas_package(self) -> None:
        from video_atlas.schemas import CanonicalExecutionPlan

        plan = CanonicalExecutionPlan()

        self.assertEqual(plan.genres, ["other"])

    def test_runtime_only_window_types_are_not_exposed_from_schemas(self) -> None:
        with self.assertRaises(ImportError):
            from video_atlas.schemas import DetectionWindowSpec  # noqa: F401

    def test_sports_broadcast_and_narrative_film_profiles_are_registered(self) -> None:
        from video_atlas.schemas.canonical_registry import (
            CAPTION_PROFILES,
            SEGMENTATION_PROFILES,
            resolve_caption_profile,
            resolve_segmentation_profile,
        )

        self.assertIn("sports_broadcast", SEGMENTATION_PROFILES)
        self.assertIn("narrative_film", SEGMENTATION_PROFILES)
        self.assertIn("sports_broadcast", CAPTION_PROFILES)
        self.assertIn("narrative_film", CAPTION_PROFILES)

        sports_name, sports_profile = resolve_segmentation_profile("sports_broadcast")
        film_name, film_profile = resolve_segmentation_profile("narrative_film")
        sports_caption_name, sports_caption = resolve_caption_profile("sports_broadcast")
        film_caption_name, film_caption = resolve_caption_profile("narrative_film")

        self.assertEqual(sports_name, "sports_broadcast")
        self.assertEqual(film_name, "narrative_film")
        self.assertEqual(sports_caption_name, "sports_broadcast")
        self.assertEqual(film_caption_name, "narrative_film")
        self.assertTrue(sports_profile.segmentation_policy)
        self.assertTrue(film_profile.segmentation_policy)
        self.assertTrue(sports_caption.caption_policy)
        self.assertTrue(film_caption.caption_policy)

    def test_vlog_documentary_and_explanatory_commentary_profiles_are_registered(self) -> None:
        from video_atlas.schemas.canonical_registry import (
            CAPTION_PROFILES,
            SEGMENTATION_PROFILES,
            resolve_caption_profile,
            resolve_segmentation_profile,
        )

        for profile_name in ("vlog_lifestyle", "documentary", "explanatory_commentary"):
            self.assertIn(profile_name, SEGMENTATION_PROFILES)
            self.assertIn(profile_name, CAPTION_PROFILES)

            resolved_name, segmentation_profile = resolve_segmentation_profile(profile_name)
            caption_name, caption_profile = resolve_caption_profile(profile_name)

            self.assertEqual(resolved_name, profile_name)
            self.assertEqual(caption_name, profile_name)
            self.assertTrue(segmentation_profile.segmentation_policy)
            self.assertTrue(caption_profile.caption_policy)


if __name__ == "__main__":
    unittest.main()
