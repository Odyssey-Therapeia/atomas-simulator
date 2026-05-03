"""Parsers for read-only real Atomas bundle and user-state evidence."""

from __future__ import annotations

from pathlib import Path
import plistlib
import re
import xml.etree.ElementTree as ET

from .models import (
    AchievementDefinition,
    AchievementProgress,
    AchievementProgressEntry,
    AtomasPreferences,
    BubbleRecord,
    ElementInfo,
    RealGameState,
)

PathLike = str | Path
STRINGS_ROW_PATTERN = re.compile(r'^\s*"(?P<key>.*)"\s*=\s*"(?P<value>.*)"\s*;?\s*$')


def parse_atoms_info(path: PathLike) -> list[ElementInfo]:
    """Parse `atoms_en.info` rows of `symbol-name-r,g,b`."""
    atoms: list[ElementInfo] = []
    for line_number, raw_line in enumerate(Path(path).read_text().splitlines(), 1):
        line = raw_line.strip()
        if not line:
            continue

        try:
            symbol, name, rgb_text = line.split("-", 2)
            rgb = tuple(int(part) for part in rgb_text.split(","))
        except ValueError as exc:
            raise ValueError(
                f"invalid atoms_en.info row at line {line_number}: {line!r}"
            ) from exc

        if len(rgb) != 3 or any(channel < 0 or channel > 255 for channel in rgb):
            raise ValueError(
                f"invalid RGB triple at line {line_number}: {rgb_text!r}"
            )

        atoms.append(
            ElementInfo(
                atomic_number=len(atoms) + 1,
                symbol=symbol,
                name=name,
                rgb=(rgb[0], rgb[1], rgb[2]),
                source_line=line_number,
            )
        )

    return atoms


def parse_achievements(path: PathLike) -> dict[str, AchievementDefinition]:
    """Parse static achievement definitions keyed by achievement id."""
    root = ET.parse(path).getroot()
    _require_tag(root, "achievements", path)

    achievements: dict[str, AchievementDefinition] = {}
    for achievement in root.findall("achievement"):
        achievement_id = _required_attr(achievement, "id", path)
        achievements[achievement_id] = AchievementDefinition(
            achievement_id=achievement_id,
            title=_child_text(achievement, "title"),
            pre_info=_child_text(achievement, "preInfo"),
            post_info=_child_text(achievement, "postInfo"),
            hidden=achievement.get("h") == "1",
            server_visible=achievement.get("svb") == "1",
            externs=_named_children(achievement, "extern", "id"),
            rewards=_named_children(achievement, "reward", "value"),
            counters=_named_children(achievement, "counter", "value"),
            info=_named_children(achievement, "info", "value"),
            raw_attributes=dict(achievement.attrib),
        )

    return achievements


def parse_achievement_progress(path: PathLike) -> AchievementProgress:
    """Parse user achievement progress from `ac_save.xml`."""
    root = ET.parse(path).getroot()
    _require_tag(root, "achievements", path)

    achievements: dict[str, AchievementProgressEntry] = {}
    counters: dict[str, int] = {}

    for child in root:
        if child.tag == "achievement":
            achievement_id = _required_attr(child, "cID", path)
            achievements[achievement_id] = AchievementProgressEntry(
                achievement_id=achievement_id,
                unlocked=child.get("ul") == "1",
                progress=float(child.get("p", "0")),
                counter_target_group_count=int(child.get("ctgc", "0")),
                raw_attributes=dict(child.attrib),
            )
        elif child.tag == "counter":
            counters[_required_attr(child, "n", path)] = int(
                _required_attr(child, "v", path)
            )

    return AchievementProgress(achievements=achievements, counters=counters)


def parse_gamestate(path: PathLike) -> RealGameState:
    """Parse an Atomas `gss_*.sg` XML game-state file without interpreting ids."""
    root = ET.parse(path).getroot()
    _require_tag(root, "gamestate", path)

    scalars: dict[str, int] = {}
    raw_scalar_text: dict[str, str] = {}
    bubbles: list[BubbleRecord] = []
    center_bubble: BubbleRecord | None = None
    next_atom: BubbleRecord | None = None

    for child in root:
        if child.tag == "bubbles":
            bubbles = [_parse_bubble(bubble, path) for bubble in child]
        elif child.tag == "centerbubble":
            center_bubble = _parse_bubble(child, path)
        elif child.tag == "nextAtom":
            next_atom = _parse_bubble(child, path)
        else:
            text = (child.text or "").strip()
            raw_scalar_text[child.tag] = text
            try:
                scalars[child.tag] = int(text)
            except ValueError as exc:
                raise ValueError(
                    f"expected integer scalar for <{child.tag}> in {path}: {text!r}"
                ) from exc

    if center_bubble is None:
        raise ValueError(f"missing <centerbubble> in {path}")
    if next_atom is None:
        raise ValueError(f"missing <nextAtom> in {path}")

    return RealGameState(
        scalars=scalars,
        bubbles=bubbles,
        center_bubble=center_bubble,
        next_atom=next_atom,
        raw_scalar_text=raw_scalar_text,
    )


def parse_preferences_plist(path: PathLike) -> AtomasPreferences:
    """Parse Atomas preferences and group known score/index keys."""
    with Path(path).open("rb") as preferences_file:
        values = plistlib.load(preferences_file)

    high_scores: dict[str, int] = {}
    last_elements: dict[str, int] = {}
    for key, value in values.items():
        if key.startswith("hs_") and isinstance(value, int):
            high_scores[key.removeprefix("hs_")] = value
        elif key.startswith("le_") and isinstance(value, int):
            last_elements[key.removeprefix("le_")] = value

    selected = values.get("selectedMainAtom")
    selected_main_atom = selected if isinstance(selected, int) else None
    return AtomasPreferences(
        values=dict(values),
        high_scores=high_scores,
        last_elements=last_elements,
        selected_main_atom=selected_main_atom,
    )


def parse_strings_file(path: PathLike) -> dict[str, str]:
    """Parse simple Apple-style `.strings` key/value rows."""
    entries: dict[str, str] = {}
    for line_number, raw_line in enumerate(Path(path).read_text().splitlines(), 1):
        line = raw_line.strip()
        if not line or line.startswith("//"):
            continue

        match = STRINGS_ROW_PATTERN.match(line)
        if match is None:
            raise ValueError(f"invalid .strings row at line {line_number}: {line!r}")

        entries[_unescape_strings_text(match.group("key"))] = _unescape_strings_text(
            match.group("value")
        )

    return entries


def _parse_bubble(element: ET.Element, path: PathLike) -> BubbleRecord:
    family = int(_required_attr(element, "f", path))
    value = int(_required_attr(element, "v", path))
    frozen_text = element.get("fr")
    return BubbleRecord(
        family=family,
        value=value,
        frozen=int(frozen_text) if frozen_text is not None else None,
        raw_attributes=dict(element.attrib),
    )


def _require_tag(element: ET.Element, expected: str, path: PathLike) -> None:
    if element.tag != expected:
        raise ValueError(f"expected <{expected}> root in {path}, got <{element.tag}>")


def _required_attr(element: ET.Element, name: str, path: PathLike) -> str:
    value = element.get(name)
    if value is None:
        raise ValueError(f"missing @{name} on <{element.tag}> in {path}")
    return value


def _child_text(element: ET.Element, tag: str) -> str:
    child = element.find(tag)
    if child is None or child.text is None:
        return ""
    return child.text.strip()


def _named_children(
    element: ET.Element, child_tag: str, value_attr: str
) -> dict[str, str]:
    values: dict[str, str] = {}
    for child in element.findall(child_tag):
        name = child.get("name")
        value = child.get(value_attr)
        if name is not None and value is not None:
            values[name] = value
    return values


def _unescape_strings_text(value: str) -> str:
    return value.replace(r"\"", '"').replace(r"\n", "\n").replace(r"\\", "\\")
