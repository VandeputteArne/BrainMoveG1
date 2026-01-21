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
    def __init__(self, sio=None):
        self._sio = sio
        self._client: Optional[aiomqtt.Client] = None
        self._connected = False
        self._running = False

        self._apparaten = {color: {"status": "offline", "batterij": None} for color in COLORS}
        self._detectie_callback: Optional[Callable] = None

    @property
    def apparaten(self):
        return self._apparaten.copy()

    async def start(self):
        self._running = True

        while self._running:
            try:
                async with aiomqtt.Client(BROKER_HOST, BROKER_PORT) as client:
                    self._client = client
                    self._connected = True
                    logger.info("MQTT connected to broker")

                    await client.subscribe(f"{TOPIC_PREFIX}/+/detect")
                    await client.subscribe(f"{TOPIC_PREFIX}/+/battery")
                    await client.subscribe(f"{TOPIC_PREFIX}/+/status")

                    async for message in client.messages:
                        await self._handle_message(message)

            except aiomqtt.MqttError as e:
                logger.error(f"MQTT error: {e}")
                self._connected = False
                if self._running:
                    await asyncio.sleep(2)
            except asyncio.CancelledError:
                break

        self._connected = False
        logger.info("MQTT client stopped")

    async def stop(self):
        self._running = False

    async def _handle_message(self, message: aiomqtt.Message):
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
        logger.info(f"Detection: {color} = {payload} mm")
        
        try:
            afstand = int(payload)
        except ValueError:
            afstand = 0

        if self._detectie_callback:
            self._detectie_callback({
                "apparaat_naam": f"BM-{color.capitalize()}",
                "kleur": color,
                "detectie_bool": True,
                "afstand": afstand
            })

        if self._sio:
            await self._sio.emit("device_detection", {
                "kleur": color, 
                "afstand": afstand
            })

    async def _handle_battery(self, color: str, payload: str):
        try:
            percentage = int(payload)
            self._apparaten[color]["batterij"] = percentage
            logger.debug(f"Battery: {color} = {percentage}%")
        except ValueError:
            pass

    async def _handle_status(self, color: str, payload: str):
        old_status = self._apparaten[color]["status"]
        new_status = payload
        self._apparaten[color]["status"] = new_status

        logger.info(f"Status: {color} = {new_status}")

        if self._sio and old_status != new_status:
            event = "device_connected" if new_status == "online" else "device_disconnected"
            await self._sio.emit(event, {
                "kleur": color,
                "status": new_status,
                "batterij": self._apparaten[color]["batterij"]
            })

    async def _publish(self, topic: str, payload: str):
        if self._client and self._connected:
            await self._client.publish(topic, payload, qos=0)

    async def send_command(self, color: str, command: str):
        await self._publish(f"{TOPIC_PREFIX}/{color}/cmd", command)

    async def send_command_all(self, command: str):
        await self._publish(f"{TOPIC_PREFIX}/all/cmd", command)

    async def start_alle(self):
        await self.send_command_all("start")
        logger.info("Sent START to all devices")

    async def stop_alle(self):
        await self.send_command_all("stop")
        logger.info("Sent STOP to all devices")

    async def set_correct_kegel(self, color: str):
        await self.send_command(color.lower(), "correct")
        logger.info(f"Set {color} as correct")

    async def reset_correct_kegel(self, color: str):
        await self.send_command(color.lower(), "incorrect")

    async def play_sound_correct(self, color: str):
        await self.send_command(color.lower(), "sound_ok")

    async def play_sound_incorrect(self, color: str):
        await self.send_command(color.lower(), "sound_fail")

    def zet_detectie_callback(self, callback: Optional[Callable]):
        self._detectie_callback = callback

    def verkrijg_alle_laatste_detecties(self):
        return {}

    def verkrijg_apparaten_status(self) -> list:
        return [
            {
                "kleur": color,
                "status": data["status"],
                "batterij": data["batterij"]
            }
            for color, data in self._apparaten.items()
        ]
