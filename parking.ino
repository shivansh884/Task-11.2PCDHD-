#include <WiFiNINA.h>
#include <ArduinoMqttClient.h>
#include <LiquidCrystal_I2C.h>
#include <NewPing.h>

// WiFi credentials
const char* ssid = "realme@24";
const char* password = "Realme27";

// MQTT settings
const char* mqtt_broker = "broker.hivemq.com";
const int mqtt_port = 1883;
const char* topic_slot1 = "parking/slots/1";
const char* topic_slot2 = "parking/slots/2";

// Hardware pins
#define TRIGGER_PIN_1 2
#define ECHO_PIN_1 3
#define TRIGGER_PIN_2 4
#define ECHO_PIN_2 5
#define BUZZER_1 6
#define BUZZER_2 7

// Constants
#define MAX_DISTANCE 10
#define SAFE_DISTANCE 5
#define DANGER_DISTANCE 3

// Initialize objects
WiFiClient wifiClient;
MqttClient mqttClient(wifiClient);
NewPing sonar1(TRIGGER_PIN_1, ECHO_PIN_1, MAX_DISTANCE);
NewPing sonar2(TRIGGER_PIN_2, ECHO_PIN_2, MAX_DISTANCE);
LiquidCrystal_I2C lcd1(0x27, 16, 2);
LiquidCrystal_I2C lcd2(0x26, 16, 2);

// Timing variables
unsigned long buzzerStartTime = 0;
const int BUZZER_DURATION = 3000; // Buzzer duration in milliseconds

void setup() {
  Serial.begin(9600);

  // Initialize LCDs
  lcd1.init();
  lcd2.init();
  lcd1.backlight();
  lcd2.backlight();

  // Initialize buzzers
  pinMode(BUZZER_1, OUTPUT);
  pinMode(BUZZER_2, OUTPUT);

  // Connect to WiFi
  connectWiFi();

  // Connect to MQTT broker
  connectMQTT();
}

void connectWiFi() {
  Serial.print("Connecting to WiFi...");
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nConnected to WiFi");
}

void connectMQTT() {
  Serial.print("Connecting to MQTT broker...");
  while (!mqttClient.connect(mqtt_broker, mqtt_port)) {
    delay(1000);
    Serial.print(".");
  }
  Serial.println("\nConnected to MQTT broker");
}

void handleParking(NewPing &sonar, LiquidCrystal_I2C &lcd, int buzzerPin, const char* topic) {
  int distance = sonar.ping_cm();

  if (distance == 0) {
    lcd.clear();
    lcd.print("No car detected");
    mqttClient.beginMessage(topic);
    mqttClient.print("empty");
    mqttClient.endMessage();
    
    // Turn off the buzzer if no car is detected
    digitalWrite(buzzerPin, LOW);
  }
  else if (distance <= DANGER_DISTANCE) {
    lcd.clear();
    lcd.print("TOO CLOSE!");

    // Turn on the buzzer and start the timer if not already buzzing
    if (digitalRead(buzzerPin) == LOW) {
      digitalWrite(buzzerPin, HIGH);
      buzzerStartTime = millis();  // Start timer
    }

    mqttClient.beginMessage(topic);
    mqttClient.print("occupied");
    mqttClient.endMessage();
  }
  else if (distance <= SAFE_DISTANCE) {
    lcd.clear();
    lcd.print("Perfect parking!");

    // Turn off the buzzer if the car is at a safe distance
    digitalWrite(buzzerPin, LOW);
    mqttClient.beginMessage(topic);
    mqttClient.print("occupied");
    mqttClient.endMessage();
  }
  else {
    lcd.clear();
    lcd.print("Move closer");

    // Turn off the buzzer if the car is not in the "too close" range
    digitalWrite(buzzerPin, LOW);
    mqttClient.beginMessage(topic);
    mqttClient.print("occupied");
    mqttClient.endMessage();
  }

  // Automatically turn off the buzzer after BUZZER_DURATION
  if (digitalRead(buzzerPin) == HIGH && (millis() - buzzerStartTime >= BUZZER_DURATION)) {
    digitalWrite(buzzerPin, LOW);  // Turn off buzzer after set duration
  }
}

void loop() {
  mqttClient.poll();

  // Handle parking slot 1
  handleParking(sonar1, lcd1, BUZZER_1, topic_slot1);

  // Handle parking slot 2
  handleParking(sonar2, lcd2, BUZZER_2, topic_slot2);

  delay(1000);
}
