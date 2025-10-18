#!/usr/bin/env python3
"""
Script d'inici per al bot genealògic Kintos75
"""

import os
import sys
import logging
from bot import main

if __name__ == "__main__":
    # Configurar logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Verificar variables d'entorn
    if not os.getenv('TELEGRAM_BOT_TOKEN'):
        print("❌ Error: TELEGRAM_BOT_TOKEN no està configurat")
        print("   Crea un fitxer .env basat en env.example")
        sys.exit(1)
    
    if not os.getenv('GEDCOM_PATH'):
        print("❌ Error: GEDCOM_PATH no està configurat")
        print("   Crea un fitxer .env basat en env.example")
        sys.exit(1)
    
    print("🚀 Iniciant bot genealògic Kintos75...")
    print("   Prem Ctrl+C per aturar el bot")
    print("=" * 40)
    
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 Bot aturat per l'usuari")
    except Exception as e:
        print(f"❌ Error inesperat: {e}")
        sys.exit(1)