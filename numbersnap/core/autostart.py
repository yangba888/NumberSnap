from __future__ import annotations

import os
import subprocess
import sys
from enum import Enum
from pathlib import Path
from typing import Any

VALUE_NAME = "NumberSnap"
RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
STARTUP_APPROVED_KEY = (
    r"Software\Microsoft\Windows\CurrentVersion\Explorer\StartupApproved\Run"
)
_DISABLED_APPROVAL_STATES = {0x03, 0x07}


class AutostartStatus(Enum):
    DISABLED = "disabled"
    ENABLED = "enabled"
    SYSTEM_DISABLED = "system_disabled"
    STALE_PATH = "stale_path"


def startup_command() -> str:
    executable = Path(sys.executable)
    if getattr(sys, "frozen", False):
        arguments = [str(executable), "--startup"]
    else:
        pythonw = executable.with_name("pythonw.exe")
        arguments = [
            str(pythonw if pythonw.exists() else executable),
            "-m",
            "numbersnap",
            "--startup",
        ]
    return subprocess.list2cmdline(arguments)


def _read_registry_value(key_path: str) -> Any | None:
    import winreg

    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path) as key:
            value, _ = winreg.QueryValueEx(key, VALUE_NAME)
            return value
    except FileNotFoundError:
        return None


def _write_run_command(command: str) -> None:
    import winreg

    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, RUN_KEY) as key:
        winreg.SetValueEx(key, VALUE_NAME, 0, winreg.REG_SZ, command)


def _delete_registry_value(key_path: str) -> None:
    import winreg

    try:
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            key_path,
            0,
            winreg.KEY_SET_VALUE,
        ) as key:
            winreg.DeleteValue(key, VALUE_NAME)
    except FileNotFoundError:
        pass


def _commands_match(first: str, second: str) -> bool:
    return os.path.normcase(first.strip()) == os.path.normcase(second.strip())


def get_autostart_status() -> AutostartStatus:
    if sys.platform != "win32":
        return AutostartStatus.DISABLED
    command = _read_registry_value(RUN_KEY)
    if not isinstance(command, str) or not command:
        return AutostartStatus.DISABLED
    approval = _read_registry_value(STARTUP_APPROVED_KEY)
    if isinstance(approval, bytes) and approval and approval[0] in _DISABLED_APPROVAL_STATES:
        return AutostartStatus.SYSTEM_DISABLED
    if not _commands_match(command, startup_command()):
        return AutostartStatus.STALE_PATH
    return AutostartStatus.ENABLED


def is_autostart_enabled() -> bool:
    return get_autostart_status() is AutostartStatus.ENABLED


def set_autostart(enabled: bool) -> None:
    if sys.platform != "win32":
        raise OSError("开机自启只支持 Windows")
    if enabled:
        _write_run_command(startup_command())
        # This is only done after the user explicitly enables the app switch.
        _delete_registry_value(STARTUP_APPROVED_KEY)
    else:
        _delete_registry_value(RUN_KEY)
        _delete_registry_value(STARTUP_APPROVED_KEY)


def reconcile_autostart(preferred_enabled: bool) -> bool:
    """Repair a moved executable without overriding a Windows-disabled item."""
    status = get_autostart_status()
    if status is AutostartStatus.STALE_PATH:
        if preferred_enabled:
            set_autostart(True)
            return True
        set_autostart(False)
    return status is AutostartStatus.ENABLED


def cleanup_autostart() -> None:
    set_autostart(False)
