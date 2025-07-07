import sys
import enum
from PyQt6.QtGui import QIcon, QAction
from PyQt6.QtCore import Qt, QEvent, QObject, QPoint
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
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


class NavBar(QDockWidget):
    def __init__(self, parent:QMainWindow):
        super().__init__(None, parent)
        self.main_window:QMainWindow = parent
        self.setFeatures(QDockWidget.DockWidgetFeature.NoDockWidgetFeatures)
        self.setAllowedAreas(Qt.DockWidgetArea.NoDockWidgetArea)
        self.setTitleBarWidget(QWidget())
        self.setFixedWidth(300)
        # List of pages
        self.list_widget = QListWidget()
        self.setWidget(self.list_widget)
        # TODO remove these Dummy items
        item = QListWidgetItem("some item")
        set_widget_icon("home", item)
        item2 = QListWidgetItem("some item2")
        item3 = QListWidgetItem("some item3")
        item4 = QListWidgetItem("some item4")
        self.list_widget.addItem(item)
        self.list_widget.addItem(item2)
        self.list_widget.addItem(item3)
        self.list_widget.addItem(item4)
        # Connect clicks to page change
        self.list_widget.itemClicked.connect(self.on_item_clicked)

    def register_page(self, name: str, widget: QWidget):
        """
        Register a new page with the NavBar.
        """
        item = QListWidgetItem(name)
        item.setData(Qt.ItemDataRole.UserRole, widget)
        self.list_widget.addItem(item)

    def on_item_clicked(self, item: QListWidgetItem):
        """
        Load the selected page into the central widget area.
        """
        page_widget = item.data(Qt.ItemDataRole.UserRole)
        self.main_window.setCentralWidget(page_widget)
        # self.parent().update_page_label(item.text())


class BFF(QMainWindow):
    def __init__(self):
        super().__init__()
        self.__theme__:Theme = Theme.LIGHT
        apply_theme(app, theme=Theme.LIGHT)
        self.setWindowTitle("BFF")
        self.setWindowIcon(QIcon(get_icon(Icons.ROBOT.value)))
        self.resize(800, 600)
        # apply_stylesheet(app, theme=Theme.LIGHT.value, invert_secondary=True)

        # Initialize the toolbar
        self.toolbar = QToolBar("Main Toolbar")
        self.toolbar.setMovable(False)
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, self.toolbar)

        self.__setup_toolbar__()

        self.nav_bar = NavBar(self)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.nav_bar)
        self.nav_bar.setVisible(False)

        self.installEventFilter(self)

    def __setup_toolbar__(self):
        """Configures the toolbar."""
        # toggle navbar button
        toggle_navbar = QAction(self)
        # toggle_navbar.setIcon(get_icon("menu", toggle_navbar))
        set_widget_icon(Icons.MENU.value, toggle_navbar)
        # toggle_navbar.setIcon(get_icon("menu"))
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
        # self.start_button.setIcon(get_icon("play", self.start_button))
        set_widget_icon(Icons.PLAY.value, self.start_button)
        self.start_button.setCheckable(True)
        self.start_button.setToolTip("Start Measurement")
        self.start_button.triggered.connect(self.on_toggle_measurement_clicked)
        self.toolbar.addAction(self.start_button)
        # home button
        home_button = QAction(self)
        # home_button.setIcon(get_icon("home", home_button))
        set_widget_icon(Icons.HOME.value, home_button)
        home_button.setToolTip("Show Home View")
        home_button.triggered.connect(self.on_show_home_clicked)
        self.toolbar.addAction(home_button)
        # setup button
        config_button = QAction(self)
        set_widget_icon(Icons.SETTINGS.value, config_button)
        # config_button.setIcon(get_icon("settings", config_button))
        config_button.setToolTip("Show Config View")
        config_button.triggered.connect(self.on_config_clicked)
        self.toolbar.addAction(config_button)
        # user manager button
        user_manager = QAction(self)
        set_widget_icon(Icons.PERSON.value, user_manager)
        # user_manager.setIcon(get_icon("person", user_manager))
        user_manager.setToolTip("Show User Manager")
        self.toolbar.addAction(user_manager)

        # change theme
        self.change_theme = QAction(self)
        if self.__theme__ == Theme.LIGHT:
            set_widget_icon(Icons.DARK_MODE.value, self.change_theme)
            # self.change_theme.setIcon(get_icon("dark_mode", self.change_theme))
            self.change_theme.setToolTip("Switch To Dark Mode")
        else:
            set_widget_icon(Icons.LIGHT_MODE.value, self.change_theme)
            # self.change_theme.setIcon(get_icon("light_mode", self.change_theme))
            self.change_theme.setToolTip("Switch To Light Mode")
        self.change_theme.triggered.connect(self.on_change_theme_clicked)
        self.toolbar.addAction(self.change_theme)
        # info
        about_button = QAction(self)
        set_widget_icon(Icons.INFO.value, about_button)
        # about_button.setIcon(get_icon("info", about_button))
        about_button.setToolTip("About The Project")
        about_button.triggered.connect(self.on_about_button_clicked)
        self.toolbar.addAction(about_button)

    def on_about_button_clicked(self):
        print("show about button")

    def on_toggle_navbar_clicked(self, val):
        self.nav_bar.setVisible(not self.nav_bar.isVisible())

    def on_toggle_measurement_clicked(self, val):
        if val:
            print("start measurement")
            set_widget_icon(Icons.STOP.value, self.start_button)
            self.start_button.setToolTip("Stop Measurement")
            # self.start_button.setIcon(get_icon(Icons.STOP.value, self.start_button))
        else:
            set_widget_icon(Icons.PLAY.value, self.start_button)
            self.start_button.setToolTip("Start Measurement")
            # self.start_button.setIcon(get_icon(Icons.PLAY.value, self.start_button))
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
        set_widget_icon(icon, self.change_theme)
        # self.change_theme.setIcon(get_icon(icon, self.change_theme))
        self.change_theme.setToolTip(tooltip)
        apply_theme(app, theme=self.__theme__)

    def eventFilter(self, obj: QObject, event: QEvent) -> bool:
        """
        Hide NavBar if user clicks outside it.
        """
        if event.type() == QEvent.Type.MouseButtonPress:
            if self.nav_bar.isVisible():
                # Get mouse position relative to NavBar
                pos = self.nav_bar.mapFromGlobal(event.globalPosition().toPoint())

                if not self.nav_bar.rect().contains(pos):
                    # Click is outside NavBar -> hide it
                    self.nav_bar.setVisible(False)
        return super().eventFilter(obj, event)

    def run(self):
        self.show()
        sys.exit(app.exec())


# if __name__ == "__main__":
    # app = QApplication(sys.argv)
    # main_window = BFF()
    # main_window.show()