String command;

#define greenLed 7
#define blueLed 8
#define whiteLed 9
#define redLed 10


void setup() {
  Serial.begin(9600);
  pinMode(greenLed, OUTPUT);
  pinMode(blueLed, OUTPUT);
  pinMode(whiteLed, OUTPUT);
  pinMode(redLed, OUTPUT);

  delay(2000);

  Serial.println("Type Command (white, blue, red, green, all, off)");
}

void loop() {
  if (Serial.available()) {
    command = Serial.readStringUntil('\n');
    command.trim();
    if (command.equals("white")) {
      digitalWrite(whiteLed, HIGH);
      digitalWrite(blueLed, LOW);
      digitalWrite(redLed, LOW);
      digitalWrite(greenLed, LOW);
    }

    else if (command.equals("blue")) {
      digitalWrite(whiteLed, LOW);
      digitalWrite(blueLed, HIGH);
      digitalWrite(redLed, LOW);
      digitalWrite(greenLed, LOW);
    }
    else if (command.equals("green")) {
      digitalWrite(whiteLed, LOW);
      digitalWrite(blueLed, LOW);
      digitalWrite(redLed, LOW);
      digitalWrite(greenLed, HIGH);
    }
    else if (command.equals("red")) {
      digitalWrite(whiteLed, LOW);
      digitalWrite(blueLed, LOW);
      digitalWrite(redLed, HIGH);
      digitalWrite(greenLed, LOW);
    }
    else if (command.equals("all")) {
      digitalWrite(whiteLed, HIGH);
      digitalWrite(blueLed, HIGH);
      digitalWrite(redLed, HIGH);
      digitalWrite(greenLed, HIGH);
    }
    else if (command.equals("off")) {
      digitalWrite(whiteLed, LOW);
      digitalWrite(blueLed, LOW);
      digitalWrite(redLed, LOW);
      digitalWrite(greenLed, LOW);
    }
    else {
      Serial.println("bad command");
    }
    Serial.print("Command: ");
    Serial.println(command);
  }
}