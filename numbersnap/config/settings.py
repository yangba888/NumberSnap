from __future__ import annotations

import json
import logging
import os
import tempfile
from dataclasses import dataclass, field, fields
from pathlib import Path

from PySide6.QtCore import QStandardPaths

LOGGER = logging.getLogger(__name__)


@dataclass(slots=True)
class Settings:
    hotkey: str = "Ctrl+Shift+X"
    toggle_hotkey: str = "Ctrl+Shift+Z"
    numbers_only: bool = True
    auto_columns: bool = True
    auto_copy: bool = True
    text_number_split: bool = True
    preserve_layout: bool = True
    always_on_top: bool = False
    start_with_windows: bool = False
    theme: str = "system"
    debug: bool = False
    load_warning: str | None = field(default=None, init=False, repr=False, compare=False)

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
            if not isinstance(payload, dict):
                raise ValueError("settings root must be an object")
            defaults = cls()
            known: dict[str, object] = {}
            for item in fields(defaults):
                if not item.init or item.name not in payload:
                    continue
                value = payload[item.name]
                if type(value) is not type(getattr(defaults, item.name)):
                    raise TypeError(f"invalid setting type: {item.name}")
                known[item.name] = value
            return cls(**known)
        except (OSError, ValueError, TypeError):
            LOGGER.exception("Unable to read settings; using defaults")
            settings = cls()
            settings.load_warning = "配置文件损坏，已安全恢复默认设置"
            return settings

    def save(self) -> None:
        path = self.path()
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            item.name: getattr(self, item.name)
            for item in fields(self)
            if item.init
        }
        temporary: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=path.parent,
                prefix=f".{path.name}.",
                suffix=".tmp",
                delete=False,
            ) as stream:
                temporary = Path(stream.name)
                json.dump(payload, stream, ensure_ascii=False, indent=2)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, path)
        finally:
            if temporary is not None and temporary.exists():
                temporary.unlink()

    @classmethod
    def remove_user_data(cls) -> None:
        try:
            cls.path().unlink()
        except FileNotFoundError:
            pass
