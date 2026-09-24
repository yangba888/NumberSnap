from numbersnap.core.clipboard import tsv_to_html


def test_html_clipboard_keeps_cells_as_left_aligned_text() -> None:
    html = tsv_to_html("00123\t456\n7\t")
    assert html.count("<tr>") == 2
    assert html.count("<td ") == 4
    assert "mso-number-format:'\\@'" in html
    assert "text-align:left" in html
    assert ">00123<" in html


def test_html_clipboard_escapes_cell_content() -> None:
    assert "&lt;" in tsv_to_html("<")
