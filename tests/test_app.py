import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', )))
print(sys.path)

from PyQt6.QtWidgets import QPushButton, QApplication

import bff.app
from bff.app.icons import Icons

# q = app = QApplication(sys.argv)

app = bff.app.BFF()

button = QPushButton()
button.setText("button1")
button.setCheckable(True)
# button.setFlat(True)
button2 = QPushButton()
button2.setText("Button2")


app.register_view(name="myView", widget=button, icon=Icons.HOME.value)
app.register_view(name="myView2", widget=button2, icon=Icons.PLAY.value)

app.run()
# app.show()
# sys.exit(q.exec())
# 