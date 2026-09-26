from numbersnap.core.formatter import to_tsv
from numbersnap.core.layout_detector import detect_layout
from numbersnap.core.models import OCRToken, rectangular_box


def token(text: str, x: float, y: float, width: float = 36, height: float = 18) -> OCRToken:
    return OCRToken(text, text, 0.99, rectangular_box(x, y, width, height))


def test_normal_three_by_three_ignores_input_order() -> None:
    tokens = [
        token("567", 210, 52), token("123", 10, 10), token("901", 410, 94),
        token("789", 410, 10), token("234", 10, 52), token("678", 210, 94),
        token("456", 210, 10), token("890", 410, 52), token("345", 10, 94),
    ]
    assert detect_layout(tokens).cells == [
        ["123", "456", "789"],
        ["234", "567", "890"],
        ["345", "678", "901"],
    ]


def test_small_vertical_misalignment_stays_in_same_row() -> None:
    tokens = [token("1", 10, 10), token("2", 110, 14), token("3", 210, 8)]
    assert detect_layout(tokens).cells == [["1", "2", "3"]]


def test_different_font_sizes_use_dynamic_row_threshold() -> None:
    tokens = [
        token("10", 10, 5, 28, 12), token("20", 110, 7, 32, 18),
        token("30", 10, 45, 45, 28), token("40", 110, 48, 50, 30),
    ]
    assert detect_layout(tokens).cells == [["10", "20"], ["30", "40"]]


def test_missing_middle_cell_is_retained() -> None:
    tokens = [
        token("123", 10, 10), token("456", 210, 10), token("789", 410, 10),
        token("234", 10, 50), token("890", 410, 50),
        token("345", 10, 90), token("678", 210, 90), token("901", 410, 90),
    ]
    assert detect_layout(tokens).cells[1] == ["234", "", "890"]


def test_single_column() -> None:
    tokens = [token("-1", 50, 10), token("2.5", 52, 40), token("10%", 49, 70)]
    assert detect_layout(tokens).cells == [["-1"], ["2.5"], ["10%"]]


def test_single_row() -> None:
    tokens = [token("001", 10, 10), token("$2", 100, 10), token("€3", 200, 10)]
    assert detect_layout(tokens).cells == [["001", "$2", "€3"]]


def test_can_disable_column_preservation() -> None:
    tokens = [
        token("1", 10, 10), token("2", 110, 10), token("3", 210, 10),
        token("4", 10, 50), token("6", 210, 50),
    ]
    assert detect_layout(tokens, preserve_columns=False).cells == [["1", "2", "3"], ["4", "6"]]


def test_auto_columns_creates_two_column_tsv() -> None:
    tokens = [
        token("123", 10, 10), token("456", 210, 10),
        token("234", 10, 50), token("567", 210, 50),
        token("345", 10, 90), token("678", 210, 90),
    ]
    result = detect_layout(tokens)
    assert result.cells == [
        ["123", "456"],
        ["234", "567"],
        ["345", "678"],
    ]
    assert to_tsv(result.cells) == "123\t456\n234\t567\n345\t678"


def test_auto_columns_retains_missing_left_cell() -> None:
    tokens = [
        token("123", 10, 10), token("456", 210, 10),
        token("567", 210, 50),
        token("345", 10, 90), token("678", 210, 90),
    ]
    result = detect_layout(tokens)
    assert result.cells == [
        ["123", "456"],
        ["", "567"],
        ["345", "678"],
    ]
    assert to_tsv(result.cells) == "123\t456\n\t567\n345\t678"


def test_auto_columns_handles_different_number_lengths() -> None:
    tokens = [
        token("12", 10, 10, 20), token("45678", 210, 10, 55),
        token("1234", 10, 50, 44), token("56", 210, 50, 22),
        token("123", 10, 90, 33), token("789", 210, 90, 33),
    ]
    result = detect_layout(tokens)
    assert result.cells == [
        ["12", "45678"],
        ["1234", "56"],
        ["123", "789"],
    ]
    assert to_tsv(result.cells) == "12\t45678\n1234\t56\n123\t789"


def test_auto_columns_can_be_disabled_for_single_column_output() -> None:
    tokens = [
        token("1", 10, 10), token("2", 210, 10),
        token("3", 10, 50), token("4", 210, 50),
    ]
    assert detect_layout(tokens, auto_columns=False).cells == [
        ["1"],
        ["2"],
        ["3"],
        ["4"],
    ]
