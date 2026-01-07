/*
 * BLE Connection Test for ESP32
 * Simple test to verify BLE connection between ESP32 and Raspberry Pi
 * 
 * This code:
 * - Advertises as a BLE device
 * - Sends periodic test messages when connected
 * - Accepts simple commands from RPI
 */

#include <NimBLEDevice.h>

// BLE UUIDs - must match the Python client
#define SERVICE_UUID        "4fafc201-1fb5-459e-8fcc-c5c9c331914b"
#define CHAR_DATA_UUID      "beb5483e-36e1-4688-b7f5-ea07361b26a8"
#define CHAR_COMMAND_UUID   "beb5483e-36e1-4688-b7f5-ea07361b26a9"

// Device configuration - CHANGE THIS FOR EACH ESP32
#define DEVICE_NAME         "BM-Test"
#define DEVICE_ID           99

// Pins
#define PIN_LED             2  // Built-in LED on most ESP32 boards

// Timing
#define MESSAGE_INTERVAL_MS 3000  // Send test message every 3 seconds

// BLE objects
NimBLEServer* pServer = nullptr;
NimBLECharacteristic* pDataCharacteristic = nullptr;
NimBLECharacteristic* pCommandCharacteristic = nullptr;

// Connection state
bool deviceConnected = false;
bool wasConnected = false;

// Timing
unsigned long lastMessageTime = 0;
uint32_t messageCounter = 0;

// BLE Server Callbacks
class ServerCallbacks : public NimBLEServerCallbacks {
    void onConnect(NimBLEServer* pServer) {
        deviceConnected = true;
        Serial.println("\n✅ Client connected!");
        digitalWrite(PIN_LED, HIGH);
    }

    void onDisconnect(NimBLEServer* pServer) {
        deviceConnected = false;
        Serial.println("\n❌ Client disconnected");
        digitalWrite(PIN_LED, LOW);
    }
};

// BLE Command Characteristic Callbacks
class CommandCallbacks : public NimBLECharacteristicCallbacks {
    void onWrite(NimBLECharacteristic* pCharacteristic) {
        std::string value = pCharacteristic->getValue();
        if (value.length() > 0) {
            uint8_t cmd = value[0];
            Serial.printf("📥 Received command: 0x%02X\n", cmd);
            
            // Echo back a response
            String response = "ACK:" + String(cmd);
            sendMessage(response);
        }
    }
};

void setup() {
    Serial.begin(115200);
    delay(500);
    
    Serial.println("\n\n========================================");
    Serial.println("   BLE Connection Test - ESP32");
    Serial.printf("   Device: %s (ID: %d)\n", DEVICE_NAME, DEVICE_ID);
    Serial.println("========================================\n");
    
    // Setup LED
    pinMode(PIN_LED, OUTPUT);
    digitalWrite(PIN_LED, LOW);
    
    // Blink LED on startup
    for (int i = 0; i < 3; i++) {
        digitalWrite(PIN_LED, HIGH);
        delay(100);
        digitalWrite(PIN_LED, LOW);
        delay(100);
    }
    
    // Initialize BLE
    initBLE();
    
    Serial.println("✅ Setup complete");
    Serial.println("📡 Waiting for RPI connection...\n");
}

void loop() {
    // Handle connection state changes
    if (deviceConnected && !wasConnected) {
        wasConnected = true;
        Serial.println("🎉 First connection established!");
        sendMessage("HELLO from " + String(DEVICE_NAME));
    }
    
    if (!deviceConnected && wasConnected) {
        wasConnected = false;
        Serial.println("🔄 Restarting advertising...");
        delay(500);
        NimBLEDevice::getAdvertising()->start();
    }
    
    // Send periodic test messages when connected
    if (deviceConnected && (millis() - lastMessageTime >= MESSAGE_INTERVAL_MS)) {
        lastMessageTime = millis();
        messageCounter++;
        
        String testMsg = "TEST #" + String(messageCounter) + " from " + String(DEVICE_NAME);
        sendMessage(testMsg);
        
        Serial.printf("📤 Sent: %s\n", testMsg.c_str());
    }
    
    delay(10);
}

/**
 * Initialize BLE server and characteristics
 */
void initBLE() {
    Serial.println("🔧 Initializing BLE...");
    
    // Initialize NimBLE
    NimBLEDevice::init(DEVICE_NAME);
    NimBLEDevice::setPower(ESP_PWR_LVL_P9);
    
    // Configure security (bonding + encryption)
    Serial.println("🔐 Configuring BLE security...");
    NimBLEDevice::setSecurityAuth(true, true, true);
    NimBLEDevice::setSecurityIOCap(BLE_HS_IO_NO_INPUT_OUTPUT);
    
    uint8_t key_dist = BLE_SM_PAIR_KEY_DIST_ENC | BLE_SM_PAIR_KEY_DIST_ID;
    NimBLEDevice::setSecurityInitKey(key_dist);
    NimBLEDevice::setSecurityRespKey(key_dist);
    
    // Create BLE Server
    pServer = NimBLEDevice::createServer();
    pServer->setCallbacks(new ServerCallbacks());
    
    // Create BLE Service
    NimBLEService* pService = pServer->createService(SERVICE_UUID);
    
    // Create Data Characteristic (for notifications to RPI)
    pDataCharacteristic = pService->createCharacteristic(
        CHAR_DATA_UUID,
        NIMBLE_PROPERTY::READ | NIMBLE_PROPERTY::NOTIFY
    );
    
    // Create Command Characteristic (for commands from RPI)
    pCommandCharacteristic = pService->createCharacteristic(
        CHAR_COMMAND_UUID,
        NIMBLE_PROPERTY::WRITE | NIMBLE_PROPERTY::WRITE_NR
    );
    pCommandCharacteristic->setCallbacks(new CommandCallbacks());
    
    // Start the service
    pService->start();
    
    // Start advertising
    NimBLEAdvertising* pAdvertising = NimBLEDevice::getAdvertising();
    pAdvertising->addServiceUUID(SERVICE_UUID);
    pAdvertising->start();
    
    Serial.printf("✅ BLE initialized as '%s'\n", DEVICE_NAME);
    Serial.printf("📡 Service UUID: %s\n", SERVICE_UUID);
    Serial.println("🔐 Security: Bonding + Encryption enabled");
}

/**
 * Send a text message via BLE notification
 */
void sendMessage(String message) {
    if (!deviceConnected || pDataCharacteristic == nullptr) {
        return;
    }
    
    pDataCharacteristic->setValue(message.c_str());
    pDataCharacteristic->notify();
}
