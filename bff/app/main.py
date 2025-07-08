import sys
import enum
from typing import Callable
from PyQt6.QtGui import QIcon, QAction
from PyQt6.QtCore import Qt, QEvent, QObject
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QStackedWidget,
    QToolBar,
    QLabel,
    QSizePolicy,
)
from bff.app.theming import get_icon, apply_theme, set_widget_icon, Theme
from bff.app.icons import Icons
from bff.app.about_view import AboutView
from bff.app.config import Config
from bff.app._404 import _404View
from bff.app.navbar import NavBar


app = QApplication(sys.argv)


class Exceptions:
    class ViewAlreadyRegistered(Exception):
        def __init__(self, view_name:str) -> None:
            super().__init__(f"A View with the name '{view_name}' is already registered")


class DefaultViews(enum.Enum):
    HOME = enum.auto()
    SETTINGS = enum.auto()
    USERS = enum.auto()
    ABOUT = enum.auto()


class BFF(QMainWindow):
    def __init__(self):
        super().__init__()
        self.__views__:dict[str, QWidget] = {}
        self.__theme__:Theme = Theme.LIGHT
        self.__views_stack__ = QStackedWidget()
        self.__views_stack__.addWidget(_404View())
        self.register_view(name=DefaultViews.ABOUT.name, widget=AboutView())
        apply_theme(app, theme=Theme.LIGHT)
        self.setWindowTitle(f"{Config.app_name} - {sys.modules["__main__"].__file__.split('\\')[-1]}") #type:ignore
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
        self.view_name = QLabel(self)
        self.view_name.setText("(˚Δ˚)b")
        self.view_name.setToolTip("Currently selected View")
        self.__toolbar__.addWidget(self.view_name)
        
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
        home_button.triggered.connect(lambda: self.show_view(name=DefaultViews.HOME.name))
        self.__toolbar__.addAction(home_button)
        
        # setup button
        settings_button = QAction(self)
        set_widget_icon(Icons.SETTINGS.value, settings_button)
        settings_button.setToolTip("Show Settings View")
        settings_button.triggered.connect(lambda: self.show_view(name=DefaultViews.SETTINGS.name))
        self.__toolbar__.addAction(settings_button)
        
        # user manager button
        user_manager = QAction(self)
        set_widget_icon(Icons.PERSON.value, user_manager)
        user_manager.setToolTip("Show User Manager")
        user_manager.triggered.connect(lambda: self.show_view(name=DefaultViews.USERS.name))
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
        about_button.triggered.connect(lambda: self.show_view(name=DefaultViews.ABOUT.name))
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
        # QMessageBox.warning(self, "Info", "This is a placeholder for the start/stop functionality.")
        # self.statusBar()..showMessage("This is a status message", 5000)  # 5s
        

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
        if name not in DefaultViews._member_names_:
            self.__nav_bar__.register_item(name, icon)

    def show_view(self, name:str):
        widget: QWidget | None = self.__views__.get(name, None)
        if widget:
            idx: int = self.__views_stack__.indexOf(widget)
            self.__views_stack__.setCurrentIndex(idx)
            self.view_name.setText(name)
            return
        self.__views_stack__.setCurrentIndex(0)
        self.view_name.setText("(˚Δ˚)b")

    def eventFilter(self, object: QObject, event: QEvent) -> bool: # type:ignore
        """
        Hide NavBar if user clicks outside it.
        """
        if event.type() == QEvent.Type.MouseButtonPress:
            if self.__nav_bar__.isVisible():
                # Get mouse position relative to NavBar
                pos = self.__nav_bar__.mapFromGlobal(event.globalPosition().toPoint()) #type:ignore
                nav_rect = self.__nav_bar__.rect()
                RESIZE_WIDTH = 20
                resize_area = nav_rect.adjusted(nav_rect.width() + RESIZE_WIDTH, 0, 0, 0)
                if resize_area.contains(pos):
                    # Click is on the resize area, do not hide
                    return super().eventFilter(object, event)
                if not nav_rect.contains(pos):
                # if not self.__nav_bar__.rect().contains(pos):
                    # Click is outside NavBar -> hide it
                    self.__nav_bar__.setVisible(False)
        return super().eventFilter(object, event)

    def run(self):
        self.show()
        sys.exit(app.exec())
