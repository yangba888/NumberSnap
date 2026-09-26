from numbersnap.core.formatter import to_tsv
from numbersnap.core.models import OCRToken, rectangular_box
from numbersnap.core.text_number_splitter import split_text_and_numbers


def token(
    text: str,
    y: float,
    *,
    x: float = 10,
    confidence: float = 0.99,
) -> OCRToken:
    return OCRToken(text, text, confidence, rectangular_box(x, y, len(text) * 12, 20))


def test_splits_product_names_and_inline_quantities_in_row_order() -> None:
    tokens = [
        token("猪梅花肉切块8", 90),
        token("猪肋排长切8", 10),
        token("精选猪小排切块6", 130),
        token("精切猪五花肉12", 50),
    ]
    result = split_text_and_numbers(tokens)
    assert result.cells == [
        ["猪肋排长切", "8"],
        ["精切猪五花肉", "12"],
        ["猪梅花肉切块", "8"],
        ["精选猪小排切块", "6"],
    ]
    assert to_tsv(result.cells) == (
        "猪肋排长切\t8\n精切猪五花肉\t12\n猪梅花肉切块\t8\n精选猪小排切块\t6"
    )


def test_supports_decimal_negative_and_leading_zero_quantities() -> None:
    result = split_text_and_numbers(
        [token("商品A-12.5", 10), token("商品B 0012", 50)]
    )
    assert result.cells == [["商品A", "-12.5"], ["商品B", "0012"]]


def test_keeps_digits_inside_name_when_quantity_is_at_end() -> None:
    result = split_text_and_numbers([token("维生素B12 30", 10)])
    assert result.cells == [["维生素B12", "30"]]
    assert not result.uncertain_rows


def test_missing_quantity_keeps_empty_cell_and_is_marked_uncertain() -> None:
    result = split_text_and_numbers([token("无数量商品", 10)])
    assert result.cells == [["无数量商品", ""]]
    assert result.uncertain_rows == frozenset({0})


def test_corrects_confusable_character_in_numeric_tail() -> None:
    result = split_text_and_numbers([token("猪肉I2", 10)])
    assert result.cells == [["猪肉", "12"]]


def test_low_confidence_row_is_marked_without_changing_tsv() -> None:
    result = split_text_and_numbers([token("猪肋排8", 10, confidence=0.5)])
    assert result.cells == [["猪肋排", "8"]]
    assert result.uncertain_rows == frozenset({0})
    assert to_tsv(result.cells) == "猪肋排\t8"


def test_uses_three_columns_for_compact_serial_name_quantity_rows() -> None:
    tokens = [
        token("03猪梅花肉切块8", 90),
        token("01猪肋排长切8", 10),
        token("02精切猪五花肉12", 50),
    ]
    result = split_text_and_numbers(tokens)
    assert result.cells == [
        ["01", "猪肋排长切", "8"],
        ["02", "精切猪五花肉", "12"],
        ["03", "猪梅花肉切块", "8"],
    ]
    assert to_tsv(result.cells) == (
        "01\t猪肋排长切\t8\n02\t精切猪五花肉\t12\n03\t猪梅花肉切块\t8"
    )


def test_three_columns_keep_internal_name_number() -> None:
    result = split_text_and_numbers(
        [token("01 维生素B12 30", 10), token("02 维生素C 8", 50)]
    )
    assert result.cells == [
        ["01", "维生素B12", "30"],
        ["02", "维生素C", "8"],
    ]


def test_three_column_structure_retains_missing_edge_cells() -> None:
    result = split_text_and_numbers(
        [
            token("01商品甲8", 10),
            token("02商品乙9", 50),
            token("商品丙10", 90),
            token("04商品丁", 130),
        ]
    )
    assert result.cells == [
        ["01", "商品甲", "8"],
        ["02", "商品乙", "9"],
        ["", "商品丙", "10"],
        ["04", "商品丁", ""],
    ]
    assert result.uncertain_rows == frozenset({2, 3})


def test_ambiguous_year_prefix_stays_in_two_column_name_and_is_marked() -> None:
    result = split_text_and_numbers(
        [token("2026年苹果12", 10), token("2025年雪梨8", 50)]
    )
    assert result.cells == [["2026年苹果", "12"], ["2025年雪梨", "8"]]
    assert result.uncertain_rows == frozenset({0, 1})


def test_three_columns_support_signed_decimal_and_leading_zero_fields() -> None:
    result = split_text_and_numbers(
        [token("-01 商品甲 -12.5", 10), token("002 商品乙 0012", 50)]
    )
    assert result.cells == [
        ["-01", "商品甲", "-12.5"],
        ["002", "商品乙", "0012"],
    ]
