"""
Models per al bot genealògic de Telegram
"""

from typing import Set, Optional, List, Dict, Any
from dataclasses import dataclass


@dataclass
class Persona:
    """Classe per representar una persona en l'arbre genealògic"""
    
    id: str
    nom: str
    sexe: Optional[str] = None
    naixement: Optional[str] = None
    defuncio: Optional[str] = None
    pares: Set[str] = None
    fills: Set[str] = None
    conjuges: Set[str] = None
    
    def __post_init__(self):
        if self.pares is None:
            self.pares = set()
        if self.fills is None:
            self.fills = set()
        if self.conjuges is None:
            self.conjuges = set()
    
    def __str__(self):
        return f"{self.nom} ({self.id})"
    
    def __repr__(self):
        return f"Persona(id='{self.id}', nom='{self.nom}', sexe='{self.sexe}')"


@dataclass
class Relacio:
    """Classe per representar una relació entre dues persones"""
    
    id1: str
    id2: str
    tipus: str  # 'sanguinia' o 'no_sanguinia'
    grau: str   # ex. 'cosí segon', 'germans', etc.
    distancia: int  # passos genealògics
    cami: List[str]  # seqüència d'IDs del camí
    
    def __str__(self):
        return f"{self.grau} ({self.tipus}, distància: {self.distancia})"
    
    def __repr__(self):
        return f"Relacio(id1='{self.id1}', id2='{self.id2}', grau='{self.grau}')"


class Usuari:
    """Classe per gestionar usuaris de Telegram"""
    
    def __init__(self, telegram_id: str, persona_id: str, nom: str, username: str = None):
        self.telegram_id = telegram_id
        self.persona_id = persona_id
        self.nom = nom
        self.username = username
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "persona_id": self.persona_id,
            "nom": self.nom,
            "username": self.username
        }
    
    @classmethod
    def from_dict(cls, telegram_id: str, data: Dict[str, Any]) -> 'Usuari':
        return cls(
            telegram_id=telegram_id,
            persona_id=data["persona_id"],
            nom=data["nom"],
            username=data.get("username")
        )
    
    def __str__(self):
        return f"{self.nom} (@{self.username})" if self.username else self.nom

