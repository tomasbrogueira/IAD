# include <Arduino.h>

// array of pins to use
int pins[6] = {A0, A1, A2, A3, A4, A5};
int sensorPin = 0; // variable to store the value coming from the sensor
int timestep = 1000;

enum ActionCode {
    STOP_ACQUISITION = 1,
    START_ACQUISITION = 2,
    ACQUIRING_DATA = 3,
    SET_TIMESTEP = 4
} action;

typedef struct 
{
    float slope;
    float intercept;
    float uncertainty;
} arduinoData;


void setup() {
  // initialize serial communication at 9600 bits per second:
  Serial.begin(9600);
  // initialize the digital pins as an output:
  for (int i = 0; i < 6; i++) {
    pinMode(pins[i], INPUT);
  }
}

void loop() {
    // wait for a signal from the serial bus to acquire data
    if (Serial.available() > 0) {
        action = (enum ActionCode)Serial.read();
        
    }
    if (action == START_ACQUISITION)
    {
        sensorPin = pins[Serial.read()];
        action = ACQUIRING_DATA;
    }
    
    if (action == ACQUIRING_DATA) {
        acquireData();
    }
    if (action == SET_TIMESTEP)
    {
        timestep = Serial.parseInt();
        action = ACQUIRING_DATA;
    }
  
}

void acquireData() {
    int sensorValue[128];
    for (int i = 0; i < 128; i++) {
        sensorValue[i] = analogRead(sensorPin);
        delay(timestep/128);
    }
    arduinoData results = linearRegression(sensorValue);
    Serial.write((uint8_t*)&results, sizeof(results));
}

arduinoData linearRegression (int* sensorValue) {
    float sumX = 0, sumY = 0, sumXY = 0, sumX2 = 0;
    for (int i = 0; i < 128; i++) {
        sumX += i;
        sumY += sensorValue[i];
        sumXY += i * sensorValue[i];
        sumX2 += i * i;
    }

    float slope = (128 * sumXY - sumX * sumY) / (128 * sumX2 - sumX * sumX);
    float intercept = (sumY - slope * sumX) / 128;

    // Calculate uncertainty (standard error of the estimate)
    float sumError = 0;
    for (int i = 0; i < 128; i++) {
        float predictedY = slope * i + intercept;
        sumError += (sensorValue[i] - predictedY) * (sensorValue[i] - predictedY);
    }
    float uncertainty = sqrt(sumError / (128 - 2));

    arduinoData results = {slope, intercept, uncertainty};
    return results;
}