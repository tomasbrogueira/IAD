import serial
import struct
import time

# Configuration: Update this to match your Arduino's serial port.
SERIAL_PORT = '/dev/ttyACM0'
BAUD_RATE = 9600

# Action codes (must match those in the Arduino code)
STOP_ACQUISITION = 1
START_ACQUISITION = 2
ACQUIRING_DATA   = 3
SET_TIMESTEP     = 4

# Initialize serial connection
ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
time.sleep(2)  # Allow time for Arduino to reset

def start_acquisition(pin_index):
    """
    Send the START_ACQUISITION command followed by a pin index.
    The Arduino expects the first byte to be the action code (2)
    and the next byte is used to index its array of analog pins.
    """
    # Send action code and then the pin index (e.g., 0 for A0)
    ser.write(bytes([START_ACQUISITION, pin_index]))
    time.sleep(0.1)  # Short delay to allow Arduino processing

def set_timestep(new_timestep):
    """
    Send the SET_TIMESTEP command.
    The Arduino will call parseInt() so we send the new timestep as an ASCII string.
    """
    ser.write(bytes([SET_TIMESTEP]))
    # Send the integer as string followed by a newline (which parseInt will use as a terminator)
    ser.write(f"{new_timestep}\n".encode('ascii'))
    time.sleep(0.1)

def read_arduino_data():
    """
    Read 12 bytes from the Arduino representing three floats:
    slope, intercept, and uncertainty.
    """
    expected_bytes = 12  # 3 floats * 4 bytes each
    data = ser.read(expected_bytes)
    if len(data) != expected_bytes:
        print("Error: Incomplete data received")
        return None

    # Unpack binary data into three little-endian floats
    slope, intercept, uncertainty = struct.unpack('<fff', data)
    return slope, intercept, uncertainty

def main():
    # Example: Start acquisition on analog pin A0 (index 0)
    start_acquisition(0)
    
    # Optionally, you can change the timestep by calling:
    # set_timestep(1000)

    # Wait sufficient time for the Arduino to acquire and process data
    time.sleep(2)

    # Read and display the results from the Arduino
    result = read_arduino_data()
    if result:
        slope, intercept, uncertainty = result
        print(f"Slope: {slope:.2f}")
        print(f"Intercept: {intercept:.2f}")
        print(f"Uncertainty: {uncertainty:.2f}")

if __name__ == "__main__":
    main()
