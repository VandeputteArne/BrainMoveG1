import sqlite3

def create_database():
    conn = sqlite3.connect('brainmove.db')
    cursor = conn.cursor()

    cursor.execute("PRAGMA foreign_keys = ON;")

    # Gebruikers
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Gebruikers (
        GebruikersId INTEGER PRIMARY KEY AUTOINCREMENT,
        Gebruikersnaam TEXT NOT NULL,
        LaatstBewerkt DATETIME DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Games
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Games (
        GameId INTEGER PRIMARY KEY AUTOINCREMENT,
        GameBeschrijving TEXT,
        GameNaam TEXT NOT NULL,
        Eenheid TEXT,
        Tag TEXT,
        LaatstBewerkt DATETIME DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Moeilijkheden
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Moeilijkheden (
        MoeilijkheidsId INTEGER PRIMARY KEY AUTOINCREMENT,
        Moeilijkheid TEXT,
        Snelheid INTEGER,
        GameId INTEGER,
        LaatstBewerkt DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (GameId) REFERENCES Games(GameId)
    );
    """)

    # Rondes
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Rondes (
        RondeId INTEGER PRIMARY KEY AUTOINCREMENT,
        Nummer INTEGER,
        GameId INTEGER,
        LaatstBewerkt DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (GameId) REFERENCES Games(GameId)
    );
    """)

    # Trainingen
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Trainingen (
        TrainingsId INTEGER PRIMARY KEY AUTOINCREMENT,
        Start DATETIME DEFAULT CURRENT_TIMESTAMP,
        AantalKleuren INTEGER,
        GebruikersId INTEGER,
        RondeId INTEGER,
        MoeilijkheidsId INTEGER,
        GameId INTEGER,
        FOREIGN KEY (GebruikersId) REFERENCES Gebruikers(GebruikersId),
        FOREIGN KEY (RondeId) REFERENCES Rondes(RondeId),
        FOREIGN KEY (MoeilijkheidsId) REFERENCES Moeilijkheden(MoeilijkheidsId),
        FOREIGN KEY (GameId) REFERENCES Games(GameId)
    );
    """)

    # RondeWaarden
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS RondeWaarden (
        RondeWaardeId INTEGER PRIMARY KEY AUTOINCREMENT,
        TrainingsId INTEGER,
        RondeNummer INTEGER,
        Waarde TEXT,
        Uitkomst TEXT,
        FOREIGN KEY (TrainingsId) REFERENCES Trainingen(TrainingsId)
    );
    """)

    print("Database succesvol aangemaakt met DATETIME types!")

    conn.commit()
    conn.close()

if __name__ == "__main__":
    create_database()