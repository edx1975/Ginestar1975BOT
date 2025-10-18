#!/usr/bin/env python3
"""
Script per actualitzar el text d'ajuda del bot
"""

import json
import os
import sys

def update_help_text(new_text):
    """Actualitza el text d'ajuda al fitxer JSON"""
    help_file = 'data/help_text.json'
    
    try:
        # Si new_text és un string, dividir-lo en línies
        if isinstance(new_text, str):
            help_lines = new_text.split('\n')
        else:
            help_lines = new_text
        
        # Crear estructura de dades
        help_data = {
            "help_text": help_lines
        }
        
        # Escriure al fitxer
        with open(help_file, 'w', encoding='utf-8') as f:
            json.dump(help_data, f, indent=2, ensure_ascii=False)
        
        print("✅ Text d'ajuda actualitzat correctament")
        return True
        
    except Exception as e:
        print(f"❌ Error actualitzant text d'ajuda: {e}")
        return False

def show_current_help():
    """Mostra el text d'ajuda actual"""
    help_file = 'data/help_text.json'
    
    try:
        if os.path.exists(help_file):
            with open(help_file, 'r', encoding='utf-8') as f:
                help_data = json.load(f)
            
            print("📝 Text d'ajuda actual:")
            print("=" * 50)
            
            # Mostrar help_text (ara és un array de línies)
            help_lines = help_data.get('help_text', [])
            if isinstance(help_lines, list):
                for line in help_lines:
                    print(line)
            else:
                # Fallback si no és un array
                print(help_lines if help_lines else 'No disponible')
            
            print("=" * 50)
        else:
            print("❌ Fitxer d'ajuda no trobat")
            
    except Exception as e:
        print(f"❌ Error llegint text d'ajuda: {e}")

def main():
    """Funció principal"""
    if len(sys.argv) > 1:
        if sys.argv[1] == "--show":
            show_current_help()
        elif sys.argv[1] == "--update":
            if len(sys.argv) > 2:
                new_text = " ".join(sys.argv[2:])
                update_help_text(new_text)
            else:
                print("❌ Has d'especificar el nou text d'ajuda")
                print("Exemple: python update_help.py --update 'Nou text d'ajuda'")
        else:
            print("❌ Opció no reconeguda")
            print("Opcions disponibles:")
            print("  --show    Mostra el text d'ajuda actual")
            print("  --update  Actualitza el text d'ajuda")
    else:
        print("🔧 Script per gestionar el text d'ajuda del bot")
        print("\nOpcions disponibles:")
        print("  --show    Mostra el text d'ajuda actual")
        print("  --update  Actualitza el text d'ajuda")
        print("\nExemples:")
        print("  python update_help.py --show")
        print("  python update_help.py --update 'Nou text d'ajuda'")

if __name__ == "__main__":
    main()
