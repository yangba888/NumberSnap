from __future__ import annotations

import ctypes
import logging
import sys
from ctypes import wintypes

from PySide6.QtCore import QAbstractNativeEventFilter, QCoreApplication, QObject, Signal

LOGGER = logging.getLogger(__name__)

WM_HOTKEY = 0x0312
MOD_CONTROL = 0x0002
MOD_SHIFT = 0x0004
MOD_WIN = 0x0008
MOD_NOREPEAT = 0x4000
CAPTURE_HOTKEY_ID = 0x4E53
TOGGLE_WINDOW_HOTKEY_ID = 0x4E54

_MODIFIERS = {
    "ctrl": MOD_CONTROL,
    "control": MOD_CONTROL,
    "shift": MOD_SHIFT,
    "alt": 0x0001,
    "meta": MOD_WIN,
    "win": MOD_WIN,
}
_NAMED_KEYS = {
    "space": 0x20,
    "tab": 0x09,
    "insert": 0x2D,
    "home": 0x24,
    "end": 0x23,
    "pageup": 0x21,
    "pagedown": 0x22,
}


def parse_hotkey(sequence: str) -> tuple[int, int]:
    parts = [part.strip() for part in sequence.split("+") if part.strip()]
    if len(parts) < 2:
        raise ValueError("快捷键必须包含至少一个修饰键")

    modifiers = MOD_NOREPEAT
    for part in parts[:-1]:
        value = _MODIFIERS.get(part.lower())
        if value is None:
            raise ValueError(f"不支持的修饰键：{part}")
        modifiers |= value

    key_name = parts[-1].upper()
    if len(key_name) == 1 and key_name.isascii() and key_name.isalnum():
        virtual_key = ord(key_name)
    elif key_name.startswith("F") and key_name[1:].isdigit():
        function_number = int(key_name[1:])
        if not 1 <= function_number <= 24:
            raise ValueError("仅支持 F1 到 F24")
        virtual_key = 0x70 + function_number - 1
    else:
        virtual_key = _NAMED_KEYS.get(key_name.lower(), 0)
        if not virtual_key:
            raise ValueError(f"不支持的按键：{parts[-1]}")
    return modifiers, virtual_key


class _HotkeyEventFilter(QAbstractNativeEventFilter):
    def __init__(self, owner: GlobalHotkey) -> None:
        super().__init__()
        self.owner = owner

    def nativeEventFilter(self, event_type, message):  # type: ignore[no-untyped-def]
        if sys.platform == "win32":
            native_message = wintypes.MSG.from_address(int(message))
            if (
                native_message.message == WM_HOTKEY
                and native_message.wParam == self.owner.hotkey_id
            ):
                self.owner.activated.emit()
        return False, 0


class GlobalHotkey(QObject):
    activated = Signal()
    failed = Signal(str)

    def __init__(
        self,
        sequence: str = "Ctrl+Shift+X",
        hotkey_id: int = CAPTURE_HOTKEY_ID,
    ) -> None:
        super().__init__()
        self.sequence = sequence
        self.hotkey_id = hotkey_id
        self._event_filter: _HotkeyEventFilter | None = None
        self._registered = False

    def start(self) -> bool:
        if sys.platform != "win32":
            self.failed.emit("全局快捷键只支持 Windows")
            return False
        if self._registered:
            return self._registered
        try:
            modifiers, virtual_key = parse_hotkey(self.sequence)
        except ValueError as exc:
            self.failed.emit(str(exc))
            return False
        app = QCoreApplication.instance()
        if app is None:
            self.failed.emit("Qt 事件循环尚未启动，无法注册全局快捷键")
            return False
        if not ctypes.windll.user32.RegisterHotKey(
            None, self.hotkey_id, modifiers, virtual_key
        ):
            self.failed.emit(f"无法注册 {self.sequence}；它可能已被其他程序占用")
            return False
        self._event_filter = _HotkeyEventFilter(self)
        app.installNativeEventFilter(self._event_filter)
        self._registered = True
        LOGGER.info("Global hotkey registered on Qt UI thread: %s", self.sequence)
        return True

    def stop(self) -> None:
        if sys.platform == "win32" and self._registered:
            ctypes.windll.user32.UnregisterHotKey(None, self.hotkey_id)
        app = QCoreApplication.instance()
        if app is not None and self._event_filter is not None:
            app.removeNativeEventFilter(self._event_filter)
        self._event_filter = None
        self._registered = False
        LOGGER.info("Global hotkey unregistered")

    def set_sequence(self, sequence: str) -> bool:
        parse_hotkey(sequence)
        previous = self.sequence
        self.stop()
        self.sequence = sequence
        if self.start():
            return True
        self.sequence = previous
        self.start()
        return False
