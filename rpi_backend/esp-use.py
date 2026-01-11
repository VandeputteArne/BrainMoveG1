#!/usr/bin/env python3

import asyncio
import sys
from datetime import datetime

sys.path.insert(0, "classes")

from bleak import BleakScanner
from config_env import (
    TRUSTED_DEVICES,
    STRICT_WHITELIST,
    SCAN_TIMEOUT,
    CONNECTION_TIMEOUT,
    MAGIC_BYTE,
)
from classes.esp32_device import (
    ESP32Device,
    DetectionEvent,
    BatteryEvent,
    StatusEvent_,
    DEVICE_PREFIX,
)


devices = {}


def on_detection(event: DetectionEvent):
    print(f"\nDETECTION from {event.device_name}: {event.distance_mm} mm")


def on_battery(event: BatteryEvent):
    print(f"\nBATTERY from {event.device_name}: {event.percent}%")


def on_status(event: StatusEvent_):
    print(f"\nSTATUS from {event.device_name}: {event.event}")


def timestamp():
    return datetime.now().strftime("%H:%M:%S")


def print_header(title: str):
    print(f"\n{'='*50}")
    print(f"  {title}")
    print(f"{'='*50}")


def print_config():
    print_header("Current Configuration")
    print(f"  MAGIC_BYTE:           0x{MAGIC_BYTE:02X}")
    print(f"  SCAN_TIMEOUT:         {SCAN_TIMEOUT}s")
    print(f"  CONNECTION_TIMEOUT:   {CONNECTION_TIMEOUT}s")
    print(f"  STRICT_WHITELIST:     {STRICT_WHITELIST}")
    print(f"\n  Trusted Devices:")
    if TRUSTED_DEVICES:
        for mac, name in TRUSTED_DEVICES.items():
            print(f"    {name}: {mac}")
    else:
        print("    (none configured)")


def print_devices():
    if not devices:
        print("  No devices yet.")
        return
    
    print_header("Devices")
    for name, device in devices.items():
        status = "connected" if device.connected else "disconnected"
        auth = "authenticated" if device.authenticated else "not authenticated"
        polling = "(polling)" if device.is_polling else ""
        print(f"  {name}: {status} | {auth} {polling}")


async def scan_for_devices():
    print_header(f"Scanning ({SCAN_TIMEOUT}s)...")
    
    discovered = await BleakScanner.discover(timeout=SCAN_TIMEOUT)
    found = []
    
    for ble_device in discovered:
        if not ble_device.name or not ble_device.name.startswith(DEVICE_PREFIX):
            continue
        
        mac = ble_device.address
        name = ble_device.name
        
        if STRICT_WHITELIST:
            trusted_macs = [m.upper() for m in TRUSTED_DEVICES.keys()]
            if mac.upper() not in trusted_macs:
                print(f"  Rejected: {name} ({mac}) - not in whitelist")
                continue
        
        if name in devices:
            print(f"  Already have: {name}")
            continue
        
        device = ESP32Device(mac, name)
        device.on_detection = on_detection
        device.on_battery = on_battery
        device.on_status = on_status
        
        devices[name] = device
        found.append(name)
        print(f"  Found: {name} ({mac})")
    
    if not found:
        print("  No new devices found.")
    else:
        print(f"\n  Found {len(found)} device(s).")


async def connect_all():
    if not devices:
        print("  No devices to connect. Run 'scan' first.")
        return
    
    print_header("Connecting...")
    
    for name, device in devices.items():
        if device.connected:
            print(f"  {name}: already connected")
            continue
        
        print(f"  Connecting to {name}...", end=" ", flush=True)
        success = await device.connect(timeout=CONNECTION_TIMEOUT)
        
        if success:
            print("OK")
        else:
            print("FAILED")


async def disconnect_all():
    print_header("Disconnecting...")
    
    for name, device in list(devices.items()):
        if device.connected:
            await device.disconnect()
            print(f"  {name}: disconnected")


async def start_polling():
    print_header("Starting polling...")
    
    count = 0
    for name, device in devices.items():
        if device.connected:
            await device.start_polling()
            print(f"  {name}: polling started")
            count += 1
    
    if count == 0:
        print("  No connected devices.")


async def stop_polling():
    print_header("Stopping polling...")
    
    for name, device in devices.items():
        if device.connected:
            await device.stop_polling()
            print(f"  {name}: stopped")


async def ping_devices():
    print_header("Pinging...")
    
    for name, device in devices.items():
        if device.connected:
            await device.ping()
            print(f"  {name}: ping sent")


async def play_sounds():
    print("\n  1. Correct sound")
    print("  2. Incorrect sound")
    
    choice = input("\n  Choose (1/2): ").strip()
    
    for name, device in devices.items():
        if device.connected:
            if choice == "1":
                await device.play_correct_sound()
                print(f"  {name}: correct sound")
            elif choice == "2":
                await device.play_incorrect_sound()
                print(f"  {name}: incorrect sound")


async def sleep_devices():
    print_header("Sleep Mode")
    print("  Warning: Devices will power down and disconnect!")
    
    confirm = input("  Continue? (y/n): ").strip().lower()
    if confirm != 'y':
        print("  Cancelled.")
        return
    
    for name, device in devices.items():
        if device.connected:
            await device.sleep()
            print(f"  {name}: entering sleep")


async def monitor_mode():
    print_header("Monitor Mode")
    print("  Press Enter to stop...\n")
    
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, input)
    
    print("  Monitor stopped.")


def show_pairing_help():
    print_header("Pairing Instructions")
    print("""
  Linux / Raspberry Pi:
  1. bluetoothctl
  2. scan on
  3. Find your device (e.g., BM-Blue)
  4. pair <MAC_ADDRESS>
  5. trust <MAC_ADDRESS>
  6. quit
  
  After pairing once, the bond is saved.
    """)


def print_menu():
    print("\n" + "-" * 50)
    print("  BRAINMOVE TEST CONSOLE")
    print("-" * 50)
    print("  1. scan      - Find BLE devices")
    print("  2. connect   - Connect to devices")
    print("  3. start     - Start polling")
    print("  4. stop      - Stop polling")
    print("  5. ping      - Ping devices")
    print("  6. sound     - Play sounds")
    print("  7. monitor   - Watch for events")
    print("  8. status    - Show devices")
    print("  9. config    - Show configuration")
    print("  h. help      - Pairing help")
    print("  0. quit      - Exit")
    print("-" * 50)


async def main():
    print("\n" + "="*50)
    print("  BRAINMOVE TEST APPLICATION")
    print("="*50)
    print("\n  Quick Start:")
    print("  1. Type 'scan' to find devices")
    print("  2. Type 'connect' to connect")
    print("  3. Type 'start' to begin detection\n")
    
    try:
        while True:
            print_menu()
            choice = input("\n  > ").strip().lower()
            
            if choice in ("1", "scan"):
                await scan_for_devices()
            elif choice in ("2", "connect"):
                await connect_all()
            elif choice in ("3", "start"):
                await start_polling()
            elif choice in ("4", "stop"):
                await stop_polling()
            elif choice in ("5", "ping"):
                await ping_devices()
            elif choice in ("6", "sound"):
                await play_sounds()
            elif choice in ("7", "monitor"):
                await monitor_mode()
            elif choice in ("8", "status"):
                print_devices()
            elif choice in ("9", "config"):
                print_config()
            elif choice in ("h", "help"):
                show_pairing_help()
            elif choice in ("0", "quit", "exit", "q"):
                print("\n  Goodbye.\n")
                break
            else:
                print("  Unknown command.")
    
    finally:
        await disconnect_all()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n  Interrupted.\n")


