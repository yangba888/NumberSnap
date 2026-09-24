import sys

from numbersnap.core.autostart import startup_command


def test_frozen_startup_command_is_quoted_and_silent(monkeypatch) -> None:
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "executable", r"C:\Program Files\NumberSnap\NumberSnap.exe")
    command = startup_command()
    assert command.startswith('"C:\\Program Files\\NumberSnap\\NumberSnap.exe"')
    assert command.endswith("--startup")
