from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass
from pathlib import Path

from PySide6.QtCore import QStandardPaths

LOGGER = logging.getLogger(__name__)


@dataclass(slots=True)
class Settings:
    hotkey: str = "Ctrl+Shift+X"
    toggle_hotkey: str = "Ctrl+Shift+Z"
    numbers_only: bool = True
    auto_copy: bool = True
    preserve_layout: bool = True
    always_on_top: bool = False
    start_with_windows: bool = False
    theme: str = "system"
    debug: bool = False

    @staticmethod
    def path() -> Path:
        root = Path(QStandardPaths.writableLocation(QStandardPaths.AppConfigLocation))
        return root / "settings.json"

    @classmethod
    def load(cls) -> Settings:
        path = cls.path()
        if not path.exists():
            return cls()
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            known = {key: payload[key] for key in asdict(cls()) if key in payload}
            return cls(**known)
        except (OSError, ValueError, TypeError):
            LOGGER.exception("Unable to read settings; using defaults")
            return cls()

    def save(self) -> None:
        path = self.path()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(asdict(self), indent=2), encoding="utf-8")
