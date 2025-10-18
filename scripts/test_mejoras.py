#!/usr/bin/env python3
"""
Test de les millores en la notació i detecció de relacions
"""

from models import Persona, Relacio
from graph_builder import GraphBuilder

def test_notacio_simplificada():
    """Prova la notació simplificada"""
    print("🧬 Test de notació simplificada")
    print("=" * 50)
    
    # Crear persones d'exemple
    persones = {
        "I001": Persona("I001", "Eduard", "M"),
        "I002": Persona("I002", "Montserrat", "F"),
        "I003": Persona("I003", "Esteve", "M"),
        "I004": Persona("I004", "Filomena", "F"),
        "I005": Persona("I005", "Roseta", "F"),
        "I006": Persona("I006", "Ramon", "M"),
        "I007": Persona("I007", "Mireia", "F")
    }
    
    # Establir relacions
    persones["I001"].pares.add("I002")
    persones["I002"].fills.add("I001")
    
    persones["I002"].pares.add("I003")
    persones["I003"].fills.add("I002")
    
    persones["I003"].pares.add("I004")
    persones["I004"].fills.add("I003")
    
    persones["I004"].fills.add("I005")
    persones["I005"].pares.add("I004")
    
    persones["I005"].conjuges.add("I006")
    persones["I006"].conjuges.add("I005")
    
    persones["I006"].fills.add("I007")
    persones["I007"].pares.add("I006")
    
    # Construir graf
    graph_builder = GraphBuilder()
    graph_builder.construir_graf(persones)
    
    # Provar relació llarga
    relacio = graph_builder.calcular_relacio("I001", "I007")
    
    if relacio:
        print(f"Relació: {relacio.grau}")
        print(f"Tipus: {relacio.tipus}")
        print(f"Distància: {relacio.distancia}")
        print(f"Camí original: {' → '.join([persones[id].nom for id in relacio.cami])}")
        
        # Simular formatat simplificat
        parts = []
        for i in range(len(relacio.cami) - 1):
            id1 = relacio.cami[i]
            id2 = relacio.cami[i + 1]
            persona1 = persones[id1]
            persona2 = persones[id2]
            
            if id2 in persona1.pares:
                parts.append(f"{persona1.nom} < {persona2.nom}")
            elif id1 in persona2.pares:
                parts.append(f"{persona1.nom} > {persona2.nom}")
            elif id2 in persona1.conjuges or id1 in persona2.conjuges:
                parts.append(f"{persona1.nom} = {persona2.nom}")
            else:
                parts.append(f"{persona1.nom} → {persona2.nom}")
        
        cami_formatat = " → ".join(parts)
        print(f"Camí formatat: {cami_formatat}")
        
        # Simplificar
        import re
        cami_simplificat = re.sub(r'([^→]+) → \1', r'\1', cami_formatat)
        print(f"Camí simplificat: {cami_simplificat}")
        
        if len(cami_simplificat) > 100:
            elements = cami_simplificat.split(' → ')
            if len(elements) > 4:
                primer = elements[0]
                ultim = elements[-1]
                print(f"Camí resumit: {primer} ... {ultim}")

def test_deteccio_tipus():
    """Prova la detecció correcta del tipus de relació"""
    print("\n🔍 Test de detecció de tipus de relació")
    print("=" * 50)
    
    # Crear persones d'exemple
    persones = {
        "I001": Persona("I001", "Eduard", "M"),
        "I002": Persona("I002", "Montserrat", "F"),
        "I003": Persona("I003", "Ramon", "M"),
        "I004": Persona("I004", "Mireia", "F")
    }
    
    # Establir relacions
    persones["I001"].pares.add("I002")
    persones["I002"].fills.add("I001")
    
    persones["I002"].conjuges.add("I003")
    persones["I003"].conjuges.add("I002")
    
    persones["I003"].fills.add("I004")
    persones["I004"].pares.add("I003")
    
    # Construir graf
    graph_builder = GraphBuilder()
    graph_builder.construir_graf(persones)
    
    # Provar relació amb matrimoni al mig
    relacio = graph_builder.calcular_relacio("I001", "I004")
    
    if relacio:
        print(f"Relació: {relacio.grau}")
        print(f"Tipus: {relacio.tipus} (hauria de ser 'no_sanguinia' perquè hi ha matrimoni)")
        print(f"Camí: {' → '.join([persones[id].nom for id in relacio.cami])}")

if __name__ == "__main__":
    test_notacio_simplificada()
    test_deteccio_tipus()

