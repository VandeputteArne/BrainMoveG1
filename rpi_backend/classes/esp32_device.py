#!/usr/bin/env python3

import asyncio
import os
import struct
import logging
from datetime import datetime
from typing import Callable, Optional
from enum import IntEnum
from webbrowser import get
from bleak import BleakClient
from bleak.exc import BleakError


# Constanten, Enums & Logging-------------------------------------------------------
logger = logging.getLogger(__name__)


SERVICE_UUID = "beb5483e-36e1-4688-b7f5-ea07361b26a7"
CHAR_DATA_UUID = "beb5483e-36e1-4688-b7f5-ea07361b26a8"
CHAR_COMMAND_UUID = "beb5483e-36e1-4688-b7f5-ea07361b26a9"


APPARAATNAMEN = {
    0: "BM-Blauw",
    1: "BM-Rood",
    2: "BM-Geel",
    3: "BM-Groen"
}


MAGIC_BYTE = int(os.getenv("VEILIGHEIDS_BYTE", "0x42"), 0)
APPARAAT_PREFIX = os.getenv("APPARAAT_PREFIX", "BM-")


class MessageType(IntEnum):
    STATUS = 0x01
    DETECTION = 0x02
    BATTERY = 0x03
    KEEPALIVE = 0x04

class Command(IntEnum):
    START = 0x01
    STOP = 0x02
    SLEEP = 0x03
    SOUND_CORRECT = 0x10
    SOUND_INCORRECT = 0x11

class StatusEvent(IntEnum):
    CONNECTED = 0x01
    RECONNECTED = 0x02
    SLEEPING = 0x03
    PONG = 0x04


# Type aliassen voor callbacks------------------------------------------------------------------
DetectieCallback = Callable[[dict], None]
BatterijCallback = Callable[[dict], None]
StatusCallback = Callable[[dict], None]
VerbreekCallback = Callable[[], None]


# ESP32 Apparaat Class-----------------------------------------------------------------------
class ESP32Device:
    def __init__(self, adres: str, naam: str, auto_herverbinden: bool = True):
        self.adres = adres
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
        self.bij_detectie: Optional[DetectieCallback] = None
        self.bij_batterij: Optional[BatterijCallback] = None
        self.bij_status: Optional[StatusCallback] = None
        self.bij_verbreek: Optional[VerbreekCallback] = None
        
        # Interne status
        self._herverbind_taak: Optional[asyncio.Task] = None
        self._laatste_keepalive: Optional[datetime] = None
        self.laatste_detectie: Optional[dict] = None
    

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
                self.adres,
                timeout=timeout,
                disconnected_callback=self._verwerk_verbreek
            )
            
            logger.info(f"Verbinden met {self.naam} ({self.adres})...")
            await self._client.connect()
            
            if self._client.is_connected:
                self._verbonden = True
                logger.info(f"Verbonden met {self.naam}")
                
                # Abonneren
                await self._client.start_notify(CHAR_DATA_UUID, self._notificatie_handler)
                logger.debug(f"Ontvangen notificaties van {self.naam}")
                
                self._herverbind_pogingen = 0
                return True
            
            return False
            
        except BleakError as e:
            foutmelding = str(e).lower()
            if any(x in foutmelding for x in ["not paired", "authentication", "encrypt"]):
                logger.error(f"Koppelen vereist voor {self.naam}. Gebruik bluetoothctl om te koppelen.")
            else:
                logger.error(f"BLE fout bij verbinden met {self.naam}: {e}")
            self._verbonden = False
            return False
            
        except Exception as e:
            logger.error(f"Mislukt om te verbinden met {self.naam}: {e}")
            self._verbonden = False
            return False
    

    async def verbreek(self) -> None:
        self.auto_herverbinden = False  # Voorkom auto-herverbinden
        
        if self._herverbind_taak:
            self._herverbind_taak.cancel()
            self._herverbind_taak = None
        
        if self._client and self._verbonden:
            try:
                await self._client.stop_notify(CHAR_DATA_UUID)
                await self._client.disconnect()
            except Exception as e:
                logger.debug(f"Fout tijdens verbreken: {e}")
            
            self._verbonden = False
            self._geauthenticeerd = False
            self._aan_het_pollen = False
            logger.info(f"Verbroken van {self.naam}")
    

    def _verwerk_verbreek(self, client: BleakClient) -> None:
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
        logger.info(f"Poging tot herverbinden met {self.naam} ({self._herverbind_pogingen}/{self._max_herverbind_pogingen})...")
        
        await asyncio.sleep(self._herverbind_vertraging)
        
        if await self.verbind():
            logger.info(f"Herverbonden met {self.naam}")
            # Hervat pollen als het actief was
            if self._aan_het_pollen:
                await self.start_pollen()
        elif self._herverbind_pogingen < self._max_herverbind_pogingen:
            self._herverbind_taak = asyncio.create_task(self._herverbind())
        else:
            logger.error(f"Mislukt om te herverbinden met {self.naam} na {self._max_herverbind_pogingen} pogingen")


    # Commando Methoden ---------------------------------------------------------------------    
    async def _stuur_commando(self, commando: Command, data: bytes = b'') -> bool:
        if not self._verbonden:
            logger.error(f"Kan commando niet sturen - niet verbonden met {self.naam}")
            return False
        
        if not self._geauthenticeerd:
            logger.warning(f"Apparaat {self.naam} nog niet geauthenticeerd")
        
        try:
            # Combineer commando byte met extra data
            payload = bytes([commando]) + data
            await self._client.write_gatt_char(CHAR_COMMAND_UUID, payload)
            logger.debug(f"Verzonden {commando.name} naar {self.naam} ({len(payload)} bytes)")
            return True
        except Exception as e:
            logger.error(f"Mislukt om commando te sturen naar {self.naam}: {e}")
            return False
    

    async def start_pollen(self, correcte_kegel: int) -> None:
        # Stuur kegel ID als byte (0=Blauw, 1=Rood, 2=Geel, 3=Groen)
        kegel_byte = bytes([correcte_kegel & 0xFF])
        if await self._stuur_commando(Command.START, kegel_byte):
            self._aan_het_pollen = True
            logger.info(f"{self.naam}: Pollen gestart (correcte_kegel={correcte_kegel})")
    

    async def stop_pollen(self) -> None:
        if await self._stuur_commando(Command.STOP):
            self._aan_het_pollen = False
            logger.info(f"{self.naam}: Pollen gestopt")
    

    async def slaap(self) -> None:
        if await self._stuur_commando(Command.SLEEP):
            self._aan_het_pollen = False
            logger.info(f"{self.naam}: Slaapstand ingaan")


    async def speel_correct_geluid(self) -> None:
        await self._stuur_commando(Command.SOUND_CORRECT)
    

    async def speel_incorrect_geluid(self) -> None:
        await self._stuur_commando(Command.SOUND_INCORRECT)
    

    # Notificatie Verwerking------------------------------------------------------
    def _notificatie_handler(self, sender, data: bytearray) -> None:
        if len(data) < 8:
            logger.warning(f"Bericht te kort van {self.naam}: {len(data)} bytes")
            return
        
        # Parse inkomende data header
        bericht_type, apparaat_id, magic, gereserveerd, timestamp = struct.unpack('<BBBBI', data[:8])
        
        # Verifieer magic byte
        if magic == MAGIC_BYTE:
            if not self._geauthenticeerd:
                self._geauthenticeerd = True
                logger.info(f"{self.naam} succesvol geauthenticeerd")
        else:
            logger.warning(f"Ongeldige magic byte van {self.naam}: 0x{magic:02X}")
            self._geauthenticeerd = False
            return
        
        nu = datetime.now()
        
        # Verstuur per bericht type
        if bericht_type == MessageType.STATUS:
            self._verwerk_status_bericht(data, apparaat_id, timestamp, nu)
        elif bericht_type == MessageType.DETECTION:
            self._verwerk_detectie_bericht(data, apparaat_id, timestamp, nu)
        elif bericht_type == MessageType.BATTERY:
            self._verwerk_batterij_bericht(data, apparaat_id, timestamp, nu)
        elif bericht_type == MessageType.KEEPALIVE:
            self._laatste_keepalive = nu
            logger.debug(f"{self.naam} keepalive")
        else:
            logger.warning(f"Onbekend bericht type 0x{bericht_type:02X} van {self.naam}")
    

    def _verwerk_status_bericht(self, data: bytes, apparaat_id: int, timestamp: int, nu: datetime) -> None:
        if len(data) < 9:
            return
        
        status_code = data[8]
        status_namen = {
            StatusEvent.CONNECTED: "VERBONDEN",
            StatusEvent.RECONNECTED: "HERVERBONDEN",
            StatusEvent.SLEEPING: "SLAAPT",
            StatusEvent.PONG: "PONG"
        }
        status_naam = status_namen.get(status_code, f"ONBEKEND({status_code})")
        
        if self.bij_status:
            gebeurtenis = {
                "apparaat_naam": self.naam,
                "apparaat_id": apparaat_id,
                "gebeurtenis": status_naam,
                "timestamp_ms": timestamp,
                "ontvangen_op": nu
            }
            self.bij_status(gebeurtenis)
    

    def _verwerk_detectie_bericht(self, data: bytes, apparaat_id: int, timestamp: int, nu: datetime) -> None:
        if len(data) < 10:
            return
        
        detectie_waar = struct.unpack('<H', data[8:10])[0]
        logger.debug(f"{self.naam} DETECTIE: {detectie_waar}")
        
        gebeurtenis = {
            "apparaat_naam": self.naam,
            "apparaat_id": apparaat_id,
            "detectie_bool": detectie_waar,
            "timestamp_ms": timestamp,
            "ontvangen_op": nu
        }
        self.laatste_detectie = gebeurtenis
        if self.bij_detectie:
            try:
                self.bij_detectie(gebeurtenis)
            except Exception as e:
                logger.exception(f"Fout in detectie callback voor {self.naam}: {e}")
    

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
    
    
    # Gezondheids Monitoring----------------------------------------------------------------
    def is_actief(self, timeout_seconden: float = 60.0) -> bool:
        if not self._verbonden:
            return False
        if self._laatste_keepalive is None:
            # Nog geen keepalive, maar recent verbonden
            return True
        tijd_sinds = (datetime.now() - self._laatste_keepalive).total_seconds()
        return tijd_sinds < timeout_seconden
    

    def tijd_sinds_keepalive(self) -> Optional[float]:
        if self._laatste_keepalive is None:
            return None
        return (datetime.now() - self._laatste_keepalive).total_seconds()


    # Representatie-------------------------------------------------------------------
    def __str__(self) -> str:
        status = "verbonden" if self._verbonden else "verbroken"
        return f"{self.naam} ({self.adres}) - {status}"

        
    def __repr__(self) -> str:
        status = "verbonden" if self._verbonden else "verbroken"
        return f"ESP32Device({self.naam!r}, {self.adres!r}, {status})"