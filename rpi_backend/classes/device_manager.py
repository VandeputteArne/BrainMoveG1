#!/usr/bin/env python3

import logging
import os
from typing import Optional, Dict, List
from bleak import BleakScanner
from dotenv import load_dotenv

from classes.esp32_device import (
    ESP32Device,
    DetectionCallback,
    BatteryCallback,
    StatusCallback,
    DEVICE_PREFIX
)

logger = logging.getLogger(__name__)

class DeviceManager:
    def __init__(self, trusted_macs: Optional[Dict[str, str]] = None, strict_whitelist: Optional[bool] = None, 
                 scan_timeout: Optional[float] = None, connection_timeout: Optional[float] = None):
        # Load .env file
        load_dotenv()
        
        # Load trusted devices from environment
        env_trusted_devices = {}
        for color in ("BLUE", "RED", "YELLOW", "GREEN"):
            mac = os.getenv(f"DEVICE_BM_{color}")
            if mac:
                env_trusted_devices[mac] = f"BM-{color.capitalize()}"
        
        # Load config from environment with defaults
        self.magic_byte = int(os.getenv("MAGIC_BYTE", "0x42"), 0)
        self.scan_timeout = scan_timeout if scan_timeout is not None else float(os.getenv("SCAN_TIMEOUT", "5.0"))
        self.connection_timeout = connection_timeout if connection_timeout is not None else float(os.getenv("CONNECTION_TIMEOUT", "10.0"))
        env_strict_whitelist = os.getenv("STRICT_WHITELIST", "").lower() == "true"
        
        # Key: device name, Value: ESP32Device instance
        self._devices: Dict[str, ESP32Device] = {}
        self._trusted_macs = trusted_macs if trusted_macs is not None else env_trusted_devices
        self._strict_whitelist = strict_whitelist if strict_whitelist is not None else env_strict_whitelist
        
        # Callback templates to apply to new devices
        self._detection_callback: Optional[DetectionCallback] = None
        self._battery_callback: Optional[BatteryCallback] = None
        self._status_callback: Optional[StatusCallback] = None
    

    # Properties----------------------------------------------------------------------
    @property
    def devices(self) -> Dict[str, ESP32Device]:
        return self._devices.copy()
    
    @property
    def trusted_macs(self) -> Dict[str, str]:
        return self._trusted_macs.copy()
    
    @property
    def strict_whitelist(self) -> bool:
        return self._strict_whitelist
    
    def get_device(self, name: str) -> Optional[ESP32Device]:
        return self._devices.get(name)
    
    def _add_device(self, device: ESP32Device) -> None:
        # Apply callbacks if set
        if self._detection_callback:
            device.on_detection = self._detection_callback
        if self._battery_callback:
            device.on_battery = self._battery_callback
        if self._status_callback:
            device.on_status = self._status_callback
        
        self._devices[device.name] = device
        logger.info(f"Added device: {device.name}")
    
    async def scan(self, timeout: Optional[float] = None, max_attempts: int = 10) -> List[ESP32Device]:
        scan_timeout = timeout if timeout is not None else self.scan_timeout
        logger.info(f"Scanning for BrainMove devices (timeout={scan_timeout}s per scan)...")
        
        if self._strict_whitelist:
            logger.info("MAC whitelist ENABLED - will scan until all 4 trusted devices are found")
        
        total_devices_needed = len(self._trusted_macs)
        new_devices = []
        attempts = 0
        
        while attempts < max_attempts:
            attempts += 1
            
            # Count how many trusted devices we've already found
            trusted_found = sum(1 for device in self._devices.values() 
                              if device.address.upper() in [m.upper() for m in self._trusted_macs.keys()])
            
            if self._strict_whitelist and trusted_found >= total_devices_needed:
                logger.info(f"All {total_devices_needed} trusted devices found!")
                break
            
            logger.info(f"Scan attempt {attempts}/{max_attempts} - Found {trusted_found}/{total_devices_needed} trusted devices")
            
            discovered = await BleakScanner.discover(timeout=scan_timeout)
            
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
                
                # Create device and add it (callbacks auto-applied)
                device = ESP32Device(mac, name)
                self._add_device(device)
                new_devices.append(device)
                logger.info(f"Discovered: {name} ({mac})")
        
        trusted_found = sum(1 for device in self._devices.values() 
                          if device.address.upper() in [m.upper() for m in self._trusted_macs.keys()])
        
        if self._strict_whitelist and trusted_found < total_devices_needed:
            logger.warning(f"Scan stopped after {attempts} attempts: Only found {trusted_found}/{total_devices_needed} trusted devices")
        else:
            logger.info(f"Scan complete after {attempts} attempt(s): {len(new_devices)} new device(s) found")
        
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
        self._detection_callback = callback
        for device in self._devices.values():
            device.on_detection = callback
    
    def set_battery_callback(self, callback: BatteryCallback) -> None:
        self._battery_callback = callback
        for device in self._devices.values():
            device.on_battery = callback
    
    def set_status_callback(self, callback: StatusCallback) -> None:
        self._status_callback = callback
        for device in self._devices.values():
            device.on_status = callback
    
    def get_device_health(self, timeout_seconds: float = 60.0) -> Dict[str, bool]:
        return {name: device.is_alive(timeout_seconds) for name, device in self._devices.items()}
    
    def get_alive_devices(self, timeout_seconds: float = 60.0) -> List[str]:
        return [name for name, device in self._devices.items() if device.is_alive(timeout_seconds)]
    
    def get_dead_devices(self, timeout_seconds: float = 60.0) -> List[str]:
        return [name for name, device in self._devices.items() if not device.is_alive(timeout_seconds)]
    
    def log_health_status(self, timeout_seconds: float = 60.0) -> None:
        health = self.get_device_health(timeout_seconds)
        alive = [name for name, status in health.items() if status]
        dead = [name for name, status in health.items() if not status]
        
        logger.info(f"Device health: {len(alive)} alive, {len(dead)} dead")
        if alive:
            logger.info(f"  Alive: {', '.join(alive)}")
        if dead:
            logger.warning(f"  Dead/Unresponsive: {', '.join(dead)}")
