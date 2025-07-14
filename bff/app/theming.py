import enum
import os
import sys
from typing import Any

from PyQt6.QtGui import QIcon, QPixmap, QPainter, QColor
from PyQt6.QtWidgets import QMainWindow, QWidget, QListWidgetItem
from PyQt6.QtSvg import QSvgRenderer
from qt_material import apply_stylesheet, QtStyleTools
from weakref import WeakSet
import enum
from typing import Protocol


class Theme(enum.Enum):
    # DARK = "dark_blue.xml"
    DARK = "dark_cyan.xml"
    LIGHT = "light_cyan_500.xml"


class IconContainer(Protocol):
    def setIcon(self, icon:QIcon):...

__icons__ : dict[str, QIcon] = {}
__icon_widgets_map__ : dict[str, list[Any]] = {}


def get_path(relative_path:str) -> str:
    base_path = getattr(sys, "_MEIPASS", os.path.abspath(os.path.dirname(__file__)))
    return os.path.join(base_path, relative_path)


def colorize_svg_icon(name:str, color:str) -> QIcon:
    svg_path = get_path(f"assets\\icons\\{name}.svg")
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
        __icons__[name] = colorize_svg_icon(name, color)


def update_widgets():
    for icon_name, icon in __icons__.items():
        if __icon_widgets_map__.get(icon_name, None) is None:
            continue
        for widget in __icon_widgets_map__[icon_name]:
            widget.setIcon(icon)


def get_icon(name:str) -> QIcon:
    if name not in __icons__:
        color = os.environ.get("QTMATERIAL_PRIMARYTEXTCOLOR", "red")
        icon = colorize_svg_icon(name, color=color)
        __icons__[name] = icon
    return __icons__[name]


def set_widget_icon(icon_name:str, widget) -> None:
    # check if current widget is already available in any list
    # is so, remove! To avoid ref leaks and unexpected icons on widgets
    for lst in __icon_widgets_map__.values():
        if widget in lst:
            lst.remove(widget)
    # then apply icon to widget
    icon = get_icon(name=icon_name)
    widget.setIcon(icon)
    if __icon_widgets_map__.get(icon_name, None) is None:
        __icon_widgets_map__[icon_name] = list()
    __icon_widgets_map__[icon_name].append(widget)


def apply_theme(app, theme:Theme) -> None:
    apply_stylesheet(app=app, theme=theme.value, invert_secondary=True)
    recolor_all_icons()
    update_widgets()