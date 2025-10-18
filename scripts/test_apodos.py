#!/usr/bin/env python3
"""
Test del sistema d'apodos i cerca sense accents
"""

from data_manager import DataManager
from utils import normalitzar_text, buscar_persona_per_apodo

def test_normalitzacio():
    """Prova la normalització de text"""
    print("🔤 Test de normalització de text")
    print("=" * 40)
    
    tests = [
        "Eduard",
        "Eduàrd", 
        "Mireia",
        "Míreia",
        "Òscar",
        "Oscar",
        "Sílvia",
        "Silvia",
        "Montserrat",
        "Montserràt"
    ]
    
    for text in tests:
        normalitzat = normalitzar_text(text)
        print(f"'{text}' → '{normalitzat}'")

def test_cerca_apodos():
    """Prova la cerca per apodos"""
    print("\n🔍 Test de cerca per apodos")
    print("=" * 40)
    
    data_manager = DataManager()
    persones = data_manager.carregar_persones()
    
    # Provar diferents cerques
    cerques = [
        "Edu",
        "edu",
        "Eduard",
        "eduard",
        "Montse",
        "montse",
        "Mireia",
        "mireia",
        "Silvia",
        "silvia",
        "Oscar",
        "oscar",
        "Marc",
        "marc",
        "Pepe",
        "pepe"
    ]
    
    for cerca in cerques:
        resultat = buscar_persona_per_apodo(cerca, persones)
        if resultat:
            print(f"✅ '{cerca}' → {resultat['nom']} ({resultat['id']})")
        else:
            print(f"❌ '{cerca}' → No trobat")

def test_llistat_apodos():
    """Prova el llistat d'apodos"""
    print("\n👥 Test de llistat d'apodos")
    print("=" * 40)
    
    data_manager = DataManager()
    apodos_data = data_manager.llistar_apodos_disponibles()
    
    for persona_data in apodos_data:
        nom = persona_data["nom"]
        apodos = persona_data["apodos"]
        print(f"• {nom}: {', '.join(apodos)}")

if __name__ == "__main__":
    test_normalitzacio()
    test_cerca_apodos()
    test_llistat_apodos()

