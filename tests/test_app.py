"""
# PyQt6 Markdown Viewer 🚀

This **supports**:

- Headings
- Bold, italic, **strikethrough**
- Lists
- Inline links like [Python.org](https://www.python.org)
- Tables 🎉

## Example Table

| Name   | Age |
|--------|-----|
| Alice  | 30  |
| Bob    | 25  |
"""

from math import fabs
import sys
import os
from turtle import update

import nidaqmx.constants
import nidaqmx.task
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', )))
print()
print(sys.path)
import dataclasses
from PyQt6.QtWidgets import QPushButton, QApplication, QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt, pyqtSignal, QObject, QTimer
from PyQt6.QtGui import QPalette, QColor
from threading import Thread
import time
from bff.app import Config, BFF, DefaultViews
from bff.app.icons import Icons
from bff.components.graph import GraphWidget
import nidaqmx

Config.app_name = "BFF Test Application"


@dataclasses.dataclass
class DI:
    GripperLeftUnlocked:bool = False
    GripperLeftLocked:bool = False
    GripperRightUnlocked:bool = False
    GripperRightLocked:bool = False
    GripperClosed:bool = False
    GripperOpen:bool = False
    HomeSwitchGripper:bool = False
    Reserve_7:bool = False
    AirPressure:bool = False
    OpenGripperSwitch = False
    EmergencyStop:bool = False
    Reserve_11:bool = False
    Reserve_12:bool = False
    Reserve_13:bool = False
    Reserve_14:bool = False
    Reserve_15:bool = False

    def from_array(self, values:list[bool]):
        fields: list[str] = [f.name for f in dataclasses.fields(self)]
        for name, value in zip(fields, values):
            setattr(self, name, value)


@dataclasses.dataclass
class DO:
    PCReady:bool = False
    LedGripperSwitch:bool = False
    Reserve_2:bool = False
    Reserve_3:bool = False
    Reserve_4:bool = False
    Reserve_5:bool = False
    Reserve_6:bool = False
    Reserve_7:bool = False
    LockGripperLeft:bool = False
    UnlockGripperLeft:bool = False
    LockGripperRight:bool = False
    UnlockGripperRight:bool = False
    OpenGripper:bool = False
    CloseGripper:bool = False
    Reserve_14:bool = False
    Reserve_15:bool = False

    def to_array(self) -> list[bool]:
        return [getattr(self, f.name) for f in dataclasses.fields(self)]
    
    def send(self) -> None:
        with nidaqmx.Task() as task:
            task.do_channels.add_do_chan("Dev2/port1/line0:3", line_grouping=nidaqmx.constants.LineGrouping.CHAN_PER_LINE)
            task.write(self.to_array()[:4])



app = BFF()
digital_inputs = DI()
digital_outputs = DO()


# @app.register_on_startup
def on_startup__():
    digital_outputs.PCReady = True
    digital_outputs.send()


# @app.register_background_task
def di_task():
    with nidaqmx.Task() as task:
        task.di_channels.add_di_chan("Dev2/port0/line0:7", line_grouping=nidaqmx.constants.LineGrouping.CHAN_PER_LINE)
        while True:
            values : list[bool] = task.read()  #type: ignore
            digital_inputs.from_array(values)
            time.sleep(0.1)



class TextUpdater(QObject):
    update_text = pyqtSignal(str)


button = QPushButton()
button.setText("button1")
button.setCheckable(True)
button2 = QPushButton()
button2.setText("Button2")
text = QLabel()
text.setText("Hello World")

gr = GraphWidget()


updater = TextUpdater()
updater.update_text.connect(text.setText)


def view_changed(name: str) -> None:
    print(f"View changed to: {name}")

app.window.register_view(name=f"myView", widget=button, icon="coffee")
app.window.register_view(name=f"myView2", widget=button2, icon="coffee")
app.window.register_view(name=f"text", widget=text, icon="coffee", on_show=view_changed)
# app.register_view(name=f"TheGraph", widget=gr, icon="coffee", on_show=view_changed)

@app.register_on_startup
def on_startup():
    print("Starting up")


@app.register_on_shutdown
def on_shutdown():
    print("Shutting down")


@app.register_on_start_measurement
def start_measurement():
    print("Measurement started")


@app.register_on_stop_measurement
def stop_measurement():
    print("Measurement stopped")


@app.register_background_task
def task() -> None:
    while True:
        updater.update_text.emit(f"Hello Background {time.time()}")
        time.sleep(0.1)


@app.register_measurement_task
def measurement_task():
    while True:
        updater.update_text.emit(f"Hello Measurement Task {time.time()}")
        time.sleep(0.1)



# @app.register_measurement_task
# def say_hello():
#     while True:
#         print(f"hello: {time.time()}")
#         time.sleep(0.01)


@app.register_measurement_task
def measurement_task2():
    print("Measurement Task 2 started"  )
    time.sleep(5)
    app.window.show_view(DefaultViews.HOME.value)
    Thread(target=app.stop_measurement, daemon=True).start()
    

app.run()
 