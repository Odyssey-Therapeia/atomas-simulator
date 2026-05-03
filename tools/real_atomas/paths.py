"""Default filesystem locations for the installed real Atomas app."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


APP_ROOT = Path("/Applications/Atomas.app/Wrapper/Atomas-mobile.app")
CONTAINER_ROOT = Path.home() / "Library/Containers/com.sirnic.atomas"


@dataclass(frozen=True)
class RealAtomasPaths:
    """Canonical bundle and user-state paths observed on Abe's Mac."""

    app_root: Path = APP_ROOT
    container_root: Path = CONTAINER_ROOT

    @property
    def config_dir(self) -> Path:
        return self.app_root / "asset/config"

    @property
    def atoms_info(self) -> Path:
        return self.config_dir / "atoms_en.info"

    @property
    def achievements_xml(self) -> Path:
        return self.config_dir / "achievements.xml"

    @property
    def english_main_strings(self) -> Path:
        return self.app_root / "asset/strings/en/en_main.strings"

    @property
    def documents_dir(self) -> Path:
        return self.container_root / "Data/Documents"

    @property
    def preferences_plist(self) -> Path:
        return (
            self.container_root
            / "Data/Library/Preferences/com.sirnic.atomas.plist"
        )

    @property
    def tutorial_gamestate(self) -> Path:
        return self.documents_dir / "gss_tutorial.sg"

    @property
    def achievement_progress(self) -> Path:
        return self.documents_dir / "ac_save.xml"

    def existing_sources(self) -> dict[str, Path]:
        """Return the known source files that exist on the current machine."""
        candidates = {
            "atoms": self.atoms_info,
            "achievements": self.achievements_xml,
            "english_main_strings": self.english_main_strings,
            "preferences": self.preferences_plist,
            "tutorial_gamestate": self.tutorial_gamestate,
            "achievement_progress": self.achievement_progress,
        }
        return {
            source_name: path
            for source_name, path in candidates.items()
            if path.exists()
        }
