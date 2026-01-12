#!/usr/bin/env python3

import asyncio
import sys
from datetime import datetime

sys.path.insert(0, "classes")

from classes.device_manager import DeviceManager
from classes.esp32_device import (
    DetectionEvent,
    BatteryEvent,
    StatusEvent_,
)

# Global DeviceManager instance
device_manager = DeviceManager()

def on_detection(event: DetectionEvent):
    if event.distance_mm < 1800: # Distance threshold
        print(f"\nDETECTION from {event.device_name}: {event.distance_mm} mm", flush=True)

def on_battery(event: BatteryEvent):
    print(f"\nBATTERY from {event.device_name}: {event.percent}%", flush=True)


def on_status(event: StatusEvent_):
    print(f"\nSTATUS from {event.device_name}: {event.event}", flush=True)


def timestamp():
    return datetime.now().strftime("%H:%M:%S")


def print_header(title: str):
    print(f"\n{'='*50}")
    print(f"  {title}")
    print(f"{'='*50}")


def print_config():
    print_header("Current Configuration")
    print(f"  MAGIC_BYTE:           0x{device_manager.magic_byte:02X}")
    print(f"  SCAN_TIMEOUT:         {device_manager.scan_timeout}s")
    print(f"  CONNECTION_TIMEOUT:   {device_manager.connection_timeout}s")
    print(f"  STRICT_WHITELIST:     {device_manager.strict_whitelist}")
    print(f"\n  Trusted Devices:")
    if device_manager.trusted_macs:
        for mac, name in device_manager.trusted_macs.items():
            print(f"    {name}: {mac}")
    else:
        print("    (none configured)")


def print_devices():
    devices = device_manager.devices
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
    print_header(f"Scanning ({device_manager.scan_timeout}s)...")
    
    new_devices = await device_manager.scan()
    
    if not new_devices:
        print("  No new devices found.")
    else:
        print(f"\n  Found {len(new_devices)} device(s).")


async def connect_all():
    devices = device_manager.devices
    if not devices:
        print("  No devices to connect. Run 'scan' first.")
        return
    
    print_header("Connecting...")
    
    results = await device_manager.connect_all()
    
    for name, success in results.items():
        if success:
            print(f"  {name}: OK")
        else:
            print(f"  {name}: FAILED")


async def disconnect_all():
    print_header("Disconnecting...")
    await device_manager.disconnect_all()
    print("  All devices disconnected")


async def start_polling():
    print_header("Starting polling...")
    
    results = await device_manager.start_all()
    
    if not results:
        print("  No connected devices.")
    else:
        for name, success in results.items():
            print(f"  {name}: {'polling started' if success else 'failed'}")


async def stop_polling():
    print_header("Stopping polling...")
    
    results = await device_manager.stop_all()
    
    for name, success in results.items():
        print(f"  {name}: {'stopped' if success else 'failed'}")


async def ping_devices():
    print_header("Pinging...")
    
    devices = device_manager.devices
    for name, device in devices.items():
        if device.connected:
            await device.ping()
            print(f"  {name}: ping sent")


async def play_sounds():
    print("\n  1. Correct sound")
    print("  2. Incorrect sound")
    
    choice = input("\n  Choose (1/2): ").strip()
    
    devices = device_manager.devices
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
    
    devices = device_manager.devices
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
    
    # Set callbacks once for all devices (current and future)
    device_manager.set_detection_callback(on_detection)
    device_manager.set_battery_callback(on_battery)
    device_manager.set_status_callback(on_status)
    
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


