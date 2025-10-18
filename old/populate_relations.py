#!/usr/bin/env python3
"""
Script per omplir l'arxiu de relacions amb totes les combinacions entre els 11 Kintos
"""

import json
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data_manager import DataManager
from gedcom_parser import GedcomParser
from graph_builder import GraphBuilder
from kinship_weights import prioritize_relationships

def main():
    print("🚀 Iniciant càlcul de relacions per tots els Kintos...")
    
    # Carregar dades
    dm = DataManager()
    gp = GedcomParser('GINESTAR.ged')
    persones = gp.parse()
    gb = GraphBuilder()
    gb.construir_graf(persones)
    
    # Llistar els 11 Kintos
    kintos_ids = [
        "I1843",  # Eduard Llorens Pujol
        "I2042",  # Òscar Pino Vandellòs
        "I3099",  # Segallet Marc Ars Borràs
        "I3004",  # Josep Maria Taule Figueras
        "I2465",  # Marta Pellissa Pujol
        "I1986",  # Mireia Bladé Montagut
        "I2217",  # Mireia Segarra Vandellòs
        "I2661",  # Sílvia Ars Poll
        "I2599",  # Montserrat Pujol Ars
        "I2994",  # Jaume Florenza Álvarez
        "I1933"   # David Usach Garcia
    ]
    
    relacions = {}
    total_combinacions = len(kintos_ids) * (len(kintos_ids) - 1)
    comptador = 0
    
    print(f"📊 Calculant {total_combinacions} combinacions de relacions...")
    
    for i, id1 in enumerate(kintos_ids):
        for j, id2 in enumerate(kintos_ids):
            if i != j:  # No calcular relació amb un mateix
                comptador += 1
                clau = f"{id1}-{id2}"
                
                print(f"  [{comptador}/{total_combinacions}] {persones[id1].nom} → {persones[id2].nom}")
                
                # Calcular relació
                relacio = gb.calcular_relacio(id1, id2)
                if relacio:
                    # Convertir a diccionari per JSON
                    relacio_dict = {
                        "id1": relacio.id1,
                        "id2": relacio.id2,
                        "tipus": relacio.tipus,
                        "grau": relacio.grau,
                        "distancia": relacio.distancia,
                        "cami": relacio.cami
                    }
                    relacions[clau] = relacio_dict
    
    # Guardar relacions
    with open('data/relacions.json', 'w', encoding='utf-8') as f:
        json.dump(relacions, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Guardades {len(relacions)} relacions a data/relacions.json")
    print("🎉 Procés completat!")

if __name__ == "__main__":
    main()
