# 🚀 Instruccions per generar Cache de Relacions

## 📋 Descripció
Aquest script genera caches pre-calculats per als comandos `/grup` i `/kintos` del bot genealògic, millorant significativament la velocitat de resposta.

## 🛠️ Ús

### Execució directa:
```bash
python generate_cache.py
```

### O com a executable:
```bash
./generate_cache.py
```

## 📁 Arxius generats

### `data/grup_cache.json`
- **Contingut:** Relacions de cada usuari amb tots els altres Kintos
- **Ús:** Comando `/grup` (instantaní)
- **Estructura:**
```json
{
  "I1843": [
    {
      "persona_id": "I2599",
      "persona_nom": "Montserrat PUJOL ARS",
      "relacio": {
        "tipus": "sanguinia",
        "grau": "cosins llunyans",
        "distancia": 11,
        "cami": ["I1843", "I1234", "..."]
      },
      "pes": 1090,
      "num_gotes": 2
    }
  ]
}
```

### `data/kintos_cache.json`
- **Contingut:** Matriu completa de relacions entre tots els Kintos
- **Ús:** Comando `/kintos` (instantaní)
- **Estructura:** Similar a grup_cache però organitzat per persona

## ⚙️ Configuració del Bot

### Per utilitzar el cache:
1. **Descomenta** les línies de cache a `bot.py`:
   - Línies 295-305 per `/grup`
   - Línies 384-390 per `/kintos`

2. **Comenta** el codi de càlcul en temps real:
   - Línies 310-371 per `/grup`
   - Línies 399-440 per `/kintos`

### Per calcular en temps real:
1. **Comenta** les línies de cache
2. **Descomenta** el codi de càlcul en temps real

## 🔧 Característiques

### ✅ Avantatges del Cache:
- **Velocitat:** Resposta instantània per `/grup` i `/kintos`
- **Consistència:** Tots els usuaris veuen les mateixes dades
- **Gotes correctes:** Compta només relacions úniques, no secundàries
- **Pesos precisos:** Utilitza la mateixa lògica que el bot

### ⚠️ Limitacions:
- **Actualització manual:** Cal regenerar si canvien les dades JSON
- **Espai:** Ocupa ~90KB de disc
- **Temps inicial:** ~30 segons per generar

## 🚨 Solució de Problemes

### Error: "No s'ha trobat el fitxer GINESTAR.ged"
- **Causa:** Executant des del directori incorrecte
- **Solució:** `cd /Users/edx/Documents/GitHub/Kintos75`

### Error: "ModuleNotFoundError"
- **Causa:** Dependències no instal·lades
- **Solució:** `pip install -r requirements.txt`

### Cache desactualitzat
- **Solució:** Executar `python generate_cache.py` de nou

## 📊 Rendiment

| Comando | Sense Cache | Amb Cache | Millora |
|---------|-------------|-----------|---------|
| `/grup` | ~5-10s | ~0.1s | 50-100x |
| `/kintos` | ~15-30s | ~0.1s | 150-300x |
| `/relacio` | ~1-3s | ~1-3s | - |

## 🔄 Manteniment

### Quan regenerar el cache:
- ✅ Canvis en `data/persones.json`
- ✅ Canvis en `data/users.json`
- ✅ Actualitzacions del GEDCOM
- ❌ Canvis en `data/relacions.json` (no afecta)

### Comando ràpid:
```bash
# Regenerar i reiniciar bot
python generate_cache.py && python start_bot.py
```

## 📝 Notes Tècniques

- **Filtrat de duplicats:** Utilitza la mateixa lògica que `_filtrar_camins_duplicats`
- **Comptatge de gotes:** Només relacions úniques per (distància, tipus)
- **Ordenació:** Per pes (sanguínies primer, després per distància)
- **Codificació:** UTF-8 amb `ensure_ascii=False`
