#!/usr/bin/env python3
"""
Demo de la nova notació de fletxes per relacions familiars
"""

from models import Persona, Relacio

def demo_notacio():
    """Demostra la nova notació de fletxes"""
    print("🧬 Demo de notació de fletxes per relacions familiars")
    print("=" * 60)
    
    # Crear persones d'exemple
    pare = Persona("I001", "Joan", "M")
    fill = Persona("I002", "Maria", "F")
    esposa = Persona("I003", "Anna", "F")
    
    # Establir relacions
    fill.pares.add("I001")
    pare.fills.add("I002")
    pare.conjuges.add("I003")
    esposa.conjuges.add("I001")
    
    # Simular camins de relació
    camins = [
        ["I002", "I001"],  # fill → pare
        ["I001", "I002"],  # pare → fill  
        ["I001", "I003"],  # matrimoni
        ["I002", "I001", "I003"],  # fill → pare → esposa
    ]
    
    persones = {"I001": pare, "I002": fill, "I003": esposa}
    
    print("📋 Exemples de notació:")
    print()
    
    for i, cami in enumerate(camins, 1):
        print(f"{i}. Camí: {' → '.join([persones[id].nom for id in cami])}")
        
        # Aplicar la nova notació
        parts = []
        for j in range(len(cami) - 1):
            id1 = cami[j]
            id2 = cami[j + 1]
            persona1 = persones[id1]
            persona2 = persones[id2]
            
            if id2 in persona1.pares:
                parts.append(f"{persona1.nom} < {persona2.nom}")
            elif id1 in persona2.pares:
                parts.append(f"{persona1.nom} > {persona2.nom}")
            elif id2 in persona1.conjuges or id1 in persona2.conjuges:
                parts.append(f"{persona1.nom} = {persona2.nom}")
            else:
                parts.append(f"{persona1.nom} → {persona2.nom}")
        
        print(f"   Notació: {' → '.join(parts)}")
        print()
    
    print("🔍 Explicació de símbols:")
    print("   <  = fill/filla de")
    print("   >  = pare/mare de") 
    print("   =  = matrimoni")
    print("   →  = relació indirecta")

if __name__ == "__main__":
    demo_notacio()

