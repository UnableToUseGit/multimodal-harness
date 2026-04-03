import unittest


class ImportSmokeTest(unittest.TestCase):
    def test_package_import(self) -> None:
        import video_atlas

        self.assertEqual(video_atlas.__version__, "0.1.0")

    def test_text_first_workflow_direct_import(self) -> None:
        from video_atlas.workflows.text_first_canonical_atlas_workflow import TextFirstCanonicalAtlasWorkflow

        self.assertEqual(TextFirstCanonicalAtlasWorkflow.__name__, "TextFirstCanonicalAtlasWorkflow")

    def test_workflows_public_export(self) -> None:
        from video_atlas.workflows import TextFirstCanonicalAtlasWorkflow

        self.assertEqual(TextFirstCanonicalAtlasWorkflow.__name__, "TextFirstCanonicalAtlasWorkflow")

    def test_create_video_atlas_result_is_not_exported(self) -> None:
        import video_atlas.schemas as schemas

        self.assertFalse(hasattr(schemas, "CreateVideoAtlasResult"))


if __name__ == "__main__":
    unittest.main()
