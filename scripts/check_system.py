#!/usr/bin/env python3
"""
Script per verificar l'estat del sistema
"""

import os
import sys
import json

def check_system():
    """Verifica l'estat del sistema"""
    print("🔍 Verificant sistema Kintos75...")
    print("=" * 40)
    
    # Verificar fitxers principals
    files_to_check = [
        "../bot.py",
        "../models.py", 
        "../gedcom_parser.py",
        "../graph_builder.py",
        "../data_manager.py",
        "../kinship_weights.py",
        "../utils.py",
        "../config.py"
    ]
    
    print("📁 Fitxers principals:")
    for file_path in files_to_check:
        if os.path.exists(file_path):
            print(f"  ✅ {file_path}")
        else:
            print(f"  ❌ {file_path}")
    
    # Verificar dades
    print("\n📊 Dades:")
    data_files = [
        "../data/persones.json",
        "../data/users.json", 
        "../data/relacions.json"
    ]
    
    for file_path in data_files:
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                print(f"  ✅ {file_path} ({len(data)} entrades)")
            except json.JSONDecodeError:
                print(f"  ⚠️  {file_path} (JSON invàlid)")
        else:
            print(f"  ❌ {file_path}")
    
    # Verificar GEDCOM
    print("\n📋 GEDCOM:")
    gedcom_path = "../GINESTAR.ged"
    if os.path.exists(gedcom_path):
        size = os.path.getsize(gedcom_path)
        print(f"  ✅ {gedcom_path} ({size:,} bytes)")
    else:
        print(f"  ❌ {gedcom_path}")
    
    # Verificar configuració
    print("\n⚙️  Configuració:")
    try:
        from config import TELEGRAM_BOT_TOKEN, GEDCOM_PATH
        if TELEGRAM_BOT_TOKEN and TELEGRAM_BOT_TOKEN != 'your_bot_token_here':
            print(f"  ✅ TELEGRAM_BOT_TOKEN configurat")
        else:
            print(f"  ❌ TELEGRAM_BOT_TOKEN no configurat")
        
        if os.path.exists(GEDCOM_PATH):
            print(f"  ✅ GEDCOM_PATH: {GEDCOM_PATH}")
        else:
            print(f"  ❌ GEDCOM_PATH: {GEDCOM_PATH} (no existeix)")
    except ImportError as e:
        print(f"  ❌ Error important config: {e}")

if __name__ == "__main__":
    check_system()
