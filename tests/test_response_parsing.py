import unittest

class ResponseParsingTest(unittest.TestCase):
    def test_parse_markdown_json_block(self) -> None:
        from video_atlas.parsing.llm_responses import parse_json_response

        parsed = parse_json_response("```json\n{\"title\": \"demo\"}\n```")
        self.assertEqual(parsed["title"], "demo")

    def test_parse_think_wrapped_payload(self) -> None:
        from video_atlas.parsing.llm_responses import parse_json_response

        parsed = parse_json_response("<think>internal</think>\n[{\"timestamp\": 12}]")
        self.assertEqual(parsed[0]["timestamp"], 12)

    def test_extract_json_payload_finds_outer_object(self) -> None:
        from video_atlas.parsing.llm_responses import extract_json_payload

        payload = extract_json_payload("prefix {\"title\": \"demo\"} suffix")
        self.assertEqual(payload, "{\"title\": \"demo\"}")


if __name__ == "__main__":
    unittest.main()
