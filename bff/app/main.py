from __future__ import annotations
import sys
import typing
import markdown
from collections.abc import Callable
from PyQt6.QtGui import QIcon, QAction, QDesktopServices, QKeySequence
from PyQt6.QtCore import (
    Qt, 
    QEvent, 
    QObject, 
    pyqtSignal, 
    pyqtSlot,
    QMetaObject, 
    QTimer, 
    QUrl,
)
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QMenu,
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


class ActionWithTooltip(QAction):
    def setToolTip(self, tip: str|None):
        shortcut = self.shortcut()
        if not shortcut.isEmpty():
            tip = f"{tip} ({shortcut.toString(QKeySequence.SequenceFormat.NativeText)})"
        super().setToolTip(tip)


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


class ToolBar(QToolBar):

    def __init__(self, parent=None, theme:Theme=Theme.LIGHT):
        super().__init__(parent)
        self.setObjectName("appBar")
        self.setMovable(False)
        self.setFloatable(False)
        self.setAllowedAreas(Qt.ToolBarArea.TopToolBarArea | Qt.ToolBarArea.BottomToolBarArea)

        self.toggle_navbar = ActionWithTooltip("toggleNavbar", self)
        self.toggle_navbar.setShortcut("Ctrl+Shift+m")
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

        self.start_stop_button = ActionWithTooltip("startStopButton", self)
        self.start_stop_button.setObjectName("startStopButton")
        self.start_stop_button.setCheckable(True)
        self.start_stop_button.setChecked(False)
        self.start_stop_button.setShortcut("Ctrl+Shift+r")
        self.start_stop_button.setToolTip("Start Measurement")
        # prevent user to check the button
        self.start_stop_button.triggered.connect(lambda _: self.start_stop_button.setChecked(not self.start_stop_button.isChecked()))
        self.addAction(self.start_stop_button)
        set_widget_icon(Icons.PLAY.value, self.start_stop_button)

        self.home_button = ActionWithTooltip(DefaultViews.HOME.value, parent=self)
        self.home_button.setShortcut("Ctrl+Shift+h")
        self.home_button.setToolTip("Show Home View")
        self.addAction(self.home_button)
        set_widget_icon(Icons.HOME.value, self.home_button)

        self.settings_button = ActionWithTooltip(DefaultViews.SETTINGS.value, self)
        self.settings_button.setShortcut("Ctrl+Shift+s")
        self.settings_button.setToolTip("Show Settings View")
        self.addAction(self.settings_button)
        set_widget_icon(Icons.SETTINGS.value, self.settings_button)

        self.user_manager = ActionWithTooltip(DefaultViews.USERS.value, self)
        self.user_manager.setShortcut("Ctrl+Shift+u")
        self.user_manager.setToolTip("Show User Manager")
        self.addAction(self.user_manager)
        set_widget_icon(Icons.PERSON.value, self.user_manager)

        self.btn_change_theme = ActionWithTooltip("changeThemeButton", self)
        self.btn_change_theme.setShortcut("Ctrl+Shift+t")
        if theme == Theme.LIGHT:
            self.btn_change_theme.setToolTip("Switch To Dark Mode")
            set_widget_icon(Icons.DARK_MODE.value, self.btn_change_theme)
        else:
            self.btn_change_theme.setToolTip("Switch To Light Mode")
            set_widget_icon(Icons.LIGHT_MODE.value, self.btn_change_theme)
        self.addAction(self.btn_change_theme)

        self.about_button = ActionWithTooltip(DefaultViews.ABOUT.value, self)
        self.about_button.setShortcut("Ctrl+Shift+i")
        self.about_button.setToolTip("About The Project")
        self.addAction(self.about_button)
        set_widget_icon(Icons.INFO.value, self.about_button)


class NavBar(QDockWidget):
    show_view = pyqtSignal(str)

    def __init__(self, parent:QMainWindow):
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
        self.setFeatures(QDockWidget.DockWidgetFeature.NoDockWidgetFeatures)
        self.setAllowedAreas(Qt.DockWidgetArea.NoDockWidgetArea)
        self.setTitleBarWidget(QWidget())
        self.items = QListWidget()
        self.items.itemClicked.connect(self.on_item_clicked)
        self.setWidget(self.items)

    def register_item(self, name: str, icon:str):
        item = QListWidgetItem(name)
        set_widget_icon(icon, item)
        self.items.addItem(item)

    @pyqtSlot(QListWidgetItem)
    def on_item_clicked(self, item: QListWidgetItem):
        self.show_view.emit(item.text())


class MainWindow(QMainWindow):
    """The main application class for the BFF (Big Fat Framework) application.
    This class is responsible for managing the main window, views, and application logic.
    It provides methods to register views, background tasks, and measurement tasks, as well as handling application startup and shutdown.
    """
    s_start_button_checked = pyqtSignal(bool)
    s_current_view_changed = pyqtSignal(str)
    s_nav_bar_visible = pyqtSignal(bool)

    def __init__(self, controller:BFF):
        super().__init__()
        self.controller: BFF = controller
        self.theme:Theme = Theme.LIGHT

        self.views:dict[str, QWidget] = {}
        self.views_stack = QStackedWidget()
        # self.view_changed_event_handlers:dict[str, Callable[[str], None]] = {}
        self.setWindowTitle(f"{Config.app_name} - {sys.modules["__main__"].__file__.split('\\')[-1]}") #type:ignore
        self.setWindowIcon(QIcon(get_icon(Icons.ROBOT.value)))
        self.resize(800, 600)
        self.setCentralWidget(self.views_stack)
        
        # Initialize the Navigation Bar
        self.nav_bar = NavBar(self)
        self.nav_bar.show_view.connect(self.on_show_view)
        self.nav_bar.setVisible(False)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.nav_bar)

        # Initialize the toolbar
        self.toolbar = ToolBar(self, theme=self.theme)
        self.toolbar.actionTriggered.connect(self.on_toolbar_action_triggered)
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, self.toolbar)
        
        self.register_view(name=DefaultViews._404.value, widget=_404View())
        self.register_view(name=DefaultViews.ABOUT.value, widget=AboutView())
        
        # start eventlistener on the page
        self.installEventFilter(self)
        apply_theme(__qapp__, theme=Theme.LIGHT)

        self.controller.s_measurement_disabled.connect(self.toolbar.start_stop_button.setDisabled)
        self.controller.s_measurement_running.connect(self.on_update_start_stop_button)
        self.controller.s_show_view.connect(self.on_show_view)

    @typing.override
    def createPopupMenu(self) -> QMenu | None:
        return None

    @pyqtSlot(bool)
    def on_update_start_stop_button(self, new_state:bool):
        """Updates the start/stop button in the toolbar based on the new state.
        Args:
            new_state (bool): The new state of the measurement. If True, the button will be set to "Stop Measurement", otherwise to "Start Measurement".
        """
        if new_state:
            self.toolbar.start_stop_button.setToolTip("Stop Measurement")
            self.toolbar.start_stop_button.setChecked(True)
            set_widget_icon(icon_name=Icons.STOP.value, widget=self.toolbar.start_stop_button)
        else:
            self.toolbar.start_stop_button.setToolTip("Start Measurement")
            self.toolbar.start_stop_button.setChecked(False)
            set_widget_icon(icon_name=Icons.PLAY.value, widget=self.toolbar.start_stop_button)
        self.s_start_button_checked.emit(self.toolbar.start_stop_button.isChecked())

    @pyqtSlot(str)
    def on_show_view(self, name:str) -> None:
        """Shows the view with the given name in the main window.
        If the view is not registered, it will show the 404 view.   
        Args:
            name (str): The name of the view to be shown.
        """
        widget: QWidget | None = self.views.get(name, None)
        if widget:
            idx: int = self.views_stack.indexOf(widget)
            self.views_stack.setCurrentIndex(idx)
            self.toolbar.view_name.setText(name)
            return
        self.views_stack.setCurrentIndex(0)
        self.toolbar.view_name.setText(name)
        self.s_current_view_changed.emit(name)

    @pyqtSlot(QAction)
    def on_toolbar_action_triggered(self, action:QAction) -> None:
        """Handles actions triggered from the toolbar.
        This method is connected to the `actionTriggered` signal of the toolbar.
        Args:
            action (QAction): The action that was triggered.
        """
        match action:
            case self.toolbar.toggle_navbar:
                self.nav_bar.setVisible(not self.nav_bar.isVisible())
                self.s_nav_bar_visible.emit(self.nav_bar.isVisible())
            
            case self.toolbar.start_stop_button:
                self.controller.request_measurement(not self.toolbar.start_stop_button.isChecked())
                self.s_start_button_checked.emit(self.toolbar.start_stop_button.isChecked())
            
            case self.toolbar.btn_change_theme:
                if self.theme == Theme.LIGHT:
                    icon, self.theme, tooltip = "light_mode", Theme.DARK, "Switch To Light Mode"
                else:
                    icon, self.theme, tooltip = "dark_mode", Theme.LIGHT, "Switch To Dark Mode"
                set_widget_icon(icon_name=icon, widget=self.toolbar.btn_change_theme)
                apply_theme(__qapp__, theme=self.theme)
                self.toolbar.btn_change_theme.setToolTip(tooltip)
            
            case _:
                self.on_show_view(name=action.text())

    def register_view(self, name:str, widget:QWidget, icon:str = Icons.ROBOT.value, on_show:Callable[[str], None]|None = None) -> None:
        """Adds a view to the navigation bar. When the item is selected, the given controls will be shown in the body.
        Args:
            name (str): The view name.
            widget (QWidget): QWidget to be displayed when the view is selected.
            icon (str, optional): The icon to be displayed in the navigation bar for this view.
        """
        if name in self.views.keys():
            raise Exceptions.ViewAlreadyRegistered(name)
        self.views[name] = widget
        self.views_stack.addWidget(self.views[name])
        if name not in [v.value for v in DefaultViews]:
            self.nav_bar.register_item(name, icon)

    def show_view(self, name:str) -> None:
        self.controller.s_show_view.emit(name)


    def closeEvent(self, event) -> None: # type:ignore
        """Handles the close event of the main window.
        This method is called when the user attempts to close the main window.
        It stops the measurement, stops all background tasks, and calls the shutdown callback if it is set.
        Args:
            event (QCloseEvent): The close event.
        """
        self.controller.shut_down()
        event.accept()

    def showEvent(self, event) -> None: #type:ignore
        """Handles the show event of the main window.
        This method is called when the main window is shown.
        It starts the background tasks and calls the startup callback if it is set.
        Args:
            event (QShowEvent): The show event.
        """
        self.controller.start_up()
    
    def eventFilter(self, object: QObject, event: QEvent) -> bool: # type:ignore
        """Event filter to handle mouse events on the main window.
        This method is used to hide the navigation bar when the mouse is clicked outside of it.
        """
        if event.type() == QEvent.Type.MouseButtonPress:
            if self.nav_bar.isVisible():
                # Get mouse position relative to NavBar
                pos = self.nav_bar.mapFromGlobal(event.globalPosition().toPoint()) #type:ignore
                nav_rect = self.nav_bar.rect()
                RESIZE_WIDTH = 20
                resize_area = nav_rect.adjusted(nav_rect.width() + RESIZE_WIDTH, 0, 0, 0)
                if resize_area.contains(pos):
                    # Click is on the resize area, do not hide
                    return super().eventFilter(object, event)
                if not nav_rect.contains(pos):
                    # if not self.__nav_bar__.rect().contains(pos):
                    # Click is outside NavBar -> hide it
                    self.nav_bar.setVisible(False)
        return super().eventFilter(object, event)

    def run(self):
        self.show()
        sys.exit(__qapp__.exec())


class BFF(QObject):
    s_measurement_disabled = pyqtSignal(bool)
    s_measurement_running = pyqtSignal(bool)
    s_show_view = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        # self.window_controller = UIController(self)
        self.window = MainWindow(self)

        self.__bg_tasks__:dict[Callable[[], None], KillableThread] = {}
        self.__m_tasks__:dict[Callable[[], None], KillableThread] = {}
        self.__on_start_measurement__:Callable[[], None]|None = None
        self.__on_stop_measurement__:Callable[[], None]|None = None
        self.__on_startup__:Callable[[], None]|None = None
        self.__on_shutdown__:Callable[[], None]|None = None
        self.__measurement_running__:bool = False

    @property
    def is_running(self) -> bool:
        """Returns True if the application is currently running, otherwise False."""
        return self.__measurement_running__

    def __register_task__(self, function:Callable[[], None], tasks:dict[Callable[[], None], KillableThread]) -> Callable[[], None]:
        """Registers a function as a task in the given dictionary.
        This method checks if the function is already registered, and if not, adds it to the dictionary with a new `KillableThread`.
        Args:
            function (Callable[[], None]): The function to be registered as a task.
            tasks (dict[Callable[[], None], KillableThread]): The dictionary to register the task in.
            Raises:
                Exceptions.TaskAlreadyDefined: If the function is already registered as a task.
                Returns:
                    Callable[[], None]: The registered function.
        """
        if function in tasks.keys():
            raise Exceptions.TaskAlreadyDefined(function=function)
        tasks[function] = KillableThread(target=function)
        return function
    
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

    @pyqtSlot(bool)
    def request_measurement(self, start:bool):
        """Request to start or stop the measurement.
        This method emits a signal to enable or disable the measurement based on the `start` parameter
        Args:
            start (bool): If True, the measurement will be started, otherwise it will be stopped.
        """
        self.start_measurement() if start else self.stop_measurement()

    def start_measurement(self) -> None:
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
        self.s_measurement_running.emit(True)     
        self.__measurement_running__ = True

    def stop_measurement(self) -> None:
        """Stops the measurement and all measurement-tasks.
        This method performs the following actions:
        1. Calls the `on_measurement_stop` callback if it is set.
        2. Iterates through all measurement tasks and kills each thread.
        3. Joins each thread to ensure they have completed execution.
        """
        self.__stop_tasks__(self.__m_tasks__)
        if self.__on_stop_measurement__ is not None:
            self.__on_stop_measurement__()
        self.s_measurement_running.emit(False)
        self.__measurement_running__ = False

    @pyqtSlot()
    def start_up(self):
        if self.__on_startup__ is not None:
            self.__on_startup__()
        self.__start_tasks__(self.__bg_tasks__)

    @pyqtSlot()
    def shut_down(self):
        self.stop_measurement()
        self.__stop_tasks__(self.__bg_tasks__)
        if self.__on_shutdown__ is not None:
            self.__on_shutdown__()

    def run(self):
        self.window.run()
