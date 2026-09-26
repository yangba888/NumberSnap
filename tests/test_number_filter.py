import pytest

from numbersnap.core.number_filter import extract_number_spans, extract_numbers, is_number


@pytest.mark.parametrize(
    "value",
    ["123", "-123", "12.56", "1,234.56", "10%", "¥123.50", "$42", "€0.99", "00123"],
)
def test_accepts_supported_number_forms(value: str) -> None:
    assert is_number(value)
    assert extract_numbers(value) == [value]


def test_extracts_number_from_surrounding_text() -> None:
    assert extract_numbers("合计: ¥1,234.50 元") == ["¥1,234.50"]
    assert extract_numbers("增长 10%") == ["10%"]


def test_extracts_numbers_adjacent_to_chinese_text() -> None:
    assert extract_numbers("达成 1") == ["1"]
    assert extract_numbers("啊2") == ["2"]
    assert extract_numbers("的观点蓄电池3") == ["3"]
    assert extract_numbers("从4") == ["4"]


def test_discards_surrounding_english_symbols_and_spaces() -> None:
    assert extract_numbers("abc ! 中文   123   xyz") == ["123"]


def test_rejects_words_and_identifiers() -> None:
    assert not is_number("hello")
    assert extract_numbers("SKU123") == []


def test_preserves_leading_zeroes() -> None:
    assert extract_numbers("00123") == ["00123"]


def test_extract_number_spans_retains_positions() -> None:
    assert extract_number_spans("金额123 456") == [
        ("123", 2, 5),
        ("456", 6, 9),
    ]
