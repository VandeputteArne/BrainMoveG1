import asyncio
import os
import struct
import logging
from datetime import datetime
from enum import IntEnum
from bleak import BleakClient
from bleak.exc import BleakError


# Constanten, Enums & Logging-------------------------------------------------------
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


SERVICE_UUID = "beb5483e-36e1-4688-b7f5-ea07361b26a7"
CHAR_DATA_UUID = "beb5483e-36e1-4688-b7f5-ea07361b26a8"
CHAR_COMMAND_UUID = "beb5483e-36e1-4688-b7f5-ea07361b26a9"


VEILIGHEIDS_BYTE = int(os.getenv("VEILIGHEIDS_BYTE", "0x42"), 0)
APPARAAT_PREFIX = os.getenv("APPARAAT_PREFIX", "BM-")


# Bericht Classes----------------------------------------------------------------------------
class MessageType(IntEnum):
    STATUS = 0x01
    DETECTIE = 0x02
    BATTERIJ = 0x03

class Command(IntEnum):
    START = 0x01
    STOP = 0x02
    GELUID_CORRECT = 0x10
    GELUID_INCORRECT = 0x11


# Type aliassen voor callbacks------------------------------------------------------------------
DetectieCallback = None
BatterijCallback = None
VerbreekCallback = None


# ESP32 Apparaat Class-----------------------------------------------------------------------
class Cone:
    def __init__(self, mac_adres: str, naam: str, auto_herverbinden: bool = True):
        self.mac_adres = mac_adres
        self.naam = naam
        self.auto_herverbinden = auto_herverbinden
        
        # Verbindingsstatus
        self._client: BleakClient
        self._verbonden = False
        self._geauthenticeerd = True
        self._aan_het_pollen = False
        
        # Herverbinding instellingen
        self._herverbind_pogingen = 0
        self._max_herverbind_pogingen = 4
        self._herverbind_vertraging = 60.0
        
        # Callbacks inkomende data
        self.bij_detectie = None
        self.bij_batterij = None
        self.bij_verbreek = None
        self.bij_herverbind = None
        
        # Interne status
        self._herverbind_taak = None
        self.laatste_detectie = None
    

    # Eigenschappen----------------------------------------------------------------------
    @property
    def verbonden(self) -> bool:
        return self._verbonden
    
    @property
    def geauthenticeerd(self) -> bool:
        return self._geauthenticeerd
    
    @property
    def is_aan_het_pollen(self) -> bool:
        return self._aan_het_pollen
    
    # Verbindings Methoden------------------------------------------------------------------    
    async def verbind(self, timeout: float = 30.0) -> bool:
        try:
            self._client = BleakClient(
                self.mac_adres,
                timeout=timeout,
                disconnected_callback=self._verwerk_verbreek
            )
            
            await self._client.connect()
            
            if self._client.is_connected:
                self._verbonden = True
                await self._client.start_notify(CHAR_DATA_UUID, self._notificatie_handler)
                self._herverbind_pogingen = 0
                logger.info(f"Verbonden met {self.naam}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Verbinden mislukt {self.naam}: {e}")
            self._verbonden = False
            return False

    async def verbreek(self) -> None:
        self.auto_herverbinden = False
        
        if self._herverbind_taak:
            self._herverbind_taak.cancel()
            self._herverbind_taak = None
        
        if self._client and self._verbonden:
            await self._client.stop_notify(CHAR_DATA_UUID)
            await self._client.disconnect()
            self._verbonden = False
            self._geauthenticeerd = False
            self._aan_het_pollen = False
            logger.info(f"Verbroken van {self.naam}")

    def _verwerk_verbreek(self, _client: BleakClient) -> None:
        self._verbonden = False
        self._geauthenticeerd = False
        self._aan_het_pollen = False
        logger.warning(f"{self.naam} verbroken")
        
        if self.bij_verbreek:
            self.bij_verbreek()
        
        if self.auto_herverbinden and self._herverbind_pogingen < self._max_herverbind_pogingen:
            self._herverbind_taak = asyncio.create_task(self._herverbind())

    async def _herverbind(self) -> None:
        self._herverbind_pogingen += 1
        logger.info(f"{self.naam} herverbinding poging {self._herverbind_pogingen}/{self._max_herverbind_pogingen}")
        await asyncio.sleep(self._herverbind_vertraging)
        
        if await self.verbind():
            logger.info(f"Herverbonden met {self.naam}")
            if self.bij_herverbind:
                self.bij_herverbind()
        elif self._herverbind_pogingen < self._max_herverbind_pogingen:
            self._herverbind_taak = asyncio.create_task(self._herverbind())
        else:
            logger.error(f"{self.naam} herverbinding mislukt na {self._max_herverbind_pogingen} pogingen")

    # Commando Methoden ---------------------------------------------------------------------    
    async def _stuur_commando(self, commando: Command, data: bytes = b'') -> bool:
        if not self._verbonden:
            return False
        
        try:
            volledig_commando = bytes([commando]) + data
            await self._client.write_gatt_char(CHAR_COMMAND_UUID, volledig_commando)
            return True
        except Exception as e:
            logger.error(f"Commando mislukt {self.naam}: {e}")
            return False

    async def start_pollen(self, correcte_kegel: int = 0) -> None:
        kegel_byte = bytes([int(correcte_kegel)])
        if await self._stuur_commando(Command.START, kegel_byte):
            self._aan_het_pollen = True
            logger.info(f"{self.naam} pollen gestart (correcte_kegel={bool(correcte_kegel)})")
        else:
            logger.warning(f"{self.naam} start pollen commando mislukt")

    async def stop_pollen(self) -> None:
        if await self._stuur_commando(Command.STOP):
            self._aan_het_pollen = False
            self.laatste_detectie = None

    async def speel_correct_geluid(self) -> None:
        await self._stuur_commando(Command.GELUID_CORRECT)

    async def speel_incorrect_geluid(self) -> None:
        await self._stuur_commando(Command.GELUID_INCORRECT)
    
    # Notificatie Verwerking------------------------------------------------------
    def _notificatie_handler(self, sender, data: bytearray) -> None:
        if len(data) < 8:
            logger.debug(f"{self.naam} ontvangen te kort bericht ({len(data)} bytes)")
            return
        
        bericht_type, apparaat_id, veiligheid_byte, gereserveerd, timestamp = struct.unpack('<BBBBI', data[:8])
        
        if veiligheid_byte != VEILIGHEIDS_BYTE:
            logger.warning(f"{self.naam} ongeldig veiligheids_byte: 0x{veiligheid_byte:02X}")
            return
        
        if not self._geauthenticeerd:
            self._geauthenticeerd = True
        
        nu = datetime.now()
        
        if bericht_type == MessageType.DETECTIE:
            self._verwerk_detectie_bericht(data, apparaat_id, timestamp, nu)
        elif bericht_type == MessageType.BATTERIJ:
            self._verwerk_batterij_bericht(data, apparaat_id, timestamp, nu)
    
    def _verwerk_detectie_bericht(self, data: bytes, apparaat_id: int, timestamp: int, nu: datetime) -> None:
        if len(data) < 10:
            return
        
        detectie_waar = struct.unpack('<H', data[8:10])[0]
        
        gebeurtenis = {
            "apparaat_naam": self.naam,
            "apparaat_id": apparaat_id,
            "detectie_bool": detectie_waar,
            "timestamp_ms": timestamp,
            "ontvangen_op": nu
        }
        self.laatste_detectie = gebeurtenis
        
        if self.bij_detectie:
            self.bij_detectie(gebeurtenis)

    def _verwerk_batterij_bericht(self, data: bytes, apparaat_id: int, timestamp: int, nu: datetime) -> None:
        if len(data) < 9:
            return
        
        percentage = data[8]
        
        if self.bij_batterij:
            gebeurtenis = {
                "apparaat_naam": self.naam,
                "apparaat_id": apparaat_id,
                "percentage": percentage,
                "timestamp_ms": timestamp,
                "ontvangen_op": nu
            }
            self.bij_batterij(gebeurtenis)

    # Representatie-------------------------------------------------------------------
    def __str__(self) -> str:
        status = "verbonden" if self._verbonden else "verbroken"
        return f"{self.naam} ({self.mac_adres}) - {status}"


    def __repr__(self) -> str:
        status = "verbonden" if self._verbonden else "verbroken"
        return f"Cone({self.naam!r}, {self.mac_adres!r}, {status})"