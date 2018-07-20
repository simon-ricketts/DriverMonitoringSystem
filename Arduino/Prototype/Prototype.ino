#include <SoftwareSerial.h>
SoftwareSerial BTSerial(2, 3); // RX | TX
bool samePulse = false;
bool firstPulse = false;
float bpm = 0;
unsigned long firstPulseTime;
unsigned long secondPulseTime;
unsigned long pulseInterval;

void setup() {
      BTSerial.begin(9600);  
}

void loop() {
      analogReference(INTERNAL);
      int tempSignal = accurateAnalogRead(0);
      BTSerial.print("Temperature:");
      BTSerial.println(tempSignal / 9.31);
      analogReference(DEFAULT);
      int GSRSignal = accurateAnalogRead(1);
      BTSerial.print("GSR:");
      BTSerial.println(GSRSignal);
      int muscleSignal = accurateAnalogRead(2);
      BTSerial.print("Muscle Tenseness:");
      BTSerial.println(muscleSignal);
      int pulseSignal = accurateAnalogRead(3);
      BTSerial.print("Pulse Signal:");
      BTSerial.println(pulseSignal);
      BTSerial.print("BPM:");
      BTSerial.println(calculateBPM(pulseSignal));
      
}

int accurateAnalogRead(int pin) {
  int sensorData = analogRead(pin);
  delay(7);
  sensorData = analogRead(pin);
  delay(7);
  return sensorData;
}

float calculateBPM(int pulse) {
  if(pulse > 600 and samePulse == false){
    if(firstPulse == false){
      firstPulseTime = millis();
      firstPulse = true;
    }
    else{
      secondPulseTime = millis();
      pulseInterval = secondPulseTime - firstPulseTime;
      firstPulseTime = secondPulseTime;
    }
    samePulse = true;
  }

  if(pulse < 590){
    samePulse = false;
  }  

  return bpm = (1.0/pulseInterval) * 60.0 * 1000;
}


