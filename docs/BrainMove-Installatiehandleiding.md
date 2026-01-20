# BrainMoveAJM: Installatiegids

**Samenvatting Project**

* **Hostnaam:** `BrainMoveAJM`
* **Gebruiker:** `bmajm`
* **Wachtwoord:** `YOUR_SECURE_PASSWORD`
* **OS:** Debian Trixie (via RPi Imager)
* **Netwerk:** Hotspot `10.42.0.1`, Ethernet `192.168.137.50`
* **URL:** `http://10.42.0.1` (Poort 80)
* **SSID:** `BrainMoveG1`

---

## Fase 1: SD Kaart Flashen (Op PC)

*Doel: Het besturingssysteem correct instellen voordat we de Pi aanraken.*

1. Download en installeer **Raspberry Pi Imager** op je PC.
2. Steek de MicroSD-kaart in je PC.
3. Open Imager en kies:
* **Device:** Raspberry Pi 5.
* **OS:** Kies "Use Custom" -> Selecteer je **Debian Trixie** image bestand.
* **Storage:** Selecteer je SD-kaart.


4. Klik op **Next** en kies **EDIT SETTINGS** (OS Customisation):
* **General:**
* Hostname: `BrainMoveAJM`
* Username: `bmajm`
* Password: `YOUR_SECURE_PASSWORD`
* Wireless LAN: **Uitvinken** (We gebruiken eerst de kabel).


* **Services:**
* Vink "Enable SSH" aan -> "Use password authentication".




5. Klik op **SAVE** en **YES** om te flashen.

---

## Fase 2: Fysieke Aansluiting

*Doel: Hardware correct aansluiten. Let op de volgorde!*

1. Haal de SD-kaart uit de PC en steek deze in de Raspberry Pi.
2. Sluit de **Ethernetkabel** aan tussen de RPi en je Windows PC.
3. Sluit de **USB WiFi Dongle** aan (voor de Hotspot).
4. Sluit de **USB Bluetooth Dongle** aan (voor de ESP's).
5. **⚠️ WACHT:** Sluit de stroom (USB-C) nog **niet** aan.

---

## Fase 3: Windows Netwerk Configureren (ICS)

*Doel: Internet delen van Windows naar de Pi via de kabel.*

1. Open op Windows: `ncpa.cpl` (via Windows-toets + R).
2. Rechtermuisknop op je **WiFi-adapter** (jouw internetbron) -> **Eigenschappen** -> **Delen**.
3. Vink aan: *"Andere netwerkgebruikers toestaan verbinding te maken..."*.
4. Selecteer bij "Thuisnetwerkverbinding" de **Ethernet-adapter** van de Pi.
* *Windows geeft de ethernetpoort nu automatisch IP `192.168.137.1`.*



---

## Fase 4: Eerste Boot & Updates

*Doel: Systeem starten en basissoftware installeren.*

1. **Stroom Aan:** Sluit nu de USB-C voeding aan. Wacht 2 minuten.
2. Open PowerShell op Windows en log in:
```powershell
ssh bmajm@192.168.137.50
# Wachtwoord: YOUR_SECURE_PASSWORD

```


*(Werkt het IP niet? Probeer `ssh bmajm@BrainMoveAJM.local`)*
3. **Statisch IP vastzetten op de Pi:**
```bash
sudo nmcli con mod "Wired connection 1" ipv4.addresses 192.168.137.50/24 ipv4.gateway 192.168.137.1 ipv4.dns 8.8.8.8 ipv4.method manual
sudo nmcli con down "Wired connection 1" && sudo nmcli con up "Wired connection 1"

```


4. **Software installeren:**
```bash
# Update pakketlijsten
sudo apt update && sudo apt full-upgrade -y

# Installeer systeemtools, Python tools en Nginx
sudo apt install -y git python3-venv python3-full tree nginx

# Installeer Node.js 20 (voor frontend)
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs

```



---

## Fase 5: Bluetooth Configureren

*Doel: Interne Bluetooth uitschakelen zodat de dongle werkt.*

1. Voeg overlay toe aan config:
```bash
echo "dtoverlay=disable-bt" | sudo tee -a /boot/firmware/config.txt

```


2. Deblokkeer services:
```bash
sudo rfkill unblock bluetooth

```


3. **Herstarten (Verplicht):**
```bash
sudo reboot

```


*(Wacht 1 minuut en log opnieuw in via SSH)*

---

## Fase 6: Project Ophalen & Hotspot

*Doel: Code downloaden en WiFi netwerk (BrainMoveG1) maken.*

1. **Clone Repository:**
```bash
mkdir -p ~/BrainMove && cd ~/BrainMove
# Vervang <URL> met jouw repo
git clone <JOUW_REPO_URL> BrainMoveG1

```


2. **Hotspot Instellen:**
*Controleer met `ip link` welke interface je dongle is (meestal `wlan1` bij RPi5).*
```bash
sudo raspi-config nonint do_wifi_country BE
# Let op: SSID is BrainMoveG1
sudo nmcli con add type wifi ifname wlan1 con-name "BrainMoveG1" autoconnect yes ssid "BrainMoveG1" mode ap ipv4.method shared wifi-sec.key-mgmt wpa-psk wifi-sec.psk "YOUR_SECURE_PASSWORD"
sudo nmcli connection up "BrainMoveG1"

```



---

## Fase 7: Backend Installatie (met venv)

*Doel: Virtuele omgeving opzetten en dependencies installeren.*

1. Ga naar de map en maak de omgeving:
```bash
cd ~/BrainMove/BrainMoveG1
python3 -m venv venv
source venv/bin/activate

```


2. Installeer packages:
*Zorg dat je requirements.txt in deze map staat, of navigeer naar `backend/` indien nodig.*
```bash
pip install -r requirements.txt

```


3. Zet environment variabelen:
```bash
cp .env.example .env

```



---

## Fase 8: Frontend Build

*Doel: Website bouwen voor productie.*

1. **IP Configureren (Kritiek!):**
Open het bestand:
```bash
nano ~/BrainMove/BrainMoveG1/frontend/src/services/socket.js

```


* Zoek de regel met de URL/IP.
* Verander `localhost` naar `http://10.42.0.1:8000`.
* Sla op (Ctrl+O, Enter, Ctrl+X).


2. **Builden:**
```bash
cd ~/BrainMove/BrainMoveG1/frontend
npm install
npm run build
sudo npm install -g serve

```



---

## Fase 9: Nginx Proxy Instellen

*Doel: Poort 3000 verbergen achter poort 80 (gebruiksvriendelijk).*

1. Configuratie maken:
```bash
sudo rm /etc/nginx/sites-enabled/default
sudo nano /etc/nginx/sites-available/brainmove

```


2. Plak deze inhoud:
```nginx
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}

```


3. Activeren:
```bash
sudo ln -s /etc/nginx/sites-available/brainmove /etc/nginx/sites-enabled/
sudo systemctl restart nginx

```



---

## Fase 10: Services (Autostart met venv)

*Doel: Alles automatisch laten starten. We wijzen direct naar de python binary in de venv.*

1. **Backend Service:** `sudo nano /etc/systemd/system/brainmove-backend.service`
```ini
[Unit]
Description=BrainMove Backend
After=network.target

[Service]
User=bmajm
WorkingDirectory=/home/bmajm/BrainMove/BrainMoveG1/backend
# PYTHONPATH zorgt dat imports werken
Environment="PYTHONPATH=/home/bmajm/BrainMove/BrainMoveG1/backend:/home/bmajm/BrainMove/BrainMoveG1/backend/src"
# BELANGRIJK: Hier verwijzen we direct naar de venv uvicorn
ExecStart=/home/bmajm/BrainMove/BrainMoveG1/venv/bin/uvicorn src.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target

```


2. **Frontend Service:** `sudo nano /etc/systemd/system/brainmove-frontend.service`
```ini
[Unit]
Description=BrainMove Frontend
After=network.target brainmove-backend.service
Requires=brainmove-backend.service

[Service]
User=bmajm
WorkingDirectory=/home/bmajm/BrainMove/BrainMoveG1/frontend
ExecStart=/usr/bin/npx serve -s dist -l 3000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target

```


3. **Starten:**
```bash
sudo systemctl daemon-reload
sudo systemctl enable brainmove-backend.service brainmove-frontend.service
sudo systemctl start brainmove-backend.service brainmove-frontend.service

```



---

## Gebruikers Toegang (QR Codes)

Print deze twee QR-codes uit voor op het apparaat:

1. **Sticker 1: "Verbind met WiFi"**
* Code: `WIFI:T:WPA;S:BrainMoveG1;P:<YOUR_PASSWORD_HERE>;;`


2. **Sticker 2: "Speel het spel"**
* Code: `http://10.42.0.1`