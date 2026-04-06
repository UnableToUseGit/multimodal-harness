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
            (Path("~/.codex/skills").expanduser(), "Codex"),
        ]
    )

    unique: list[tuple[Path, str]] = []
    seen: set[Path] = set()
    for path, platform_name in candidates:
        if path not in seen:
            seen.add(path)
            unique.append((path, platform_name))
    return unique


def _packaged_skill_names() -> tuple[str, ...]:
    skills_root = resources.files("video_atlas").joinpath("skills")
    names: list[str] = []
    for child in skills_root.iterdir():
        if child.is_dir() and child.joinpath("SKILL.md").is_file():
            names.append(child.name)
    return tuple(sorted(names))


def _copy_tree(source, target_dir: Path) -> None:
    target_dir.mkdir(parents=True, exist_ok=True)
    for child in source.iterdir():
        destination = target_dir / child.name
        if child.is_dir():
            _copy_tree(child, destination)
        else:
            destination.write_bytes(child.read_bytes())


def _copy_packaged_skills(skill_root: Path) -> tuple[Path, ...]:
    installed_paths: list[Path] = []
    skills_root = resources.files("video_atlas").joinpath("skills")
    for skill_name in _packaged_skill_names():
        source_dir = skills_root.joinpath(skill_name)
        target_dir = skill_root / skill_name
        if target_dir.exists():
            shutil.rmtree(target_dir)
        _copy_tree(source_dir, target_dir)
        installed_paths.append(target_dir)
    return tuple(installed_paths)


def install_skill() -> SkillInstallResult:
    for skill_root, platform_name in _candidate_skill_dirs():
        if skill_root.is_dir():
            installed_paths = _copy_packaged_skills(skill_root)
            return SkillInstallResult(
                installed=True,
                target_dir=skill_root / SKILL_DIR_NAME,
                platform_name=platform_name,
                message=f"Installed {len(installed_paths)} skills to {skill_root}",
            )

    fallback_root = Path("~/.agents/skills").expanduser()
    installed_paths = _copy_packaged_skills(fallback_root)
    return SkillInstallResult(
        installed=True,
        target_dir=fallback_root / SKILL_DIR_NAME,
        platform_name="Agent",
        message=f"Installed {len(installed_paths)} skills to {fallback_root}",
    )


def uninstall_skill() -> SkillUninstallResult:
    removed_paths: list[Path] = []
    packaged_skill_names = _packaged_skill_names()
    for skill_root, _platform_name in _candidate_skill_dirs():
        for skill_name in packaged_skill_names:
            skill_dir = skill_root / skill_name
            if skill_dir.is_dir():
                shutil.rmtree(skill_dir)
                removed_paths.append(skill_dir)
    return SkillUninstallResult(removed_paths=tuple(removed_paths))
