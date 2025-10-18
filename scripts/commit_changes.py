#!/usr/bin/env python3
"""
Script per fer commit dels canvis
"""

import os
import sys
import subprocess
from datetime import datetime

def run_command(cmd):
    """Executa una comanda i retorna el resultat"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)

def commit_changes():
    """Fa commit dels canvis"""
    print("📝 Preparant commit...")
    print("=" * 40)
    
    # Verificar estat de git
    success, stdout, stderr = run_command("git status --porcelain")
    if not success:
        print(f"❌ Error verificant git: {stderr}")
        return False
    
    if not stdout.strip():
        print("ℹ️  No hi ha canvis per fer commit")
        return True
    
    print("📋 Canvis detectats:")
    for line in stdout.strip().split('\n'):
        if line:
            print(f"  {line}")
    
    # Afegir tots els fitxers
    print("\n➕ Afegint fitxers...")
    success, stdout, stderr = run_command("git add .")
    if not success:
        print(f"❌ Error afegint fitxers: {stderr}")
        return False
    
    # Fer commit
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    commit_message = f"Organització del codi - {timestamp}\n\n- Creat carpeta scripts/ per tests i debug\n- Creat carpeta old/ per arxius antics\n- Afegit .gitignore\n- Netejat README.md\n- Creat scripts d'utilitat"
    
    print(f"\n💾 Fent commit...")
    success, stdout, stderr = run_command(f'git commit -m "{commit_message}"')
    if not success:
        print(f"❌ Error fent commit: {stderr}")
        return False
    
    print("✅ Commit realitzat correctament")
    
    # Preguntar si fer push
    response = input("\n🚀 Vols fer push al repositori remot? (y/N): ").strip().lower()
    if response in ['y', 'yes', 'sí', 'si']:
        print("📤 Fent push...")
        success, stdout, stderr = run_command("git push")
        if success:
            print("✅ Push realitzat correctament")
        else:
            print(f"❌ Error fent push: {stderr}")
    
    return True

if __name__ == "__main__":
    commit_changes()
