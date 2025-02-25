# include <Arduino.h>
// array of pins to use
int pins[6] = {A0, A1, A2, A3, A4, A5};
int pin = -1;
int sensorPin = 0; // variable to store the value coming from the sensor
unsigned long currentTime;

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
    // wait for a signal from the serial bus to acquire data
    if (Serial.available() >= 2) {
        action = (enum ActionCode)Serial.read();
    }
    if (action == START_ACQUISITION)
    {
        sensorPin = pins[pin = Serial.read()];
        int value = analogRead(sensorPin);
        currentTime = millis();
        Serial.write((uint8_t*)&value, sizeof(value));
        Serial.write((uint8_t*)&pin, sizeof(pin));
        Serial.write((uint8_t*)&currentTime, sizeof(currentTime));
    }
    action = STOP_ACQUISITION;
}
