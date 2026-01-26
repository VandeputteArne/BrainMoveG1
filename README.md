# BrainMoveG1

Een interactief cognitief en motorisch trainingssysteem met fysieke aanraakgevoelige gekleurde potten en boeiende browsergebaseerde spelletjes. Ontworpen voor cognitieve revalidatie, fitnesscentra en educatieve omgevingen.

## Overzicht

BrainMoveG1 combineert hardware en software om een boeiende trainingservaring te creëren:

- **4 Gekleurde Aanraakpotten** - Fysieke apparaten (rood, blauw, geel, groen) met nabijheidssensoren
- **Centrale Hub** - Raspberry Pi 5 die de webapplicatie draait
- **5 Trainingsspellen** - Gericht op reactiesnelheid, geheugen en hand-oogcoördinatie
- **Real-time Communicatie** - MQTT voor hardware, Socket.IO voor multiplayer gaming

## Spellen

| Spel | Type | Beschrijving |
|------|------|--------------|
| **Color Sprint** | Reactiesnelheid | Match de weergegeven kleuren zo snel mogelijk met de fysieke potten |
| **Memory** | Geheugenreeks | Onthoud en herhaal steeds langere kleursequenties |
| **Number Match** | Cognitieve Mapping | Leer nummer-naar-kleur koppelingen en match nummers met de juiste potten |
| **Falling Colors** | Timing & Precisie | Tik op potten voordat vallende kleuren de onderkant van het scherm bereiken |
| **Color Battle** | 1v1 Multiplayer | Twee spelers racen om als eerste hun toegewezen kleuren aan te tikken |

Elk spel bevat:
- 3 moeilijkheidsgraden (Makkelijk, Gemiddeld, Moeilijk)
- Configureerbare rondes (5, 10 of 15)
- Selecteerbare kleurpotten
- Ranglijsten
- Trainingsgeschiedenis met Excel-export

## Technologie Stack

### Frontend
- **Vue 3** met TypeScript
- **Vite** build tool
- **Vue Router** voor navigatie
- **Socket.IO Client** voor real-time multiplayer
- **ApexCharts** voor datavisualisatie

### Backend
- **FastAPI** (Python)
- **SQLite3** database
- **Socket.IO Server** voor real-time communicatie
- **MQTT** (aiomqtt) voor hardwarecommunicatie
- **Uvicorn** ASGI server

### Hardware
- **Raspberry Pi 5** - Centrale server
- **ESP32 Microcontrollers** (4x) - Eén per gekleurde pot
- **VL53L0X ToF Sensoren** - Nabijheidsdetectie
- **Mosquitto** MQTT broker

## Projectstructuur

```
BrainMoveG1/
├── backend/                    # Python FastAPI backend
│   ├── src/
│   │   ├── main.py            # FastAPI applicatie entry
│   │   ├── database.py        # SQLite connectie handler
│   │   ├── models/            # Pydantic datamodellen
│   │   ├── repositories/      # Database query laag
│   │   ├── routers/           # API endpoint handlers
│   │   └── services/          # Business logic & MQTT
│   └── scripts/               # DB initialisatie scripts
│
├── frontend/                   # Vue 3 + TypeScript web app
│   ├── src/
│   │   ├── components/        # Herbruikbare Vue componenten
│   │   ├── views/             # Pagina componenten
│   │   ├── composables/       # Vue 3 composables
│   │   ├── services/          # API clients
│   │   └── router/            # Route definities
│   └── public/                # Statische bestanden
│
├── esp32/                      # Arduino firmware voor ESP32
│   └── brainmove_mqtt/        # MQTT-enabled pot firmware
│
├── hardware/                   # Hardware ontwerpbestanden
│   ├── 3d-models/             # 3D CAD bestanden voor potten
│   └── electronics/           # Schema's
│
├── docs/                       # Documentatie
│   ├── BrainMove-Installatiehandleiding.md
│   └── BrainMove-Gebruikshandleiding.md
│
└── requirements.txt            # Python dependencies
```

## Vereisten

- Raspberry Pi 5 met microSD kaart (32GB+)
- 4x ESP32 microcontrollers met VL53L0X sensoren
- USB-C voeding voor Raspberry Pi
- Python 3.11+
- Node.js 20.x
- Mosquitto MQTT broker

## Installatie

### 1. Clone de Repository

```bash
git clone https://github.com/your-org/BrainMoveG1.git
cd BrainMoveG1
```

### 2. Backend Setup

```bash
# Maak en activeer virtuele omgeving
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# of: venv\Scripts\activate  # Windows

# Installeer dependencies
pip install -r requirements.txt

# Configureer omgeving
cp .env.example .env
# Bewerk .env met je MQTT broker instellingen

# Initialiseer database
python backend/scripts/init_db.py
python backend/scripts/seed_games.py
```

### 3. Frontend Setup

```bash
cd frontend

# Installeer dependencies
npm install

# Voor ontwikkeling
npm run dev

# Voor productie build
npm run build
```

### 4. MQTT Broker Setup

```bash
# Installeer Mosquitto
sudo apt install mosquitto mosquitto-clients

# Configureer voor anonieme toegang (ontwikkeling)
sudo nano /etc/mosquitto/conf.d/brainmove.conf
# Voeg toe:
# listener 1883
# allow_anonymous true

sudo systemctl restart mosquitto
```

### 5. ESP32 Firmware

1. Open `esp32/brainmove_mqtt/brainmove_mqtt.ino` in Arduino IDE
2. Stel `DEVICE_COLOR` in op: `"rood"`, `"blauw"`, `"geel"`, of `"groen"`
3. Update WiFi-gegevens naar je netwerk
4. Flash elk ESP32 apparaat

## Applicatie Starten

### Ontwikkelmodus

```bash
# Terminal 1: Backend
source venv/bin/activate
uvicorn backend.src.main:app --host 0.0.0.0 --port 8000 --reload

# Terminal 2: Frontend
cd frontend
npm run dev
```

### Productiemodus

```bash
# Backend
uvicorn backend.src.main:app --host 0.0.0.0 --port 8000

# Frontend (serveer gebouwde bestanden)
npm install -g serve
serve -s frontend/dist -l 3000
```

### Toegangspunten

| Service | URL |
|---------|-----|
| Web App | http://localhost:3000 |
| API | http://localhost:8000 |
| API Docs (Swagger) | http://localhost:8000/docs |
| MQTT Broker | localhost:1883 |

## API Documentatie

De backend biedt een RESTful API met de volgende hoofdendpoints:

- `GET /games` - Lijst van alle beschikbare spellen
- `GET /games/{id}` - Speldetails ophalen
- `POST /trainingen` - Trainingsresultaten opslaan
- `GET /trainingen` - Trainingsgeschiedenis ophalen
- `GET /leaderboard/{game_id}` - Ranglijst voor spel ophalen
- `GET /devices` - Status van verbonden apparaten

Volledige interactieve documentatie beschikbaar op `/docs` wanneer de backend draait.

## Hardware Communicatie

### MQTT Topics

| Topic | Richting | Beschrijving |
|-------|----------|--------------|
| `bm/{kleur}/detect` | Apparaat → Server | Aanraakdetectie event |
| `bm/{kleur}/battery` | Apparaat → Server | Batterijniveau rapport |
| `bm/{kleur}/status` | Apparaat → Server | Apparaatstatus update |
| `bm/{kleur}/cmd` | Server → Apparaat | Commando's naar apparaat |

Kleuren: `rood`, `blauw`, `geel`, `groen`

## Documentatie

Gedetailleerde documentatie is beschikbaar in de `docs/` map:

- **Installatiehandleiding** - Complete setup instructies voor Raspberry Pi deployment
- **Gebruikshandleiding** - Hoe de applicatie te gebruiken en spellen te spelen

## Omgevingsvariabelen

### Backend (.env)

```env
MQTT_BROKER_HOST=localhost
MQTT_BROKER_PORT=1883
MQTT_KEEPALIVE=60
MQTT_RECONNECT_INTERVAL=5
HOST_IP=10.42.0.1
```

### Frontend (.env.production)

```env
VITE_API_BASE_URL=http://10.42.0.1:8000
```

## Licentie

Dit project is gelicentieerd onder de **GNU Affero General Public License v3.0** (AGPL-3.0).

Zie [LICENSE](LICENSE) voor details.
