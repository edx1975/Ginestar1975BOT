"""
Script de prova per verificar el funcionament del sistema genealògic
"""

import os
import sys
from gedcom_parser import GedcomParser
from graph_builder import GraphBuilder
from data_manager import DataManager


def test_gedcom_parser():
    """Prova el parser del GEDCOM"""
    print("🧬 Provant parser del GEDCOM...")
    
    gedcom_path = "GINESTAR.ged"
    if not os.path.exists(gedcom_path):
        print(f"❌ Fitxer GEDCOM no trobat: {gedcom_path}")
        return False
    
    parser = GedcomParser(gedcom_path)
    persones = parser.parse()
    
    print(f"✅ Parser completat. Trobades {len(persones)} persones")
    
    # Mostrar algunes persones
    for i, (id, persona) in enumerate(list(persones.items())[:5]):
        print(f"  {i+1}. {persona.nom} ({id})")
    
    return True


def test_data_manager():
    """Prova el gestor de dades"""
    print("\n📊 Provant gestor de dades...")
    
    data_manager = DataManager()
    
    # Provar carregar persones
    persones = data_manager.carregar_persones()
    print(f"✅ Carregades {len(persones)} persones des de JSON")
    
    # Provar buscar persona
    persona = data_manager.buscar_persona_per_nom("Eduard")
    if persona:
        print(f"✅ Persona trobada: {persona['nom']} ({persona['id']})")
    else:
        print("❌ No s'ha trobat Eduard")
    
    return True


def test_graph_builder():
    """Prova el constructor de graf"""
    print("\n🕸️ Provant constructor de graf...")
    
    # Carregar dades
    data_manager = DataManager()
    persones_data = data_manager.carregar_persones()
    
    # Convertir a objectes Persona
    from models import Persona
    persones = {}
    for id, data in persones_data.items():
        persones[id] = Persona(
            id=id,
            nom=data["nom"],
            sexe=data.get("sexe"),
            naixement=data.get("naixement"),
            defuncio=data.get("defuncio")
        )
    
    # Construir graf
    graph_builder = GraphBuilder()
    graf = graph_builder.construir_graf(persones)
    
    print(f"✅ Graf construït amb {graf.number_of_nodes()} nodes i {graf.number_of_edges()} arestes")
    
    # Provar càlcul de relació
    if len(persones) >= 2:
        ids = list(persones.keys())
        relacio = graph_builder.calcular_relacio(ids[0], ids[1])
        if relacio:
            print(f"✅ Relació calculada: {relacio}")
        else:
            print("ℹ️ No s'ha trobat relació entre les primeres dues persones")
    
    return True


def test_relation_calculation():
    """Prova el càlcul de relacions"""
    print("\n🔗 Provant càlcul de relacions...")
    
    # Carregar dades
    data_manager = DataManager()
    persones_data = data_manager.carregar_persones()
    
    # Convertir a objectes Persona
    from models import Persona
    persones = {}
    for id, data in persones_data.items():
        persones[id] = Persona(
            id=id,
            nom=data["nom"],
            sexe=data.get("sexe"),
            naixement=data.get("naixement"),
            defuncio=data.get("defuncio")
        )
    
    # Construir graf
    graph_builder = GraphBuilder()
    graf = graph_builder.construir_graf(persones)
    
    # Provar diferents relacions
    ids = list(persones.keys())
    if len(ids) >= 2:
        for i in range(min(3, len(ids))):
            for j in range(i+1, min(i+3, len(ids))):
                relacio = graph_builder.calcular_relacio(ids[i], ids[j])
                if relacio:
                    persona1 = persones[ids[i]].nom
                    persona2 = persones[ids[j]].nom
                    # Simular formatat de camí
                    cami_simple = " → ".join([persones[id].nom for id in relacio.cami])
                    print(f"  {persona1} ↔ {persona2}: {relacio.grau} ({relacio.tipus})")
                    print(f"    Camí: {cami_simple}")
    
    return True


def main():
    """Funció principal de prova"""
    print("🚀 Iniciant proves del sistema genealògic...\n")
    
    tests = [
        test_gedcom_parser,
        test_data_manager,
        test_graph_builder,
        test_relation_calculation
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Error en prova: {e}")
    
    print(f"\n📊 Resultats: {passed}/{total} proves passades")
    
    if passed == total:
        print("🎉 Totes les proves han passat! El sistema està llest.")
        return True
    else:
        print("⚠️ Algunes proves han fallat. Revisa els errors.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
