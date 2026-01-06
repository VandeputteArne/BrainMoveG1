# BrainMoveG1 - ESP32 ToF Sensor Network Firmware

**Version:** 1.0.0  
**Date:** 2026-01-06

## Overview

This firmware implements a low-power ESP32 node that communicates with a Raspberry Pi 5 hotspot. Features include deep sleep with button wake-up, ToF sensor polling, buzzer feedback, and robust connection management.

## Hardware Components

- **ESP32** microcontroller
- **VL53L1X** ToF distance sensor (I2C)
- **Wake-up button** (pullup configuration)
- **Buzzer** for audio feedback

## Network Configuration

- **SSID:** BrainMoveG1
- **Server:** Raspberry Pi 5 running TCP server

## Communication Protocol

All data transmitted as JSON over TCP.

### Server to ESP32

```json
{"command": "START"}
{"command": "STOP"}
```

### ESP32 to Server

**Detection Event:**
```json
{"device": "esp-blue", "event": "detection", "distance": 25, "timestamp": 123456}
```

**Keepalive:**
```json
{"device": "esp-blue", "event": "keepalive"}
```

**Connected:**
```json
{"device": "esp-blue", "event": "connected"}
```

## Pin Configuration

| GPIO | Function | Notes |
|------|----------|-------|
| 4 | WAKE_UP_BUTTON | External pullup, active LOW, ext0 wakeup |
| 21 | I2C SDA | ToF sensor data line |
| 22 | I2C SCL | ToF sensor clock line |
| 25 | BUZZER | Active HIGH, PWM capable |
| 2 | STATUS_LED | Built-in LED for status indication |

## Features

- **Deep Sleep Management:** Ultra-low power consumption with external button wake-up
- **Distributed Sensing:** Multi-node ToF sensor network
- **Audio Feedback:** Buzzer for user feedback and alerts
- **Robust Connection:** Automatic reconnection and keepalive messaging
- **Flexible Control:** Remote START/STOP commands from server