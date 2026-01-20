import asyncio
import os
import struct
import logging
from enum import IntEnum
from bleak import BleakClient
from bleak.exc import BleakError

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

SERVICE_UUID = "beb5483e-36e1-4688-b7f5-ea07361b26a7"
CHAR_DATA_UUID = "beb5483e-36e1-4688-b7f5-ea07361b26a8"
CHAR_COMMAND_UUID = "beb5483e-36e1-4688-b7f5-ea07361b26a9"

VEILIGHEIDS_BYTE = int(os.getenv("VEILIGHEIDS_BYTE", "0x42"), 0)
APPARAAT_PREFIX = os.getenv("APPARAAT_PREFIX", "BM-")

class MessageType(IntEnum):
    STATUS = 0x01
    DETECTIE = 0x02
    BATTERIJ = 0x03

class Command(IntEnum):
    START = 0x01
    STOP = 0x02
    KEEPALIVE = 0x05
    SET_CORRECT = 0x06
    GELUID_CORRECT = 0x10
    GELUID_INCORRECT = 0x11

DetectieCallback = None
BatterijCallback = None
VerbreekCallback = None

class Cone:
    def __init__(self, mac_adres: str, naam: str, lock: asyncio.Lock = None, auto_herverbinden: bool = True):
        self.mac_adres = mac_adres
        self.naam = naam
        self._lock = lock
        self.auto_herverbinden = auto_herverbinden
        
        self._client: BleakClient
        self._verbonden = False
        self._geauthenticeerd = True
        self._aan_het_pollen = False
        
        self._herverbind_pogingen = 0
        self._max_herverbind_pogingen = 1000000 
        self._herverbind_vertraging = 5.0
        
        self.bij_detectie = None
        self.bij_batterij = None
        self.bij_verbreek = None
        self.bij_herverbind = None
        
        self._herverbind_taak = None
        self.laatste_detectie = None

    @property
    def verbonden(self) -> bool: return self._verbonden
    
    @property
    def geauthenticeerd(self) -> bool: return self._geauthenticeerd
    
    @property
    def is_aan_het_pollen(self) -> bool: return self._aan_het_pollen
        
    async def verbind(self, timeout: float = 30.0) -> bool:
        async def _doe_verbinden():
            try:
                self._client = BleakClient(
                    self.mac_adres, 
                    timeout=timeout, 
                    disconnected_callback=self._verwerk_verbreek
                )
                await self._client.connect()
                
                if self._client.is_connected:
                    self._verbonden = True
                    try:
                        await self._client.start_notify(CHAR_DATA_UUID, self._notificatie_handler)
                    except BleakError: 
                        pass
                        
                    self._herverbind_pogingen = 0
                    logger.info(f"Verbonden: {self.naam}")
                    return True
                return False
            except Exception as e:
                logger.error(f"Fout {self.naam}: {e}")
                self._verbonden = False
                return False

        if self._lock:
            async with self._lock: 
                return await _doe_verbinden()
        return await _doe_verbinden()

    async def verbreek(self) -> None:
        self.auto_herverbinden = False
        if self._herverbind_taak:
            self._herverbind_taak.cancel()
            self._herverbind_taak = None
        
        if self._client and self._verbonden:
            try: 
                await self._client.stop_notify(CHAR_DATA_UUID)
            except Exception: 
                pass
            
            await self._client.disconnect()
            self._verbonden = False
            self._geauthenticeerd = False
            self._aan_het_pollen = False

    def _verwerk_verbreek(self, _client: BleakClient) -> None:
        self._verbonden = False
        self._geauthenticeerd = False
        self._aan_het_pollen = False
        
        if self.bij_verbreek: 
            self.bij_verbreek()
            
        if self.auto_herverbinden and self._herverbind_pogingen < self._max_herverbind_pogingen:
            self._herverbind_taak = asyncio.create_task(self._herverbind())

    async def _herverbind(self) -> None:
        self._herverbind_pogingen += 1
        await asyncio.sleep(self._herverbind_vertraging)
        
        if await self.verbind():
            if self.bij_herverbind: 
                self.bij_herverbind()
        elif self._herverbind_pogingen < self._max_herverbind_pogingen:
            self._herverbind_taak = asyncio.create_task(self._herverbind())

    async def send_keepalive(self) -> bool:
        return await self._stuur_commando(Command.KEEPALIVE)

    async def _stuur_commando(self, commando: Command, data: bytes = b'', wacht_op_antwoord: bool = False) -> bool:
        if not self._verbonden: return False
        try:
            payload = bytes([commando]) + data
            # response=False means "write without response" - much faster, doesn't wait for ACK
            await self._client.write_gatt_char(CHAR_COMMAND_UUID, payload, response=wacht_op_antwoord)
            return True
        except Exception:
            return False

    async def start_pollen(self) -> None:
        if await self._stuur_commando(Command.START):
            self._aan_het_pollen = True

    async def set_correct(self, is_correct: bool = False) -> bool:
        payload = bytes([int(is_correct)])
        return await self._stuur_commando(Command.SET_CORRECT, payload)

    async def stop_pollen(self) -> None:
        if await self._stuur_commando(Command.STOP):
            self._aan_het_pollen = False
            self.laatste_detectie = None

    async def speel_correct_geluid(self) -> None: 
        await self._stuur_commando(Command.GELUID_CORRECT)
        
    async def speel_incorrect_geluid(self) -> None: 
        await self._stuur_commando(Command.GELUID_INCORRECT)
    
    def _notificatie_handler(self, sender, data: bytearray) -> None:
        if len(data) < 4: return
        
        bericht_type, _, veiligheid_byte, _ = struct.unpack('<BBBB', data[:4])
        
        if veiligheid_byte != VEILIGHEIDS_BYTE: return
        if not self._geauthenticeerd: self._geauthenticeerd = True
        
        if bericht_type == MessageType.DETECTIE: 
            self._verwerk_detectie_bericht(data, data[1])
        elif bericht_type == MessageType.BATTERIJ: 
            self._verwerk_batterij_bericht(data, data[1])
    
    def _verwerk_detectie_bericht(self, data: bytes, apparaat_id: int) -> None:
        if len(data) < 6: return
        
        detectie_waar = struct.unpack('<H', data[4:6])[0]
        gebeurtenis = {
            "apparaat_naam": self.naam, 
            "apparaat_id": apparaat_id, 
            "detectie_bool": detectie_waar
        }
        self.laatste_detectie = gebeurtenis
        if self.bij_detectie: self.bij_detectie(gebeurtenis)

    def _verwerk_batterij_bericht(self, data: bytes, apparaat_id: int) -> None:
        if len(data) < 5: return
        
        gebeurtenis = {
            "apparaat_naam": self.naam, 
            "apparaat_id": apparaat_id, 
            "percentage": data[4]
        }
        if self.bij_batterij: self.bij_batterij(gebeurtenis)

    def __str__(self) -> str: 
        status = 'verbonden' if self._verbonden else 'verbroken'
        return f"{self.naam} ({self.mac_adres}) - {status}"
        
    def __repr__(self) -> str: 
        return f"Cone({self.naam!r}, {self.mac_adres!r})"