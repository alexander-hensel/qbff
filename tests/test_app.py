"""
# PyQt6 Markdown Viewer 🚀

This **supports**:

- Headings
- Bold, italic, strikethrough
- Lists
- Inline links like [Python.org](https://www.python.org)
- Tables 🎉

## Example Table

| Name   | Age |
|--------|-----|
| Alice  | 30  |
| Bob    | 25  |
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', )))
print(sys.path)

from PyQt6.QtWidgets import QPushButton, QApplication
import bff.app
from bff.app.icons import Icons
from bff.app.config import Config

Config.app_name = "BFF Test App"

app = bff.app.BFF()

button = QPushButton()
button.setText("button1")
button.setCheckable(True)
# button.setFlat(True)
button2 = QPushButton()
button2.setText("Button2")

for x in range(100):
    app.register_view(name=f"myView_{x}", widget=button, icon="coffee")
    app.register_view(name=f"myView2_{x}", widget=button2, icon="coffee")

app.run()
# app.show()
# sys.exit(q.exec())
# 