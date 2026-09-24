import pytest

from numbersnap.core.hotkey import (
    CAPTURE_HOTKEY_ID,
    MOD_CONTROL,
    MOD_NOREPEAT,
    MOD_SHIFT,
    MOD_WIN,
    TOGGLE_WINDOW_HOTKEY_ID,
    parse_hotkey,
)


def test_parses_default_hotkey() -> None:
    modifiers, key = parse_hotkey("Ctrl+Shift+X")
    assert modifiers == MOD_CONTROL | MOD_SHIFT | MOD_NOREPEAT
    assert key == ord("X")
    assert CAPTURE_HOTKEY_ID != TOGGLE_WINDOW_HOTKEY_ID


def test_parses_function_and_windows_keys() -> None:
    assert parse_hotkey("Alt+F8")[1] == 0x77
    assert parse_hotkey("Meta+1")[0] & MOD_WIN


@pytest.mark.parametrize("value", ["X", "Ctrl+Escape", "Ctrl+F25", "Ctrl+"])
def test_rejects_unsupported_hotkeys(value: str) -> None:
    with pytest.raises(ValueError):
        parse_hotkey(value)
