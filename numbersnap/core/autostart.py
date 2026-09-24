from __future__ import annotations

import subprocess
import sys
from pathlib import Path

VALUE_NAME = "NumberSnap"
RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"


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


def is_autostart_enabled() -> bool:
    if sys.platform != "win32":
        return False
    import winreg

    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY) as key:
            value, _ = winreg.QueryValueEx(key, VALUE_NAME)
            return bool(value)
    except OSError:
        return False


def set_autostart(enabled: bool) -> None:
    if sys.platform != "win32":
        raise OSError("开机自启只支持 Windows")
    import winreg

    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, RUN_KEY) as key:
        if enabled:
            winreg.SetValueEx(key, VALUE_NAME, 0, winreg.REG_SZ, startup_command())
        else:
            try:
                winreg.DeleteValue(key, VALUE_NAME)
            except FileNotFoundError:
                pass
