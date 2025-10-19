"""
Bot de Telegram per al sistema genealògic
"""

import os
import json
import logging
import asyncio
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
            'k': 'Josep Maria Taulé Figueras Piñol'
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
        self.application.add_handler(CommandHandler("grup", self.grup_command))
        self.application.add_handler(CommandHandler("kintos", self.kintos_command))
        self.application.add_handler(CommandHandler("identifica", self.identifica_command))
        self.application.add_handler(CommandHandler("apodos", self.apodos_command))
        self.application.add_handler(CallbackQueryHandler(self.button_callback))
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler per al comando /start"""
        user = update.effective_user
        
        # Verificar si l'usuari ja està identificat
        usuari = self.data_manager.obtenir_usuari(str(user.id))
        
        if usuari:
            await update.message.reply_text(
                f"👋 Hola {user.first_name}!\n\n"
                f"Ja estàs identificat com: *{usuari.nom}*\n\n"
                f"Usa `/help` per veure les comandes disponibles.",
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text(
                f"👋 Hola {user.first_name}!\n\n"
                f"Benvingut al bot genealògic! 🧬\n\n"
                f"Primer has d'identificar-te com una de les persones de l'arbre familiar.\n\n"
                f"Usa `/identifica` per començar.",
                parse_mode='Markdown'
            )
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler per al comando /ajuda"""
        help_text = """
🧬 *Bot Genealògic - Comandes disponibles:*


/kintos - Mostra les teves relacions amb el grup

/tots - Mostra matriu de totes les relacions
/apodos - Mostra tots els apodos disponibles




        """
        await update.message.reply_text(help_text, parse_mode='Markdown')
    
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
                "❌ No estàs identificat.\n\n"
                "Usa `/identifica` per identificar-te com una persona de l'arbre."
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
                "❌ No estàs identificat.\n\n"
                "Usa `/identifica` per identificar-te com una persona de l'arbre."
            )
            return
        
        if not context.args:
            await update.message.reply_text(
                "✖️ Has d'especificar dos noms.\n\n"
                "Exemple: `/relacio Taule Montse`",
                parse_mode='Markdown'
            )
            return
        
        # Buscar la persona
        nom_buscat = " ".join(context.args)
        persona_trobada = self.data_manager.buscar_persona_per_nom(nom_buscat)
        
        if not persona_trobada:
            await update.message.reply_text(
                f"❌ No s'ha trobat cap persona amb el nom '{nom_buscat}'.\n\n"
                f"Usa `/grup` per veure totes les persones disponibles."
            )
            return
        
        # Calcular totes les relacions possibles
        relacions = self._calcular_totes_relacions(usuari.persona_id, persona_trobada["id"])
        
        if not relacions:
            await update.message.reply_text(
                f"❌ No s'ha pogut calcular la relació amb {persona_trobada['nom']}."
            )
            return
        
        # Les relacions ja venen ordenades per importància genealògica
        # Separar per tipus per mostrar correctament
        relacions_sanguinies = [r for r in relacions if r.tipus == "sanguinia"]
        relacions_no_sanguinies = [r for r in relacions if r.tipus == "no_sanguinia"]
        
        # Determinar quines relacions mostrar
        if relacions_sanguinies:
            # Mostrar TOTES les relacions sanguínies (ja ordenades per importància)
            relacions_a_mostrar = relacions_sanguinies
            # Generar gotes de sang dinàmiques
            gotes_sang = "🩸" * len(relacions_sanguinies)
            text = f"{gotes_sang} *Relacions sanguínies amb {persona_trobada['nom']}:*\n\n"
        else:
            # Mostrar les 3 millors relacions per afinitat
            relacions_a_mostrar = relacions_no_sanguinies[:3]
            text = f"💍 *Relació amb {persona_trobada['nom']}:*\n"
            text += f"*Nota:* No hi ha relacions sanguínies directes. Mostrant les millors relacions per afinitat:\n\n"
        
        # Dividir en múltiples missatges si és massa llarg
        if len(relacions_a_mostrar) > 1 or len(text) > 3000:
            # Enviar missatge inicial
            await self._send_message_safe(update, text)
            
            # Enviar cada relació per separat amb delay
            for i, relacio in enumerate(relacions_a_mostrar):
                if i > 0:  # Delay entre missatges
                    await asyncio.sleep(1.5)
                
                relacio_text = f"**Camí {i+1}:**\n\n"
                
                emoji = "🩸" if relacio.tipus == "sanguinia" else "💍"
                cami_formatat = self._formatar_cami_relacio(relacio.cami)
                
                # Sistema simplificat - sense càlculs complexos de pesos
                
                # Determinar si és relació pura per mostrar text especial
                es_pura = self._es_relacio_pura(relacio.cami)
                if es_pura and relacio.tipus == "sanguinia":
                    grau_text = "cosins sanguínis directes"
                else:
                    # Arreglar format si és una tupla
                    if isinstance(relacio.grau, tuple):
                        grau_text = "Parents llunyans"
                    else:
                        grau_text = relacio.grau
                
                # Calcular pes simple
                pes = 1000 if relacio.tipus == "sanguinia" else 100
                pes += 1000 // relacio.distancia
                
                relacio_text += f"• **Relació:** {grau_text}\n"
                relacio_text += f"• **Tipus:** {relacio.tipus}\n"
                relacio_text += f"• **Distància:** {relacio.distancia} passos\n"
                relacio_text += f"• **Pes:** {pes}\n"
                relacio_text += f"• **Camí:** {cami_formatat}"
                
                await self._send_message_safe(update, relacio_text)
        else:
            # Mostrar totes les relacions en un sol missatge
            for i, relacio in enumerate(relacions_a_mostrar):
                if len(relacions_a_mostrar) > 1:
                    text += f"**Camí {i+1}:**\n"
                
                emoji = "🩸" if relacio.tipus == "sanguinia" else "💍"
                cami_formatat = self._formatar_cami_relacio(relacio.cami)
                
                # Sistema simplificat - sense càlculs complexos de pesos
                
                # Determinar si és relació pura per mostrar text especial
                es_pura = self._es_relacio_pura(relacio.cami)
                if es_pura and relacio.tipus == "sanguinia":
                    grau_text = "cosins sanguínis directes"
                else:
                    # Arreglar format si és una tupla
                    if isinstance(relacio.grau, tuple):
                        grau_text = "Parents llunyans"
                    else:
                        grau_text = relacio.grau
                
                text += f"• **Relació:** {grau_text}\n"
                text += f"• **Tipus:** {relacio.tipus}\n"
                text += f"• **Distància:** {relacio.distancia} passos\n"
                text += f"• **Camí:** {cami_formatat}\n\n"
            
            await self._send_message_safe(update, text)
    
    async def grup_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler per al comando /grup"""
        user = update.effective_user
        usuari = self.data_manager.obtenir_usuari(str(user.id))
        
        if not usuari:
            await update.message.reply_text(
                "❌ No estàs identificat.\n\n"
                "Usa `/identifica` per identificar-te com una persona de l'arbre."
            )
            return
        
        persones = self.data_manager.llistar_persones_disponibles()
        
        if not persones:
            await update.message.reply_text("❌ No s'han trobat persones disponibles.")
            return
        
        # Utilitzar cache complet per /grup
        grup_cache_file = 'data/grup_cache.json'
        if not os.path.exists(grup_cache_file):
            await update.message.reply_text("❌ Cache no disponible. Executa el script de generació.")
            return
        
        with open(grup_cache_file, 'r', encoding='utf-8') as f:
            grup_cache = json.load(f)
        
        if usuari.persona_id not in grup_cache:
            await update.message.reply_text("❌ No s'ha trobat cache per aquest usuari.")
            return
        
        # Mostrar resultats des del cache
        text = f"🧬 *Les teves relacions amb el grup Kintos:*\n\n"
        
        relacions_cache = grup_cache[usuari.persona_id]
        
        for item in relacions_cache:
            persona_altra = item['persona_nom']
            relacio_data = item['relacio']
            pes = item['pes']
            num_gotes = item['num_gotes']
            
            # Generar emoji dinàmic sense espais
            if num_gotes > 0:
                emoji = "🩸" * num_gotes
            else:
                emoji = "💍"
            
            text += f"{emoji} *{persona_altra}*\n"
            text += f"   {relacio_data['grau']} (distància: {relacio_data['distancia']} | Pes: {pes})\n\n"
        
        await self._send_long_message(update, text)
    
    async def kintos_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler per al comando /kintos - mostra matriu de relacions entre tots els Kintos"""
        persones = self.data_manager.llistar_persones_disponibles()
        
        if not persones:
            await update.message.reply_text("❌ No s'han trobat persones disponibles.")
            return
        
        # Utilitzar cache dinàmic per /kintos
        kintos_cache_file = 'data/kintos_dynamic_cache.json'
        
        # Carregar cache existent o crear nou
        kintos_cache = {}
        if os.path.exists(kintos_cache_file):
            try:
                with open(kintos_cache_file, 'r', encoding='utf-8') as f:
                    kintos_cache = json.load(f)
            except:
                kintos_cache = {}
        
        # Organitzar per persona
        text = "🧬 *Matriu de relacions Kintos*\n\n"
        
        # Llistar persones que falten al cache
        persones_faltants = []
        
        for persona in persones:
            persona_id = persona["id"]
            persona_nom = persona["nom"]
            
            if persona_id in kintos_cache:
                relacions_persona = kintos_cache[persona_id]
                
                text += f"👤 *{persona_nom}:*\n"
                for item in relacions_persona:
                    persona_altra = item['persona_nom']
                    relacio_data = item['relacio']
                    num_gotes = item['num_gotes']
                    
                    # Generar emoji dinàmic
                    if num_gotes > 0:
                        emoji = "🩸" * num_gotes
                    else:
                        emoji = "💍"
                    
                    text += f"  {emoji} {persona_altra} ({relacio_data['grau']}, dist:{relacio_data['distancia']})\n"
                text += "\n"
            else:
                # Marcar per calcular en segon pla
                persones_faltants.append(persona)
                text += f"👤 *{persona_nom}:*\n"
                text += f"  ⏳ Calculant relacions...\n\n"
        
        # Si hi ha persones faltants, calcular-les en segon pla
        if persones_faltants:
            # Executar càlcul en segon pla
            asyncio.create_task(self._actualitzar_kintos_cache_async(persones_faltants, kintos_cache_file))
        
        # Enviar missatge
        await self._send_long_message(update, text)
    
    async def _actualitzar_kintos_cache_async(self, persones_faltants, cache_file):
        """Actualitza el cache de kintos en segon pla"""
        try:
            print(f"🔄 Actualitzant cache per {len(persones_faltants)} persones...")
            
            # Carregar cache existent
            kintos_cache = {}
            if os.path.exists(cache_file):
                try:
                    with open(cache_file, 'r', encoding='utf-8') as f:
                        kintos_cache = json.load(f)
                except:
                    kintos_cache = {}
            
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
                kintos_cache[persona_id] = persona_relacions
                
                # Guardar fitxer després de cada persona
                with open(cache_file, 'w', encoding='utf-8') as f:
                    json.dump(kintos_cache, f, indent=2, ensure_ascii=False)
                
                print(f"  ✅ {persona_nom} completat")
            
            print(f"🎉 Cache actualitzat completament!")
            
        except Exception as e:
            print(f"❌ Error actualitzant cache: {e}")
    
    async def apodos_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler per al comando /apodos"""
        apodos_data = self.data_manager.llistar_apodos_disponibles()
        
        if not apodos_data:
            await update.message.reply_text("❌ No s'han trobat apodos disponibles.")
            return
        
        text = "👥 *Apodos i malnoms disponibles:*\n\n"
        
        for persona_data in apodos_data:
            nom = persona_data["nom"]
            apodos = persona_data["apodos"]
            apodos_str = ", ".join(apodos)
            text += f"• **{nom}**\n"
            text += f"  _{apodos_str}_\n\n"
        
        text += "💡 *Pots usar qualsevol apodo per buscar relacions!*\n"
        text += "Exemple: `/relacio amb Edu` o `/relacio amb Montse`"
        
        await update.message.reply_text(text)
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler per a missatges de text"""
        await update.message.reply_text(
            "🤔 No he entès el missatge.\n\n"
            "Usa `/ajuda` per veure les comandes disponibles."
        )
    
    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler per a callbacks de botons"""
        query = update.callback_query
        await query.answer()
        
        if query.data.startswith("identifica_"):
            persona_id = query.data.split("_", 1)[1]
            await self._processar_identificacio(query, persona_id)
    
    async def _processar_identificacio(self, query, persona_id: str):
        """Processa la identificació d'un usuari"""
        user = query.from_user
        user_id = str(user.id)
        persona_data = self.data_manager.carregar_persones().get(persona_id)
        
        if not persona_data:
            await query.edit_message_text("❌ Error: Persona no trobada.")
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
                f"Usa `/help` per veure les comandes disponibles.",
                parse_mode='Markdown'
            )
        else:
            logger.error(f"Error: No s'ha pogut guardar la identificació per usuari {user_id}")
            await query.edit_message_text("❌ Error: No s'ha pogut guardar la identificació.")
    
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
            
            # Per cada grup, seleccionar només la millor relació
            resultat.append(grup_relacions[0])
        
        # Ordenar per tipus (sanguínies primer) i després per distància
        resultat.sort(key=lambda r: (r.tipus != "sanguinia", r.distancia))
        
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
            await update.message.reply_text(text)
        except RetryAfter as e:
            logger.warning(f"Rate limited, esperant {e.retry_after} segons...")
            await asyncio.sleep(e.retry_after)
            await update.message.reply_text(text)
        except Exception as e:
            logger.error(f"Error enviant missatge: {e}")
            # Si el missatge és massa llarg, dividir-lo
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

