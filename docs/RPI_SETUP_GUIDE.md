# Raspberry Pi Setup Guide - MQTT Version

## Overview

This guide covers the complete setup of the Raspberry Pi for the MQTT-based BrainMove system.

## Prerequisites

- Raspberry Pi 4 (recommended) or Pi 3B+
- Raspberry Pi OS (Bullseye or later)
- WiFi adapter configured as hotspot
- Internet connection for initial setup

## 1. Install Mosquitto MQTT Broker

```bash
# Update package list
sudo apt update

# Install Mosquitto broker and clients
sudo apt install -y mosquitto mosquitto-clients

# Enable Mosquitto to start on boot
sudo systemctl enable mosquitto

# Start Mosquitto
sudo systemctl start mosquitto

# Verify it's running
sudo systemctl status mosquitto
```

Expected output:
```
● mosquitto.service - Mosquitto MQTT Broker
   Loaded: loaded (/lib/systemd/system/mosquitto.service; enabled)
   Active: active (running)
```

## 2. Configure Mosquitto

Create configuration file:

```bash
sudo nano /etc/mosquitto/conf.d/brainmove.conf
```

Add the following configuration:

```conf
# BrainMove MQTT Configuration

# Listen on all interfaces
listener 1883

# Allow anonymous connections (since we're on a local hotspot)
allow_anonymous true

# Logging (optional, for debugging)
log_dest file /var/log/mosquitto/mosquitto.log
log_dest stdout
log_type error
log_type warning
log_type notice
log_type information

# Connection messages
connection_messages true

# Persistence
persistence true
persistence_location /var/lib/mosquitto/

# Max queued messages (increase for reliability)
max_queued_messages 1000
```

Restart Mosquitto to apply changes:

```bash
sudo systemctl restart mosquitto
```

## 3. Test MQTT Broker

### Terminal 1 - Subscribe to all topics:

```bash
mosquitto_sub -h localhost -t "bm/#" -v
```

### Terminal 2 - Publish test message:

```bash
mosquitto_pub -h localhost -t "bm/test" -m "hello"
```

You should see in Terminal 1:
```
bm/test hello
```

## 4. Configure WiFi Hotspot

### Check Current Hotspot Status

```bash
sudo systemctl status hostapd
```

### Hotspot Configuration

If not already configured, set up hotspot with these settings:

**SSID:** `BrainMove` (or your preferred name)
**Password:** `brainmove2025` (or your preferred password)
**IP Address:** `10.42.0.1`
**DHCP Range:** `10.42.0.10 - 10.42.0.50`

**IMPORTANT:** Update the WiFi credentials in the ESP32 firmware if you use different values:

```cpp
// In esp32/brainmove_mqtt/brainmove_mqtt.ino
const char* WIFI_SSID = "BrainMove";           // Match your SSID
const char* WIFI_PASSWORD = "brainmove2025";   // Match your password
```

### Verify Hotspot

```bash
# Check WiFi interface
ip addr show wlan0

# Should show: inet 10.42.0.1/24
```

## 5. Install Python Dependencies

```bash
cd ~/BrainMoveG1  # Or your project directory

# Install dependencies
pip3 install -r requirements.txt

# Specifically verify aiomqtt is installed
pip3 show aiomqtt
```

Expected output:
```
Name: aiomqtt
Version: 2.x.x
```

## 6. Configure Backend Environment

Verify `.env` file in `backend/` directory:

```bash
cat backend/.env
```

Should contain:

```env
# MQTT Configuration
MQTT_BROKER_HOST=localhost
MQTT_BROKER_PORT=1883
MQTT_KEEPALIVE=60
MQTT_RECONNECT_INTERVAL=5

# Network
HOST_IP=10.42.0.1
```

## 7. Test Backend MQTT Connection

```bash
cd backend

# Run test script
python3 test_mqtt.py
```

Expected output:
```
=== Testing MQTT Client ===

Starting MQTT client...
✓ MQTT connected successfully!
✓ Subscribed to topics: bm/+/detect, bm/+/battery, bm/+/status

Testing command publishing...
✓ Sent command: bm/rood/cmd -> start
✓ Sent command: bm/all/cmd -> start
✓ Sent command: bm/blauw/cmd -> correct

Device status:
  - blauw: offline (battery: None)
  - rood: offline (battery: None)
  - geel: offline (battery: None)
  - groen: offline (battery: None)

Listening for messages for 10 seconds...
```

## 8. Start Backend Application

```bash
cd backend/src

# Run FastAPI server
python3 main.py
```

Expected output:
```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:mqtt_client:MQTT connecting to localhost:1883...
INFO:mqtt_client:MQTT connected successfully
INFO:mqtt_client:Subscribed to: bm/+/detect
INFO:mqtt_client:Subscribed to: bm/+/battery
INFO:mqtt_client:Subscribed to: bm/+/status
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

## 9. Monitor MQTT Traffic

While the system is running, you can monitor all MQTT messages:

```bash
# In a separate terminal
mosquitto_sub -h localhost -t "bm/#" -v
```

You'll see messages like:
```
bm/rood/status online
bm/blauw/status online
bm/rood/battery 87
bm/blauw/detect 1
bm/blauw/detect 0
```

## 10. Frontend Setup

The frontend should work without changes, but verify configuration:

```bash
cd frontend

# Check environment files exist
ls -la .env.*

# Should see:
# .env.development
# .env.production
```

Content of `.env.development`:
```env
VITE_API_BASE_URL=http://10.42.0.1:8000
```

Content of `.env.production`:
```env
VITE_API_BASE_URL=http://10.42.0.1:8000
```

Install and run frontend:

```bash
npm install
npm run dev    # Development mode
# OR
npm run build  # Production build
```

## 11. Verify Complete System

### Check All Services

```bash
# MQTT Broker
sudo systemctl status mosquitto

# WiFi Hotspot
sudo systemctl status hostapd

# Backend (if running as service)
# sudo systemctl status brainmove-backend
```

### Check Connected Devices

```bash
# See connected ESP32 devices
sudo iw dev wlan0 station dump

# You should see 4 devices (one per color)
```

### Test API Endpoint

```bash
curl http://localhost:8000/devices/status
```

Expected response:
```json
{
  "apparaten": [
    {"kleur": "blauw", "status": "online", "batterij": 85},
    {"kleur": "rood", "status": "online", "batterij": 92},
    {"kleur": "geel", "status": "online", "batterij": 78},
    {"kleur": "groen", "status": "online", "batterij": 81}
  ],
  "connected": true,
  "totaal_verwacht": 4
}
```

## 12. Systemd Service (Optional)

Create a service to auto-start backend on boot:

```bash
sudo nano /etc/systemd/system/brainmove-backend.service
```

Add:

```ini
[Unit]
Description=BrainMove Backend Service
After=network.target mosquitto.service

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/BrainMoveG1/backend/src
ExecStart=/usr/bin/python3 /home/pi/BrainMoveG1/backend/src/main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable brainmove-backend
sudo systemctl start brainmove-backend
sudo systemctl status brainmove-backend
```

## Troubleshooting

### Mosquitto Not Starting

```bash
# Check logs
sudo journalctl -u mosquitto -n 50

# Check configuration syntax
mosquitto -c /etc/mosquitto/mosquitto.conf -v
```

### ESP32 Can't Connect to MQTT

```bash
# Verify broker is listening
sudo netstat -tuln | grep 1883

# Test broker locally
mosquitto_pub -h localhost -t test -m hello

# Check firewall (if enabled)
sudo ufw status
sudo ufw allow 1883/tcp
```

### Backend Can't Connect to MQTT

```bash
# Check if broker is running
sudo systemctl status mosquitto

# Test connection
mosquitto_sub -h localhost -t "test"

# Check Python dependencies
pip3 show aiomqtt
```

### No Messages from ESP32

```bash
# Check ESP32 is connected to WiFi
sudo iw dev wlan0 station dump

# Monitor MQTT for any messages
mosquitto_sub -h localhost -t "#" -v

# Check ESP32 Serial Monitor for errors
# Should show "MQTT connected!" message
```

### High Latency

```bash
# Check WiFi signal strength on ESP32 (Serial Monitor)
# Should show RSSI: -40 to -70 dBm

# Check MQTT queue
mosquitto_sub -h localhost -t '$SYS/broker/messages/#' -v

# Monitor system resources
htop
```

## Performance Monitoring

### MQTT Statistics

```bash
# Subscribe to broker statistics
mosquitto_sub -h localhost -t '$SYS/#' -v
```

Useful topics:
- `$SYS/broker/clients/connected` - Number of connected clients
- `$SYS/broker/messages/received` - Total messages received
- `$SYS/broker/messages/sent` - Total messages sent
- `$SYS/broker/uptime` - Broker uptime

### System Resources

```bash
# CPU and memory usage
htop

# Network traffic
sudo iftop -i wlan0

# Disk usage
df -h
```

## Backup Configuration

```bash
# Backup Mosquitto config
sudo cp /etc/mosquitto/conf.d/brainmove.conf ~/brainmove_mosquitto_backup.conf

# Backup backend .env
cp backend/.env backend/.env.backup

# Backup frontend .env files
cp frontend/.env.development frontend/.env.development.backup
cp frontend/.env.production frontend/.env.production.backup
```

## Updates and Maintenance

### Update System

```bash
sudo apt update
sudo apt upgrade -y
sudo reboot
```

### Update Python Dependencies

```bash
cd ~/BrainMoveG1
pip3 install --upgrade -r requirements.txt
```

### Update Frontend Dependencies

```bash
cd frontend
npm update
```

### View Logs

```bash
# Mosquitto logs
sudo tail -f /var/log/mosquitto/mosquitto.log

# Backend logs (if running as service)
sudo journalctl -u brainmove-backend -f

# System logs
sudo journalctl -xe
```

## Security Considerations

Since this is a local hotspot system:

1. **MQTT Anonymous Access:** Enabled for simplicity (no internet exposure)
2. **WiFi Password:** Use a strong password for the hotspot
3. **Firewall:** Not strictly necessary but can be enabled
4. **Updates:** Keep system updated for security patches

For production deployment with internet access, consider:
- MQTT authentication (username/password)
- TLS/SSL encryption
- Firewall rules
- VPN access

## Next Steps

1. ✅ Verify all services are running
2. ✅ Flash ESP32 devices with MQTT firmware
3. ✅ Test one device at a time
4. ✅ Test all devices together
5. ✅ Run a complete game test
6. ✅ Monitor performance and adjust if needed

## Quick Reference Commands

```bash
# Start everything
sudo systemctl start mosquitto
cd ~/BrainMoveG1/backend/src && python3 main.py

# Stop everything
sudo systemctl stop mosquitto
# Ctrl+C to stop backend

# Monitor MQTT
mosquitto_sub -h localhost -t "bm/#" -v

# Check device status
curl http://localhost:8000/devices/status

# Test MQTT publish
mosquitto_pub -h localhost -t "bm/all/cmd" -m "start"
```
