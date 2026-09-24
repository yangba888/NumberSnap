from numbersnap.core.formatter import to_tsv


def test_formats_grid_as_tsv() -> None:
    assert to_tsv([["123", "456"], ["789", "012"]]) == "123\t456\n789\t012"


def test_preserves_missing_cells() -> None:
    assert to_tsv([["123", "", "789"]]) == "123\t\t789"


def test_sanitizes_embedded_delimiters() -> None:
    assert to_tsv([["12\t3", "4\n5"]]) == "12 3\t4 5"


def test_empty_grid() -> None:
    assert to_tsv([]) == ""

