"""
Constructor de graf familiar amb networkx
"""

import networkx as nx
from typing import Dict, List, Tuple, Optional
from models import Persona, Relacio


class GraphBuilder:
    """Constructor i gestor del graf familiar"""
    
    def __init__(self):
        self.graph = nx.Graph()
        self.persones: Dict[str, Persona] = {}
    
    def construir_graf(self, persones: Dict[str, Persona]) -> nx.Graph:
        """Construeix el graf familiar a partir de les persones"""
        self.persones = persones
        self.graph.clear()
        
        # Afegir nodes (persones)
        for persona_id, persona in persones.items():
            self.graph.add_node(persona_id, **{
                'nom': persona.nom,
                'sexe': persona.sexe,
                'naixement': persona.naixement,
                'defuncio': persona.defuncio
            })
        
        # Afegir arestes (relacions)
        for persona_id, persona in persones.items():
            # Relacions pare-fill (sanguínies)
            for pare_id in persona.pares:
                if pare_id in persones:
                    self.graph.add_edge(
                        persona_id, 
                        pare_id, 
                        tipus='sanguinia', 
                        relacio='pare-fill', 
                        pes=1
                    )
            
            # Relacions matrimonials (no sanguínies)
            for conjug_id in persona.conjuges:
                if conjug_id in persones:
                    self.graph.add_edge(
                        persona_id, 
                        conjug_id, 
                        tipus='no_sanguinia', 
                        relacio='matrimoni', 
                        pes=1
                    )
        
        return self.graph
    
    def calcular_relacio(self, id1: str, id2: str) -> Optional[Relacio]:
        """Calcula la relació entre dues persones"""
        if id1 not in self.graph or id2 not in self.graph:
            return None
        
        if id1 == id2:
            return Relacio(
                id1=id1,
                id2=id2,
                tipus='sanguinia',
                grau='la mateixa persona',
                distancia=0,
                cami=[id1]
            )
        
        try:
            # Trobar el camí més curt
            cami = nx.shortest_path(self.graph, id1, id2)
            distancia = len(cami) - 1
            
            # Interpretar el camí
            grau, tipus = self._interpretar_cami(cami)
            
            return Relacio(
                id1=id1,
                id2=id2,
                tipus=tipus,
                grau=grau,
                distancia=distancia,
                cami=cami
            )
        
        except nx.NetworkXNoPath:
            return None
    
    def _interpretar_cami(self, cami: List[str]) -> Tuple[str, str]:
        """Interpreta un camí i determina la relació"""
        if len(cami) < 2:
            return "desconeguda", "sanguinia"
        
        # Verificar si hi ha ancestres comuns importants (BLENGUA, Anton Pujol, etc.)
        has_important_ancestor = self._has_important_common_ancestor(cami)
        
        # Verificar si hi ha matrimonis al camí
        has_marriage = False
        for i in range(len(cami) - 1):
            id1 = cami[i]
            id2 = cami[i + 1]
            if (id1 in self.persones and id2 in self.persones and
                (id2 in self.persones[id1].conjuges or id1 in self.persones[id2].conjuges)):
                has_marriage = True
                break
        
        # Determinar tipus de relació
        if has_important_ancestor and not has_marriage:
            # Camí pur a través d'ancestre important = sanguínia
            tipus = "sanguinia"
        elif has_important_ancestor and has_marriage:
            # Camí amb ancestre important però amb matrimonis = no_sanguinia
            tipus = "no_sanguinia"
        elif not has_important_ancestor and not has_marriage:
            # Camí pur sense ancestre important = sanguínia
            tipus = "sanguinia"
        else:
            # Camí amb matrimonis sense ancestre important = no_sanguinia
            tipus = "no_sanguinia"
        
        # Analitzar el camí per determinar la relació
        if len(cami) == 2:
            # Relació directa
            grau, _ = self._relacio_directa(cami[0], cami[1])
            return grau, tipus
        elif len(cami) == 3:
            # Relació de segon grau
            grau, _ = self._relacio_segon_grau(cami)
            return grau, tipus
        else:
            # Relació de tercer grau o superior
            grau, _ = self._relacio_grau_superior(cami)
            return grau, tipus
    
    def _has_important_common_ancestor(self, cami: List[str]) -> bool:
        """Verifica si el camí passa per ancestres comuns importants"""
        # Llistar ancestres comuns importants (TEMPORALMENT DESACTIVAT)
        important_ancestors = [
            # "BLENGUA",
            # "Anton PUJOL",
            # "germana1 BLENGUA",
            # "germana2 BLENGUA",
            # "Jaime SABATÉ BLENGUA",
            # "Dolores SENDRA BLENGUA"
        ]
        
        for persona_id in cami:
            if persona_id in self.persones:
                nom = self.persones[persona_id].nom
                for ancestor in important_ancestors:
                    if ancestor.upper() in nom.upper():
                        return True
        
        return False
    
    def _relacio_directa(self, id1: str, id2: str) -> Tuple[str, str]:
        """Determina relacions directes"""
        persona1 = self.persones[id1]
        persona2 = self.persones[id2]
        
        # Pare-fill
        if id2 in persona1.pares:
            return "pare" if persona1.sexe == 'M' else "mare", "sanguinia"
        elif id1 in persona2.pares:
            return "fill" if persona1.sexe == 'M' else "filla", "sanguinia"
        
        # Germans
        elif persona1.pares & persona2.pares:
            return "germà" if persona1.sexe == 'M' else "germana", "sanguinia"
        
        # Matrimoni
        elif id2 in persona1.conjuges:
            return "esposa" if persona1.sexe == 'M' else "esposo", "no_sanguinia"
        
        return "desconeguda", "sanguinia"
    
    def _relacio_segon_grau(self, cami: List[str]) -> Tuple[str, str]:
        """Determina relacions de segon grau"""
        id1, id_intermedi, id2 = cami
        
        # Avi-nét
        if (id_intermedi in self.persones[id1].pares and 
            id2 in self.persones[id_intermedi].fills):
            return "avi" if self.persones[id1].sexe == 'M' else "àvia", "sanguinia"
        elif (id1 in self.persones[id_intermedi].fills and 
              id_intermedi in self.persones[id2].pares):
            return "nét" if self.persones[id1].sexe == 'M' else "néta", "sanguinia"
        
        # Oncle-nebot
        elif (id_intermedi in self.persones[id1].pares and 
              id_intermedi in self.persones[id2].pares and
              id1 != id2):
            return "oncle" if self.persones[id1].sexe == 'M' else "tia", "sanguinia"
        elif (id1 in self.persones[id_intermedi].fills and 
              id2 in self.persones[id_intermedi].fills and
              id1 != id2):
            return "nebot" if self.persones[id1].sexe == 'M' else "neboda", "sanguinia"
        
        # Relacions per matrimoni
        elif id_intermedi in self.persones[id1].conjuges:
            return "sogre" if self.persones[id1].sexe == 'M' else "sogra", "no_sanguinia"
        elif id1 in self.persones[id_intermedi].conjuges:
            return "gendre" if self.persones[id1].sexe == 'M' else "nora", "no_sanguinia"
        
        return "cosí" if self.persones[id1].sexe == 'M' else "cosina", "sanguinia"
    
    def _relacio_grau_superior(self, cami: List[str]) -> Tuple[str, str]:
        """Determina relacions de tercer grau o superior"""
        distancia = len(cami) - 1
        
        # Determinar si és sanguínia o no
        has_marriage = False
        for i in range(len(cami) - 1):
            id1 = cami[i]
            id2 = cami[i + 1]
            if (id1 in self.persones and id2 in self.persones and
                (id2 in self.persones[id1].conjuges or id1 in self.persones[id2].conjuges)):
                has_marriage = True
                break
        
        tipus = "no_sanguinia" if has_marriage else "sanguinia"
        
        if distancia == 3:
            if tipus == "sanguinia":
                return "cosí segon" if self.persones[cami[0]].sexe == 'M' else "cosina segona", tipus
            else:
                return "parents propers", tipus
        elif distancia == 4:
            if tipus == "sanguinia":
                return "cosí tercer" if self.persones[cami[0]].sexe == 'M' else "cosina tercera", tipus
            else:
                return "parents propers", tipus
        elif distancia < 8:
            if tipus == "sanguinia":
                return "cosins propers", tipus
            else:
                return "parents propers", tipus
        else:
            if tipus == "sanguinia":
                return "cosins llunyans", tipus
            else:
                return "parents llunyans", tipus
    
    def obtenir_relacions_grup(self, persones_ids: List[str]) -> List[Relacio]:
        """Obté totes les relacions entre un grup de persones"""
        relacions = []
        
        for i, id1 in enumerate(persones_ids):
            for id2 in persones_ids[i+1:]:
                relacio = self.calcular_relacio(id1, id2)
                if relacio:
                    relacions.append(relacio)
        
        return relacions
    
    def obtenir_grau_separacio(self, id1: str, id2: str) -> Optional[int]:
        """Obté el grau de separació entre dues persones"""
        try:
            return nx.shortest_path_length(self.graph, id1, id2)
        except nx.NetworkXNoPath:
            return None
