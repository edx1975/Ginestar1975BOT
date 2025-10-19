"""
Bot de Telegram per al sistema genealògic
"""

import os
import json
import logging
import asyncio
import time
import traceback
from typing import Optional, List
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from telegram.error import RetryAfter

from models import Usuari, Relacio
from gedcom_parser import GedcomParser
from graph_builder import GraphBuilder
from data_manager import DataManager
from config import TELEGRAM_BOT_TOKEN, GEDCOM_PATH
# Sistema simplificat - sense pesos complexos

# Configurar logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


class GenealogicBot:
    """Bot principal de Telegram per al sistema genealògic"""
    
    def __init__(self, token: str, gedcom_path: str):
        self.token = token
        self.gedcom_path = gedcom_path
        self.data_manager = DataManager()
        
        # Mapeig de lletres a noms de persones
        self.persona_letters = {
            'a': 'Eduard Llorens Pujol',
            'b': 'Montserrat Pujol Ars', 
            'c': 'David Usach Garcia',
            'd': 'Jaume Florenza Álvarez',
            'e': 'Marta Pellissa Pujol',
            'f': 'Mireia Bladé Montagut',
            'g': 'Mireia Segarra Vandellòs',
            'h': 'Sílvia Ars Poll',
            'i': 'Òscar Pino Vandellòs',
            'j': 'Segallet Marc Ars Borràs',
            'k': 'Josep Maria Taule Figueras Piñol'
        }
        
        # Carregar dades
        self.persones = {}
        self.graph_builder = GraphBuilder()
        self.relacions_cache = {}  # Cache per relacions calculades
        
        # Inicialitzar bot
        self.application = Application.builder().token(token).build()
        self._setup_handlers()
    
    def _setup_handlers(self):
        """Configura els handlers del bot"""
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("ajuda", self.help_command))
        self.application.add_handler(CommandHandler("qui_soc", self.qui_so_command))
        self.application.add_handler(CommandHandler("relacio", self.relacio_command))
        self.application.add_handler(CommandHandler("kintos", self.kintos_command))
        self.application.add_handler(CommandHandler("tots", self.tots_command))
        self.application.add_handler(CommandHandler("identifica", self.identifica_command))
        self.application.add_handler(CommandHandler("apodos", self.apodos_command))
        self.application.add_handler(CommandHandler("aporta", self.aporta_command))
        self.application.add_handler(CommandHandler("enviar", self.enviar_command))
        self.application.add_handler(CallbackQueryHandler(self.button_callback))
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        
        # Afegir handlers per a totes les combinacions de lletres
        self._setup_letter_handlers()
    
    def _setup_letter_handlers(self):
        """Configura handlers per a totes les combinacions de lletres (ab, ac, ad, ..., jk)"""
        letters = list(self.persona_letters.keys())
        print(f"🔧 Configurant handlers per a {len(letters)} lletres: {letters}")
        
        # Generar totes les combinacions úniques
        handler_count = 0
        for i, letter1 in enumerate(letters):
            for j, letter2 in enumerate(letters):
                if i != j:  # No comparar una persona amb ella mateixa
                    command = f"{letter1}{letter2}"
                    nom1 = self.persona_letters[letter1]
                    nom2 = self.persona_letters[letter2]
                    
                    # Crear handler dinàmic
                    def create_handler(l1, l2, n1, n2):
                        async def handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
                            print(f"🔍 Handler {l1}{l2} executat: {n1} -> {n2}")
                            await self._mostrar_relacio_entre_persones(update, n1, n2)
                        return handler
                    
                    # Afegir handler
                    handler_func = create_handler(letter1, letter2, nom1, nom2)
                    self.application.add_handler(CommandHandler(command, handler_func))
                    handler_count += 1
                    print(f"  ✅ Handler /{command} creat: {nom1} -> {nom2}")
        
        print(f"🎉 Total handlers creats: {handler_count}")
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler per al comando /start"""
        try:
            user = update.effective_user
            
            # Verificar si l'usuari ja està identificat
            usuari = self.data_manager.obtenir_usuari(str(user.id))
            
            if usuari:
                await update.message.reply_text(
                    f"👋 Hola {user.first_name}!\n\n"
                    f"Ja estàs identificat com: *{usuari.nom}*\n\n"
                    f"Usa /help per veure les comandes disponibles.",
                    parse_mode='Markdown'
                )
            else:
                # Si no està identificat, obrir automàticament /identifica
                await self.identifica_command(update, context)
                
        except Exception as e:
            logger.error(f"Error en start_command: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            await update.message.reply_text(
                "✖️ Error processant el comando /start. Torna-ho a intentar.",
                parse_mode='Markdown'
            )
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler per al comando /ajuda"""
        try:
            logger.info("Iniciant help_command")
            # Llegir text d'ajuda des del fitxer JSON
            help_file = 'data/help_text.json'
            logger.info(f"Verificant fitxer: {help_file}")
            
            if os.path.exists(help_file):
                logger.info("Fitxer existeix, llegint...")
                with open(help_file, 'r', encoding='utf-8') as f:
                    help_data = json.load(f)
                logger.info(f"Dades llegides: {help_data}")
                
                # Usar help_text (ara és un array) i unir-les amb \n
                help_lines = help_data.get('help_text', [])
                help_text = '\n'.join(help_lines) if help_lines else 'Text d\'ajuda no disponible.'
                logger.info(f"Text d'ajuda formatat: {help_text[:100]}...")
            else:
                logger.warning("Fitxer d'ajuda no trobat")
                help_text = 'Text d\'ajuda no trobat.'
            
            logger.info("Enviant missatge d'ajuda")
            await update.message.reply_text(help_text, parse_mode='HTML')
            logger.info("Missatge d'ajuda enviat correctament")
        except Exception as e:
            logger.error(f"Error llegint text d'ajuda: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            await update.message.reply_text(
                "✖️ Error carregant l'ajuda. Torna-ho a intentar més tard.",
                parse_mode='Markdown'
            )
    
    async def identifica_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler per al comando /identifica"""
        persones = self.data_manager.llistar_persones_disponibles()
        
        if not persones:
            await update.message.reply_text("✖️ No s'han trobat persones disponibles.", parse_mode='Markdown')
            return
        
        # Crear teclat inline
        keyboard = []
        for persona in persones:
            keyboard.append([InlineKeyboardButton(
                persona["nom"], 
                callback_data=f"identifica_{persona['id']}"
            )])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "🔍 *Selecciona la teva identitat:*\n\n"
            "Tria la persona que et correspon de la llista:",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    async def qui_so_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler per al comando /qui_so"""
        user = update.effective_user
        user_id = str(user.id)
        
        # Log per debug
        logger.info(f"Comanda /qui_soc executada per usuari {user_id}")
        
        usuari = self.data_manager.obtenir_usuari(user_id)
        
        if not usuari:
            logger.warning(f"Usuari {user_id} no identificat")
            await update.message.reply_text(
                "✖️ No estàs identificat.\n\n"
                "Usa /identifica per identificar-te com una persona de l'arbre.",
                parse_mode='Markdown'
            )
            return
        
        logger.info(f"Usuari {user_id} identificat com {usuari.nom}")
        
        await update.message.reply_text(
            f"👤 *La teva identitat:*\n\n"
            f"Nom: *{usuari.nom}*\n"
            f"ID: `{usuari.persona_id}`",
            parse_mode='Markdown'
        )
    
    async def relacio_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler per al comando /relacio"""
        user = update.effective_user
        usuari = self.data_manager.obtenir_usuari(str(user.id))
        
        if not usuari:
            await update.message.reply_text(
                "✖️ No estàs identificat.\n\n"
                "Usa /identifica per identificar-te com una persona de l'arbre.",
                parse_mode='Markdown'
            )
            return
        
        if len(context.args) < 2:
            await update.message.reply_text(
                "✖️ Has d'especificar dos noms.\n\n"
                "Exemple: `/relacio Taule Montse`",
                parse_mode='Markdown'
            )
            return
        
        # Buscar les dues persones
        nom1 = context.args[0]
        nom2 = context.args[1]
        await self._mostrar_relacio_entre_persones(update, nom1, nom2)
    
    async def kintos_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler per al comando /kintos"""
        user = update.effective_user
        usuari = self.data_manager.obtenir_usuari(str(user.id))
        
        if not usuari:
            await update.message.reply_text(
                "✖️ No estàs identificat.\n\n"
                "Usa /identifica per identificar-te com una persona de l'arbre.",
                parse_mode='Markdown'
            )
            return
        
        persones = self.data_manager.llistar_persones_disponibles()
        
        if not persones:
            await update.message.reply_text("✖️ No s'han trobat persones disponibles.", parse_mode='Markdown')
            return
        
        # Utilitzar cache dinàmic per /kintos (mateix que /tots)
        tots_cache_file = 'data/tots_dynamic_cache.json'
        if not os.path.exists(tots_cache_file):
            await update.message.reply_text("✖️ Cache no disponible. Executa el script de generació.", parse_mode='Markdown')
            return
        
        with open(tots_cache_file, 'r', encoding='utf-8') as f:
            tots_cache = json.load(f)
        
        if usuari.persona_id not in tots_cache:
            await update.message.reply_text("✖️ No s'ha trobat cache per aquest usuari.", parse_mode='Markdown')
            return
        
        # Mostrar resultats des del cache
        text = f"🧬 *Les teves relacions amb el grup Kintos:*\n\n"
        
        relacions_cache = tots_cache[usuari.persona_id]
        
        # Crear diccionari de relacions per persona
        relacions_per_persona = {}
        for item in relacions_cache:
            persona_id = item['persona_id']
            relacions_per_persona[persona_id] = item
        
        # Ordenar per pes (calcular dinàmicament)
        relacions_ordenades = []
        for item in relacions_cache:
            relacio_data = item['relacio']
            # Calcular pes: 1000 si sanguinia + 1000/distancia
            pes = 1000 if relacio_data['tipus'] == 'sanguinia' else 100
            pes += 1000 // relacio_data['distancia']
            item['pes'] = pes
            relacions_ordenades.append(item)
        
        # Ordenar per pes descendent
        relacions_ordenades.sort(key=lambda x: x['pes'], reverse=True)
        
        contador = 1
        
        # Mostrar persones amb relació (ordenades per pes)
        for item in relacions_ordenades:
            persona_id = item['persona_id']
            relacio_data = item['relacio']
            pes = item['pes']
            num_gotes = item['num_gotes']
            
            # Trobar nom de la persona
            persona_nom = "Desconegut"
            for persona in persones:
                if persona["id"] == persona_id:
                    persona_nom = persona["nom"]
                    break
            
            # Generar emoji dinàmic sense espais
            if num_gotes > 0:
                emoji = "🩸" * num_gotes
            else:
                emoji = "💍"
            
            # Trobar lletra de la persona
            persona_letter = None
            for letter, nom in self.persona_letters.items():
                if nom == persona_nom:
                    persona_letter = letter
                    break
            
            # Trobar lletra de l'usuari actual
            usuari_letter = None
            for letter, nom in self.persona_letters.items():
                if nom == usuari.nom:
                    usuari_letter = letter
                    break
            
            # Mostrar nom amb enllaç de lletres
            if persona_letter and usuari_letter:
                text += f"{emoji} *{persona_nom}* (/{usuari_letter}{persona_letter})\n"
            else:
                text += f"{emoji} *{persona_nom}*\n"
            text += f"   {relacio_data['grau']} (distància: {relacio_data['distancia']} | Pes: {pes})\n\n"
            contador += 1
        
        # Mostrar persones sense relació
        for persona in persones:
            if persona["id"] == usuari.persona_id:
                continue  # No mostrar-se a si mateix
            
            persona_id = persona["id"]
            if persona_id not in relacions_per_persona:
                persona_nom = persona["nom"]
                
                # Trobar lletra de la persona
                persona_letter = None
                for letter, nom in self.persona_letters.items():
                    if nom == persona_nom:
                        persona_letter = letter
                        break
                
                # Trobar lletra de l'usuari actual
                usuari_letter = None
                for letter, nom in self.persona_letters.items():
                    if nom == usuari.nom:
                        usuari_letter = letter
                        break
                
                # Mostrar nom amb enllaç de lletres
                if persona_letter and usuari_letter:
                    text += f"✖️ *{persona_nom}* (/{usuari_letter}{persona_letter})\n"
                else:
                    text += f"✖️ *{persona_nom}*\n"
                text += f"   No hi ha relació\n\n"
                contador += 1
        
        # Afegir peu de pàgina amb informació sobre comandos de lletres
        text += "\n💡 *Prem /xy per veure /relacio tu 'y'*"
        
        # Enviar missatge sense botons
        await self._send_long_message(update, text)
    
    async def tots_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler per al comando /tots - mostra matriu de totes les relacions"""
        persones = self.data_manager.llistar_persones_disponibles()
        
        if not persones:
            await update.message.reply_text("✖️ No s'han trobat persones disponibles.", parse_mode='Markdown')
            return
        
        # Utilitzar cache dinàmic per /tots
        tots_cache_file = 'data/tots_dynamic_cache.json'
        
        # Carregar cache existent o crear nou
        tots_cache = {}
        if os.path.exists(tots_cache_file):
            try:
                with open(tots_cache_file, 'r', encoding='utf-8') as f:
                    tots_cache = json.load(f)
            except:
                tots_cache = {}
        
        # Organitzar per persona
        text = "🧬 *Matriu de totes les relacions*\n\n"
        
        # Verificar que totes les persones estan al cache
        persones_faltants = []
        for persona in persones:
            persona_id = persona["id"]
            if persona_id not in tots_cache:
                persones_faltants.append(persona)
        
        if persones_faltants:
            await update.message.reply_text(
                f"✖️ Cache incomplet. Falten {len(persones_faltants)} persones.\n\n"
                f"Executa el script de generació per completar el cache."
            )
            return
        
        # Crear diccionari per organitzar relacions per persona
        relacions_per_persona = {}
        for persona in persones:
            persona_id = persona["id"]
            relacions_persona = tots_cache[persona_id]
            relacions_per_persona[persona_id] = relacions_persona
        
        # Mostrar resultats des del cache
        for persona in persones:
            persona_id = persona["id"]
            persona_nom = persona["nom"]
            relacions_persona = relacions_per_persona[persona_id]
            
            # Ordenar relacions per pes (calcular dinàmicament)
            relacions_ordenades = []
            for item in relacions_persona:
                relacio_data = item['relacio']
                # Calcular pes: 1000 si sanguinia + 1000/distancia
                pes = 1000 if relacio_data['tipus'] == 'sanguinia' else 100
                pes += 1000 // relacio_data['distancia']
                item['pes'] = pes
                relacions_ordenades.append(item)
            
            # Ordenar per pes descendent
            relacions_ordenades.sort(key=lambda x: x['pes'], reverse=True)
            
            text += f"👤 *{persona_nom}:*\n\n"
            contador = 1
            for item in relacions_ordenades:
                persona_altra = item['persona_nom']
                relacio_data = item['relacio']
                num_gotes = item['num_gotes']
                pes = item['pes']
                
                # Generar emoji dinàmic
                if num_gotes > 0:
                    emoji = "🩸" * num_gotes
                else:
                        emoji = "💍"
                    
                # Trobar lletres de les persones
                persona_letter = None
                for letter, nom in self.persona_letters.items():
                    if nom == persona_altra:
                        persona_letter = letter
                        break
                
                persona_actual_letter = None
                for letter, nom in self.persona_letters.items():
                    if nom == persona_nom:
                        persona_actual_letter = letter
                        break
                
                # Mostrar nom amb enllaç de lletres
                if persona_letter and persona_actual_letter:
                    text += f"  {emoji} *{persona_altra}* (/{persona_actual_letter}{persona_letter})\n"
                else:
                    text += f"  {emoji} *{persona_altra}*\n"
                text += f"         ({relacio_data['grau']}, dist:{relacio_data['distancia']}, pes:{pes})\n\n"
                contador += 1
            text += "\n"
        
        # Enviar missatge dividit per persona sense botons
        await self._send_tots_message(update, text)
    
    async def _actualitzar_tots_cache_async(self, persones_faltants, cache_file):
        """Actualitza el cache de tots en segon pla"""
        try:
            print(f"🔄 Actualitzant cache per {len(persones_faltants)} persones...")
            
            # Carregar cache existent
            tots_cache = {}
            if os.path.exists(cache_file):
                try:
                    with open(cache_file, 'r', encoding='utf-8') as f:
                        tots_cache = json.load(f)
                except:
                    tots_cache = {}
            
            # Calcular relacions per cada persona faltant
            for persona in persones_faltants:
                persona_id = persona["id"]
                persona_nom = persona["nom"]
                
                print(f"  Calculant relacions per {persona_nom}...")
                persona_relacions = []
                
                # Calcular relacions amb totes les altres persones
                for persona_altra in self.data_manager.llistar_persones_disponibles():
                    if persona_altra["id"] != persona_id:
                        # Calcular totes les relacions
                        relacions_totes = self._calcular_totes_relacions(persona_id, persona_altra["id"])
                        
                        if relacions_totes:
                            # Filtrar relacions úniques
                            relacions_filtrades = self._filtrar_camins_duplicats(relacions_totes)
                            
                            # Comptar relacions sanguínies úniques
                            relacions_sanguinies = [r for r in relacions_filtrades if r.tipus == "sanguinia"]
                            num_gotes = len(relacions_sanguinies) if relacions_sanguinies else 0
                            
                            # Agafar la millor relació
                            if relacions_sanguinies:
                                millor_relacio = relacions_sanguinies[0]
                            else:
                                millor_relacio = relacions_filtrades[0]
                            
                            persona_relacions.append({
                                'persona_id': persona_altra["id"],
                                'persona_nom': persona_altra["nom"],
                                'relacio': {
                                    'tipus': millor_relacio.tipus,
                                    'grau': millor_relacio.grau,
                                    'distancia': millor_relacio.distancia,
                                    'cami': millor_relacio.cami
                                },
                                'num_gotes': num_gotes
                            })
                
                # Guardar al cache
                tots_cache[persona_id] = persona_relacions
                
                # Guardar fitxer després de cada persona
                with open(cache_file, 'w', encoding='utf-8') as f:
                    json.dump(tots_cache, f, indent=2, ensure_ascii=False)
                
                print(f"  ✅ {persona_nom} completat")
            
            print(f"🎉 Cache actualitzat completament!")
            
        except Exception as e:
            print(f"✖️ Error actualitzant cache: {e}")
    
    async def apodos_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler per al comando /apodos"""
        apodos_data = self.data_manager.llistar_apodos_disponibles()
        
        if not apodos_data:
            await update.message.reply_text("✖️ No s'han trobat apodos disponibles.", parse_mode='Markdown')
            return
        
        text = "👥 *Apodos i malnoms disponibles:*\n\n"
        
        for persona_data in apodos_data:
            nom = persona_data["nom"]
            apodos = persona_data["apodos"]
            apodos_str = ", ".join(apodos)
            text += f"• **{nom}**\n"
            text += f"  _{apodos_str}_\n\n"
        
        text += "💡 *Pots usar qualsevol apodo per buscar relacions!*\n"
        text += "Exemple: `/relacio Parreta Taule`"
        
        await update.message.reply_text(text, parse_mode='Markdown')
    
    async def aporta_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler per al comando /aporta - mostra com aportar informació"""
        text = """📝 *Com aportar informació genealògica*

Si vols aportar informació o suggerir canvis, envia un missatge al bot amb la següent sintaxi:

🔗 *Relacions de parentiu:*
`persona1>persona2>persona3>persona4`
On `>` vol dir que persona1 és pare/mare de persona2, persona2 és pare/mare de persona3, etc.

💍 *Relacions de matrimoni:*
`persona1=persona2`
On `=` vol dir que persona1 i persona2 estan casats.

📤 *Per enviar la informació:*
`/enviar "el teu missatge aquí"`

*Exemples:*
• `/enviar "Joan>Montserrat>David"`
• `/enviar "Joan=Maria"`
• `/enviar "Alba>Montserrat=Joan>David"`

💡 *Consells:*
• Usa noms complets o apodos coneguts
• Pots combinar relacions de parentiu i matrimoni
• La informació es guardarà per revisió manual

Gràcies per la teva contribució! 🙏"""
        
        await update.message.reply_text(text, parse_mode='Markdown')
    
    async def enviar_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler per al comando /enviar - guarda aportacions dels usuaris"""
        try:
            if not context.args:
                await update.message.reply_text(
                    "✖️ Has d'especificar el missatge a enviar.\n\n"
                    "Exemple: `/enviar JoanPratMoliner>MontserratMolinerRoca>DavidGilRoca`",
                    parse_mode='Markdown'
                )
                return
            
            # Unir tots els arguments en un sol missatge
            missatge = " ".join(context.args)
            
            # Obtenir informació de l'usuari
            user = update.effective_user
            user_id = str(user.id)
            username = user.username or "Sense username"
            nom_complet = f"{user.first_name or ''} {user.last_name or ''}".strip() or "Usuari desconegut"
            
            # Crear entrada d'aportació
            aportacio = {
                "id": f"aport_{user_id}_{int(time.time())}",
                "usuari_id": user_id,
                "usuari_nom": nom_complet,
                "username": username,
                "missatge": missatge,
                "data": time.strftime("%Y-%m-%d %H:%M:%S"),
                "timestamp": time.time()
            }
            
            # Guardar a l'arxiu persistent
            aportacions_file = 'data/aportacions.json'
            
            # Carregar dades existents
            if os.path.exists(aportacions_file):
                with open(aportacions_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            else:
                data = {"aportacions": [], "total": 0, "ultima_actualitzacio": None}
            
            # Afegir nova aportació
            data["aportacions"].append(aportacio)
            data["total"] = len(data["aportacions"])
            data["ultima_actualitzacio"] = time.strftime("%Y-%m-%d %H:%M:%S")
            
            # Guardar fitxer
            with open(aportacions_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            # Escapar caràcters especials del missatge per evitar errors de parsing
            import re
            missatge_escapat = re.sub(r'([*_`[\]()~>#+=|{}.!-])', r'\\\1', missatge)
            nom_complet_escapat = re.sub(r'([*_`[\]()~>#+=|{}.!-])', r'\\\1', nom_complet)
            
            # Resposta d'èxit
            await update.message.reply_text(
                f"✅ *Aportació rebuda!*\n\n"
                f"📝 **Missatge:** {missatge_escapat}\n"
                f"👤 **Usuari:** {nom_complet_escapat}\n"
                f"📅 **Data:** {aportacio['data']}\n\n"
                f"Gràcies per la teva contribució! La revisarem i l'afegirem al sistema si és correcta.",
                parse_mode='Markdown'
            )
            
            # Log per administrador
            logger.info(f"Nova aportació de {nom_complet} ({user_id}): {missatge}")
            
        except Exception as e:
            logger.error(f"Error guardant aportació: {e}")
            await update.message.reply_text(
                "✖️ Error guardant la teva aportació. Torna-ho a intentar més tard.",
                parse_mode='Markdown'
            )
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler per a missatges de text"""
        await update.message.reply_text(
            "🤔 No he entès el missatge.\n\n"
            "Usa /ajuda per veure les comandes disponibles.",
            parse_mode='Markdown'
        )
    
    
    
    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler per a callbacks de botons"""
        query = update.callback_query
        await query.answer()
        
        if query.data.startswith("identifica_"):
            persona_id = query.data.split("_", 1)[1]
            await self._processar_identificacio(query, persona_id)
        elif query.data.startswith("relacio_"):
            persona_id = query.data.split("_", 1)[1]
            await self._processar_relacio_callback(query, persona_id)
    
    async def _processar_identificacio(self, query, persona_id: str):
        """Processa la identificació d'un usuari"""
        user = query.from_user
        user_id = str(user.id)
        persona_data = self.data_manager.carregar_persones().get(persona_id)
        
        if not persona_data:
            await query.edit_message_text("✖️ Error: Persona no trobada.", parse_mode='Markdown')
            return
        
        # Log per debug
        logger.info(f"Processant identificació: usuari {user_id} com {persona_data['nom']}")
        
        # Guardar identificació
        self.data_manager.afegir_usuari(
            telegram_id=user_id,
            persona_id=persona_id,
            nom=persona_data["nom"],
            username=user.username
        )
        
        # Verificar que s'ha guardat
        usuari_guardat = self.data_manager.obtenir_usuari(user_id)
        if usuari_guardat:
            logger.info(f"Identificació guardada correctament: {usuari_guardat.nom}")
            await query.edit_message_text(
                f"✅ *Identificació completada!*\n\n"
                f"Has estat identificat com: *{persona_data['nom']}*\n\n"
                f"Usa /help per veure les comandes disponibles.",
                parse_mode='Markdown'
            )
        else:
            logger.error(f"Error: No s'ha pogut guardar la identificació per usuari {user_id}")
            await query.edit_message_text("✖️ Error: No s'ha pogut guardar la identificació.", parse_mode='Markdown')
    
    async def _processar_relacio_callback(self, query, persona_id: str):
        """Processa el callback de relació quan es clica un botó"""
        # Trobar nom de la persona
        persona_nom = "Desconegut"
        persones = self.data_manager.llistar_persones_disponibles()
        for persona in persones:
            if persona["id"] == persona_id:
                persona_nom = persona["nom"]
                break
        
        # Simular comando /relacio amb [nom] - cridar directament la lògica
        await self._mostrar_relacio(query, persona_nom)
    
    async def _mostrar_relacio_entre_persones(self, update_or_query, nom1: str, nom2: str):
        """Mostra la relació entre dues persones"""
        # Determinar si és Update o CallbackQuery
        if hasattr(update_or_query, 'effective_user'):
            # És Update
            user = update_or_query.effective_user
            reply_method = update_or_query.message.reply_text
        else:
            # És CallbackQuery
            user = update_or_query.from_user
            reply_method = update_or_query.edit_message_text
        
        # Buscar les dues persones
        persona1 = self.data_manager.buscar_persona_per_nom(nom1)
        persona2 = self.data_manager.buscar_persona_per_nom(nom2)
        
        if not persona1:
            await reply_method(
                f"✖️ No s'ha trobat cap persona amb el nom '{nom1}'.\n\n"
                f"Usa /kintos per veure totes les persones disponibles.",
                parse_mode='Markdown'
            )
            return
        
        if not persona2:
            await reply_method(
                f"✖️ No s'ha trobat cap persona amb el nom '{nom2}'.\n\n"
                f"Usa /kintos per veure totes les persones disponibles.",
                parse_mode='Markdown'
            )
            return
        
        # Calcular relació entre les dues persones
        relacions = self._calcular_totes_relacions(persona1["id"], persona2["id"])
        
        if not relacions:
            await reply_method(
                f"✖️ No s'ha trobat cap relació entre {nom1} i {nom2}.",
                parse_mode='Markdown'
            )
            return
        
        # Separar relacions sanguínies i no sanguínies
        relacions_sanguinies = [r for r in relacions if r.tipus == "sanguinia"]
        relacions_no_sanguinies = [r for r in relacions if r.tipus != "sanguinia"]
        
        # Determinar quines relacions mostrar
        if relacions_sanguinies:
            # Mostrar TOTES les relacions sanguínies
            relacions_a_mostrar = relacions_sanguinies
            gotes_sang = "🩸" * len(relacions_sanguinies)
            text = f"{gotes_sang} *Relació entre {nom1} i {nom2}:*\n\n"
        else:
            # Mostrar les 3 millors relacions no sanguínies
            relacions_a_mostrar = relacions_no_sanguinies[:3]
            text = f"💍 *Relació entre {nom1} i {nom2}:*\n"
            text += f"*Nota:* No hi ha relacions sanguínies directes. Mostrant les millors relacions per afinitat:\n\n"
        
        # Mostrar cada relació
        for i, relacio in enumerate(relacions_a_mostrar):
            if len(relacions_a_mostrar) > 1:
                text += f"**Camí {i+1}:**\n\n"
            
            text += f"• **Relació:** {relacio.grau}\n"
            text += f"• **Tipus:** {relacio.tipus}\n"
            text += f"• **Distància:** {relacio.distancia} passos\n"
            
            # Afegir camí familiar si està disponible
            if relacio.cami:
                cami_formatat = self._formatar_cami_relacio(relacio.cami)
                text += f"• **Camí:** {cami_formatat}\n"
            
            text += "\n"
        
        # Usar _send_long_message per evitar errors de Markdown
        if hasattr(update_or_query, 'effective_user'):
            # És Update
            await self._send_long_message(update_or_query, text)
        else:
            # És CallbackQuery - dividir manualment
            max_length = 3500
            if len(text) > max_length:
                parts = []
                lines = text.split('\n')
                current_part = ""
                
                for line in lines:
                    if len(current_part + line + '\n') > max_length:
                        if current_part:
                            parts.append(current_part.strip())
                            current_part = line + '\n'
                        else:
                            parts.append(line[:max_length])
                            current_part = line[max_length:] + '\n'
                    else:
                        current_part += line + '\n'
                
                if current_part.strip():
                    parts.append(current_part.strip())
                
                for i, part in enumerate(parts):
                    if i > 0:
                        await asyncio.sleep(1.0)
                    await reply_method(part, parse_mode='Markdown')
            else:
                await reply_method(text, parse_mode='Markdown')
    
    async def _mostrar_relacio(self, update_or_query, persona_nom: str):
        """Mostra la relació amb una persona (funciona amb Update o CallbackQuery)"""
        # Determinar si és Update o CallbackQuery
        if hasattr(update_or_query, 'effective_user'):
            # És Update
            user = update_or_query.effective_user
            reply_method = update_or_query.message.reply_text
        else:
            # És CallbackQuery
            user = update_or_query.from_user
            reply_method = update_or_query.edit_message_text
        
        usuari = self.data_manager.obtenir_usuari(str(user.id))
        
        if not usuari:
            await reply_method(
                "✖️ No estàs identificat.\n\n"
                "Usa /identifica per identificar-te com una persona de l'arbre."
            )
            return
        
        # Buscar la persona
        persona_trobada = self.data_manager.buscar_persona_per_nom(persona_nom)
        
        if not persona_trobada:
            await reply_method(
                f"✖️ No s'ha trobat cap persona amb el nom '{persona_nom}'.\n\n"
                f"Usa /kintos per veure totes les persones disponibles."
            )
            return
        
        # Utilitzar cache per /relacio (mateix que /kintos i /tots)
        tots_cache_file = 'data/tots_dynamic_cache.json'
        if not os.path.exists(tots_cache_file):
            await reply_method("✖️ Cache no disponible. Executa el script de generació.")
            return
        
        with open(tots_cache_file, 'r', encoding='utf-8') as f:
            tots_cache = json.load(f)
        
        if usuari.persona_id not in tots_cache:
            await reply_method("✖️ No s'ha trobat cache per aquest usuari.")
            return
        
        # Buscar totes les relacions amb aquesta persona al cache
        relacions_cache = tots_cache[usuari.persona_id]
        relacions_persona = []
        
        for item in relacions_cache:
            if item['persona_id'] == persona_trobada["id"]:
                relacions_persona.append(item)
        
        if not relacions_persona:
            await reply_method(f"✖️ No s'ha trobat relació amb {persona_nom}.")
            return
        
        # Separar relacions sanguínies i no sanguínies
        relacions_sanguinies = []
        relacions_no_sanguinies = []
        
        for item in relacions_persona:
            relacio_data = item['relacio']
            if relacio_data['tipus'] == 'sanguinia':
                relacions_sanguinies.append(item)
            else:
                relacions_no_sanguinies.append(item)
        
        # Si no hi ha relacions sanguínies al cache, calcular-les en temps real
        if not relacions_sanguinies:
            print(f"🔍 No hi ha relacions sanguínies al cache per {persona_nom}, calculant en temps real...")
            relacions_calculades = self._calcular_totes_relacions(usuari.persona_id, persona_trobada["id"])
            relacions_sanguinies_calculades = [r for r in relacions_calculades if r.tipus == "sanguinia"]
            
            # Convertir a format del cache (màxim 3)
            for relacio in relacions_sanguinies_calculades[:3]:
                relacions_sanguinies.append({
                    'persona_id': persona_trobada["id"],
                    'persona_nom': persona_nom,
                    'relacio': {
                        'tipus': relacio.tipus,
                        'grau': relacio.grau,
                        'distancia': relacio.distancia,
                        'cami': relacio.cami
                    },
                    'num_gotes': 1
                })
        
        # Ordenar per distància (més properes primer)
        relacions_sanguinies.sort(key=lambda x: x['relacio']['distancia'])
        relacions_no_sanguinies.sort(key=lambda x: x['relacio']['distancia'])
        
        # Determinar quines relacions mostrar
        if relacions_sanguinies:
            # Mostrar TOTES les relacions sanguínies
            relacions_a_mostrar = relacions_sanguinies
            gotes_sang = "🩸" * len(relacions_sanguinies)
            text = f"{gotes_sang} *Relacions sanguínies amb {persona_nom}:*\n\n"
        else:
            # Mostrar les 3 millors relacions no sanguínies
            relacions_a_mostrar = relacions_no_sanguinies[:3]
            text = f"💍 *Relació amb {persona_nom}:*\n"
            text += f"*Nota:* No hi ha relacions sanguínies directes. Mostrant les millors relacions per afinitat:\n\n"
        
        # Mostrar cada relació
        for i, item in enumerate(relacions_a_mostrar):
            relacio_data = item['relacio']
            num_gotes = item['num_gotes']
            
            # Generar emoji dinàmic
            if num_gotes > 0:
                emoji = "🩸" * num_gotes
            else:
                emoji = "💍"
            
            if len(relacions_a_mostrar) > 1:
                text += f"**Camí {i+1}:**\n\n"
            
            text += f"{emoji} *{persona_nom}*\n"
            text += f"• **Relació:** {relacio_data['grau']}\n"
            text += f"• **Tipus:** {relacio_data['tipus']}\n"
            text += f"• **Distància:** {relacio_data['distancia']} passos\n"
            
            # Afegir camí familiar si està disponible
            if 'cami' in relacio_data and relacio_data['cami']:
                cami_formatat = self._formatar_cami_relacio(relacio_data['cami'])
                text += f"• **Camí:** {cami_formatat}\n"
            
            text += "\n"
        
        # Usar _send_long_message per evitar errors de Markdown
        if hasattr(update_or_query, 'effective_user'):
            # És Update
            await self._send_long_message(update_or_query, text)
        else:
            # És CallbackQuery - dividir manualment
            max_length = 3500
            if len(text) > max_length:
                parts = []
                lines = text.split('\n')
                current_part = ""
                
                for line in lines:
                    if len(current_part + line + '\n') > max_length:
                        if current_part:
                            parts.append(current_part.strip())
                            current_part = line + '\n'
                        else:
                            parts.append(line[:max_length])
                            current_part = line[max_length:] + '\n'
                    else:
                        current_part += line + '\n'
                
                if current_part.strip():
                    parts.append(current_part.strip())
                
                for i, part in enumerate(parts):
                    if i > 0:
                        await asyncio.sleep(1.0)
                    await reply_method(part, parse_mode='Markdown')
            else:
                await reply_method(text, parse_mode='Markdown')
    
    def _calcular_relacio(self, id1: str, id2: str) -> Optional[Relacio]:
        """Calcula la relació entre dues persones"""
        # Verificar cache
        relacio_cache = self.data_manager.obtenir_relacio(id1, id2)
        if relacio_cache:
            return Relacio(
                id1=id1,
                id2=id2,
                tipus=relacio_cache["tipus"],
                grau=relacio_cache["grau"],
                distancia=relacio_cache["distancia"],
                cami=relacio_cache["cami"]
            )
        
        # Calcular nova relació
        relacio = self.graph_builder.calcular_relacio(id1, id2)
        if relacio:
            self.data_manager.afegir_relacio(relacio)
        
        return relacio
    
    def _calcular_totes_relacions(self, id1: str, id2: str) -> List[Relacio]:
        """Calcula les 3 relacions més importants entre dues persones utilitzant el sistema de pesos genealògics"""
        import networkx as nx
        
        # Assegurar-se que el graf estigui construït
        if not hasattr(self.graph_builder, 'graph') or self.graph_builder.graph is None:
            self.graph_builder.construir_graf(self.persones)
        
        # ESTRATÈGIA NOVA: Buscar primer camins amb ancestres comuns importants
        relacions_importants = self._buscar_relacions_amb_ancestres_importants(id1, id2)
        
        # Sempre buscar tots els camins per no perdre relacions directes
        try:
            tots_camins = list(nx.all_simple_paths(self.graph_builder.graph, id1, id2, cutoff=15))
        except nx.NetworkXNoPath:
            tots_camins = []
        
        if tots_camins:
            # Calcular relació per cada camí
            relacions_totes = []
            for cami in tots_camins:
                if len(cami) >= 2:
                    grau, tipus = self.graph_builder._interpretar_cami(cami)
                    relacio = Relacio(
                        id1=id1,
                        id2=id2,
                        tipus=tipus,
                        grau=grau,
                        distancia=len(cami) - 1,
                        cami=cami
                    )
                    relacions_totes.append(relacio)
            
            # Filtrar camins duplicats o amb loops innecessaris
            relacions_filtrades = self._filtrar_camins_duplicats(relacions_totes)
            
            # Ordenar per tipus (sanguínies primer) i després per distància
            relacions_ordenades = sorted(relacions_filtrades, key=lambda r: (r.tipus != "sanguinia", r.distancia))
            
            return relacions_ordenades
        
        return []
    
    def _obtenir_relacio_cached(self, id1: str, id2: str) -> Optional[Relacio]:
        """Obté una relació del cache o la calcula si no existeix"""
        cache_key = f"{id1}-{id2}"
        
        if cache_key in self.relacions_cache:
            return self.relacions_cache[cache_key]
        
        # Calcular totes les relacions
        relacions_totes = self._calcular_totes_relacions(id1, id2)
        if not relacions_totes:
            self.relacions_cache[cache_key] = None
            return None
        
        # Agafar la primera relació (ja ordenada per tipus i distància)
        millor_relacio = relacions_totes[0]
        
        # Guardar al cache
        self.relacions_cache[cache_key] = millor_relacio
        return millor_relacio
    
    def _filtrar_camins_duplicats(self, relacions: List[Relacio]) -> List[Relacio]:
        """Filtra camins duplicats o amb loops innecessaris"""
        if not relacions:
            return []
        
        # Filtrar camins innecessaris que passen per matrimonis quan no cal
        relacions_filtrades = []
        for relacio in relacions:
            if self._es_cami_necessari(relacio.cami):
                relacions_filtrades.append(relacio)
        
        # Agrupar per distància i tipus
        relacions_per_grup = {}
        for relacio in relacions_filtrades:
            clau = (relacio.distancia, relacio.tipus)
            if clau not in relacions_per_grup:
                relacions_per_grup[clau] = []
            relacions_per_grup[clau].append(relacio)
        
        # Per cada grup, seleccionar relacions úniques
        resultat = []
        for clau, grup_relacions in relacions_per_grup.items():
            # Ordenar per longitud del camí (més curt = millor)
            grup_relacions.sort(key=lambda r: len(r.cami))
            
            # Per cada grup, seleccionar fins a 2 relacions per mostrar varietat
            # però mantenir la millor com a prioritat
            resultat.append(grup_relacions[0])  # Sempre la millor
            if len(grup_relacions) > 1:
                # Afegir una segona si és significativament diferent
                for relacio in grup_relacions[1:]:
                    if not self._són_relacions_similars(grup_relacions[0], relacio):
                        resultat.append(relacio)
                        break
        
        # Ordenar per tipus (sanguínies primer) i després per distància
        resultat.sort(key=lambda r: (r.tipus != "sanguinia", r.distancia))
        
        # Assegurar-se que tenim fins a 3 resultats
        if len(resultat) < 3:
            # Si no tenim prou, afegir més relacions del grup original
            relacions_restants = [r for r in relacions_filtrades if r not in resultat]
            relacions_restants.sort(key=lambda r: (r.tipus != "sanguinia", r.distancia))
            
            # Afegir fins a completar 3
            for relacio in relacions_restants:
                if len(resultat) >= 3:
                    break
                # Verificar que no sigui duplicada
                if not any(self._són_relacions_similars(relacio, r) for r in resultat):
                    resultat.append(relacio)
        
        return resultat
    
    def _són_relacions_similars(self, relacio1: Relacio, relacio2: Relacio) -> bool:
        """Determina si dues relacions són similars (mateix fil genealògic)"""
        # Si tenen la mateixa distància i tipus, comparar els camins
        if relacio1.distancia == relacio2.distancia and relacio1.tipus == relacio2.tipus:
            # Simplificar els camins i comparar
            estructura1 = self._simplificar_estructura_cami(relacio1.cami)
            estructura2 = self._simplificar_estructura_cami(relacio2.cami)
            return estructura1 == estructura2
        return False
    
    def _es_cami_necessari(self, cami: List[str]) -> bool:
        """Verifica si un camí és necessari o si passa per matrimonis innecessaris"""
        if len(cami) < 3:
            return True
        
        # Verificar si el camí passa per matrimonis innecessaris
        for i in range(1, len(cami) - 1):
            persona_actual = cami[i]
            persona_anterior = cami[i-1]
            persona_seguent = cami[i+1]
            
            if (persona_actual in self.persones and 
                persona_anterior in self.persones and 
                persona_seguent in self.persones):
                
                persona_obj = self.persones[persona_actual]
                persona_ant_obj = self.persones[persona_anterior]
                persona_seg_obj = self.persones[persona_seguent]
                
                # Cas 1: La persona actual està casada amb l'anterior i és pare/mare de la següent
                if (persona_anterior in persona_obj.conjuges and 
                    (persona_seguent in persona_obj.fills or persona_actual in persona_seg_obj.pares)):
                    return False
                
                # Cas 2: La persona actual està casada amb la següent i és pare/mare de l'anterior
                if (persona_seguent in persona_obj.conjuges and 
                    (persona_anterior in persona_obj.fills or persona_actual in persona_ant_obj.pares)):
                    return False
                
                # Cas 3: L'anterior està casat amb la següent (matrimoni directe)
                if (persona_anterior in persona_seg_obj.conjuges or 
                    persona_seguent in persona_ant_obj.conjuges):
                    return False
        
        return True
    
    def _buscar_relacions_amb_ancestres_importants(self, id1: str, id2: str) -> List[Relacio]:
        """Busca relacions que passen per ancestres comuns importants"""
        import networkx as nx
        
        # Llistar ancestres comuns importants (TEMPORALMENT DESACTIVAT)
        important_ancestors = [
            # "BLENGUA",
            # "Anton PUJOL",
            # "germana1 BLENGUA",
            # "germana2 BLENGUA",
            # "Jaime SABATÉ BLENGUA",
            # "Dolores SENDRA BLENGUA"
        ]
        
        # Buscar persones que contenen aquests noms
        ancestor_ids = []
        for persona_id, persona in self.persones.items():
            nom = persona.nom.upper()
            for ancestor in important_ancestors:
                if ancestor.upper() in nom:
                    ancestor_ids.append(persona_id)
                    break
        
        if not ancestor_ids:
            return []
        
        # Buscar camins que passen per aquests ancestres
        relacions_importants = []
        camins_vistos = set()  # Per evitar duplicats
        
        for ancestor_id in ancestor_ids:
            try:
                # Camí d'id1 a ancestor
                cami1 = nx.shortest_path(self.graph_builder.graph, id1, ancestor_id)
                # Camí d'ancestor a id2
                cami2 = nx.shortest_path(self.graph_builder.graph, ancestor_id, id2)
                # Combinar camins (eliminar duplicat de ancestor_id)
                cami_complet = cami1 + cami2[1:]
                
                # Evitar duplicats - comparar per estructura, no per IDs exactes
                cami_simplificat = self._simplificar_estructura_cami(cami_complet)
                if cami_simplificat in camins_vistos:
                    continue
                camins_vistos.add(cami_simplificat)
                
                if len(cami_complet) >= 2:
                    # Usar la lògica del graph_builder per determinar el tipus
                    grau, tipus = self.graph_builder._interpretar_cami(cami_complet)
                    relacio = Relacio(
                        id1=id1,
                        id2=id2,
                        tipus=tipus,
                        grau=grau,
                        distancia=len(cami_complet) - 1,
                        cami=cami_complet
                    )
                    relacions_importants.append(relacio)
                    
            except nx.NetworkXNoPath:
                continue
        
        # Ordenar per distància (més properes primer)
        relacions_importants.sort(key=lambda r: r.distancia)
        
        return relacions_importants
    
    def _buscar_relacions_no_sanguinies(self, id1: str, id2: str, relacions_existents: List[Relacio]) -> List[Relacio]:
        """Busca relacions no sanguínies per completar fins a 3 relacions"""
        import networkx as nx
        
        # Trobar camins curts que no siguin duplicats
        try:
            tots_camins = list(nx.all_simple_paths(self.graph_builder.graph, id1, id2, cutoff=12))
        except nx.NetworkXNoPath:
            return []
        
        # Filtrar camins que ja tenim
        camins_existents = set()
        for relacio in relacions_existents:
            cami_str = "->".join(relacio.cami)
            camins_existents.add(cami_str)
        
        relacions_no_sanguinies = []
        
        for cami in tots_camins:
            if len(cami) >= 2:
                cami_str = "->".join(cami)
                if cami_str in camins_existents:
                    continue
                
                # Verificar si hi ha matrimonis (relació no sanguínia)
                has_marriage = False
                for i in range(len(cami) - 1):
                    p1_id = cami[i]
                    p2_id = cami[i + 1]
                    if (p1_id in self.persones and p2_id in self.persones and
                        (p2_id in self.persones[p1_id].conjuges or p1_id in self.persones[p2_id].conjuges)):
                        has_marriage = True
                        break
                
                if has_marriage:
                    grau, _ = self.graph_builder._interpretar_cami(cami)
                    relacio = Relacio(
                        id1=id1,
                        id2=id2,
                        tipus="no_sanguinia",
                        grau=grau,
                        distancia=len(cami) - 1,
                        cami=cami
                    )
                    relacions_no_sanguinies.append(relacio)
                    
                    # Només volem unes poques per completar
                    if len(relacions_no_sanguinies) >= 2:
                        break
        
        # Ordenar per distància (més properes primer)
        relacions_no_sanguinies.sort(key=lambda r: r.distancia)
        
        return relacions_no_sanguinies
    
    def _simplificar_estructura_cami(self, cami: List[str]) -> str:
        """Simplifica l'estructura d'un camí per detectar duplicats"""
        if len(cami) < 2:
            return "->".join(cami)
        
        # Crear una representació simplificada del camí
        estructura = []
        for i in range(len(cami) - 1):
            p1_id = cami[i]
            p2_id = cami[i + 1]
            
            # Determinar tipus de relació
            if (p1_id in self.persones and p2_id in self.persones and
                (p2_id in self.persones[p1_id].conjuges or p1_id in self.persones[p2_id].conjuges)):
                estructura.append("M")  # Matrimoni
            else:
                estructura.append("P")  # Parentiu
        
        return "->".join(estructura)
    
    def _es_relacio_pura(self, cami: List[str]) -> bool:
        """Determina si una relació és pura (només pares i fills, sense canvis de direcció)"""
        if len(cami) < 2:
            return True
        
        # Verificar que tots els passos siguin relacions pare-fill directes
        for i in range(len(cami) - 1):
            id1 = cami[i]
            id2 = cami[i + 1]
            persona1 = self.persones[id1]
            persona2 = self.persones[id2]
            
            # Només acceptar relacions pare-fill directes
            if not (id2 in persona1.pares or id1 in persona2.pares):
                return False
        
        # Verificar que no hi hagi canvis de direcció
        direccions = []
        for i in range(len(cami) - 1):
            id1 = cami[i]
            id2 = cami[i + 1]
            persona1 = self.persones[id1]
            persona2 = self.persones[id2]
            
            # Determinar direcció d'aquest pas
            if id2 in persona1.pares:
                direccions.append("pujant")  # id1 és fill de id2
            elif id1 in persona2.pares:
                direccions.append("baixant")  # id1 és pare de id2
            else:
                return False
        
        # Verificar que no hi hagi canvis de direcció
        if len(direccions) < 2:
            return True
        
        # Comptar canvis de direcció
        canvis = 0
        for i in range(1, len(direccions)):
            if direccions[i] != direccions[i-1]:
                canvis += 1
        
        # Acceptar si no hi ha canvis de direcció o màxim 3 canvis
        return canvis <= 3
    
    def _simplificar_estructura_cami(self, cami: List[str]) -> str:
        """Simplifica l'estructura d'un camí per detectar variants del mateix fil genealògic"""
        if len(cami) < 3:
            return tuple(cami)
        
        # Crear una representació simplificada del camí
        estructura = []
        for i in range(len(cami) - 1):
            id1 = cami[i]
            id2 = cami[i + 1]
            persona1 = self.persones[id1]
            persona2 = self.persones[id2]
            
            # Determinar el tipus de relació
            if id2 in persona1.pares:
                estructura.append("P")  # Parent
            elif id1 in persona2.pares:
                estructura.append("F")  # Fill
            elif id2 in persona1.conjuges or id1 in persona2.conjuges:
                estructura.append("M")  # Matrimoni
            else:
                estructura.append("O")  # Altres
        
        # Simplificar agrupant patrons comuns
        estructura_simplificada = []
        i = 0
        while i < len(estructura):
            if i < len(estructura) - 2:
                # Detectar patrons de germans: F-P-F o P-F-P
                if (estructura[i] == "F" and estructura[i+1] == "P" and estructura[i+2] == "F") or \
                   (estructura[i] == "P" and estructura[i+1] == "F" and estructura[i+2] == "P"):
                    estructura_simplificada.append("G")  # Germans
                    i += 3
                else:
                    estructura_simplificada.append(estructura[i])
                    i += 1
            else:
                estructura_simplificada.append(estructura[i])
                i += 1
        
        # Agrupar patrons repetitius per simplificar encara més
        final = []
        i = 0
        while i < len(estructura_simplificada):
            if i < len(estructura_simplificada) - 1 and estructura_simplificada[i] == estructura_simplificada[i+1]:
                # Comptar repeticions
                count = 1
                j = i + 1
                while j < len(estructura_simplificada) and estructura_simplificada[j] == estructura_simplificada[i]:
                    count += 1
                    j += 1
                final.append(f"{estructura_simplificada[i]}{count}")
                i = j
            else:
                final.append(estructura_simplificada[i])
                i += 1
        
        return tuple(final)
    
    def _calcular_relacions_grup(self, persones_ids: List[str]) -> List[Relacio]:
        """Calcula totes les relacions d'un grup"""
        return self.graph_builder.obtenir_relacions_grup(persones_ids)
    
    def _formatar_cami_relacio(self, cami: List[str]) -> str:
        """Formata el camí d'una relació amb fletxes indicatives"""
        if len(cami) < 2:
            return " → ".join([self.persones[id].nom for id in cami])
        
        parts = []
        for i in range(len(cami) - 1):
            id1 = cami[i]
            id2 = cami[i + 1]
            persona1 = self.persones[id1]
            persona2 = self.persones[id2]
            
            # Determinar el tipus de relació
            if id2 in persona1.pares:
                # persona1 és fill de persona2
                parts.append(f"{persona1.nom} < {persona2.nom}")
            elif id1 in persona2.pares:
                # persona1 és pare de persona2
                parts.append(f"{persona1.nom} > {persona2.nom}")
            elif id2 in persona1.conjuges:
                # matrimoni
                parts.append(f"{persona1.nom} = {persona2.nom}")
            elif id1 in persona2.conjuges:
                # matrimoni (ordre invers)
                parts.append(f"{persona1.nom} = {persona2.nom}")
            else:
                # Relació indirecta o desconeguda
                parts.append(f"{persona1.nom} → {persona2.nom}")
        
        # Simplificar camins repetitius
        return self._simplificar_cami(parts)
    
    def _simplificar_cami(self, parts: List[str]) -> str:
        """Simplifica un camí eliminant repeticions i fent-lo més llegible"""
        if not parts:
            return ""
        
        # Unir parts i després simplificar
        cami_complet = " → ".join(parts)
        
        # Eliminar repeticions de noms consecutius
        import re
        # Patró per trobar "Nom < Nom → Nom < Nom" i simplificar a "Nom < Nom"
        cami_simplificat = re.sub(r'([^→]+) → \1', r'\1', cami_complet)
        
        # Si el camí és massa llarg, mostrar només els punts clau
        if len(cami_simplificat) > 200:
            # Agafar primer i últim element, i alguns intermedis
            elements = cami_simplificat.split(' → ')
            if len(elements) > 4:
                primer = elements[0]
                ultim = elements[-1]
                mig = " ... "
                return f"{primer}{mig}{ultim}"
        
        return cami_simplificat
    
    async def _send_message_safe(self, update: Update, text: str, delay: float = 1.0):
        """Envia un missatge amb rate limiting per evitar flood control"""
        try:
            await update.message.reply_text(text, parse_mode='Markdown')
        except RetryAfter as e:
            logger.warning(f"Rate limited, esperant {e.retry_after} segons...")
            await asyncio.sleep(e.retry_after)
            await update.message.reply_text(text, parse_mode='Markdown')
        except Exception as e:
            logger.error(f"Error enviant missatge: {e}")
            # Si hi ha error de Markdown parsing, enviar sense Markdown
            try:
                await update.message.reply_text(text)
            except Exception as e2:
                logger.error(f"Error enviant sense Markdown: {e2}")
                # Si encara falla, dividir el missatge
            if len(text) > 4000:
                await self._send_long_message(update, text, delay)
            else:
                raise e
    
    async def _send_long_message(self, update: Update, text: str, delay: float = 1.0):
        """Divideix i envia un missatge llarg en parts"""
        max_length = 3500
        parts = []
        
        # Dividir per línies
        lines = text.split('\n')
        current_part = ""
        
        for line in lines:
            if len(current_part + line + '\n') > max_length:
                if current_part:
                    parts.append(current_part.strip())
                    current_part = line + '\n'
                else:
                    # Línia massa llarga, dividir-la
                    parts.append(line[:max_length])
                    current_part = line[max_length:] + '\n'
            else:
                current_part += line + '\n'
        
        if current_part.strip():
            parts.append(current_part.strip())
        
        # Enviar cada part amb delay
        for i, part in enumerate(parts):
            if i > 0:
                await asyncio.sleep(delay)
            await self._send_message_safe(update, part, delay)
    
    async def _send_tots_message(self, update: Update, text: str):
        """Envia missatge de tots dividit per persona"""
        # Dividir per seccions de persona
        sections = text.split('👤 *')
        
        # Primer missatge amb títol
        if sections:
            first_section = sections[0].strip()
            if first_section:
                await update.message.reply_text(first_section, parse_mode='Markdown')
                await asyncio.sleep(0.5)
        
        # Enviar cada persona per separat
        for i, section in enumerate(sections[1:], 1):
            if section.strip():
                persona_text = f"👤 *{section.strip()}"
                await update.message.reply_text(persona_text, parse_mode='Markdown')
                await asyncio.sleep(0.3)  # Pausa per evitar flood control
    
    async def _send_tots_message_with_buttons(self, update: Update, text: str, keyboard: List):
        """Envia missatge de tots dividit per persona amb botons"""
        # Dividir per seccions de persona
        sections = text.split('👤 *')
        
        # Primer missatge amb títol
        if sections:
            first_section = sections[0].strip()
            if first_section:
                await update.message.reply_text(first_section, parse_mode='Markdown')
                await asyncio.sleep(0.5)
        
        # Enviar cada persona per separat amb botons
        for i, section in enumerate(sections[1:], 1):
            if section.strip():
                persona_text = f"👤 *{section.strip()}"
                
                # Crear botons per aquesta persona (aproximadament 10 per persona)
                persona_keyboard = keyboard[(i-1)*10:i*10] if len(keyboard) > (i-1)*10 else keyboard[(i-1)*10:]
                
                if persona_keyboard:
                    reply_markup = InlineKeyboardMarkup(persona_keyboard)
                    await update.message.reply_text(persona_text, reply_markup=reply_markup, parse_mode='Markdown')
                else:
                    await update.message.reply_text(persona_text, parse_mode='Markdown')
                
                await asyncio.sleep(0.3)  # Pausa per evitar flood control
    
    def carregar_dades(self):
        """Carrega les dades del GEDCOM i construeix el graf"""
        logger.info("Carregant dades del GEDCOM...")
        
        # Carregar GEDCOM
        parser = GedcomParser(self.gedcom_path)
        self.persones = parser.parse()
        
        # Construir graf
        self.graph_builder.construir_graf(self.persones)
        
        logger.info(f"Carregades {len(self.persones)} persones")
    
    def run(self):
        """Executa el bot"""
        self.carregar_dades()
        logger.info("Iniciant bot...")
        self.application.run_polling()


def main():
    """Funció principal"""
    if not TELEGRAM_BOT_TOKEN or TELEGRAM_BOT_TOKEN == 'your_bot_token_here':
        logger.error("TELEGRAM_BOT_TOKEN no configurat. Crea un fitxer .env amb el token del bot.")
        return
    
    if not os.path.exists(GEDCOM_PATH):
        logger.error(f"Fitxer GEDCOM no trobat: {GEDCOM_PATH}")
        return
    
    bot = GenealogicBot(TELEGRAM_BOT_TOKEN, GEDCOM_PATH)
    bot.run()


if __name__ == "__main__":
    main()

