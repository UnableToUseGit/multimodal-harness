import unittest

from video_atlas.agents.video_atlas.strategy_builder import StrategyBuilderMixin


class _Builder(StrategyBuilderMixin):
    pass


class StrategyBuilderTest(unittest.TestCase):
    def test_build_spec_fills_defaults_and_normalizes(self) -> None:
        builder = _Builder()
        spec = builder._build_spec_from_strategy_pkg(
            {
                "genre_distribution": {"tutorial_howto": 5, "other": 1},
                "segmentation": {
                    "target_segment_length_sec": [30, 120],
                    "sampling": {"fps": 1.2, "max_resolution": 720, "use_subtitles": "true"},
                },
            }
        )

        self.assertEqual(spec.segmentation_sampling.fps, 1.2)
        self.assertEqual(spec.segmentation_sampling.max_resolution, 720)
        self.assertTrue(spec.segmentation_sampling.use_subtitles)
        self.assertIn("tutorial_howto", spec.segment_spec.genre_str)


if __name__ == "__main__":
    unittest.main()
