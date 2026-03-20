from pathlib import Path
import unittest


class NoCoreDependencyTest(unittest.TestCase):
    def test_source_tree_does_not_reference_video_atlas_core(self):
        source_root = Path(__file__).resolve().parents[1] / "src" / "video_atlas"
        forbidden_refs = []

        for path in source_root.rglob("*.py"):
            if "__pycache__" in path.parts:
                continue
            text = path.read_text(encoding="utf-8")
            if "video_atlas.core" in text or ".core" in text and "from ..core" in text:
                forbidden_refs.append(str(path.relative_to(source_root.parent)))

        self.assertEqual(forbidden_refs, [])


if __name__ == "__main__":
    unittest.main()
