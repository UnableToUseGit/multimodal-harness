import unittest


class ImportSmokeTest(unittest.TestCase):
    def test_package_import(self) -> None:
        import video_atlas

        self.assertEqual(video_atlas.__version__, "0.1.0")


if __name__ == "__main__":
    unittest.main()
