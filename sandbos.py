# import pyqtgraph.examples
# pyqtgraph.examples.run()

"""
Demonstrates use of PlotWidget class. This is little more than a 
GraphicsView with a PlotItem placed in its center.
"""

import numpy as np

import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtWidgets

# pg.useOpenGL = False  # Use OpenGL for better performance if available

app = pg.mkQApp()
mw = QtWidgets.QMainWindow()
mw.setWindowTitle('pyqtgraph example: PlotWidget')
mw.resize(800,800)
cw = QtWidgets.QWidget()
mw.setCentralWidget(cw)
l = QtWidgets.QVBoxLayout()
cw.setLayout(l)

pw = pg.PlotWidget(name='Plot1')  ## giving the plots names allows us to link their axes together
l.addWidget(pw)
pw2 = pg.PlotWidget(name='Plot2')
l.addWidget(pw2)
pw3 = pg.PlotWidget()
l.addWidget(pw3)

mw.show()

## Create an empty plot curve to be filled later, set its pen
p1 = pw.plot()

data1 = pg.PlotDataItem([])
data2 = pg.PlotDataItem([])
data1.setPen(pg.mkPen("#0080c0"))
data2.setPen(pg.mkPen("#c000b6"))
pw.addItem(data1)
pw.addItem(data2)
# p1.setPen((200,200,100))
# p42 = pw.plot(pen=(100, 200, 100), name='Plot42')




## Add in some extra graphics
rect = QtWidgets.QGraphicsRectItem(QtCore.QRectF(0, 0, 1, 5e-11))
# rect.setPen(pg.mkPen(100, 200, 100))
# pw.addItem(rect)

# pw.setLabel('left', 'Value', units='V')
# pw.setLabel('right', 'Value2', units='A')

# pw.setLabel('bottom', 'Time', units='s')
# pw.setXRange(0, 200)
# pw.setYRange(0, 1e-10)

def rand(n):
    data = np.random.random(n)
    data[int(n*0.1):int(n*0.13)] += .5
    data[int(n*0.18)] += 2
    data[int(n*0.1):int(n*0.13)] *= 5
    data[int(n*0.18)] *= 20
    data *= 1e-12
    return data, np.arange(n, n+len(data)) / float(n)
    

def updateData():
    # yd, xd = rand(1000_000)
    xd = np.linspace(0, 100, 100_000)
    yd = np.sin(xd) + np.random.normal(size=xd.shape) * 2
    p1.setData(y=yd, x=xd)
    yd2 = np.cos(xd) + np.random.normal(size=xd.shape) * 0.1
    # p42.setData(y=yd2, x=xd)
    # data2.setData((yd))
    data1.setData(yd2)

## Start a timer to rapidly update the plot in pw
t = QtCore.QTimer()
t.timeout.connect(updateData)
t.start(50)
#updateData()

## Multiple parameterized plots--we can autogenerate averages for these.
for i in range(0, 5):
    for j in range(0, 3):
        yd, xd = rand(10000)
        pw2.plot(y=yd*(j+1), x=xd, params={'iter': i, 'val': j})

## Test large numbers
curve = pw3.plot(np.random.normal(size=10000)*1e0, clickable=True)
curve.curve.setClickable(True)
curve.setPen('w')  ## white pen
curve.setShadowPen(pg.mkPen((70,70,30), width=6, cosmetic=True))

def clicked():
    print("curve clicked")
curve.sigClicked.connect(clicked)

lr = pg.LinearRegionItem([1, 30], bounds=[0,100], movable=True)
pw3.addItem(lr)
line = pg.InfiniteLine(angle=90, movable=True)
pw3.addItem(line)
line.setBounds([0,200])

if __name__ == '__main__':
    pg.exec()