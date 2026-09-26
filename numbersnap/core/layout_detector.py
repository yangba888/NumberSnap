from __future__ import annotations

import logging
from dataclasses import dataclass
from statistics import median

from numbersnap.core.models import OCRToken

LOGGER = logging.getLogger(__name__)


@dataclass(slots=True)
class LayoutResult:
    cells: list[list[str]]
    rows: list[list[OCRToken]]
    column_centers: list[float]
    uncertain_rows: frozenset[int] = frozenset()

    @property
    def row_count(self) -> int:
        return len(self.cells)

    @property
    def column_count(self) -> int:
        return max((len(row) for row in self.cells), default=0)


@dataclass(frozen=True, slots=True)
class _ColumnAnchor:
    left: float
    center: float
    right: float


def _cluster_rows(tokens: list[OCRToken]) -> list[list[OCRToken]]:
    if not tokens:
        return []

    typical_height = median(token.height for token in tokens)
    tolerance = max(1.0, typical_height * 0.6)
    groups: list[list[OCRToken]] = []

    for token in sorted(tokens, key=lambda item: (item.center_y, item.center_x)):
        best_index: int | None = None
        best_distance = float("inf")
        for index, row in enumerate(groups):
            row_y = median(item.center_y for item in row)
            distance = abs(token.center_y - row_y)
            overlap_bottom = min(token.bottom, max(item.bottom for item in row))
            overlap_top = max(token.top, min(item.top for item in row))
            overlap = max(0.0, overlap_bottom - overlap_top)
            overlap_ratio = overlap / min(token.height, median(i.height for i in row))
            if (distance <= tolerance or overlap_ratio >= 0.45) and distance < best_distance:
                best_index = index
                best_distance = distance
        if best_index is None:
            groups.append([token])
        else:
            groups[best_index].append(token)

    groups.sort(key=lambda row: median(item.center_y for item in row))
    for row in groups:
        row.sort(key=lambda item: item.center_x)
    if LOGGER.isEnabledFor(logging.DEBUG):
        LOGGER.debug(
            "Row clustering: %s",
            [[item.normalized_text for item in row] for row in groups],
        )
    return groups


def _token_column_cost(token: OCRToken, anchor: _ColumnAnchor) -> float:
    """Support left-, center- and right-aligned numbers of different lengths."""
    return min(
        abs(token.left - anchor.left),
        abs(token.center_x - anchor.center),
        abs(token.right - anchor.right),
    )


def _assignment_cost(row: list[OCRToken], anchors: list[_ColumnAnchor]) -> list[int]:
    """Monotonically assign a sparse row to columns using dynamic programming."""

    item_count, column_count = len(row), len(anchors)
    if item_count == 0:
        return []
    if item_count > column_count:
        return list(range(item_count))

    infinity = float("inf")
    costs = [[infinity] * column_count for _ in range(item_count)]
    previous = [[-1] * column_count for _ in range(item_count)]
    for column in range(column_count):
        costs[0][column] = _token_column_cost(row[0], anchors[column])

    for item in range(1, item_count):
        for column in range(item, column_count):
            for prior in range(item - 1, column):
                value = costs[item - 1][prior] + _token_column_cost(
                    row[item], anchors[column]
                )
                if value < costs[item][column]:
                    costs[item][column] = value
                    previous[item][column] = prior

    last = min(range(item_count - 1, column_count), key=lambda col: costs[-1][col])
    result = [last]
    for item in range(item_count - 1, 0, -1):
        last = previous[item][last]
        result.append(last)
    result.reverse()
    return result


def _detect_columns(rows: list[list[OCRToken]]) -> tuple[list[float], list[list[int]]]:
    if not rows:
        return [], []

    column_count = max(len(row) for row in rows)
    reference_candidates = [row for row in rows if len(row) == column_count]
    all_tokens = [token for row in rows for token in row]
    typical_height = median(token.height for token in all_tokens)
    typical_character_width = median(
        token.width / max(1, len(token.normalized_text)) for token in all_tokens
    )
    gap_scale = max(1.0, typical_height, typical_character_width)

    def gap_score(row: list[OCRToken]) -> tuple[float, float, float]:
        gaps = [
            max(0.0, following.left - current.right) / gap_scale
            for current, following in zip(row, row[1:], strict=False)
        ]
        if not gaps:
            return (0.0, 0.0, -sum(token.width for token in row))
        return (min(gaps), median(gaps), -sum(token.width for token in row))

    reference = max(
        reference_candidates,
        key=gap_score,
    )
    anchors = [
        _ColumnAnchor(token.left, token.center_x, token.right) for token in reference
    ]

    assignments: list[list[int]] = []
    for _ in range(3):
        assignments = [_assignment_cost(row, anchors) for row in rows]
        refined: list[_ColumnAnchor] = []
        for column, fallback in enumerate(anchors):
            samples = [
                row[item]
                for row, mapping in zip(rows, assignments, strict=True)
                for item, assigned in enumerate(mapping)
                if assigned == column
            ]
            refined.append(
                _ColumnAnchor(
                    median(token.left for token in samples),
                    median(token.center_x for token in samples),
                    median(token.right for token in samples),
                )
                if samples
                else fallback
            )
        anchors = refined

    centers = [anchor.center for anchor in anchors]
    LOGGER.debug(
        "Column clustering: scale=%s centers=%s assignments=%s",
        gap_scale,
        centers,
        assignments,
    )
    return centers, assignments


def detect_layout(
    tokens: list[OCRToken],
    preserve_columns: bool = True,
    auto_columns: bool = True,
) -> LayoutResult:
    rows = _cluster_rows(tokens)
    if not rows:
        return LayoutResult([], [], [])

    if not preserve_columns:
        return LayoutResult(
            [[token.normalized_text for token in row] for row in rows], rows, []
        )

    if not auto_columns:
        single_column_rows = [[token] for row in rows for token in row]
        return LayoutResult(
            [[row[0].normalized_text] for row in single_column_rows],
            single_column_rows,
            [],
        )

    centers, assignments = _detect_columns(rows)
    cells: list[list[str]] = []
    for row, mapping in zip(rows, assignments, strict=True):
        values = [""] * len(centers)
        for token, column in zip(row, mapping, strict=True):
            values[column] = token.normalized_text
        cells.append(values)

    LOGGER.debug("Final 2D array: %s", cells)
    return LayoutResult(cells, rows, centers)
