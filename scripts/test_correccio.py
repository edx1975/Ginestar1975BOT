#!/usr/bin/env python3
"""
Test de la correcció de detecció de relacions no sanguínies
"""

from models import Persona, Relacio
from graph_builder import GraphBuilder

def test_deteccio_matrimonis():
    """Prova la detecció correcta de matrimonis al camí"""
    print("🔍 Test de detecció de matrimonis al camí")
    print("=" * 50)
    
    # Crear persones d'exemple
    persones = {
        "I001": Persona("I001", "Eduard", "M"),
        "I002": Persona("I002", "Montserrat", "F"),
        "I003": Persona("I003", "Esteve", "M"),
        "I004": Persona("I004", "Filomena", "F"),
        "I005": Persona("I005", "Roseta", "F"),
        "I006": Persona("I006", "Ramon", "M"),
        "I007": Persona("I007", "Manuel", "M"),
        "I008": Persona("I008", "Francisco", "M"),
        "I009": Persona("I009", "Paquita", "F"),
        "I010": Persona("I010", "Carlos", "M"),
        "I011": Persona("I011", "Mireia", "F")
    }
    
    # Establir relacions (simulant el camí del GEDCOM)
    # Eduard < Montserrat < Esteve < Filomena > Roseta = Ramon < Manuel < Francisco > Paquita > Carlos = Mireia
    
    # Relacions pare-fill
    persones["I001"].pares.add("I002")
    persones["I002"].fills.add("I001")
    
    persones["I002"].pares.add("I003")
    persones["I003"].fills.add("I002")
    
    persones["I003"].pares.add("I004")
    persones["I004"].fills.add("I003")
    
    persones["I004"].fills.add("I005")
    persones["I005"].pares.add("I004")
    
    persones["I006"].pares.add("I007")
    persones["I007"].fills.add("I006")
    
    persones["I007"].pares.add("I008")
    persones["I008"].fills.add("I007")
    
    persones["I008"].fills.add("I009")
    persones["I009"].pares.add("I008")
    
    persones["I009"].fills.add("I010")
    persones["I010"].pares.add("I009")
    
    # Matrimonis
    persones["I005"].conjuges.add("I006")
    persones["I006"].conjuges.add("I005")
    
    persones["I010"].conjuges.add("I011")
    persones["I011"].conjuges.add("I010")
    
    # Construir graf
    graph_builder = GraphBuilder()
    graph_builder.construir_graf(persones)
    
    # Provar relació llarga amb matrimonis
    relacio = graph_builder.calcular_relacio("I001", "I011")
    
    if relacio:
        print(f"Relació: {relacio.grau}")
        print(f"Tipus: {relacio.tipus} (hauria de ser 'no_sanguinia' perquè hi ha matrimonis)")
        print(f"Distància: {relacio.distancia}")
        print(f"Camí: {' → '.join([persones[id].nom for id in relacio.cami])}")
        
        # Verificar matrimonis al camí
        matrimonis = 0
        for i in range(len(relacio.cami) - 1):
            id1 = relacio.cami[i]
            id2 = relacio.cami[i + 1]
            if (id2 in persones[id1].conjuges or id1 in persones[id2].conjuges):
                matrimonis += 1
                print(f"  Matrimoni trobat: {persones[id1].nom} = {persones[id2].nom}")
        
        print(f"Total matrimonis al camí: {matrimonis}")
        
        if matrimonis > 0 and relacio.tipus == "no_sanguinia":
            print("✅ CORRECTE: Relació detectada com no sanguínia")
        elif matrimonis > 0 and relacio.tipus == "sanguinia":
            print("❌ ERROR: Relació detectada com sanguínia però hi ha matrimonis")
        else:
            print("ℹ️  Relació sanguínia sense matrimonis")

if __name__ == "__main__":
    test_deteccio_matrimonis()

