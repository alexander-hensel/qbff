from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QToolBar,
    QLabel,
    QPushButton,
    QSpacerItem,
    QSizePolicy
)
from PyQt6.QtGui import QIcon, QAction
from PyQt6.QtCore import Qt
import sys
from qt_material import apply_stylesheet
from icons import get_icon, update_icons
import enum

class Theme(enum.Enum):
    DARK = "dark_cyan.xml"
    LIGHT = "light_cyan.xml"



app = QApplication(sys.argv)
apply_stylesheet(app, theme=Theme.LIGHT.value, invert_secondary=True)

class BFF(QMainWindow):
    def __init__(self):
        super().__init__()
        self.__theme__:Theme = Theme.LIGHT
        self.setWindowTitle("BFF")
        self.setWindowIcon(QIcon("icon.png"))
        self.resize(800, 600)

        # Initialize the toolbar
        self.toolbar = QToolBar("Main Toolbar")
        self.toolbar.setMovable(False)
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, self.toolbar)
        self.__setup_toolbar__()

    def __setup_toolbar__(self):
        # toggle navbar button
        toggle_navbar = QAction(self)
        toggle_navbar.setIcon(get_icon("menu", toggle_navbar))
        toggle_navbar.setToolTip("Toggle Navigation Bar")
        toggle_navbar.triggered.connect(self.on_toggle_navbar_clicked)
        self.toolbar.addAction(toggle_navbar)
        # current page name
        route_name = QLabel(self)
        route_name.setText("/home")
        route_name.setToolTip("Currently selected View")
        self.toolbar.addWidget(route_name)
        # this spacer is used to allign other buttons to the right
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.toolbar.addWidget(spacer)
        # start/stop button
        self.start_button = QAction(self)
        self.start_button.setIcon(get_icon("play", self.start_button))
        self.start_button.setCheckable(True)
        self.start_button.setToolTip("Start Measurement")
        self.start_button.triggered.connect(self.on_toggle_measurement_clicked)
        self.toolbar.addAction(self.start_button)
        # home button
        home_button = QAction(self)
        home_button.setIcon(get_icon("home", home_button))
        home_button.setToolTip("Show Home View")
        home_button.triggered.connect(self.on_show_home_clicked)
        self.toolbar.addAction(home_button)
        # setup button
        config_button = QAction(self)
        config_button.setIcon(get_icon("settings", config_button))
        config_button.setToolTip("Show Config View")
        config_button.triggered.connect(self.on_config_clicked)
        self.toolbar.addAction(config_button)
        # change theme
        self.change_theme = QAction(self)
        if self.__theme__ == Theme.LIGHT:
            self.change_theme.setIcon(get_icon("dark_mode", self.change_theme))
            self.change_theme.setToolTip("Switch To Dark Mode")
        else:
            self.change_theme.setIcon(get_icon("light_mode", self.change_theme))
            self.change_theme.setToolTip("Switch To Light Mode")
        self.change_theme.triggered.connect(self.on_change_theme_clicked)
        self.toolbar.addAction(self.change_theme)
        # info
        about_button = QAction(self)
        about_button.setIcon(get_icon("info", about_button))
        about_button.setToolTip("About The Project")
        about_button.triggered.connect(self.on_about_button_clicked)
        self.toolbar.addAction(about_button)

    def on_about_button_clicked(self):
        print("show about button")

    def on_toggle_navbar_clicked(self, val):
        print(f"toggle nav bar {val}")

    def on_toggle_measurement_clicked(self, val):
        if val:
            print("start measurement")
            self.start_button.setIcon(get_icon("stop", self.start_button))
        else:
            self.start_button.setIcon(get_icon("play", self.start_button))
            print("stop measurement")

    def on_show_home_clicked(self):
        print("Show Home")

    def on_config_clicked(self):
        print ("config")

    def on_change_theme_clicked(self, val):
        icon:str
        tooltip:str
        if self.__theme__ == Theme.LIGHT:
            icon, self.__theme__, tooltip = "light_mode", Theme.DARK, "Switch To Light Mode"
        else:
            icon, self.__theme__, tooltip = "dark_mode", Theme.LIGHT, "Switch To Dark Mode"
        self.change_theme.setIcon(get_icon(icon, self.change_theme))
        self.change_theme.setToolTip(tooltip)
        apply_stylesheet(app, theme=self.__theme__.value, invert_secondary=True)
        update_icons()


if __name__ == "__main__":
    # app = QApplication(sys.argv)
    main_window = BFF()
    main_window.show()
    sys.exit(app.exec())