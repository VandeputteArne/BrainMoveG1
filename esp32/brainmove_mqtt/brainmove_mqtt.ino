#include <Arduino.h>
#include <WiFi.h>
#include <PubSubClient.h>
#include <Wire.h>
#include <VL53L0X.h>

#define DEVICE_COLOR "geel"

const char* WIFI_SSID = "BrainMoveG1";
const char* WIFI_PASSWORD = "bmSecure1998";

const char* MQTT_BROKER = "10.42.0.1";
const int MQTT_PORT = 1883;
const int MQTT_KEEPALIVE_DURATION = 5; 

const int PIN_BATTERIJ_ADC = 2;
const int PIN_KNOP = 3;
const int PIN_TOF_XSHUT = 4;
const int PIN_ZOEMER = 5;

const int PIN_I2C_SDA = 6;
const int PIN_I2C_SCL = 7;

const uint16_t TOF_DETECTIE_MIN_MM = 50;
const uint16_t TOF_DETECTIE_MAX_MM = 1000;
const uint16_t TOF_POLL_INTERVAL_MS = 40;
const uint16_t TOF_DETECTIE_AFKOELING_MS = 500;

const float BATTERIJ_VOL_SPANNING = 4.2f;
const float BATTERIJ_LEEG_SPANNING = 3.0f;
const float BATTERIJ_SPANNINGSDELER = 2.0f;

const unsigned long BATTERIJ_UPDATE_INTERVAL = 600000;
const uint8_t BATTERIJ_KRITIEK_PERCENTAGE = 5;

const unsigned long GLOBALE_INACTIEF_TIMEOUT_MS = (10UL * 60UL * 1000UL);
const unsigned long KNOP_DEBOUNCE_MS = 150;
const unsigned long VERBINDING_PIEP_INTERVAL_MS = 10000;

const int ZOEMER_KANAAL = 0;
const int ZOEMER_RESOLUTIE = 8;
const int ZOEMER_FREQ_STANDAARD = 2000;

WiFiClient wifiClient;
PubSubClient mqttClient(wifiClient);
VL53L0X tofSensor;

String topic_detect, topic_battery, topic_status, topic_cmd, topic_cmd_all;

bool isPolling = false;
bool isCorrectTarget = false;
bool tofGeinitialiseerd = false;
volatile bool knopIngedrukt = false;

unsigned long laatsteTofPollTijd = 0;
unsigned long laatsteDetectieTijd = 0;
unsigned long laatsteActiviteitTijd = 0;
unsigned long laatsteBatterijUpdateTijd = 0;
unsigned long laatsteKnopDrukTijd = 0;

void IRAM_ATTR knopISR() { knopIngedrukt = true; }
void verbindGeforceerd();
void mqttCallback(char* topic, byte* payload, unsigned int length);
void initHardware();
void verwerkKnopDruk();
void verwerkKnopTijdensVerbinden();
void verwerkKnopHold(bool tijdensVerbinden);
void verwerkToF();
uint8_t leesBatterijPercentage();
void speelCorrectGeluid();
void speelIncorrectGeluid();
void speelVerbindingGeluid();
void speelOntwaakGeluid();
void speelVerbindingZoekGeluid();
void speelBatterijLeegGeluid();
void zoemerToon(uint32_t freq, uint32_t duur);
void zoemerUit();
void gaaDiepeSlaap();
void controleerKritiekeBatterij();

void setup() {
  Serial.begin(115200);
  delay(3000);
  
  esp_sleep_wakeup_cause_t ontwaakOorzaak = esp_sleep_get_wakeup_cause();
  initHardware();
  if (ontwaakOorzaak == ESP_SLEEP_WAKEUP_GPIO) speelOntwaakGeluid();
  
  topic_detect = String("bm/") + DEVICE_COLOR + "/detect";
  topic_battery = String("bm/") + DEVICE_COLOR + "/battery";
  topic_status = String("bm/") + DEVICE_COLOR + "/status";
  topic_cmd = String("bm/") + DEVICE_COLOR + "/cmd";
  topic_cmd_all = "bm/all/cmd";
  
  mqttClient.setServer(MQTT_BROKER, MQTT_PORT);
  mqttClient.setCallback(mqttCallback);
  mqttClient.setKeepAlive(MQTT_KEEPALIVE_DURATION);
  
  laatsteActiviteitTijd = millis();

  uint8_t batterijPercentageBoot = leesBatterijPercentage();
    Serial.print("Battery % on boot: ");
    Serial.println(batterijPercentageBoot);
}

void loop() {
  if (WiFi.status() != WL_CONNECTED || !mqttClient.connected()) {
    verbindGeforceerd(); 
  }

  mqttClient.loop();
  verwerkKnopDruk();

  if (isPolling) {
    verwerkToF();
  }

  if (millis() - laatsteBatterijUpdateTijd >= BATTERIJ_UPDATE_INTERVAL) {
    laatsteBatterijUpdateTijd = millis();
    uint8_t batterijPercentage = leesBatterijPercentage();
    String payload = String(batterijPercentage);
    mqttClient.publish(topic_battery.c_str(), payload.c_str(), false);

    Serial.print("Battery % sent: ");
    Serial.println(batterijPercentage);
    if (batterijPercentage <= BATTERIJ_KRITIEK_PERCENTAGE) {
      Serial.println("Kritieke batterij - ga slapen...");
      speelBatterijLeegGeluid();
      gaaDiepeSlaap();
    }
  }


  yield();
}

void verbindGeforceerd() {
  static unsigned long verbindingStartTijd = 0;
  static unsigned long laatstePiepTijd = 0;

  if (verbindingStartTijd == 0) {
    verbindingStartTijd = millis();
    laatstePiepTijd = 0;
  }

  Serial.println("Verbinding verloren...");
  zoemerUit();
  isPolling = false;

  if (WiFi.status() != WL_CONNECTED) {
    Serial.print("WiFi: "); Serial.println(WIFI_SSID);
    WiFi.disconnect();
    WiFi.mode(WIFI_STA);
    WiFi.setSleep(true);
    WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

    while (WiFi.status() != WL_CONNECTED) {
      if (knopIngedrukt) {
        knopIngedrukt = false;
        verwerkKnopTijdensVerbinden();
      }
      if (millis() - verbindingStartTijd > GLOBALE_INACTIEF_TIMEOUT_MS) {
        Serial.println("\nWiFi timeout - ga slapen...");
        gaaDiepeSlaap();
      }
      if (millis() - laatstePiepTijd >= VERBINDING_PIEP_INTERVAL_MS) {
        speelVerbindingZoekGeluid();
        laatstePiepTijd = millis();
      }
      delay(500); Serial.print(".");
    }
    Serial.println(" WiFi OK.");
  }

  while (!mqttClient.connected()) {
    if (knopIngedrukt) {
      knopIngedrukt = false;
      verwerkKnopTijdensVerbinden();
    }
    if (millis() - verbindingStartTijd > GLOBALE_INACTIEF_TIMEOUT_MS) {
      Serial.println("MQTT timeout - ga slapen...");
      gaaDiepeSlaap();
    }
    if (millis() - laatstePiepTijd >= VERBINDING_PIEP_INTERVAL_MS) {
      speelVerbindingZoekGeluid();
      laatstePiepTijd = millis();
    }

    if (WiFi.status() != WL_CONNECTED) return;

    String clientId = String("BM-") + DEVICE_COLOR + "-" + String(ESP.getEfuseMac(), HEX);

    if (mqttClient.connect(clientId.c_str(), topic_status.c_str(), 1, true, "offline")) {
      Serial.println("MQTT OK!");

      mqttClient.subscribe(topic_cmd.c_str());
      mqttClient.subscribe(topic_cmd_all.c_str());

      mqttClient.publish(topic_status.c_str(), "online", true);

      uint8_t batterijPercentage = leesBatterijPercentage();
      String battPayload = String(batterijPercentage);
      mqttClient.publish(topic_battery.c_str(), battPayload.c_str(), false);

      Serial.print("Battery % sent: ");
      Serial.println(batterijPercentage);

      laatsteBatterijUpdateTijd = millis();
      speelVerbindingGeluid();
      laatsteActiviteitTijd = millis();

      verbindingStartTijd = 0;

    } else {
      Serial.print("MQTT Fail rc="); Serial.println(mqttClient.state());
      delay(2000);
    }
  }
}

void mqttCallback(char* topic, byte* payload, unsigned int length) {
  String message = "";
  for (unsigned int i = 0; i < length; i++) message += (char)payload[i];
  laatsteActiviteitTijd = millis();
  if (message == "start") {
    isPolling = true;
    WiFi.setSleep(false);
  }
  else if (message == "stop") {
    isPolling = false;
    WiFi.setSleep(true);
  }
  else if (message == "correct") isCorrectTarget = true;
  else if (message == "incorrect") isCorrectTarget = false;
  else if (message == "sleep") gaaDiepeSlaap();
  else if (message == "sound_ok") speelCorrectGeluid();
  else if (message == "sound_fail") speelIncorrectGeluid();
}

void initHardware() {
  pinMode(PIN_KNOP, INPUT_PULLUP);
  attachInterrupt(digitalPinToInterrupt(PIN_KNOP), knopISR, FALLING);
  ledcAttach(PIN_ZOEMER, ZOEMER_FREQ_STANDAARD, ZOEMER_RESOLUTIE);
  ledcWrite(PIN_ZOEMER, 0);
  analogReadResolution(12);
  analogSetAttenuation(ADC_11db);

  pinMode(PIN_TOF_XSHUT, OUTPUT);
  digitalWrite(PIN_TOF_XSHUT, LOW);
  delay(10);
  digitalWrite(PIN_TOF_XSHUT, HIGH);
  delay(10);

  Wire.begin(PIN_I2C_SDA, PIN_I2C_SCL);
  Wire.setClock(400000);
  tofSensor.setTimeout(500);
  if (!tofSensor.init()) {
    Serial.println("FOUT: Geen sensor!");
    tofGeinitialiseerd = false;
  } else {
    tofSensor.setMeasurementTimingBudget(40000);
    tofSensor.startContinuous();
    tofGeinitialiseerd = true;
  }
}

void verwerkKnopHold(bool tijdensVerbinden) {
    const unsigned long HOLD_RESTART_MS = 1500;
    const unsigned long HOLD_CANCEL_MS = 3000;

    unsigned long pressStart = millis();
    bool restartBeeped = false;

    while (digitalRead(PIN_KNOP) == LOW) {
        unsigned long holdTime = millis() - pressStart;

        if (!restartBeeped && holdTime >= HOLD_RESTART_MS) {
            zoemerToon(1500, 80);
            restartBeeped = true;
        }

        if (holdTime >= HOLD_CANCEL_MS + 1000) break;

        delay(10);
    }

    unsigned long holdDuration = millis() - pressStart;

    if (holdDuration >= HOLD_CANCEL_MS) {
        Serial.println("Knop te lang ingedrukt - geannuleerd");
        zoemerToon(300, 200);

        while (digitalRead(PIN_KNOP) == LOW) delay(10);
        delay(500);
        knopIngedrukt = false;
        return;

    } else if (holdDuration >= HOLD_RESTART_MS) {
        Serial.println("Knop lang ingedrukt - herstart ESP...");
        zoemerToon(1000, 100); delay(50); zoemerToon(1500, 100);
        if (!tijdensVerbinden && mqttClient.connected()) {
            mqttClient.publish(topic_status.c_str(), "restarting", true);
            mqttClient.disconnect();
        }
        delay(100);
        ESP.restart();

    } else {
        Serial.println("Knop kort ingedrukt - ga slapen...");
        zoemerToon(800, 100); delay(50); zoemerToon(500, 150);
        gaaDiepeSlaap();
    }
}

void verwerkKnopDruk() {
    if (!knopIngedrukt) return;
    if (millis() - laatsteKnopDrukTijd < KNOP_DEBOUNCE_MS) { knopIngedrukt = false; return; }
    knopIngedrukt = false;
    laatsteKnopDrukTijd = millis();
    laatsteActiviteitTijd = millis();

    verwerkKnopHold(false);
}

void verwerkKnopTijdensVerbinden() {
    verwerkKnopHold(true);
}

void verwerkToF() {
    if (!tofGeinitialiseerd) return;
    if (millis() - laatsteTofPollTijd >= TOF_POLL_INTERVAL_MS) {
        laatsteTofPollTijd = millis();
        uint16_t afstand = tofSensor.readRangeContinuousMillimeters();
        if (tofSensor.timeoutOccurred()) return; 
        bool geldigeDetectie = (afstand > TOF_DETECTIE_MIN_MM && afstand < TOF_DETECTIE_MAX_MM);
        if (geldigeDetectie && (millis() - laatsteDetectieTijd >= TOF_DETECTIE_AFKOELING_MS)) {
            if (isCorrectTarget) speelCorrectGeluid(); else speelIncorrectGeluid();
            String payload = String(afstand);
            mqttClient.publish(topic_detect.c_str(), payload.c_str(), false);
            laatsteDetectieTijd = millis();
            laatsteActiviteitTijd = millis();
        }
    }
}

uint8_t leesBatterijPercentage() {
    long totaal = 0;
    for (int i = 0; i < 16; i++) {
        totaal += analogRead(PIN_BATTERIJ_ADC);
        delayMicroseconds(500);
    }
    int adcWaarde = totaal / 16;

    float spanning = (adcWaarde / 4095.0f) * 3.3f * BATTERIJ_SPANNINGSDELER;

    const float lipoTabel[][2] = {
        {4.20f, 100.0f},
        {4.10f,  90.0f},
        {4.00f,  80.0f},
        {3.90f,  70.0f},
        {3.80f,  55.0f},
        {3.70f,  40.0f},
        {3.60f,  25.0f},
        {3.50f,  15.0f},
        {3.40f,   8.0f},
        {3.30f,   4.0f},
        {3.00f,   0.0f}
    };
    const int tabelGrootte = sizeof(lipoTabel) / sizeof(lipoTabel[0]);

    if (spanning >= lipoTabel[0][0]) return 100;
    if (spanning <= lipoTabel[tabelGrootte - 1][0]) return 0;

    for (int i = 0; i < tabelGrootte - 1; i++) {
        if (spanning >= lipoTabel[i + 1][0]) {
            float spanHoog = lipoTabel[i][0];
            float spanLaag = lipoTabel[i + 1][0];
            float percHoog = lipoTabel[i][1];
            float percLaag = lipoTabel[i + 1][1];
            float percentage = percLaag + (spanning - spanLaag) / (spanHoog - spanLaag) * (percHoog - percLaag);
            return (uint8_t)percentage;
        }
    }
    return 0;
}

void zoemerToon(uint32_t freq, uint32_t duur) {
    ledcChangeFrequency(PIN_ZOEMER, freq, ZOEMER_RESOLUTIE);
    ledcWrite(PIN_ZOEMER, 127); delay(duur); zoemerUit();
}
void zoemerUit() { ledcWrite(PIN_ZOEMER, 0); }
void speelCorrectGeluid() { zoemerToon(1000, 100); delay(50); zoemerToon(1500, 100); delay(50); zoemerToon(2000, 150); }
void speelIncorrectGeluid() { zoemerToon(400, 150); delay(50); zoemerToon(300, 150); delay(50); zoemerToon(200, 200); }
void speelVerbindingGeluid() { zoemerToon(800, 100); delay(50); zoemerToon(1200, 150); }
void speelOntwaakGeluid() { zoemerToon(500, 100); delay(30); zoemerToon(800, 100); delay(30); zoemerToon(1200, 120); }
void speelVerbindingZoekGeluid() { zoemerToon(600, 80); }
void speelBatterijLeegGeluid() { zoemerToon(300, 200); delay(100); zoemerToon(200, 300); }

void gaaDiepeSlaap() {
    if (mqttClient.connected()) {
        mqttClient.publish(topic_status.c_str(), "sleeping", true);
        mqttClient.disconnect();
    }
    delay(100); zoemerUit();
    if (tofGeinitialiseerd) tofSensor.stopContinuous();

    digitalWrite(PIN_TOF_XSHUT, LOW);

    esp_deep_sleep_enable_gpio_wakeup(BIT(PIN_KNOP), ESP_GPIO_WAKEUP_GPIO_LOW);
    esp_deep_sleep_start();
}

void controleerKritiekeBatterij() {
    uint8_t batterij = leesBatterijPercentage();
    if (batterij <= BATTERIJ_KRITIEK_PERCENTAGE) {
        Serial.println("Kritieke batterij - ga slapen...");
        speelBatterijLeegGeluid();
        gaaDiepeSlaap();
    }
}