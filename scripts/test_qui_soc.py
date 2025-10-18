#!/usr/bin/env python3
"""
Test de la comanda /qui_soc
"""

from data_manager import DataManager

def test_qui_soc():
    """Prova la funcionalitat de /qui_soc"""
    print("🔍 Testant comanda /qui_soc")
    print("=" * 40)
    
    data_manager = DataManager()
    
    # Simular usuari identificat
    user_id = "8062511186"
    usuari = data_manager.obtenir_usuari(user_id)
    
    if usuari:
        print(f"✅ Usuari trobat: {usuari.nom}")
        print(f"   ID Telegram: {usuari.telegram_id}")
        print(f"   ID Persona: {usuari.persona_id}")
        print(f"   Username: {usuari.username}")
        
        # Simular resposta de la comanda
        resposta = f"""👤 *La teva identitat:*

Nom: *{usuari.nom}*
ID: `{usuari.persona_id}`
Username: @{usuari.username}""" if usuari.username else f"""👤 *La teva identitat:*

Nom: *{usuari.nom}*
ID: `{usuari.persona_id}`
Username: No disponible"""
        
        print(f"\n📱 Resposta de /qui_soc:")
        print(resposta)
        
    else:
        print("❌ Usuari no identificat")
        print("   Resposta: No estàs identificat. Usa /identifica per identificar-te.")

if __name__ == "__main__":
    test_qui_soc()

