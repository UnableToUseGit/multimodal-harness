import json
import unittest

from video_atlas.schemas import AtlasUnit
from video_atlas.workflows.canonical_atlas.structure_composition import (
    CanonicalStructureComposer,
    CanonicalStructureCompositionError,
    build_canonical_structure_composition_messages,
    compose_canonical_structure,
    parse_canonical_structure_composition_result,
    serialize_units_for_composition,
)


class _QueueGenerator:
    def __init__(self, responses):
        self._responses = list(responses)
        self.calls = []

    def generate_single(self, prompt=None, messages=None, schema=None, extra_body=None):
        self.calls.append(
            {
                "prompt": prompt,
                "messages": messages,
                "schema": schema,
                "extra_body": extra_body,
            }
        )
        payload = self._responses.pop(0)
        return {
            "text": json.dumps(payload, ensure_ascii=False),
            "json": payload,
            "response": {"usage": {"total_tokens": 1}},
        }


def _make_units() -> list[AtlasUnit]:
    return [
        AtlasUnit(
            unit_id="unit_0001",
            title="Intro",
            start_time=0.0,
            end_time=10.0,
            summary="Opening block",
            caption="Opening caption",
            subtitles_text="hello",
            folder_name="unit0001-intro",
        ),
        AtlasUnit(
            unit_id="unit_0002",
            title="Middle",
            start_time=10.0,
            end_time=20.0,
            summary="Middle block",
            caption="Middle caption",
            subtitles_text="world",
            folder_name="unit0002-middle",
        ),
        AtlasUnit(
            unit_id="unit_0003",
            title="End",
            start_time=20.0,
            end_time=30.0,
            summary="Ending block",
            caption="Ending caption",
            subtitles_text="done",
            folder_name="unit0003-end",
        ),
    ]


class CanonicalStructureCompositionTest(unittest.TestCase):
    def test_serialize_units_for_composition(self) -> None:
        units = _make_units()

        serialized = serialize_units_for_composition(units)

        self.assertIn("[UNIT_1]", serialized)
        self.assertIn("unit_id: unit_0001", serialized)
        self.assertIn("title: Intro", serialized)
        self.assertIn("time_range: 00:00:00-00:00:10", serialized)
        self.assertIn("subtitles_text:", serialized)

    def test_build_messages_include_priors_and_units(self) -> None:
        units = _make_units()

        messages = build_canonical_structure_composition_messages(
            units=units,
            concise_description="A short explainer",
            genres=["lecture_talk"],
            structure_request="Make it coarse",
        )

        self.assertEqual(messages[0]["role"], "system")
        self.assertEqual(messages[1]["role"], "user")
        self.assertIn("A short explainer", messages[1]["content"])
        self.assertIn("lecture_talk", messages[1]["content"])
        self.assertIn("Make it coarse", messages[1]["content"])
        self.assertIn("unit_id: unit_0001", messages[1]["content"])

    def test_compose_structure_success(self) -> None:
        units = _make_units()
        payload = {
            "title": "A Coarse Chaptered Video",
            "abstract": "A short summary of the full structure.",
            "composition_rationale": "Keep related explanation blocks together.",
            "segments": [
                {
                    "segment_id": "seg_0001",
                    "unit_ids": ["unit_0001", "unit_0002"],
                    "title": "Opening and Development",
                    "summary": "The opening setup and the first explanatory block.",
                    "composition_rationale": "The first two units form one continuous arc.",
                },
                {
                    "segment_id": "seg_0002",
                    "unit_ids": ["unit_0003"],
                    "title": "Closing",
                    "summary": "The ending block.",
                    "composition_rationale": "The final unit is self-contained.",
                },
            ],
        }

        composer = CanonicalStructureComposer(_QueueGenerator([payload]))
        result = composer.compose(
            units=units,
            concise_description="A short explainer",
            genres=["lecture_talk"],
            structure_request="Make it coarse",
        )

        self.assertEqual(result.title, "A Coarse Chaptered Video")
        self.assertEqual(result.abstract, "A short summary of the full structure.")
        self.assertEqual(result.composition_rationale, "Keep related explanation blocks together.")
        self.assertEqual([segment.segment_id for segment in result.segments], ["seg_0001", "seg_0002"])
        self.assertEqual(result.segments[0].unit_ids, ["unit_0001", "unit_0002"])
        self.assertEqual(result.segments[0].folder_name, "seg-0001-opening-and-development-00:00:00-00:00:20")
        self.assertEqual(result.segments[1].start_time, 20.0)
        self.assertEqual(result.segments[1].end_time, 30.0)

    def test_compose_structure_rejects_empty_unit_ids(self) -> None:
        units = _make_units()
        payload = {
            "title": "Broken",
            "abstract": "Broken",
            "segments": [
                {
                    "segment_id": "seg_0001",
                    "unit_ids": [],
                    "title": "Broken segment",
                    "summary": "Broken",
                    "composition_rationale": "Broken",
                }
            ],
        }

        with self.assertRaises(CanonicalStructureCompositionError):
            parse_canonical_structure_composition_result(payload, units)

    def test_compose_structure_rejects_duplicate_units(self) -> None:
        units = _make_units()
        payload = {
            "title": "Broken",
            "abstract": "Broken",
            "segments": [
                {
                    "segment_id": "seg_0001",
                    "unit_ids": ["unit_0001", "unit_0002"],
                    "title": "Segment one",
                    "summary": "One",
                    "composition_rationale": "One",
                },
                {
                    "segment_id": "seg_0002",
                    "unit_ids": ["unit_0002", "unit_0003"],
                    "title": "Segment two",
                    "summary": "Two",
                    "composition_rationale": "Two",
                },
            ],
        }

        with self.assertRaises(CanonicalStructureCompositionError):
            parse_canonical_structure_composition_result(payload, units)

    def test_compose_structure_rejects_non_adjacent_or_reordered_units(self) -> None:
        units = _make_units()
        payload = {
            "title": "Broken",
            "abstract": "Broken",
            "segments": [
                {
                    "segment_id": "seg_0001",
                    "unit_ids": ["unit_0001", "unit_0003"],
                    "title": "Segment one",
                    "summary": "One",
                    "composition_rationale": "One",
                },
                {
                    "segment_id": "seg_0002",
                    "unit_ids": ["unit_0002"],
                    "title": "Segment two",
                    "summary": "Two",
                    "composition_rationale": "Two",
                },
            ],
        }

        with self.assertRaises(CanonicalStructureCompositionError):
            parse_canonical_structure_composition_result(payload, units)

    def test_compose_canonical_structure_uses_structure_composer(self) -> None:
        units = _make_units()
        payload = {
            "title": "Structured",
            "abstract": "Structured abstract",
            "segments": [
                {
                    "segment_id": "seg_0001",
                    "unit_ids": ["unit_0001", "unit_0002", "unit_0003"],
                    "title": "All together",
                    "summary": "All units together.",
                    "composition_rationale": "One continuous block.",
                }
            ],
        }
        composer = _QueueGenerator([payload])

        result = compose_canonical_structure(
            composer,
            units=units,
            concise_description="A short explainer",
            genres=["lecture_talk"],
            structure_request="Make it coarse",
        )

        self.assertEqual(result.title, "Structured")
        self.assertEqual(len(composer.calls), 1)
        self.assertIn("Make it coarse", composer.calls[0]["messages"][1]["content"])


if __name__ == "__main__":
    unittest.main()
