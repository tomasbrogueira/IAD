import sys
import serial
import struct
import time
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QComboBox,
    QPushButton,
    QSizePolicy,
    QMainWindow,
    QApplication,
    QListWidget,
    QAbstractItemView,
    QLineEdit,
)
import pyqtgraph as pg
from pyqtgraph.exporters import CSVExporter
from PyQt5.QtCore import QTimer
from pyqt_switch import PyQtSwitch

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
        self.setGeometry(100, 100, 800, 500)    # set window size

        self.initUI()
        self.timer = QTimer()       # timer for data acquisition
        self.timer.timeout.connect(self.update_plot)    # update with new data

        self.timestep = 100  # Default acquisition time
        self.selected_pins = []  # List to store selected pins
        self.data = {}  # Dictionary to store data for each pin
        self.plot_curves = {}  # Dictionary for plot curves
        self.starting_time = None   # time for 1st measurements
        self.needsReset = True  # should labels be replotted
        self.conversionFactor = 1   # show in Volts or in bits
        self.persistence = False    # whether to limit samples poits to 100

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
        self.time_dropdown.addItems(["10", "20", "50", "100", "200", "500", "1000"])
        self.time_dropdown.setCurrentText("100")
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
        # Select the first item (A0)
        initial_item = self.pin_list.item(0)
        initial_item.setSelected(True)
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

        # bits or Volts switcher
        self.ADCswitch = PyQtSwitch()
        self.ADCswitch.toggled.connect(self.toogleUnit)
        self.ADClabel = QLabel()
        self.ADClabel.setText("Bits")
        button_layout.addWidget(self.ADCswitch)
        button_layout.addWidget(self.ADClabel)

        # temporary or persistent data switcher
        self.PersistencySwitch = PyQtSwitch()
        self.PersistencySwitch.toggled.connect(self.togglePersistence)
        self.PersistencyLabel = QLabel()
        self.PersistencyLabel.setText("Temporary Plot")
        button_layout.addWidget(self.PersistencySwitch)
        button_layout.addWidget(self.PersistencyLabel)

        # simple terminal window to input commands
        self.command_line = QLineEdit()  # TODO: ADD TEXT "ENTER COMMAND"
        self.command_line.setPlaceholderText("ENTER COMMAND")
        self.command_line.returnPressed.connect(self.send_command)
        button_layout.addWidget(self.command_line)

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
        """Returns a list of selected analog pins"""
        selected_items = self.pin_list.selectedItems()
        return [item.text() for item in selected_items]

    def set_acquisition_time(self, timestep=None):
        """Updates the acquisition time based on dropdown selection"""
        if not timestep:
            self.timestep = int(self.time_dropdown.currentText())
        else:
            self.timestep = timestep
        print(f"Acquisition time set to: {self.timestep} ms")
        self.timer.start(self.timestep)

    def togglePersistence(self, f):
        """Whether to store all data or to restrict to 100 samples"""
        if f:
            self.persistence = True
            self.PersistencyLabel.setText("Persistent Plot")
        else:
            self.persistence = False
            self.PersistencyLabel.setText("Temporary Plot")

    def send_command(self):
        """Manages the CLI of this script"""
        command = self.command_line.text()
        print(f"Command: {command}")

        if command == "start":
            self.start_button.click()
        elif command == "stop":
            self.stop_button.click()
        elif command == "reset":
            self.reset_button.click()
        elif command == "unit":
            self.ADCswitch.setChecked(not self.ADCswitch.isChecked())
        elif command.startswith("acqtime"): # usage: acqtime 100 -> set 100 ms
            try:
                timestep = int(command.split()[1])
                if timestep < 10:
                    print("Error: Acquisition time must be at least 10 ms")
                    return

                self.set_acquisition_time(timestep)  # Directly set any value
                if str(timestep) not in [
                    self.time_dropdown.itemText(i)
                    for i in range(self.time_dropdown.count())
                ]:
                    self.time_dropdown.addItem(str(timestep)) # add a custom timestep to the dropdown
                self.time_dropdown.setCurrentText(str(timestep))    # select it
            except (ValueError, IndexError):
                print("Error: Invalid time value. Usage: 'acqtime 150'")
                return

        elif command.startswith("pin"): # usage: pin A0 -> select pin A0
            try:
                pin = command.split()[1]
                if pin not in ["A0", "A1", "A2", "A3", "A4", "A5"]:
                    print("Error: Invalid pin number. Usage: 'pin A0'")
                    return

                if pin not in self.selected_pins:
                    self.pin_list.item(
                        [self.pin_list.item(i).text() for i in range(self.pin_list.count())].index(pin)
                    ).setSelected(True) # select pin in dropdown
                    self.selected_pins.append(pin)  # add pin to active list

            except IndexError:
                print("Error: Invalid pin number. Usage: 'pin A0'")
                return

        elif command.startswith("unpin"):   # usage: pin A0-> unselect pin A0
            try:
                pin = command.split()[1]
                if pin not in ["A0", "A1", "A2", "A3", "A4", "A5"]:
                    print("Error: Invalid pin number. Usage: 'unpin A0'")
                    return

                if pin in self.selected_pins:
                    self.pin_list.item(
                        [self.pin_list.item(i).text() for i in range(self.pin_list.count())].index(pin)
                    ).setSelected(False)    # unselect pin in dropdown

                    self.selected_pins.remove(pin)  # remove pin from active list
            except IndexError:
                print("Error: Invalid pin number. Usage: 'unpin A0'")
                return

        elif command.startswith("savecsv"): # usage: savecsv or savecsv filename.csv
            try:
                parts = command.split()
                filename = parts[1] if len(parts) > 1 else "data.csv"

                # Use PyQtGraph's CSV exporter
                exporter = CSVExporter(self.plot_widget.plotItem)
                exporter.export(filename)
                print(f"Plot data saved to {filename}")
            except Exception as e:
                print(f"Export error: {str(e)}")

        else:
            print("Command not recognized")
            return

        self.command_line.clear()

    def start_acquisition(self):
        """Starts data acquisition for multiple pins"""
        ser.reset_input_buffer()

        if len(self.get_selected_pins()) == 0:
            print("Error: No pins selected")
            return

        if ser:
            if self.needsReset:     # update labels if needed
                self.selected_pins = self.get_selected_pins()
                self.data = {
                    pin: [] for pin in self.selected_pins
                }  # Initialize data storage
                self.plot_curves = {}  # Clear old curves

                # Create a different color for each pin
                colors = ["r", "g", "b", "y", "m", "c"]

                for i, pin in enumerate(self.selected_pins):
                    self.plot_curves[pin] = self.plot_widget.plot(
                        pen=colors[i % len(colors)], name=pin
                    )
                self.needsReset = False

            # Send start signal for each pin
            for pin in self.selected_pins:
                pin_number = int(pin[1])  # Convert "A0" to 0, "A1" to 1, etc.
                ser.write(bytes([START_ACQUISITION, pin_number]))

            self.timer.start(self.timestep)

    def stop_acquisition(self):
        """Stops data acquisition"""
        self.timer.stop()
        ser.reset_input_buffer()

    def clear_plot(self):
        """Clears the plot"""
        self.data = {pin: [] for pin in self.selected_pins}
        self.plot_widget.clear()  # Remove all plot items, including curves and legend entries
        self.needsReset = True
        self.starting_time = None

    def update_plot(self):
        """Reads and plots data from multiple pins"""
        if ser:
            for i in range(len(self.selected_pins)):
                pin, value, timestamp = self.read_arduino_data()
                if self.starting_time is None:  # use 1st time as 0 seconds marker
                    self.starting_time = timestamp

                if pin in self.data:
                    self.data[pin].append(
                        (timestamp - self.starting_time, value * self.conversionFactor)
                    )

                    # Keep only the last 100 points, if not persistent
                    if len(self.data[pin]) > 100 and not self.persistence:
                        self.data[pin].pop(0)

                timestamps, values = zip(*self.data[pin])
                self.plot_curves[pin].setData(timestamps, values)

            for pin in self.selected_pins: # ask form more acquisition
                pin_number = int(pin[1])  # Convert "A0" to 0, "A1" to 1, etc.
                ser.write(bytes([START_ACQUISITION, pin_number]))

    def read_arduino_data(self):
        """Reads 12 bytes from Arduino and extracts timestamp, pin, and value"""
        expected_bytes = 8  # 2 int (2 bytes each) + 1 long
        data = ser.read(expected_bytes)

        if len(data) != expected_bytes:
            print("Error: Incomplete data received")
            return None, None, None

        value, pin_number, timestamp = struct.unpack("<hhI", data) # short+short+unsigned long
        pin = f"A{pin_number}"
        return pin, value, timestamp

    def toogleUnit(self, f):
        if f:
            self.conversionFactor = 5 / 1024    # volts conversion
            self.ADClabel.setText("Volts")

        else:
            self.conversionFactor = 1
            self.ADClabel.setText("Bits")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    mainWin = DataPlotter()
    mainWin.show()
    sys.exit(app.exec_())
