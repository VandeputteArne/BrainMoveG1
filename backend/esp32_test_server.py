#!/usr/bin/env python3
"""
ESP32 BLE Server - Receives messages from ESP32 devices via Bluetooth Low Energy
"""

import asyncio
import struct
from datetime import datetime
from bleak import BleakClient, BleakScanner

# BLE UUIDs - must match ESP32 firmware
SERVICE_UUID = "4fafc201-1fb5-459e-8fcc-c5c9c331914b"
CHAR_DATA_UUID = "beb5483e-36e1-4688-b7f5-ea07361b26a8"
CHAR_COMMAND_UUID = "beb5483e-36e1-4688-b7f5-ea07361b26a9"

# Device name prefix to scan for
DEVICE_PREFIX = "BM-"

# Message types (matching ESP32 firmware)
MSG_STATUS = 0x01
MSG_DETECTION = 0x02
MSG_BATTERY = 0x03
MSG_KEEPALIVE = 0x04
MSG_TEST = 0x05

# Command types (to send to ESP32)
CMD_START = 0x01
CMD_STOP = 0x02
CMD_SLEEP = 0x03
CMD_PING = 0x04

# Status events
STATUS_CONNECTED = 0x01
STATUS_RECONNECTED = 0x02
STATUS_SLEEPING = 0x03
STATUS_PONG = 0x04

# Device names by ID
DEVICE_NAMES = {
    0: "BM-Blue",
    1: "BM-Red",
    2: "BM-Yellow",
    3: "BM-Green"
}


class MessageParser:
    """Parse binary messages from ESP32 devices"""
    
    @staticmethod
    def parse_header(data):
        """Parse the common message header (8 bytes)"""
        if len(data) < 8:
            return None
        
        message_type, device_id, reserved, timestamp = struct.unpack('<BBHI', data[:8])
        return {
            'message_type': message_type,
            'device_id': device_id,
            'device_name': DEVICE_NAMES.get(device_id, f"unknown-{device_id}"),
            'reserved': reserved,
            'timestamp': timestamp
        }
    
    @staticmethod
    def parse_status_message(data):
        """Parse status message (12 bytes total)"""
        if len(data) < 12:
            return None
        
        header = MessageParser.parse_header(data)
        if not header:
            return None
        
        status_event = struct.unpack('<B', data[8:9])[0]
        
        status_names = {
            STATUS_CONNECTED: "CONNECTED",
            STATUS_RECONNECTED: "RECONNECTED",
            STATUS_SLEEPING: "SLEEPING",
            STATUS_PONG: "PONG"
        }
        
        header['status_event'] = status_names.get(status_event, f"UNKNOWN({status_event})")
        return header
    
    @staticmethod
    def parse_detection_message(data):
        """Parse detection message (12 bytes total)"""
        if len(data) < 12:
            return None
        
        header = MessageParser.parse_header(data)
        if not header:
            return None
        
        distance = struct.unpack('<H', data[8:10])[0]
        header['distance_mm'] = distance
        return header
    
    @staticmethod
    def parse_battery_message(data):
        """Parse battery message (12 bytes total)"""
        if len(data) < 12:
            return None
        
        header = MessageParser.parse_header(data)
        if not header:
            return None
        
        battery_percent = struct.unpack('<B', data[8:9])[0]
        header['battery_percent'] = battery_percent
        return header
    
    @staticmethod
    def parse_keepalive_message(data):
        """Parse keepalive message (8 bytes total)"""
        return MessageParser.parse_header(data)
    
    @staticmethod
    def parse_test_message(data):
        """Parse test message (12 bytes total)"""
        if len(data) < 12:
            return None
        
        header = MessageParser.parse_header(data)
        if not header:
            return None
        
        test_id = struct.unpack('<B', data[8:9])[0]
        header['test_id'] = test_id
        return header


def format_timestamp():
    """Get formatted timestamp for logging"""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]


def handle_message(device_name: str, data: bytes):
    """Parse and handle incoming message"""
    if len(data) < 8:
        print(f"[{format_timestamp()}] ERROR: Message too short ({len(data)} bytes)")
        return
    
    header = MessageParser.parse_header(data)
    if not header:
        print(f"[{format_timestamp()}] ERROR: Failed to parse message header")
        return
    
    msg_type = header['message_type']
    device_id = header['device_id']
    timestamp_ms = header['timestamp']
    
    if msg_type == MSG_STATUS:
        msg = MessageParser.parse_status_message(data)
        if msg:
            print(f"[{format_timestamp()}] 📊 STATUS from {device_name} (ID:{device_id}): {msg['status_event']}")
    
    elif msg_type == MSG_DETECTION:
        msg = MessageParser.parse_detection_message(data)
        if msg:
            print(f"[{format_timestamp()}] 🎯 DETECTION from {device_name} (ID:{device_id}): {msg['distance_mm']} mm")
    
    elif msg_type == MSG_BATTERY:
        msg = MessageParser.parse_battery_message(data)
        if msg:
            print(f"[{format_timestamp()}] 🔋 BATTERY from {device_name} (ID:{device_id}): {msg['battery_percent']}%")
    
    elif msg_type == MSG_KEEPALIVE:
        pass  # Don't print keepalives
    
    elif msg_type == MSG_TEST:
        msg = MessageParser.parse_test_message(data)
        if msg:
            print(f"\n{'='*70}")
            print(f"[{format_timestamp()}] 🧪 TEST BUTTON PRESSED!")
            print(f"  Device: {device_name} (ID: {device_id})")
            print(f"  Test ID: {msg['test_id']}")
            print(f"  Device timestamp: {timestamp_ms} ms")
            print(f"{'='*70}\n")
    
    else:
        print(f"[{format_timestamp()}] ⚠️  Unknown message type: 0x{msg_type:02X} from {device_name}")


class ESP32Device:
    """Manages BLE connection to a single ESP32 device"""
    
    def __init__(self, address: str, name: str):
        self.address = address
        self.name = name
        self.client: BleakClient = None
        self.connected = False
    
    def notification_handler(self, sender, data: bytearray):
        """Handle incoming BLE notifications"""
        handle_message(self.name, bytes(data))
    
    async def connect(self):
        """Connect to the ESP32 device"""
        try:
            self.client = BleakClient(self.address)
            await self.client.connect()
            self.connected = True
            
            print(f"[{format_timestamp()}] ✅ Connected to {self.name} ({self.address})")
            
            await self.client.start_notify(CHAR_DATA_UUID, self.notification_handler)
            print(f"[{format_timestamp()}] 📡 Subscribed to notifications from {self.name}")
            
            return True
        except Exception as e:
            print(f"[{format_timestamp()}] ❌ Failed to connect to {self.name}: {e}")
            self.connected = False
            return False
    
    async def disconnect(self):
        """Disconnect from the ESP32 device"""
        if self.client and self.connected:
            try:
                await self.client.stop_notify(CHAR_DATA_UUID)
                await self.client.disconnect()
            except:
                pass
            self.connected = False
            print(f"[{format_timestamp()}] 👋 Disconnected from {self.name}")
    
    async def send_command(self, command: int):
        """Send a command to the ESP32"""
        if not self.connected:
            print(f"[{format_timestamp()}] ❌ Cannot send command - not connected to {self.name}")
            return False
        
        try:
            cmd_data = bytes([command])
            await self.client.write_gatt_char(CHAR_COMMAND_UUID, cmd_data)
            
            cmd_names = {CMD_START: "START", CMD_STOP: "STOP", CMD_SLEEP: "SLEEP", CMD_PING: "PING"}
            print(f"[{format_timestamp()}] 📤 Sent {cmd_names.get(command, 'UNKNOWN')} to {self.name}")
            return True
        except Exception as e:
            print(f"[{format_timestamp()}] ❌ Failed to send command to {self.name}: {e}")
            return False


async def scan_for_devices():
    """Scan for BrainMove ESP32 devices"""
    print(f"[{format_timestamp()}] 🔍 Scanning for BrainMove devices (prefix: {DEVICE_PREFIX})...")
    
    devices = await BleakScanner.discover(timeout=5.0)
    
    brainmove_devices = []
    for device in devices:
        if device.name and device.name.startswith(DEVICE_PREFIX):
            brainmove_devices.append((device.address, device.name))
            print(f"[{format_timestamp()}] 📱 Found: {device.name} ({device.address})")
    
    return brainmove_devices


async def handle_user_input(connected_devices: dict):
    """Handle user commands from stdin"""
    print("\nCommands: 'start <device>', 'stop <device>', 'sleep <device>', 'ping <device>', 'scan', 'list', 'quit'")
    print("Example: 'start BM-Blue' or 'start all'\n")
    
    while True:
        try:
            loop = asyncio.get_event_loop()
            user_input = await loop.run_in_executor(None, input)
            
            if not user_input.strip():
                continue
            
            parts = user_input.strip().lower().split()
            cmd = parts[0]
            
            if cmd == 'quit' or cmd == 'exit':
                return False
            
            elif cmd == 'list':
                print(f"\n[{format_timestamp()}] Connected devices:")
                for name, device in connected_devices.items():
                    status = "✅ Connected" if device.connected else "❌ Disconnected"
                    print(f"  {name}: {status}")
                print()
            
            elif cmd == 'scan':
                new_devices = await scan_for_devices()
                for addr, name in new_devices:
                    if name not in connected_devices:
                        device = ESP32Device(addr, name)
                        if await device.connect():
                            connected_devices[name] = device
            
            elif cmd in ['start', 'stop', 'sleep', 'ping']:
                if len(parts) < 2:
                    print(f"Usage: {cmd} <device_name|all>")
                    continue
                
                target = parts[1]
                command_map = {'start': CMD_START, 'stop': CMD_STOP, 'sleep': CMD_SLEEP, 'ping': CMD_PING}
                
                if target == 'all':
                    for device in connected_devices.values():
                        await device.send_command(command_map[cmd])
                else:
                    found = None
                    for name, device in connected_devices.items():
                        if target in name.lower():
                            found = device
                            break
                    
                    if found:
                        await found.send_command(command_map[cmd])
                    else:
                        print(f"[{format_timestamp()}] ❌ Device '{target}' not found")
            
            else:
                print(f"Unknown command: {cmd}")
                
        except EOFError:
            return False
        except Exception as e:
            print(f"Error: {e}")
    
    return True


async def main():
    """Main BLE client loop"""
    print("=" * 70)
    print("ESP32 BLE Server - BrainMoveG1")
    print("=" * 70)
    print("Scanning for ESP32 devices via Bluetooth Low Energy...")
    print("Press Ctrl+C to stop\n")
    
    connected_devices = {}
    
    try:
        devices = await scan_for_devices()
        
        if not devices:
            print(f"[{format_timestamp()}] ⚠️  No BrainMove devices found. Make sure ESP32s are advertising.")
            print(f"[{format_timestamp()}] 💡 Tip: Use 'scan' command to search again.\n")
        
        for address, name in devices:
            device = ESP32Device(address, name)
            if await device.connect():
                connected_devices[name] = device
        
        if connected_devices:
            print(f"\n[{format_timestamp()}] 🎉 Ready! Connected to {len(connected_devices)} device(s).\n")
        
        await handle_user_input(connected_devices)
        
    except KeyboardInterrupt:
        print(f"\n[{format_timestamp()}] 🛑 Stopped by user")
    
    finally:
        for device in connected_devices.values():
            await device.disconnect()
        
        print(f"[{format_timestamp()}] 🔒 All connections closed")


if __name__ == "__main__":
    asyncio.run(main())
