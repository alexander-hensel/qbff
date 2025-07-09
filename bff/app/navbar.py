from PyQt6.QtWidgets import (
    QDockWidget,
    QListWidget,
    QListWidgetItem,
    QWidget,
    QMainWindow
)
from PyQt6.QtCore import Qt
from bff.app import set_widget_icon
from collections.abc import Callable

class NavBar(QDockWidget):
    def __init__(self, parent:QMainWindow, show_view:Callable[[str], None]):
        super().__init__(None, parent)
        self.setStyleSheet("""
            QDockWidget {
                background: transparent;
            }
            QDockWidget QWidget {
                background: transparent;
            }
            QListWidget {
                background: transparent;
                border: none;
            }
        """)
        self.__show_view__: Callable[[str], None] = show_view
        self.setFeatures(QDockWidget.DockWidgetFeature.NoDockWidgetFeatures)
        self.setAllowedAreas(Qt.DockWidgetArea.NoDockWidgetArea)
        self.setTitleBarWidget(QWidget())
        # self.
        # self.setFixedWidth(300)
        self.items = QListWidget()
        self.items.itemClicked.connect(self.on_item_clicked)
        self.setWidget(self.items)

    def register_item(self, name: str, icon:str):
        item = QListWidgetItem(name)
        # item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        set_widget_icon(icon, item)
        self.items.addItem(item)

    def on_item_clicked(self, item: QListWidgetItem):
        self.__show_view__(item.text())