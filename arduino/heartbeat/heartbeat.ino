# include <Arduino.h>
// array of pins to use
int pins[6] = {A0, A1, A2, A3, A4, A5};
// value from 0 to 5 sent by the RPi controler
int pin = -1;
// Actual pin used for aquisition: A0 -> A5
int sensorPin = 0;
// Time of measurement
unsigned long currentTime;

// Possible codes sent by RPi
enum ActionCode {
    STOP_ACQUISITION = 1,
    START_ACQUISITION = 2,
} action;

void setup() {
  // initialize serial communication at 9600 bits per second:
  Serial.begin(9600);
  // initialize the digital pins as an INPUT:
  for (int i = 0; i < 6; i++) {
    pinMode(pins[i], INPUT);
  }
}

void loop() {
    // wait for a signal from the serial bus to acquire data: code + value
    if (Serial.available() >= 2) {
        action = (enum ActionCode)Serial.read();
    }
    if (action == START_ACQUISITION)
    {
        sensorPin = pins[pin = Serial.read()];
        int value = analogRead(sensorPin);
        currentTime = millis();
        Serial.write((uint8_t*)&value, sizeof(value));  // send value (2 byte)
        Serial.write((uint8_t*)&pin, sizeof(pin));      // send aquisition pin (2 byte)
        Serial.write((uint8_t*)&currentTime, sizeof(currentTime));  // send time of aquisition (4 byte)
    }
    action = STOP_ACQUISITION;
}
