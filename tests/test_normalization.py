from numbersnap.core.normalization import normalize_numeric_context


def test_keeps_valid_values_as_strings() -> None:
    assert normalize_numeric_context("00123") == "00123"
    assert normalize_numeric_context(" ¥ 123.50 ") == "¥123.50"


def test_fixes_confusables_only_in_numeric_context() -> None:
    assert normalize_numeric_context("l23") == "123"
    assert normalize_numeric_context("O.5") == "0.5"
    assert normalize_numeric_context("1O%") == "10%"


def test_does_not_aggressively_change_words() -> None:
    assert normalize_numeric_context("OIL") == "OIL"
    assert normalize_numeric_context("TOTAL") == "TOTAL"
    assert normalize_numeric_context("ROOM12") == "ROOM12"

