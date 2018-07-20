void setup() {
  Serial.begin(9600);
}

void loop() {
  int sensorValue = analogRead(A2);
  Serial.println(sensorValue);
  delay(1);        // delay in between reads for stability
}
