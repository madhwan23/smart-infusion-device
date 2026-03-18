#include <Servo.h>

Servo motor;

int sensorPin = 2;
int servoPin = 9;

void setup() {
  pinMode(sensorPin, INPUT);
  motor.attach(servoPin);
  motor.write(0);

  Serial.begin(9600);
}

void loop() {
  int sensorValue = digitalRead(sensorPin);

  if (sensorValue == LOW) {
    Serial.println("Bottle Empty - Replacing");

    motor.write(90);
    delay(2000);

    motor.write(0);
    delay(2000);
  }

  delay(500);
}
