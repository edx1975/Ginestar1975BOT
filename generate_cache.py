#!/usr/bin/env python3
"""
Script executable per generar cache complet de relacions per /grup i /kintos
Utilitza la mateixa lògica que el bot per assegurar consistència
"""

import json
import os
import sys
from pathlib import Path

# Afegir el directori actual al path per importar mòduls locals
sys.path.append(str(Path(__file__).parent))

from data_manager import DataManager
from gedcom_parser import GedcomParser
from graph_builder import GraphBuilder
from models import Relacio

# Variable global per a les persones
persones = None

def són_relacions_similars(relacio1, relacio2):
    """Determina si dues relacions són similars (mateix fil genealògic)"""
    # Si tenen la mateixa distància i tipus, comparar els camins
    if relacio1.distancia == relacio2.distancia and relacio1.tipus == relacio2.tipus:
        # Simplificar els camins i comparar
        estructura1 = simplificar_estructura_cami(relacio1.cami)
        estructura2 = simplificar_estructura_cami(relacio2.cami)
        return estructura1 == estructura2
    return False

def simplificar_estructura_cami(cami):
    """Simplifica l'estructura d'un camí per detectar variants del mateix fil genealògic"""
    if len(cami) < 3:
        return tuple(cami)
    
    # Crear una representació simplificada del camí
    estructura = []
    for i in range(len(cami) - 1):
        id1 = cami[i]
        id2 = cami[i + 1]
        
        # Determinar el tipus de relació (simplificat)
        if id1 in persones and id2 in persones:
            persona1 = persones[id1]
            persona2 = persones[id2]
            
            if id2 in persona1.pares:
                estructura.append("P")  # Parent
            elif id1 in persona2.pares:
                estructura.append("F")  # Fill
            elif id2 in persona1.conjuges or id1 in persona2.conjuges:
                estructura.append("M")  # Matrimoni
            else:
                estructura.append("O")  # Altres
        else:
            estructura.append("O")
    
    return tuple(estructura)

def es_cami_necessari(cami, persones):
    """Verifica si un camí és necessari o si passa per matrimonis innecessaris"""
    if len(cami) < 3:
        return True
    
    # Verificar si el camí passa per matrimonis innecessaris
    for i in range(1, len(cami) - 1):
        persona_actual = cami[i]
        persona_anterior = cami[i-1]
        persona_seguent = cami[i+1]
        
        if (persona_actual in persones and 
            persona_anterior in persones and 
            persona_seguent in persones):
            
            persona_obj = persones[persona_actual]
            persona_ant_obj = persones[persona_anterior]
            persona_seg_obj = persones[persona_seguent]
            
            # Cas 1: La persona actual està casada amb l'anterior i és pare/mare de la següent
            if (persona_anterior in persona_obj.conjuges and 
                (persona_seguent in persona_obj.fills or persona_actual in persona_seg_obj.pares)):
                return False
            
            # Cas 2: La persona actual està casada amb la següent i és pare/mare de l'anterior
            if (persona_seguent in persona_obj.conjuges and 
                (persona_anterior in persona_obj.fills or persona_actual in persona_ant_obj.pares)):
                return False
            
            # Cas 3: L'anterior està casat amb la següent (matrimoni directe)
            if (persona_anterior in persona_seg_obj.conjuges or 
                persona_seguent in persona_ant_obj.conjuges):
                return False
    
    return True

def filtrar_relacions_úniques(relacions_totes, persones):
    """Filtra relacions duplicades utilitzant la mateixa lògica que el bot"""
    if not relacions_totes:
        return []
    
    # Filtrar camins innecessaris que passen per matrimonis quan no cal
    relacions_filtrades = []
    for relacio in relacions_totes:
        if es_cami_necessari(relacio.cami, persones):
            relacions_filtrades.append(relacio)
    
    # Agrupar per distància i tipus
    relacions_per_grup = {}
    for relacio in relacions_filtrades:
        clau = (relacio.distancia, relacio.tipus)
        if clau not in relacions_per_grup:
            relacions_per_grup[clau] = []
        relacions_per_grup[clau].append(relacio)
    
    # Per cada grup, seleccionar relacions úniques
    resultat = []
    for clau, grup_relacions in relacions_per_grup.items():
        # Ordenar per longitud del camí (més curt = millor)
        grup_relacions.sort(key=lambda r: len(r.cami))
        
        # Per relacions sanguínies, agafar només 1 per distància
        # Per no sanguínies, agafar només la millor
        if grup_relacions[0].tipus == "sanguinia":
            # Per sanguínies, agafar només 1 per distància
            resultat.append(grup_relacions[0])
        else:
            # Per no sanguínies, agafar només la millor
            resultat.append(grup_relacions[0])
    
    # Ordenar per tipus (sanguínies primer) i després per distància
    resultat.sort(key=lambda r: (r.tipus != "sanguinia", r.distancia))
    
    return resultat

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

def generate_grup_cache():
    """Genera cache complet per comando /grup"""
    print("🔄 Generant cache per /grup...")
    
    # Carregar dades
    global persones
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
                print(f"    → {persones[persona_id].nom}...")
                
                # Calcular totes les relacions
                relacions_totes = calcular_totes_relacions(gb, usuari_id, persona_id)
                if relacions_totes:
                    # Filtrar relacions úniques (mateixa lògica que el bot)
                    relacions_filtrades = filtrar_relacions_úniques(relacions_totes, persones)
                    
                    # Separar relacions sanguínies i no sanguínies
                    relacions_sanguinies = [r for r in relacions_filtrades if r.tipus == "sanguinia"]
                    relacions_no_sanguinies = [r for r in relacions_filtrades if r.tipus == "no_sanguinia"]
                    
                    print(f"      Sanguínies: {len(relacions_sanguinies)}, No sanguínies: {len(relacions_no_sanguinies)}")
                    
                    # Agafar les 3 millors relacions (prioritzant sanguínies)
                    relacions_a_guardar = []
                    
                    # Primer, agafar totes les sanguínies (màxim 3)
                    for relacio in relacions_sanguinies[:3]:
                        pes = 1000 + 1000 // relacio.distancia
                        relacions_a_guardar.append({
                            'persona_id': persona_id,
                            'persona_nom': persones[persona_id].nom,
                            'relacio': {
                                'tipus': relacio.tipus,
                                'grau': relacio.grau,
                                'distancia': relacio.distancia,
                                'cami': relacio.cami
                            },
                            'num_gotes': 1,
                            'pes': pes
                        })
                    
                    # Després, agafar no sanguínies fins a completar 3
                    relacions_restants = 3 - len(relacions_a_guardar)
                    for relacio in relacions_no_sanguinies[:relacions_restants]:
                        pes = 100 + 1000 // relacio.distancia
                        relacions_a_guardar.append({
                            'persona_id': persona_id,
                            'persona_nom': persones[persona_id].nom,
                            'relacio': {
                                'tipus': relacio.tipus,
                                'grau': relacio.grau,
                                'distancia': relacio.distancia,
                                'cami': relacio.cami
                            },
                            'num_gotes': 0,
                            'pes': pes
                        })
                    
                    print(f"      Guardant {len(relacions_a_guardar)} relacions")
                    
                    # Afegir totes les relacions trobades
                    usuari_relacions.extend(relacions_a_guardar)
                else:
                    print(f"      No s'han trobat relacions")
        
        # Ordenar per pes
        usuari_relacions.sort(key=lambda x: x['pes'], reverse=True)
        grup_cache[usuari_id] = usuari_relacions
        print(f"  Total relacions per {persones[usuari_id].nom}: {len(usuari_relacions)}")
    
    # Guardar cache
    with open('data/grup_cache.json', 'w', encoding='utf-8') as f:
        json.dump(grup_cache, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Cache /grup guardat: {len(grup_cache)} usuaris")

def generate_kintos_cache():
    """Genera cache complet per comando /kintos"""
    print("🔄 Generant cache per /kintos...")
    
    # Carregar dades
    global persones
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
                print(f"    → {persones[persona2_id].nom}...")
                
                # Calcular totes les relacions
                relacions_totes = calcular_totes_relacions(gb, persona1_id, persona2_id)
                if relacions_totes:
                    # Filtrar relacions úniques (mateixa lògica que el bot)
                    relacions_filtrades = filtrar_relacions_úniques(relacions_totes, persones)
                    
                    # Separar relacions sanguínies i no sanguínies
                    relacions_sanguinies = [r for r in relacions_filtrades if r.tipus == "sanguinia"]
                    relacions_no_sanguinies = [r for r in relacions_filtrades if r.tipus == "no_sanguinia"]
                    
                    print(f"      Sanguínies: {len(relacions_sanguinies)}, No sanguínies: {len(relacions_no_sanguinies)}")
                    
                    # Agafar les 3 millors relacions (prioritzant sanguínies)
                    relacions_a_guardar = []
                    
                    # Primer, agafar totes les sanguínies (màxim 3)
                    for relacio in relacions_sanguinies[:3]:
                        relacions_a_guardar.append({
                            'persona_id': persona2_id,
                            'persona_nom': persones[persona2_id].nom,
                            'relacio': {
                                'tipus': relacio.tipus,
                                'grau': relacio.grau,
                                'distancia': relacio.distancia,
                                'cami': relacio.cami
                            },
                            'num_gotes': 1
                        })
                    
                    # Després, agafar no sanguínies fins a completar 3
                    relacions_restants = 3 - len(relacions_a_guardar)
                    for relacio in relacions_no_sanguinies[:relacions_restants]:
                        relacions_a_guardar.append({
                            'persona_id': persona2_id,
                            'persona_nom': persones[persona2_id].nom,
                            'relacio': {
                                'tipus': relacio.tipus,
                                'grau': relacio.grau,
                                'distancia': relacio.distancia,
                                'cami': relacio.cami
                            },
                            'num_gotes': 0
                        })
                    
                    print(f"      Guardant {len(relacions_a_guardar)} relacions")
                    
                    # Afegir totes les relacions trobades
                    persona_relacions.extend(relacions_a_guardar)
                else:
                    print(f"      No s'han trobat relacions")
        
        kintos_cache[persona1_id] = persona_relacions
        print(f"  Total relacions per {persones[persona1_id].nom}: {len(persona_relacions)}")
    
    # Guardar cache
    with open('data/kintos_cache.json', 'w', encoding='utf-8') as f:
        json.dump(kintos_cache, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Cache /kintos guardat: {len(kintos_cache)} persones")

def main():
    """Funció principal"""
    print("🚀 Generant cache complet per Kintos...")
    print("=" * 50)
    
    # Crear directori data si no existeix
    os.makedirs('data', exist_ok=True)
    
    # Verificar que existeix el fitxer GEDCOM
    if not os.path.exists('GINESTAR.ged'):
        print("❌ Error: No s'ha trobat el fitxer GINESTAR.ged")
        print("   Assegura't que estàs executant el script des del directori correcte")
        return
    
    try:
        # Generar caches
        generate_grup_cache()
        print()
        generate_kintos_cache()
        
        print("=" * 50)
        print("🎉 Cache complet generat!")
        print("📁 Arxius creats:")
        print("  - data/grup_cache.json")
        print("  - data/kintos_cache.json")
        print()
        print("💡 Per utilitzar el cache, descomenta les línies corresponents a bot.py")
        
    except Exception as e:
        print(f"❌ Error durant la generació: {e}")
        print("   Verifica que tots els mòduls necessaris estan instal·lats")

if __name__ == "__main__":
    main()
