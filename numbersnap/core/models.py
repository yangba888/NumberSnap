from __future__ import annotations

from dataclasses import dataclass, replace

type Point = tuple[float, float]
type BoundingBox = tuple[Point, Point, Point, Point]


@dataclass(frozen=True, slots=True)
class OCRToken:
    """One OCR result, retaining both source and normalized text."""

    raw_text: str
    normalized_text: str
    confidence: float
    box: BoundingBox

    @property
    def left(self) -> float:
        return min(point[0] for point in self.box)

    @property
    def right(self) -> float:
        return max(point[0] for point in self.box)

    @property
    def top(self) -> float:
        return min(point[1] for point in self.box)

    @property
    def bottom(self) -> float:
        return max(point[1] for point in self.box)

    @property
    def width(self) -> float:
        return max(1.0, self.right - self.left)

    @property
    def height(self) -> float:
        return max(1.0, self.bottom - self.top)

    @property
    def center_x(self) -> float:
        return (self.left + self.right) / 2.0

    @property
    def center_y(self) -> float:
        return (self.top + self.bottom) / 2.0

    def with_text(self, normalized_text: str) -> OCRToken:
        return replace(self, normalized_text=normalized_text)


def rectangular_box(x: float, y: float, width: float, height: float) -> BoundingBox:
    return ((x, y), (x + width, y), (x + width, y + height), (x, y + height))
