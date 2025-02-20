import sys
import numpy as np
import pyqtgraph as pg
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QPushButton, QWidget
from PyQt5.QtCore import QTimer

class DataPlotter(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Arduino Data Plotter")
        self.setGeometry(100, 100, 800, 500)

        self.initUI()
        self.data = []
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_plot)

    def initUI(self):
        # Create central widget and layout
        central_widget = QWidget()
        layout = QVBoxLayout()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

        # Start and Stop buttons
        self.start_button = QPushButton("Start")
        self.start_button.clicked.connect(self.start_acquisition)
        layout.addWidget(self.start_button)

        self.stop_button = QPushButton("Stop")
        self.stop_button.clicked.connect(self.stop_acquisition)
        layout.addWidget(self.stop_button)

        # Reset button
        self.reset_button = QPushButton("Reset")
        self.reset_button.clicked.connect(self.clear_plot)
        layout.addWidget(self.reset_button)

        # Create plot widget
        self.plot_widget = pg.PlotWidget()
        layout.addWidget(self.plot_widget)

        self.plot_curve = self.plot_widget.plot(pen="y")

    def start_acquisition(self):
        self.timer.start(100)  # Update every 100 ms

    def stop_acquisition(self):
        self.timer.stop()

    def clear_plot(self):
        self.data = []
        self.plot_curve.setData([])

    def update_plot(self):
        # Simulated data (replace this with actual Arduino data)
        new_value = np.random.normal()
        self.data.append(new_value)
        
        if len(self.data) > 100:
            self.data.pop(0)  # Keep only the last 100 points

        self.plot_curve.setData(self.data)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    mainWin = DataPlotter()
    mainWin.show()
    sys.exit(app.exec_())
