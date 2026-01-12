#!/usr/bin/env python3

import asyncio
import struct
import logging
from datetime import datetime
from dataclasses import dataclass
from typing import Callable, Optional
from enum import IntEnum
from bleak import BleakClient
from bleak.exc import BleakError

logger = logging.getLogger(__name__)


# Constants and Enums----------------------------------------------------------------
SERVICE_UUID = "beb5483e-36e1-4688-b7f5-ea07361b26a7"
CHAR_DATA_UUID = "beb5483e-36e1-4688-b7f5-ea07361b26a8"
CHAR_COMMAND_UUID = "beb5483e-36e1-4688-b7f5-ea07361b26a9"

MAGIC_BYTE = 0x42
DEVICE_PREFIX = "BM-"

class MessageType(IntEnum):
    STATUS = 0x01
    DETECTION = 0x02
    BATTERY = 0x03
    KEEPALIVE = 0x04

class Command(IntEnum):
    START = 0x01
    STOP = 0x02
    SLEEP = 0x03
    PING = 0x04
    SOUND_CORRECT = 0x10
    SOUND_INCORRECT = 0x11

class StatusEvent(IntEnum):
    CONNECTED = 0x01
    RECONNECTED = 0x02
    SLEEPING = 0x03
    PONG = 0x04

DEVICE_NAMES = {
    0: "BM-Blue",
    1: "BM-Red",
    2: "BM-Yellow",
    3: "BM-Green"
}


# Data Classes for Events--------------------------------------------------------------
@dataclass
class DetectionEvent:
    device_name: str
    device_id: int
    detection_bool: int
    timestamp_ms: int
    received_at: datetime

@dataclass
class BatteryEvent:
    device_name: str
    device_id: int
    percent: int
    timestamp_ms: int
    received_at: datetime

@dataclass
class StatusEvent_:
    device_name: str
    device_id: int
    event: str
    timestamp_ms: int
    received_at: datetime


# Type aliases for callbacks------------------------------------------------------------------
DetectionCallback = Callable[[DetectionEvent], None]
BatteryCallback = Callable[[BatteryEvent], None]
StatusCallback = Callable[[StatusEvent_], None]
DisconnectCallback = Callable[[], None]


# ESP32 Device Class-----------------------------------------------------------------------
class ESP32Device:
    def __init__(self, address: str, name: str, auto_reconnect: bool = True):
        self.address = address
        self.name = name
        self.auto_reconnect = auto_reconnect
        
        # Connection state
        self._client: Optional[BleakClient] = None
        self._connected = False
        self._authenticated = False
        self._polling = False
        
        # Reconnection settings
        self._reconnect_attempts = 0
        self._max_reconnect_attempts = 3
        self._reconnect_delay = 2.0  # seconds
        
        # Callbacks incoming data
        self.on_detection: Optional[DetectionCallback] = None
        self.on_battery: Optional[BatteryCallback] = None
        self.on_status: Optional[StatusCallback] = None
        self.on_disconnect: Optional[DisconnectCallback] = None
        
        # Internal state
        self._reconnect_task: Optional[asyncio.Task] = None
        self._last_keepalive: Optional[datetime] = None
        # Last received detection event (updated immediately on notification)
        self.last_detection: Optional[DetectionEvent] = None
    

    # Properties----------------------------------------------------------------------
    @property
    def connected(self) -> bool:
        return self._connected
    
    @property
    def authenticated(self) -> bool:
        return self._authenticated
    
    @property
    def is_polling(self) -> bool:
        return self._polling
    

    # Connection Methods------------------------------------------------------------------    
    async def connect(self, timeout: float = 30.0) -> bool:
        try:
            self._client = BleakClient(
                self.address,
                timeout=timeout,
                disconnected_callback=self._handle_disconnect
            )
            
            logger.info(f"Connecting to {self.name} ({self.address})...")
            await self._client.connect()
            
            if self._client.is_connected:
                self._connected = True
                logger.info(f"Connected to {self.name}")
                
                # Subscribe
                await self._client.start_notify(CHAR_DATA_UUID, self._notification_handler)
                logger.debug(f"Getting notifications from {self.name}")
                
                self._reconnect_attempts = 0
                return True
            
            return False
            
        except BleakError as e:
            error_msg = str(e).lower()
            if any(x in error_msg for x in ["not paired", "authentication", "encrypt"]):
                logger.error(f"Pairing required for {self.name}. Use bluetoothctl to pair.")
            else:
                logger.error(f"BLE error connecting to {self.name}: {e}")
            self._connected = False
            return False
            
        except Exception as e:
            logger.error(f"Failed to connect to {self.name}: {e}")
            self._connected = False
            return False
    
    async def disconnect(self) -> None:
        self.auto_reconnect = False  # Prevent auto-reconnect
        
        if self._reconnect_task:
            self._reconnect_task.cancel()
            self._reconnect_task = None
        
        if self._client and self._connected:
            try:
                await self._client.stop_notify(CHAR_DATA_UUID)
                await self._client.disconnect()
            except Exception as e:
                logger.debug(f"Error during disconnect: {e}")
            
            self._connected = False
            self._authenticated = False
            self._polling = False
            logger.info(f"Disconnected from {self.name}")
    
    def _handle_disconnect(self, client: BleakClient) -> None:
        self._connected = False
        self._authenticated = False
        self._polling = False
        logger.warning(f"{self.name} disconnected unexpectedly")
        
        if self.on_disconnect:
            self.on_disconnect()
        
        if self.auto_reconnect and self._reconnect_attempts < self._max_reconnect_attempts:
            self._reconnect_task = asyncio.create_task(self._reconnect())
    
    async def _reconnect(self) -> None:
        self._reconnect_attempts += 1
        logger.info(f"Attempting reconnect to {self.name} ({self._reconnect_attempts}/{self._max_reconnect_attempts})...")
        
        await asyncio.sleep(self._reconnect_delay)
        
        if await self.connect():
            logger.info(f"Reconnected to {self.name}")
            # Resume polling if it was active
            if self._polling:
                await self.start_polling()
        elif self._reconnect_attempts < self._max_reconnect_attempts:
            self._reconnect_task = asyncio.create_task(self._reconnect())
        else:
            logger.error(f"Failed to reconnect to {self.name} after {self._max_reconnect_attempts} attempts")


    # Command Methods ---------------------------------------------------------------------    
    async def _send_command(self, command: Command) -> bool:
        if not self._connected:
            logger.error(f"Cannot send command - not connected to {self.name}")
            return False
        
        if not self._authenticated:
            logger.warning(f"Device {self.name} not yet authenticated")
        
        try:
            await self._client.write_gatt_char(CHAR_COMMAND_UUID, bytes([command]))
            logger.debug(f"Sent {command.name} to {self.name}")
            return True
        except Exception as e:
            logger.error(f"Failed to send command to {self.name}: {e}")
            return False
    
    async def start_polling(self) -> bool:
        if await self._send_command(Command.START):
            self._polling = True
            logger.info(f"{self.name}: Started polling")
            return True
        return False
    
    async def stop_polling(self) -> bool:
        if await self._send_command(Command.STOP):
            self._polling = False
            logger.info(f"{self.name}: Stopped polling")
            return True
        return False
    
    async def sleep(self) -> bool:
        result = await self._send_command(Command.SLEEP)
        if result:
            self._polling = False
            logger.info(f"{self.name}: Entering sleep mode")
        return result
    
    async def ping(self) -> bool:
        return await self._send_command(Command.PING)
    
    async def play_correct_sound(self) -> bool:
        return await self._send_command(Command.SOUND_CORRECT)
    
    async def play_incorrect_sound(self) -> bool:
        return await self._send_command(Command.SOUND_INCORRECT)
    

    # Notification Handling------------------------------------------------------
    def _notification_handler(self, sender, data: bytearray) -> None:
        if len(data) < 8:
            logger.warning(f"Message too short from {self.name}: {len(data)} bytes")
            return
        
        # Parse incoming data header
        msg_type, device_id, magic, reserved, timestamp = struct.unpack('<BBBBI', data[:8])
        
        # Verify magic byte
        if magic == MAGIC_BYTE:
            if not self._authenticated:
                self._authenticated = True
                logger.info(f"{self.name} authenticated successfully")
        else:
            logger.warning(f"Invalid magic byte from {self.name}: 0x{magic:02X}")
            self._authenticated = False
            return
        
        now = datetime.now()
        
        # Send by message type
        if msg_type == MessageType.STATUS:
            self._handle_status_message(data, device_id, timestamp, now)
        elif msg_type == MessageType.DETECTION:
            self._handle_detection_message(data, device_id, timestamp, now)
        elif msg_type == MessageType.BATTERY:
            self._handle_battery_message(data, device_id, timestamp, now)
        elif msg_type == MessageType.KEEPALIVE:
            self._last_keepalive = now
            logger.debug(f"{self.name} keepalive")
        else:
            logger.warning(f"Unknown message type 0x{msg_type:02X} from {self.name}")
    
    def _handle_status_message(self, data: bytes, device_id: int, timestamp: int, now: datetime) -> None:
        if len(data) < 9:
            return
        
        status_code = data[8]
        status_names = {
            StatusEvent.CONNECTED: "CONNECTED",
            StatusEvent.RECONNECTED: "RECONNECTED",
            StatusEvent.SLEEPING: "SLEEPING",
            StatusEvent.PONG: "PONG"
        }
        status_name = status_names.get(status_code, f"UNKNOWN({status_code})")
        
        
        if self.on_status:
            event = StatusEvent_(
                device_name=self.name,
                device_id=device_id,
                event=status_name,
                timestamp_ms=timestamp,
                received_at=now
            )
            self.on_status(event)
    
    def _handle_detection_message(self, data: bytes, device_id: int, timestamp: int, now: datetime) -> None:
        if len(data) < 10:
            return
        
        detection_true = struct.unpack('<H', data[8:10])[0]
        logger.debug(f"{self.name} DETECTION: {detection_true}")
        
        event = DetectionEvent(
            device_name=self.name,
            device_id=device_id,
            detection_bool=detection_true,
            timestamp_ms=timestamp,
            received_at=now
        )
        self.last_detection = event
        if self.on_detection:
            try:
                self.on_detection(event)
            except Exception as e:
                logger.exception(f"Error in detection callback for {self.name}: {e}")
    
    def _handle_battery_message(self, data: bytes, device_id: int, timestamp: int, now: datetime) -> None:
        if len(data) < 9:
            return
        
        percent = data[8]
        
        if self.on_battery:
            event = BatteryEvent(
                device_name=self.name,
                device_id=device_id,
                percent=percent,
                timestamp_ms=timestamp,
                received_at=now
            )
            self.on_battery(event)
    
    
    # Health Monitoring----------------------------------------------------------------
    def is_alive(self, timeout_seconds: float = 60.0) -> bool:
        if not self._connected:
            return False
        if self._last_keepalive is None:
            # No keepalive yet, but connected recently
            return True
        time_since = (datetime.now() - self._last_keepalive).total_seconds()
        return time_since < timeout_seconds
    
    def time_since_keepalive(self) -> Optional[float]:
        if self._last_keepalive is None:
            return None
        return (datetime.now() - self._last_keepalive).total_seconds()

    # Representation-------------------------------------------------------------------
    def __str__(self) -> str:
        status = "connected" if self._connected else "disconnected"
        return f"{self.name} ({self.address}) - {status}"
        
    def __repr__(self) -> str:
        status = "connected" if self._connected else "disconnected"
        return f"ESP32Device({self.name!r}, {self.address!r}, {status})"