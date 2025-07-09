from PyQt6.QtWidgets import (    
    QWidget,
    QLabel,
    QVBoxLayout,
    QSpacerItem,
    QSizePolicy,
)
from PyQt6.QtCore import Qt

from bff.app import DefaultViews


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