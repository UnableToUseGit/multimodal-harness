from __future__ import annotations

import unittest
from unittest.mock import patch

from scripts import run_review_app


class ReviewAppScriptTest(unittest.TestCase):
    def test_parser_uses_atlas_dir_arguments(self) -> None:
        parser = run_review_app.build_parser()

        args = parser.parse_args(
            [
                "--canonical-atlas-dir",
                "/tmp/canonical",
                "--derived-atlas-dir",
                "/tmp/derived",
            ]
        )

        self.assertEqual(args.canonical_atlas_dir, "/tmp/canonical")
        self.assertEqual(args.derived_atlas_dir, "/tmp/derived")

    def test_main_passes_atlas_dir_arguments_to_server(self) -> None:
        fake_server = type(
            "FakeServer",
            (),
            {
                "url": "http://127.0.0.1:8765",
                "serve_forever": lambda self: None,
                "shutdown": lambda self: None,
            },
        )()

        with patch(
            "scripts.run_review_app.run_review_app",
            return_value=fake_server,
        ) as mock_run_review_app:
            with patch(
                "argparse.ArgumentParser.parse_args",
                return_value=type(
                    "Args",
                    (),
                    {
                        "canonical_atlas_dir": "/tmp/canonical",
                        "derived_atlas_dir": "/tmp/derived",
                        "host": "127.0.0.1",
                        "port": 8765,
                    },
                )(),
            ):
                result = run_review_app.main()

        self.assertEqual(result, 0)
        mock_run_review_app.assert_called_once_with(
            canonical_atlas_dir="/tmp/canonical",
            derived_atlas_dir="/tmp/derived",
            host="127.0.0.1",
            port=8765,
        )


if __name__ == "__main__":
    unittest.main()
