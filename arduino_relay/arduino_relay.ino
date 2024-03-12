const int RELAY_PIN = 13;
const int DETECTION_PIN = 14;
int previousTriggerState = HIGH;

void setup() {
  Serial.begin(115200);
  pinMode(RELAY_PIN, OUTPUT);
  digitalWrite(RELAY_PIN, LOW);
  pinMode(DETECTION_PIN, INPUT_PULLUP);
}

void loop() {
  int detectionTrigger = digitalRead(DETECTION_PIN); /*HIGH means not active due to internal PULLUP resistor*/
  
  if (detectionTrigger == LOW && previousTriggerState == HIGH)
  {
    Serial.print("ANPR start\n");
    delay(1000); 
  }
  else if (detectionTrigger == HIGH && previousTriggerState == LOW)
  {
    Serial.print("ANPR stop\n");
    delay(1000);    
  }
  
  previousTriggerState = detectionTrigger;
  
  if (Serial.available() > 0)
  {    
    int condition = Serial.read();

    if (condition == '1')
    {
      digitalWrite(RELAY_PIN, HIGH);
      Serial.print("Arduino: Relay active...\n");
      delay(300);
    }
    digitalWrite(RELAY_PIN, LOW);
    Serial.print("Arduino: Relay disabled...\n");
  }
}
