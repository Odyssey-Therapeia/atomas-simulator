"""Typed records emitted by the real Atomas evidence parsers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ElementInfo:
    """Element metadata from Atomas' `atoms_en.info` config."""

    atomic_number: int
    symbol: str
    name: str
    rgb: tuple[int, int, int]
    source_line: int


@dataclass(frozen=True)
class AchievementDefinition:
    """Static achievement metadata from the app bundle XML."""

    achievement_id: str
    title: str
    pre_info: str
    post_info: str
    hidden: bool
    server_visible: bool
    externs: dict[str, str]
    rewards: dict[str, str]
    counters: dict[str, str]
    info: dict[str, str]
    raw_attributes: dict[str, str]


@dataclass(frozen=True)
class AchievementProgressEntry:
    """User progress for one achievement in `ac_save.xml`."""

    achievement_id: str
    unlocked: bool
    progress: float
    counter_target_group_count: int
    raw_attributes: dict[str, str]


@dataclass(frozen=True)
class AchievementProgress:
    """Parsed achievement-progress save plus global counters."""

    achievements: dict[str, AchievementProgressEntry]
    counters: dict[str, int]


@dataclass(frozen=True)
class BubbleRecord:
    """Raw Atomas bubble token. Family/value semantics are still being mapped."""

    family: int
    value: int
    frozen: int | None
    raw_attributes: dict[str, str]


@dataclass(frozen=True)
class RealGameState:
    """Parsed `gss_*.sg` game state with unknown scalars preserved."""

    scalars: dict[str, int]
    bubbles: list[BubbleRecord]
    center_bubble: BubbleRecord
    next_atom: BubbleRecord
    raw_scalar_text: dict[str, str]


@dataclass(frozen=True)
class AtomasPreferences:
    """Known preference groups plus the raw plist dictionary."""

    values: dict[str, Any]
    high_scores: dict[str, int]
    last_elements: dict[str, int]
    selected_main_atom: int | None
