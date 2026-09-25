import sys

import numbersnap.core.autostart as autostart
from numbersnap.core.autostart import AutostartStatus


def test_frozen_startup_command_is_quoted_and_silent(monkeypatch) -> None:
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "executable", r"C:\Program Files\NumberSnap\NumberSnap.exe")
    command = autostart.startup_command()
    assert command.startswith('"C:\\Program Files\\NumberSnap\\NumberSnap.exe"')
    assert command.endswith("--startup")


def _fake_registry(monkeypatch, initial: dict[str, object] | None = None):
    values = dict(initial or {})
    monkeypatch.setattr(sys, "platform", "win32")
    monkeypatch.setattr(autostart, "_read_registry_value", values.get)
    monkeypatch.setattr(
        autostart,
        "_write_run_command",
        lambda command: values.__setitem__(autostart.RUN_KEY, command),
    )
    monkeypatch.setattr(autostart, "_delete_registry_value", lambda key: values.pop(key, None))
    monkeypatch.setattr(autostart, "startup_command", lambda: '"C:\\App\\NumberSnap.exe" --startup')
    return values


def test_enable_and_disable_autostart(monkeypatch) -> None:
    values = _fake_registry(
        monkeypatch,
        {autostart.STARTUP_APPROVED_KEY: bytes([3, 0, 0, 0])},
    )
    autostart.set_autostart(True)
    assert values[autostart.RUN_KEY].endswith("--startup")
    assert autostart.STARTUP_APPROVED_KEY not in values
    assert autostart.get_autostart_status() is AutostartStatus.ENABLED

    autostart.set_autostart(False)
    assert values == {}


def test_system_disabled_item_is_not_reenabled(monkeypatch) -> None:
    values = _fake_registry(
        monkeypatch,
        {
            autostart.RUN_KEY: '"C:\\App\\NumberSnap.exe" --startup',
            autostart.STARTUP_APPROVED_KEY: bytes([3, 0, 0, 0]),
        },
    )
    assert autostart.get_autostart_status() is AutostartStatus.SYSTEM_DISABLED
    assert not autostart.reconcile_autostart(preferred_enabled=True)
    assert autostart.STARTUP_APPROVED_KEY in values


def test_moved_executable_is_repaired_only_for_saved_preference(monkeypatch) -> None:
    values = _fake_registry(
        monkeypatch,
        {autostart.RUN_KEY: '"C:\\Old\\NumberSnap.exe" --startup'},
    )
    assert autostart.get_autostart_status() is AutostartStatus.STALE_PATH
    assert autostart.reconcile_autostart(preferred_enabled=True)
    assert values[autostart.RUN_KEY] == '"C:\\App\\NumberSnap.exe" --startup'

    values[autostart.RUN_KEY] = '"C:\\Old\\NumberSnap.exe" --startup'
    assert not autostart.reconcile_autostart(preferred_enabled=False)
    assert autostart.RUN_KEY not in values


def test_cleanup_removes_all_created_startup_values(monkeypatch) -> None:
    values = _fake_registry(
        monkeypatch,
        {
            autostart.RUN_KEY: "command",
            autostart.STARTUP_APPROVED_KEY: b"state",
        },
    )
    autostart.cleanup_autostart()
    assert values == {}
