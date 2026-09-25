import os
import uuid

from PySide6.QtCore import QCoreApplication

from numbersnap.core.single_instance import SingleInstanceGuard


def test_second_instance_activates_first_instance() -> None:
    app = QCoreApplication.instance() or QCoreApplication([])
    server_name = f"NumberSnap.Test.{os.getpid()}.{uuid.uuid4().hex}"
    first = SingleInstanceGuard(server_name)
    second = SingleInstanceGuard(server_name)
    activations: list[bool] = []
    first.activation_requested.connect(lambda: activations.append(True))
    try:
        assert first.acquire()
        assert not second.acquire()
        for _ in range(10):
            app.processEvents()
            if activations:
                break
        assert activations == [True]
    finally:
        first.release()
        second.release()
