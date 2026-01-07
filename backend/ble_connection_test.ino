/*
 * BLE Connection Test voor ESP32-C3 (NimBLE)
 * Zonder LED, geoptimaliseerd voor RPi connectie
 */

#include <NimBLEDevice.h>

// BLE UUIDs - moeten overeenkomen met het Python script op de RPi
#define SERVICE_UUID        "4fafc201-1fb5-459e-8fcc-c5c9c331914b"
#define CHAR_DATA_UUID      "beb5483e-36e1-4688-b7f5-ea07361b26a8"
#define CHAR_COMMAND_UUID   "beb5483e-36e1-4688-b7f5-ea07361b26a9"

// Apparaat configuratie
#define DEVICE_NAME         "BM-Test-C3"
#define DEVICE_ID           99

// Timing
#define MESSAGE_INTERVAL_MS 3000  // Elke 3 seconden een bericht

// BLE objecten
NimBLEServer* pServer = nullptr;
NimBLECharacteristic* pDataCharacteristic = nullptr;
NimBLECharacteristic* pCommandCharacteristic = nullptr;

// Status variabelen
bool deviceConnected = false;
bool wasConnected = false;

// Tellers
unsigned long lastMessageTime = 0;
uint32_t messageCounter = 0;

// Functie declaraties
void sendMessage(std::string message);
void initBLE();

// --- Callbacks voor Connectie Status ---
class ServerCallbacks : public NimBLEServerCallbacks {
    void onConnect(NimBLEServer* pServer) {
        deviceConnected = true;
        Serial.println("\n✅ Client verbonden! (Client connected)");
    }

    void onDisconnect(NimBLEServer* pServer) {
        deviceConnected = false;
        Serial.println("\n❌ Client verbroken (Client disconnected)");
    }
};

// --- Callbacks voor Ontvangen Commando's ---
class CommandCallbacks : public NimBLECharacteristicCallbacks {
    void onWrite(NimBLECharacteristic* pCharacteristic) {
        std::string value = pCharacteristic->getValue();
        
        if (value.length() > 0) {
            // We lezen de eerste byte als commando
            uint8_t cmd = value[0];
            Serial.printf("📥 Commando ontvangen: 0x%02X\n", cmd);
            
            // Stuur een bevestiging (ACK) terug
            char responseBuffer[32];
            snprintf(responseBuffer, sizeof(responseBuffer), "ACK:0x%02X", cmd);
            sendMessage(std::string(responseBuffer));
        }
    }
};

void setup() {
    // Start seriële communicatie (zorg dat 'USB CDC On Boot' aanstaat in IDE!)
    Serial.begin(115200);
    delay(2000); // Wacht even op de USB Serial connectie
    
    Serial.println("\n\n========================================");
    Serial.println("   BLE Test - ESP32-C3 (No LED)");
    Serial.printf("   Device: %s\n", DEVICE_NAME);
    Serial.println("========================================\n");
    
    // Initialiseer BLE
    initBLE();
    
    Serial.println("📡 Wachten op RPI verbinding...");
}

void loop() {
    // 1. Logica voor herverbinden (Reconnection logic)
    if (deviceConnected && !wasConnected) {
        wasConnected = true;
        Serial.println("🎉 Verbinding gestabiliseerd.");
    }
    
    if (!deviceConnected && wasConnected) {
        wasConnected = false;
        Serial.println("🔄 Verbinding verloren, start adverteren opnieuw...");
        delay(500);
        NimBLEDevice::getAdvertising()->start();
    }
    
    // 2. Stuur periodieke data als we verbonden zijn
    if (deviceConnected && (millis() - lastMessageTime >= MESSAGE_INTERVAL_MS)) {
        lastMessageTime = millis();
        messageCounter++;
        
        char msgBuffer[64];
        snprintf(msgBuffer, sizeof(msgBuffer), "TEST #%d from %s", messageCounter, DEVICE_NAME);
        
        sendMessage(std::string(msgBuffer));
        Serial.printf("📤 Verstuurd: %s\n", msgBuffer);
    }
    
    delay(10); // Korte pauze voor stabiliteit
}

void initBLE() {
    // A. Device initialisatie
    NimBLEDevice::init(DEVICE_NAME);
    NimBLEDevice::setPower(ESP_PWR_LVL_P9); // Maximaal zendvermogen
    
    // B. Beveiliging (Security) - UITGESCHAKELD voor RPi test
    // Zet dit pas aan als de basisverbinding werkt.
    NimBLEDevice::setSecurityAuth(false, false, false);

    // C. Server aanmaken
    pServer = NimBLEDevice::createServer();
    pServer->setCallbacks(new ServerCallbacks());
    
    // D. Dienst (Service) aanmaken
    NimBLEService* pService = pServer->createService(SERVICE_UUID);
    
    // E. Karakteristieken (Characteristics) aanmaken
    // 1. Data karakteristiek (ESP -> RPi via Notify)
    pDataCharacteristic = pService->createCharacteristic(
        CHAR_DATA_UUID,
        NIMBLE_PROPERTY::READ | NIMBLE_PROPERTY::NOTIFY
    );
    
    // 2. Commando karakteristiek (RPi -> ESP via Write)
    pCommandCharacteristic = pService->createCharacteristic(
        CHAR_COMMAND_UUID,
        NIMBLE_PROPERTY::WRITE | NIMBLE_PROPERTY::WRITE_NR
    );
    pCommandCharacteristic->setCallbacks(new CommandCallbacks());
    
    // F. Start alles
    pService->start();
    
    NimBLEAdvertising* pAdvertising = NimBLEDevice::getAdvertising();
    pAdvertising->addServiceUUID(SERVICE_UUID);
    pAdvertising->start();
    
    Serial.println("✅ BLE Geïnitialiseerd en aan het adverteren.");
}

void sendMessage(std::string message) {
    if (deviceConnected && pDataCharacteristic != nullptr) {
        pDataCharacteristic->setValue(message);
        pDataCharacteristic->notify();
    }
}