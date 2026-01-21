"""
Quick test script for MQTT functionality
Run this to verify MQTT client works before full integration
"""
import asyncio
import logging
from src.services.mqtt_client import MQTTDeviceManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_mqtt():
    """Test MQTT client connection and message handling."""

    print("\n=== Testing MQTT Client ===\n")

    # Create device manager without socket.io
    dm = MQTTDeviceManager(sio=None)

    # Set up detection callback
    detections = []

    def on_detect(event):
        print(f"✓ Detection: {event}")
        detections.append(event)

    dm.zet_detectie_callback(on_detect)

    print("Starting MQTT client...")
    try:
        # Start in background
        mqtt_task = asyncio.create_task(dm.start())

        # Wait for connection
        await asyncio.sleep(2)

        if dm._connected:
            print("✓ MQTT connected successfully!")
            print(f"✓ Subscribed to topics: bm/+/detect, bm/+/battery, bm/+/status")

            # Test sending commands
            print("\nTesting command publishing...")
            await dm.send_command("rood", "start")
            print("✓ Sent command: bm/rood/cmd -> start")

            await dm.start_alle()
            print("✓ Sent command: bm/all/cmd -> start")

            await dm.set_correct_kegel("blauw")
            print("✓ Sent command: bm/blauw/cmd -> correct")

            # Check device status
            print("\nDevice status:")
            status = dm.verkrijg_apparaten_status()
            for device in status:
                print(f"  - {device['kleur']}: {device['status']} (battery: {device['batterij']})")

            print("\nListening for messages for 10 seconds...")
            print("(Publish test messages with: mosquitto_pub -h localhost -t 'bm/rood/detect' -m '1')")
            await asyncio.sleep(10)

            print(f"\nTotal detections received: {len(detections)}")

        else:
            print("✗ Failed to connect to MQTT broker")
            print("Make sure Mosquitto is running: sudo systemctl status mosquitto")

        # Stop
        print("\nStopping MQTT client...")
        await dm.stop()
        mqtt_task.cancel()

        print("✓ Test complete!")

    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)
        await dm.stop()


if __name__ == "__main__":
    asyncio.run(test_mqtt())
