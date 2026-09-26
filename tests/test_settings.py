import json

import pytest

import numbersnap.config.settings as settings_module
from numbersnap.config.settings import Settings


def _use_path(monkeypatch, path) -> None:
    monkeypatch.setattr(Settings, "path", staticmethod(lambda: path))


def test_missing_file_uses_defaults(monkeypatch, tmp_path) -> None:
    _use_path(monkeypatch, tmp_path / "settings.json")
    settings = Settings.load()
    assert settings.hotkey == "Ctrl+Shift+X"
    assert settings.auto_columns
    assert settings.text_number_split
    assert not settings.start_with_windows
    assert settings.load_warning is None


def test_shortcuts_survive_restart(monkeypatch, tmp_path) -> None:
    path = tmp_path / "settings.json"
    _use_path(monkeypatch, path)
    Settings(hotkey="Ctrl+Alt+8", toggle_hotkey="Ctrl+Alt+9").save()
    restarted = Settings.load()
    assert restarted.hotkey == "Ctrl+Alt+8"
    assert restarted.toggle_hotkey == "Ctrl+Alt+9"


def test_auto_columns_setting_survives_restart(monkeypatch, tmp_path) -> None:
    path = tmp_path / "settings.json"
    _use_path(monkeypatch, path)
    Settings(auto_columns=False).save()
    assert not Settings.load().auto_columns


def test_text_number_split_setting_survives_restart(monkeypatch, tmp_path) -> None:
    path = tmp_path / "settings.json"
    _use_path(monkeypatch, path)
    Settings(text_number_split=False).save()
    assert not Settings.load().text_number_split


def test_corrupt_file_falls_back_and_warns(monkeypatch, tmp_path) -> None:
    path = tmp_path / "settings.json"
    path.write_text("{broken", encoding="utf-8")
    _use_path(monkeypatch, path)
    settings = Settings.load()
    assert settings.hotkey == "Ctrl+Shift+X"
    assert settings.load_warning


def test_atomic_save_keeps_previous_file_on_replace_failure(monkeypatch, tmp_path) -> None:
    path = tmp_path / "settings.json"
    path.write_text(json.dumps({"hotkey": "Ctrl+Alt+1"}), encoding="utf-8")
    _use_path(monkeypatch, path)

    def fail_replace(source, target) -> None:
        raise OSError("locked")

    monkeypatch.setattr(settings_module.os, "replace", fail_replace)
    with pytest.raises(OSError, match="locked"):
        Settings(hotkey="Ctrl+Alt+2").save()
    assert json.loads(path.read_text(encoding="utf-8"))["hotkey"] == "Ctrl+Alt+1"
    assert list(tmp_path.glob("*.tmp")) == []


def test_remove_user_data_is_idempotent(monkeypatch, tmp_path) -> None:
    path = tmp_path / "settings.json"
    path.write_text("{}", encoding="utf-8")
    _use_path(monkeypatch, path)
    Settings.remove_user_data()
    Settings.remove_user_data()
    assert not path.exists()
