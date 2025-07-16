import sys
import numpy as np
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QPushButton,
    QCheckBox, QLabel, QWidget
)
import pyqtgraph as pg
from pyqtgraph.Qt import QtCore


pg.setConfigOptions(useOpenGL=True, antialias=True, background='k', foreground='w')


class Oscilloscope(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🚀 PyQt6 GPU Oscilloscope with Downsampling")
        self.resize(1000, 600)

        # Main widget and layout
        centralWidget = QWidget()
        self.setCentralWidget(centralWidget)
        layout = QVBoxLayout()
        centralWidget.setLayout(layout)

        # Plot widget
        self.plotWidget = pg.PlotWidget(title="Oscilloscope View")
        self.plotWidget.showGrid(x=True, y=True)
        self.plotWidget.setLabel('left', 'Amplitude', units='V')
        self.plotWidget.setLabel('bottom', 'Time', units='s')
        layout.addWidget(self.plotWidget)

        # Channels
        self.channels_enabled = [True, True, True, True]
        colors = ['y', 'c', 'm', 'g']
        self.curves = []
        self.buffers = []
        self.bufferSize = 2_000_000  # 5 million samples
        self.chunkSize = 1000      # New points per update
        self.sample_rate = 100_000       # 1 MHz
        self.timebase = np.linspace(-self.bufferSize / self.sample_rate, 0, self.bufferSize)

        for i, color in enumerate(colors):
            curve = self.plotWidget.plot(pen=pg.mkPen(color=color, width=1))
            curve.setDownsampling("peak")
            curve.setClipToView(True)
            curve.setSkipFiniteCheck(True)
            self.curves.append(curve)
            self.buffers.append(np.zeros(self.bufferSize))

        # Trigger settings
        self.trigger_level = 0.0
        self.trigger_channel = 0
        self.trigger_edge = 'rising'  # or 'falling'

        # Control panel
        controlLayout = QHBoxLayout()
        layout.addLayout(controlLayout)

        self.startButton = QPushButton("Start")
        self.startButton.setCheckable(True)
        self.startButton.clicked.connect(self.toggle_running)
        controlLayout.addWidget(self.startButton)

        self.triggerLabel = QLabel(f"Trigger: CH{self.trigger_channel+1} @ {self.trigger_level:.2f}V ({self.trigger_edge})")
        controlLayout.addWidget(self.triggerLabel)

        # Channel checkboxes
        for i in range(4):
            cb = QCheckBox(f"CH{i+1}")
            cb.setChecked(True)
            cb.stateChanged.connect(lambda state, ch=i: self.toggle_channel(ch, state))
            controlLayout.addWidget(cb)

        controlLayout.addStretch()

        # Timer for updates
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update_plot)
        self.running = False

    def toggle_running(self, checked):
        if checked:
            self.startButton.setText("Stop")
            self.running = True
            self.timer.start(1)  # 100 Hz updates
        else:
            self.startButton.setText("Start")
            self.running = False
            self.timer.stop()

    def toggle_channel(self, ch, state):
        self.channels_enabled[ch] = bool(state)

    def find_trigger(self, signal):
        # Find trigger point (simple rising/falling edge)
        if self.trigger_edge == 'rising':
            crossings = np.where((signal[:-1] < self.trigger_level) & (signal[1:] >= self.trigger_level))[0]
        else:
            crossings = np.where((signal[:-1] > self.trigger_level) & (signal[1:] <= self.trigger_level))[0]

        return crossings[0] if len(crossings) else 0

    def min_max_downsample(self, data, target_points):
        """Preserve spikes for oscilloscope look."""
        factor = len(data) // target_points
        if factor < 2:
            return data  # No downsampling needed
        reshaped = data[:factor * target_points].reshape(-1, factor)
        mins = reshaped.min(axis=1)
        maxs = reshaped.max(axis=1)
        interleaved = np.empty(mins.size + maxs.size, dtype=mins.dtype)
        interleaved[0::2] = mins
        interleaved[1::2] = maxs
        return interleaved

    def update_plot(self):
        # Simulate data streaming
        t = np.arange(self.chunkSize) / self.sample_rate
        for i in range(4):
            new_data = np.sin(2 * np.pi * (5 + i*2) * t + np.random.uniform(0, np.pi)) \
                       + np.random.normal(0, 0.1, size=self.chunkSize)
            self.buffers[i] = np.roll(self.buffers[i], -self.chunkSize)
            self.buffers[i][-self.chunkSize:] = new_data

        # Trigger on selected channel
        trig_idx = self.find_trigger(self.buffers[self.trigger_channel])
        window_start = trig_idx
        window_end = trig_idx + self.bufferSize
        if window_end > len(self.buffers[0]):
            window_end = len(self.buffers[0])
            window_start = window_end - self.bufferSize

        # Update curves with downsampling
        view_width = self.plotWidget.getViewBox().width()
        target_points = int(view_width) if view_width > 0 else 2000  # Approximate display width
        for i, curve in enumerate(self.curves):
            if self.channels_enabled[i]:
                y_data = self.buffers[i][window_start:window_end]
                y_ds = self.min_max_downsample(y_data, target_points)
                x_ds = np.linspace(self.timebase[0], self.timebase[-1], len(y_ds))
                curve.setData(x_ds, y_ds)
            else:
                curve.clear()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    scope = Oscilloscope()
    scope.show()
    sys.exit(app.exec())
