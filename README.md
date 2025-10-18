# Kintos75 - Bot Genealògic Telegram

Bot de Telegram per calcular relacions familiars basat en un fitxer GEDCOM.

## 🚀 Funcionalitats

- **Identificació d'usuaris**: Vincula usuaris de Telegram amb persones del GEDCOM
- **Càlcul de relacions**: Troba relacions familiars entre persones
- **Classificació**: Diferencia entre relacions sanguínies i per afinitat
- **Sistema de pesos**: Prioritza relacions segons proximitat genealògica
- **Cerca per malnoms**: Cerca persones per apodos sense accents

## 📁 Estructura del projecte

```
Kintos75/
├── data/                    # Dades del sistema
│   ├── persones.json       # 11 persones principals
│   ├── users.json          # Usuaris de Telegram
│   └── relacions.json      # Cache de relacions
├── scripts/                # Scripts de test i debug
├── old/                    # Arxius antics i documentació
├── bot.py                  # Bot principal
├── models.py               # Models de dades
├── gedcom_parser.py        # Parser del GEDCOM
├── graph_builder.py        # Constructor del graf familiar
├── data_manager.py         # Gestor de dades
├── kinship_weights.py      # Sistema de pesos genealògics
├── utils.py                # Funcions utilitàries
├── config.py               # Configuració
└── start_bot.py           # Script d'inici
```

## 🛠️ Instal·lació

1. **Crear entorn conda**:
   ```bash
   conda create -n kintos python=3.11
   conda activate kintos
   ```

2. **Instal·lar dependències**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configurar variables d'entorn**:
   ```bash
   cp .env.example .env
   # Editar .env amb el token del bot i ruta del GEDCOM
   ```

## 🤖 Comandos del bot

- `/start` - Iniciar el bot
- `/identifica` - Identificar-se com una persona
- `/qui_soc` - Mostrar identitat actual
- `/relacio <nom>` - Calcular relació amb una persona
- `/grup` - Mostrar relacions amb tot el grup
- `/kintos` - Matriu de relacions entre tots
- `/apodos` - Llistar malnoms disponibles
- `/help` - Ajuda

## 📊 Sistema de pesos

El bot utilitza un sistema de pesos genealògics per prioritzar relacions:

- **Relacions sanguínies**: Pesos basats en proximitat biològica
- **Ancestres importants**: BLENGUA, Anton Pujol "el Franses"
- **Puresa**: Relacions només parent-fill (sense matrimonis)
- **Distància**: Menor distància = major prioritat

## 🔧 Desenvolupament

### Scripts de test
Els scripts de test i debug estan a la carpeta `scripts/`:
- `test_system.py` - Test del sistema complet
- `debug_*.py` - Scripts de debug específic

### Estructura de dades
- **Persona**: ID, nom, sexe, dates, pares, fills, cònjuges
- **Relació**: ID1, ID2, tipus, grau, distància, camí
- **Usuari**: ID Telegram, persona_id, nom, username

## 📝 Notes

- El fitxer GEDCOM principal és `GINESTAR.ged`
- Les relacions es calculen en temps real i es cachegen
- El sistema suporta cerca sense accents i per malnoms
- Les relacions es mostren amb notació de fletxes (`<`, `>`, `=`)

## 🐛 Troubleshooting

Si el bot no respon:
1. Verificar que només hi ha una instància executant-se
2. Comprovar el token del bot a `config.py`
3. Verificar que el fitxer GEDCOM existeix
4. Revisar els logs per errors

## 📄 Llicència

Projecte personal per a càlcul de relacions familiars.