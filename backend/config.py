import os

# Absoluut pad naar je BrainMove database
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_PATH = os.path.join(BASE_DIR, "data", "brainmove.db")

# Optionele settings
DEBUG = True
DB_TIMEOUT = 30  # seconden

# Voor testing: print het pad (verwijder later)
print(f"Database pad: {DATABASE_PATH}")
