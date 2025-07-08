import sys
import enum
from typing import Callable
from PyQt6.QtGui import QIcon, QAction
from PyQt6.QtCore import Qt, QEvent, QObject, QPoint
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QStackedWidget,
    QToolBar,
    QLabel,
    QDockWidget,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QSpacerItem,
    QSizePolicy
)

from bff.app.theming import get_icon, apply_theme, set_widget_icon, Theme
from bff.app.icons import Icons


app = QApplication(sys.argv)


class Exceptions:
    class ViewAlreadyRegistered(Exception):
        def __init__(self, view_name:str) -> None:
            super().__init__(f"A View with the name '{view_name}' is already registered")


class DefaultViews(enum.Enum):
    HOME = "/home"
    SETTINGS = "/settings"
    USERS = "/users"
    ABOUT = "/about"


class _404View(QWidget):
    pass


class AboutView(QWidget):
    pass


class NavBar(QDockWidget):
    def __init__(self, parent:QMainWindow, show_view:Callable[[str], None]):
        super().__init__(None, parent)
        self.__show_view__: Callable[[str], None] = show_view
        self.setFeatures(QDockWidget.DockWidgetFeature.NoDockWidgetFeatures)
        self.setAllowedAreas(Qt.DockWidgetArea.NoDockWidgetArea)
        self.setTitleBarWidget(QWidget())
        self.setFixedWidth(300)
        self.items = QListWidget()
        self.items.itemClicked.connect(self.on_item_clicked)
        self.setWidget(self.items)

    def register_item(self, name: str, icon:str):
        item = QListWidgetItem(name)
        set_widget_icon(icon, item)
        self.items.addItem(item)

    def on_item_clicked(self, item: QListWidgetItem):
        self.__show_view__(item.text())


class BFF(QMainWindow):
    def __init__(self):
        super().__init__()
        self.__views__:dict[str, QWidget] = {}
        self.__theme__:Theme = Theme.LIGHT
        self.__views_stack__ = QStackedWidget()
        self.__views_stack__.addWidget(_404View())
        apply_theme(app, theme=Theme.LIGHT)
        self.setWindowTitle(f"BFF - {sys.modules["__main__"].__file__.split('\\')[-1]}") #type:ignore
        self.setWindowIcon(QIcon(get_icon(Icons.ROBOT.value)))
        self.resize(800, 600)
        self.setCentralWidget(self.__views_stack__)
        # Initialize the toolbar
        self.__toolbar__ = QToolBar("Main Toolbar")
        self.__toolbar__.setMovable(False)
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, self.__toolbar__)
        self.__setup_toolbar__()
        # Initialize the Navigation Bar
        self.__nav_bar__ = NavBar(self, self.show_view)
        self.__nav_bar__.setVisible(False)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.__nav_bar__)
        # start eventlistener on the page
        self.installEventFilter(self)

    def __setup_toolbar__(self):
        """Configures the toolbar."""
        # toggle navbar button
        toggle_navbar = QAction(self)
        set_widget_icon(Icons.MENU.value, toggle_navbar)
        toggle_navbar.setToolTip("Toggle Navigation Bar")
        toggle_navbar.triggered.connect(self.toggle_navbar_visibility)
        self.__toolbar__.addAction(toggle_navbar)
        # current page name
        view_name = QLabel(self)
        view_name.setText("/home")
        view_name.setToolTip("Currently selected View")
        self.__toolbar__.addWidget(view_name)
        # spacer is used to allign other buttons to the right
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.__toolbar__.addWidget(spacer)
        # start/stop button
        self.start_stop_button = QAction(self)
        set_widget_icon(Icons.PLAY.value, self.start_stop_button)
        self.start_stop_button.setCheckable(True)
        self.start_stop_button.setToolTip("Start Measurement")
        self.start_stop_button.triggered.connect(self.on_start_stop_automatic)
        self.__toolbar__.addAction(self.start_stop_button)
        # home button
        home_button = QAction(self)
        set_widget_icon(Icons.HOME.value, home_button)
        home_button.setToolTip("Show Home View")
        home_button.triggered.connect(lambda: self.show_view(name=DefaultViews.HOME.value))
        self.__toolbar__.addAction(home_button)
        # setup button
        settings_button = QAction(self)
        set_widget_icon(Icons.SETTINGS.value, settings_button)
        settings_button.setToolTip("Show Settings View")
        settings_button.triggered.connect(lambda: self.show_view(name=DefaultViews.SETTINGS.value))
        self.__toolbar__.addAction(settings_button)
        # user manager button
        user_manager = QAction(self)
        set_widget_icon(Icons.PERSON.value, user_manager)
        user_manager.setToolTip("Show User Manager")
        user_manager.triggered.connect(lambda: self.show_view(name=DefaultViews.USERS.value))
        self.__toolbar__.addAction(user_manager)
        # change theme
        self.btn_change_theme = QAction(self)
        if self.__theme__ == Theme.LIGHT:
            set_widget_icon(Icons.DARK_MODE.value, self.btn_change_theme)
            self.btn_change_theme.setToolTip("Switch To Dark Mode")
        else:
            set_widget_icon(Icons.LIGHT_MODE.value, self.btn_change_theme)
            self.btn_change_theme.setToolTip("Switch To Light Mode")
        self.btn_change_theme.triggered.connect(self.on_change_theme_clicked)
        self.__toolbar__.addAction(self.btn_change_theme)
        # info
        about_button = QAction(self)
        set_widget_icon(Icons.INFO.value, about_button)
        about_button.setToolTip("About The Project")
        about_button.triggered.connect(lambda: self.show_view(name=DefaultViews.ABOUT.value))
        self.__toolbar__.addAction(about_button)

    def toggle_navbar_visibility(self, val):
        self.__nav_bar__.setVisible(not self.__nav_bar__.isVisible())

    def on_start_stop_automatic(self, val):
        if val:
            set_widget_icon(icon_name=Icons.STOP.value, widget=self.start_stop_button)
            self.start_stop_button.setToolTip("Stop Measurement")
        else:
            set_widget_icon(icon_name=Icons.PLAY.value, widget=self.start_stop_button)
            self.start_stop_button.setToolTip("Start Measurement")

    def on_change_theme_clicked(self):
        if self.__theme__ == Theme.LIGHT:
            icon, self.__theme__, tooltip = "light_mode", Theme.DARK, "Switch To Light Mode"
        else:
            icon, self.__theme__, tooltip = "dark_mode", Theme.LIGHT, "Switch To Dark Mode"
        set_widget_icon(icon_name=icon, widget=self.btn_change_theme)
        self.btn_change_theme.setToolTip(tooltip)
        apply_theme(app, theme=self.__theme__)

    def register_view(self, name:str, widget:QWidget, icon:str = Icons.ROBOT.value):
        if name in self.__views__.keys():
            raise Exceptions.ViewAlreadyRegistered(name)
        self.__views__[name] = widget
        self.__views_stack__.addWidget(self.__views__[name])
        self.__nav_bar__.register_item(name, icon)

    def show_view(self, name:str):
        widget: QWidget | None = self.__views__.get(name, None)
        if widget:
            idx: int = self.__views_stack__.indexOf(widget)
            self.__views_stack__.setCurrentIndex(idx)
            return
        self.__views_stack__.setCurrentIndex(0)

    def eventFilter(self, object: QObject, event: QEvent) -> bool: # type:ignore
        """
        Hide NavBar if user clicks outside it.
        """
        if event.type() == QEvent.Type.MouseButtonPress:
            if self.__nav_bar__.isVisible():
                # Get mouse position relative to NavBar
                pos = self.__nav_bar__.mapFromGlobal(event.globalPosition().toPoint()) #type:ignore
                if not self.__nav_bar__.rect().contains(pos):
                    # Click is outside NavBar -> hide it
                    self.__nav_bar__.setVisible(False)
        return super().eventFilter(object, event)

    def run(self):
        self.show()
        sys.exit(app.exec())


# if __name__ == "__main__":
    # app = QApplication(sys.argv)
    # main_window = BFF()
    # main_window.show()