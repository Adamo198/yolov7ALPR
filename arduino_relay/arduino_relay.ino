const int RELAY_PIN = 2;

void setup() {
  Serial.begin(115200);
  pinMode(RELAY_PIN, OUTPUT);
  digitalWrite(RELAY_PIN, LOW);
}

void loop() {
  if (Serial.available() > 0)
  {    
    int condition = Serial.read();

    if (condition == '1')
    {
      digitalWrite(RELAY_PIN, HIGH);
      Serial.print("Arduino: Relay active...\n");
      delay(500);
    }
    digitalWrite(RELAY_PIN, LOW);
    Serial.print("Arduino: Relay disabled...\n");

  }
}
