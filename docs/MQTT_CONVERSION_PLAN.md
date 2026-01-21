# BLE to MQTT Conversion Plan

## Overview

Convert the BrainMove system from Bluetooth Low Energy (BLE) to MQTT over WiFi for communication between ESP32 devices and the Raspberry Pi.

### Current Architecture (BLE)
```
ESP32 ──(BLE)──► RPI (Bleak) ──► Python Backend ──(Socket.io)──► Browser
```

### Target Architecture (MQTT)
```
ESP32 ──(WiFi/MQTT)──► Mosquitto (RPI) ──► Python Backend ──(Socket.io)──► Browser
```

### Benefits
- **Lower latency**: WiFi is faster than BLE
- **No 2.4GHz interference**: BLE and WiFi won't compete
- **Simpler code**: No BLE thread management needed
- **Better range**: WiFi covers more area than BLE
- **Easier debugging**: MQTT messages can be monitored with tools

---

## Phase 1: RPI Setup (Mosquitto Broker)

### 1.1 Install Mosquitto
```bash
sudo apt update
sudo apt install mosquitto mosquitto-clients
```

### 1.2 Configure Mosquitto
Create `/etc/mosquitto/conf.d/brainmove.conf`:
```conf
# Listen on all interfaces
listener 1883 0.0.0.0

# Allow anonymous connections (local network only)
allow_anonymous true

# Disable persistence for speed
persistence false

# Optimize for low latency
max_queued_messages 100
```

### 1.3 Start and Enable
```bash
sudo systemctl enable mosquitto
sudo systemctl start mosquitto
```

### 1.4 Test
```bash
# Terminal 1: Subscribe
mosquitto_sub -h localhost -t "bm/#" -v

# Terminal 2: Publish
mosquitto_pub -h localhost -t "bm/test" -m "hello"
```

---

## Phase 2: MQTT Topic Structure

### 2.1 Topic Design (Lightweight)

| Direction | Topic | Payload | Description |
|-----------|-------|---------|-------------|
| **ESP → RPI** | `bm/{color}/detect` | `1` or `0` | Detection event |
| **ESP → RPI** | `bm/{color}/battery` | `85` | Battery percentage |
| **ESP → RPI** | `bm/{color}/status` | `online` / `offline` | Connection status |
| **RPI → ESP** | `bm/{color}/cmd` | `start` / `stop` / `correct` / `incorrect` / `sound_ok` / `sound_fail` | Commands |
| **RPI → ALL** | `bm/all/cmd` | `start` / `stop` | Broadcast commands |

Where `{color}` = `rood`, `blauw`, `geel`, `groen`

### 2.2 Payload Format (Raw/Minimal)

Keep payloads as simple strings or single values - no JSON overhead:

```
# Detection (ESP → RPI)
Topic: bm/rood/detect
Payload: 1

# Battery (ESP → RPI)
Topic: bm/rood/battery
Payload: 78

# Status (ESP → RPI - Last Will)
Topic: bm/rood/status
Payload: offline

# Command (RPI → ESP)
Topic: bm/rood/cmd
Payload: correct
```

### 2.3 QoS Levels

| Message Type | QoS | Reason |
|--------------|-----|--------|
| Detection | 0 | Speed over reliability |
| Commands | 0 | Speed, can retry |
| Battery | 0 | Not critical |
| Status (LWT) | 1 | Must be delivered |

---

## Phase 3: Python Backend Changes

### 3.1 Install Dependencies
```bash
pip install aiomqtt
```

Add to `requirements.txt`:
```
aiomqtt>=2.0.0
```

### 3.2 New File: `backend/src/services/mqtt_client.py`

```python
"""
MQTT Client for BrainMove - Replaces BLE communication
"""
import asyncio
import logging
from typing import Callable, Optional
import aiomqtt

logger = logging.getLogger(__name__)

BROKER_HOST = "localhost"
BROKER_PORT = 1883
TOPIC_PREFIX = "bm"

COLORS = ["rood", "blauw", "geel", "groen"]


class MQTTDeviceManager:
    """
    Manages ESP32 devices via MQTT.
    Replaces the BLE-based DeviceManager.
    """

    def __init__(self, sio=None):
        self._sio = sio
        self._client: Optional[aiomqtt.Client] = None
        self._connected = False
        self._running = False

        # Device state
        self._apparaten = {color: {"status": "offline", "batterij": None} for color in COLORS}
        self._detectie_callback: Optional[Callable] = None

    @property
    def apparaten(self):
        return self._apparaten.copy()

    async def start(self):
        """Start MQTT client and subscribe to topics."""
        self._running = True

        while self._running:
            try:
                async with aiomqtt.Client(BROKER_HOST, BROKER_PORT) as client:
                    self._client = client
                    self._connected = True
                    logger.info("MQTT connected to broker")

                    # Subscribe to all device topics
                    await client.subscribe(f"{TOPIC_PREFIX}/+/detect")
                    await client.subscribe(f"{TOPIC_PREFIX}/+/battery")
                    await client.subscribe(f"{TOPIC_PREFIX}/+/status")

                    # Process incoming messages
                    async for message in client.messages:
                        await self._handle_message(message)

            except aiomqtt.MqttError as e:
                logger.error(f"MQTT error: {e}")
                self._connected = False
                if self._running:
                    await asyncio.sleep(2)  # Reconnect delay
            except asyncio.CancelledError:
                break

        self._connected = False
        logger.info("MQTT client stopped")

    async def stop(self):
        """Stop MQTT client."""
        self._running = False

    async def _handle_message(self, message: aiomqtt.Message):
        """Process incoming MQTT message."""
        topic_parts = str(message.topic).split("/")
        if len(topic_parts) != 3:
            return

        _, color, msg_type = topic_parts
        payload = message.payload.decode() if message.payload else ""

        if color not in COLORS:
            return

        if msg_type == "detect":
            await self._handle_detection(color, payload)
        elif msg_type == "battery":
            await self._handle_battery(color, payload)
        elif msg_type == "status":
            await self._handle_status(color, payload)

    async def _handle_detection(self, color: str, payload: str):
        """Handle detection event from ESP."""
        logger.info(f"Detection: {color} = {payload}")

        if self._detectie_callback:
            self._detectie_callback({
                "apparaat_naam": f"BM-{color.capitalize()}",
                "kleur": color,
                "detectie_bool": payload == "1"
            })

        # Emit to frontend
        if self._sio:
            await self._sio.emit("device_detection", {"kleur": color})

    async def _handle_battery(self, color: str, payload: str):
        """Handle battery update from ESP."""
        try:
            percentage = int(payload)
            self._apparaten[color]["batterij"] = percentage
            logger.debug(f"Battery: {color} = {percentage}%")
        except ValueError:
            pass

    async def _handle_status(self, color: str, payload: str):
        """Handle status update (online/offline) from ESP."""
        old_status = self._apparaten[color]["status"]
        new_status = payload  # "online" or "offline"
        self._apparaten[color]["status"] = new_status

        logger.info(f"Status: {color} = {new_status}")

        if self._sio and old_status != new_status:
            event = "device_connected" if new_status == "online" else "device_disconnected"
            await self._sio.emit(event, {
                "kleur": color,
                "status": new_status,
                "batterij": self._apparaten[color]["batterij"]
            })

    # ==================== Commands (RPI → ESP) ====================

    async def _publish(self, topic: str, payload: str):
        """Publish message to MQTT broker."""
        if self._client and self._connected:
            await self._client.publish(topic, payload, qos=0)

    async def send_command(self, color: str, command: str):
        """Send command to specific device."""
        await self._publish(f"{TOPIC_PREFIX}/{color}/cmd", command)

    async def send_command_all(self, command: str):
        """Send command to all devices."""
        await self._publish(f"{TOPIC_PREFIX}/all/cmd", command)

    async def start_alle(self):
        """Start polling on all devices."""
        await self.send_command_all("start")
        logger.info("Sent START to all devices")

    async def stop_alle(self):
        """Stop polling on all devices."""
        await self.send_command_all("stop")
        logger.info("Sent STOP to all devices")

    async def set_correct_kegel(self, color: str):
        """Mark a cone as the correct target."""
        await self.send_command(color.lower(), "correct")
        logger.info(f"Set {color} as correct")

    async def reset_correct_kegel(self, color: str):
        """Reset a cone to not be the target."""
        await self.send_command(color.lower(), "incorrect")

    async def play_sound_correct(self, color: str):
        """Play correct sound on device."""
        await self.send_command(color.lower(), "sound_ok")

    async def play_sound_incorrect(self, color: str):
        """Play incorrect sound on device."""
        await self.send_command(color.lower(), "sound_fail")

    # ==================== Callbacks ====================

    def zet_detectie_callback(self, callback: Optional[Callable]):
        """Set detection callback for game logic."""
        self._detectie_callback = callback

    def verwijder_alle_laatste_detecties(self):
        """Clear detection state (compatibility)."""
        pass  # Not needed with MQTT

    def verkrijg_alle_laatste_detecties(self):
        """Get last detections (compatibility)."""
        return {}

    def verkrijg_apparaten_status(self) -> list:
        """Get status of all devices."""
        return [
            {
                "kleur": color,
                "status": data["status"],
                "batterij": data["batterij"]
            }
            for color, data in self._apparaten.items()
        ]
```

### 3.3 Update `main.py`

Replace BLE DeviceManager with MQTT:

```python
# OLD (remove)
from backend.src.services.device_manager import DeviceManager

# NEW (add)
from backend.src.services.mqtt_client import MQTTDeviceManager

# OLD (remove)
device_manager = DeviceManager(sio=sio)

# NEW (add)
device_manager = MQTTDeviceManager(sio=sio)

# Update lifespan
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Start MQTT client
    mqtt_task = asyncio.create_task(device_manager.start())

    yield

    # Stop MQTT client
    await device_manager.stop()
    mqtt_task.cancel()
```

### 3.4 Update `colorgame()` Function

The game logic stays mostly the same, but remove BLE-specific code:

```python
async def colorgame(aantal_rondes, kleuren, snelheid):
    # Detection event handling
    detectie_event = asyncio.Event()
    detected_color = {}

    def on_detectie(gebeurtenis):
        detected_color.clear()
        detected_color.update(gebeurtenis)
        detectie_event.set()

    device_manager.zet_detectie_callback(on_detectie)

    # Start all devices
    await device_manager.start_alle()

    colorgame_rondes = []
    max_tijd = float(snelheid)

    for ronde in range(1, aantal_rondes + 1):
        gekozen_kleur = random.choice(kleuren).upper()

        # Emit to frontend
        await sio.emit('gekozen_kleur', {
            'rondenummer': ronde,
            'maxronden': aantal_rondes,
            'kleur': gekozen_kleur
        })

        # Set correct cone
        await device_manager.set_correct_kegel(gekozen_kleur)

        # Wait for detection
        detectie_event.clear()
        detected_color.clear()
        starttijd = time.time()

        try:
            await asyncio.wait_for(detectie_event.wait(), timeout=max_tijd)
            reactietijd = round(time.time() - starttijd, 2)

            # Check if correct color
            if detected_color.get("kleur", "").lower() == gekozen_kleur.lower():
                status = "correct"
            else:
                status = "fout"
                reactietijd += max_tijd  # Penalty

        except asyncio.TimeoutError:
            reactietijd = max_tijd
            status = "te laat"

        colorgame_rondes.append({
            "rondenummer": ronde,
            "waarde": reactietijd,
            "uitkomst": status
        })

        # Reset cone
        await device_manager.reset_correct_kegel(gekozen_kleur)

    # Stop all devices
    await device_manager.stop_alle()
    device_manager.zet_detectie_callback(None)

    await sio.emit('game_einde', {"status": "game gedaan"})
    return colorgame_rondes
```

### 3.5 Files to Remove/Archive

After migration, these files are no longer needed:
- `backend/src/services/cone.py` (BLE device class)
- `backend/src/services/ble_thread.py` (BLE thread manager)
- `backend/src/services/device_manager.py` (BLE device manager)

---

## Phase 4: ESP32 Firmware Changes

### 4.1 Required Libraries (Arduino/PlatformIO)

```cpp
#include <WiFi.h>
#include <PubSubClient.h>  // MQTT client
```

### 4.2 New ESP32 Firmware Structure

```cpp
// config.h
#define WIFI_SSID "BrainMove"           // RPI hotspot SSID
#define WIFI_PASSWORD "your_password"    // RPI hotspot password
#define MQTT_SERVER "10.42.0.1"          // RPI IP
#define MQTT_PORT 1883

#define DEVICE_COLOR "rood"              // Change per device: rood, blauw, geel, groen

// Topic strings
#define TOPIC_DETECT   "bm/" DEVICE_COLOR "/detect"
#define TOPIC_BATTERY  "bm/" DEVICE_COLOR "/battery"
#define TOPIC_STATUS   "bm/" DEVICE_COLOR "/status"
#define TOPIC_CMD      "bm/" DEVICE_COLOR "/cmd"
#define TOPIC_CMD_ALL  "bm/all/cmd"
```

### 4.3 Main Firmware Code

```cpp
// main.cpp
#include <WiFi.h>
#include <PubSubClient.h>
#include "config.h"

WiFiClient wifiClient;
PubSubClient mqtt(wifiClient);

bool isPolling = false;
bool isCorrectCone = false;
unsigned long lastBatteryReport = 0;
const unsigned long BATTERY_INTERVAL = 60000;  // 60 seconds

void setup() {
    Serial.begin(115200);

    // Initialize hardware (button, LED, buzzer)
    setupHardware();

    // Connect to WiFi
    connectWiFi();

    // Setup MQTT
    mqtt.setServer(MQTT_SERVER, MQTT_PORT);
    mqtt.setCallback(onMqttMessage);

    connectMQTT();
}

void loop() {
    // Maintain connections
    if (WiFi.status() != WL_CONNECTED) {
        connectWiFi();
    }

    if (!mqtt.connected()) {
        connectMQTT();
    }

    mqtt.loop();

    // Poll sensor if active
    if (isPolling) {
        checkDetection();
    }

    // Periodic battery report
    if (millis() - lastBatteryReport > BATTERY_INTERVAL) {
        reportBattery();
        lastBatteryReport = millis();
    }
}

void connectWiFi() {
    Serial.print("Connecting to WiFi...");
    WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

    int attempts = 0;
    while (WiFi.status() != WL_CONNECTED && attempts < 20) {
        delay(500);
        Serial.print(".");
        attempts++;
    }

    if (WiFi.status() == WL_CONNECTED) {
        Serial.println(" Connected!");
        Serial.print("IP: ");
        Serial.println(WiFi.localIP());
    } else {
        Serial.println(" Failed!");
    }
}

void connectMQTT() {
    while (!mqtt.connected()) {
        Serial.print("Connecting to MQTT...");

        // Connect with Last Will Testament (LWT)
        if (mqtt.connect(
            DEVICE_COLOR,           // Client ID
            NULL,                   // Username (none)
            NULL,                   // Password (none)
            TOPIC_STATUS,           // LWT topic
            1,                      // LWT QoS
            true,                   // LWT retain
            "offline"               // LWT message
        )) {
            Serial.println(" Connected!");

            // Subscribe to command topics
            mqtt.subscribe(TOPIC_CMD);
            mqtt.subscribe(TOPIC_CMD_ALL);

            // Publish online status
            mqtt.publish(TOPIC_STATUS, "online", true);

            // Report initial battery
            reportBattery();
        } else {
            Serial.print(" Failed, rc=");
            Serial.println(mqtt.state());
            delay(2000);
        }
    }
}

void onMqttMessage(char* topic, byte* payload, unsigned int length) {
    // Convert payload to string
    char msg[length + 1];
    memcpy(msg, payload, length);
    msg[length] = '\0';

    Serial.printf("MQTT: %s = %s\n", topic, msg);

    // Handle commands
    if (strcmp(msg, "start") == 0) {
        isPolling = true;
        Serial.println("Polling STARTED");
    }
    else if (strcmp(msg, "stop") == 0) {
        isPolling = false;
        isCorrectCone = false;
        Serial.println("Polling STOPPED");
    }
    else if (strcmp(msg, "correct") == 0) {
        isCorrectCone = true;
        Serial.println("Marked as CORRECT cone");
    }
    else if (strcmp(msg, "incorrect") == 0) {
        isCorrectCone = false;
        Serial.println("Marked as INCORRECT cone");
    }
    else if (strcmp(msg, "sound_ok") == 0) {
        playCorrectSound();
    }
    else if (strcmp(msg, "sound_fail") == 0) {
        playIncorrectSound();
    }
}

void checkDetection() {
    // Read your sensor (button, IR, touch, etc.)
    bool detected = readSensor();

    if (detected) {
        // Publish detection immediately
        mqtt.publish(TOPIC_DETECT, "1");
        Serial.println("Detection sent!");

        // Brief debounce
        delay(100);
    }
}

void reportBattery() {
    int percentage = readBatteryPercentage();
    char payload[4];
    snprintf(payload, sizeof(payload), "%d", percentage);
    mqtt.publish(TOPIC_BATTERY, payload);
    Serial.printf("Battery: %d%%\n", percentage);
}

// ==================== Hardware Functions (implement these) ====================

void setupHardware() {
    // Setup your pins: button, LED, buzzer, battery ADC
    // Example:
    // pinMode(BUTTON_PIN, INPUT_PULLUP);
    // pinMode(LED_PIN, OUTPUT);
}

bool readSensor() {
    // Read your detection sensor
    // Example for button:
    // return digitalRead(BUTTON_PIN) == LOW;
    return false;
}

int readBatteryPercentage() {
    // Read battery voltage and convert to percentage
    // Example:
    // int raw = analogRead(BATTERY_PIN);
    // float voltage = raw * (3.3 / 4095.0) * 2;  // Voltage divider
    // return map(voltage * 100, 320, 420, 0, 100);
    return 100;
}

void playCorrectSound() {
    // Play success tone
    // Example: tone(BUZZER_PIN, 1000, 200);
}

void playIncorrectSound() {
    // Play failure tone
    // Example: tone(BUZZER_PIN, 400, 500);
}
```

### 4.4 PlatformIO Configuration

```ini
; platformio.ini
[env:esp32]
platform = espressif32
board = esp32dev
framework = arduino
lib_deps =
    knolleary/PubSubClient@^2.8
monitor_speed = 115200
```

### 4.5 Device-Specific Configuration

Create 4 firmware variants, one per device. Only change `DEVICE_COLOR`:

| Device | DEVICE_COLOR |
|--------|--------------|
| Blue cone | `"blauw"` |
| Red cone | `"rood"` |
| Yellow cone | `"geel"` |
| Green cone | `"groen"` |

---

## Phase 5: Environment Configuration

### 5.1 Update `backend/.env`

Remove BLE-specific vars, add MQTT:

```env
# MQTT Configuration
MQTT_BROKER=localhost
MQTT_PORT=1883

# Remove these BLE vars:
# APPARAAT_BM_BLAUW=...
# APPARAAT_BM_ROOD=...
# APPARAAT_BM_GEEL=...
# APPARAAT_BM_GROEN=...
# VEILIGHEIDS_BYTE=...
# SCAN_TIMEOUT=...
# STRIKTE_WHITELIST=...

# Keep these:
HARDWARE_DELAY=0.02  # Can be lower with MQTT
```

### 5.2 RPI Hotspot Configuration

Ensure ESP32 devices can connect to the RPI hotspot:

```bash
# /etc/NetworkManager/system-connections/Hotspot.nmconnection
[wifi]
ssid=BrainMove

[wifi-security]
key-mgmt=wpa-psk
psk=your_secure_password
```

---

## Phase 6: Testing

### 6.1 Test MQTT Broker
```bash
# Subscribe to all BrainMove topics
mosquitto_sub -h localhost -t "bm/#" -v
```

### 6.2 Test ESP32 Connection
Flash firmware, check serial output:
```
Connecting to WiFi... Connected!
IP: 10.42.0.50
Connecting to MQTT... Connected!
```

### 6.3 Test Commands
```bash
# Send start command
mosquitto_pub -h localhost -t "bm/all/cmd" -m "start"

# Send correct to red
mosquitto_pub -h localhost -t "bm/rood/cmd" -m "correct"
```

### 6.4 Test Detection
Press button on ESP32, verify:
```
bm/rood/detect 1
```

### 6.5 Test Full Game
Run colorgame, verify:
1. Frontend shows color
2. ESP32 receives `correct` command
3. Detection sent via MQTT
4. Backend processes and emits to frontend

---

## Phase 7: Migration Checklist

### Backend
- [ ] Install `aiomqtt` dependency
- [ ] Create `mqtt_client.py`
- [ ] Update `main.py` imports and initialization
- [ ] Update `colorgame()` function
- [ ] Update `memorygame()` function (if using devices)
- [ ] Update `/devices/status` endpoint
- [ ] Remove BLE files (cone.py, ble_thread.py, device_manager.py)
- [ ] Update `.env` configuration
- [ ] Test all game modes

### ESP32
- [ ] Create new firmware with WiFi/MQTT
- [ ] Configure WiFi credentials
- [ ] Configure MQTT broker address
- [ ] Implement detection publishing
- [ ] Implement command handling
- [ ] Implement battery reporting
- [ ] Flash all 4 devices with correct color config
- [ ] Test each device individually

### Infrastructure
- [ ] Install Mosquitto on RPI
- [ ] Configure Mosquitto for local network
- [ ] Configure RPI hotspot with static SSID/password
- [ ] Test ESP32 can connect to hotspot
- [ ] Test MQTT communication

---

## Rollback Plan

If issues arise, the BLE code can be restored:
1. Keep backup of BLE files
2. Revert `main.py` to use `DeviceManager`
3. Restore `.env` with MAC addresses
4. Flash original BLE firmware to ESP32s

---

## Performance Comparison

| Metric | BLE | MQTT |
|--------|-----|------|
| Latency | 50-200ms | 5-20ms |
| Range | ~10m | ~50m (WiFi) |
| Interference | High (2.4GHz shared) | Low |
| Power (ESP32) | Lower | Higher |
| Complexity | High (threads, bleak) | Low |
| Debugging | Hard | Easy (mosquitto_sub) |

---

## Timeline Estimate

| Phase | Duration |
|-------|----------|
| Phase 1: RPI Setup | 30 min |
| Phase 2: Topic Design | Done (this doc) |
| Phase 3: Python Backend | 2-3 hours |
| Phase 4: ESP32 Firmware | 3-4 hours |
| Phase 5: Configuration | 30 min |
| Phase 6: Testing | 1-2 hours |
| **Total** | **~8-10 hours** |
