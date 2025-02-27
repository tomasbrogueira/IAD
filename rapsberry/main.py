import sys
import serial
import struct
import time
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QPushButton, QSizePolicy, QMainWindow, QApplication, QListWidget, QAbstractItemView
)
import pyqtgraph as pg
from PyQt5.QtCore import QTimer

# Serial Port Configuration (Update as needed)
SERIAL_PORT = "/dev/ttyACM0"  # Change for Windows (e.g., "COM3")
BAUD_RATE = 9600

# Action codes (must match those in Arduino)
STOP_ACQUISITION = 1
START_ACQUISITION = 2

# Attempt to connect to Arduino
try:
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
    time.sleep(2)  # Allow time for Arduino to reset
except serial.SerialException:
    print("Error: Could not open serial port.")
    ser = None

class DataPlotter(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Arduino Multi-Pin Data Plotter")
        self.setGeometry(100, 100, 800, 500)

        self.initUI()
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_plot)

        self.timestep = 100  # Default acquisition time
        self.selected_pins = []  # List to store selected pins
        self.data = {}  # Dictionary to store data for each pin
        self.plot_curves = {}  # Dictionary for plot curves
        self.starting_time = None

    def initUI(self):
        # Create central widget and layout
        central_widget = QWidget()
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

        # Create horizontal layout for dropdowns
        dropdown_layout = QVBoxLayout()
        dropdown_widget = QWidget()
        dropdown_widget.setLayout(dropdown_layout)
        dropdown_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        # Dropdown for acquisition time
        self.time_label = QLabel("Select Acquisition Time (ms):")
        dropdown_layout.addWidget(self.time_label)

        self.time_dropdown = QComboBox()
        self.time_dropdown.addItems(["100", "200", "500", "1000"])
        self.time_dropdown.currentIndexChanged.connect(self.set_acquisition_time)
        self.time_dropdown.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        dropdown_layout.addWidget(self.time_dropdown)

        # Multi-selection list for pin selection
        self.pin_label = QLabel("Select Analog Pins:")
        dropdown_layout.addWidget(self.pin_label)

        self.pin_list = QListWidget()
        self.pin_list.addItems(["A0", "A1", "A2", "A3", "A4", "A5"])
        self.pin_list.setSelectionMode(QAbstractItemView.MultiSelection)
        self.pin_list.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        dropdown_layout.addWidget(self.pin_list)

        # Create horizontal layout for buttons
        button_layout = QVBoxLayout()
        button_widget = QWidget()
        button_widget.setLayout(button_layout)
        button_widget.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)

        # Start and Stop buttons
        self.start_button = QPushButton("Start")
        self.start_button.clicked.connect(self.start_acquisition)
        button_layout.addWidget(self.start_button)

        self.stop_button = QPushButton("Stop")
        self.stop_button.clicked.connect(self.stop_acquisition)
        button_layout.addWidget(self.stop_button)

        # Reset button
        self.reset_button = QPushButton("Reset")
        self.reset_button.clicked.connect(self.clear_plot)
        button_layout.addWidget(self.reset_button)

        # Create horizontal layout for dropdowns and buttons
        top_layout = QHBoxLayout()
        top_layout.addWidget(dropdown_widget, 2)
        top_layout.addWidget(button_widget, 1)
        main_layout.addLayout(top_layout)

        # Create plot widget
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.addLegend()
        main_layout.addWidget(self.plot_widget)

    def get_selected_pins(self):
        """ Returns a list of selected analog pins """
        selected_items = self.pin_list.selectedItems()
        return [item.text() for item in selected_items]

    def set_acquisition_time(self):
        """ Updates the acquisition time based on dropdown selection """
        self.timestep = int(self.time_dropdown.currentText())
        print(f"Acquisition time set to: {self.timestep} ms")

    def start_acquisition(self):
        """ Starts data acquisition for multiple pins """
        if ser:
            self.selected_pins = self.get_selected_pins()
            self.data = {pin: [] for pin in self.selected_pins}  # Initialize data storage
            self.plot_curves = {}  # Clear old curves

            # Create a different color for each pin
            colors = ['r', 'g', 'b', 'y', 'm', 'c']  
            
            for i, pin in enumerate(self.selected_pins):
                self.plot_curves[pin] = self.plot_widget.plot(
                    pen=colors[i % len(colors)], name=pin
                )

            # Send start signal for each pin
            for pin in self.selected_pins:
                pin_number = int(pin[1])  # Convert "A0" to 0, "A1" to 1, etc.
                ser.write(bytes([START_ACQUISITION, pin_number]))

            self.timer.start(self.timestep)

    def stop_acquisition(self):
        """ Stops data acquisition """
        self.timer.stop()
        if ser:
            ser.write(bytes([STOP_ACQUISITION]))

    def clear_plot(self):
        """ Clears the plot """
        self.data = {pin: [] for pin in self.selected_pins}
        for curve in self.plot_curves.values():
            curve.setData([])

    def update_plot(self):
        """ Reads and plots data from multiple pins """
        if ser:
            pin, value, timestamp = self.read_arduino_data()

            if pin in self.data:
                self.data[pin].append(value)

                # Keep only the last 100 points
                if len(self.data[pin]) > 100:
                    self.data[pin].pop(0)

                self.plot_curves[pin].setData(self.data[pin])

    def read_arduino_data(self):
        """ Reads 12 bytes from Arduino and extracts timestamp, pin, and value """
        expected_bytes = 8  # 2 int (2 bytes each) + 1 long
        data = ser.read(expected_bytes)

        if len(data) != expected_bytes:
            print("Error: Incomplete data received")
            return None, None, None

        value, pin_number, timestamp = struct.unpack("<iiI", data)
        pin = f"A{pin_number}"
        return pin, value, timestamp

if __name__ == "__main__":
    app = QApplication(sys.argv)
    mainWin = DataPlotter()
    mainWin.show()
    sys.exit(app.exec_())
