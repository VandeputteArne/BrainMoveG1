"""
MQTT Client for BrainMove - Replaces BLE communication
"""
import asyncio
import logging
from typing import Callable, Optional
import aiomqtt

logger = logging.getLogger(__name__)

BROKER_HOST = "localhost"
BROKER_PORT = 1883
TOPIC_PREFIX = "bm"

COLORS = ["rood", "blauw", "geel", "groen"]


class MQTTDeviceManager:
    """
    Manages ESP32 devices via MQTT.
    Replaces the BLE-based DeviceManager.
    """

    def __init__(self, sio=None):
        self._sio = sio
        self._client: Optional[aiomqtt.Client] = None
        self._connected = False
        self._running = False

        # Device state
        self._apparaten = {color: {"status": "offline", "batterij": None} for color in COLORS}
        self._detectie_callback: Optional[Callable] = None

    @property
    def apparaten(self):
        return self._apparaten.copy()

    async def start(self):
        """Start MQTT client and subscribe to topics."""
        self._running = True

        while self._running:
            try:
                async with aiomqtt.Client(BROKER_HOST, BROKER_PORT) as client:
                    self._client = client
                    self._connected = True
                    logger.info("MQTT connected to broker")

                    # Subscribe to all device topics
                    await client.subscribe(f"{TOPIC_PREFIX}/+/detect")
                    await client.subscribe(f"{TOPIC_PREFIX}/+/battery")
                    await client.subscribe(f"{TOPIC_PREFIX}/+/status")

                    # Process incoming messages
                    async for message in client.messages:
                        await self._handle_message(message)

            except aiomqtt.MqttError as e:
                logger.error(f"MQTT error: {e}")
                self._connected = False
                if self._running:
                    await asyncio.sleep(2)  # Reconnect delay
            except asyncio.CancelledError:
                break

        self._connected = False
        logger.info("MQTT client stopped")

    async def stop(self):
        """Stop MQTT client."""
        self._running = False

    async def _handle_message(self, message: aiomqtt.Message):
        """Process incoming MQTT message."""
        topic_parts = str(message.topic).split("/")
        if len(topic_parts) != 3:
            return

        _, color, msg_type = topic_parts
        payload = message.payload.decode() if message.payload else ""

        if color not in COLORS:
            return

        if msg_type == "detect":
            await self._handle_detection(color, payload)
        elif msg_type == "battery":
            await self._handle_battery(color, payload)
        elif msg_type == "status":
            await self._handle_status(color, payload)

    async def _handle_detection(self, color: str, payload: str):
        """Handle detection event from ESP."""
        logger.info(f"Detection: {color} = {payload}")

        if self._detectie_callback:
            self._detectie_callback({
                "apparaat_naam": f"BM-{color.capitalize()}",
                "kleur": color,
                "detectie_bool": payload == "1"
            })

        # Emit to frontend
        if self._sio:
            await self._sio.emit("device_detection", {"kleur": color})

    async def _handle_battery(self, color: str, payload: str):
        """Handle battery update from ESP."""
        try:
            percentage = int(payload)
            self._apparaten[color]["batterij"] = percentage
            logger.debug(f"Battery: {color} = {percentage}%")
        except ValueError:
            pass

    async def _handle_status(self, color: str, payload: str):
        """Handle status update (online/offline) from ESP."""
        old_status = self._apparaten[color]["status"]
        new_status = payload  # "online" or "offline"
        self._apparaten[color]["status"] = new_status

        logger.info(f"Status: {color} = {new_status}")

        if self._sio and old_status != new_status:
            event = "device_connected" if new_status == "online" else "device_disconnected"
            await self._sio.emit(event, {
                "kleur": color,
                "status": new_status,
                "batterij": self._apparaten[color]["batterij"]
            })

    # ==================== Commands (RPI → ESP) ====================

    async def _publish(self, topic: str, payload: str):
        """Publish message to MQTT broker."""
        if self._client and self._connected:
            await self._client.publish(topic, payload, qos=0)

    async def send_command(self, color: str, command: str):
        """Send command to specific device."""
        await self._publish(f"{TOPIC_PREFIX}/{color}/cmd", command)

    async def send_command_all(self, command: str):
        """Send command to all devices."""
        await self._publish(f"{TOPIC_PREFIX}/all/cmd", command)

    async def start_alle(self):
        """Start polling on all devices."""
        await self.send_command_all("start")
        logger.info("Sent START to all devices")

    async def stop_alle(self):
        """Stop polling on all devices."""
        await self.send_command_all("stop")
        logger.info("Sent STOP to all devices")

    async def set_correct_kegel(self, color: str):
        """Mark a cone as the correct target."""
        await self.send_command(color.lower(), "correct")
        logger.info(f"Set {color} as correct")

    async def reset_correct_kegel(self, color: str):
        """Reset a cone to not be the target."""
        await self.send_command(color.lower(), "incorrect")

    async def play_sound_correct(self, color: str):
        """Play correct sound on device."""
        await self.send_command(color.lower(), "sound_ok")

    async def play_sound_incorrect(self, color: str):
        """Play incorrect sound on device."""
        await self.send_command(color.lower(), "sound_fail")

    # ==================== Callbacks ====================

    def zet_detectie_callback(self, callback: Optional[Callable]):
        """Set detection callback for game logic."""
        self._detectie_callback = callback

    def verwijder_alle_laatste_detecties(self):
        """Clear detection state (compatibility)."""
        pass  # Not needed with MQTT

    def verkrijg_alle_laatste_detecties(self):
        """Get last detections (compatibility)."""
        return {}

    def verkrijg_apparaten_status(self) -> list:
        """Get status of all devices."""
        return [
            {
                "kleur": color,
                "status": data["status"],
                "batterij": data["batterij"]
            }
            for color, data in self._apparaten.items()
        ]
