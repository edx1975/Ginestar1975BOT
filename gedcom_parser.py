"""
Parser per llegir i processar fitxers GEDCOM
"""

import re
from typing import Dict, List, Optional, Tuple
from models import Persona


class GedcomParser:
    """Parser per processar fitxers GEDCOM"""
    
    def __init__(self, gedcom_path: str):
        self.gedcom_path = gedcom_path
        self.persones: Dict[str, Persona] = {}
        self.families: Dict[str, Dict] = {}
    
    def parse(self) -> Dict[str, Persona]:
        """Llegeix el fitxer GEDCOM i retorna un diccionari de persones"""
        with open(self.gedcom_path, 'r', encoding='utf-8-sig') as file:
            lines = file.readlines()
        
        current_record = None
        current_level = 0
        
        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            if not line:
                continue
            
            # Parsear línia GEDCOM
            parts = line.split(' ', 2)
            if len(parts) < 2:
                continue
            
            try:
                level = int(parts[0])
            except ValueError:
                continue
                
            tag = parts[1]
            value = parts[2] if len(parts) > 2 else ""
            
            # Detectar inici d'un individu
            if level == 0 and tag.startswith('@I') and tag.endswith('@'):
                current_record = tag[1:-1]  # Treure @ del principi i final
                self.persones[current_record] = Persona(
                    id=current_record,
                    nom="",
                    sexe=None
                )
                current_level = 0
            
            # Detectar inici d'una família
            elif level == 0 and tag.startswith('@F') and tag.endswith('@'):
                current_record = tag[1:-1]
                self.families[current_record] = {
                    'husband': None,
                    'wife': None,
                    'children': []
                }
                current_level = 0
            
            # Processar camps d'un individu
            elif current_record and current_record.startswith('I'):
                if level == 1:
                    if tag == 'NAME':
                        self.persones[current_record].nom = self._clean_name(value)
                    elif tag == 'SEX':
                        self.persones[current_record].sexe = value
                    elif tag == 'BIRT':
                        # Buscar data de naixement
                        birth_date = self._find_date(lines, line_num)
                        if birth_date:
                            self.persones[current_record].naixement = birth_date
                    elif tag == 'DEAT':
                        # Buscar data de defunció
                        death_date = self._find_date(lines, line_num)
                        if death_date:
                            self.persones[current_record].defuncio = death_date
                    elif tag == 'FAMC':
                        # Família com a filla
                        family_id = value[1:-1]  # Treure @
                        if family_id in self.families:
                            self.families[family_id]['children'].append(current_record)
                    elif tag == 'FAMS':
                        # Família com a esposa/esposo
                        family_id = value[1:-1]  # Treure @
                        if family_id in self.families:
                            if self.persones[current_record].sexe == 'M':
                                self.families[family_id]['husband'] = current_record
                            elif self.persones[current_record].sexe == 'F':
                                self.families[family_id]['wife'] = current_record
            
            # Processar camps d'una família
            elif current_record and current_record.startswith('F'):
                if level == 1:
                    if tag == 'HUSB':
                        husband_id = value[1:-1]
                        self.families[current_record]['husband'] = husband_id
                    elif tag == 'WIFE':
                        wife_id = value[1:-1]
                        self.families[current_record]['wife'] = wife_id
                    elif tag == 'CHIL':
                        child_id = value[1:-1]
                        self.families[current_record]['children'].append(child_id)
        
        # Establir relacions familiars
        self._establish_relationships()
        
        return self.persones
    
    def _clean_name(self, name: str) -> str:
        """Netega el nom eliminant caràcters GEDCOM"""
        # Treure / del principi i final
        name = name.strip('/')
        # Separar nom i cognoms
        parts = name.split('/')
        if len(parts) >= 2:
            given = parts[0].strip()
            surname = parts[1].strip()
            return f"{given} {surname}"
        return name.strip()
    
    def _find_date(self, lines: List[str], start_line: int) -> Optional[str]:
        """Busca una data en les línies següents"""
        for i in range(start_line, min(start_line + 10, len(lines))):
            line = lines[i].strip()
            if line.startswith('2 DATE'):
                return line[6:].strip()
        return None
    
    def _establish_relationships(self):
        """Estableix les relacions familiars entre persones"""
        for family_id, family_data in self.families.items():
            husband = family_data.get('husband')
            wife = family_data.get('wife')
            children = family_data.get('children', [])
            
            # Relació matrimonial
            if husband and wife:
                if husband in self.persones and wife in self.persones:
                    self.persones[husband].conjuges.add(wife)
                    self.persones[wife].conjuges.add(husband)
            
            # Relacions pare-fill
            for child in children:
                if child in self.persones:
                    if husband and husband in self.persones:
                        self.persones[husband].fills.add(child)
                        self.persones[child].pares.add(husband)
                    if wife and wife in self.persones:
                        self.persones[wife].fills.add(child)
                        self.persones[child].pares.add(wife)
    
    def get_persona_by_name(self, name: str) -> Optional[Persona]:
        """Busca una persona pel nom"""
        name_lower = name.lower()
        for persona in self.persones.values():
            if name_lower in persona.nom.lower():
                return persona
        return None
    
    def get_persona_by_id(self, persona_id: str) -> Optional[Persona]:
        """Busca una persona per ID"""
        return self.persones.get(persona_id)
