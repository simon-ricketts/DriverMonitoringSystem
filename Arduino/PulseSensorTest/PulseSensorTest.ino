int PulseSensorPin = 3;
int LED13 = 13;
int Signal;
int Threshold = 650;

void setup() {
  pinMode(LED13,OUTPUT);
  Serial.begin(9600);
}

void loop() {
  delay(20);
  Signal = analogRead(PulseSensorPin);
  Serial.println(Signal);
  if(Signal > Threshold){
    digitalWrite(LED13,HIGH);
  }
  else{
    digitalWrite(LED13,LOW);
  }
  }
