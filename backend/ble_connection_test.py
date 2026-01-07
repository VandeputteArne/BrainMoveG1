import asyncio
from bleak import BleakScanner, BleakClient

# UUIDs - Moeten exact overeenkomen met de ESP32 code
# Zorg dat deze hetzelfde zijn als in je C++ bestand
SERVICE_UUID = "4fafc201-1fb5-459e-8fcc-c5c9c331914b"
CHAR_DATA_UUID = "beb5483e-36e1-4688-b7f5-ea07361b26a8"    # Read/Notify
CHAR_COMMAND_UUID = "beb5483e-36e1-4688-b7f5-ea07361b26a9" # Write

# Naam van het apparaat zoals gedefinieerd in de ESP32 code
TARGET_DEVICE_NAME = "BM-Test-C3"

async def notification_handler(sender, data):
    """
    Deze functie wordt aangeroepen wanneer de ESP32 data stuurt.
    """
    # Decodeer bytes naar string
    decoded_message = data.decode('utf-8')
    print(f"📩 Ontvangen van ESP32: {decoded_message}")

async def main():
    print(f"🔍 Scannen naar '{TARGET_DEVICE_NAME}'...")
    
    # Scan naar het apparaat
    device = await BleakScanner.find_device_by_filter(
        lambda d, ad: d.name and d.name == TARGET_DEVICE_NAME
    )

    if not device:
        print(f"❌ Apparaat '{TARGET_DEVICE_NAME}' niet gevonden.")
        print("   Tips: Controleer of ESP32 aan staat en 'USB CDC On Boot' actief is.")
        return

    print(f"✅ Apparaat gevonden: {device.address}")
    print("🔗 Verbinding maken...")

    async with BleakClient(device) as client:
        print(f"✅ Verbonden! Connected: {client.is_connected}")

        # 1. Abonneren op notificaties (Subscribe to notifications)
        # Dit zorgt ervoor dat we de "TEST #1..." berichten ontvangen
        await client.start_notify(CHAR_DATA_UUID, notification_handler)
        print("👂 Luisteren naar notificaties...")

        # Wacht 5 seconden om een paar testberichten te ontvangen
        await asyncio.sleep(5)

        # 2. Een commando sturen (Write command)
        # We sturen de byte 0x42 (hexadecimaal voor decimaal 66)
        print("\n📤 Commando sturen (0x42)...")
        command_bytes = bytes([0x42]) 
        await client.write_gatt_char(CHAR_COMMAND_UUID, command_bytes)

        # Wacht nog 5 seconden om de "ACK" (bevestiging) te zien
        await asyncio.sleep(5)

        # Stoppen
        print("\n🛑 Test voltooid, verbinding verbreken...")
        await client.stop_notify(CHAR_DATA_UUID)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nGebruiker stopte het script.")
    except Exception as e:
        print(f"\n❌ Er ging iets mis: {e}")