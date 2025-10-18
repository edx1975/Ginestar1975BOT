"""
Gestor de dades JSON per al bot genealògic
"""

import json
import os
from typing import Dict, List, Optional
from models import Usuari, Relacio
from utils import buscar_persona_per_apodo, llistar_apodos_disponibles, formatar_apodos_per_persona


class DataManager:
    """Gestor de persistència de dades"""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self.users_file = os.path.join(data_dir, "users.json")
        self.relacions_file = os.path.join(data_dir, "relacions.json")
        self.persones_file = os.path.join(data_dir, "persones.json")
        
        # Crear directori si no existeix
        os.makedirs(data_dir, exist_ok=True)
    
    def carregar_usuaris(self) -> Dict[str, Dict]:
        """Carrega els usuaris des del fitxer JSON"""
        if os.path.exists(self.users_file):
            with open(self.users_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def guardar_usuaris(self, usuaris: Dict[str, Dict]):
        """Guarda els usuaris al fitxer JSON"""
        with open(self.users_file, 'w', encoding='utf-8') as f:
            json.dump(usuaris, f, ensure_ascii=False, indent=2)
    
    def afegir_usuari(self, telegram_id: str, persona_id: str, nom: str, username: str = None):
        """Afegeix un usuari nou"""
        usuaris = self.carregar_usuaris()
        usuaris[telegram_id] = {
            "persona_id": persona_id,
            "nom": nom,
            "username": username
        }
        self.guardar_usuaris(usuaris)
    
    def obtenir_usuari(self, telegram_id: str) -> Optional[Usuari]:
        """Obté un usuari per ID de Telegram"""
        usuaris = self.carregar_usuaris()
        if telegram_id in usuaris:
            return Usuari.from_dict(telegram_id, usuaris[telegram_id])
        return None
    
    def obtenir_usuari_per_persona_id(self, persona_id: str) -> Optional[Usuari]:
        """Obté un usuari per ID de persona"""
        usuaris = self.carregar_usuaris()
        for telegram_id, data in usuaris.items():
            if data["persona_id"] == persona_id:
                return Usuari.from_dict(telegram_id, data)
        return None
    
    def carregar_relacions(self) -> Dict[str, Dict]:
        """Carrega les relacions des del fitxer JSON"""
        if os.path.exists(self.relacions_file):
            with open(self.relacions_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def guardar_relacions(self, relacions: Dict[str, Dict]):
        """Guarda les relacions al fitxer JSON"""
        with open(self.relacions_file, 'w', encoding='utf-8') as f:
            json.dump(relacions, f, ensure_ascii=False, indent=2)
    
    def afegir_relacio(self, relacio: Relacio):
        """Afegeix una relació al cache"""
        relacions = self.carregar_relacions()
        clau = f"{relacio.id1}-{relacio.id2}"
        relacions[clau] = {
            "tipus": relacio.tipus,
            "grau": relacio.grau,
            "distancia": relacio.distancia,
            "cami": relacio.cami
        }
        self.guardar_relacions(relacions)
    
    def obtenir_relacio(self, id1: str, id2: str) -> Optional[Dict]:
        """Obté una relació del cache"""
        relacions = self.carregar_relacions()
        clau1 = f"{id1}-{id2}"
        clau2 = f"{id2}-{id1}"
        
        if clau1 in relacions:
            return relacions[clau1]
        elif clau2 in relacions:
            return relacions[clau2]
        return None
    
    def carregar_persones(self) -> Dict[str, Dict]:
        """Carrega les persones des del fitxer JSON"""
        if os.path.exists(self.persones_file):
            with open(self.persones_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def llistar_persones_disponibles(self) -> List[Dict[str, str]]:
        """Llista totes les persones disponibles per a identificació"""
        persones = self.carregar_persones()
        return [
            {"id": persona_id, "nom": data["nom"]}
            for persona_id, data in persones.items()
        ]
    
    def buscar_persona_per_nom(self, nom: str) -> Optional[Dict[str, str]]:
        """Busca una persona pel nom o apodo, sense importar accents"""
        persones = self.carregar_persones()
        return buscar_persona_per_apodo(nom, persones)
    
    def llistar_apodos_disponibles(self) -> List[Dict]:
        """Llista tots els apodos disponibles per a cerca"""
        persones = self.carregar_persones()
        return llistar_apodos_disponibles(persones)
