import sys
import numpy as np
from PyQt6.QtWidgets import QApplication, QMainWindow
import pyqtgraph as pg


class DualAxisPlot(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Dual Y-Axis Plot")

        # Main plot widget
        self.plot_widget = pg.PlotWidget()
        self.setCentralWidget(self.plot_widget)

        # Create the first (left) plot
        self.left_plot = self.plot_widget.getPlotItem()
        self.left_plot.showGrid(x=True, y=True)
        self.left_plot.setLabel("left", "Left Y-Axis")
        self.left_plot.setLabel("bottom", "X-Axis")

        # Create the second ViewBox for right Y-axis
        self.right_view = pg.ViewBox()
        self.plot_widget.scene().addItem(self.right_view)

        # Link X-axis of right_view to left_plot
        self.right_view.setXLink(self.left_plot)

        # Add second Y-axis to the right
        self.right_axis = pg.AxisItem('right')
        self.left_plot.layout.addItem(self.right_axis, 2, 2)
        self.right_axis.linkToView(self.right_view)
        self.right_axis.setLabel("Right Y-Axis")

        # Update right_view when left_view changes
        self.left_plot.vb.sigResized.connect(self.update_right_view)

        # Plot data
        self.plot_data()

    def update_right_view(self):
        self.right_view.setGeometry(self.left_plot.vb.sceneBoundingRect())
        self.right_view.linkedViewChanged(self.left_plot.vb, self.right_view.XAxis)

    def plot_data(self):
        x = np.linspace(0, 10, 1000)
        y1 = np.sin(x) * 10           # Left plot data
        y2 = np.exp(-x / 3) * 100     # Right plot data

        # Plot on left Y-axis
        left_curve = self.left_plot.plot(x, y1, pen=pg.mkPen('b', width=2), name="Left Data")

        # Plot on right Y-axis
        right_curve = pg.PlotCurveItem(x, y2, pen=pg.mkPen('r', width=2), name="Right Data")
        self.right_view.addItem(right_curve)

        # Auto-range both views
        self.left_plot.enableAutoRange(axis=pg.ViewBox.YAxis)
        self.right_view.enableAutoRange(axis=pg.ViewBox.YAxis)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = DualAxisPlot()
    win.show()
    sys.exit(app.exec())
