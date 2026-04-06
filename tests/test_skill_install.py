import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from video_atlas.skill_install import install_skill, uninstall_skill


class SkillInstallTest(unittest.TestCase):
    def test_install_skill_uses_existing_skill_dir(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            skill_root = Path(tmpdir) / ".openclaw" / "skills"
            skill_root.mkdir(parents=True)
            with patch("video_atlas.skill_install._candidate_skill_dirs", return_value=[(skill_root, "OpenClaw")]):
                result = install_skill()

            installed = skill_root / "mm-harness" / "SKILL.md"
            podcast_skill = skill_root / "podcast-to-xhs-post" / "SKILL.md"
            render_script = skill_root / "podcast-to-xhs-post" / "scripts" / "render_xhs.py"
            self.assertTrue(installed.exists())
            self.assertTrue(podcast_skill.exists())
            self.assertTrue(render_script.exists())
            self.assertEqual(result.target_dir, skill_root / "mm-harness")
            self.assertEqual(result.platform_name, "OpenClaw")

    def test_install_skill_falls_back_to_agents_dir(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_home:
            previous_home = os.environ.get("HOME")
            os.environ["HOME"] = tmp_home
            try:
                with patch("video_atlas.skill_install._candidate_skill_dirs", return_value=[]):
                    result = install_skill()
                installed = Path(tmp_home) / ".agents" / "skills" / "mm-harness" / "SKILL.md"
                podcast_skill = Path(tmp_home) / ".agents" / "skills" / "podcast-to-xhs-post" / "SKILL.md"
                self.assertTrue(installed.exists())
                self.assertTrue(podcast_skill.exists())
                self.assertEqual(result.target_dir, installed.parent)
            finally:
                if previous_home is None:
                    os.environ.pop("HOME", None)
                else:
                    os.environ["HOME"] = previous_home

    def test_uninstall_skill_removes_all_known_installations(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root_a = Path(tmpdir) / "a"
            root_b = Path(tmpdir) / "b"
            (root_a / "mm-harness").mkdir(parents=True)
            (root_a / "podcast-to-xhs-post").mkdir(parents=True)
            (root_b / "mm-harness").mkdir(parents=True)
            (root_b / "podcast-to-xhs-post").mkdir(parents=True)
            with patch(
                "video_atlas.skill_install._candidate_skill_dirs",
                return_value=[(root_a, "Agent"), (root_b, "Claude Code")],
            ):
                result = uninstall_skill()

            self.assertEqual(len(result.removed_paths), 4)
            self.assertFalse((root_a / "mm-harness").exists())
            self.assertFalse((root_a / "podcast-to-xhs-post").exists())
            self.assertFalse((root_b / "mm-harness").exists())
            self.assertFalse((root_b / "podcast-to-xhs-post").exists())
