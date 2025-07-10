from __future__ import annotations
from concurrent.futures import thread
from email.policy import default
import sys
import enum
import time
import markdown
import threading
from collections.abc import Callable
from PyQt6.QtCore import Qt, QEvent, QObject, pyqtSignal, QMetaObject, QTimer, QUrl
from PyQt6.QtGui import QIcon, QAction, QDesktopServices
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QStackedWidget,
    QDockWidget,
    QListWidget,
    QListWidgetItem,
    QToolBar,
    QLabel,
    QSizePolicy,
    QVBoxLayout,
    QHBoxLayout,
    QTextBrowser,
    QSpacerItem,
    QPushButton,
)


from bff.app.theming import get_icon, apply_theme, set_widget_icon, Theme
from bff.app.icons import Icons
from bff.app.types import Config, DefaultViews
from bff.app.killable_thread import KillableThread
from bff.app.mp_logging import get_logger, start_logging_subprocess
import logging

__qapp__ = QApplication(sys.argv)


class Exceptions:
    class ViewAlreadyRegistered(Exception):
        def __init__(self, view_name:str) -> None:
            super().__init__(f"A View with the name '{view_name}' is already registered")

    class TaskAlreadyDefined(Exception):
        def __init__(self, function:Callable) -> None:
            super().__init__(f"A Task with the name '{function.__name__}' is already registered")
    
    class TasksAlreadyRunning(Exception):
        def __init__(self, functions:list[str]) -> None:
            functions_str = ", ".join(functions)
            super().__init__(f"Following functions are already running: {functions_str}")


class _404View(QWidget):
    def __init__(self):
        super().__init__()
        face = QLabel(DefaultViews._404.value)
        face.setAlignment(Qt.AlignmentFlag.AlignCenter)
        face.setStyleSheet("font-size: 48px;")
        label = QLabel("404 - it's lonely here")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout = QVBoxLayout(self)
        layout.addStretch(1)
        layout.addWidget(face)
        layout.addSpacerItem(QSpacerItem(0, 20, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed))
        layout.addWidget(label)
        layout.addStretch(1)
        layout.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self.setLayout(layout)


class AboutView(QWidget):
    def __init__(self):
        super().__init__()
        # --- Layouts ---
        main_layout = QHBoxLayout(self)
        self.setLayout(main_layout)
        # --- Markdown Viewer (QTextBrowser) ---
        self.text_browser = QTextBrowser()
        self.text_browser.setStyleSheet("""
            QTextBrowser {
                border: none;
                background: transparent;
            }
        """)
        self.text_browser.setOpenExternalLinks(True)  # Make links clickable
        # Convert Markdown to HTML
        markdown_text = sys.modules["__main__"].__doc__ if sys.modules["__main__"].__doc__ else """ - """
        html = markdown.markdown(markdown_text, extensions=["tables"])
        # add minimal CSS styling
        styled_html = f"""
        <style>
            table {{ border-collapse: collapse; width: 100%; }}
            th, td {{ border: 1px solid #ccc; padding: 8px; text-align: left; }}
            body {{ font-family: Arial, sans-serif; }}
        </style>
        {html}
        """
        self.text_browser.setHtml(styled_html)

        # --- Buttons for URLs ---
        button_urls = [
            ("Find Me On Bitbucket", Config.repository, "storage"),
            ("Get Help", Config.docu_depot, "help"),
            ("About HTTP server", f"http://127.0.0.1:{Config.server_port}/docs", "api"),
        ]
        button_layout = QVBoxLayout()
        for label, url, icon in button_urls:
            btn = QPushButton(label)
            set_widget_icon(icon, btn)  # Set icon if available
            btn.setFlat(True)
            btn.setStyleSheet("text-align: left; padding-left: 8px;") 
            if not url:
                btn.setEnabled(False)
            else:
                btn.clicked.connect(lambda _, link=url: self.open_url(link))
            button_layout.addWidget(btn)
        button_layout.addStretch()

        # --- Assemble layouts ---
        main_layout.addStretch(1)
        main_layout.addWidget(self.text_browser, 3)   # Markdown view
        main_layout.addLayout(button_layout, 1)       # Buttons

    def open_url(self, url):
        """Open the given URL in the system's default browser."""
        QDesktopServices.openUrl(QUrl(url))


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


class BFF(QMainWindow):
    __instance__:BFF|None = None
    __lock__:threading.Lock = threading.Lock()
    __init_done__:bool = False

    def __init__(self):
        super().__init__()
        
        self.__theme__:Theme = Theme.LIGHT

        self.__bg_tasks__:dict[Callable[[], None], KillableThread] = {}
        self.__m_tasks__:dict[Callable[[], None], KillableThread] = {}
        self.__on_start_measurement__:Callable[[], None]|None = None
        self.__on_stop_measurement__:Callable[[], None]|None = None
        self.__on_startup__:Callable[[], None]|None = None
        self.__on_shutdown__:Callable[[], None]|None = None

        self.__views__:dict[str, QWidget] = {}
        self.__views_stack__ = QStackedWidget()
        self.setWindowTitle(f"{Config.app_name} - {sys.modules["__main__"].__file__.split('\\')[-1]}") #type:ignore
        self.setWindowIcon(QIcon(get_icon(Icons.ROBOT.value)))
        self.resize(800, 600)
        self.setCentralWidget(self.__views_stack__)
        
        # Initialize the Navigation Bar
        self.__nav_bar__ = NavBar(self, self.__show_view__)
        self.__nav_bar__.setVisible(False)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.__nav_bar__)

        # Initialize the toolbar
        self.__toolbar__ = AppBar(self, theme=self.__theme__)
        self.__toolbar__.actionTriggered.connect(self.__on_toolbar_action_triggered__)
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, self.__toolbar__)
        
        self.register_view(name=DefaultViews._404.name, widget=_404View())
        self.register_view(name=DefaultViews.ABOUT.name, widget=AboutView())
        
        # start eventlistener on the page
        self.installEventFilter(self)
        apply_theme(__qapp__, theme=Theme.LIGHT)

        BFF.__init_done__ = True  # Mark the instance as initialized

    def __update_start_stop_button__(self, new_state:bool):
        if new_state:
            self.__toolbar__.start_stop_button.setToolTip("Stop Measurement")
            self.__toolbar__.start_stop_button.setChecked(True)
            set_widget_icon(icon_name=Icons.STOP.value, widget=self.__toolbar__.start_stop_button)
        else:
            self.__toolbar__.start_stop_button.setToolTip("Start Measurement")
            self.__toolbar__.start_stop_button.setChecked(False)
            set_widget_icon(icon_name=Icons.PLAY.value, widget=self.__toolbar__.start_stop_button)

    def __show_view__(self, name:str) -> None:
        """Shows the view with the given name in the main window.
        If the view is not registered, it will show the 404 view.   
        Args:
            name (str): The name of the view to be shown.
        """
        widget: QWidget | None = self.__views__.get(name, None)
        if widget:
            idx: int = self.__views_stack__.indexOf(widget)
            self.__views_stack__.setCurrentIndex(idx)
            self.__toolbar__.view_name.setText(name)
            return
        self.__views_stack__.setCurrentIndex(0)
        self.__toolbar__.view_name.setText(DefaultViews._404.value)

    def __on_toolbar_action_triggered__(self, action:QAction) -> None:
        """Handles actions triggered from the toolbar.
        This method is connected to the `actionTriggered` signal of the toolbar.
        Args:
            action (QAction): The action that was triggered.
        """
        match action:
            case self.__toolbar__.toggle_navbar:
                self.__nav_bar__.setVisible(not self.__nav_bar__.isVisible())
            
            case self.__toolbar__.start_stop_button:
                self.__stop_measurement__() if action.isChecked() else self.__start_measurement__()
            
            case self.__toolbar__.btn_change_theme:
                if self.__theme__ == Theme.LIGHT:
                    icon, self.__theme__, tooltip = "light_mode", Theme.DARK, "Switch To Light Mode"
                else:
                    icon, self.__theme__, tooltip = "dark_mode", Theme.LIGHT, "Switch To Dark Mode"
                set_widget_icon(icon_name=icon, widget=self.__toolbar__.btn_change_theme)
                apply_theme(__qapp__, theme=self.__theme__)
                self.__toolbar__.btn_change_theme.setToolTip(tooltip)
            
            case _:
                self.__show_view__(name=action.text())

    def __register_task__(self, function:Callable[[], None], tasks:dict[Callable[[], None], KillableThread]) -> Callable[[], None]:
        if function in tasks.keys():
            raise Exceptions.TaskAlreadyDefined(function=function)
        tasks[function] = KillableThread(target=function)
        return function

    def __get_running_tasks__(self, tasks:dict[Callable[[], None], KillableThread]) -> list[Callable[[], None]]:
        """Returns a list if functions that are currently running (appropriate thread is alive)."""
        running_tasks: list[Callable[[], None]] = []
        for function, thread in tasks.items():
            if thread is None:
                continue
            if thread.is_alive():
                running_tasks.append(function)
        return running_tasks
    
    def __stop_tasks__(self, tasks:dict[Callable[[], None], KillableThread]):
        """Stops all tasks in the given dictionary by killing their threads."""
        running_functions: list[Callable[[], None]] = self.__get_running_tasks__(tasks=tasks)
        for function in running_functions:
            tasks[function].kill()
        for function in running_functions:
            tasks[function].join()

    def __start_tasks__(self, tasks:dict[Callable[[], None], KillableThread]) -> None:
        """Starts all tasks in the given dictionary by starting their threads."""
        running_functions: list[Callable[[], None]] = self.__get_running_tasks__(tasks=tasks)
        if running_functions:
            # raise an error because at least one of the tasks to be started is already running
            names = [function.__name__ for function in running_functions]
            raise Exceptions.TasksAlreadyRunning(names)
        for function in tasks.keys():
            tasks[function] = KillableThread(target=function)
            tasks[function].start()

    def __start_measurement__(self) -> None:
        """Starts measurement and all measurement-tasks in separate threads.
        This method performs the following actions:
        1. Calls the `on_measurement_start` callback if it is set.
        2. Iterates over the measurement tasks and starts each task in a new `KillableThread`.
        3. Updates the application bar.
        """
        # check if any thread is still running
        running_functions = self.__get_running_tasks__(self.__m_tasks__)
        if running_functions:
            # raise an error because at least one of the tasks to be started is already running
            names = [function.__name__ for function in running_functions]
            raise Exceptions.TasksAlreadyRunning(names)
        # let's get started
        if self.__on_start_measurement__ is not None:
            self.__on_start_measurement__()
        self.__start_tasks__(self.__m_tasks__)
        self.__toolbar__.start_stop_button.setToolTip("Stop Measurement")
        self.__toolbar__.start_stop_button.setChecked(True)
        set_widget_icon(icon_name=Icons.STOP.value, widget=self.__toolbar__.start_stop_button)

    def __stop_measurement__(self) -> None:
        """Stops the measurement and all measurement-tasks.
        This method performs the following actions:
        1. Calls the `on_measurement_stop` callback if it is set.
        2. Iterates through all measurement tasks and kills each thread.
        3. Joins each thread to ensure they have completed execution.
        """
        self.__stop_tasks__(self.__m_tasks__)
        if self.__on_stop_measurement__ is not None:
            self.__on_stop_measurement__()
        self.__toolbar__.start_stop_button.setToolTip("Start Measurement")
        self.__toolbar__.start_stop_button.setChecked(False)
        set_widget_icon(icon_name=Icons.PLAY.value, widget=self.__toolbar__.start_stop_button)

    def stop_measurement(self):
        """Stops the measurement and all measurement-tasks.
        Triggers self.__stop_measurement__ in Display Thread so start button us zpdated thread-safe.
        """
        QTimer.singleShot(0, self.__stop_measurement__)

    def register_background_task(self, function:Callable[[], None]) -> Callable[[], None]:
        """Decorator to mark a function as a background task.
        This decorator allows you to define a function that will be executed in the background. 
        The function will be started when the application starts.
        Args:
            function (Callable[[]]): The function to be decorated as a background task.
            Raises:
                Exceptions.BackgroundTaskAlreadyDefined: If the function is already registered as a background task.
            Returns:
                Callable[[], None]: The decorated function.
        """
        return self.__register_task__(function = function, tasks = self.__bg_tasks__)
    
    def register_measurement_task(self, function:Callable[[], None]) -> Callable[[], None]:
        """Decorator to mark a function as a measurement task.
        This decorator allows you to define a function that will be executed as a measurement task. 
        The function will be started when the measurement is started.
        Args:
            function (Callable[[]]): The function to be decorated as a measurement task.
            Raises:
                Exceptions.MeasurementTaskAlreadyDefined: If the function is already registered as a measurement task.
        Returns:    
            None
        """
        return self.__register_task__(function = function, tasks = self.__m_tasks__)
    
    def register_on_start_measurement(self, function:Callable[[], None]) -> Callable[[], None]:
        """Registers a callback function to be called when the measurement is started.
        This function will be called before any measurement tasks are started.
        Args:
            callback (Callable[[]]): The callback function to be called on measurement start.
        """
        self.__on_start_measurement__ = function
        return self.__on_start_measurement__

    def register_on_stop_measurement(self, function:Callable[[], None]) -> Callable[[], None]:
        """Registers a callback function to be called when the measurement is stopped.
        This function will be called after all measurement tasks are stopped.
        Args:
            callback (Callable[[]]): The callback function to be called on measurement stop.
        """
        self.__on_stop_measurement__ = function
        return self.__on_stop_measurement__

    def register_on_startup(self, function:Callable[[], None]) -> Callable[[], None]:
        """Registers a callback function to be called when the application starts up.
        This function will be called after the application is initialized but before any background tasks are started.
        Args:
            callback (Callable[[]]): The callback function to be called on application startup.
        """
        self.__on_startup__ = function
        return self.__on_startup__

    def register_on_shutdown(self, function:Callable[[], None]) -> Callable[[], None]:
        """Registers a callback function to be called when the application is shutting down.
        This function will be called after all background tasks are stopped and before the application exits.
        Args:
            callback (Callable[[]]): The callback function to be called on application shutdown.
        """
        self.__on_shutdown__ = function
        return self.__on_shutdown__

    def register_view(self, name:str, widget:QWidget, icon:str = Icons.ROBOT.value) -> None:
        """Adds a view to the navigation bar. When the item is selected, the given controls will be shown in the body.
        Args:
            name (str): The view name.
            widget (QWidget): QWidget to be displayed when the view is selected.
            icon (str, optional): The icon to be displayed in the navigation bar for this view.
        """
        if name in self.__views__.keys():
            raise Exceptions.ViewAlreadyRegistered(name)
        self.__views__[name] = widget
        self.__views_stack__.addWidget(self.__views__[name])
        if name not in DefaultViews._member_names_:
            self.__nav_bar__.register_item(name, icon)

    def closeEvent(self, event) -> None: # type:ignore
        """Handles the close event of the main window.
        This method is called when the user attempts to close the main window.
        It stops the measurement, stops all background tasks, and calls the shutdown callback if it is set.
        Args:
            event (QCloseEvent): The close event.
        """
        self.__stop_measurement__()
        self.__stop_tasks__(self.__bg_tasks__)
        if self.__on_shutdown__ is not None:
            self.__on_shutdown__()
        event.accept()

    def showEvent(self, event) -> None: #type:ignore
        """Handles the show event of the main window.
        This method is called when the main window is shown.
        It starts the background tasks and calls the startup callback if it is set.
        Args:
            event (QShowEvent): The show event.
        """
        if self.__on_startup__ is not None:
            self.__on_startup__()
        self.__start_tasks__(self.__bg_tasks__)
    
    def eventFilter(self, object: QObject, event: QEvent) -> bool: # type:ignore
        """Event filter to handle mouse events on the main window.
        This method is used to hide the navigation bar when the mouse is clicked outside of it.
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
        sys.exit(__qapp__.exec())


instance:BFF = BFF() 