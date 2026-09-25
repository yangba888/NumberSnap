from __future__ import annotations

import ctypes
import sys
from ctypes import wintypes

from PySide6.QtCore import QObject, Signal
from PySide6.QtNetwork import QLocalServer, QLocalSocket

SERVER_NAME = "NumberSnap.SingleInstance.v1"
ERROR_ALREADY_EXISTS = 183


class SingleInstanceGuard(QObject):
    """Single-instance coordinator using a lightweight local named pipe."""

    activation_requested = Signal()

    def __init__(self, name: str = SERVER_NAME) -> None:
        super().__init__()
        self.name = name
        self._server = QLocalServer(self)
        self._mutex_handle: int | None = None
        self._server.setSocketOptions(QLocalServer.UserAccessOption)
        self._server.newConnection.connect(self._on_new_connection)

    def acquire(self) -> bool:
        if sys.platform == "win32" and not self._acquire_windows_mutex():
            self._request_activation()
            return False
        if self._server.listen(self.name):
            return True
        self._release_windows_mutex()
        if self._request_activation():
            return False
        if sys.platform != "win32":
            QLocalServer.removeServer(self.name)
            return self._server.listen(self.name)
        return False

    def _acquire_windows_mutex(self) -> bool:
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel32.CreateMutexW.argtypes = (ctypes.c_void_p, wintypes.BOOL, wintypes.LPCWSTR)
        kernel32.CreateMutexW.restype = wintypes.HANDLE
        handle = kernel32.CreateMutexW(None, False, f"Local\\{self.name}.Mutex")
        if not handle:
            raise ctypes.WinError(ctypes.get_last_error())
        if ctypes.get_last_error() == ERROR_ALREADY_EXISTS:
            kernel32.CloseHandle(handle)
            return False
        self._mutex_handle = int(handle)
        return True

    def _release_windows_mutex(self) -> None:
        if self._mutex_handle is None:
            return
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel32.CloseHandle(wintypes.HANDLE(self._mutex_handle))
        self._mutex_handle = None

    def _request_activation(self) -> bool:
        socket = QLocalSocket()
        socket.connectToServer(self.name)
        connected = socket.waitForConnected(750)
        if connected:
            socket.disconnectFromServer()
        return connected

    def _on_new_connection(self) -> None:
        while self._server.hasPendingConnections():
            socket = self._server.nextPendingConnection()
            socket.disconnectFromServer()
            socket.deleteLater()
            self.activation_requested.emit()

    def release(self) -> None:
        if self._server.isListening():
            self._server.close()
        if sys.platform != "win32":
            QLocalServer.removeServer(self.name)
        self._release_windows_mutex()

    def __enter__(self) -> SingleInstanceGuard:
        if not self.acquire():
            raise RuntimeError("NumberSnap is already running")
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:  # type: ignore[no-untyped-def]
        self.release()
