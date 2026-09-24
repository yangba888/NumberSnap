import os
import sys

import pytest

from numbersnap.core.single_instance import SingleInstanceGuard


@pytest.mark.skipif(sys.platform != "win32", reason="Windows named mutex test")
def test_rejects_second_process_instance() -> None:
    mutex_name = f"Local\\NumberSnap.Test.{os.getpid()}"
    first = SingleInstanceGuard(mutex_name)
    second = SingleInstanceGuard(mutex_name)
    try:
        assert first.acquire()
        assert not second.acquire()
    finally:
        first.release()
        second.release()
