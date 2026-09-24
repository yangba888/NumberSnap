from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtCore import QRect, Qt
from PySide6.QtGui import QColor, QGuiApplication, QImage, QPainter, QPixmap


@dataclass(frozen=True, slots=True)
class ScreenSnapshot:
    geometry: QRect
    pixmap: QPixmap
    device_pixel_ratio: float


@dataclass(frozen=True, slots=True)
class DesktopSnapshot:
    geometry: QRect
    screens: tuple[ScreenSnapshot, ...]

    def crop(self, global_rect: QRect) -> QImage:
        selected = global_rect.intersected(self.geometry)
        if selected.isEmpty():
            return QImage()

        for screen in self.screens:
            if screen.geometry.contains(selected):
                local = selected.translated(-screen.geometry.topLeft())
                native_rect = _scaled_rect(local, screen.device_pixel_ratio)
                return screen.pixmap.copy(native_rect).toImage().convertToFormat(
                    QImage.Format_RGB888
                )

        # A selection spanning monitors is composed at the highest involved DPR.
        # This avoids lowering a high-DPI screen to logical desktop resolution.
        involved = [screen for screen in self.screens if screen.geometry.intersects(selected)]
        scale = max((screen.device_pixel_ratio for screen in involved), default=1.0)
        target = QImage(
            max(1, round(selected.width() * scale)),
            max(1, round(selected.height() * scale)),
            QImage.Format_RGB888,
        )
        target.fill(QColor(Qt.black))
        painter = QPainter(target)
        try:
            for screen in involved:
                intersection = screen.geometry.intersected(selected)
                source = intersection.translated(-screen.geometry.topLeft())
                source = _scaled_rect(source, screen.device_pixel_ratio)
                destination = intersection.translated(-selected.topLeft())
                destination = _scaled_rect(destination, scale)
                painter.drawPixmap(destination, screen.pixmap, source)
        finally:
            painter.end()
        return target


def _scaled_rect(rect: QRect, scale: float) -> QRect:
    return QRect(
        round(rect.x() * scale),
        round(rect.y() * scale),
        max(1, round(rect.width() * scale)),
        max(1, round(rect.height() * scale)),
    )


def capture_virtual_desktop() -> DesktopSnapshot:
    screens = QGuiApplication.screens()
    if not screens:
        raise RuntimeError("No display is available")

    geometry = screens[0].geometry()
    for screen in screens[1:]:
        geometry = geometry.united(screen.geometry())

    snapshots_list: list[ScreenSnapshot] = []
    for screen in screens:
        pixmap = screen.grabWindow(0)
        snapshots_list.append(
            ScreenSnapshot(screen.geometry(), pixmap, pixmap.devicePixelRatio())
        )
    snapshots = tuple(snapshots_list)
    return DesktopSnapshot(geometry, snapshots)
