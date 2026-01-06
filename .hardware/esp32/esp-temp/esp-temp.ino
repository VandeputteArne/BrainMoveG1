#include <WiFi.h>
#include <WiFiClient.h>
#include <Wire.h>
#include <VL53L1X.h>
#include <esp_sleep.h>
#include <esp_wifi.h>
#include <ArduinoJson.h>

// ============================================================================
// CONFIGURATION - MODIFY THESE FOR EACH ESP32 MODULE
// ============================================================================

// Device identification - CHANGE THIS FOR EACH ESP32
// Options: "esp-blue", "esp-red", "esp-yellow", "esp-green"
#define DEVICE_NAME         "esp-blue"

// WiFi Configuration
#define WIFI_SSID           "BrainMoveG1"
#define WIFI_PASSWORD       "bmhotspotajm"

// RPI5 Server Configuration
#define SERVER_IP           "192.168.4.1"   // Default hotspot IP for RPI
#define SERVER_PORT         5000            // TCP server port

// ============================================================================
// HARDWARE PIN DEFINITIONS
// ============================================================================

#define PIN_WAKE_BUTTON     GPIO_NUM_4      // Wake-up button (pullup, active LOW)
#define PIN_I2C_SDA         21              // I2C data for ToF sensor
#define PIN_I2C_SCL         22              // I2C clock for ToF sensor
#define PIN_BUZZER          25              // Buzzer output
#define PIN_STATUS_LED      2               // Built-in LED

// ============================================================================
// TIMING CONSTANTS (milliseconds)
// ============================================================================

#define WIFI_TIMEOUT_MS         300000      // 5 minutes WiFi connection timeout
#define RECONNECT_TIMEOUT_MS    300000      // 5 minutes reconnection timeout
#define KEEPALIVE_INTERVAL_MS   5000        // Send keepalive every 5 seconds
#define SENSOR_POLL_INTERVAL_MS 50          // Poll ToF sensor every 50ms
#define DETECTION_DEBOUNCE_MS   500         // Debounce time between detections
#define BUZZER_DURATION_MS      75          // Buzzer beep duration
#define WIFI_RETRY_BASE_MS      1000        // Base delay for exponential backoff
#define WIFI_RETRY_MAX_MS       30000       // Maximum retry delay
#define SERVER_READ_TIMEOUT_MS  100         // Non-blocking read timeout
#define CONNECTION_CHECK_MS     1000        // Check connection every second

// ============================================================================
// TOF SENSOR CONFIGURATION
// ============================================================================

#define TOF_DETECTION_THRESHOLD_MM  300     // Detection threshold (300mm = 30cm)
#define TOF_TIMING_BUDGET_US        50000   // Measurement timing budget (50ms)
#define TOF_DISTANCE_MODE           2       // 1 = Short, 2 = Long range mode

// ============================================================================
// STATE MACHINE DEFINITIONS
// ============================================================================

enum SystemState {
    STATE_STARTUP,              // Initial startup after wake
    STATE_CONNECTING,           // Attempting WiFi connection
    STATE_WAITING_FOR_SIGNAL,   // Connected, waiting for START from RPI
    STATE_ACTIVE_POLLING,       // Actively polling ToF sensor
    STATE_RECONNECTING,         // Lost connection, attempting to reconnect
    STATE_SLEEP                 // Entering deep sleep
};

// State names for debugging
const char* stateNames[] = {
    "STARTUP",
    "CONNECTING", 
    "WAITING_FOR_SIGNAL",
    "ACTIVE_POLLING",
    "RECONNECTING",
    "SLEEP"
};

// ============================================================================
// GLOBAL VARIABLES
// ============================================================================

// State machine
SystemState currentState = STATE_STARTUP;
SystemState previousState = STATE_STARTUP;

// WiFi and networking
WiFiClient tcpClient;
bool serverConnected = false;

// Timing variables
unsigned long wifiStartTime = 0;
unsigned long lastKeepaliveTime = 0;
unsigned long lastSensorPollTime = 0;
unsigned long lastDetectionTime = 0;
unsigned long lastConnectionCheckTime = 0;
unsigned long reconnectStartTime = 0;

// ToF sensor
VL53L1X tofSensor;
bool sensorInitialized = false;
bool objectDetected = false;

// Buzzer state (non-blocking)
bool buzzerActive = false;
unsigned long buzzerStartTime = 0;

// WiFi retry tracking
int wifiRetryCount = 0;

// Boot count for debugging (RTC memory survives deep sleep)
RTC_DATA_ATTR int bootCount = 0;

// ============================================================================
// FUNCTION PROTOTYPES
// ============================================================================

void transitionToState(SystemState newState);
bool connectWiFi();
bool connectToServer();
void communicateWithRPI();
void pollToFSensor();
void handleDetection(uint16_t distance);
void triggerBuzzer();
void updateBuzzer();
void sendToServer(const char* eventType, int distance = -1);
void enterDeepSleep();
void printWakeupReason();
void blinkLED(int times, int delayMs);
bool isWiFiConnected();
bool isServerConnected();
void handleServerData();
unsigned long getExponentialBackoff(int retryCount);

// ============================================================================
// SETUP FUNCTION
// ============================================================================

void setup() {
    // Initialize serial communication
    Serial.begin(115200);
    delay(100);
    
    Serial.println("\n\n========================================");
    Serial.println("   BrainMoveG1 - ESP32 ToF Node");
    Serial.printf("   Device: %s\n", DEVICE_NAME);
    Serial.println("========================================\n");
    
    // Increment and display boot count
    bootCount++;
    Serial.printf("[BOOT] Boot count: %d\n", bootCount);
    
    // Print wake-up reason
    printWakeupReason();
    
    // Initialize GPIO pins
    pinMode(PIN_STATUS_LED, OUTPUT);
    pinMode(PIN_BUZZER, OUTPUT);
    pinMode(PIN_WAKE_BUTTON, INPUT_PULLUP);
    
    // Ensure outputs are off initially
    digitalWrite(PIN_STATUS_LED, LOW);
    digitalWrite(PIN_BUZZER, LOW);
    
    // Visual feedback: device is starting
    blinkLED(3, 100);
    
    // Initialize I2C for ToF sensor
    Wire.begin(PIN_I2C_SDA, PIN_I2C_SCL);
    Wire.setClock(400000); // 400kHz I2C
    
    // Initialize ToF sensor
    Serial.println("[SENSOR] Initializing VL53L1X ToF sensor...");
    tofSensor.setTimeout(500);
    
    if (tofSensor.init()) {
        sensorInitialized = true;
        tofSensor.setDistanceMode(VL53L1X::Long);
        tofSensor.setMeasurementTimingBudget(TOF_TIMING_BUDGET_US);
        tofSensor.startContinuous(SENSOR_POLL_INTERVAL_MS);
        Serial.println("[SENSOR] VL53L1X initialized successfully");
    } else {
        sensorInitialized = false;
        Serial.println("[SENSOR] ERROR: Failed to initialize VL53L1X!");
        Serial.println("[SENSOR] Check wiring: SDA=GPIO21, SCL=GPIO22");
    }
    
    // Configure deep sleep wake-up source
    esp_sleep_enable_ext0_wakeup(PIN_WAKE_BUTTON, 0); // Wake on LOW (button pressed)
    Serial.printf("[SLEEP] Wake-up configured on GPIO%d (active LOW)\n", PIN_WAKE_BUTTON);
    
    // Transition to connecting state
    transitionToState(STATE_CONNECTING);
}

// ============================================================================
// MAIN LOOP - STATE MACHINE
// ============================================================================

void loop() {
    // Update non-blocking buzzer
    updateBuzzer();
    
    // State machine
    switch (currentState) {
        case STATE_STARTUP:
            // Should not reach here, handled in setup()
            transitionToState(STATE_CONNECTING);
            break;
            
        case STATE_CONNECTING:
            handleConnectingState();
            break;
            
        case STATE_WAITING_FOR_SIGNAL:
            handleWaitingState();
            break;
            
        case STATE_ACTIVE_POLLING:
            handleActivePollingState();
            break;
            
        case STATE_RECONNECTING:
            handleReconnectingState();
            break;
            
        case STATE_SLEEP:
            enterDeepSleep();
            break;
    }
}

// ============================================================================
// STATE HANDLERS
// ============================================================================

/**
 * Handle CONNECTING state
 * Attempts to connect to WiFi with 5-minute timeout
 */
void handleConnectingState() {
    if (connectWiFi()) {
        // WiFi connected, now connect to server
        Serial.println("[WIFI] Connected to hotspot");
        Serial.printf("[WIFI] IP Address: %s\n", WiFi.localIP().toString().c_str());
        Serial.printf("[WIFI] Signal strength: %d dBm\n", WiFi.RSSI());
        
        // Attempt server connection
        if (connectToServer()) {
            transitionToState(STATE_WAITING_FOR_SIGNAL);
        } else {
            Serial.println("[SERVER] Failed to connect to RPI server");
            // Continue trying within timeout period
        }
    }
    
    // Check for timeout
    if (millis() - wifiStartTime > WIFI_TIMEOUT_MS) {
        Serial.println("[TIMEOUT] WiFi connection timeout (5 minutes)");
        transitionToState(STATE_SLEEP);
    }
}

/**
 * Handle WAITING_FOR_SIGNAL state
 * Waits for START command from RPI server
 */
void handleWaitingState() {
    // Check WiFi connection
    if (!isWiFiConnected()) {
        Serial.println("[WIFI] Connection lost while waiting for signal");
        transitionToState(STATE_RECONNECTING);
        return;
    }
    
    // Check server connection
    if (!isServerConnected()) {
        Serial.println("[SERVER] Connection lost while waiting for signal");
        transitionToState(STATE_RECONNECTING);
        return;
    }
    
    // Send keepalive periodically
    if (millis() - lastKeepaliveTime > KEEPALIVE_INTERVAL_MS) {
        sendToServer("keepalive");
        lastKeepaliveTime = millis();
    }
    
    // Handle incoming server data
    handleServerData();
}

/**
 * Handle ACTIVE_POLLING state
 * Continuously polls ToF sensor and reports detections
 */
void handleActivePollingState() {
    unsigned long currentMillis = millis();
    
    // Periodic connection check (less frequent to reduce overhead)
    if (currentMillis - lastConnectionCheckTime > CONNECTION_CHECK_MS) {
        lastConnectionCheckTime = currentMillis;
        
        if (!isWiFiConnected() || !isServerConnected()) {
            Serial.println("[CONNECTION] Lost during active polling");
            transitionToState(STATE_RECONNECTING);
            return;
        }
    }
    
    // Poll ToF sensor
    if (currentMillis - lastSensorPollTime >= SENSOR_POLL_INTERVAL_MS) {
        lastSensorPollTime = currentMillis;
        pollToFSensor();
    }
    
    // Send keepalive
    if (currentMillis - lastKeepaliveTime > KEEPALIVE_INTERVAL_MS) {
        sendToServer("keepalive");
        lastKeepaliveTime = currentMillis;
    }
    
    // Handle incoming server commands (e.g., STOP)
    handleServerData();
}

/**
 * Handle RECONNECTING state
 * Attempts to reconnect with 5-minute timeout
 */
void handleReconnectingState() {
    static bool wasReconnecting = false;
    
    if (!wasReconnecting) {
        reconnectStartTime = millis();
        wifiRetryCount = 0;
        wasReconnecting = true;
        WiFi.disconnect();
        delay(100);
    }
    
    // Check timeout
    if (millis() - reconnectStartTime > RECONNECT_TIMEOUT_MS) {
        Serial.println("[RECONNECT] Timeout reached (5 minutes)");
        wasReconnecting = false;
        transitionToState(STATE_SLEEP);
        return;
    }
    
    // Attempt reconnection
    if (WiFi.status() != WL_CONNECTED) {
        Serial.printf("[RECONNECT] Attempting WiFi connection (attempt %d)...\n", wifiRetryCount + 1);
        
        WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
        
        unsigned long retryDelay = getExponentialBackoff(wifiRetryCount);
        unsigned long waitStart = millis();
        
        while (WiFi.status() != WL_CONNECTED && millis() - waitStart < retryDelay) {
            delay(100);
            updateBuzzer();
        }
        
        wifiRetryCount++;
    }
    
    if (WiFi.status() == WL_CONNECTED) {
        Serial.println("[RECONNECT] WiFi reconnected!");
        
        if (connectToServer()) {
            Serial.println("[RECONNECT] Server reconnected!");
            wasReconnecting = false;
            sendToServer("reconnected");
            transitionToState(STATE_ACTIVE_POLLING);
        }
    }
}

// ============================================================================
// WIFI FUNCTIONS
// ============================================================================

/**
 * Connect to WiFi with exponential backoff retry
 * @return true if connected, false if still trying
 */
bool connectWiFi() {
    static bool wifiStarted = false;
    static unsigned long lastRetryTime = 0;
    
    if (!wifiStarted) {
        Serial.println("[WIFI] Starting connection process...");
        Serial.printf("[WIFI] SSID: %s\n", WIFI_SSID);
        
        WiFi.mode(WIFI_STA);
        WiFi.setAutoReconnect(true);
        WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
        
        wifiStarted = true;
        wifiStartTime = millis();
        lastRetryTime = millis();
        wifiRetryCount = 0;
    }
    
    if (WiFi.status() == WL_CONNECTED) {
        wifiStarted = false; // Reset for next time
        return true;
    }
    
    // Implement exponential backoff retry
    unsigned long backoffTime = getExponentialBackoff(wifiRetryCount);
    
    if (millis() - lastRetryTime > backoffTime) {
        Serial.printf("[WIFI] Connection attempt %d (backoff: %lu ms)...\n", 
                      wifiRetryCount + 1, backoffTime);
        
        // Print current status
        switch (WiFi.status()) {
            case WL_IDLE_STATUS:
                Serial.println("[WIFI] Status: Idle");
                break;
            case WL_NO_SSID_AVAIL:
                Serial.println("[WIFI] Status: SSID not found");
                break;
            case WL_CONNECT_FAILED:
                Serial.println("[WIFI] Status: Connection failed");
                break;
            case WL_DISCONNECTED:
                Serial.println("[WIFI] Status: Disconnected");
                break;
            default:
                Serial.printf("[WIFI] Status: %d\n", WiFi.status());
                break;
        }
        
        lastRetryTime = millis();
        wifiRetryCount++;
        
        // Restart WiFi connection after several failures
        if (wifiRetryCount % 5 == 0) {
            Serial.println("[WIFI] Restarting WiFi...");
            WiFi.disconnect();
            delay(100);
            WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
        }
    }
    
    return false;
}

/**
 * Check if WiFi is currently connected
 */
bool isWiFiConnected() {
    return WiFi.status() == WL_CONNECTED;
}

/**
 * Calculate exponential backoff delay
 */
unsigned long getExponentialBackoff(int retryCount) {
    unsigned long delay = WIFI_RETRY_BASE_MS * (1 << min(retryCount, 5));
    return min(delay, (unsigned long)WIFI_RETRY_MAX_MS);
}

// ============================================================================
// SERVER COMMUNICATION FUNCTIONS
// ============================================================================

/**
 * Connect to RPI5 TCP server
 */
bool connectToServer() {
    Serial.printf("[SERVER] Connecting to %s:%d...\n", SERVER_IP, SERVER_PORT);
    
    if (tcpClient.connected()) {
        tcpClient.stop();
    }
    
    if (tcpClient.connect(SERVER_IP, SERVER_PORT)) {
        Serial.println("[SERVER] Connected to RPI5 server");
        serverConnected = true;
        
        // Send connection announcement
        sendToServer("connected");
        
        return true;
    } else {
        Serial.println("[SERVER] Failed to connect to server");
        serverConnected = false;
        return false;
    }
}

/**
 * Check if server connection is alive
 */
bool isServerConnected() {
    return tcpClient.connected();
}

/**
 * Handle incoming data from server
 */
void handleServerData() {
    if (!tcpClient.available()) {
        return;
    }
    
    // Read incoming JSON message
    String incoming = tcpClient.readStringUntil('\n');
    incoming.trim();
    
    if (incoming.length() == 0) {
        return;
    }
    
    Serial.printf("[SERVER] Received: %s\n", incoming.c_str());
    
    // Parse JSON
    StaticJsonDocument<256> doc;
    DeserializationError error = deserializeJson(doc, incoming);
    
    if (error) {
        Serial.printf("[SERVER] JSON parse error: %s\n", error.c_str());
        return;
    }
    
    // Handle commands
    const char* command = doc["command"];
    
    if (command == nullptr) {
        Serial.println("[SERVER] No command field in message");
        return;
    }
    
    if (strcmp(command, "START") == 0) {
        Serial.println("[COMMAND] Received START - beginning sensor polling");
        triggerBuzzer(); // Feedback beep
        transitionToState(STATE_ACTIVE_POLLING);
    }
    else if (strcmp(command, "STOP") == 0) {
        Serial.println("[COMMAND] Received STOP - pausing sensor polling");
        triggerBuzzer();
        transitionToState(STATE_WAITING_FOR_SIGNAL);
    }
    else if (strcmp(command, "SLEEP") == 0) {
        Serial.println("[COMMAND] Received SLEEP - entering deep sleep");
        triggerBuzzer();
        transitionToState(STATE_SLEEP);
    }
    else if (strcmp(command, "PING") == 0) {
        Serial.println("[COMMAND] Received PING - sending PONG");
        sendToServer("pong");
    }
    else {
        Serial.printf("[COMMAND] Unknown command: %s\n", command);
    }
}

/**
 * Send JSON message to server
 */
void sendToServer(const char* eventType, int distance) {
    if (!tcpClient.connected()) {
        Serial.println("[SERVER] Cannot send - not connected");
        return;
    }
    
    StaticJsonDocument<256> doc;
    doc["device"] = DEVICE_NAME;
    doc["event"] = eventType;
    doc["timestamp"] = millis();
    
    if (distance >= 0) {
        doc["distance"] = distance;
    }
    
    String output;
    serializeJson(doc, output);
    output += "\n";
    
    tcpClient.print(output);
    
    // Only log non-keepalive messages to reduce spam
    if (strcmp(eventType, "keepalive") != 0) {
        Serial.printf("[SERVER] Sent: %s", output.c_str());
    }
}

// ============================================================================
// TOF SENSOR FUNCTIONS
// ============================================================================

/**
 * Poll ToF sensor and handle detections
 */
void pollToFSensor() {
    if (!sensorInitialized) {
        return;
    }
    
    // Check if new data is available
    if (!tofSensor.dataReady()) {
        return;
    }
    
    // Read distance
    uint16_t distance = tofSensor.read(false); // Don't block
    
    // Check for read errors
    if (tofSensor.timeoutOccurred()) {
        Serial.println("[SENSOR] Timeout error!");
        return;
    }
    
    // Check for valid reading
    if (distance == 0 || distance > 8000) {
        // Invalid reading (out of range)
        return;
    }
    
    // Detection logic with debouncing
    bool currentlyDetected = (distance < TOF_DETECTION_THRESHOLD_MM);
    unsigned long currentMillis = millis();
    
    // Detect rising edge (object just entered range)
    if (currentlyDetected && !objectDetected) {
        // Check debounce
        if (currentMillis - lastDetectionTime > DETECTION_DEBOUNCE_MS) {
            handleDetection(distance);
            lastDetectionTime = currentMillis;
        }
    }
    
    objectDetected = currentlyDetected;
}

/**
 * Handle object detection event
 */
void handleDetection(uint16_t distance) {
    Serial.printf("[DETECTION] Object detected at %d mm\n", distance);
    
    // Trigger buzzer feedback
    triggerBuzzer();
    
    // Send detection to server
    sendToServer("detection", distance);
    
    // Visual feedback
    digitalWrite(PIN_STATUS_LED, HIGH);
    delay(50);
    digitalWrite(PIN_STATUS_LED, LOW);
}

// ============================================================================
// BUZZER FUNCTIONS
// ============================================================================

/**
 * Start buzzer beep (non-blocking)
 */
void triggerBuzzer() {
    digitalWrite(PIN_BUZZER, HIGH);
    buzzerActive = true;
    buzzerStartTime = millis();
}

/**
 * Update buzzer state (call in loop)
 */
void updateBuzzer() {
    if (buzzerActive && (millis() - buzzerStartTime >= BUZZER_DURATION_MS)) {
        digitalWrite(PIN_BUZZER, LOW);
        buzzerActive = false;
    }
}

// ============================================================================
// DEEP SLEEP FUNCTIONS
// ============================================================================

/**
 * Enter deep sleep mode
 */
void enterDeepSleep() {
    Serial.println("\n[SLEEP] Preparing to enter deep sleep...");
    
    // Stop sensor
    if (sensorInitialized) {
        tofSensor.stopContinuous();
        Serial.println("[SLEEP] ToF sensor stopped");
    }
    
    // Disconnect from server and WiFi
    if (tcpClient.connected()) {
        sendToServer("sleeping");
        delay(100);
        tcpClient.stop();
        Serial.println("[SLEEP] Server connection closed");
    }
    
    WiFi.disconnect(true);
    WiFi.mode(WIFI_OFF);
    Serial.println("[SLEEP] WiFi disabled");
    
    // Turn off all outputs
    digitalWrite(PIN_STATUS_LED, LOW);
    digitalWrite(PIN_BUZZER, LOW);
    
    // Final message
    Serial.println("[SLEEP] Entering deep sleep mode...");
    Serial.println("[SLEEP] Press wake button to restart");
    Serial.println("========================================\n");
    Serial.flush();
    
    // Enter deep sleep
    esp_deep_sleep_start();
    
    // Code never reaches here
}

/**
 * Print the reason for waking up
 */
void printWakeupReason() {
    esp_sleep_wakeup_cause_t wakeup_reason = esp_sleep_get_wakeup_cause();
    
    Serial.print("[WAKEUP] Reason: ");
    
    switch (wakeup_reason) {
        case ESP_SLEEP_WAKEUP_EXT0:
            Serial.println("External wakeup (button press on GPIO4)");
            break;
        case ESP_SLEEP_WAKEUP_EXT1:
            Serial.println("External wakeup (EXT1)");
            break;
        case ESP_SLEEP_WAKEUP_TIMER:
            Serial.println("Timer wakeup");
            break;
        case ESP_SLEEP_WAKEUP_TOUCHPAD:
            Serial.println("Touchpad wakeup");
            break;
        case ESP_SLEEP_WAKEUP_ULP:
            Serial.println("ULP program wakeup");
            break;
        default:
            Serial.printf("Other/Power-on reset (%d)\n", wakeup_reason);
            break;
    }
}

// ============================================================================
// UTILITY FUNCTIONS
// ============================================================================

/**
 * Transition to a new state with logging
 */
void transitionToState(SystemState newState) {
    if (newState != currentState) {
        Serial.printf("[STATE] %s -> %s\n", 
                      stateNames[currentState], 
                      stateNames[newState]);
        previousState = currentState;
        currentState = newState;
        
        // State entry actions
        switch (newState) {
            case STATE_CONNECTING:
                wifiRetryCount = 0;
                break;
                
            case STATE_WAITING_FOR_SIGNAL:
                lastKeepaliveTime = millis();
                Serial.println("[STATUS] Waiting for START command from RPI...");
                break;
                
            case STATE_ACTIVE_POLLING:
                lastSensorPollTime = millis();
                lastKeepaliveTime = millis();
                lastConnectionCheckTime = millis();
                objectDetected = false;
                Serial.println("[STATUS] Active polling mode - monitoring ToF sensor");
                break;
                
            case STATE_RECONNECTING:
                reconnectStartTime = millis();
                Serial.println("[STATUS] Attempting to reconnect...");
                break;
                
            case STATE_SLEEP:
                // Handled in loop
                break;
                
            default:
                break;
        }
    }
}

/**
 * Blink status LED
 */
void blinkLED(int times, int delayMs) {
    for (int i = 0; i < times; i++) {
        digitalWrite(PIN_STATUS_LED, HIGH);
        delay(delayMs);
        digitalWrite(PIN_STATUS_LED, LOW);
        delay(delayMs);
    }
}

// ============================================================================
// END OF FIRMWARE
// ============================================================================
