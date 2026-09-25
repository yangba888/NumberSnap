from numbersnap.main import should_show_window


def test_startup_login_is_hidden() -> None:
    assert not should_show_window(["NumberSnap.exe", "--startup"])
    assert should_show_window(["NumberSnap.exe"])
