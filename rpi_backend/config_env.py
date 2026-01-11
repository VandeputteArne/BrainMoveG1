from dotenv import load_dotenv
import os

load_dotenv()   # Load .env

TRUSTED_DEVICES = {}
for color in ("BLUE","RED","YELLOW","GREEN"):
    mac = os.getenv(f"DEVICE_BM_{color}")
    if mac:
        TRUSTED_DEVICES[mac] = f"BM-{color.capitalize()}"

MAGIC_BYTE = int(os.getenv("MAGIC_BYTE", "0x42"), 0)
SCAN_TIMEOUT = float(os.getenv("SCAN_TIMEOUT", "5.0"))
CONNECTION_TIMEOUT = float(os.getenv("CONNECTION_TIMEOUT", "10.0"))
STRICT_WHITELIST = os.getenv("STRICT_WHITELIST", "").lower() == "true"