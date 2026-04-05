from __future__ import annotations

import os
import shutil
from dataclasses import dataclass
from importlib import resources
from pathlib import Path


SKILL_DIR_NAME = "mm-harness"


@dataclass(frozen=True)
class SkillInstallResult:
    installed: bool
    target_dir: Path | None
    platform_name: str | None
    message: str


@dataclass(frozen=True)
class SkillUninstallResult:
    removed_paths: tuple[Path, ...]


def _candidate_skill_dirs() -> list[tuple[Path, str]]:
    candidates: list[tuple[Path, str]] = []
    openclaw_home = os.environ.get("OPENCLAW_HOME", "").strip()
    if openclaw_home:
        candidates.append((Path(openclaw_home).expanduser() / ".openclaw" / "skills", "OpenClaw"))
    candidates.extend(
        [
            (Path("~/.agents/skills").expanduser(), "Agent"),
            (Path("~/.openclaw/skills").expanduser(), "OpenClaw"),
            (Path("~/.claude/skills").expanduser(), "Claude Code"),
        ]
    )

    unique: list[tuple[Path, str]] = []
    seen: set[Path] = set()
    for path, platform_name in candidates:
        if path not in seen:
            seen.add(path)
            unique.append((path, platform_name))
    return unique


def _copy_packaged_skill(target_dir: Path) -> None:
    target_dir.mkdir(parents=True, exist_ok=True)
    skill_md = (
        resources.files("video_atlas")
        .joinpath("skills", "mm-harness", "SKILL.md")
        .read_text(encoding="utf-8")
    )
    (target_dir / "SKILL.md").write_text(skill_md, encoding="utf-8")


def install_skill() -> SkillInstallResult:
    for skill_root, platform_name in _candidate_skill_dirs():
        if skill_root.is_dir():
            target_dir = skill_root / SKILL_DIR_NAME
            _copy_packaged_skill(target_dir)
            return SkillInstallResult(
                installed=True,
                target_dir=target_dir,
                platform_name=platform_name,
                message=f"Installed skill to {target_dir}",
            )

    fallback_root = Path("~/.agents/skills").expanduser()
    target_dir = fallback_root / SKILL_DIR_NAME
    _copy_packaged_skill(target_dir)
    return SkillInstallResult(
        installed=True,
        target_dir=target_dir,
        platform_name="Agent",
        message=f"Installed skill to {target_dir}",
    )


def uninstall_skill() -> SkillUninstallResult:
    removed_paths: list[Path] = []
    for skill_root, _platform_name in _candidate_skill_dirs():
        skill_dir = skill_root / SKILL_DIR_NAME
        if skill_dir.is_dir():
            shutil.rmtree(skill_dir)
            removed_paths.append(skill_dir)
    return SkillUninstallResult(removed_paths=tuple(removed_paths))
