# BrainMove API Reference

## HTTP Endpoints

### Game Settings

#### POST `/games/{game_id}/instellingen`
Save settings for single-player games (ColorSprint, Memory, NumberMatch, FallingColors).

**Request Body:**
```json
{
  "game_id": 1,
  "gebruikersnaam": "string",
  "moeilijkheids_id": 1,
  "snelheid": 5.0,
  "ronde_id": 1,
  "rondes": 10,
  "kleuren": ["rood", "blauw", "groen", "geel"]
}
```

**Response:** Returns the same object.

---

#### POST `/games/colorbattle/instellingen`
Save settings for Color Battle (2 players).

**Request Body:**
```json
{
  "game_id": 5,
  "speler1_naam": "string",
  "speler2_naam": "string",
  "moeilijkheids_id": 1,
  "snelheid": 5.0,
  "ronde_id": 1,
  "rondes": 10,
  "kleuren": ["rood", "blauw", "groen", "geel"]
}
```

**Response:** Returns the same object.

---

### Game Control

#### GET `/games/{game_id}/play`
Start a game. Requires settings to be set first.

| game_id | Game |
|---------|------|
| 1 | Color Sprint |
| 2 | Memory |
| 3 | Number Match |
| 4 | Falling Colors |
| 5 | Color Battle |

**Response:**
```json
{
  "status": "started",
  "message": "Game is gestart"
}
```

**Errors:**
- `409`: `{"status": "already_running", "message": "Er is al een game actief."}`
- `400`: `{"status": "missing_settings", "message": "Game instellingen zijn niet compleet..."}`

---

#### GET `/games/stop`
Stop the currently running game.

**Response:**
```json
{
  "status": "stopped",
  "message": "Game gestopt"
}
```

---

### Game Information

#### GET `/games/overview`
Get all games with highscores.

**Response:**
```json
[
  {
    "game_naam": "Color Sprint",
    "tag": "reactiesnelheid",
    "highscore": 1.23,
    "eenheid": "s"
  }
]
```

---

#### GET `/games/details/{game_id}`
Get detailed information for a specific game.

---

### Leaderboard

#### GET `/leaderboard/games/{game_id}/{max}`
Get leaderboard for a game.

**Parameters:**
- `game_id`: Game ID (1-5)
- `max`: Maximum number of results

---

#### GET `/leaderboard/overview/{game_id}/{moeilijkheids_id}`
Get filtered leaderboard by difficulty.

---

### Training History

#### GET `/trainingen/laatste_rondewaarden`
Get results from the last completed training.

**Response:**
```json
{
  "game_id": 1,
  "gebruikersnaam": "string",
  "ranking": 1,
  "gemiddelde_waarde": 1.5,
  "beste_waarde": 1.2,
  "exactheid": 90.0,
  "aantal_correct": 9,
  "aantal_fout": 1,
  "aantal_telaat": 0,
  "lijst_voor_grafiek": [
    {"ronde_nummer": 1, "waarde": 1.3}
  ]
}
```

---

#### GET `/trainingen/historie/{game_id}`
Get training history with optional filters.

**Query Parameters:**
- `gebruikersnaam` (optional)
- `datum` (optional, format: dd-mm-yyyy)

---

### Devices

#### GET `/devices/status`
Get status of all hardware devices.

**Response:**
```json
{
  "apparaten": {
    "rood": {"online": true, "batterij": 85},
    "blauw": {"online": true, "batterij": 90},
    "groen": {"online": false, "batterij": null},
    "geel": {"online": true, "batterij": 75}
  },
  "connected": true,
  "totaal_verwacht": 4
}
```

---

#### POST `/devices/uitschakelen`
Shut down all devices (requires password).

**Request Body:**
```json
{
  "inputGebruiker": "password"
}
```

---

## Socket.IO Events

### Color Sprint (Game 1)

| Event | When | Payload |
|-------|------|---------|
| `gekozen_kleur` | Each round starts | `{rondenummer, maxronden, kleur}` |
| `game_einde` | Game ends | `{status: "game gedaan"}` |

**`gekozen_kleur` payload:**
```json
{
  "rondenummer": 1,
  "maxronden": 10,
  "kleur": "ROOD"
}
```

---

### Memory (Game 2)

| Event | When | Payload |
|-------|------|---------|
| `ronde_start` | Round begins | `{rondenummer, maxronden}` |
| `wacht_even` | Before sequence | `{bericht: "start"}` |
| `toon_kleur` | Each color shown | `{kleur}` |
| `kleuren_getoond` | Sequence complete | `{aantal}` |
| `fout_kleur` | Mistake/timeout | `{status}` |
| `ronde_einde` | Round ends | `{ronde, status}` |
| `game_einde` | Game ends | `{status: "game gedaan"}` |

---

### Number Match (Game 3)

| Event | When | Payload |
|-------|------|---------|
| `nummer_mapping` | Game starts | `{mapping: {kleur: nummer}}` |
| `gekozen_nummer` | Each round | `{rondenummer, maxronden, nummer}` |
| `game_einde` | Game ends | `{status: "game gedaan"}` |

**`nummer_mapping` payload:**
```json
{
  "mapping": {
    "rood": 1,
    "blauw": 2,
    "groen": 3,
    "geel": 4
  }
}
```

---

### Falling Colors (Game 4)

| Event | When | Payload |
|-------|------|---------|
| `vallende_kleur_start` | Round starts | `{rondenummer, maxronden, kleur, val_tijd}` |
| `vallende_kleur_percentage` | Every 50ms | `{percentage, rondenummer}` |
| `fout_kleur` | Player dies | `{status}` |
| `game_einde` | Game ends | `{status: "game gedaan"}` |

**`vallende_kleur_start` payload:**
```json
{
  "rondenummer": 1,
  "maxronden": 10,
  "kleur": "ROOD",
  "val_tijd": 5.0
}
```

---

### Color Battle (Game 5)

| Event | When | Payload |
|-------|------|---------|
| `colorbattle_start` | Game starts | `{speler1_naam, speler2_naam, aantal_rondes}` |
| `colorbattle_ronde` | Round starts | `{rondenummer, maxronden, speler1_kleur, speler2_kleur}` |
| `colorbattle_ronde_einde` | Round ends | See below |
| `colorbattle_einde` | Game ends | See below |

**`colorbattle_ronde_einde` payload:**
```json
{
  "rondenummer": 1,
  "speler1_kleur": "ROOD",
  "speler2_kleur": "BLAUW",
  "speler1_tijd": 1.23,
  "speler2_tijd": 1.45,
  "speler1_uitkomst": "correct",
  "speler2_uitkomst": "correct",
  "ronde_winnaar": 1
}
```
- `uitkomst`: `"correct"` | `"fout"` | `"te laat"`
- `ronde_winnaar`: `1`, `2`, or `null` (tie)

**`colorbattle_einde` payload:**
```json
{
  "speler1_naam": "Player 1",
  "speler2_naam": "Player 2",
  "speler1_correct": 7,
  "speler2_correct": 5,
  "speler1_totaal_tijd": 12.5,
  "speler2_totaal_tijd": 14.2,
  "winnaar": 1,
  "rondes": [...]
}
```
- `winnaar`: `1`, `2`, or `null` (complete tie)

---

### Error Event (All Games)

| Event | When | Payload |
|-------|------|---------|
| `game_error` | Error occurs | `{error: "message"}` |
