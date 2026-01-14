#include <Arduino.h>
#include <BLEDevice.h>
#include <BLEUtils.h>
#include <BLEServer.h>
#include <BLE2902.h>
#include <Wire.h>
#include <VL53L0X.h>

const uint8_t APPARAAT_ID = 1;
const char* APPARAAT_NAMEN[] = {"BM-Blauw", "BM-Rood", "BM-Geel", "BM-Groen"};
const char* APPARAAT_NAAM = APPARAAT_NAMEN[APPARAAT_ID];

// GPIO Pinnen
const uint8_t PIN_KNOP = GPIO_NUM_3;  // RTC geschikt
const uint8_t PIN_BATTERIJ_ADC_1 = GPIO_NUM_2;
const uint8_t PIN_BATTERIJ_ADC_2 = GPIO_NUM_4;
const uint8_t PIN_ZOEMER = GPIO_NUM_5;
const uint8_t PIN_I2C_SDA = GPIO_NUM_6;
const uint8_t PIN_I2C_SCL = GPIO_NUM_7;


// USB Meting
const uint8_t PIN_USB_VBUS = GPIO_NUM_21;
const uint16_t USB_VBUS_DREMPEL = 2000;    // Spanningsdeler 10k/10k nodig


// LED
const uint8_t PIN_LED_ROOD = GPIO_NUM_8;
const uint8_t PIN_LED_GROEN = GPIO_NUM_9;
const uint8_t PIN_LED_BLAUW = GPIO_NUM_10;
const bool RGB_LED_GEMEENSCHAPPELIJKE_ANODE = false;


// PWM
const uint8_t ZOEMER_KANAAL = 0;
const uint8_t ZOEMER_RESOLUTIE = 8;
const uint16_t ZOEMER_FREQ_STANDAARD = 2000;
const uint16_t LED_PWM_FREQ = 5000;
const uint8_t LED_PWM_RESOLUTIE = 8;


// Batterijniveaus
const uint8_t BATTERIJ_NIVEAU_LAAG = 20;
const uint8_t BATTERIJ_NIVEAU_MIDDEL = 50;
const uint16_t LED_UPDATE_INTERVAL = 5000;
const uint16_t LED_OPLADEN_KNIPPEREN_MS = 500;


// Debug Configuratie
const bool DEBUG_UITGEBREID = false;
const bool DEBUG_SERIEEL = true;


// Timing
const unsigned long KNOP_DEBOUNCE_MS = 150;
const unsigned long ADVERTEREN_TIMEOUT_MS = (5UL * 60UL * 1000UL);
const unsigned long BATTERIJ_RAPPORT_INTERVAL = (5UL * 60UL * 1000UL);
const unsigned long KEEPALIVE_INTERVAL = (30UL * 1000UL);
const unsigned long GLOBALE_INACTIEF_TIMEOUT_MS = (10UL * 60UL * 1000UL);


// TOF Configuratie
const uint16_t TOF_POLL_INTERVAL_MS = 33;
const uint16_t TOF_DETECTIE_MIN_MM = 50;
const uint16_t TOF_DETECTIE_MAX_MM = 1000;
const uint16_t TOF_DETECTIE_AFKOELING_MS = 500;


// Batterij Configuratie
const uint8_t BATTERIJ_ADC_RESOLUTIE = 12;
const float BATTERIJ_SPANNINGSDELER = 2.0f;
const float BATTERIJ_VOL_SPANNING = 4.2f;
const float BATTERIJ_LEEG_SPANNING = 3.0f;
const bool BATTERIJ_GEBRUIK_GEMIDDELDE = true;


const char SERVICE_UUID[] = "beb5483e-36e1-4688-b7f5-ea07361b26a7";
const char CHAR_DATA_UUID[] = "beb5483e-36e1-4688-b7f5-ea07361b26a8";
const char CHAR_COMMAND_UUID[] = "beb5483e-36e1-4688-b7f5-ea07361b26a9";


const uint8_t VEILIGHEIDS_BYTE = 0x42;


// Bericht Type Hex
const uint8_t BERICHT_STATUS = 0x01;
const uint8_t BERICHT_DETECTIE = 0x02;
const uint8_t BERICHT_BATTERIJ = 0x03;
const uint8_t BERICHT_KEEPALIVE = 0x04;


// Commando Type Hex
const uint8_t CMD_START = 0x01;
const uint8_t CMD_STOP = 0x02;
const uint8_t CMD_SLAAP = 0x03;
const uint8_t CMD_GELUID_CORRECT = 0x10;
const uint8_t CMD_GELUID_INCORRECT = 0x11;


// Status Types Hex
const uint8_t STATUS_VERBONDEN = 0x01;
const uint8_t STATUS_HERVERBONDEN = 0x02;
const uint8_t STATUS_SLAAPT = 0x03;
const uint8_t STATUS_PONG = 0x04;


enum class SystemState : uint8_t {
    INIT,
    ADVERTISING,
    CONNECTED,
    POLLING,
    ENTERING_SLEEP
};


enum class RpiCommand : uint8_t {
    GEEN = 0,
    START = CMD_START,
    STOP = CMD_STOP,
    SLAAP = CMD_SLAAP,
    GELUID_CORRECT = CMD_GELUID_CORRECT,
    GELUID_INCORRECT = CMD_GELUID_INCORRECT
};


volatile SystemState huidigeStatus = SystemState::INIT;
volatile SystemState vorigeStatus = SystemState::INIT;


// Timing Variabelen in Milliseconden
unsigned long statusStartTijd = 0;
unsigned long laatsteBatterijRapportTijd = 0;
unsigned long laatsteKeepaliveTijd = 0;
unsigned long laatsteTofPollTijd = 0;
unsigned long laatsteActiviteitTijd = 0;


// BLE Objecten (pointers vereist door BLE bibliotheek)
BLEServer* bleServer;
BLECharacteristic* charData;
BLECharacteristic* charCommando;
BLEAdvertising* bleAdverteren;


// Verbindingsstatus, RPI verandert dit
volatile bool bleVerbonden = false;
volatile bool nieuwCommandoOntvangen = false;


// Commando Status
RpiCommand wachtendCommando = RpiCommand::GEEN;
uint8_t ontvangencorrecteKegel = 0xFF; // 0xFF = geen waarde


// Hardware
VL53L0X tofSensor;
bool tofGeinitialiseerd = false;
uint16_t laatsteDetectieAfstand = 0;
unsigned long laatsteDetectieTijd = 0;
bool objectInVeld = false;


// USB & Opladen 
bool rgbGemeenschappelijkeAnode = false;
volatile bool usbVerbonden = false;
unsigned long laatsteLedUpdateTijd = 0;
unsigned long laatsteOplaadKnipperTijd = 0;
bool oplaadLedStatus = false;
uint8_t laatsteBatterijPercentage = 0;


// Ontwaken-Knop 
volatile bool knopIngedrukt = false;
unsigned long laatsteKnopDrukTijd = 0;


// Status Functies
void veranderNaarStatus(SystemState nieuweStatus);
void verwerkStatusInit();
void verwerkStatusAdverteren();
void verwerkStatusVerbonden();
void verwerkStatusPollen();
void verwerkStatusNaarSlaap();


// BLE Functies
void initBLE();
void startAdverteren();
void stopAdverteren();
void stuurStatusBericht(uint8_t statusGebeurtenis);
void stuurDetectieBericht(uint16_t afstand);
void stuurBatterijBericht(uint8_t batterijPercentage);
void stuurKeepaliveBericht();


// Hardware Functies
void initHardware();
void initTofSensor();
void initZoemer();
void initRgbLed();
void initKnop();
uint16_t leesTofAfstand();
bool isObjectGedetecteerd();
uint8_t leesBatterijPercentage();
float leesBatterijSpanning(bool gebruikGemiddelde = BATTERIJ_GEBRUIK_GEMIDDELDE);
void verwerkKnopDruk();


// USB & Opladen Functies
bool isUsbVerbonden();
void updateOplaadStatus();


// RGB LED Functies
void zetRgbKleur(uint8_t rood, uint8_t groen, uint8_t blauw);
void updateBatterijLed();
void toonBatterijNiveau(uint8_t percentage, bool aanHetOpladen);
void rgbLedUit();


// Geluid Functies
void speelCorrectGeluid();
void speelIncorrectGeluid();
void speelVerbindingGeluid();
void speelVerbreekGeluid();
void speelOntwaakGeluid();
void zoemerToon(uint32_t frequentie, uint32_t duur);
void zoemerUit();


void gaaDiepeSlaap();


void logStatus(const char* bericht);


class ServerCallbacks : public BLEServerCallbacks {
    void onConnect(BLEServer* server) override {
        bleVerbonden = true;
        laatsteActiviteitTijd = millis();
        speelVerbindingGeluid();
    }

    void onDisconnect(BLEServer* server) override {
        bleVerbonden = false;
        speelVerbreekGeluid();
        
        if (huidigeStatus != SystemState::ENTERING_SLEEP) {
            veranderNaarStatus(SystemState::ADVERTISING);
        }
    }
};


// BLE Inkomende Commando's
class CommandCallbacks : public BLECharacteristicCallbacks {
    void onWrite(BLECharacteristic* characteristic) override {
        String waarde = characteristic->getValue();
        Serial.printf("[BLE] Ontvangen Commando: %s\n", waarde.c_str());
        
        if (waarde.length() > 0) {
            uint8_t cmd = (uint8_t)waarde[0];
            
            if (waarde.length() > 1) {
                ontvangencorrecteKegel = (uint8_t)waarde[1];
            } else {
                ontvangencorrecteKegel = 0xFF;
                Serial.println();
            }
            
            wachtendCommando = static_cast<RpiCommand>(cmd);
            nieuwCommandoOntvangen = true;
            laatsteActiviteitTijd = millis();
        }
    }
};


void setup() {
    Serial.begin(115200);
    delay(100);

    esp_sleep_wakeup_cause_t ontwaakOorzaak = esp_sleep_get_wakeup_cause();
    
    initHardware();
    initBLE();
    
    if (ontwaakOorzaak == ESP_SLEEP_WAKEUP_GPIO) {
        speelOntwaakGeluid();
    }
    
    statusStartTijd = millis();
    laatsteActiviteitTijd = millis();
    
    veranderNaarStatus(SystemState::ADVERTISING);
}


void loop() {
    if (millis() - laatsteActiviteitTijd > GLOBALE_INACTIEF_TIMEOUT_MS) {
        veranderNaarStatus(SystemState::ENTERING_SLEEP);
    }
    
    switch (huidigeStatus) {
        case SystemState::INIT:
            verwerkStatusInit();
            break;
            
        case SystemState::ADVERTISING:
            verwerkStatusAdverteren();
            break;
            
        case SystemState::CONNECTED:
            verwerkStatusVerbonden();
            break;
            
        case SystemState::POLLING:
            verwerkStatusPollen();
            break;
            
        case SystemState::ENTERING_SLEEP:
            verwerkStatusNaarSlaap();
            break;
    }
    
    // Update batterij LED
    if (millis() - laatsteLedUpdateTijd >= LED_UPDATE_INTERVAL) {
        laatsteLedUpdateTijd = millis();
        laatsteBatterijPercentage = leesBatterijPercentage();
    }

    // Update LED altijd voor opladen en knipper
    updateBatterijLed();
    verwerkKnopDruk();
    
    // CPU tijd geven, anders miserie met BLE
    yield();
}


// Transitie en timing
void veranderNaarStatus(SystemState nieuweStatus) {
    if (huidigeStatus == nieuweStatus) return;
    
    vorigeStatus = huidigeStatus;
    huidigeStatus = nieuweStatus;
    statusStartTijd = millis();
}


void verwerkStatusInit() {
    veranderNaarStatus(SystemState::ADVERTISING);
}


void verwerkStatusAdverteren() {
    if (millis() - statusStartTijd > ADVERTEREN_TIMEOUT_MS) {
        veranderNaarStatus(SystemState::ENTERING_SLEEP);
        return;
    }
    
    if (vorigeStatus != SystemState::ADVERTISING) {
        startAdverteren();
    }
    
    if (bleVerbonden) {
        veranderNaarStatus(SystemState::CONNECTED);
    }
}


void verwerkStatusVerbonden() {
    if (!bleVerbonden) {
        veranderNaarStatus(SystemState::ADVERTISING);
        return;
    }
    
    // Stuur batterij % bij verbinding & elke xm
    if (millis() - statusStartTijd >= 600) {
        if (laatsteBatterijRapportTijd == 0 || 
            (millis() - laatsteBatterijRapportTijd >= BATTERIJ_RAPPORT_INTERVAL)) {
            uint8_t batterijPercentage = leesBatterijPercentage();
            stuurBatterijBericht(batterijPercentage);
            laatsteBatterijRapportTijd = millis();
        }
    }
    
    // Keep-alive
    if (millis() - laatsteKeepaliveTijd >= KEEPALIVE_INTERVAL) {
        stuurKeepaliveBericht();
        laatsteKeepaliveTijd = millis();
    }
    
    if (nieuwCommandoOntvangen) {
        nieuwCommandoOntvangen = false;
        laatsteActiviteitTijd = millis();
        
        switch (wachtendCommando) {
            case RpiCommand::START:
                veranderNaarStatus(SystemState::POLLING);
                break;
                
            case RpiCommand::STOP:
                break;
                
            case RpiCommand::SLAAP:
                veranderNaarStatus(SystemState::ENTERING_SLEEP);
                break;
                                
            case RpiCommand::GELUID_CORRECT:
                speelCorrectGeluid();
                break;
                
            case RpiCommand::GELUID_INCORRECT:
                speelIncorrectGeluid();
                break;
                
            default:
                break;
        }
        
        wachtendCommando = RpiCommand::GEEN;
    }
}

void verwerkStatusPollen() {
    if (!bleVerbonden) {
        veranderNaarStatus(SystemState::ADVERTISING);
        return;
    }

    if (nieuwCommandoOntvangen) {
        nieuwCommandoOntvangen = false;
        laatsteActiviteitTijd = millis();
        
        switch (wachtendCommando) {
            case RpiCommand::STOP:
                veranderNaarStatus(SystemState::CONNECTED);
                wachtendCommando = RpiCommand::GEEN;
                return;
            case RpiCommand::SLAAP:
                veranderNaarStatus(SystemState::ENTERING_SLEEP);
                wachtendCommando = RpiCommand::GEEN;
                return;
            case RpiCommand::GELUID_CORRECT: speelCorrectGeluid(); break;
            case RpiCommand::GELUID_INCORRECT: speelIncorrectGeluid(); break;
            default: break;
        }
        wachtendCommando = RpiCommand::GEEN;
    }

    if (millis() - laatsteTofPollTijd >= TOF_POLL_INTERVAL_MS) {
        laatsteTofPollTijd = millis();

        uint16_t afstand = leesTofAfstand();
        
        bool geldgeMeting = (afstand < 2000 && afstand > 0);

        if (geldgeMeting && afstand > TOF_DETECTIE_MIN_MM && afstand < TOF_DETECTIE_MAX_MM) {
            
            if (!objectInVeld && (millis() - laatsteDetectieTijd >= TOF_DETECTIE_AFKOELING_MS)) {
                                
                // Speel geluid op basis of dit de correcte kegel is
                // ontvangencorrecteKegel is 1 als dit apparaat correct is, 0 als fout
                if (ontvangencorrecteKegel == 1) {
                    speelCorrectGeluid();
                } else {
                    speelIncorrectGeluid();
                }
                
                stuurDetectieBericht(afstand);
                
                laatsteActiviteitTijd = millis();
                laatsteDetectieTijd = millis();
                objectInVeld = true;
                
                // Stop automatisch met pollen na detectie (one-shot)
                veranderNaarStatus(SystemState::CONNECTED);
                return;
            }
        } else {
            if (afstand > TOF_DETECTIE_MAX_MM || afstand > 2000) {
                objectInVeld = false;
            }
        }
    }

    if (millis() - laatsteBatterijRapportTijd >= BATTERIJ_RAPPORT_INTERVAL) {
        uint8_t batterijPercentage = leesBatterijPercentage();
        stuurBatterijBericht(batterijPercentage);
        laatsteBatterijRapportTijd = millis();
    }
    
    if (millis() - laatsteKeepaliveTijd >= KEEPALIVE_INTERVAL) {
        stuurKeepaliveBericht();
        laatsteKeepaliveTijd = millis();
    }
}

void verwerkStatusNaarSlaap() {
    
    if (bleVerbonden) {
        stuurStatusBericht(STATUS_SLAAPT);
        delay(100); // Vertraging voor bericht
    }
    
    stopAdverteren();
    if (bleVerbonden) {
        // Verbreek verbinding met BLE client voor slapen
        bleServer->disconnect(bleServer->getConnId());
    }
    
    zoemerUit();
    
    rgbLedUit();
    
    if (tofGeinitialiseerd) {
        tofSensor.stopContinuous();
    }
    
    // Opruim vertraging
    delay(100);
    
    gaaDiepeSlaap();
}

void initBLE() {    
    BLEDevice::init(APPARAAT_NAAM);

//  Setup BLE beveiliging (vereist door bibliotheek om pointers te gebruiken)
    BLESecurity* beveiliging = new BLESecurity();
    beveiliging->setAuthenticationMode(ESP_LE_AUTH_BOND);  // Change: Remove _REQ_SC
    beveiliging->setCapability(ESP_IO_CAP_NONE);
    beveiliging->setKeySize(16);
    // Maak BLE server en service aan (bibliotheek geeft pointers terug)
    bleServer = BLEDevice::createServer();
    bleServer->setCallbacks(new ServerCallbacks());
    
    BLEService* dienst = bleServer->createService(SERVICE_UUID);
    
    // Maak data characteristic aan voor verzenden sensordata
    charData = dienst->createCharacteristic(
        CHAR_DATA_UUID,
        BLECharacteristic::PROPERTY_READ | 
        BLECharacteristic::PROPERTY_NOTIFY
    );
    charData->addDescriptor(new BLE2902());

    // Maak commando characteristic aan voor ontvangen commando's
    charCommando = dienst->createCharacteristic(
        CHAR_COMMAND_UUID,
        BLECharacteristic::PROPERTY_WRITE
    );
    charCommando->setCallbacks(new CommandCallbacks());
    
    dienst->start();
    
    // Setup advertising
    bleAdverteren = BLEDevice::getAdvertising();
    bleAdverteren->addServiceUUID(SERVICE_UUID);
    bleAdverteren->setScanResponse(true);
    bleAdverteren->setMinPreferred(0x06);
    bleAdverteren->setMinPreferred(0x12);
    
}

void startAdverteren() {
    BLEDevice::startAdvertising();
    Serial.printf("[BLE] Start adverteren %s\n", APPARAAT_NAAM);
}

void stopAdverteren() {
    bleAdverteren->stop();
}

// Formaat: [type(1)][apparaat_id(1)][magic(1)][gereserveerd(1)][timestamp(4)][status_gebeurtenis(1)][opvulling(3)]
void stuurStatusBericht(uint8_t statusGebeurtenis) {
    if (!bleVerbonden) return;
    
    uint8_t bericht[12] = {0};
    uint32_t timestamp = millis();
    
    bericht[0] = BERICHT_STATUS;
    bericht[1] = APPARAAT_ID;
    bericht[2] = VEILIGHEIDS_BYTE;
    bericht[3] = 0;
    // Kopieer timestamp bytes handmatig (bytes 4-7)
    bericht[4] = timestamp & 0xFF;
    bericht[5] = (timestamp >> 8) & 0xFF;
    bericht[6] = (timestamp >> 16) & 0xFF;
    bericht[7] = (timestamp >> 24) & 0xFF;
    bericht[8] = statusGebeurtenis;
    
    charData->setValue(bericht, 12);
    charData->notify();
}

// Formaat: [type(1)][apparaat_id(1)][magic(1)][gereserveerd(1)][timestamp(4)][afstand_mm(2)][opvulling(2)]
void stuurDetectieBericht(uint16_t afstand) {
    if (!bleVerbonden) return;
    
    uint8_t bericht[12] = {0};
    uint32_t timestamp = millis();
    
    bericht[0] = BERICHT_DETECTIE;
    bericht[1] = APPARAAT_ID;
    bericht[2] = VEILIGHEIDS_BYTE;
    bericht[3] = 0;
    // Kopieer timestamp bytes handmatig (bytes 4-7)
    bericht[4] = timestamp & 0xFF;
    bericht[5] = (timestamp >> 8) & 0xFF;
    bericht[6] = (timestamp >> 16) & 0xFF;
    bericht[7] = (timestamp >> 24) & 0xFF;
    // Kopieer afstand bytes handmatig (bytes 8-9)
    bericht[8] = afstand & 0xFF;
    bericht[9] = (afstand >> 8) & 0xFF;
    
    charData->setValue(bericht, 12);
    charData->notify();
}

// Formaat: [type(1)][apparaat_id(1)][magic(1)][gereserveerd(1)][timestamp(4)][batterij_percentage(1)][opvulling(3)]
void stuurBatterijBericht(uint8_t batterijPercentage) {
    if (!bleVerbonden) return;
    
    uint8_t bericht[12] = {0};
    uint32_t timestamp = millis();
    
    bericht[0] = BERICHT_BATTERIJ;
    bericht[1] = APPARAAT_ID;
    bericht[2] = VEILIGHEIDS_BYTE;
    bericht[3] = 0;
    // Kopieer timestamp bytes handmatig (bytes 4-7)
    bericht[4] = timestamp & 0xFF;
    bericht[5] = (timestamp >> 8) & 0xFF;
    bericht[6] = (timestamp >> 16) & 0xFF;
    bericht[7] = (timestamp >> 24) & 0xFF;
    bericht[8] = batterijPercentage;
    
    charData->setValue(bericht, 12);
    charData->notify();
    
    Serial.printf("[BLE] Verzonden BATTERIJ: %d%%\n", batterijPercentage);
}

// Formaat: [type(1)][apparaat_id(1)][magic(1)][gereserveerd(1)][timestamp(4)]
void stuurKeepaliveBericht() {
    if (!bleVerbonden) return;
    
    uint8_t bericht[8] = {0};
    uint32_t timestamp = millis();
    
    bericht[0] = BERICHT_KEEPALIVE;
    bericht[1] = APPARAAT_ID;
    bericht[2] = VEILIGHEIDS_BYTE;
    bericht[3] = 0;
    // Kopieer timestamp bytes handmatig (bytes 4-7)
    bericht[4] = timestamp & 0xFF;
    bericht[5] = (timestamp >> 8) & 0xFF;
    bericht[6] = (timestamp >> 16) & 0xFF;
    bericht[7] = (timestamp >> 24) & 0xFF;
    
    charData->setValue(bericht, 8);
    charData->notify();
}

void initHardware() {
    Serial.println("[HW] Initialiseren hardware");
    
    analogReadResolution(BATTERIJ_ADC_RESOLUTIE);
    analogSetAttenuation(ADC_11db);
    
    Wire.begin(PIN_I2C_SDA, PIN_I2C_SCL);
    
    initKnop();
    initZoemer();
    initRgbLed();
    initTofSensor();
    
    updateOplaadStatus();
    
    laatsteBatterijPercentage = leesBatterijPercentage();
    updateBatterijLed();
    
    Serial.println("[HW] Initialisatie voltooid");
}

// [HERSTELD VOOR VL53L0X MAAR SNELLER]
void initTofSensor() {
    Serial.println("[TOF] Initialiseren VL53L0X (Hoge Snelheid)");
    
    Wire.setClock(400000); // 400kHz I2C
    
    tofSensor.setTimeout(500);
    
    if (!tofSensor.init()) {
        Serial.println("[TOF] VL53L0X init mislukt");
        tofGeinitialiseerd = false;
        return;
    }

    // Polling snelheid    
    tofSensor.setMeasurementTimingBudget(33000);

    tofSensor.startContinuous();

    tofGeinitialiseerd = true;
    Serial.println("[TOF] VL53L0X geinitialiseerd (Budget: 33ms)");
}

void initZoemer() {
    Serial.println("[ZOEMER] Initialiseren PWM");
    
    ledcAttach(PIN_ZOEMER, ZOEMER_FREQ_STANDAARD, ZOEMER_RESOLUTIE);
    ledcWrite(PIN_ZOEMER, 0);
    
    Serial.println("[ZOEMER] PWM geinitialiseerd");
}

void initRgbLed() {
    Serial.println("[RGB] Initialiseren RGB LED");
    
    ledcAttach(PIN_LED_ROOD, LED_PWM_FREQ, LED_PWM_RESOLUTIE);
    ledcAttach(PIN_LED_GROEN, LED_PWM_FREQ, LED_PWM_RESOLUTIE);
    ledcAttach(PIN_LED_BLAUW, LED_PWM_FREQ, LED_PWM_RESOLUTIE);
    
    rgbLedUit();
    
    Serial.println("[RGB] RGB LED geinitialiseerd");
}

void IRAM_ATTR knopISR() {
    knopIngedrukt = true;
}

void initKnop() {
    Serial.println("[KNOP] Initialiseren knop");
    
    pinMode(PIN_KNOP, INPUT_PULLUP);
    attachInterrupt(digitalPinToInterrupt(PIN_KNOP), knopISR, FALLING);
    
    Serial.println("[KNOP] Knop geinitialiseerd");
}

void verwerkKnopDruk() {
    if (!knopIngedrukt) return;
    
    if (millis() - laatsteKnopDrukTijd < KNOP_DEBOUNCE_MS) {
        knopIngedrukt = false;
        return;
    }
    
    knopIngedrukt = false;
    laatsteKnopDrukTijd = millis();
    laatsteActiviteitTijd = millis();
    
    Serial.println("[KNOP] Knop ingedrukt");
}

// [HERSTELD] Simpele uitlezing voor L0X zonder buffer
uint16_t leesTofAfstand() {
    if (!tofGeinitialiseerd) return 9999;
    
    // Lees continue data
    uint16_t afstand = tofSensor.readRangeContinuousMillimeters();
    
    if (tofSensor.timeoutOccurred()) {
        // Serial.println("[TOF] Timeout");
        return 9999;
    }
    
    return afstand;
}

bool isObjectGedetecteerd() {
    uint16_t afstand = leesTofAfstand();
    
    return (afstand < TOF_DETECTIE_MAX_MM && afstand > TOF_DETECTIE_MIN_MM);
}

float leesBatterijSpanningVanPin(int pin) {
    int adcWaarde = analogRead(pin);
    
    float spanning = (adcWaarde / 4095.0f) * 3.3f;
    
    spanning *= BATTERIJ_SPANNINGSDELER;
    
    return spanning;
}

float leesBatterijSpanning(bool gebruikGemiddelde) {
    float v1 = leesBatterijSpanningVanPin(PIN_BATTERIJ_ADC_1);
    float v2 = leesBatterijSpanningVanPin(PIN_BATTERIJ_ADC_2);

    if (gebruikGemiddelde) {
        return (v1 + v2) / 2.0f;
    } else {
        return (v1 < v2) ? v1 : v2;
    }
}

uint8_t leesBatterijPercentage() {
    float spanning = leesBatterijSpanning();
    
    float percentage = (spanning - BATTERIJ_LEEG_SPANNING) / 
        (BATTERIJ_VOL_SPANNING - BATTERIJ_LEEG_SPANNING) * 100.0f;
    
    if (percentage > 100.0f) percentage = 100.0f;
    if (percentage < 0.0f) percentage = 0.0f;
    
    Serial.printf("[BATTERIJ] Spanning: %.2fV, Percentage: %.0f%%\n", spanning, percentage);
    
    return (uint8_t)percentage;
}

// Hardware: 5V VBUS -> spanningsdeler: 10k/10k -> GPIO2
bool isUsbVerbonden() {
    int adcWaarde = analogRead(PIN_USB_VBUS);
    
    return (adcWaarde > USB_VBUS_DREMPEL);
}

void updateOplaadStatus() {
    bool wasVerbonden = usbVerbonden;
    usbVerbonden = isUsbVerbonden();
    
    if (usbVerbonden != wasVerbonden) {
        if (usbVerbonden) {
            Serial.println("[USB] USB verbonden, aan het opladen");
        } else {
            Serial.println("[USB] USB verbroken, op batterij");
        }
    }
}

void zetRgbKleur(uint8_t r, uint8_t g, uint8_t b) {
    if (rgbGemeenschappelijkeAnode) {
        r = 255 - r; g = 255 - g; b = 255 - b;
    }
    ledcWrite(PIN_LED_ROOD, r);
    ledcWrite(PIN_LED_GROEN, g);
    ledcWrite(PIN_LED_BLAUW, b);
}

void rgbLedUit() {
    zetRgbKleur(0, 0, 0);
}

void toonBatterijNiveau(uint8_t percentage, bool aanHetOpladen) {
    uint8_t rood = 0, groen = 0, blauw = 0;
    
    if (percentage < BATTERIJ_NIVEAU_LAAG) {
        // LAAG: Rood
        rood = 255;
        groen = 0;
        blauw = 0;
    } else if (percentage < BATTERIJ_NIVEAU_MIDDEL) {
        // MIDDEL: Geel/Oranje, als niet duidelijk verander naar blauw
        rood = 255;
        groen = 128;
        blauw = 0;
    } else {
        // HOOG: Groen
        rood = 0;
        groen = 255;
        blauw = 0;
    }
    
    // Als aan het opladen, knipperen
    if (aanHetOpladen) {
        if (millis() - laatsteOplaadKnipperTijd >= LED_OPLADEN_KNIPPEREN_MS) {
            laatsteOplaadKnipperTijd = millis();
            oplaadLedStatus = !oplaadLedStatus;
        }
        
        if (oplaadLedStatus) {
            zetRgbKleur(rood, groen, blauw);
        } else {
            rgbLedUit();
        }
    } else {
        // Niet aan het opladen: vast
        zetRgbKleur(rood, groen, blauw);
    }
}

void updateBatterijLed() {
    updateOplaadStatus();

    toonBatterijNiveau(laatsteBatterijPercentage, usbVerbonden);
}

void speelCorrectGeluid() {
    Serial.println("[ZOEMER] Spelen CORRECT geluid");
    
    zoemerToon(1000, 100);
    delay(50);
    zoemerToon(1500, 100);
    delay(50);
    zoemerToon(2000, 150);
    zoemerUit();
}

void speelIncorrectGeluid() {
    Serial.println("[ZOEMER] Spelen INCORRECT geluid");
    
    zoemerToon(400, 150);
    delay(50);
    zoemerToon(300, 150);
    delay(50);
    zoemerToon(200, 200);
    zoemerUit();
}

void speelVerbindingGeluid() {
    Serial.println("[ZOEMER] Spelen verbinding geluid");
    
    zoemerToon(800, 100);
    delay(50);
    zoemerToon(1200, 150);
    zoemerUit();
}

void speelVerbreekGeluid() {
    Serial.println("[ZOEMER] Spelen verbreek geluid");
    
    zoemerToon(600, 150);
    delay(50);
    zoemerToon(400, 200);
    zoemerUit();
}

void speelOntwaakGeluid() {
    Serial.println("[ZOEMER] Spelen ontwaak geluid");
    
    zoemerToon(500, 100);
    delay(30);
    zoemerToon(800, 100);
    delay(30);
    zoemerToon(1200, 120);
    zoemerUit();
}

void zoemerToon(uint32_t frequentie, uint32_t duur) {
    ledcChangeFrequency(PIN_ZOEMER, frequentie, ZOEMER_RESOLUTIE);
    ledcWrite(PIN_ZOEMER, 127);
    delay(duur);
    zoemerUit();
}

void zoemerUit() {
    ledcWrite(PIN_ZOEMER, 0);
}

void gaaDiepeSlaap() {
    Serial.println("\n[SLAAP] Starten diepe slaap setup");
    Serial.flush(); // Zorg dat data verzonden is
    
    esp_deep_sleep_enable_gpio_wakeup(BIT(PIN_KNOP), ESP_GPIO_WAKEUP_GPIO_LOW);
    
    BLEDevice::deinit(false);
    
    esp_deep_sleep_start();
}

void logStatus(const char* bericht) {
    Serial.printf("[DEBUG] %s (Status: %d, Verbonden: %d)\n", 
                  bericht, 
                  static_cast<uint8_t>(huidigeStatus), 
                  bleVerbonden);
}