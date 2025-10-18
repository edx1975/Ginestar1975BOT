#!/usr/bin/env python3
"""
Test per verificar múltiples relacions
"""

from gedcom_parser import GedcomParser
from graph_builder import GraphBuilder
from models import Persona

def test_multiple_relacions():
    """Test de múltiples relacions"""
    print("🔍 Test de múltiples relacions Eduard -> Montse")
    print("=" * 60)
    
    # Carregar GEDCOM
    parser = GedcomParser("GINESTAR.ged")
    persones = parser.parse()
    
    # Buscar persones
    eduard = None
    montse = None
    
    for id, persona in persones.items():
        if "Eduard" in persona.nom and "LLORENS" in persona.nom:
            eduard = persona
        elif "Montserrat" in persona.nom and "PUJOL" in persona.nom and "ARS" in persona.nom:
            montse = persona
    
    if not all([eduard, montse]):
        print("❌ No s'han trobat les persones")
        return
    
    print(f"✅ Eduard: {eduard.nom} ({eduard.id})")
    print(f"✅ Montse: {montse.nom} ({montse.id})")
    
    # Construir graf
    graph_builder = GraphBuilder()
    graf = graph_builder.construir_graf(persones)
    
    # Trobar tots els camins
    import networkx as nx
    try:
        tots_camins = list(nx.all_simple_paths(graf, eduard.id, montse.id, cutoff=15))
        print(f"\n🔍 Trobats {len(tots_camins)} camins possibles")
        
        for i, cami in enumerate(tots_camins):
            print(f"\n**Camí {i+1}:**")
            print(f"  Distància: {len(cami)-1}")
            print(f"  Camí: {' → '.join([persones[id].nom for id in cami])}")
            
            # Analitzar tipus
            grau, tipus = graph_builder._interpretar_cami(cami)
            print(f"  Tipus: {tipus}")
            print(f"  Grau: {grau}")
            
            # Verificar matrimonis
            matrimonis = 0
            for j in range(len(cami) - 1):
                id1 = cami[j]
                id2 = cami[j + 1]
                if (id2 in persones[id1].conjuges or id1 in persones[id2].conjuges):
                    matrimonis += 1
            print(f"  Matrimonis al camí: {matrimonis}")
            
    except nx.NetworkXNoPath:
        print("❌ No hi ha camins entre les persones")

if __name__ == "__main__":
    test_multiple_relacions()
