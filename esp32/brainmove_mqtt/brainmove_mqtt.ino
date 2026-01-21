#include <Arduino.h>
#include <WiFi.h>
#include <PubSubClient.h>
#include <Wire.h>
#include <VL53L0X.h>

#define DEVICE_COLOR "blauw" 

const char* WIFI_SSID = "BrainMoveG1";
const char* WIFI_PASSWORD = "bmSecure1998";

const char* MQTT_BROKER = "10.42.0.1";
const int MQTT_PORT = 1883;
const int MQTT_KEEPALIVE_DURATION = 60; 

// ==================== PIN DEFINITIES (Seeed XIAO ESP32-C3) ====================
const int PIN_BATTERIJ_ADC_1 = 2; // D0
const int PIN_KNOP = 3;           // D1
const int PIN_BATTERIJ_ADC_2 = 4; // D2
const int PIN_ZOEMER = 5;         // D3

const int PIN_I2C_SDA = 6;        // D4 (SDA)
const int PIN_I2C_SCL = 7;        // D5 (SCL)

const int PIN_USB_VBUS = 21;      // D6 

// LEDS
const int PIN_LED_ROOD = 8;       // D8
const int PIN_LED_GROEN = 20;     // D7 (VEILIGE PIN: GPIO 20)
const int PIN_LED_BLAUW = 10;     // D10

const uint16_t TOF_DETECTIE_MIN_MM = 50;
const uint16_t TOF_DETECTIE_MAX_MM = 1000;
const uint16_t TOF_POLL_INTERVAL_MS = 33;
const uint16_t TOF_DETECTIE_AFKOELING_MS = 500;

const float BATTERIJ_VOL_SPANNING = 4.2f;
const float BATTERIJ_LEEG_SPANNING = 3.0f;
const float BATTERIJ_SPANNINGSDELER = 2.0f;
const int BATTERIJ_NIVEAU_LAAG = 20;
const int BATTERIJ_NIVEAU_MIDDEL = 50;
const int LED_OPLADEN_KNIPPEREN_MS = 500;
const int LED_UPDATE_INTERVAL = 5000;
const bool RGB_GEMEENSCHAPPELIJKE_ANODE = false;

const unsigned long GLOBALE_INACTIEF_TIMEOUT_MS = (30UL * 60UL * 1000UL); // 30 min
const unsigned long KNOP_DEBOUNCE_MS = 150;
const uint16_t USB_VBUS_DREMPEL = 2000;

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
bool usbVerbonden = false;
bool oplaadLedStatus = false;
volatile bool knopIngedrukt = false;

unsigned long laatsteTofPollTijd = 0;
unsigned long laatsteDetectieTijd = 0;
unsigned long laatsteActiviteitTijd = 0;
unsigned long laatsteLedUpdateTijd = 0;
unsigned long laatsteOplaadKnipperTijd = 0;
unsigned long lastReconnectAttempt = 0;
unsigned long laatsteKnopDrukTijd = 0;
uint8_t laatsteBatterijPercentage = 0;

void IRAM_ATTR knopISR() { knopIngedrukt = true; }
void connectWiFi();
bool connectMQTT();
void mqttCallback(char* topic, byte* payload, unsigned int length);
void initHardware();
void verwerkKnopDruk();
void verwerkToF();
void updateBatterijLed();
uint8_t leesBatterijPercentage();
bool isUsbVerbonden();
void zetRgbKleur(uint8_t r, uint8_t g, uint8_t b);
void rgbLedUit();
void speelCorrectGeluid();
void speelIncorrectGeluid();
void speelVerbindingGeluid();
void speelOntwaakGeluid();
void zoemerToon(uint32_t freq, uint32_t duur);
void zoemerUit();
void gaaDiepeSlaap();

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
  connectWiFi();
  mqttClient.setServer(MQTT_BROKER, MQTT_PORT);
  mqttClient.setCallback(mqttCallback);
  mqttClient.setKeepAlive(MQTT_KEEPALIVE_DURATION);
  connectMQTT();
  laatsteActiviteitTijd = millis();
}

void loop() {
  // Check WiFi verbinding
  if (WiFi.status() != WL_CONNECTED) {
    connectWiFi();
  }

  // Check MQTT verbinding
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

  // Logica
  verwerkKnopDruk();

  if (isPolling) {
    verwerkToF();
  }

  // Batterij en LED updates
  if (millis() - laatsteLedUpdateTijd >= LED_UPDATE_INTERVAL) {
    laatsteLedUpdateTijd = millis();
    laatsteBatterijPercentage = leesBatterijPercentage();
    
    if (mqttClient.connected()) {
        String payload = String(laatsteBatterijPercentage);
        mqttClient.publish(topic_battery.c_str(), payload.c_str(), false);
    }
  }
  updateBatterijLed();

  // Slaap check
  if (millis() - laatsteActiviteitTijd > GLOBALE_INACTIEF_TIMEOUT_MS) {
    gaaDiepeSlaap();
  }

  yield();
}

void connectWiFi() {
  Serial.print("Verbinden met WiFi: ");
  Serial.println(WIFI_SSID);
  
  WiFi.mode(WIFI_STA);
  WiFi.setSleep(false); // Belangrijk voor performance
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print("."); 
    digitalWrite(PIN_LED_BLAUW, !digitalRead(PIN_LED_BLAUW));
  }
  
  Serial.println("");
  Serial.println("WiFi Verbonden!");
  Serial.print("IP Adres: ");
  Serial.println(WiFi.localIP());
  
  digitalWrite(PIN_LED_BLAUW, LOW);
}

bool connectMQTT() {
  String clientId = String("BM-") + DEVICE_COLOR + "-" + String(ESP.getEfuseMac(), HEX);
  
  // Last Will message: als hij crasht, stuurt de broker "offline"
  bool verbonden = mqttClient.connect(clientId.c_str(), topic_status.c_str(), 1, true, "offline");

  if (verbonden) {
    Serial.println("MQTT Verbonden!");
    mqttClient.subscribe(topic_cmd.c_str());
    mqttClient.subscribe(topic_cmd_all.c_str());
    mqttClient.publish(topic_status.c_str(), "online", true);
    speelVerbindingGeluid();
    return true;
  } else {
    Serial.print("MQTT Fout, rc=");
    Serial.println(mqttClient.state());
    return false;
  }
}

void mqttCallback(char* topic, byte* payload, unsigned int length) {
  String message = "";
  for (unsigned int i = 0; i < length; i++) message += (char)payload[i];
  
  Serial.print("Bericht ontvangen: ");
  Serial.println(message);

  laatsteActiviteitTijd = millis();

  if (message == "start") isPolling = true;
  else if (message == "stop") isPolling = false;
  else if (message == "correct") isCorrectTarget = true;
  else if (message == "incorrect") isCorrectTarget = false;
  else if (message == "sleep") gaaDiepeSlaap();
  else if (message == "sound_ok") speelCorrectGeluid();
  else if (message == "sound_fail") speelIncorrectGeluid();
}

void initHardware() {
  Serial.println("Hardware initialiseren...");

  // 1. Knoppen
  pinMode(PIN_KNOP, INPUT_PULLUP);
  attachInterrupt(digitalPinToInterrupt(PIN_KNOP), knopISR, FALLING);

  // 2. LED's
  ledcAttach(PIN_LED_ROOD, 5000, 8);
  ledcAttach(PIN_LED_GROEN, 5000, 8);
  ledcAttach(PIN_LED_BLAUW, 5000, 8);
  rgbLedUit();

  // 3. Zoemer
  ledcAttach(PIN_ZOEMER, ZOEMER_FREQ_STANDAARD, ZOEMER_RESOLUTIE);
  ledcWrite(PIN_ZOEMER, 0);

  // 4. Batterij ADC
  analogReadResolution(12);
  analogSetAttenuation(ADC_11db);

  // 5. I2C en Sensor (VL53L0X)
  Serial.println("- I2C Starten...");
  Wire.begin(PIN_I2C_SDA, PIN_I2C_SCL);
  Wire.setClock(400000);

  Serial.println("- Sensor zoeken...");
  tofSensor.setTimeout(500);
  
  if (!tofSensor.init()) {
    Serial.println("FOUT: Geen sensor gevonden! Check bedrading.");
    Serial.println("      (SDA=D4, SCL=D5)");
    tofGeinitialiseerd = false;
    // Rood knipperen ter waarschuwing
    for(int i=0; i<3; i++) { zetRgbKleur(255,0,0); delay(100); rgbLedUit(); delay(100); }
  } else {
    Serial.println("SUCCESS: Sensor gevonden en gestart.");
    tofSensor.setMeasurementTimingBudget(33000);
    tofSensor.startContinuous();
    tofGeinitialiseerd = true;
    // Groen knipperen ter bevestiging
    zetRgbKleur(0, 255, 0); delay(300); rgbLedUit();
  }
}

void verwerkKnopDruk() {
    if (!knopIngedrukt) return;
    if (millis() - laatsteKnopDrukTijd < KNOP_DEBOUNCE_MS) {
        knopIngedrukt = false;
        return;
    }
    Serial.println("Knop ingedrukt!");
    knopIngedrukt = false;
    laatsteKnopDrukTijd = millis();
    laatsteActiviteitTijd = millis();
}

void verwerkToF() {
    if (!tofGeinitialiseerd) return;

    if (millis() - laatsteTofPollTijd >= TOF_POLL_INTERVAL_MS) {
        laatsteTofPollTijd = millis();
        
        uint16_t afstand = tofSensor.readRangeContinuousMillimeters();
        if (tofSensor.timeoutOccurred()) { 
            // Serial.println("Sensor Timeout!"); 
            return; 
        }

        bool geldigeDetectie = (afstand > TOF_DETECTIE_MIN_MM && afstand < TOF_DETECTIE_MAX_MM);
        
        if (geldigeDetectie && (millis() - laatsteDetectieTijd >= TOF_DETECTIE_AFKOELING_MS)) {
            Serial.print("Detectie! Afstand: ");
            Serial.println(afstand);
            
            if (isCorrectTarget) speelCorrectGeluid();
            else speelIncorrectGeluid();

            String payload = String(afstand);
            mqttClient.publish(topic_detect.c_str(), payload.c_str(), false);

            laatsteDetectieTijd = millis();
            laatsteActiviteitTijd = millis();
        }
    }
}

float leesBatterijSpanningVanPin(int pin) {
    int adcWaarde = analogRead(pin);
    float spanning = (adcWaarde / 4095.0f) * 3.3f;
    spanning *= BATTERIJ_SPANNINGSDELER;
    return spanning;
}

uint8_t leesBatterijPercentage() {
    float v1 = leesBatterijSpanningVanPin(PIN_BATTERIJ_ADC_1);
    float v2 = leesBatterijSpanningVanPin(PIN_BATTERIJ_ADC_2);
    float spanning = (v1 + v2) / 2.0f; 

    float percentage = (spanning - BATTERIJ_LEEG_SPANNING) / (BATTERIJ_VOL_SPANNING - BATTERIJ_LEEG_SPANNING) * 100.0f;
    if (percentage > 100.0f) percentage = 100.0f;
    if (percentage < 0.0f) percentage = 0.0f;
    return (uint8_t)percentage;
}

bool isUsbVerbonden() {
    return (analogRead(PIN_USB_VBUS) > USB_VBUS_DREMPEL);
}

void zetRgbKleur(uint8_t r, uint8_t g, uint8_t b) {
    if (RGB_GEMEENSCHAPPELIJKE_ANODE) {
        r = 255 - r; g = 255 - g; b = 255 - b;
    }
    ledcWrite(PIN_LED_ROOD, r);
    ledcWrite(PIN_LED_GROEN, g);
    ledcWrite(PIN_LED_BLAUW, b);
}

void rgbLedUit() { zetRgbKleur(0, 0, 0); }

void updateBatterijLed() {
    usbVerbonden = isUsbVerbonden();

    if (isPolling && !usbVerbonden && laatsteBatterijPercentage > BATTERIJ_NIVEAU_LAAG) {
        if (isCorrectTarget) zetRgbKleur(0, 255, 0);
        else zetRgbKleur(255, 0, 0);
        return;
    }

    uint8_t r = 0, g = 0, b = 0;
    if (laatsteBatterijPercentage < BATTERIJ_NIVEAU_LAAG) { 
        r = 255; 
    } else if (laatsteBatterijPercentage < BATTERIJ_NIVEAU_MIDDEL) { 
        r = 255; g = 128; 
    } else { 
        g = 255; 
    }

    if (usbVerbonden) {
        if (millis() - laatsteOplaadKnipperTijd >= LED_OPLADEN_KNIPPEREN_MS) {
            laatsteOplaadKnipperTijd = millis();
            oplaadLedStatus = !oplaadLedStatus;
        }
        if (oplaadLedStatus) zetRgbKleur(r, g, b);
        else rgbLedUit();
    } else {
        zetRgbKleur(r, g, b);
    }
}

void zoemerToon(uint32_t freq, uint32_t duur) {
    ledcChangeFrequency(PIN_ZOEMER, freq, ZOEMER_RESOLUTIE);
    ledcWrite(PIN_ZOEMER, 127);
    delay(duur);
    zoemerUit();
}
void zoemerUit() { ledcWrite(PIN_ZOEMER, 0); }

void speelCorrectGeluid() {
    zoemerToon(1000, 100); delay(50); zoemerToon(1500, 100); delay(50); zoemerToon(2000, 150);
}
void speelIncorrectGeluid() {
    zoemerToon(400, 150); delay(50); zoemerToon(300, 150); delay(50); zoemerToon(200, 200);
}
void speelVerbindingGeluid() {
    zoemerToon(800, 100); delay(50); zoemerToon(1200, 150);
}
void speelOntwaakGeluid() {
    zoemerToon(500, 100); delay(30); zoemerToon(800, 100); delay(30); zoemerToon(1200, 120);
}

void gaaDiepeSlaap() {
    if (mqttClient.connected()) {
        mqttClient.publish(topic_status.c_str(), "sleeping", true);
        mqttClient.disconnect();
    }
    delay(100);
    
    zoemerUit();
    rgbLedUit();
    if (tofGeinitialiseerd) tofSensor.stopContinuous();

    esp_deep_sleep_enable_gpio_wakeup(BIT(PIN_KNOP), ESP_GPIO_WAKEUP_GPIO_LOW);
    esp_deep_sleep_start();
    if (mqttClient.connected()) {
      mqttClient.publish(topic_status.c_str(), "sleeping", true);
      mqttClient.disconnect();
    }
    delay(100);
    zoemerUit();
    rgbLedUit();
    if (tofGeinitialiseerd) tofSensor.stopContinuous();
    esp_deep_sleep_enable_gpio_wakeup(BIT(PIN_KNOP), ESP_GPIO_WAKEUP_GPIO_LOW);
    esp_deep_sleep_start();
}