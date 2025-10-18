"""
Configuració del bot genealògic
"""

import os
from dotenv import load_dotenv

# Carregar variables d'entorn
load_dotenv()

# Configuració del bot
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', 'your_bot_token_here')
GEDCOM_PATH = 'GINESTAR.ged'

# Configuració de dades
DATA_DIR = 'data'
PERSONES_FILE = os.path.join(DATA_DIR, 'persones.json')
USERS_FILE = os.path.join(DATA_DIR, 'users.json')
RELACIONS_FILE = os.path.join(DATA_DIR, 'relacions.json')

# Configuració de logging
LOG_LEVEL = 'INFO'

