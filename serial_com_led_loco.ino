String command;


#define redLed1 10
#define redLed2 7
#define whiteLed1 9
#define whiteLed2 6
#define blueLed1 8
#define blueLed2 5




void setup() {
  Serial.begin(9600);
  
  pinMode(redLed1, OUTPUT);
  pinMode(redLed2, OUTPUT);
  pinMode(whiteLed1, OUTPUT);
  pinMode(whiteLed2, OUTPUT);
  pinMode(blueLed1, OUTPUT);
  pinMode(blueLed2, OUTPUT);
    
  delay(2000);

  Serial.println("Type Command ( frontleft, frontright, midleft, midright, backleft, backright, all, off)");
}

void loop() {
  if (Serial.available()) {
    command = Serial.readStringUntil('\n');
    command.trim();
    if (command.equals("frontleft")) {
      digitalWrite(whiteLed1, LOW);
      digitalWrite(blueLed1, LOW);
      digitalWrite(redLed1, HIGH);
      digitalWrite(whiteLed2, LOW);
      digitalWrite(blueLed2, LOW);
      digitalWrite(redLed2, LOW);
    }
    else if (command.equals("frontright")) {
      digitalWrite(whiteLed1, LOW);
      digitalWrite(blueLed1, LOW);
      digitalWrite(redLed1, LOW);
      digitalWrite(whiteLed2, LOW);
      digitalWrite(blueLed2, LOW);
      digitalWrite(redLed2, HIGH);
    }
    else if (command.equals("midleft")) {
      digitalWrite(whiteLed1, HIGH);
      digitalWrite(blueLed1, LOW);
      digitalWrite(redLed1, LOW);
      digitalWrite(whiteLed2, LOW);
      digitalWrite(blueLed2, LOW);
      digitalWrite(redLed2, LOW);
    }
    else if (command.equals("midright")) {
      digitalWrite(whiteLed1, LOW);
      digitalWrite(blueLed1, LOW);
      digitalWrite(redLed1, LOW);
      digitalWrite(whiteLed2, HIGH);
      digitalWrite(blueLed2, LOW);
      digitalWrite(redLed2, LOW);
    }
    else if (command.equals("backleft")) {
      digitalWrite(whiteLed1, LOW);
      digitalWrite(blueLed1, HIGH);
      digitalWrite(redLed1, LOW);
      digitalWrite(whiteLed2, LOW);
      digitalWrite(blueLed2, LOW);
      digitalWrite(redLed2, LOW);
    }
    else if (command.equals("backright")) {
      digitalWrite(whiteLed1, LOW);
      digitalWrite(blueLed1, LOW);
      digitalWrite(redLed1, LOW);
      digitalWrite(whiteLed2, LOW);
      digitalWrite(blueLed2, HIGH);
      digitalWrite(redLed2, LOW);
    }
    else if (command.equals("all")) {
      digitalWrite(whiteLed1, HIGH);
      digitalWrite(blueLed1, HIGH);
      digitalWrite(redLed1, HIGH);
      digitalWrite(whiteLed2, HIGH);
      digitalWrite(blueLed2, HIGH);
      digitalWrite(redLed2, HIGH);
    }
    else if (command.equals("off")) {
      digitalWrite(whiteLed1, LOW);
      digitalWrite(blueLed1, LOW);
      digitalWrite(redLed1, LOW);
      digitalWrite(whiteLed2, LOW);
      digitalWrite(blueLed2, LOW);
      digitalWrite(redLed2, LOW);
    }
    else {
      Serial.println("bad command");
    }
    Serial.print("Command: ");
    Serial.println(command);
  }
}