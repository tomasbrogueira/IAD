import sys
import numpy as np
import pyqtgraph as pg
import serial
import struct
import time
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QPushButton, QWidget, QLabel, QComboBox
from PyQt5.QtCore import QTimer

# Serial Port Configuration (Update this to match your Arduino's port)
SERIAL_PORT = "/dev/ttyACM0"  # Change for Windows (e.g., "COM3")
BAUD_RATE = 9600

# Action codes (must match those in the Arduino code)
STOP_ACQUISITION = 1
START_ACQUISITION = 2
ACQUIRING_DATA = 3
SET_TIMESTEP = 4

# Attempt to connect to the Arduino
try:
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
    time.sleep(2)  # Allow time for Arduino to reset
except serial.SerialException:
    print("Error: Could not open serial port.")
    ser = None

class DataPlotter(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Arduino Data Plotter")
        self.setGeometry(100, 100, 800, 500)

        self.initUI()
        self.data = []
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_plot)

        self.current_pin = 0

    def initUI(self):
        # Create central widget and layout
        central_widget = QWidget()
        layout = QVBoxLayout()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

        # Dropdown for acquisition time
        self.time_label = QLabel("Select Acquisition Time (ms):")
        layout.addWidget(self.time_label)

        self.time_dropdown = QComboBox()
        self.time_dropdown.addItems(["100", "200", "500", "1000"])  # Options in milliseconds
        self.time_dropdown.currentIndexChanged.connect(self.set_acquisition_time)
        layout.addWidget(self.time_dropdown)

        # Dropdown for pin selection
        self.pin_label = QLabel("Select Analog Pin:")
        layout.addWidget(self.pin_label)

        self.pin_dropdown = QComboBox()
        self.pin_dropdown.addItems(["A0", "A1", "A2", "A3", "A4", "A5"])
        self.pin_dropdown.currentIndexChanged.connect(self.set_acquisition_pin)
        layout.addWidget(self.pin_dropdown)

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

    def set_acquisition_pin(self):
        # Update the current pin
        self.current_pin = self.pin_dropdown.currentIndex()
        print(f"Setting acquisition pin: {self.current_pin}")

    def set_acquisition_time(self):
        """ Send the selected acquisition time to the Arduino """
        if ser:
            timestep = int(int(self.time_dropdown.currentText()) / 100) # Get selected time in ms
            print(f"Setting acquisition time: {timestep} ms")
            ser.write(bytes([SET_TIMESTEP, timestep]))  # Send command

    def start_acquisition(self):
        if ser:
            ser.write(bytes([START_ACQUISITION, self.current_pin]))  # Start data acquisition on A0
            self.timer.start(100)  # Update every 100 ms

    def stop_acquisition(self):
        if ser:
            ser.write(bytes([STOP_ACQUISITION]))  # Stop data acquisition
        self.timer.stop()

    def clear_plot(self):
        self.data = []
        self.plot_curve.setData([])

    def update_plot(self):
        if ser:
            new_value = self.read_arduino_data()[1]
            if new_value is not None:
                self.data.append(new_value)

                if len(self.data) > 100:
                    self.data.pop(0)  # Keep only the last 100 points

                self.plot_curve.setData(self.data)

    def read_arduino_data(self):
        """ Reads 12 bytes from Arduino and extracts slope, intercept, and uncertainty. """
        expected_bytes = 12 # 3 int * 4 bytes 
        data = ser.read(expected_bytes)

        if len(data) != expected_bytes:
            print("Error: Incomplete data received")
            return None

        # Unpack binary data into three little-endian floats
        value, pin, time = struct.unpack("<iii", data)
        return time, value, pin

if __name__ == "__main__":
    app = QApplication(sys.argv)
    mainWin = DataPlotter()
    mainWin.show()
    sys.exit(app.exec_())
