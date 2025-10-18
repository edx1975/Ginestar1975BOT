# 🚀 Instruccions ràpides - Bot Genealògic

## 1. Configuració inicial

### Crear el bot de Telegram:
1. Parla amb [@BotFather](https://t.me/botfather) a Telegram
2. Executa `/newbot`
3. Segueix les instruccions per crear el bot
4. Copia el token que et dona

### Configurar el token:
```bash
# Crea el fitxer .env
echo "TELEGRAM_BOT_TOKEN=el_teu_token_aqui" > .env
```

## 2. Executar el bot

```bash
# Activar l'entorn conda
conda activate kintos

# Executar el bot
python start_bot.py
```

## 3. Comandes del bot

- `/start` - Inicia el bot
- `/identifica` - Identifica't com una persona de l'arbre
- `/qui_so` - Mostra la teva identitat
- `/relacio amb <nom>` - Calcula relació amb una persona
- `/grup` - Mostra totes les relacions del grup
- `/help` - Ajuda

## 4. Persones disponibles

El bot treballa amb aquestes 11 persones:

1. Eduard Llorens Pujol
2. Òscar Pino Vandellòs  
3. Segallet Marc Ars Borràs
4. Josep Maria Taule Figueras
5. Marta Pellissa Pujol
6. Mireia Bladé Montagut
7. Mireia Segarra Vandellòs
8. Sílvia Ars Poll
9. Montserrat Pujol Ars
10. Jaume Florenza Álvarez
11. David Usach Garcia

## 5. Exemple d'ús

1. Executa `/start` al bot
2. Executa `/identifica` i tria la teva persona
3. Executa `/relacio amb Eduard` per veure la relació
4. Executa `/grup` per veure totes les relacions

## 6. Solució de problemes

### Error de token:
- Verifica que el fitxer `.env` existeix
- Verifica que el token és correcte

### Error de GEDCOM:
- Verifica que `GINESTAR.ged` existeix al directori

### Error de dependències:
```bash
conda activate kintos
pip install -r requirements.txt
```

## 7. Aturar el bot

Prem `Ctrl+C` al terminal on s'executa el bot.

