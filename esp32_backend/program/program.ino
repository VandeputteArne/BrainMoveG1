#include <Arduino.h>
#include <BLEDevice.h>
#include <BLEUtils.h>
#include <BLEServer.h>
#include <BLE2902.h>
#include <Wire.h>
#include <VL53L0X.h>

#define DEVICE_ID 3
const char* DEVICE_NAMES[] = {"BM-Blue", "BM-Red", "BM-Yellow", "BM-Green"};
#define DEVICE_NAME DEVICE_NAMES[DEVICE_ID]

// GPIO
#define PIN_BUTTON  GPIO_NUM_3  // RTC capable
#define PIN_BATTERY_ADC_1   GPIO_NUM_2
#define PIN_BATTERY_ADC_2   GPIO_NUM_4
#define PIN_BUZZER  GPIO_NUM_5
#define PIN_I2C_SDA GPIO_NUM_6
#define PIN_I2C_SCL GPIO_NUM_7

// USB
#define PIN_USB_VBUS    GPIO_NUM_21
#define USB_VBUS_THRESHOLD  2000    // Need voltage divider 10k/10k

// LED
#define PIN_LED_RED GPIO_NUM_8
#define PIN_LED_GREEN   GPIO_NUM_9
#define PIN_LED_BLUE    GPIO_NUM_10
#define RGB_LED_COMMON_ANODE false

// PWM
#define BUZZER_CHANNEL  0
#define BUZZER_RESOLUTION   8
#define BUZZER_FREQ_DEFAULT 2000
#define LED_PWM_FREQ    5000
#define LED_PWM_RESOLUTION  8

// Battery Levels
#define BATTERY_LEVEL_LOW   20
#define BATTERY_LEVEL_MEDIUM    50
#define LED_UPDATE_INTERVAL 5000
#define LED_CHARGING_BLINK_MS   500

// Debug Config
#define DEBUG_VERBOSE   false
#define DEBUG_SERIAL    true

// Timing
#define BUTTON_DEBOUNCE_MS  200
#define ADVERTISING_TIMEOUT_MS  (5UL * 60UL * 1000UL)
#define BATTERY_REPORT_INTERVAL (5UL * 60UL * 1000UL)
#define KEEPALIVE_INTERVAL  (30UL * 1000UL)
#define GLOBAL_IDLE_TIMEOUT_MS  (10UL * 60UL * 1000UL)
#define TOF_POLL_INTERVAL_MS    50
#define TOF_DETECTION_THRESHOLD 300

// Battery Config
#define BATTERY_ADC_RESOLUTION  12
#define BATTERY_VOLTAGE_DIVIDER 2.0f
#define BATTERY_FULL_VOLTAGE    4.2f
#define BATTERY_EMPTY_VOLTAGE   3.0f
#define BATTERY_USE_AVERAGE true

// BLE UUIDs -> uuidgenerator.net
#define SERVICE_UUID    "beb5483e-36e1-4688-b7f5-ea07361b26a7"
#define CHAR_DATA_UUID  "beb5483e-36e1-4688-b7f5-ea07361b26a8"
#define CHAR_COMMAND_UUID   "beb5483e-36e1-4688-b7f5-ea07361b26a9"

// Security
#define MAGIC_BYTE  0x42

// BLE Pin
#define BLE_PAIRING_PIN 589175

// Message Type
#define MSG_STATUS  0x01
#define MSG_DETECTION  0x02
#define MSG_BATTERY  0x03
#define MSG_KEEPALIVE  0x04

// Command Type
#define CMD_START   0x01
#define CMD_STOP    0x02
#define CMD_SLEEP   0x03
#define CMD_PING    0x04
#define CMD_SOUND_CORRECT   0x10
#define CMD_SOUND_INCORRECT 0x11

// Status Event Types
#define STATUS_CONNECTED  0x01
#define STATUS_RECONNECTED  0x02
#define STATUS_SLEEPING 0x03
#define STATUS_PONG  0x04

// States Enums
enum class SystemState : uint8_t {
    INIT,
    ADVERTISING,
    CONNECTED,
    POLLING,
    ENTERING_SLEEP
};

// Command Types From RPi
enum class RpiCommand : uint8_t {
    NONE = 0,
    START = CMD_START,
    STOP = CMD_STOP,
    SLEEP = CMD_SLEEP,
    PING = CMD_PING,
    SOUND_CORRECT = CMD_SOUND_CORRECT,
    SOUND_INCORRECT = CMD_SOUND_INCORRECT
};

// FSM State
volatile SystemState currentState = SystemState::INIT;
volatile SystemState previousState = SystemState::INIT;

// Timing Vars In Millis
unsigned long stateEntryTime = 0;
unsigned long lastBatteryReportTime = 0;
unsigned long lastKeepaliveTime = 0;
unsigned long lastTofPollTime = 0;
unsigned long lastActivityTime = 0;

// BLE Objects
BLEServer* pServer = nullptr;
BLECharacteristic* pCharData = nullptr;
BLECharacteristic* pCharCommand = nullptr;
BLEAdvertising* pAdvertising = nullptr;

// Connection State, RPI Changes State
volatile bool bleConnected = false;
volatile bool newCommandReceived = false;

// Command State
RpiCommand pendingCommand = RpiCommand::NONE;

// Hardware
VL53L0X tofSensor;
bool tofInitialized = false;

// USB & Charging State
bool rgbCommonAnode = false;
volatile bool usbConnected = false;
unsigned long lastLedUpdateTime = 0;
unsigned long lastChargingBlinkTime = 0;
bool chargingLedState = false;
uint8_t lastBatteryPercent = 0;

// Wake-Up Button State
volatile bool buttonPressed = false;
unsigned long lastButtonPressTime = 0;

// State Functions
void transitionToState(SystemState newState);
void handleStateInit();
void handleStateAdvertising();
void handleStateConnected();
void handleStatePolling();
void handleStateEnteringSleep();

// BLE Functions
void initBLE();
void startAdvertising();
void stopAdvertising();
void sendStatusMessage(uint8_t statusEvent);
void sendDetectionMessage(uint16_t distance);
void sendBatteryMessage(uint8_t batteryPercent);
void sendKeepaliveMessage();

// Hardware Functions
void initHardware();
void initTofSensor();
void initBuzzer();
void initRgbLed();
void initButton();
uint16_t readTofDistance();
bool isObjectDetected();
uint8_t readBatteryPercentage();
float readBatteryVoltage(bool useAverage = BATTERY_USE_AVERAGE);
void handleButtonPress();

// USB & Charging Functions
bool isUsbConnected();
void updateChargingState();

// RGB LED Functions
void setRgbColor(uint8_t red, uint8_t green, uint8_t blue);
void updateBatteryLed();
void showBatteryLevel(uint8_t percent, bool charging);
void rgbLedOff();

// Sound Functions
void playCorrectSound();
void playIncorrectSound();
void playConnectionSound();
void playDisconnectSound();
void buzzerTone(uint32_t frequency, uint32_t duration);
void buzzerOff();

// Power Management
void enterDeepSleep();
void printWakeupReason();

// Utility
void logState(const char* message);

// BLE Server Events
class ServerCallbacks : public BLEServerCallbacks {
    void onConnect(BLEServer* pServer) override {
        Serial.println("[BLE] RPi connected");
        bleConnected = true;
        lastActivityTime = millis();
        playConnectionSound();
    }

    void onDisconnect(BLEServer* pServer) override {
        Serial.println("[BLE] RPi disconnected");
        bleConnected = false;
        playDisconnectSound();
        
        // If disconnected, Return to advertising
        if (currentState != SystemState::ENTERING_SLEEP) {
            transitionToState(SystemState::ADVERTISING);
        }
    }
};

// BLE Incoming CMD's
class CommandCallbacks : public BLECharacteristicCallbacks {
    void onWrite(BLECharacteristic* pCharacteristic) override {
        String value = pCharacteristic->getValue();
        
        if (value.length() > 0) {
            uint8_t cmd = (uint8_t)value[0];
            Serial.printf("[BLE] Command received: 0x%02X\n", cmd);
            
            pendingCommand = static_cast<RpiCommand>(cmd);
            newCommandReceived = true;
            lastActivityTime = millis();
        }
    }
};

void setup() {
    Serial.begin(115200);
    delay(100);

    printWakeupReason();
    
    initHardware();
    initBLE();
    
    stateEntryTime = millis();
    lastActivityTime = millis();
    
    transitionToState(SystemState::ADVERTISING);
    
    Serial.println("[INIT] setup successful\n");
}

void loop() {
    if (millis() - lastActivityTime > GLOBAL_IDLE_TIMEOUT_MS) {
        Serial.println("Timeout exceeded");
        transitionToState(SystemState::ENTERING_SLEEP);
    }
    
    // Execute current state handler
    switch (currentState) {
        case SystemState::INIT:
            handleStateInit();
            break;
            
        case SystemState::ADVERTISING:
            handleStateAdvertising();
            break;
            
        case SystemState::CONNECTED:
            handleStateConnected();
            break;
            
        case SystemState::POLLING:
            handleStatePolling();
            break;
            
        case SystemState::ENTERING_SLEEP:
            handleStateEnteringSleep();
            break;
    }
    
    // Update battery LED
    if (millis() - lastLedUpdateTime >= LED_UPDATE_INTERVAL) {
        lastLedUpdateTime = millis();
        lastBatteryPercent = readBatteryPercentage();
    }
    // Always update LED for charging blink animation
    updateBatteryLed();
    handleButtonPress();
    yield();
}

// Transition, log, timing
void transitionToState(SystemState newState) {
    if (currentState == newState) return;
    
    previousState = currentState;
    currentState = newState;
    stateEntryTime = millis();
    
    const char* stateNames[] = {
        "INIT", "ADVERTISING", "CONNECTED", "POLLING", "ENTERING_SLEEP"
    };
    
    Serial.printf("STATE transition: %s -> %s\n", 
                  stateNames[static_cast<uint8_t>(previousState)],
                  stateNames[static_cast<uint8_t>(newState)]);
}

void handleStateInit() {
    transitionToState(SystemState::ADVERTISING);
}

void handleStateAdvertising() {
    if (millis() - stateEntryTime > ADVERTISING_TIMEOUT_MS) {
        Serial.println("[ADVERTISING] Timeout - no connection");
        transitionToState(SystemState::ENTERING_SLEEP);
        return;
    }
    
    if (previousState != SystemState::ADVERTISING) {
        startAdvertising();
    }
    
    if (bleConnected) {
        transitionToState(SystemState::CONNECTED);
    }
}

void handleStateConnected() {
    if (!bleConnected) {
        transitionToState(SystemState::ADVERTISING);
        return;
    }
    
    // Send battery % on connect & every xm
    if (millis() - stateEntryTime >= 1000) {
        if (lastBatteryReportTime == 0 || 
            (millis() - lastBatteryReportTime >= BATTERY_REPORT_INTERVAL)) {
            uint8_t batteryPercent = readBatteryPercentage();
            sendBatteryMessage(batteryPercent);
            lastBatteryReportTime = millis();
        }
    }
    
    // Keep-alive
    if (millis() - lastKeepaliveTime >= KEEPALIVE_INTERVAL) {
        sendKeepaliveMessage();
        lastKeepaliveTime = millis();
    }
    
    if (newCommandReceived) {
        newCommandReceived = false;
        lastActivityTime = millis();
        
        switch (pendingCommand) {
            case RpiCommand::START:
                Serial.println("[CONNECTED] START CMD, polling");
                transitionToState(SystemState::POLLING);
                break;
                
            case RpiCommand::STOP:
                Serial.println("[CONNECTED] STOP CMD, idle");
                break;
                
            case RpiCommand::SLEEP:
                Serial.println("[CONNECTED] SLEEP CMD, sleeping");
                transitionToState(SystemState::ENTERING_SLEEP);
                break;
                
            case RpiCommand::PING:
                Serial.println("[CONNECTED] PING CMD, send pong");
                sendStatusMessage(STATUS_PONG);
                break;
                
            case RpiCommand::SOUND_CORRECT:
                Serial.println("[CONNECTED] SOUND_CORRECT CMD, correct sound");
                playCorrectSound();
                break;
                
            case RpiCommand::SOUND_INCORRECT:
                Serial.println("[CONNECTED] SOUND_INCORRECT CMD, incorrect sound");
                playIncorrectSound();
                break;
                
            default:
                break;
        }
        
        pendingCommand = RpiCommand::NONE;
    }
}

void handleStatePolling() {
    if (!bleConnected) {
        transitionToState(SystemState::ADVERTISING);
        return;
    }
    
    // Check for stop/sleep commands
    if (newCommandReceived) {
        newCommandReceived = false;
        lastActivityTime = millis();
        
        switch (pendingCommand) {
            case RpiCommand::STOP:
                Serial.println("[POLLING] STOP CMD, returning to idle");
                transitionToState(SystemState::CONNECTED);
                pendingCommand = RpiCommand::NONE;
                return;
                
            case RpiCommand::SLEEP:
                Serial.println("[POLLING] SLEEP CMD");
                transitionToState(SystemState::ENTERING_SLEEP);
                pendingCommand = RpiCommand::NONE;
                return;
                
            case RpiCommand::SOUND_CORRECT:
                Serial.println("[POLLING] SOUND_CORRECT CMD, correct sound");
                playCorrectSound();
                break;
                
            case RpiCommand::SOUND_INCORRECT:
                Serial.println("[POLLING] SOUND_INCORRECT CMD, incorrect sound");
                playIncorrectSound();
                break;
                
            default:
                break;
        }
        
        pendingCommand = RpiCommand::NONE;
    }
    
    // TOF polling
    if (millis() - lastTofPollTime >= TOF_POLL_INTERVAL_MS) {
        lastTofPollTime = millis();
        
        if (isObjectDetected()) {
            uint16_t distance = readTofDistance();
            Serial.printf("[POLLING] Object detected at %d mm!\n", distance);
            lastActivityTime = millis();
            
            sendDetectionMessage(distance);
        }
    }
    
    // Continue battery report
    if (millis() - lastBatteryReportTime >= BATTERY_REPORT_INTERVAL) {
        uint8_t batteryPercent = readBatteryPercentage();
        sendBatteryMessage(batteryPercent);
        lastBatteryReportTime = millis();
    }
    
    // Continue keepalive
    if (millis() - lastKeepaliveTime >= KEEPALIVE_INTERVAL) {
        sendKeepaliveMessage();
        lastKeepaliveTime = millis();
    }
}

void handleStateEnteringSleep() {
    Serial.println("[SLEEP] Preparing deep sleep...");
    
    if (bleConnected) {
        sendStatusMessage(STATUS_SLEEPING);
        delay(100); // Delay for message
    }
    
    stopAdvertising();
    if (pServer && bleConnected) {
        pServer->disconnect(pServer->getConnId());
    }
    
    buzzerOff();
    
    rgbLedOff();
    
    if (tofInitialized) {
        tofSensor.stopContinuous();
    }
    
    // Cleanup delay
    delay(100);
    
    enterDeepSleep();
}

void initBLE() {
    Serial.println("[BLE] Initializing BLE as Server/Peripheral...");
    
    BLEDevice::init(DEVICE_NAME);

    BLESecurity *pSecurity = new BLESecurity();
    pSecurity->setAuthenticationMode(ESP_LE_AUTH_REQ_SC_MITM_BOND);
    pSecurity->setCapability(ESP_IO_CAP_OUT);
    pSecurity->setKeySize(16);
    pSecurity->setInitEncryptionKey(ESP_BLE_ENC_KEY_MASK | ESP_BLE_ID_KEY_MASK);
    pSecurity->setRespEncryptionKey(ESP_BLE_ENC_KEY_MASK | ESP_BLE_ID_KEY_MASK);
    
    Serial.println("[BLE] Bonding enabled");
    Serial.printf("[BLE] Pairing XIAO ESP32-C3\n");
    
    pServer = BLEDevice::createServer();
    pServer->setCallbacks(new ServerCallbacks());
    
    BLEService* pService = pServer->createService(SERVICE_UUID);
    
    pCharData = pService->createCharacteristic(
        CHAR_DATA_UUID,
        BLECharacteristic::PROPERTY_READ | 
        BLECharacteristic::PROPERTY_NOTIFY
    );
    pCharData->addDescriptor(new BLE2902());

    pCharCommand = pService->createCharacteristic(
        CHAR_COMMAND_UUID,
        BLECharacteristic::PROPERTY_WRITE
    );
    pCharCommand->setCallbacks(new CommandCallbacks());
    
    pService->start();
    
    pAdvertising = BLEDevice::getAdvertising();
    pAdvertising->addServiceUUID(SERVICE_UUID);
    pAdvertising->setScanResponse(true);
    pAdvertising->setMinPreferred(0x06);
    pAdvertising->setMinPreferred(0x12);
    
    Serial.printf("[BLE] Started as '%s'\n", DEVICE_NAME);
}

void startAdvertising() {
    Serial.println("[BLE] Advertising");
    BLEDevice::startAdvertising();
    Serial.printf("[BLE] Advertising, name: '%s', waiting for RPi\n", DEVICE_NAME);
}

void stopAdvertising() {
    if (pAdvertising) {
        pAdvertising->stop();
        Serial.println("[BLE] Stopped advertising");
    }
}

// Format: [type(1)][device_id(1)][magic(1)][reserved(1)][timestamp(4)][status_event(1)][padding(3)]
void sendStatusMessage(uint8_t statusEvent) {
    if (!bleConnected || !pCharData) return;
    
    uint8_t message[12] = {0};
    uint32_t timestamp = millis();
    
    message[0] = MSG_STATUS;
    message[1] = DEVICE_ID;
    message[2] = MAGIC_BYTE;
    message[3] = 0;
    memcpy(&message[4], &timestamp, 4);
    message[8] = statusEvent;
    
    pCharData->setValue(message, 12);
    pCharData->notify();
    
    Serial.printf("[BLE] Sent STATUS: event=0x%02X\n", statusEvent);
}

// Format: [type(1)][device_id(1)][magic(1)][reserved(1)][timestamp(4)][distance_mm(2)][padding(2)]
void sendDetectionMessage(uint16_t distance) {
    if (!bleConnected || !pCharData) return;
    
    uint8_t message[12] = {0};
    uint32_t timestamp = millis();
    
    message[0] = MSG_DETECTION;
    message[1] = DEVICE_ID;
    message[2] = MAGIC_BYTE;
    message[3] = 0;
    memcpy(&message[4], &timestamp, 4);
    memcpy(&message[8], &distance, 2);
    
    pCharData->setValue(message, 12);
    pCharData->notify();
    
    Serial.printf("[BLE] Sent DETECTION: distance=%d mm\n", distance);
}

// Format: [type(1)][device_id(1)][magic(1)][reserved(1)][timestamp(4)][battery_percent(1)][padding(3)]
void sendBatteryMessage(uint8_t batteryPercent) {
    if (!bleConnected || !pCharData) return;
    
    uint8_t message[12] = {0};
    uint32_t timestamp = millis();
    
    message[0] = MSG_BATTERY;
    message[1] = DEVICE_ID;
    message[2] = MAGIC_BYTE;
    message[3] = 0;
    memcpy(&message[4], &timestamp, 4);
    message[8] = batteryPercent;
    
    pCharData->setValue(message, 12);
    pCharData->notify();
    
    Serial.printf("[BLE] Sent BATTERY: %d%%\n", batteryPercent);
}

// Format: [type(1)][device_id(1)][magic(1)][reserved(1)][timestamp(4)]
void sendKeepaliveMessage() {
    if (!bleConnected || !pCharData) return;
    
    uint8_t message[8] = {0};
    uint32_t timestamp = millis();
    
    message[0] = MSG_KEEPALIVE;
    message[1] = DEVICE_ID;
    message[2] = MAGIC_BYTE;
    message[3] = 0;
    memcpy(&message[4], &timestamp, 4);
    
    pCharData->setValue(message, 8);
    pCharData->notify();
}

void initHardware() {
    Serial.println("[HW] Initializing hardware");
    
    analogReadResolution(BATTERY_ADC_RESOLUTION);
    analogSetAttenuation(ADC_11db);
    
    Wire.begin(PIN_I2C_SDA, PIN_I2C_SCL);
    
    initButton();
    initBuzzer();
    initRgbLed();
    initTofSensor();
    
    updateChargingState();
    
    lastBatteryPercent = readBatteryPercentage();
    updateBatteryLed();
    
    Serial.println("[HW] Initialization complete");
}

void initTofSensor() {
    Serial.println("[TOF] Initializing VL53L0X");
    
    Wire.setClock(400000);
    
    tofSensor.setTimeout(500);
    
    if (!tofSensor.init()) {
        Serial.println("[TOF] VL53L0X init failed");
        tofInitialized = false;
        return;
    }
    
    // Swipe detection settings
    tofSensor.setSignalRateLimit(0.1);
    tofSensor.setVcselPulsePeriod(VL53L0X::VcselPeriodPreRange, 18);
    tofSensor.setVcselPulsePeriod(VL53L0X::VcselPeriodFinalRange, 14);
    
    // Higher speed = shorter measurement timing
    tofSensor.setMeasurementTimingBudget(33000);

    tofSensor.startContinuous();
    
    tofInitialized = true;
    Serial.println("[TOF] VL53L0X initialized");
}

void initBuzzer() {
    Serial.println("[BUZZER] Initializing PWM");
    
    ledcAttach(PIN_BUZZER, BUZZER_FREQ_DEFAULT, BUZZER_RESOLUTION);
    ledcWrite(PIN_BUZZER, 0);
    
    Serial.println("[BUZZER] PWM initialized");
}

void initRgbLed() {
    Serial.println("[RGB] Initializing RGB LED");
    
    ledcAttach(PIN_LED_RED, LED_PWM_FREQ, LED_PWM_RESOLUTION);
    ledcAttach(PIN_LED_GREEN, LED_PWM_FREQ, LED_PWM_RESOLUTION);
    ledcAttach(PIN_LED_BLUE, LED_PWM_FREQ, LED_PWM_RESOLUTION);
    
    rgbLedOff();
    
    Serial.println("[RGB] RGB LED initialized");
}

void IRAM_ATTR buttonISR() {
    buttonPressed = true;
}

void initButton() {
    Serial.println("[BUTTON] Initializing button");
    
    pinMode(PIN_BUTTON, INPUT_PULLUP);
    attachInterrupt(digitalPinToInterrupt(PIN_BUTTON), buttonISR, FALLING);
    
    Serial.println("[BUTTON] Button initialized");
}

void handleButtonPress() {
    if (!buttonPressed) return;
    
    if (millis() - lastButtonPressTime < BUTTON_DEBOUNCE_MS) {
        buttonPressed = false;
        return;
    }
    
    buttonPressed = false;
    lastButtonPressTime = millis();
    lastActivityTime = millis();
    
    Serial.println("[BUTTON] Button pressed");
}

uint16_t readTofDistance() {
    if (!tofInitialized) return 9999;
    
    uint16_t distance = tofSensor.readRangeContinuousMillimeters();
    
    if (tofSensor.timeoutOccurred()) {
        Serial.println("[TOF] Timeout");
        return 9999;
    }
    
    return distance;
}

bool isObjectDetected() {
    uint16_t distance = readTofDistance();
    
    return (distance < TOF_DETECTION_THRESHOLD && distance > 0);
}

float readBatteryVoltageFromPin(int pin) {
    int adcValue = analogRead(pin);
    
    float voltage = (adcValue / 4095.0f) * 3.3f;
    
    voltage *= BATTERY_VOLTAGE_DIVIDER;
    
    return voltage;
}

float readBatteryVoltage(bool useAverage) {
    float v1 = readBatteryVoltageFromPin(PIN_BATTERY_ADC_1);
    float v2 = readBatteryVoltageFromPin(PIN_BATTERY_ADC_2);

    if (useAverage) {
        return (v1 + v2) / 2.0f;
    } else {
        return (v1 < v2) ? v1 : v2;
    }
}

uint8_t readBatteryPercentage() {
    float voltage = readBatteryVoltage();
    
    float percentage = (voltage - BATTERY_EMPTY_VOLTAGE) / 
        (BATTERY_FULL_VOLTAGE - BATTERY_EMPTY_VOLTAGE) * 100.0f;
    
    if (percentage > 100.0f) percentage = 100.0f;
    if (percentage < 0.0f) percentage = 0.0f;
    
    Serial.printf("[BATTERY] Voltage: %.2fV, Percentage: %.0f%%\n", voltage, percentage);
    
    return (uint8_t)percentage;
}

// Check if USB is connected
// Hardware: 5V VBUS -> voltage divider: 10k/10k -> GPIO2
// With 10k/10k divider: 5V -> 2.5V, safe for ESP32-C3(3.3V max)
bool isUsbConnected() {
    int adcValue = analogRead(PIN_USB_VBUS);
    
    return (adcValue > USB_VBUS_THRESHOLD);
}

void updateChargingState() {
    bool wasConnected = usbConnected;
    usbConnected = isUsbConnected();
    
    if (usbConnected != wasConnected) {
        if (usbConnected) {
            Serial.println("[USB] USB connected, charging");
        } else {
            Serial.println("[USB] USB disconnected, on battery");
        }
    }
}

void setRgbColor(uint8_t r, uint8_t g, uint8_t b) {
    if (rgbCommonAnode) {
        r = 255 - r; g = 255 - g; b = 255 - b;
    }
    ledcWrite(PIN_LED_RED, r);
    ledcWrite(PIN_LED_GREEN, g);
    ledcWrite(PIN_LED_BLUE, b);
}

void rgbLedOff() {
    setRgbColor(0, 0, 0);
}

void showBatteryLevel(uint8_t percent, bool charging) {
    uint8_t red = 0, green = 0, blue = 0;
    
    if (percent < BATTERY_LEVEL_LOW) {
        // LOW: Red
        red = 255;
        green = 0;
        blue = 0;
    } else if (percent < BATTERY_LEVEL_MEDIUM) {
        // MEDIUM: Yellow/Orange, if not clear change to blue
        red = 255;
        green = 128;
        blue = 0;
    } else {
        // HIGH: Green
        red = 0;
        green = 255;
        blue = 0;
    }
    
    // If charging, blink
    if (charging) {
        if (millis() - lastChargingBlinkTime >= LED_CHARGING_BLINK_MS) {
            lastChargingBlinkTime = millis();
            chargingLedState = !chargingLedState;
        }
        
        if (chargingLedState) {
            setRgbColor(red, green, blue);
        } else {
            rgbLedOff();
        }
    } else {
        // Not charging: solid
        setRgbColor(red, green, blue);
    }
}

void updateBatteryLed() {
    updateChargingState();

    showBatteryLevel(lastBatteryPercent, usbConnected);
}

void playCorrectSound() {
    Serial.println("[BUZZER] Playing CORRECT sound");
    
    buzzerTone(1000, 100);
    delay(50);
    buzzerTone(1500, 100);
    delay(50);
    buzzerTone(2000, 150);
    buzzerOff();
}

void playIncorrectSound() {
    Serial.println("[BUZZER] Playing INCORRECT sound");
    
    buzzerTone(400, 150);
    delay(50);
    buzzerTone(300, 150);
    delay(50);
    buzzerTone(200, 200);
    buzzerOff();
}

void playConnectionSound() {
    Serial.println("[BUZZER] Playing connection sound");
    
    buzzerTone(800, 100);
    delay(50);
    buzzerTone(1200, 150);
    buzzerOff();
}

void playDisconnectSound() {
    Serial.println("[BUZZER] Playing disconnect sound");
    
    buzzerTone(600, 150);
    delay(50);
    buzzerTone(400, 200);
    buzzerOff();
}

void buzzerTone(uint32_t frequency, uint32_t duration) {
    ledcChangeFrequency(PIN_BUZZER, frequency, BUZZER_RESOLUTION);
    ledcWrite(PIN_BUZZER, 127);
    delay(duration);
    buzzerOff();
}

void buzzerOff() {
    ledcWrite(PIN_BUZZER, 0);
}

void enterDeepSleep() {
    Serial.println("\n[SLEEP] Starting deep sleep setup");
    Serial.flush(); // Make sure data is sent
    
    esp_deep_sleep_enable_gpio_wakeup(BIT(PIN_BUTTON), ESP_GPIO_WAKEUP_GPIO_LOW);
    
    BLEDevice::deinit(false);
    
    esp_deep_sleep_start();
}

void printWakeupReason() {
    esp_sleep_wakeup_cause_t wakeupReason = esp_sleep_get_wakeup_cause();
    
    Serial.print("[WAKE] Wake-up cause: ");
    
    switch (wakeupReason) {
        case ESP_SLEEP_WAKEUP_EXT0:
            Serial.println("External signal using RTC_IO");
            break;
        case ESP_SLEEP_WAKEUP_EXT1:
            Serial.println("External signal using RTC_CNTL");
            break;
        case ESP_SLEEP_WAKEUP_TIMER:
            Serial.println("Timer");
            break;
        case ESP_SLEEP_WAKEUP_TOUCHPAD:
            Serial.println("Touchpad");
            break;
        case ESP_SLEEP_WAKEUP_ULP:
            Serial.println("ULP program");
            break;
        case ESP_SLEEP_WAKEUP_GPIO:
            Serial.println("GPIO (button press)");
            break;
        default:
            Serial.printf("Other/Power-on reset (%d)\n", wakeupReason);
            break;
    }
}

void logState(const char* message) {
    Serial.printf("[DEBUG] %s (State: %d, Connected: %d)\n", 
                  message, 
                  static_cast<uint8_t>(currentState), 
                  bleConnected);
}
