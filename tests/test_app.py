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

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', )))
print(sys.path)

from PyQt6.QtWidgets import QPushButton, QApplication, QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt
import bff.app
from bff.app.icons import Icons
from bff.app.types import Config
from PyQt6.QtGui import QPalette, QColor

from threading import Thread
import time

Config.app_name = "BFF Test App"

app = bff.app.BFF()


button = QPushButton()
button.setText("button1")
button.setCheckable(True)
# button.setFlat(True)
button2 = QPushButton()
button2.setText("Button2")
text = QLabel()
text.setText("Hello World")


app.register_view(name=f"myView", widget=button, icon="coffee")
app.register_view(name=f"myView2", widget=button2, icon="coffee")
app.register_view(name=f"text", widget=text, icon="coffee")


@app.register_on_startup
def on_startup():
    print("Application started up")
    # app.show_view("myView")


@app.register_on_start_measurement
def start_measurement():
    print("Measurement started")

@app.register_on_stop_measurement
def stop_measurement():
    print("Measurement stopped")

@app.register_background_task
def task() -> None:
    while True:
        print(f"task running: {time.time()}")
        # time.sleep(0.0002)

@app.register_measurement_task
def second_task():
    while True:
        print(f"measurement task is also runnig {time.time()}")
        text.setText(f"Hello World {time.time()}")
        time.sleep(0.0002)

app.run()
# app.show()
# sys.exit(q.exec())
# 