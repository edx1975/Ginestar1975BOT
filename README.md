# Kintos75 - Bot Genealògic Telegram

Bot de Telegram per calcular relacions familiars basat en un fitxer GEDCOM.

## 🚀 Inici ràpid

```bash
# Activar entorn
conda activate kintos

# Executar bot
python start_bot.py
```

## 📁 Estructura

```
Kintos75/
├── bot.py              # Bot principal
├── start_bot.py        # Script d'inici
├── data/               # Dades del sistema
├── scripts/            # Scripts de test i utilitats
├── docs/               # Documentació detallada
├── old/                # Arxius antics
└── backup/             # Backups i arxius temporals
```

## 🤖 Comandos

- `/start` - Iniciar
- `/identifica` - Identificar-se
- `/qui_soc` - Mostrar identitat
- `/relacio <nom>` - Calcular relació
- `/grup` - Relacions amb grup
- `/kintos` - Matriu de relacions
- `/apodos` - Llistar malnoms
- `/ajuda` - Ajuda

## 📚 Documentació

Veure `docs/README.md` per a documentació completa.

## 🛠️ Desenvolupament

```bash
# Verificar sistema
python scripts/check_system.py

# Netejar cache
python scripts/clear_cache.py

# Fer commit
python scripts/commit_changes.py
```