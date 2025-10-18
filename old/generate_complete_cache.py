#!/usr/bin/env python3
"""
Script per generar cache complet de relacions per /grup i /kintos
"""

import json
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data_manager import DataManager
from gedcom_parser import GedcomParser
from graph_builder import GraphBuilder

def generate_grup_cache():
    """Genera cache complet per comando /grup"""
    print("🔄 Generant cache per /grup...")
    
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
    
    grup_cache = {}
    
    for usuari_id in kintos_ids:
        print(f"  Calculant relacions per {persones[usuari_id].nom}...")
        usuari_relacions = []
        
        for persona_id in kintos_ids:
            if persona_id != usuari_id:
                # Calcular totes les relacions
                relacions_totes = calcular_totes_relacions(gb, usuari_id, persona_id)
                if relacions_totes:
                    # Filtrar relacions úniques (mateixa lògica que el bot)
                    relacions_filtrades = filtrar_relacions_úniques(relacions_totes)
                    
                    # Comptar relacions sanguínies úniques
                    relacions_sanguinies = [r for r in relacions_filtrades if r.tipus == "sanguinia"]
                    num_gotes = len(relacions_sanguinies) if relacions_sanguinies else 0
                    
                    # Agafar la millor relació
                    if relacions_sanguinies:
                        millor_relacio = relacions_sanguinies[0]
                    else:
                        millor_relacio = relacions_filtrades[0]
                    
                    # Calcular pes
                    pes = 1000 if millor_relacio.tipus == "sanguinia" else 100
                    pes += 1000 // millor_relacio.distancia
                    
                    usuari_relacions.append({
                        'persona_id': persona_id,
                        'persona_nom': persones[persona_id].nom,
                        'relacio': {
                            'tipus': millor_relacio.tipus,
                            'grau': millor_relacio.grau,
                            'distancia': millor_relacio.distancia,
                            'cami': millor_relacio.cami
                        },
                        'pes': pes,
                        'num_gotes': num_gotes
                    })
        
        # Ordenar per pes
        usuari_relacions.sort(key=lambda x: x['pes'], reverse=True)
        grup_cache[usuari_id] = usuari_relacions
    
    # Guardar cache
    with open('data/grup_cache.json', 'w', encoding='utf-8') as f:
        json.dump(grup_cache, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Cache /grup guardat: {len(grup_cache)} usuaris")

def generate_kintos_cache():
    """Genera cache complet per comando /kintos"""
    print("🔄 Generant cache per /kintos...")
    
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
    
    kintos_cache = {}
    
    for persona1_id in kintos_ids:
        print(f"  Calculant relacions per {persones[persona1_id].nom}...")
        persona_relacions = []
        
        for persona2_id in kintos_ids:
            if persona2_id != persona1_id:
                # Calcular totes les relacions
                relacions_totes = calcular_totes_relacions(gb, persona1_id, persona2_id)
                if relacions_totes:
                    # Filtrar relacions úniques (mateixa lògica que el bot)
                    relacions_filtrades = filtrar_relacions_úniques(relacions_totes)
                    
                    # Comptar relacions sanguínies úniques
                    relacions_sanguinies = [r for r in relacions_filtrades if r.tipus == "sanguinia"]
                    num_gotes = len(relacions_sanguinies) if relacions_sanguinies else 0
                    
                    # Agafar la millor relació
                    if relacions_sanguinies:
                        millor_relacio = relacions_sanguinies[0]
                    else:
                        millor_relacio = relacions_filtrades[0]
                    
                    persona_relacions.append({
                        'persona_id': persona2_id,
                        'persona_nom': persones[persona2_id].nom,
                        'relacio': {
                            'tipus': millor_relacio.tipus,
                            'grau': millor_relacio.grau,
                            'distancia': millor_relacio.distancia,
                            'cami': millor_relacio.cami
                        },
                        'num_gotes': num_gotes
                    })
        
        kintos_cache[persona1_id] = persona_relacions
    
    # Guardar cache
    with open('data/kintos_cache.json', 'w', encoding='utf-8') as f:
        json.dump(kintos_cache, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Cache /kintos guardat: {len(kintos_cache)} persones")

def filtrar_relacions_úniques(relacions_totes):
    """Filtra relacions duplicades utilitzant la mateixa lògica que el bot"""
    # Agrupar per (distancia, tipus)
    grups = {}
    for relacio in relacions_totes:
        clau = (relacio.distancia, relacio.tipus)
        if clau not in grups:
            grups[clau] = []
        grups[clau].append(relacio)
    
    # Per cada grup, agafar només les relacions úniques
    relacions_filtrades = []
    for clau, relacions_grup in grups.items():
        if relacions_grup:
            # Agafar la primera relació del grup (ja està ordenada)
            relacions_filtrades.append(relacions_grup[0])
    
    # Ordenar per tipus i distància
    relacions_filtrades.sort(key=lambda r: (r.tipus != "sanguinia", r.distancia))
    
    return relacions_filtrades

def calcular_totes_relacions(gb, id1, id2):
    """Calcula totes les relacions entre dues persones"""
    import networkx as nx
    
    try:
        tots_camins = list(nx.all_simple_paths(gb.graph, id1, id2, cutoff=15))
    except nx.NetworkXNoPath:
        return []
    
    if not tots_camins:
        return []
    
    # Calcular relació per cada camí
    relacions_totes = []
    for cami in tots_camins:
        if len(cami) >= 2:
            grau, tipus = gb._interpretar_cami(cami)
            from models import Relacio
            relacio = Relacio(
                id1=id1,
                id2=id2,
                tipus=tipus,
                grau=grau,
                distancia=len(cami) - 1,
                cami=cami
            )
            relacions_totes.append(relacio)
    
    # Ordenar per tipus i distància
    relacions_totes.sort(key=lambda r: (r.tipus != "sanguinia", r.distancia))
    
    return relacions_totes

def main():
    print("🚀 Generant cache complet per Kintos...")
    print("=" * 50)
    
    # Crear directori data si no existeix
    os.makedirs('data', exist_ok=True)
    
    # Generar caches
    generate_grup_cache()
    print()
    generate_kintos_cache()
    
    print("=" * 50)
    print("🎉 Cache complet generat!")
    print("📁 Arxius creats:")
    print("  - data/grup_cache.json")
    print("  - data/kintos_cache.json")

if __name__ == "__main__":
    main()
