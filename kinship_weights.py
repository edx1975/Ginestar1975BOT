"""
Sistema de pesos genealògics basat en coeficients de consanguinitat
Implementa el sistema de Wright's Coefficient of Relationship
"""

# Pesos de proximitat genealògica (de més a menys proper)
KINSHIP_WEIGHTS = {
    # Relacions directes (50% ADN compartit)
    "pare": 1.0,
    "mare": 1.0,
    "fill": 1.0,
    "filla": 1.0,
    "germà": 1.0,
    "germana": 1.0,
    
    # Relacions de segon grau (25% ADN compartit)
    "avi": 0.5,
    "àvia": 0.5,
    "nét": 0.5,
    "néta": 0.5,
    "oncle": 0.5,
    "tia": 0.5,
    "nebot": 0.5,
    "neboda": 0.5,
    
    # Relacions de tercer grau (12.5% ADN compartit)
    "cosí": 0.25,
    "cosina": 0.25,
    "cosí_germà": 0.25,
    "cosina_germana": 0.25,
    
    # Relacions de quart grau (6.25% ADN compartit)
    "cosí_segon": 0.125,
    "cosina_segona": 0.125,
    
    # Relacions de cinquè grau (3.125% ADN compartit)
    "cosí_tercer": 0.0625,
    "cosina_tercera": 0.0625,
    
    # Relacions llunyanes (1.5625% ADN compartit)
    "cosí_quart": 0.03125,
    "cosina_quarta": 0.03125,
    
    # Relacions molt llunyanes
    "cosí_llunyà": 0.015625,
    "cosina_llunyana": 0.015625,
    "parent_llunyà": 0.0078125,
    
    # Relacions per afinitat (sense consanguinitat)
    "cònjuge": 0.0,
    "sogre": 0.0,
    "sogra": 0.0,
    "cunyat": 0.0,
    "cunyada": 0.0,
    "gendre": 0.0,
    "nora": 0.0,
    "sogre": 0.0,
    "sogra": 0.0,
    
    # Relacions desconegudes o molt llunyanes
    "desconegut": 0.001,
    "matrimoni": 0.0,
    "no_sanguinia": 0.0
}

def get_kinship_weight(relacio_type: str) -> float:
    """
    Retorna el pes de proximitat per a un tipus de relació
    
    Args:
        relacio_type: Tipus de relació (ex: "cosí", "avi", etc.)
    
    Returns:
        float: Pes de proximitat (0.0 a 1.0)
    """
    return KINSHIP_WEIGHTS.get(relacio_type.lower(), 0.001)

def calculate_kinship_score(path_weights: list) -> float:
    """
    Calcula el kinship score d'un camí basat en els pesos de les relacions
    
    Args:
        path_weights: Llista de pesos de les relacions del camí
    
    Returns:
        float: Kinship score (més alt = més proper)
    """
    if not path_weights:
        return 0.0
    
    # Suma ponderada dels pesos (inversa per a distància)
    total_weight = sum(path_weights)
    
    if total_weight == 0:
        return 0.0
    
    # Kinship score = 1 / suma_de_pesos (inversa de la distància ponderada)
    return 1.0 / total_weight

def get_relationship_type_from_path(cami: list, persones: dict) -> str:
    """
    Determina el tipus de relació basat en el camí entre dues persones
    
    Args:
        cami: Llista d'IDs de persones del camí
        persones: Diccionari de persones
    
    Returns:
        str: Tipus de relació (ex: "cosí", "avi", etc.)
    """
    if len(cami) < 2:
        return "desconegut"
    
    # Analitzar el camí per determinar el tipus de relació
    distancia = len(cami) - 1
    
    # Verificar si hi ha matrimonis (relació per afinitat)
    has_marriage = False
    for i in range(len(cami) - 1):
        id1 = cami[i]
        id2 = cami[i + 1]
        if id1 in persones and id2 in persones:
            persona1 = persones[id1]
            persona2 = persones[id2]
            if id2 in persona1.conjuges or id1 in persona2.conjuges:
                has_marriage = True
                break
    
    # Si hi ha matrimoni, és relació per afinitat
    if has_marriage:
        if distancia <= 2:
            return "cunyat"
        elif distancia <= 4:
            return "sogre"
        else:
            return "parent_afinitat"
    
    # Relacions sanguínies
    if distancia == 1:
        return "germà"
    elif distancia == 2:
        return "cosí"
    elif distancia == 3:
        return "cosí_segon"
    elif distancia == 4:
        return "cosí_tercer"
    elif distancia <= 8:
        return "cosí_llunyà"
    else:
        return "parent_llunyà"

def calculate_path_kinship_score(cami: list, persones: dict) -> tuple:
    """
    Calcula el kinship score d'un camí complet
    
    Args:
        cami: Llista d'IDs de persones del camí
        persones: Diccionari de persones
    
    Returns:
        tuple: (kinship_score, relationship_type, path_weights)
    """
    if len(cami) < 2:
        return 0.0, "desconegut", []
    
    # Calcular pesos per cada pas del camí
    path_weights = []
    for i in range(len(cami) - 1):
        id1 = cami[i]
        id2 = cami[i + 1]
        
        if id1 not in persones or id2 not in persones:
            path_weights.append(0.001)  # Pes mínim per relacions desconegudes
            continue
        
        persona1 = persones[id1]
        persona2 = persones[id2]
        
        # Determinar tipus de relació per aquest pas
        if id2 in persona1.pares or id1 in persona2.pares:
            # Relació pare-fill
            rel_type = "pare" if id2 in persona1.pares else "fill"
        elif id2 in persona1.conjuges or id1 in persona2.conjuges:
            # Relació matrimonial
            rel_type = "matrimoni"
        else:
            # Relació desconeguda
            rel_type = "desconegut"
        
        # Obtenir pes
        weight = get_kinship_weight(rel_type)
        path_weights.append(weight)
    
    # Calcular kinship score
    kinship_score = calculate_kinship_score(path_weights)
    
    # Determinar tipus de relació general
    relationship_type = get_relationship_type_from_path(cami, persones)
    
    return kinship_score, relationship_type, path_weights

def prioritize_relationships(relacions: list, persones: dict) -> list:
    """
    Prioritza les relacions segons proximitat genealògica i importància genealògica
    
    Criteris de priorització:
    1. Relacions sanguínies (amb ancestres comuns reals)
    2. Relacions més properes (menys passos)
    3. Màxim 3 relacions sempre
    
    Args:
        relacions: Llista de relacions (objectes Relacio)
        persones: Diccionari de persones
    
    Returns:
        list: Llista de relacions ordenada de més a menys important
    """
    if not relacions:
        return []
    
    # Calcular scores i metadades per cada relació
    relacions_with_scores = []
    for relacio in relacions:
        kinship_score, rel_type, path_weights = calculate_path_kinship_score(relacio.cami, persones)
        
        # Calcular score d'importància genealògica
        importance_score = calculate_genealogical_importance(relacio, persones)
        
        relacions_with_scores.append({
            'relacio': relacio,
            'kinship_score': kinship_score,
            'relationship_type': rel_type,
            'path_weights': path_weights,
            'total_weight': sum(path_weights),
            'distancia': relacio.distancia,
            'importance_score': importance_score
        })
    
    # Ordenar per importància genealògica (més alt = més important)
    relacions_with_scores.sort(key=lambda x: x['importance_score'], reverse=True)
    
    # Combinar relacions similars
    combined_relations = _combine_similar_relations(relacions_with_scores)
    
    # Retornar només les 3 millors relacions
    return [item['relacio'] for item in combined_relations[:3]]

def calculate_genealogical_importance(relacio, persones: dict) -> float:
    """
    Calcula la importància genealògica d'una relació
    
    Criteris PRIORITARIS:
    1. Ancestres comuns importants: +10000 punts (MÀXIMA PRIORITAT)
    2. Relacions sanguínies: +1000 punts
    3. Relacions més properes: +1000/distancia
    4. Relacions per afinitat: +100/distancia
    
    Args:
        relacio: Objecte Relacio
        persones: Diccionari de persones
    
    Returns:
        float: Score d'importància (més alt = més important)
    """
    score = 0.0
    
    # 1. MÀXIMA PRIORITAT: Ancestres comuns importants SENSE matrimonis
    if has_important_common_ancestor(relacio.cami, persones):
        if is_pure_blood_relation(relacio.cami, persones):
            score += 10000.0  # MÀXIMA PRIORITAT per camins purs
        else:
            score += 5000.0   # Alta prioritat però no màxima si hi ha matrimonis
        return score  # Retornar immediatament, no cal calcular res més
    
    # 2. Prioritat per relacions sanguínies
    if relacio.tipus == "sanguinia":
        score += 1000.0
    else:
        score += 100.0  # Relacions per afinitat
    
    # 3. Prioritat per proximitat (menys distància = més important)
    score += 1000.0 / relacio.distancia
    
    # 4. Bonus per relacions pures (sense matrimonis)
    if is_pure_blood_relation(relacio.cami, persones):
        score += 200.0
    
    return score

def has_important_common_ancestor(cami: list, persones: dict) -> bool:
    """
    Verifica si el camí passa per ancestres comuns importants
    
    Args:
        cami: Llista d'IDs del camí
        persones: Diccionari de persones
    
    Returns:
        bool: True si passa per ancestres importants
    """
    # Llistar ancestres comuns importants
    important_ancestors = [
        "BLENGUA",
        "Anton PUJOL",
        "germana1 BLENGUA",
        "germana2 BLENGUA",
        "Jaime SABATÉ BLENGUA",
        "Dolores SENDRA BLENGUA"
    ]
    
    for persona_id in cami:
        if persona_id in persones:
            nom = persones[persona_id].nom
            for ancestor in important_ancestors:
                if ancestor.upper() in nom.upper():
                    return True
    
    return False

def is_pure_blood_relation(cami: list, persones: dict) -> bool:
    """
    Verifica si la relació és pura (només línies sanguínies, sense matrimonis)
    
    Args:
        cami: Llista d'IDs del camí
        persones: Diccionari de persones
    
    Returns:
        bool: True si és relació pura
    """
    for i in range(len(cami) - 1):
        id1 = cami[i]
        id2 = cami[i + 1]
        
        if id1 in persones and id2 in persones:
            persona1 = persones[id1]
            persona2 = persones[id2]
            
            # Si hi ha matrimoni, no és pura
            if id2 in persona1.conjuges or id1 in persona2.conjuges:
                return False
    
    return True

def _combine_similar_relations(relacions_with_scores: list) -> list:
    """
    Combina relacions similars que només difereixen per un germà intermedi
    
    Args:
        relacions_with_scores: Llista de relacions amb scores
    
    Returns:
        list: Llista de relacions combinades
    """
    if not relacions_with_scores:
        return []
    
    # Agrupar per tipus de relació i distància similar
    groups = {}
    for item in relacions_with_scores:
        rel_type = item['relationship_type']
        distancia = item['distancia']
        
        # Crear clau de grup (tipus + distància similar)
        group_key = f"{rel_type}_{distancia}"
        
        if group_key not in groups:
            groups[group_key] = []
        groups[group_key].append(item)
    
    # Per cada grup, seleccionar la millor relació
    combined = []
    for group_items in groups.values():
        if len(group_items) == 1:
            # Només una relació, afegir-la
            combined.append(group_items[0])
        else:
            # Múltiples relacions, seleccionar la millor
            best_item = max(group_items, key=lambda x: x['kinship_score'])
            combined.append(best_item)
    
    # Ordenar per kinship score
    combined.sort(key=lambda x: x['kinship_score'], reverse=True)
    
    return combined

def get_relationship_priority(rel_type: str) -> int:
    """
    Retorna la prioritat d'un tipus de relació (menor número = major prioritat)
    
    Args:
        rel_type: Tipus de relació
    
    Returns:
        int: Prioritat (1 = més alta, 100 = més baixa)
    """
    priority_map = {
        # Relacions directes (prioritat 1-10)
        "germà": 1,
        "germana": 1,
        "pare": 2,
        "mare": 2,
        "fill": 2,
        "filla": 2,
        
        # Relacions de segon grau (prioritat 11-20)
        "cosí": 11,
        "cosina": 11,
        "avi": 12,
        "àvia": 12,
        "nét": 12,
        "néta": 12,
        "oncle": 13,
        "tia": 13,
        "nebot": 13,
        "neboda": 13,
        
        # Relacions de tercer grau (prioritat 21-30)
        "cosí_segon": 21,
        "cosina_segona": 21,
        
        # Relacions de quart grau (prioritat 31-40)
        "cosí_tercer": 31,
        "cosina_tercera": 31,
        
        # Relacions llunyanes (prioritat 41-50)
        "cosí_llunyà": 41,
        "cosina_llunyana": 41,
        "parent_llunyà": 45,
        
        # Relacions per afinitat (prioritat 51-60)
        "cunyat": 51,
        "cunyada": 51,
        "sogre": 52,
        "sogra": 52,
        "parent_afinitat": 55,
        
        # Relacions desconegudes (prioritat baixa)
        "desconegut": 90,
        "matrimoni": 95,
        "no_sanguinia": 95
    }
    
    return priority_map.get(rel_type.lower(), 80)
