# from PyQt6 import QtCore, QtWidgets
from PyQt6.QtWidgets import QPushButton, QApplication, QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt, pyqtSignal, QObject, QTimer
from PyQt6.QtGui import QPalette, QColor
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qtagg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
import numpy as np



class MplCanvas(FigureCanvas):

    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure((width,height), dpi=dpi)
        self.axes = fig.add_subplot(111)
        super().__init__(fig)


class GraphWidget(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.canvas = MplCanvas(self, width=5, height=4, dpi=100)
        toolbar = NavigationToolbar(self.canvas, self)
        self.layout:QVBoxLayout = QVBoxLayout(self)
        self.layout.addWidget(toolbar)
        self.layout.addWidget(self.canvas)
        self.setLayout(self.layout)
        self.canvas.axes.set_title('Sample Graph')
        self.canvas.axes.set_xlabel('X-axis')
        self.canvas.axes.set_ylabel('Y-axis')
        self.canvas.axes.grid(True)
        x = np.linspace(0, 10_000, 10_000)
        y = np.sin(x)
        self.plot_data(x, y)

    def plot_data(self, x_data, y_data):
        # self.canvas.axes.clear()
        self.canvas.axes.plot(x_data, y_data)
        # self.canvas.axes.set_title('Sample Graph')
        # self.canvas.axes.set_xlabel('X-axis')
        # self.canvas.axes.set_ylabel('Y-axis')
        # self.canvas.axes.grid(True)
        self.canvas.draw()