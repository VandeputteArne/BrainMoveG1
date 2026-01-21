#include <WiFi.h>
#include <PubSubClient.h>

#define DEVICE_COLOR "rood"

const char* WIFI_SSID = "BrainMoveG1";
const char* WIFI_PASSWORD = "bmSecure1998";

const char* MQTT_BROKER = "10.42.0.1";
const int MQTT_PORT = 1883;
const int MQTT_KEEPALIVE = 60;

const int SENSOR_PIN = 34;
const int LED_GREEN = 25;
const int LED_RED = 26;
const int BUZZER_PIN = 27;
const int BATTERY_PIN = 35;

const int DETECTION_THRESHOLD = 1500;
const int DEBOUNCE_MS = 100;
const int BATTERY_INTERVAL = 300000;

WiFiClient wifiClient;
PubSubClient mqttClient(wifiClient);

// MQTT Topics
String topic_detect;
String topic_battery;
String topic_status;
String topic_cmd;
String topic_cmd_all;

// State
bool isPolling = false;
bool isCorrectTarget = false;
bool lastDetectionState = false;
unsigned long lastDebounceTime = 0;
unsigned long lastBatteryTime = 0;
unsigned long lastReconnectAttempt = 0;

void setup() {
  Serial.begin(115200);
  delay(1000);

  Serial.println("\n=== BrainMove MQTT Firmware ===");
  Serial.print("Device: BM-");
  Serial.println(DEVICE_COLOR);

  pinMode(SENSOR_PIN, INPUT);
  pinMode(LED_GREEN, OUTPUT);
  pinMode(LED_RED, OUTPUT);
  pinMode(BUZZER_PIN, OUTPUT);
  pinMode(BATTERY_PIN, INPUT);

  digitalWrite(LED_RED, HIGH);
  digitalWrite(LED_GREEN, LOW);

  topic_detect = String("bm/") + DEVICE_COLOR + "/detect";
  topic_battery = String("bm/") + DEVICE_COLOR + "/battery";
  topic_status = String("bm/") + DEVICE_COLOR + "/status";
  topic_cmd = String("bm/") + DEVICE_COLOR + "/cmd";
  topic_cmd_all = "bm/all/cmd";

  connectWiFi();

  mqttClient.setServer(MQTT_BROKER, MQTT_PORT);
  mqttClient.setCallback(mqttCallback);
  mqttClient.setKeepAlive(MQTT_KEEPALIVE);

  String lwt_message = "offline";
  mqttClient.setWill(topic_status.c_str(), lwt_message.c_str(), 1, true);

  connectMQTT();

  Serial.println("Setup complete!");
}

// ==================== MAIN LOOP ====================
void loop() {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("WiFi disconnected! Reconnecting...");
    connectWiFi();
  }

  if (!mqttClient.connected()) {
    unsigned long now = millis();
    if (now - lastReconnectAttempt > 5000) {
      lastReconnectAttempt = now;
      if (connectMQTT()) {
        lastReconnectAttempt = 0;
      }
    }
  } else {
    mqttClient.loop();
  }

  if (isPolling) {
    checkSensor();
  }

  unsigned long now = millis();
  if (now - lastBatteryTime > BATTERY_INTERVAL) {
    lastBatteryTime = now;
    sendBatteryStatus();
  }
}

void connectWiFi() {
  Serial.print("Connecting to WiFi: ");
  Serial.println(WIFI_SSID);

  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 20) {
    delay(500);
    Serial.print(".");
    attempts++;
  }

  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\nWiFi connected!");
    Serial.print("IP: ");
    Serial.println(WiFi.localIP());
    Serial.print("RSSI: ");
    Serial.print(WiFi.RSSI());
    Serial.println(" dBm");
  } else {
    Serial.println("\nWiFi connection failed!");
  }
}

bool connectMQTT() {
  Serial.print("Connecting to MQTT broker: ");
  Serial.println(MQTT_BROKER);

  String clientId = String("BM-") + DEVICE_COLOR + "-" + String(ESP.getEfuseMac(), HEX);

  if (mqttClient.connect(clientId.c_str())) {
    Serial.println("MQTT connected!");

    mqttClient.subscribe(topic_cmd.c_str());
    mqttClient.subscribe(topic_cmd_all.c_str());
    Serial.print("Subscribed to: ");
    Serial.println(topic_cmd);
    Serial.print("Subscribed to: ");
    Serial.println(topic_cmd_all);

    mqttClient.publish(topic_status.c_str(), "online", true);
    Serial.println("Published: online");

    return true;
  } else {
    Serial.print("MQTT connection failed, rc=");
    Serial.println(mqttClient.state());
    return false;
  }
}

void mqttCallback(char* topic, byte* payload, unsigned int length) {
  String message = "";
  for (unsigned int i = 0; i < length; i++) {
    message += (char)payload[i];
  }

  Serial.print("MQTT message: ");
  Serial.print(topic);
  Serial.print(" -> ");
  Serial.println(message);

  if (message == "start") {
    isPolling = true;
    Serial.println("Polling STARTED");
  }
  else if (message == "stop") {
    isPolling = false;
    lastDetectionState = false;
    Serial.println("Polling STOPPED");
  }
  else if (message == "correct") {
    isCorrectTarget = true;
    digitalWrite(LED_GREEN, HIGH);
    digitalWrite(LED_RED, LOW);
    Serial.println("Set as CORRECT target");
  }
  else if (message == "incorrect") {
    isCorrectTarget = false;
    digitalWrite(LED_GREEN, LOW);
    digitalWrite(LED_RED, HIGH);
    Serial.println("Set as INCORRECT");
  }
  else if (message == "sound_ok") {
    playSuccessSound();
  }
  else if (message == "sound_fail") {
    playFailureSound();
  }
}

void checkSensor() {
  int sensorValue = analogRead(SENSOR_PIN);
  bool isDetected = (sensorValue > DETECTION_THRESHOLD);

  unsigned long now = millis();
  if (isDetected != lastDetectionState) {
    if (now - lastDebounceTime > DEBOUNCE_MS) {
      lastDebounceTime = now;
      lastDetectionState = isDetected;

      String payload = isDetected ? "1" : "0";
      mqttClient.publish(topic_detect.c_str(), payload.c_str(), false);

      Serial.print("Detection: ");
      Serial.print(payload);
      Serial.print(" (sensor: ");
      Serial.print(sensorValue);
      Serial.println(")");
    }
  }
}

void sendBatteryStatus() {
  int rawValue = analogRead(BATTERY_PIN);
  float voltage = (rawValue / 4095.0) * 3.3 * 2.0;  // Assuming voltage divider

  int percentage = (int)((voltage - 3.0) / 1.2 * 100.0);
  percentage = constrain(percentage, 0, 100);

  String payload = String(percentage);
  mqttClient.publish(topic_battery.c_str(), payload.c_str(), false);

  Serial.print("Battery: ");
  Serial.print(percentage);
  Serial.print("% (");
  Serial.print(voltage);
  Serial.println("V)");
}

void playSuccessSound() {
  tone(BUZZER_PIN, 523, 100);
  delay(100);
  tone(BUZZER_PIN, 659, 100);
  delay(100);
  tone(BUZZER_PIN, 784, 150);
  delay(150);
  noTone(BUZZER_PIN);
  Serial.println("Played success sound");
}

void playFailureSound() {
  tone(BUZZER_PIN, 392, 100);
  delay(100);
  tone(BUZZER_PIN, 330, 100);
  delay(100);
  tone(BUZZER_PIN, 262, 200);
  delay(200);
  noTone(BUZZER_PIN);
  Serial.println("Played failure sound");
}
