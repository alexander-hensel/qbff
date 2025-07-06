import os
import sys

from PyQt6.QtGui import QIcon, QPixmap, QPainter, QColor
from PyQt6.QtSvg import QSvgRenderer
from qt_material import apply_stylesheet, QtStyleTools


__icons__ = {}
__widgets__ = {}


def __get_path__(relative_path:str) -> str:
    base_path = getattr(sys, "_MEIPASS", os.path.abspath(os.path.dirname(__file__)))
    return os.path.join(base_path, relative_path)


def __colorize_svg_icon__(name:str, color:str) -> QIcon:
    svg_path = __get_path__(f"assets\\icons\\{name}.svg")
    # Render the SVG to a transparent pixmap
    pixmap = QPixmap(24, 24)
    pixmap.fill(QColor(0,0,0,0))
    renderer = QSvgRenderer(svg_path)
    painter = QPainter(pixmap)
    renderer.render(painter)
    painter.end()

    # Apply color tint
    tinted_pixmap = QPixmap(24, 24)
    tinted_pixmap.fill(QColor(0,0,0,0))
    painter = QPainter(tinted_pixmap)
    painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Source)
    painter.drawPixmap(0, 0, pixmap)
    painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
    painter.fillRect(tinted_pixmap.rect(), QColor(color))
    painter.end()
    return QIcon(tinted_pixmap)


def recolor_all_icons():
    color = os.environ.get("QTMATERIAL_PRIMARYTEXTCOLOR", "red")
    for name in __icons__.keys():
        __icons__[name] = __colorize_svg_icon__(name, color)


def get_icon(name:str, widget=None) -> QIcon:
    if name not in __icons__:
        color = os.environ.get("QTMATERIAL_PRIMARYTEXTCOLOR", "red")
        icon = __colorize_svg_icon__(name, color=color)
        __icons__[name] = icon
    if widget:
        __widgets__[widget] = name
    return __icons__[name]


def update_icons():
    recolor_all_icons()
    for widget, name in __widgets__.items():
        icon = get_icon(name)
        widget.setIcon(icon)