#include <Wire.h>

    int GSRPin = 1;
    int threshold=0;
    int Signal;

    void setup(){
      Serial.begin(9600);
      }

    void loop(){
      Signal = analogRead(GSRPin);
      Serial.println(Signal);
      }
