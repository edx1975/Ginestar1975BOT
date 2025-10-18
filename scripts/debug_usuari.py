#!/usr/bin/env python3
"""
Debug per verificar l'usuari
"""

from data_manager import DataManager

def debug_usuari():
    """Debug de l'usuari"""
    print("🔍 Debug de l'usuari")
    print("=" * 40)
    
    data_manager = DataManager()
    
    # Llistar tots els usuaris
    usuaris = data_manager.carregar_usuaris()
    print(f"Usuaris registrats: {len(usuaris)}")
    
    for user_id, data in usuaris.items():
        print(f"  - ID: {user_id}")
        print(f"    Persona: {data['persona_id']}")
        print(f"    Nom: {data['nom']}")
        print(f"    Username: {data['username']}")
        print()
    
    # Provar diferents IDs
    ids_prova = ["8062511186", "806251118", "80625111860"]
    
    for id_prova in ids_prova:
        usuari = data_manager.obtenir_usuari(id_prova)
        if usuari:
            print(f"✅ ID {id_prova}: {usuari.nom}")
        else:
            print(f"❌ ID {id_prova}: No trobat")

if __name__ == "__main__":
    debug_usuari()

