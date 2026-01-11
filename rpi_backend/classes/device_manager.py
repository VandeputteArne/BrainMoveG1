#!/usr/bin/env python3

import logging
from typing import Optional, Dict, List
from bleak import BleakScanner

from esp32_device import (
    ESP32Device,
    DetectionCallback,
    BatteryCallback,
    StatusCallback,
    DEVICE_PREFIX
)

logger = logging.getLogger(__name__)


class DeviceManager:  
    def __init__(self, trusted_macs: Optional[Dict[str, str]] = None, strict_whitelist: bool = False):
        self._devices: Dict[str, ESP32Device] = {}
        self._trusted_macs = trusted_macs or {}
        self._strict_whitelist = strict_whitelist
    
    @property
    def devices(self) -> Dict[str, ESP32Device]:
        return self._devices.copy()
    
    def get_device(self, name: str) -> Optional[ESP32Device]:
        return self._devices.get(name)
    
    def add_device(self, device: ESP32Device) -> None:
        self._devices[device.name] = device
        logger.info(f"Added device: {device.name}")
    
    async def scan(self, timeout: float = 5.0) -> List[ESP32Device]:
        logger.info(f"Scanning for BrainMove devices (timeout={timeout}s)...")
        
        if self._strict_whitelist:
            logger.info("MAC whitelist ENABLED")
        
        discovered = await BleakScanner.discover(timeout=timeout)
        new_devices = []
        
        for ble_device in discovered:
            if not ble_device.name or not ble_device.name.startswith(DEVICE_PREFIX):
                continue
            
            mac = ble_device.address
            name = ble_device.name
            
            # Check whitelist
            if self._strict_whitelist:
                if mac.upper() not in [m.upper() for m in self._trusted_macs.keys()]:
                    logger.warning(f"REJECTED: {name} ({mac}) - not in whitelist")
                    continue
                
                expected_name = self._trusted_macs.get(mac.upper())
                if expected_name and expected_name != name:
                    logger.warning(f"SECURITY: {mac} advertising as '{name}' but expected '{expected_name}'")
                    continue
            
            # Check if already managed
            if name in self._devices:
                logger.debug(f"Already managing: {name}")
                continue
            
            # Create and add device
            device = ESP32Device(mac, name)
            self._devices[name] = device
            new_devices.append(device)
            logger.info(f"Discovered: {name} ({mac})")
        
        logger.info(f"Scan complete: {len(new_devices)} new device(s) found")
        return new_devices
    
    async def connect_all(self) -> Dict[str, bool]:
        results = {}
        for name, device in self._devices.items():
            results[name] = await device.connect()
        return results
    
    async def disconnect_all(self) -> None:
        for device in self._devices.values():
            await device.disconnect()
    
    async def start_all(self) -> Dict[str, bool]:
        results = {}
        for name, device in self._devices.items():
            if device.connected:
                results[name] = await device.start_polling()
        return results
    
    async def stop_all(self) -> Dict[str, bool]:
        results = {}
        for name, device in self._devices.items():
            if device.connected:
                results[name] = await device.stop_polling()
        return results
    
    def set_detection_callback(self, callback: DetectionCallback) -> None:
        for device in self._devices.values():
            device.on_detection = callback
    
    def set_battery_callback(self, callback: BatteryCallback) -> None:
        for device in self._devices.values():
            device.on_battery = callback
    
    def set_status_callback(self, callback: StatusCallback) -> None:
        for device in self._devices.values():
            device.on_status = callback
