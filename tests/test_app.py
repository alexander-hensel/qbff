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

from cgitb import text
import sys
import os
from turtle import update
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', )))
print(sys.path)

from PyQt6.QtWidgets import QPushButton, QApplication, QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt, pyqtSignal, QObject, QTimer
import bff.app
from bff.app.icons import Icons
from bff.app.types import Config
from PyQt6.QtGui import QPalette, QColor

from threading import Thread
import time

Config.app_name = "BFF Test App"

app = bff.app.instance


class TextUpdater(QObject):
    update_text = pyqtSignal(str)


button = QPushButton()
button.setText("button1")
button.setCheckable(True)
button2 = QPushButton()
button2.setText("Button2")
text = QLabel()
text.setText("Hello World")


updater = TextUpdater()
updater.update_text.connect(text.setText)


app.register_view(name=f"myView", widget=button, icon="coffee")
app.register_view(name=f"myView2", widget=button2, icon="coffee")
app.register_view(name=f"text", widget=text, icon="coffee")


@app.register_on_startup
def on_startup():
    print("Application started up")
    # app.show_view("myView")


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


@app.register_measurement_task
def measurement_task2():
    time.sleep(10)
    app.stop_measurement()


app.run()
# app.show()
# sys.exit(q.exec())
# 