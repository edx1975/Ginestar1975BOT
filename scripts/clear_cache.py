#!/usr/bin/env python3
"""
Script per netejar el cache de relacions
"""

import os
import sys
import json

def clear_relations_cache():
    """Neteja el cache de relacions"""
    cache_file = "../data/relacions.json"
    
    if os.path.exists(cache_file):
        # Crear backup
        backup_file = f"{cache_file}.backup"
        with open(cache_file, 'r') as f:
            data = f.read()
        with open(backup_file, 'w') as f:
            f.write(data)
        print(f"✅ Backup creat: {backup_file}")
        
        # Netejar cache
        with open(cache_file, 'w') as f:
            json.dump({}, f)
        print(f"🗑️  Cache netejat: {cache_file}")
    else:
        print(f"ℹ️  No existeix cache: {cache_file}")

if __name__ == "__main__":
    clear_relations_cache()
