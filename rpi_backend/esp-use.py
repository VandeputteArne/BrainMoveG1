#!/usr/bin/env python3

import asyncio
import sys

sys.path.insert(0, "classes")

from classes.device_manager import DeviceManager
from classes.esp32_device import DetectionEvent

device_manager = DeviceManager()

def on_detection(event: DetectionEvent):
    print(f"\nDETECTION from {event.device_name}: {event.detection_bool} mm", flush=True)


def print_menu():
    print("\n" + "-" * 40)
    print("  BRAINMOVE SIMPLE CONTROLLER")
    print("-" * 40)
    print("  1. connect   - Scan and connect to devices")
    print("  2. start     - Start polling on connected devices")
    print("  3. stop      - Stop polling on connected devices")
    print("  4. sound     - Play sound on connected devices")
    print("  5. disconnect - Disconnect all devices")
    print("  6. last-detections - Show last detection per device")
    print("  0. quit      - Exit")
    print("-" * 40)

async def get_first_seen(device_manager):
    detections = device_manager.get_all_last_detections()
    for name, ev in detections.items():
        if ev and ev.detection_bool:
            return name
    return None

async def main():
    device_manager.set_detection_callback(on_detection)

    try:
        while True:
            print_menu()
            choice = input("\n> ").strip()

            if choice == "1":
                # Disconnect first if already connected to avoid "Notify acquired" error
                await device_manager.disconnect_all()
                await device_manager.scan()
                results = await device_manager.connect_all()
                for name, ok in results.items():
                    print(f"{name}: {'OK' if ok else 'FAILED'}")

            elif choice == "2":
                results = await device_manager.start_all()
                for name, ok in results.items():
                    print(f"{name}: {'started' if ok else 'failed'}")

            elif choice == "3":
                results = await device_manager.stop_all()
                for name, ok in results.items():
                    print(f"{name}: stopped")

            elif choice == "4":
                c = input("1=correct, 2=incorrect: ").strip()
                for device in device_manager.devices.values():
                    if device.connected:
                        if c == "1":
                            await device.play_correct_sound()
                        elif c == "2":
                            await device.play_incorrect_sound()

            elif choice == "5":
                await device_manager.disconnect_all()
                print("All devices disconnected")

            elif choice == "6":
                first = await get_first_seen(device_manager)
                print(first)

            elif choice == "0":
                break

    finally:
        await device_manager.disconnect_all()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n  Interrupted.")


