import sqlite3
import os

def add_color_sprint():
    db_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'brainmove.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute('''
    INSERT INTO Games (GameId, GameBeschrijving, GameNaam, Eenheid, Tag) 
    VALUES (?, ?, ?, ?, ?)
    ''', (
        1,
        'Blijf scherp! Zodra een kleur op het scherm verschijnt, moet je onmiddellijk in actie komen en naar de bijpassende kleur bewegen. Elke seconde telt. Verbeter je reactietijd, versla je eigen records en word steeds sneller.',
        'Color Sprint',
        's',
        'reactiesnelheid'
    ))

    conn.commit()
    print('✓ Game "Color Sprint" succesvol toegevoegd met ID 1')

    moeilijkheden = [
        ('Gemakkelijk', 10, 1),
        ('Gemiddeld', 5, 1),
        ('Moeilijk', 3, 1)
    ]
    
    for moeilijkheid, snelheid, game_id in moeilijkheden:
        cursor.execute('''
        INSERT INTO Moeilijkheden (Moeilijkheid, Snelheid, GameId) 
        VALUES (?, ?, ?)
        ''', (moeilijkheid, snelheid, game_id))
    
    conn.commit()
    print('✓ Moeilijkheden toegevoegd (Gemakkelijk, Gemiddeld, Moeilijk)')

    rondes = [5, 10, 15]
    
    for nummer in rondes:
        cursor.execute('''
        INSERT INTO Rondes (Nummer, GameId) 
        VALUES (?, ?)
        ''', (nummer, 1))
    
    conn.commit()
    print('✓ Rondes toegevoegd (5, 10, 15)')

    cursor.execute('SELECT * FROM Games WHERE GameId = 1')
    row = cursor.fetchone()
    print(f'\nOpgeslagen Game:')
    print(f'  GameId: {row[0]}')
    print(f'  GameNaam: {row[2]}')
    print(f'  Eenheid: {row[3]}')
    print(f'  Tag: {row[4]}')
    print(f'  LaatstBewerkt: {row[5]}')

    cursor.execute('SELECT * FROM Moeilijkheden WHERE GameId = 1')
    print(f'\nOpgeslagen Moeilijkheden:')
    for row in cursor.fetchall():
        print(f'  {row[1]} - Snelheid: {row[2]} (LaatstBewerkt: {row[4]})')

    cursor.execute('SELECT * FROM Rondes WHERE GameId = 1')
    print(f'\nOpgeslagen Rondes:')
    for row in cursor.fetchall():
        print(f'  Nummer: {row[1]} (LaatstBewerkt: {row[3]})')

    conn.close()

def add_memory_game():
    db_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'brainmove.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute('''
    INSERT INTO Games (GameId, GameBeschrijving, GameNaam, Eenheid, Tag) 
    VALUES (?, ?, ?, ?, ?)
    ''', (
        2,
        'Blijf scherp met Memory! Kleuren verschijnen op het scherm – onthoud de volgorde perfect en herhaal ze daarna zo snel mogelijk. Elke ronde wordt uitdagender. Train je geheugen, versla je records en word een geheugenkampioen.',
        'Memory',
        'kleuren',
        'geheugen'
    ))

    conn.commit()
    print('✓ Game "Memory" succesvol toegevoegd met ID 2')

    moeilijkheden = [
        ('Gemakkelijk', 3, 2),
        ('Gemiddeld', 2, 2),
        ('Moeilijk', 1, 2)
    ]
    
    for moeilijkheid, snelheid, game_id in moeilijkheden:
        cursor.execute('''
        INSERT INTO Moeilijkheden (Moeilijkheid, Snelheid, GameId) 
        VALUES (?, ?, ?)
        ''', (moeilijkheid, snelheid, game_id))
    
    conn.commit()
    print('✓ Moeilijkheden toegevoegd (Gemakkelijk, Gemiddeld, Moeilijk)')

    rondes = [5, 10, 15]
    
    for nummer in rondes:
        cursor.execute('''
        INSERT INTO Rondes (Nummer, GameId) 
        VALUES (?, ?)
        ''', (nummer, 2))
    
    conn.commit()
    print('✓ Rondes toegevoegd (5, 10, 15)')

    cursor.execute('SELECT * FROM Games WHERE GameId = 2')
    row = cursor.fetchone()
    print(f'\nOpgeslagen Game:')
    print(f'  GameId: {row[0]}')
    print(f'  GameNaam: {row[2]}')
    print(f'  Eenheid: {row[3]}')
    print(f'  Tag: {row[4]}')
    print(f'  LaatstBewerkt: {row[5]}')

    cursor.execute('SELECT * FROM Moeilijkheden WHERE GameId = 2')
    print(f'\nOpgeslagen Moeilijkheden:')
    for row in cursor.fetchall():
        print(f'  {row[1]} - Snelheid: {row[2]} (LaatstBewerkt: {row[4]})')

    cursor.execute('SELECT * FROM Rondes WHERE GameId = 2')
    print(f'\nOpgeslagen Rondes:')
    for row in cursor.fetchall():
        print(f'  Nummer: {row[1]} (LaatstBewerkt: {row[3]})')

    conn.close()

def add_number_match():
    db_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'brainmove.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute('''
    INSERT INTO Games (GameId, GameBeschrijving, GameNaam, Eenheid, Tag, LaatstBewerkt) 
    VALUES (?, ?, ?, ?, ?, ?)
    ''', (
        3,
        'Blijf gefocust! Eerst zie je welke kleur bij welk potje hoort, bijvoorbeeld rood is 1, blauw 2, groen 3, geel 4. Onthoud de koppeling en zoek daarna razendsnel het juiste potje op. Elke seconde telt. Verbeter je geheugen, versla je records en word steeds sneller.',
        'Number Match',
        's',
        'geheugen',
        '2026-01-22'
    ))

    conn.commit()
    print('✓ Game "Number Match" succesvol toegevoegd met ID 3')

    moeilijkheden = [
        ('Gemakkelijk', 5, 3),
        ('Gemiddeld', 3, 3),
        ('Moeilijk', 2, 3)
    ]
    
    for moeilijkheid, snelheid, game_id in moeilijkheden:
        cursor.execute('''
        INSERT INTO Moeilijkheden (Moeilijkheid, Snelheid, GameId) 
        VALUES (?, ?, ?)
        ''', (moeilijkheid, snelheid, game_id))
    
    conn.commit()
    print('✓ Moeilijkheden toegevoegd (Gemakkelijk, Gemiddeld, Moeilijk)')

    rondes = [5, 10, 15]
    
    for nummer in rondes:
        cursor.execute('''
        INSERT INTO Rondes (Nummer, GameId) 
        VALUES (?, ?)
        ''', (nummer, 3))
    
    conn.commit()
    print('✓ Rondes toegevoegd (5, 10, 15)')

    cursor.execute('SELECT * FROM Games WHERE GameId = 3')
    row = cursor.fetchone()
    print(f'\nOpgeslagen Game:')
    print(f'  GameId: {row[0]}')
    print(f'  GameNaam: {row[2]}')
    print(f'  Eenheid: {row[3]}')
    print(f'  Tag: {row[4]}')
    print(f'  LaatstBewerkt: {row[5]}')

    cursor.execute('SELECT * FROM Moeilijkheden WHERE GameId = 3')
    print(f'\nOpgeslagen Moeilijkheden:')
    for row in cursor.fetchall():
        print(f'  {row[1]} - Snelheid: {row[2]} (LaatstBewerkt: {row[4]})')

    cursor.execute('SELECT * FROM Rondes WHERE GameId = 3')
    print(f'\nOpgeslagen Rondes:')
    for row in cursor.fetchall():
        print(f'  Nummer: {row[1]} (LaatstBewerkt: {row[3]})')

    conn.close()

def add_falling_color():
    db_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'brainmove.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute('''
    INSERT INTO Games (GameId, GameBeschrijving, GameNaam, Eenheid, Tag, LaatstBewerkt) 
    VALUES (?, ?, ?, ?, ?, ?)
    ''', (
        4,
        'Blijf alert! Een kleur verschijnt en valt van 100% naar 0%. Raak het juiste potje aan voordat de kleur de grond raakt. Als de kleur op 0% komt of je raakt het verkeerde potje aan, ben je af. Elke seconde telt. Verbeter je reactiesnelheid en word de beste.',
        'Falling Colors',
        's',
        'reactiesnelheid',
        '2026-01-23'
    ))

    conn.commit()
    print('✓ Game "Falling Colors" succesvol toegevoegd met ID 4')

    moeilijkheden = [
        ('Gemakkelijk', 5, 4),
        ('Gemiddeld', 3, 4),
        ('Moeilijk', 2, 4)
    ]
    
    for moeilijkheid, snelheid, game_id in moeilijkheden:
        cursor.execute('''
        INSERT INTO Moeilijkheden (Moeilijkheid, Snelheid, GameId) 
        VALUES (?, ?, ?)
        ''', (moeilijkheid, snelheid, game_id))
    
    conn.commit()
    print('✓ Moeilijkheden toegevoegd (Gemakkelijk, Gemiddeld, Moeilijk)')

    rondes = [5, 10, 15]
    
    for nummer in rondes:
        cursor.execute('''
        INSERT INTO Rondes (Nummer, GameId) 
        VALUES (?, ?)
        ''', (nummer, 4))
    
    conn.commit()
    print('✓ Rondes toegevoegd (5, 10, 15)')

    cursor.execute('SELECT * FROM Games WHERE GameId = 4')
    row = cursor.fetchone()
    print(f'\nOpgeslagen Game:')
    print(f'  GameId: {row[0]}')
    print(f'  GameNaam: {row[2]}')
    print(f'  Eenheid: {row[3]}')
    print(f'  Tag: {row[4]}')
    print(f'  LaatstBewerkt: {row[5]}')

    cursor.execute('SELECT * FROM Moeilijkheden WHERE GameId = 4')
    print(f'\nOpgeslagen Moeilijkheden:')
    for row in cursor.fetchall():
        print(f'  {row[1]} - Snelheid: {row[2]} (LaatstBewerkt: {row[4]})')

    cursor.execute('SELECT * FROM Rondes WHERE GameId = 4')
    print(f'\nOpgeslagen Rondes:')
    for row in cursor.fetchall():
        print(f'  Nummer: {row[1]} (LaatstBewerkt: {row[3]})')

    conn.close()

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "memory":
        add_memory_game()
    elif len(sys.argv) > 1 and sys.argv[1] == "number":
        add_number_match()
    elif len(sys.argv) > 1 and sys.argv[1] == "falling":
        add_falling_color()
    else:
        add_color_sprint()