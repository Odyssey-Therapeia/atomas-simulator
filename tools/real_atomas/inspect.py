"""CLI summary for installed Atomas evidence files."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from .parsers import (
    parse_achievement_progress,
    parse_achievements,
    parse_atoms_info,
    parse_gamestate,
    parse_preferences_plist,
    parse_strings_file,
)
from .paths import RealAtomasPaths


def build_summary(paths: RealAtomasPaths) -> dict[str, Any]:
    """Parse available sources and return a compact JSON-safe summary."""
    summary: dict[str, Any] = {"existing_sources": {}}
    for source_name, source_path in paths.existing_sources().items():
        summary["existing_sources"][source_name] = {
            "path": str(source_path),
            "sha256": _sha256_file(source_path),
        }

    if paths.atoms_info.exists():
        atoms = parse_atoms_info(paths.atoms_info)
        summary["atoms"] = {
            "count": len(atoms),
            "first": atoms[0].__dict__ if atoms else None,
            "last": atoms[-1].__dict__ if atoms else None,
        }

    if paths.achievements_xml.exists():
        achievements = parse_achievements(paths.achievements_xml)
        summary["achievements"] = {
            "count": len(achievements),
            "ids": sorted(achievements),
        }

    if paths.english_main_strings.exists():
        strings = parse_strings_file(paths.english_main_strings)
        rule_keywords = ("plus", "minus", "neutrino", "dark", "antimatter")
        summary["english_main_strings"] = {
            "count": len(strings),
            "rule_hint_count": sum(
                1
                for value in strings.values()
                if any(keyword in value.lower() for keyword in rule_keywords)
            ),
        }

    if paths.achievement_progress.exists():
        progress = parse_achievement_progress(paths.achievement_progress)
        summary["achievement_progress"] = {
            "achievement_count": len(progress.achievements),
            "counters": progress.counters,
        }

    if paths.tutorial_gamestate.exists():
        state = parse_gamestate(paths.tutorial_gamestate)
        summary["tutorial_gamestate"] = {
            "scalars": state.scalars,
            "bubble_count": len(state.bubbles),
            "center_bubble": state.center_bubble.__dict__,
            "next_atom": state.next_atom.__dict__,
        }

    if paths.preferences_plist.exists():
        preferences = parse_preferences_plist(paths.preferences_plist)
        summary["preferences"] = {
            "high_scores": preferences.high_scores,
            "last_elements": preferences.last_elements,
            "selected_main_atom": preferences.selected_main_atom,
        }

    return summary


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Summarize installed Atomas bundle/user-state evidence."
    )
    parser.add_argument("--app-root", type=Path, default=None)
    parser.add_argument("--container-root", type=Path, default=None)
    args = parser.parse_args()

    default_paths = RealAtomasPaths()
    paths = RealAtomasPaths(
        app_root=args.app_root or default_paths.app_root,
        container_root=args.container_root or default_paths.container_root,
    )
    print(json.dumps(build_summary(paths), indent=2, sort_keys=True))


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source_file:
        for chunk in iter(lambda: source_file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


if __name__ == "__main__":
    main()
