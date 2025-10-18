#!/usr/bin/env python3
"""
Debug per verificar matrimonis al GEDCOM
"""

from gedcom_parser import GedcomParser
from graph_builder import GraphBuilder
from models import Persona

def debug_matrimonis():
    """Debug de matrimonis al GEDCOM"""
    print("🔍 Debug de matrimonis al GEDCOM")
    print("=" * 50)
    
    # Carregar GEDCOM
    parser = GedcomParser("GINESTAR.ged")
    persones = parser.parse()
    
    # Buscar persones específiques
    tauleret = None
    mireia = None
    eduard = None
    
    for id, persona in persones.items():
        if "Tauleret" in persona.nom and "FIGUERAS" in persona.nom:
            tauleret = persona
            print(f"✅ Tauleret trobat: {persona.nom} ({id})")
        elif "Mireia" in persona.nom and "SEGARRA" in persona.nom:
            mireia = persona
            print(f"✅ Mireia trobat: {persona.nom} ({id})")
        elif "Eduard" in persona.nom and "LLORENS" in persona.nom:
            eduard = persona
            print(f"✅ Eduard trobat: {persona.nom} ({id})")
    
    if not all([tauleret, mireia, eduard]):
        print("❌ No s'han trobat totes les persones")
        return
    
    # Verificar matrimonis
    print(f"\n🔍 Matrimonis de Tauleret: {tauleret.conjuges}")
    print(f"🔍 Matrimonis de Mireia: {mireia.conjuges}")
    print(f"🔍 Matrimonis de Eduard: {eduard.conjuges}")
    
    # Construir graf
    graph_builder = GraphBuilder()
    graf = graph_builder.construir_graf(persones)
    
    # Provar relacions
    print(f"\n🔍 Provar relació Eduard -> Tauleret")
    relacio1 = graph_builder.calcular_relacio(eduard.id, tauleret.id)
    if relacio1:
        print(f"  Tipus: {relacio1.tipus}")
        print(f"  Camí: {' → '.join([persones[id].nom for id in relacio1.cami])}")
        
        # Verificar matrimonis al camí
        matrimonis = 0
        for i in range(len(relacio1.cami) - 1):
            id1 = relacio1.cami[i]
            id2 = relacio1.cami[i + 1]
            if (id2 in persones[id1].conjuges or id1 in persones[id2].conjuges):
                matrimonis += 1
                print(f"    Matrimoni: {persones[id1].nom} = {persones[id2].nom}")
        print(f"  Total matrimonis al camí: {matrimonis}")
    
    print(f"\n🔍 Provar relació Eduard -> Mireia")
    relacio2 = graph_builder.calcular_relacio(eduard.id, mireia.id)
    if relacio2:
        print(f"  Tipus: {relacio2.tipus}")
        print(f"  Camí: {' → '.join([persones[id].nom for id in relacio2.cami])}")
        
        # Verificar matrimonis al camí
        matrimonis = 0
        for i in range(len(relacio2.cami) - 1):
            id1 = relacio2.cami[i]
            id2 = relacio2.cami[i + 1]
            if (id2 in persones[id1].conjuges or id1 in persones[id2].conjuges):
                matrimonis += 1
                print(f"    Matrimoni: {persones[id1].nom} = {persones[id2].nom}")
        print(f"  Total matrimonis al camí: {matrimonis}")

if __name__ == "__main__":
    debug_matrimonis()

