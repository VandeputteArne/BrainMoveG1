# BrainMoveAJM: Rpi 5 Setup Gids

**Inhoudsopgave**

* [1. Projectconfiguratie](https://www.google.com/search?q=%231-projectconfiguratie)
* [2. Gedetailleerde Setup Stappen](https://www.google.com/search?q=%232-gedetailleerde-setup-stappen)
* [Fase 1: Windows Netwerk Voorbereiding](https://www.google.com/search?q=%23fase-1-windows-netwerk-voorbereiding)
* [Fase 2: SD Kaart Flashen (Debian Trixie)](https://www.google.com/search?q=%23fase-2-sd-kaart-flashen-debian-trixie)
* [Fase 3: Eerste Opstart & Systeem Update](https://www.google.com/search?q=%23fase-3-eerste-opstart--systeem-update)
* [Fase 4: Bluetooth Configureren](https://www.google.com/search?q=%23fase-4-bluetooth-configureren)
* [Fase 5: Project Ophalen & Netwerk](https://www.google.com/search?q=%23fase-5-project-ophalen--netwerk)
* [Fase 6: Backend Installatie](https://www.google.com/search?q=%23fase-6-backend-installatie)
* [Fase 7: Frontend Build (Kritiek)](https://www.google.com/search?q=%23fase-7-frontend-build-kritiek)
* [Fase 8: Nginx Proxy Instellen (Nieuw)](https://www.google.com/search?q=%23fase-8-nginx-proxy-instellen-nieuw)
* [Fase 9: Services Instellen](https://www.google.com/search?q=%23fase-9-services-instellen)


* [3. Gebruikers Toegang (QR Codes)](https://www.google.com/search?q=%233-gebruikers-toegang-qr-codes)
* [4. Verificatie](https://www.google.com/search?q=%234-verificatie)

---

## 1. Projectconfiguratie

| Categorie | Instelling | Waarde |
| --- | --- | --- |
| **Systeem** | Hostnaam | `BrainMoveAJM` |
|  | OS | **Debian Trixie** (Testing / RPi OS) |
|  | Gebruiker | `bmajm` |
|  | Projectpad | `/home/bmajm/BrainMove/BrainMoveG1` |
| **Netwerk** | Eth0 IP | `192.168.137.50/24` |
|  | Hotspot IP | `10.42.0.1` (Standaard Gateway) |
| **URL** | Frontend | `http://10.42.0.1` (Poort 80 via Nginx) |
|  | Backend API | `http://10.42.0.1:8000` |

---

## 2. Gedetailleerde Setup Stappen

### Fase 1: Windows Netwerk Voorbereiding

*Doel: Internet delen vanaf Windows zodat de Pi updates kan downloaden via de kabel.*

1. Sluit de RPi5 met een ethernetkabel aan op je Windows PC.
2. Open **Netwerkverbindingen** (`ncpa.cpl`).
3. Rechtermuisknop op je **WiFi-adapter** (internetbron) -> **Eigenschappen** -> **Delen**.
4. Vink aan: *"Andere netwerkgebruikers toestaan verbinding te maken..."*.
5. Selecteer de **Ethernet-adapter** waar de Pi aan hangt.
* *Windows zet het IP van de ethernetpoort automatisch op `192.168.137.1`.*



### Fase 2: SD Kaart Flashen (Debian Trixie)

*Doel: OS installatie.*

1. Open **Raspberry Pi Imager**.
2. **OS Kiezen:** "Use Custom" -> Selecteer je Debian Trixie image.
3. **Opslag:** Selecteer SD-kaart.
4. **Settings (Tandwiel):**
* Hostname: `BrainMoveAJM`
* Username: `bmajm`
* Password: `secureajm5!`
* Enable SSH: AAN.
* Wireless LAN: UIT.


5. **Write:** Flash en steek in de Pi.

### Fase 3: Eerste Opstart & Systeem Update

*Doel: Verbinden en tools installeren.*

1. PowerShell: `ssh bmajm@192.168.137.50`.
2. Stel statisch IP in (match met Windows ICS):
```bash
sudo nmcli con mod "Wired connection 1" ipv4.addresses 192.168.137.50/24 ipv4.gateway 192.168.137.1 ipv4.dns 8.8.8.8 ipv4.method manual
sudo nmcli con down "Wired connection 1" && sudo nmcli con up "Wired connection 1"

```


3. Update en installeer tools (inclusief Nginx):
```bash
sudo apt update && sudo apt full-upgrade -y
sudo apt install -y git python3-venv python3-full tree nginx
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs

```



### Fase 4: Bluetooth Configureren

*Doel: Interne chip uitschakelen.*

1. Configuratie aanpassen:
```bash
echo "dtoverlay=disable-bt" | sudo tee -a /boot/firmware/config.txt
sudo rfkill unblock bluetooth

```


2. **Reboot:** `sudo reboot`
3. Log opnieuw in via SSH.

### Fase 5: Project Ophalen & Netwerk

*Doel: Code downloaden en Hotspot starten.*

1. **Clone:**
```bash
mkdir -p ~/BrainMove && cd ~/BrainMove
git clone <JOUW_REPO_URL> BrainMoveG1

```


2. **Hotspot:**
*Check met `ip link` of dongle `wlan0` of `wlan1` is (hier `wlan1`).*
```bash
sudo raspi-config nonint do_wifi_country BE
sudo nmcli con add type wifi ifname wlan1 con-name "BrainMoveAJM" autoconnect yes ssid "BrainMoveAJM" mode ap ipv4.method shared wifi-sec.key-mgmt wpa-psk wifi-sec.psk "bmSecure1998"
sudo nmcli connection up "BrainMoveAJM"

```



### Fase 6: Backend Installatie

```bash
cd ~/BrainMove/BrainMoveG1
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env

```

### Fase 7: Frontend Build (Kritiek)

*Doel: App bouwen voor productie.*

1. **Check IP in Code:**
Open `frontend/src/services/socket.js`.
**Belangrijk:** Zorg dat de API calls naar `http://10.42.0.1:8000` gaan (de backend blijft op poort 8000).
2. **Build:**
```bash
cd ~/BrainMove/BrainMoveG1/frontend
npm install
npm run build
sudo npm install -g serve

```



### Fase 8: Nginx Proxy Instellen (Nieuw)

*Doel: Poort 3000 verbergen achter poort 80.*

1. Verwijder standaard config:
```bash
sudo rm /etc/nginx/sites-enabled/default

```


2. Maak nieuwe config:
```bash
sudo nano /etc/nginx/sites-available/brainmove

```


3. Plak inhoud:
```nginx
server {
    listen 80;
    server_name _;

    # Proxy alles naar de frontend service op poort 3000
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


4. Activeren:
```bash
sudo ln -s /etc/nginx/sites-available/brainmove /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx

```



### Fase 9: Services Instellen

*Doel: Auto-start.*

1. **Backend Service:** `sudo nano /etc/systemd/system/brainmove-backend.service`
```ini
[Unit]
Description=BrainMove Backend
After=network.target

[Service]
User=bmajm
WorkingDirectory=/home/bmajm/BrainMove/BrainMoveG1/backend
Environment="PYTHONPATH=/home/bmajm/BrainMove/BrainMoveG1/backend:/home/bmajm/BrainMove/BrainMoveG1/backend/src"
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
# Serve op poort 3000, Nginx pakt dit op en toont het op poort 80
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

## 3. Gebruikers Toegang (QR Codes)

Om gebruikers eenvoudig te laten verbinden, print je twee QR-codes uit en plak je deze op het apparaat.

**Sticker 1: "Verbinden met WiFi"**
Gebruik een online generator (zoals qifi.org) met deze tekst:
`WIFI:T:WPA;S:BrainMoveAJM;P:bmSecure1998;;`

**Sticker 2: "Start het Spel"**
Gebruik een URL QR-code generator voor deze link:
`http://10.42.0.1`
*(Dankzij Nginx hoeft de gebruiker geen :3000 meer te typen)*

---

## 4. Verificatie

1. **Verbind:** Scan QR code 1 met je telefoon. Verbindt hij?
2. **Surf:** Scan QR code 2 (of ga naar `http://10.42.0.1`). Zie je de app?
3. **Backend Check:** Werkt de data in de app? (Dit bevestigt dat de API calls naar :8000 werken).