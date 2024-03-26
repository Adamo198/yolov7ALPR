const int RELAY_PIN = 2;
const int DETECTION_PIN = 3;
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
    Serial.print("AON\n");
    delay(300); 
  }
  else if (detectionTrigger == HIGH && previousTriggerState == LOW)
  {
    Serial.print("AOFF\n");
    delay(300);    
  }
  
  previousTriggerState = detectionTrigger;
  
  if (Serial.available() > 0)
  {    
    int condition = Serial.read();

    if (condition == '1')
    {
      digitalWrite(RELAY_PIN, HIGH);
      Serial.print("Arduino: Relay active...");
      delay(300);
    }
    digitalWrite(RELAY_PIN, LOW);
    Serial.print("Arduino: Relay disabled...");
  }
}
