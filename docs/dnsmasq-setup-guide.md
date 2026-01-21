# Setting Up brainmove.g1 Domain on Raspberry Pi Hotspot

This guide configures the custom domain `brainmove.g1` for the BrainMove webapp using NetworkManager's built-in dnsmasq.

## Architecture Overview

```
Client Device (Phone/Laptop)
    │
    ├── http://brainmove.g1:3000  ──►  Frontend (serve)
    │
    └── http://brainmove.g1:8000  ──►  Backend (uvicorn + Socket.IO)

ESP32 Devices
    │
    └── 10.42.0.1:1883  ──►  MQTT Broker (mosquitto)
```

**Note:** This setup does NOT use nginx. The frontend and backend are accessed directly on their respective ports, which provides the lowest latency for real-time Socket.IO communication.

## Prerequisites

- Raspberry Pi 5 with hotspot already configured
- BrainMove services running
- SSH access to the Pi

---

## Step 1: Create dnsmasq Configuration

NetworkManager uses an internal dnsmasq instance when `ipv4.method shared` is set. We can extend it with custom configurations.

```bash
# Create the dnsmasq config directory if it doesn't exist
sudo mkdir -p /etc/NetworkManager/dnsmasq.d

# Create the BrainMove DNS configuration
sudo nano /etc/NetworkManager/dnsmasq.d/brainmove.conf
```

Add the following content:

```conf
# BrainMove custom domain configuration
# Maps brainmove.g1 to the hotspot IP

address=/brainmove.g1/10.42.0.1

# Optional: Also allow just "brainmove" without the .g1
address=/brainmove/10.42.0.1
```

Save and exit (`Ctrl+X`, then `Y`, then `Enter`).

---

## Step 2: Restart NetworkManager

Apply the changes by restarting NetworkManager:

```bash
sudo systemctl restart NetworkManager
```

Wait a few seconds for the hotspot to come back up:

```bash
# Verify the hotspot is active
nmcli connection show --active | grep BrainMoveG1
```

---

## Step 3: Test DNS Resolution

From the Raspberry Pi itself:

```bash
# Test the DNS resolution
nslookup brainmove.g1 127.0.0.1
```

Expected output:
```
Server:    127.0.0.1
Address:   127.0.0.1#53

Name:      brainmove.g1
Address:   10.42.0.1
```

---

## Step 4: Update Frontend Configuration

Update the frontend to use the new domain.

### 4.1 Update .env.production

```bash
# On your development machine or Pi
nano /home/bmajm/BrainMove/BrainMoveG1/frontend/.env.production
```

Change:
```env
VITE_API_BASE_URL=http://brainmove.g1:8000
```

### 4.2 Update .env.development (optional)

```bash
nano /home/bmajm/BrainMove/BrainMoveG1/frontend/.env.development
```

Change:
```env
VITE_API_BASE_URL=http://brainmove.g1:8000
```

### 4.3 Update api.js (fallback config)

```bash
nano /home/bmajm/BrainMove/BrainMoveG1/frontend/src/config/api.js
```

Update the base URL:
```javascript
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://brainmove.g1:8000';
```

---

## Step 5: Rebuild the Frontend

After updating the configuration, rebuild the frontend:

```bash
cd /home/bmajm/BrainMove/BrainMoveG1/frontend

# Install dependencies if needed
npm install

# Build for production
npm run build
```

---

## Step 6: Restart BrainMove Services

```bash
# Using the provided scripts
cd /home/bmajm/BrainMove/BrainMoveG1/scripts
./restart_all.sh

# Or manually
sudo systemctl restart brainmove-backend.service
sudo systemctl restart brainmove-frontend.service
```

---

## Step 7: Test from a Client Device

1. Connect your phone/laptop to the `BrainMoveG1` WiFi network
2. Open a browser and navigate to: `http://brainmove.g1:3000`
3. The webapp should load

### Troubleshooting DNS on Client

If the domain doesn't resolve on your client device:

**On Android/iOS:**
- Forget and reconnect to the WiFi network
- This forces the device to get fresh DNS settings

**On Windows:**
```cmd
ipconfig /flushdns
```

**On macOS/Linux:**
```bash
sudo dscacheutil -flushcache  # macOS
sudo systemd-resolve --flush-caches  # Linux
```

---

## What Stays the Same

The following components continue using the IP address and **do not need changes**:

| Component | Reason |
|-----------|--------|
| ESP32 MQTT connection | Hardcoded IP, no DNS lookup needed |
| Backend MQTT client | Uses `localhost` to connect to broker |
| Mosquitto broker | Listens on all interfaces |

---

## Fallback Access

The IP address `10.42.0.1` will **still work** as a fallback:

- `http://10.42.0.1` → Frontend
- `http://10.42.0.1:8000` → Backend API

This provides redundancy if DNS resolution fails on any device.

---

## Quick Reference

| URL | Service |
|-----|---------|
| `http://brainmove.g1:3000` | Frontend (webapp) |
| `http://brainmove.g1:8000` | Backend API |
| `http://brainmove.g1:8000/docs` | API Documentation |
| `10.42.0.1:1883` | MQTT Broker (ESP32s) |

---

## Verification Checklist

- [ ] dnsmasq config created at `/etc/NetworkManager/dnsmasq.d/brainmove.conf`
- [ ] NetworkManager restarted
- [ ] DNS resolution works from Pi (`nslookup brainmove.g1 127.0.0.1`)
- [ ] Frontend `.env.production` updated
- [ ] Frontend rebuilt (`npm run build`)
- [ ] BrainMove services restarted
- [ ] Webapp accessible at `http://brainmove.g1:3000` from client device

---

## Rollback

If you need to revert to IP-only access:

```bash
# Remove the dnsmasq config
sudo rm /etc/NetworkManager/dnsmasq.d/brainmove.conf

# Restart NetworkManager
sudo systemctl restart NetworkManager

# Revert frontend .env files to use 10.42.0.1
# Rebuild frontend
```
