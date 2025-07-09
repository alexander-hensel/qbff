from PyQt6.QtWidgets import QToolBar, QLabel, QWidget, QSizePolicy
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction

from bff.app import Icons, set_widget_icon, DefaultViews, Theme


class AppBar(QToolBar):

    def __init__(self, parent=None, theme:Theme=Theme.LIGHT):
        super().__init__(parent)
        self.setObjectName("appBar")
        self.setMovable(False)
        self.setFloatable(False)
        self.setAllowedAreas(Qt.ToolBarArea.TopToolBarArea | Qt.ToolBarArea.BottomToolBarArea)

        self.toggle_navbar = QAction("toggleNavbar", self)
        self.toggle_navbar.setToolTip("Toggle Navigation Bar")
        set_widget_icon(Icons.MENU.value, self.toggle_navbar)
        self.addAction(self.toggle_navbar)

        self.view_name = QLabel(self)
        self.view_name.setText(DefaultViews._404.value)
        self.view_name.setToolTip("Currently selected View")
        self.addWidget(self.view_name)

        # spacer is used to allign other buttons to the right
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.addWidget(spacer)

        self.start_stop_button = QAction("startStopButton", self)
        self.start_stop_button.setObjectName("startStopButton")
        self.start_stop_button.setCheckable(True)
        self.start_stop_button.setChecked(False)
        self.start_stop_button.setToolTip("Start Measurement")
        # prevent user to check the button
        self.start_stop_button.triggered.connect(lambda _: self.start_stop_button.setChecked(not self.start_stop_button.isChecked()))
        self.addAction(self.start_stop_button)
        set_widget_icon(Icons.PLAY.value, self.start_stop_button)

        self.home_button = QAction(DefaultViews.HOME.name, parent=self)
        self.home_button.setToolTip("Show Home View")
        self.addAction(self.home_button)
        set_widget_icon(Icons.HOME.value, self.home_button)

        self.settings_button = QAction("settingButton", self)
        self.settings_button.setToolTip("Show Settings View")
        self.addAction(self.settings_button)
        set_widget_icon(Icons.SETTINGS.value, self.settings_button)

        self.user_manager = QAction(DefaultViews.USERS.name, self)
        self.user_manager.setToolTip("Show User Manager")
        self.addAction(self.user_manager)
        set_widget_icon(Icons.PERSON.value, self.user_manager)

        self.btn_change_theme = QAction("changeThemeButton", self)
        if theme == Theme.LIGHT:
            self.btn_change_theme.setToolTip("Switch To Dark Mode")
            set_widget_icon(Icons.DARK_MODE.value, self.btn_change_theme)
        else:
            self.btn_change_theme.setToolTip("Switch To Light Mode")
            set_widget_icon(Icons.LIGHT_MODE.value, self.btn_change_theme)
        self.addAction(self.btn_change_theme)

        self.about_button = QAction(DefaultViews.ABOUT.name, self)
        self.about_button.setToolTip("About The Project")
        self.addAction(self.about_button)
        set_widget_icon(Icons.INFO.value, self.about_button)
