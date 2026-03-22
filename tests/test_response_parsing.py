import unittest

from video_atlas.agents.canonical_atlas.response_parsing import ResponseParsingMixin


class _Parser(ResponseParsingMixin):
    pass


class ResponseParsingTest(unittest.TestCase):
    def test_parse_markdown_json_block(self) -> None:
        parser = _Parser()
        parsed = parser.parse_response("```json\n{\"title\": \"demo\"}\n```")
        self.assertEqual(parsed["title"], "demo")

    def test_parse_think_wrapped_payload(self) -> None:
        parser = _Parser()
        parsed = parser.parse_response("<think>internal</think>\n[{\"timestamp\": 12}]")
        self.assertEqual(parsed[0]["timestamp"], 12)


if __name__ == "__main__":
    unittest.main()
