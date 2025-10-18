"""
Utilitats per al bot genealògic
"""

import unicodedata
import re


def normalitzar_text(text: str) -> str:
    """
    Normalitza un text eliminant accents i convertint a minúscules
    """
    if not text:
        return ""
    
    # Normalitzar unicode (NFD = Normalized Form Decomposed)
    text_normalitzat = unicodedata.normalize('NFD', text)
    
    # Eliminar accents (caràcters de combinació)
    text_sense_accents = ''.join(
        char for char in text_normalitzat 
        if unicodedata.category(char) != 'Mn'
    )
    
    # Convertir a minúscules
    return text_sense_accents.lower().strip()


def buscar_persona_per_apodo(nom_buscat: str, persones: dict) -> dict:
    """
    Busca una persona per nom o apodo, sense importar accents
    """
    nom_normalitzat = normalitzar_text(nom_buscat)
    
    for persona_id, data in persones.items():
        # Buscar en el nom principal
        nom_principal = normalitzar_text(data.get("nom", ""))
        if nom_normalitzat in nom_principal:
            return {"id": persona_id, "nom": data["nom"]}
        
        # Buscar en els apodos
        apodos = data.get("apodos", [])
        for apodo in apodos:
            apodo_normalitzat = normalitzar_text(apodo)
            if nom_normalitzat in apodo_normalitzat:
                return {"id": persona_id, "nom": data["nom"]}
    
    return None


def llistar_apodos_disponibles(persones: dict) -> list:
    """
    Llista tots els apodos disponibles per a cerca
    """
    apodos = []
    for persona_id, data in persones.items():
        nom_principal = data.get("nom", "")
        apodos.append({
            "nom": nom_principal,
            "apodos": data.get("apodos", []),
            "id": persona_id
        })
    return apodos


def formatar_apodos_per_persona(persona_data: dict) -> str:
    """
    Formata els apodos d'una persona per mostrar-los
    """
    nom = persona_data.get("nom", "")
    apodos = persona_data.get("apodos", [])
    
    if not apodos:
        return nom
    
    apodos_str = ", ".join(apodos)
    return f"{nom} ({apodos_str})"

