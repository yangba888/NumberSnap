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

