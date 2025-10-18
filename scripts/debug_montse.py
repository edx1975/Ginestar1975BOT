#!/usr/bin/env python3
"""
Debug específic per la relació amb Montse
"""

from gedcom_parser import GedcomParser
from graph_builder import GraphBuilder

def debug_montse():
    """Debug de la relació amb Montse"""
    print("🔍 Debug relació Eduard -> Montse")
    print("=" * 50)
    
    # Carregar GEDCOM
    parser = GedcomParser("GINESTAR.ged")
    persones = parser.parse()
    
    # Buscar persones
    eduard = None
    montse = None
    
    for id, persona in persones.items():
        if "Eduard" in persona.nom and "LLORENS" in persona.nom:
            eduard = persona
            print(f"✅ Eduard: {persona.nom} ({id})")
        elif "Montserrat" in persona.nom and "PUJOL" in persona.nom and "ARS" in persona.nom:
            montse = persona
            print(f"✅ Montse: {persona.nom} ({id})")
    
    if not all([eduard, montse]):
        print("❌ No s'han trobat les persones")
        return
    
    # Construir graf
    graph_builder = GraphBuilder()
    graf = graph_builder.construir_graf(persones)
    
    # Calcular relació
    relacio = graph_builder.calcular_relacio(eduard.id, montse.id)
    
    if relacio:
        print(f"\n🔍 Relació calculada:")
        print(f"  Tipus: {relacio.tipus}")
        print(f"  Grau: {relacio.grau}")
        print(f"  Distància: {relacio.distancia}")
        print(f"  Camí: {' → '.join([persones[id].nom for id in relacio.cami])}")
        
        # Verificar matrimonis al camí
        print(f"\n🔍 Verificant matrimonis al camí:")
        matrimonis = 0
        for i in range(len(relacio.cami) - 1):
            id1 = relacio.cami[i]
            id2 = relacio.cami[i + 1]
            persona1 = persones[id1]
            persona2 = persones[id2]
            
            if (id2 in persona1.conjuges or id1 in persona2.conjuges):
                matrimonis += 1
                print(f"  ✅ Matrimoni: {persona1.nom} = {persona2.nom}")
            else:
                print(f"  ❌ No matrimoni: {persona1.nom} → {persona2.nom}")
        
        print(f"\n📊 Total matrimonis al camí: {matrimonis}")
        print(f"📊 Tipus final: {'no_sanguinia' if matrimonis > 0 else 'sanguinia'}")
    else:
        print("❌ No s'ha pogut calcular la relació")

if __name__ == "__main__":
    debug_montse()
