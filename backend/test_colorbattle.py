"""
Test script for Color Battle game with Socket.IO events
Run this while the backend is running to see real-time game events.

Usage:
1. Start the backend: python -m backend.src.main
2. Run this script: python backend/test_colorbattle.py
3. Touch the cones when prompted!
"""

import socketio
import requests
import time

BASE_URL = "http://localhost:8000"

# Socket.IO client
sio = socketio.Client()

@sio.event
def connect():
    print("\n✓ Connected to server")

@sio.event
def disconnect():
    print("\n✗ Disconnected from server")

@sio.on('colorbattle_start')
def on_start(data):
    print(f"\n{'='*50}")
    print(f"GAME START!")
    print(f"  {data['speler1_naam']} vs {data['speler2_naam']}")
    print(f"  Rounds: {data['aantal_rondes']}")
    print(f"{'='*50}")

@sio.on('colorbattle_ronde')
def on_ronde(data):
    print(f"\n--- ROUND {data['rondenummer']}/{data['maxronden']} ---")
    print(f"  Player 1 → {data['speler1_kleur']}")
    print(f"  Player 2 → {data['speler2_kleur']}")
    print("  GO! Touch your cones!")

@sio.on('colorbattle_ronde_einde')
def on_ronde_einde(data):
    print(f"\n  Round {data['rondenummer']} Results:")
    print(f"    P1 ({data['speler1_kleur']}): {data['speler1_tijd']}s - {data['speler1_uitkomst']}")
    print(f"    P2 ({data['speler2_kleur']}): {data['speler2_tijd']}s - {data['speler2_uitkomst']}")
    if data['ronde_winnaar']:
        print(f"    Winner: Player {data['ronde_winnaar']}")
    else:
        print(f"    Winner: TIE")

@sio.on('colorbattle_einde')
def on_einde(data):
    print(f"\n{'='*50}")
    print("GAME OVER!")
    print(f"{'='*50}")
    print(f"\n  {data['speler1_naam']}: {data['speler1_correct']} correct, {data['speler1_totaal_tijd']}s total")
    print(f"  {data['speler2_naam']}: {data['speler2_correct']} correct, {data['speler2_totaal_tijd']}s total")
    print()
    if data['winnaar'] == 1:
        print(f"  🏆 WINNER: {data['speler1_naam']}!")
    elif data['winnaar'] == 2:
        print(f"  🏆 WINNER: {data['speler2_naam']}!")
    else:
        print(f"  🤝 IT'S A TIE!")
    print(f"{'='*50}\n")

@sio.on('game_error')
def on_error(data):
    print(f"\n⚠ ERROR: {data}")

@sio.on('device_detection')
def on_detection(data):
    print(f"  [DETECT] {data['kleur']} - {data['afstand']}mm")

def main():
    print("Color Battle Test Script")
    print("=" * 50)

    # Connect to Socket.IO
    print("Connecting to server...")
    try:
        sio.connect(BASE_URL)
    except Exception as e:
        print(f"Failed to connect: {e}")
        print("Make sure the backend is running!")
        return

    time.sleep(0.5)

    # Configure game settings
    settings = {
        "game_id": 5,
        "speler1_naam": "Alice",
        "speler2_naam": "Bob",
        "moeilijkheids_id": 1,
        "snelheid": 10,  # 10 seconds per round
        "ronde_id": 1,
        "rondes": 3,
        "kleuren": ["rood", "blauw"]  # Only red and blue since you have those cones
    }

    print(f"\nSetting up game...")
    print(f"  Players: {settings['speler1_naam']} vs {settings['speler2_naam']}")
    print(f"  Rounds: {settings['rondes']}")
    print(f"  Time limit: {settings['snelheid']}s per round")
    print(f"  Colors: {settings['kleuren']}")

    try:
        resp = requests.post(f"{BASE_URL}/games/colorbattle/instellingen", json=settings)
        if resp.status_code != 200:
            print(f"Failed to set settings: {resp.text}")
            sio.disconnect()
            return
        print("  ✓ Settings saved")
    except Exception as e:
        print(f"Failed to set settings: {e}")
        sio.disconnect()
        return

    # Start the game
    print("\nStarting game...")
    try:
        resp = requests.get(f"{BASE_URL}/games/5/play")
        if resp.status_code != 200:
            print(f"Failed to start: {resp.json()}")
            sio.disconnect()
            return
        print("  ✓ Game started!")
    except Exception as e:
        print(f"Failed to start game: {e}")
        sio.disconnect()
        return

    print("\nListening for events... (Press Ctrl+C to stop)")

    try:
        # Keep running to receive events
        while True:
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("\n\nStopping game...")
        try:
            requests.get(f"{BASE_URL}/games/stop")
            print("Game stopped.")
        except:
            pass

    sio.disconnect()
    print("Done!")

if __name__ == "__main__":
    main()
