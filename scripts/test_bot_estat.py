#!/usr/bin/env python3
"""
Test ràpid per verificar l'estat del bot
"""

from data_manager import DataManager
from gedcom_parser import GedcomParser
from graph_builder import GraphBuilder

def test_estat_bot():
    """Verifica l'estat del bot"""
    print("🔍 Verificant estat del bot...")
    
    # 1. Verificar dades JSON
    data_manager = DataManager()
    persones = data_manager.carregar_persones()
    print(f"✅ Persones carregades: {len(persones)}")
    
    usuaris = data_manager.carregar_usuaris()
    print(f"✅ Usuaris registrats: {len(usuaris)}")
    
    for user_id, data in usuaris.items():
        print(f"  - Usuari {user_id}: {data['nom']} ({data['persona_id']})")
    
    # 2. Verificar GEDCOM
    try:
        parser = GedcomParser("GINESTAR.ged")
        persones_gedcom = parser.parse()
        print(f"✅ GEDCOM carregat: {len(persones_gedcom)} persones")
    except Exception as e:
        print(f"❌ Error GEDCOM: {e}")
        return False
    
    # 3. Verificar graf (convertir JSON a objectes Persona)
    try:
        from models import Persona
        persones_obj = {}
        for id, data in persones.items():
            persones_obj[id] = Persona(
                id=id,
                nom=data["nom"],
                sexe=data.get("sexe"),
                naixement=data.get("naixement"),
                defuncio=data.get("defuncio")
            )
        
        graph_builder = GraphBuilder()
        graf = graph_builder.construir_graf(persones_obj)
        print(f"✅ Graf construït: {graf.number_of_nodes()} nodes, {graf.number_of_edges()} arestes")
    except Exception as e:
        print(f"❌ Error graf: {e}")
        return False
    
    # 4. Provar cerca
    try:
        resultat = data_manager.buscar_persona_per_nom("Edu")
        if resultat:
            print(f"✅ Cerca funciona: 'Edu' → {resultat['nom']}")
        else:
            print("❌ Cerca no funciona")
    except Exception as e:
        print(f"❌ Error cerca: {e}")
        return False
    
    print("\n🎉 Bot llest per funcionar!")
    return True

if __name__ == "__main__":
    test_estat_bot()
