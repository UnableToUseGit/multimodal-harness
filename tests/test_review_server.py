from __future__ import annotations

import unittest

from video_atlas.review.server import _parse_range_header


class ReviewServerRangeTest(unittest.TestCase):
    def test_parse_explicit_range(self) -> None:
        self.assertEqual(_parse_range_header("bytes=10-19", 100), (10, 19))

    def test_parse_open_ended_range(self) -> None:
        self.assertEqual(_parse_range_header("bytes=10-", 100), (10, 99))

    def test_parse_suffix_range(self) -> None:
        self.assertEqual(_parse_range_header("bytes=-20", 100), (80, 99))

    def test_reject_invalid_range(self) -> None:
        self.assertIsNone(_parse_range_header("bytes=150-160", 100))
        self.assertIsNone(_parse_range_header("items=10-20", 100))


if __name__ == "__main__":
    unittest.main()
