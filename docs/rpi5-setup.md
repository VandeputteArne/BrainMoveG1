# BrainMoveAJM: Rpi 5 Setup Gids

**Inhoudsopgave**

* [1. Projectconfiguratie](#1-projectconfiguratie)
* [2. Snelle Referentie (Echt Kopiëren-Plakken)](#2-snelle-referentie-echt-kopiëren-plakken)
  * [A. Statisch Eth0 IP instellen](#a-statisch-eth0-ip-instellen)
  * [B. Systeem bijwerken](#b-systeem-bijwerken)
  * [C. Interne Bluetooth uitschakelen](#c-interne-bluetooth-uitschakelen)
  * [D. WiFi & Bluetooth deblokkeren](#d-wifi--bluetooth-deblokkeren-indien-nodig)
  * [E. Hotspot instellen](#e-hotspot-instellen-wlan1)
  * [F. Bluetooth Koppelen](#f-bluetooth-koppelen-esp32-c3)
* [3. Gedetailleerde Setup Stappen](#3-gedetailleerde-setup-stappen)
  * [Fase 1: PC & OS Voorbereiding](#fase-1-pc--os-voorbereiding)
  * [Fase 2: Statisch Eth0 IP instellen](#fase-2-statisch-eth0-ip-instellen)
  * [Fase 3: Systeem bijwerken](#fase-3-systeem-bijwerken)
  * [Fase 4: Interne Bluetooth uitschakelen](#fase-4-interne-bluetooth-uitschakelen)
  * [Fase 5: WiFi & Bluetooth deblokkeren](#fase-5-wifi--bluetooth-deblokkeren)
  * [Fase 6: Hotspot instellen (wlan1)](#fase-6-hotspot-instellen-wlan1)
  * [Fase 7: Bluetooth Koppelen](#fase-7-bluetooth-koppelen-esp32-c3)
* [4. Verificatie (Python Script)](#4-verificatie-python-script)

---

## 1. Projectconfiguratie

| Categorie | Instelling | Waarde |
| --- | --- | --- |
| **Inloggegevens** | Hostnaam | `<REDACTED>` |
|  | Gebruiker | `<REDACTED>` |
|  | Wachtwoord | `<REDACTED>` |
| **Ethernet** | Statisch IP | `192.168.137.50/24` |
|  | Gateway (PC) | `192.168.137.1` |
|  | DNS | `8.8.8.8` |
| **Hotspot** | SSID | `<REDACTED>` |
|  | Wachtwoord | `<REDACTED>` |
| **Hardware** | Bluetooth | TP-Link UB500 (Extern) |

---

## 2. Snelle Referentie (Echt Kopiëren-Plakken)

Je kunt deze blokken rechtstreeks in je terminal plakken. Ze voeren de acties **automatisch** uit (geen editors).

**SSH Inloggen:**

```bash
ssh bmajm@BrainMoveAJM.local
# Wachtwoord: <REDACTED>

```

**A. Statisch Eth0 IP instellen**

```bash
sudo nmcli con mod "Wired connection 1" ipv4.addresses 192.168.137.50/24 ipv4.gateway 192.168.137.1 ipv4.dns 8.8.8.8 ipv4.method manual
sudo nmcli con down "Wired connection 1" && sudo nmcli con up "Wired connection 1"

# (Optioneel) Internet delen van eth0 of verbind met WiFi op wlan0 voor internettoegang:
sudo nmcli connection modify "Wired connection 1" ipv4.never-default yes
sudo ip route del default via 192.168.137.1

```

**B. Systeem bijwerken**

```bash
sudo apt update && sudo apt full-upgrade -y

```

**C. Interne Bluetooth uitschakelen**

```bash
echo "dtoverlay=disable-bt" | sudo tee -a /boot/firmware/config.txt
sudo reboot

```

**D. WiFi & Bluetooth deblokkeren (indien nodig)**

```bash
sudo rfkill unblock wifi
sudo rfkill unblock bluetooth
```

**E. Hotspot instellen (wlan1)**

```bash
sudo raspi-config nonint do_wifi_country BE
sudo nmcli con add type wifi ifname wlan1 con-name "<REDACTED>" autoconnect yes ssid "<REDACTED>" mode ap ipv4.method shared wifi-sec.key-mgmt wpa-psk wifi-sec.psk "<REDACTED>"
sudo nmcli connection up "BrainMoveAJM"

```

**F. MAC-adressen zoeken (ESP32-C3)**

```bash
sudo bluetoothctl
# In het hulpprogramma:
agent on
default-agent
scan on
# Wacht op MAC-adres...
connect XX:XX:XX:XX:XX:XX
trust XX:XX:XX:XX:XX:XX
pair XX:XX:XX:XX:XX:XX
scan off

```

**G. Project Repository klonen**

```bash
git clone # <REPO_URL>
```

**H. Pakketafhankelijkheden installeren**

```bash
cd BrainMove/BrainMoveG1
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**I. Start bij boot instellen (systemd)**

```bash
sudo cp ./devices/rpi5/brainmoveajm.service /etc/systemd/system/
sudo systemctl enable brainmoveajm.service
```

**J. Opnieuw opstarten om alle wijzigingen toe te passen**

```bash
sudo reboot
```

---

## 3. Gedetailleerde Setup Stappen

### Fase 1: PC & OS Voorbereiding

1. **Windows Internet Sharing (ICS):**
* Ga naar Netwerkverbindingen (`ncpa.cpl`).
* Klik met de rechtermuisknop op je WiFi-adapter -> Eigenschappen -> Delen.
* Vink "Andere netwerkgebruikers toestaan verbinding te maken..." aan.
* Selecteer de Ethernet-adapter waarop de Pi is aangesloten.
* *Resultaat:* Windows stelt de Ethernet-adapter automatisch in op `192.168.137.1`.

2. **OS flashen:**
* Gebruik Raspberry Pi Imager.
* OS: Raspberry Pi OS (64-bit) Bookworm.
* Instellingen: Hostnaam `BrainMoveAJM`, Gebruiker `bmajm`, Wachtwoord `secureajm5!`, **SSH inschakelen**.

### Fase 2: Statisch Eth0 IP instellen

Configureer Ethernet met een statisch IP-adres (`192.168.137.50/24`) zodat je altijd betrouwbare SSH-toegang hebt:

```bash
sudo nmcli con mod "Wired connection 1" ipv4.addresses 192.168.137.50/24 ipv4.gateway 192.168.137.1 ipv4.dns 8.8.8.8 ipv4.method manual
sudo nmcli con down "Wired connection 1" && sudo nmcli con up "Wired connection 1"
```

**Waarom statisch IP?** In plaats van DHCP (dynamisch IP dat verandert), garandeert een statisch IP dat de Pi altijd hetzelfde adres heeft, wat het betrouwbaar maakt voor SSH en netwerkcommunicatie.

### Fase 3: Systeem bijwerken

Bijwerk alle systeempakketten:

```bash
sudo apt update && sudo apt full-upgrade -y
```

**Waarom updates?** Dit brengt veiligheidsupdates, bugfixes en nieuwe functies met zich mee. `full-upgrade` verwerkt afhankelijkheidsveranderingen (veiliger dan `upgrade`).

### Fase 4: Interne Bluetooth uitschakelen

De interne Bluetooth van de RPi 5 veroorzaakt massale interferentie. We dwingen de TP-Link dongle om primair te zijn door de interne Bluetooth uit te schakelen:

```bash
echo "dtoverlay=disable-bt" | sudo tee -a /boot/firmware/config.txt
sudo reboot
```

Het commando schrijft dit rechtstreeks naar het configuratiebestand, dus na opnieuw opstarten ben je gegarandeerd dat `hci0` je TP-Link dongle is (controleer met `hciconfig -a`, zoek naar "Realtek").

### Fase 5: WiFi & Bluetooth deblokkeren

Als WiFi of Bluetooth zijn geblokkeerd door rfkill (softwareblokkering), deblokkeer ze:

```bash
sudo rfkill unblock wifi
sudo rfkill unblock bluetooth
```

**Waarom deblokkeren?** Soms blokkeert het systeem draadloze interfaces om stroom te besparen of vanwege hardwareschakelaars. Dit zorgt ervoor dat zowel WiFi als Bluetooth beschikbaar zijn voor gebruik.

### Fase 6: Hotspot instellen (wlan1)

Transformeer de WiFi-adapter (wlan1 - externe USB-adapter) in een toegangspunt (hotspot) zodat andere apparaten draadloos met de Pi kunnen verbinden:

```bash
sudo raspi-config nonint do_wifi_country BE
sudo nmcli con add type wifi ifname wlan1 con-name "BrainMoveAJM" autoconnect yes ssid "BrainMoveAJM" mode ap ipv4.method shared wifi-sec.key-mgmt wpa-psk wifi-sec.psk "bmSecure1998"
sudo nmcli connection up "BrainMoveAJM"
```

# (Optioneel) Internet delen van eth0 of verbind met WiFi op wlan0 voor internettoegang:

```bash
sudo nmcli connection modify "Wired connection 1" ipv4.never-default yes
sudo ip route del default via 192.168.137.1
```

**Parameters:**
- `ifname wlan1` - Gebruik externe WiFi-adapter (TP-Link of vergelijkbare USB WiFi dongle)
- `mode ap` - Toegangspuntmodus (WiFi-signaal uitzenden)
- `ipv4.method shared` - DHCP-server inschakelen zodat apparaten automatisch IP-adressen krijgen
- `wifi-sec.psk "bmSecure1998"` - WiFi-wachtwoord

### Fase 7: MAC-adressen zoeken (ESP32-C3)

```bash
sudo bluetoothctl
# Inside the tool:
agent on
default-agent
scan on
# Wait for MAC address...
connect XX:XX:XX:XX:XX:XX
trust XX:XX:XX:XX:XX:XX
pair XX:XX:XX:XX:XX:XX
scan off
```

### Fase 8: Project Repository klonen

Kloon de projectrepository naar de Pi:

```bash
git clone # <REPO_URL>
```

### Fase 9: Pakketafhankelijkheden installeren

Stel de Python-omgeving in en installeer vereiste pakketten:

```bash
cd BrainMove/BrainMoveG1
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**Waarom virtuele omgeving?** Dit isoleert projectafhankelijkheden van systeemPython-pakketten, waardoor versieconflicten worden voorkomen.

### Fase 10: Start bij boot instellen (systemd)

Configureer de service om automatisch op te starten bij het opstarten:

```bash
sudo cp ./devices/rpi5/brainmoveajm.service /etc/systemd/system/
sudo systemctl enable brainmoveajm.service
```

**Waarom systemd?** Dit garandeert dat de BrainMove-applicatie automatisch start wanneer de Pi opstart, wat betrouwbaar is voor headless-werking.

### Fase 11: Opnieuw opstarten om alle wijzigingen toe te passen

Start het systeem opnieuw op om alle configuraties af te ronden:

```bash
sudo reboot
```

---

## 4. Verificatie (Python Script)

Om te verifiëren dat de verbinding werkt zonder `bluetoothctl` te gebruiken, gebruik je dit testscript.

**Installeer bibliotheek:**

```bash
sudo apt install python3-pip -y
python3 -m venv myenv
source myenv/bin/activate
pip install bleak

```

**Maak script (`test_ble.py`):**

```python
import asyncio
from bleak import BleakClient

# VERVANG DIT MET JE ESP32 MAC-ADRES
ADDRESS = "<REDACTED>"

async def main():
    print(f"Verbinding maken met {ADDRESS}...")
    try:
        async with BleakClient(ADDRESS) as client:
            print(f"Verbonden: {client.is_connected}")
            for service in client.services:
                print(f"[Service] {service.uuid}")
                for char in service.characteristics:
                    print(f"  - [Char] {char.uuid}")
    except Exception as e:
        print(f"Fout: {e}")

asyncio.run(main())

```

**Voer uit:**

```bash
python test_ble.py

```

Als dit `Verbonden: True` afdrukt, is je systeem perfect geconfigureerd.