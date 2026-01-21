# MQTT Backend Implementation Status

## Completed Backend Changes

### 1. Created MQTT Client
**File:** [backend/src/services/mqtt_client.py](../backend/src/services/mqtt_client.py)
- ✅ Complete `MQTTDeviceManager` class
- ✅ Auto-reconnecting MQTT client
- ✅ Topic subscriptions: `bm/+/detect`, `bm/+/battery`, `bm/+/status`
- ✅ Message parsing and handling
- ✅ Socket.IO integration for frontend updates
- ✅ Command publishing to ESP32 devices
- ✅ Detection callback system

### 2. Updated Main Application
**File:** [backend/src/main.py](../backend/src/main.py)

✅ **Import Changes:**
```python
from backend.src.services.mqtt_client import MQTTDeviceManager
```

✅ **Device Manager Instantiation:**
```python
device_manager = MQTTDeviceManager(sio=sio)
```

✅ **Lifespan Management:**
```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    mqtt_task = asyncio.create_task(device_manager.start())
    yield
    await device_manager.stop()
    mqtt_task.cancel()
```

✅ **colorgame() Function:**
- Removed complex BLE device mapping
- Uses direct color-based MQTT detection
- Simplified detection callback
- Proper timeout handling

✅ **memorygame() Function:**
- Replaced blocking `input()` with async MQTT detection
- Waits for cone touches in correct sequence
- 30-second timeout per cone
- Proper error handling

✅ **Device Endpoints:**
- Updated `/devices/status` to work with MQTT
- Updated `/devices/stop-scan` (now no-op for MQTT)

### 3. Dependencies
**File:** [requirements.txt](../requirements.txt)
- ✅ Added `aiomqtt>=2.0.0`
- ✅ Marked BLE packages as deprecated

### 4. Environment Configuration
**File:** [backend/.env](../backend/.env)
- ✅ Added MQTT configuration:
  - `MQTT_BROKER_HOST=localhost`
  - `MQTT_BROKER_PORT=1883`
  - `MQTT_KEEPALIVE=60`
  - `MQTT_RECONNECT_INTERVAL=5`
- ✅ Commented out BLE configuration

## Testing Required

### Backend Testing Steps

1. **Install Dependencies:**
```bash
cd backend
pip install -r ../requirements.txt
```

2. **Install Mosquitto (if not installed):**
```bash
sudo apt update
sudo apt install mosquitto mosquitto-clients
sudo systemctl enable mosquitto
sudo systemctl start mosquitto
```

3. **Test MQTT Broker:**
```bash
# In terminal 1 - Subscribe to all topics
mosquitto_sub -h localhost -t "bm/#" -v

# In terminal 2 - Publish test message
mosquitto_pub -h localhost -t "bm/rood/detect" -m "1"
```

4. **Start Backend:**
```bash
cd backend/src
python main.py
```

5. **Monitor Logs:**
- Look for "MQTT connected successfully"
- Check for subscription confirmations
- Watch for any connection errors

6. **Test Endpoints:**
```bash
# Check device status
curl http://localhost:8000/devices/status

# Should return:
{
  "apparaten": [
    {"kleur": "blauw", "status": "offline", "batterij": null},
    {"kleur": "rood", "status": "offline", "batterij": null},
    {"kleur": "geel", "status": "offline", "batterij": null},
    {"kleur": "groen", "status": "offline", "batterij": null}
  ],
  "connected": true,
  "totaal_verwacht": 4
}
```

## Pending Tasks

### ESP32 Firmware (NOT STARTED)

**Required:** Create new firmware with WiFi + MQTT

**Key Components:**
1. WiFi connection to RPI hotspot (SSID: needs configuration)
2. MQTT client using PubSubClient library
3. Topics to publish:
   - `bm/{color}/detect` - "1" when detected, "0" when released
   - `bm/{color}/battery` - "0-100" battery percentage
   - `bm/{color}/status` - "online"/"offline" with LWT
4. Topics to subscribe:
   - `bm/{color}/cmd` - device-specific commands
   - `bm/all/cmd` - broadcast commands
5. Command handling:
   - `start` - Begin sensor polling
   - `stop` - Stop sensor polling
   - `correct` - Mark as correct target (green LED/sound)
   - `incorrect` - Reset from correct state
   - `sound_ok` - Play success sound
   - `sound_fail` - Play failure sound

**Variants Needed:** 4 firmware builds (one per color)
- BM-Blauw (blue)
- BM-Rood (red)
- BM-Geel (yellow)
- BM-Groen (green)

**Configuration per Device:**
```cpp
#define DEVICE_COLOR "rood"  // or "blauw", "geel", "groen"
```

### Infrastructure Setup

1. **Mosquitto Configuration (Optional):**
   Create `/etc/mosquitto/conf.d/brainmove.conf`:
```conf
listener 1883
allow_anonymous true
```

2. **WiFi Hotspot on RPI:**
   - Verify SSID and password
   - Ensure ESP32s can connect
   - Test MQTT connectivity from ESP32

3. **Network Testing:**
```bash
# From ESP32 (via serial monitor):
# Should see successful WiFi connection
# Should see MQTT connection to 10.42.0.1:1883
```

## Migration Checklist

- [x] Backend MQTT client created
- [x] Main.py updated for MQTT
- [x] colorgame() updated
- [x] memorygame() updated
- [x] Device endpoints updated
- [x] Dependencies updated
- [x] Environment config updated
- [ ] Install Mosquitto on RPI
- [ ] Test MQTT broker
- [ ] Create ESP32 firmware
- [ ] Flash 4 ESP32 devices
- [ ] End-to-end testing
- [ ] Remove old BLE files:
  - [ ] `backend/src/services/cone.py`
  - [ ] `backend/src/services/ble_thread.py`
  - [ ] `backend/src/services/device_manager.py`

## Expected Benefits

1. **Performance:**
   - No event loop blocking (BLE eliminated)
   - Instant socket emissions
   - Lower latency (WiFi vs BLE)

2. **Reliability:**
   - No 2.4GHz interference between BLE and WiFi
   - Auto-reconnect on both MQTT and WiFi
   - Simpler connection management

3. **Scalability:**
   - Easy to add more devices
   - Centralized broker
   - Standard MQTT protocol

## Next Steps

1. **Test current backend implementation** (install mosquitto, run backend, verify MQTT connection)
2. **Create ESP32 firmware** based on [MQTT_CONVERSION_PLAN.md](MQTT_CONVERSION_PLAN.md)
3. **Flash and test one ESP32** before flashing all 4
4. **End-to-end game testing** with real hardware
5. **Remove deprecated BLE code** after successful migration
