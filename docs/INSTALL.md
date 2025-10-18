# Guia d'Instal·lació - Kintos75

## Requisits del sistema

- Python 3.11+
- Conda (recomanat)
- Git

## Pas a pas

### 1. Clonar el repositori

```bash
git clone <repository-url>
cd Kintos75
```

### 2. Crear entorn conda

```bash
conda create -n kintos python=3.11
conda activate kintos
```

### 3. Instal·lar dependències

```bash
pip install -r requirements.txt
```

### 4. Configurar variables d'entorn

```bash
cp env.example .env
```

Editar `.env` amb:
```
TELEGRAM_BOT_TOKEN=your_bot_token_here
GEDCOM_PATH=./GINESTAR.ged
LOG_LEVEL=INFO
```

### 5. Verificar configuració

```bash
python scripts/check_system.py
```

### 6. Executar el bot

```bash
python start_bot.py
```

## Verificació

El bot hauria de mostrar:
```
🚀 Iniciant bot genealògic Kintos75...
   Prem Ctrl+C per aturar el bot
========================================
2025-10-18 13:38:00,614 - __main__ - INFO - Carregant dades del GEDCOM...
2025-10-18 13:38:00,637 - __main__ - INFO - Carregades 1323 persones
2025-10-18 13:38:00,637 - __main__ - INFO - Iniciant bot...
```

## Comandos útils

```bash
# Verificar estat del sistema
python scripts/check_system.py

# Netejar cache de relacions
python scripts/clear_cache.py

# Fer commit dels canvis
python scripts/commit_changes.py
```
