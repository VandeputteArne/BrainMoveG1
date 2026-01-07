#!/usr/bin/env python3
"""
BLE Connection Test for Raspberry Pi
Simple test to verify BLE connection between Raspberry Pi and ESP32

This code:
- Scans for ESP32 BLE devices
- Connects to the device
- Receives and displays test messages
- Sends simple test commands

PAIRING INSTRUCTIONS:
If connection fails, pair the device first:
    1. bluetoothctl
    2. scan on
    3. pair <MAC_ADDRESS>
    4. trust <MAC_ADDRESS>
    5. exit
"""

import asyncio
import sys
from datetime import datetime
from bleak import BleakClient, BleakScanner
from bleak.exc import BleakError

# BLE UUIDs - must match ESP32
SERVICE_UUID = "4fafc201-1fb5-459e-8fcc-c5c9c331914b"
CHAR_DATA_UUID = "beb5483e-36e1-4688-b7f5-ea07361b26a8"
CHAR_COMMAND_UUID = "beb5483e-36e1-4688-b7f5-ea07361b26a9"

# Device name to look for
DEVICE_PREFIX = "BM-"

def format_timestamp():
    """Get formatted timestamp for logging"""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]


class BLETestClient:
    """Simple BLE client for testing ESP32 connection"""
    
    def __init__(self, address: str, name: str):
        self.address = address
        self.name = name
        self.client = None
        self.connected = False
        self.message_count = 0
    
    def notification_handler(self, sender, data: bytearray):
        """Handle incoming BLE notifications"""
        self.message_count += 1
        try:
            # Try to decode as UTF-8 text
            message = data.decode('utf-8')
            print(f"[{format_timestamp()}] 📨 Message #{self.message_count}: {message}")
        except:
            # If not text, show as hex
            hex_data = ' '.join([f'{b:02X}' for b in data])
            print(f"[{format_timestamp()}] 📨 Raw data #{self.message_count}: {hex_data}")
    
    async def connect(self):
        """Connect to the ESP32 device"""
        try:
            print(f"[{format_timestamp()}] 🔗 Connecting to {self.name} ({self.address})...")
            
            self.client = BleakClient(
                self.address,
                timeout=30.0,
                disconnected_callback=self._on_disconnect
            )
            
            await self.client.connect()
            self.connected = True
            
            print(f"[{format_timestamp()}] ✅ Connected to {self.name}")
            print(f"[{format_timestamp()}] 🔐 Connection is secured")
            
            # Subscribe to notifications
            await self.client.start_notify(CHAR_DATA_UUID, self.notification_handler)
            print(f"[{format_timestamp()}] 📡 Subscribed to notifications")
            
            return True
            
        except BleakError as e:
            error_msg = str(e).lower()
            if "not paired" in error_msg or "authentication" in error_msg:
                print(f"\n[{format_timestamp()}] 🔒 PAIRING REQUIRED!")
                print(f"Run these commands to pair:")
                print(f"  bluetoothctl")
                print(f"  pair {self.address}")
                print(f"  trust {self.address}")
                print(f"  exit\n")
            else:
                print(f"[{format_timestamp()}] ❌ Connection error: {e}")
            return False
        except Exception as e:
            print(f"[{format_timestamp()}] ❌ Failed to connect: {e}")
            return False
    
    def _on_disconnect(self, client):
        """Callback when device disconnects"""
        self.connected = False
        print(f"[{format_timestamp()}] ⚠️  Disconnected from {self.name}")
    
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
    
    async def send_command(self, command_byte: int):
        """Send a test command to ESP32"""
        if not self.connected:
            print(f"[{format_timestamp()}] ❌ Not connected - cannot send command")
            return False
        
        try:
            cmd_data = bytes([command_byte])
            await self.client.write_gatt_char(CHAR_COMMAND_UUID, cmd_data)
            print(f"[{format_timestamp()}] 📤 Sent command: 0x{command_byte:02X}")
            return True
        except Exception as e:
            print(f"[{format_timestamp()}] ❌ Failed to send command: {e}")
            return False


async def scan_for_devices():
    """Scan for BLE devices with matching prefix"""
    print(f"[{format_timestamp()}] 🔍 Scanning for devices (prefix: {DEVICE_PREFIX})...")
    
    devices = await BleakScanner.discover(timeout=5.0)
    
    found_devices = []
    for device in devices:
        if device.name and device.name.startswith(DEVICE_PREFIX):
            found_devices.append((device.address, device.name))
            print(f"[{format_timestamp()}] 📱 Found: {device.name} ({device.address})")
    
    return found_devices


async def interactive_test(client: BLETestClient):
    """Interactive test mode with user commands"""
    print("\n" + "=" * 70)
    print("Interactive Test Mode - Available Commands:")
    print("  ping      - Send a ping command (0x01)")
    print("  test      - Send a test command (0xFF)")
    print("  status    - Show connection status")
    print("  quit      - Exit")
    print("=" * 70 + "\n")
    
    while True:
        try:
            loop = asyncio.get_event_loop()
            user_input = await loop.run_in_executor(None, input, "Command: ")
            
            cmd = user_input.strip().lower()
            
            if cmd == 'quit' or cmd == 'exit':
                break
            
            elif cmd == 'ping':
                await client.send_command(0x01)
            
            elif cmd == 'test':
                await client.send_command(0xFF)
            
            elif cmd == 'status':
                status = "✅ Connected" if client.connected else "❌ Disconnected"
                print(f"\nDevice: {client.name} ({client.address})")
                print(f"Status: {status}")
                print(f"Messages received: {client.message_count}\n")
            
            elif cmd == 'help':
                print("\nCommands: ping, test, status, quit\n")
            
            elif cmd:
                print(f"Unknown command: {cmd}")
                
        except EOFError:
            break
        except Exception as e:
            print(f"Error: {e}")


async def main():
    """Main test program"""
    print("=" * 70)
    print("   BLE Connection Test - Raspberry Pi")
    print("   Simple BLE test for ESP32 connection")
    print("=" * 70)
    print()
    
    client = None
    
    try:
        # Scan for devices
        devices = await scan_for_devices()
        
        if not devices:
            print(f"\n[{format_timestamp()}] ⚠️  No devices found!")
            print(f"Make sure your ESP32 is running and advertising.\n")
            return
        
        # Connect to first device found
        address, name = devices[0]
        client = BLETestClient(address, name)
        
        if not await client.connect():
            print(f"\n[{format_timestamp()}] ❌ Connection failed. Exiting.\n")
            return
        
        print(f"\n[{format_timestamp()}] 🎉 Connection test successful!")
        print(f"[{format_timestamp()}] 📡 Listening for messages...\n")
        
        # Enter interactive mode
        await interactive_test(client)
        
    except KeyboardInterrupt:
        print(f"\n[{format_timestamp()}] 🛑 Stopped by user")
    
    finally:
        if client:
            await client.disconnect()
        print(f"[{format_timestamp()}] 🔒 Test complete\n")


if __name__ == "__main__":
    print("\n💡 Tip: If pairing is needed, press Ctrl+C and follow the instructions.\n")
    asyncio.run(main())
