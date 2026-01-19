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

const uint8_t PIN_KNOP = GPIO_NUM_3;  // RTC geschikt
const uint8_t PIN_BATTERIJ_ADC_1 = GPIO_NUM_2;
const uint8_t PIN_BATTERIJ_ADC_2 = GPIO_NUM_4;
const uint8_t PIN_ZOEMER = GPIO_NUM_5;
const uint8_t PIN_I2C_SDA = GPIO_NUM_6;
const uint8_t PIN_I2C_SCL = GPIO_NUM_7;

const uint8_t PIN_USB_VBUS = GPIO_NUM_21;
const uint16_t USB_VBUS_DREMPEL = 2000;    // Spanningsdeler 10k/10k nodig

const uint8_t PIN_LED_ROOD = GPIO_NUM_8;
const uint8_t PIN_LED_GROEN = GPIO_NUM_9;
const uint8_t PIN_LED_BLAUW = GPIO_NUM_10;
const bool RGB_LED_GEMEENSCHAPPELIJKE_ANODE = false;

const uint8_t ZOEMER_KANAAL = 0;
const uint8_t ZOEMER_RESOLUTIE = 8;
const uint16_t ZOEMER_FREQ_STANDAARD = 2000;
const uint16_t LED_PWM_FREQ = 5000;
const uint8_t LED_PWM_RESOLUTIE = 8;

const uint8_t BATTERIJ_NIVEAU_LAAG = 20;
const uint8_t BATTERIJ_NIVEAU_MIDDEL = 50;
const uint16_t LED_UPDATE_INTERVAL = 5000;
const uint16_t LED_OPLADEN_KNIPPEREN_MS = 500;

const unsigned long KNOP_DEBOUNCE_MS = 150;
const unsigned long ADVERTEREN_TIMEOUT_MS = (5UL * 60UL * 1000UL);
const unsigned long GLOBALE_INACTIEF_TIMEOUT_MS = (30UL * 60UL * 1000UL);  // 30 min

const uint16_t TOF_POLL_INTERVAL_MS = 33;
const uint16_t TOF_DETECTIE_MIN_MM = 50;
const uint16_t TOF_DETECTIE_MAX_MM = 1000;
const uint16_t TOF_DETECTIE_AFKOELING_MS = 500;

const uint8_t BATTERIJ_ADC_RESOLUTIE = 12;
const float BATTERIJ_SPANNINGSDELER = 2.0f;
const float BATTERIJ_VOL_SPANNING = 4.2f;
const float BATTERIJ_LEEG_SPANNING = 3.0f;
const bool BATTERIJ_GEBRUIK_GEMIDDELDE = true;

const char SERVICE_UUID[] = "beb5483e-36e1-4688-b7f5-ea07361b26a7";
const char CHAR_DATA_UUID[] = "beb5483e-36e1-4688-b7f5-ea07361b26a8";
const char CHAR_COMMAND_UUID[] = "beb5483e-36e1-4688-b7f5-ea07361b26a9";

const uint8_t VEILIGHEIDS_BYTE = 0x42;

const uint8_t BERICHT_STATUS = 0x01;
const uint8_t BERICHT_DETECTIE = 0x02;
const uint8_t BERICHT_BATTERIJ = 0x03;

const uint8_t CMD_START = 0x01;
const uint8_t CMD_STOP = 0x02;
const uint8_t CMD_SLAAP = 0x03;
const uint8_t CMD_KEEPALIVE = 0x05;
const uint8_t CMD_GELUID_CORRECT = 0x10;
const uint8_t CMD_GELUID_INCORRECT = 0x11;

// Status Types Hex
const uint8_t STATUS_VERBONDEN = 0x01;
const uint8_t STATUS_HERVERBONDEN = 0x02;
const uint8_t STATUS_SLAAPT = 0x03;

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
    KEEPALIVE = CMD_KEEPALIVE,
    GELUID_CORRECT = CMD_GELUID_CORRECT,
    GELUID_INCORRECT = CMD_GELUID_INCORRECT
};

volatile SystemState huidigeStatus = SystemState::INIT;
volatile SystemState vorigeStatus = SystemState::INIT;

unsigned long statusStartTijd = 0;
unsigned long laatsteTofPollTijd = 0;
unsigned long laatsteActiviteitTijd = 0;

BLEServer* bleServer;
BLECharacteristic* charData;
BLECharacteristic* charCommando;
BLEAdvertising* bleAdverteren;

volatile bool bleVerbonden = false;
volatile bool nieuwCommandoOntvangen = false;

RpiCommand wachtendCommando = RpiCommand::GEEN;
uint8_t ontvangencorrecteKegel = 0xFF; // 0xFF = geen waarde

VL53L0X tofSensor;
bool tofGeinitialiseerd = false;
uint16_t laatsteDetectieAfstand = 0;
unsigned long laatsteDetectieTijd = 0;
bool objectInVeld = false;

bool rgbGemeenschappelijkeAnode = false;
volatile bool usbVerbonden = false;
unsigned long laatsteLedUpdateTijd = 0;
unsigned long laatsteOplaadKnipperTijd = 0;
bool oplaadLedStatus = false;
uint8_t laatsteBatterijPercentage = 0;

volatile bool knopIngedrukt = false;
unsigned long laatsteKnopDrukTijd = 0;

void veranderNaarStatus(SystemState nieuweStatus);
void verwerkStatusInit();
void verwerkStatusAdverteren();
void verwerkStatusVerbonden();
void verwerkStatusPollen();
void verwerkStatusNaarSlaap();

void initBLE();
void startAdverteren();
void stopAdverteren();
void stuurStatusBericht(uint8_t statusGebeurtenis);
void stuurDetectieBericht(uint16_t afstand);
void stuurBatterijBericht(uint8_t batterijPercentage);

void initHardware();
void initTofSensor();
void initZoemer();
void initRgbLed();
void initKnop();
uint16_t leesTofAfstand();
uint8_t leesBatterijPercentage();
float leesBatterijSpanning(bool gebruikGemiddelde = BATTERIJ_GEBRUIK_GEMIDDELDE);
void verwerkKnopDruk();

bool isUsbVerbonden();
void updateOplaadStatus();

void zetRgbKleur(uint8_t rood, uint8_t groen, uint8_t blauw);
void updateBatterijLed();
void toonBatterijNiveau(uint8_t percentage, bool aanHetOpladen);
void rgbLedUit();

void speelCorrectGeluid();
void speelIncorrectGeluid();
void speelVerbindingGeluid();
void speelVerbreekGeluid();
void speelOntwaakGeluid();
void zoemerToon(uint32_t frequentie, uint32_t duur);
void zoemerUit();

void gaaDiepeSlaap();

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
        
        if (waarde.length() > 0) {
            uint8_t cmd = (uint8_t)waarde[0];
            
            if (waarde.length() > 1) {
                ontvangencorrecteKegel = (uint8_t)waarde[1];
            } else {
                ontvangencorrecteKegel = 0xFF;
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
            
            case RpiCommand::KEEPALIVE:
                stuurBatterijBericht(leesBatterijPercentage());
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
            case RpiCommand::KEEPALIVE:
                stuurBatterijBericht(leesBatterijPercentage());
                break;
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

    BLESecurity* beveiliging = new BLESecurity();
    beveiliging->setAuthenticationMode(ESP_LE_AUTH_BOND);
    beveiliging->setCapability(ESP_IO_CAP_NONE);
    beveiliging->setKeySize(16);
    
    bleServer = BLEDevice::createServer();
    bleServer->setCallbacks(new ServerCallbacks());
    
    BLEService* dienst = bleServer->createService(SERVICE_UUID);
    
    charData = dienst->createCharacteristic(
        CHAR_DATA_UUID,
        BLECharacteristic::PROPERTY_READ | 
        BLECharacteristic::PROPERTY_NOTIFY
    );
    charData->addDescriptor(new BLE2902());

    charCommando = dienst->createCharacteristic(
        CHAR_COMMAND_UUID,
        BLECharacteristic::PROPERTY_WRITE
    );
    charCommando->setCallbacks(new CommandCallbacks());
    
    dienst->start();
    
    bleAdverteren = BLEDevice::getAdvertising();
    bleAdverteren->addServiceUUID(SERVICE_UUID);
    bleAdverteren->setScanResponse(true);
    bleAdverteren->setMinPreferred(0x06);
    bleAdverteren->setMinPreferred(0x12);
}

void startAdverteren() {
    BLEDevice::startAdvertising();
}

void stopAdverteren() {
    bleAdverteren->stop();
}

void stuurStatusBericht(uint8_t statusGebeurtenis) {
    if (!bleVerbonden) return;
    
    // We hebben nu minder bytes nodig (4 header + 1 data = 5 minimum, we maken buffer 8 voor veiligheid)
    uint8_t bericht[8] = {0}; 
    
    bericht[0] = BERICHT_STATUS;
    bericht[1] = APPARAAT_ID;
    bericht[2] = VEILIGHEIDS_BYTE;
    bericht[3] = 0; // Gereserveerd

    // Timestamp (bytes 4-7) is weggehaald.
    // De status komt nu direct na de header op plek 4.
    bericht[4] = statusGebeurtenis;
    
    // We sturen nu slechts 5 bytes (of rond af naar 8 als je vaste lengte wilt houden, hier 8 voor veiligheid)
    charData->setValue(bericht, 8);
    charData->notify();
}

void stuurDetectieBericht(uint16_t afstand) {
    if (!bleVerbonden) return;
    
    uint8_t bericht[8] = {0};
    
    bericht[0] = BERICHT_DETECTIE;
    bericht[1] = APPARAAT_ID;
    bericht[2] = VEILIGHEIDS_BYTE;
    bericht[3] = 0;

    bericht[4] = afstand & 0xFF;
    bericht[5] = (afstand >> 8) & 0xFF;
    
    charData->setValue(bericht, 8);
    charData->notify();
}

void stuurBatterijBericht(uint8_t batterijPercentage) {
    if (!bleVerbonden) return;
    
    uint8_t bericht[8] = {0};
    
    bericht[0] = BERICHT_BATTERIJ;
    bericht[1] = APPARAAT_ID;
    bericht[2] = VEILIGHEIDS_BYTE;
    bericht[3] = 0;

    bericht[4] = batterijPercentage;
    
    charData->setValue(bericht, 8);
    charData->notify();
}

void initHardware() {
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
}

void initTofSensor() {
    Wire.setClock(400000);
    tofSensor.setTimeout(500);
    
    if (!tofSensor.init()) {
        tofGeinitialiseerd = false;
        return;
    }

    tofSensor.setMeasurementTimingBudget(33000);
    tofSensor.startContinuous();
    tofGeinitialiseerd = true;
}

void initZoemer() {
    ledcAttach(PIN_ZOEMER, ZOEMER_FREQ_STANDAARD, ZOEMER_RESOLUTIE);
    ledcWrite(PIN_ZOEMER, 0);
}

void initRgbLed() {
    ledcAttach(PIN_LED_ROOD, LED_PWM_FREQ, LED_PWM_RESOLUTIE);
    ledcAttach(PIN_LED_GROEN, LED_PWM_FREQ, LED_PWM_RESOLUTIE);
    ledcAttach(PIN_LED_BLAUW, LED_PWM_FREQ, LED_PWM_RESOLUTIE);
    rgbLedUit();
}

void IRAM_ATTR knopISR() {
    knopIngedrukt = true;
}

void initKnop() {
    pinMode(PIN_KNOP, INPUT_PULLUP);
    attachInterrupt(digitalPinToInterrupt(PIN_KNOP), knopISR, FALLING);
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
}

uint16_t leesTofAfstand() {
    if (!tofGeinitialiseerd) return 9999;
    
    uint16_t afstand = tofSensor.readRangeContinuousMillimeters();
    
    if (tofSensor.timeoutOccurred()) {
        return 9999;
    }
    
    return afstand;
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
    
    return (uint8_t)percentage;
}

bool isUsbVerbonden() {
    int adcWaarde = analogRead(PIN_USB_VBUS);
    
    return (adcWaarde > USB_VBUS_DREMPEL);
}

void updateOplaadStatus() {
    bool wasVerbonden = usbVerbonden;
    usbVerbonden = isUsbVerbonden();
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
    zoemerToon(1000, 100);
    delay(50);
    zoemerToon(1500, 100);
    delay(50);
    zoemerToon(2000, 150);
    zoemerUit();
}

void speelIncorrectGeluid() {
    zoemerToon(400, 150);
    delay(50);
    zoemerToon(300, 150);
    delay(50);
    zoemerToon(200, 200);
    zoemerUit();
}

void speelVerbindingGeluid() {
    zoemerToon(800, 100);
    delay(50);
    zoemerToon(1200, 150);
    zoemerUit();
}

void speelVerbreekGeluid() {
    zoemerToon(600, 150);
    delay(50);
    zoemerToon(400, 200);
    zoemerUit();
}

void speelOntwaakGeluid() {
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
    Serial.flush();
    
    esp_deep_sleep_enable_gpio_wakeup(BIT(PIN_KNOP), ESP_GPIO_WAKEUP_GPIO_LOW);
    BLEDevice::deinit(false);
    esp_deep_sleep_start();
}