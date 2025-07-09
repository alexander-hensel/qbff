from concurrent.futures import thread
from email.policy import default
import sys
import enum
from typing import Callable
from PyQt6.QtGui import QIcon, QAction
from PyQt6.QtCore import Qt, QEvent, QObject, pyqtSignal, QMetaObject
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
from bff.app.types import Config, DefaultViews
from bff.app.exceptions import Exceptions
from bff.app._404_view import _404View
from bff.app.appbar import AppBar
from bff.app.navbar import NavBar
from bff.app.killable_thread import KillableThread
from bff.app.mp_logging import get_logger, start_logging_subprocess
import logging


__qapp__ = QApplication(sys.argv)


class BFF(QMainWindow):

    def __init__(self):
        super().__init__()

        # log_queue = start_logging_subprocess()
        # logger: logging.Logger = get_logger(log_queue)
        # logger.info("Hello from main process!")
        
        self.__theme__:Theme = Theme.LIGHT

        self.__bg_tasks__:dict[Callable[[], None], KillableThread] = {}
        self.__m_tasks__:dict[Callable[[], None], KillableThread] = {}
        self.__on_start_measurement__:Callable[[], None]|None = None
        self.__on_stop_measurement__:Callable[[], None]|None = None
        self.__on_startup__:Callable[[], None]|None = None

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
        self.__toolbar__.actionTriggered.connect(self.on_toolbar_action_triggered)
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, self.__toolbar__)
        
        self.register_view(name=DefaultViews._404.name, widget=_404View())
        self.register_view(name=DefaultViews.ABOUT.name, widget=AboutView())
        
        # start eventlistener on the page
        self.installEventFilter(self)
        apply_theme(__qapp__, theme=Theme.LIGHT)

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

    def __start_background_tasks__(self) -> None:
        """Starts all registered background tasks in separate threads.
        This method iterates over all registered background tasks and starts each one in a new `KillableThread`.
        Raises:
            Exceptions.BackgroundTaskAlreadyDefined: If a task is already registered.
        """
        for task in self.__bg_tasks__.keys():
            self.__bg_tasks__[task].start()
            # TODO write to log

    def on_toolbar_action_triggered(self, action:QAction) -> None:
        """Handles actions triggered from the toolbar.
        This method is connected to the `actionTriggered` signal of the toolbar.
        Args:
            action (QAction): The action that was triggered.
        """
        match action:
            case self.__toolbar__.toggle_navbar:
                self.__nav_bar__.setVisible(not self.__nav_bar__.isVisible())
            
            case self.__toolbar__.start_stop_button:
                print(f"Start/Stop Measurement: {action.isChecked()}")
                self.stop_measurement() if action.isChecked() else self.start_measurement()
            
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
        if function in self.__bg_tasks__.keys():
            raise Exceptions.BackgroundTaskAlreadyDefined(function=function)
        self.__bg_tasks__[function] = KillableThread(target=function)
        return function
    
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
        if function in self.__m_tasks__.keys():
            raise Exceptions.MeasurementTaskAlreadyDefined(function=function)
        self.__m_tasks__[function] = KillableThread(target=function)
        return function
    
    def register_on_start_measurement(self, callback:Callable[[], None]) -> None:
        """Registers a callback function to be called when the measurement is started.
        This function will be called before any measurement tasks are started.
        Args:
            callback (Callable[[]]): The callback function to be called on measurement start.
        """
        self.__on_start_measurement__ = callback

    def register_on_stop_measurement(self, callback:Callable[[], None]) -> None:
        """Registers a callback function to be called when the measurement is stopped.
        This function will be called after all measurement tasks are stopped.
        Args:
            callback (Callable[[]]): The callback function to be called on measurement stop.
        """
        self.__on_stop_measurement__ = callback

    def register_on_startup(self, callback:Callable[[], None]) -> None:
        """Registers a callback function to be called when the application starts up.
        This function will be called after the application is initialized but before any background tasks are started.
        Args:
            callback (Callable[[]]): The callback function to be called on application startup.
        """
        self.__on_startup__ = callback

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

    def start_measurement(self) -> None:
        """Starts measurement and all measurement-tasks in separate threads.
        This method performs the following actions:
        1. Calls the `on_measurement_start` callback if it is set.
        2. Iterates over the measurement tasks and starts each task in a new `KillableThread`.
        3. Updates the application bar.
        """
        # check if any thread is still running
        running_tasks = []
        for function, thread in self.__m_tasks__.items():
            if thread.is_alive():
                running_tasks.append(function.__name__)
        if running_tasks:
            raise Exceptions.MeasurementAlreadyRunning(functions=running_tasks)
        # let's get started
        if self.__on_start_measurement__ is not None:
            self.__on_start_measurement__()
        for task in self.__m_tasks__.keys():
            thread = KillableThread(target=task)
            self.__m_tasks__[task] = KillableThread(target=task)
            self.__m_tasks__[task].start()
        self.__toolbar__.start_stop_button.setToolTip("Stop Measurement")
        self.__toolbar__.start_stop_button.setChecked(True)
        set_widget_icon(icon_name=Icons.STOP.value, widget=self.__toolbar__.start_stop_button)

    def stop_measurement(self) -> None:
        """Stops the measurement and all measurement-tasks.
        This method performs the following actions:
        1. Calls the `on_measurement_stop` callback if it is set.
        2. Iterates through all measurement tasks and kills each thread.
        3. Joins each thread to ensure they have completed execution.
        """
        if self.__on_stop_measurement__ is not None:
            self.__on_stop_measurement__()
        for thread in self.__m_tasks__.values():
            thread.kill()
        for thread in self.__m_tasks__.values():
            thread.join()
        self.__toolbar__.start_stop_button.setToolTip("Start Measurement")
        self.__toolbar__.start_stop_button.setChecked(False)
        set_widget_icon(icon_name=Icons.PLAY.value, widget=self.__toolbar__.start_stop_button)
        
    
    def eventFilter(self, object: QObject, event: QEvent) -> bool: # type:ignore
        """Hide NavBar if user clicks outside it.
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
        if self.__on_startup__ is not None:
            self.__on_startup__()
        self.__start_background_tasks__()
        sys.exit(__qapp__.exec())
