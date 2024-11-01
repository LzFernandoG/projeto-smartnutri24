import os
import asyncio
import logging
from dotenv import load_dotenv
from pyrogram import Client, filters
from pyrogram.handlers import MessageHandler
from pyrogram.types import Message
from pyrogram.enums import ChatAction
from nutritionist import NutritionistAgent
from database import save_user_preferences
from pyrogram.handlers import MessageHandler
from pyrogram import filters
from database import get_user_preferences
from database import save_user_progress
from database import save_user_preferences
from database import get_monthly_progress
from database import get_user_habits
import random
from schedule import daily_tips

load_dotenv()

class TelegramBot:
    def __init__(self, db_path) -> None:
        logging.basicConfig(
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            level=logging.INFO
        )
        self.logger = logging.getLogger(__name__)
        
        self.app = Client(
            "SmartNutri24Bot",
            api_id=os.getenv('TELEGRAM_API_ID'),
            api_hash=os.getenv('TELEGRAM_API_HASH'),
            bot_token=os.getenv('TELEGRAM_TOKEN'),
        )
        self.db_path = db_path
        self._setup_handle()
    
        preferences_handler = MessageHandler(self.collect_detailed_preferences, filters.command("definir_preferencias") & filters.private)
        self.app.add_handler(preferences_handler)
        
        meal_plan_handler = MessageHandler(self.send_meal_plan, filters.command("plano_alimentar") & filters.private)
        self.app.add_handler(meal_plan_handler)
        
        progress_handler = MessageHandler(self.save_progress_response, filters.command("atualizar_progresso") & filters.private)
        self.app.add_handler(progress_handler)
        
        challenge_progress_handler = MessageHandler(self.share_challenge_progress, filters.command("progresso_desafio") & filters.private)
        self.app.add_handler(challenge_progress_handler)
        
        # Comando para o usuário definir suas condições de saúde
        health_conditions_handler = MessageHandler(self.collect_health_conditions, filters.command("definir_condicoes") & filters.private)
        self.app.add_handler(health_conditions_handler)
        
        report_handler = MessageHandler(self.send_report_on_demand, filters.command("relatorio_mensal") & filters.private)
        self.app.add_handler(report_handler)
        
        habits_handler = MessageHandler(self.send_healthy_habits, filters.command("checklist_habitos") & filters.private)
        self.app.add_handler(habits_handler)
        
        complete_habit_handler = MessageHandler(self.complete_habit, filters.command("completar_habito") & filters.private)
        self.app.add_handler(complete_habit_handler)
        
        view_progress_handler = MessageHandler(self.view_habit_progress, filters.command("progresso_habitos") & filters.private)
        self.app.add_handler(view_progress_handler)
        
        tip_handler = MessageHandler(self.send_tip_on_demand, filters.command("dica") & filters.private)
        self.app.add_handler(tip_handler)
        
    def _setup_handle(self):
        start_handle = MessageHandler(
            self.start,
            filters.command("start") & filters.private
        )
        self.app.add_handler(start_handle)
        
        text_filter = filters.text & filters.private
        message_handler = MessageHandler(
            self.handle_message,
            text_filter
        )
        self.app.add_handler(message_handler)
        
        photo_filter = filters.photo & filters.private
        photo_handler = MessageHandler(self.handle_photo, filters.photo & filters.private)
        
        self.app.add_handler(photo_handler)
        
        # Dentro do método __init__ ou onde os handlers são configurados no TelegramBot
        start_handle = MessageHandler(self.set_user_preferences, filters.command("definir_preferencias") & filters.private)
        self.app.add_handler(start_handle)
    
    async def generate_meal_plan(self, user_id):
        preferences = get_user_preferences(user_id)
        health_conditions = preferences.health_conditions.split(",") if preferences.health_conditions else []

    # Exemplo de plano básico com base no objetivo e nas condições de saúde
        if preferences.goal == "perda de peso":
            if "diabetes" in health_conditions:
                meal_plan = "Plano para perda de peso com diabetes:\nCafé da manhã: Aveia com frutas de baixo índice glicêmico\nAlmoço: Salada com frango grelhado\nJantar: Legumes cozidos com peixe grelhado."
            elif "hipertensao" in health_conditions:
                meal_plan = "Plano para perda de peso com hipertensão:\nCafé da manhã: Frutas frescas e iogurte sem sal\nAlmoço: Salada com peito de frango sem sal\nJantar: Sopa de vegetais com temperos naturais."
            else:
                meal_plan = "Plano de perda de peso:\nCafé da manhã: Aveia com frutas\nAlmoço: Salada com frango grelhado\nJantar: Sopa de legumes."
        elif preferences.goal == "ganho de massa":
            if "colesterol alto" in health_conditions:
                meal_plan = "Plano para ganho de massa com colesterol alto:\nCafé da manhã: Smoothie de frutas com aveia\nAlmoço: Arroz integral com frango grelhado\nJantar: Quinoa com vegetais e peito de frango."
            else:
                meal_plan = "Plano para ganho de massa:\nCafé da manhã: Omelete com vegetais\nAlmoço: Arroz integral com carne vermelha\nJantar: Peito de frango com quinoa."
        else:
            meal_plan = "Plano básico:\nCafé da manhã: Frutas e iogurte\nAlmoço: Arroz e feijão com carne\nJantar: Sopa de vegetais."

        return meal_plan
    
    async def send_meal_plan(self, client, message: Message):
        user_id = message.from_user.id
        meal_plan = await self.generate_meal_plan(user_id)
        await message.reply_text(meal_plan)
        
    async def start(self, client: Client, message: Message):
        await message.reply_text("Olá! Eu sou sua IA Nutricionista. Envie uma mensagem ou uma foto de um prato de comida para começar.")
        self.logger.info(f"Usuário {message.from_user.id} iniciou uma conversa.")
        
    async def handle_message(self, client: Client, message: Message):
        user_id = message.from_user.id
        user_input = message.text
        
        await client.send_chat_action(chat_id=message.chat.id, action=ChatAction.TYPING)
        
        # Instancia o NutritionistAgent com session_id e db_path
        self.agent = NutritionistAgent(session_id=str(user_id), db_path=self.db_path)
        
        try:
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                self.agent.run,
                user_input
            )
        except Exception as err:
            self.logger.error(f"Erro ao processar a mensagem do usuário {user_id}: {err}", exc_info=True)
            response = "Desculpe, ocorreu um erro ao processar sua solicitação. Por favor, tente novamente."
        
        await message.reply_text(response)
        self.logger.info(f"Resposta enviada para o usuário {user_id}.")
        
    async def handle_photo(self, client, message: Message):
        user_id = message.from_user.id
        await client.send_chat_action(chat_id=message.chat.id, action=ChatAction.TYPING)
    
        # Salva a imagem recebida em uma pasta 'storage'
        storage_dir = os.path.join(os.getcwd(), 'storage')
        os.makedirs(storage_dir, exist_ok=True)
    
        photo_file_name = f"{user_id}_{message.photo.file_id}.jpg"
        photo_path = os.path.join(storage_dir, photo_file_name)
        await message.download(file_name=photo_path)
    
        # Instancia o NutritionistAgent e passa a imagem para análise
        self.agent = NutritionistAgent(session_id=str(user_id), db_path=self.db_path)
    
        try:
            # Processa a imagem usando NutritionistAgent
            response = await asyncio.get_event_loop().run_in_executor(
            None,
            self.agent.run,
            photo_path
            )
        
            # Envia a resposta de volta ao usuário
            if isinstance(response, str):
                await message.reply_text(response)
            else:
                await message.reply_text("Não foi possível processar a imagem. Por favor, envie outra foto ou tente novamente mais tarde.")

        except Exception as err:
            self.logger.error(f"Erro ao processar a imagem do usuário {user_id}: {err}", exc_info=True)
            await message.reply_text("Desculpe, ocorreu um erro ao processar sua solicitação. Por favor, tente novamente.")
    
        self.logger.info(f"Resposta enviada para o usuário {user_id}.")
        
    async def set_user_preferences(self, client: Client, message: Message):
        await message.reply_text("Quais são suas metas nutricionais? Ex: perda de peso, ganho de massa.")
        response_goal = await client.listen()  # Aguarda resposta do usuário
    
        await message.reply_text("Você tem alguma restrição alimentar? Ex: vegetariano, intolerância à lactose.")
        response_restrictions = await client.listen()  # Aguarda resposta do usuário

        # Salva as preferências usando a função de banco de dados
        user_id = message.from_user.id
        save_user_preferences(user_id, response_goal.text, response_restrictions.text)

        await message.reply_text("Suas preferências foram salvas!")
    
    async def collect_detailed_preferences(self, client, message: Message):
        user_id = message.from_user.id

        # Pergunta sobre o objetivo
        await message.reply_text("Qual é o seu objetivo nutricional? Ex: perda de peso, ganho de massa, manutenção.")
        response_goal = await client.listen()  # Aguarda resposta do usuário

        # Pergunta sobre preferências alimentares
        await message.reply_text("Você possui alguma preferência alimentar? Ex: vegetariano, vegano.")
        response_preference = await client.listen()  # Aguarda resposta do usuário

        # Pergunta sobre restrições alimentares
        await message.reply_text("Você possui alguma restrição alimentar? Ex: intolerância à lactose, alergia a nozes.")
        response_restrictions = await client.listen()  # Aguarda resposta do usuário

        # Salva as preferências detalhadas do usuário no banco de dados
        save_user_preferences(user_id, response_goal.text, response_preference.text, response_restrictions.text)

        await message.reply_text("Suas preferências detalhadas foram salvas! Agora você receberá um plano alimentar personalizado.")

    async def save_progress_response(self, client, message):
        user_id = message.from_user.id

        # Extrai o peso e o comentário do progresso (exemplo simples)
        await message.reply_text("Por favor, informe seu peso atual em kg:")
        response_weight = await client.listen()  # Aguarda o peso

        await message.reply_text("Se tiver algum comentário adicional sobre seu progresso, você pode enviá-lo agora:")
        response_comment = await client.listen()  # Aguarda o comentário

        # Salva os dados de progresso no banco
        save_user_progress(user_id, int(response_weight.text), response_comment.text)
        await message.reply_text("Progresso salvo com sucesso! Obrigado por compartilhar suas atualizações.")
        
    async def share_challenge_progress(self, client, message: Message):
        user_id = message.from_user.id
    
        await message.reply_text("Compartilhe seu progresso no desafio deste mês:")
        progress_update = await client.listen()  # Aguarda a resposta do usuário

        # Aqui você pode salvar o progresso em um banco de dados ou apenas agradecer
        await message.reply_text("Obrigado por compartilhar seu progresso! Continue firme no desafio.")
        
    async def collect_health_conditions(self, client, message: Message):
        user_id = message.from_user.id

        await message.reply_text("Você tem alguma condição de saúde específica? Ex: diabetes, hipertensão, colesterol alto. Responda listando as condições, separadas por vírgula.")
        response_conditions = await client.listen()  # Aguarda a resposta do usuário

        # Salva as condições de saúde junto com as preferências existentes
        preferences = get_user_preferences(user_id)
        save_user_preferences(user_id, preferences.goal, preferences.preference, preferences.restrictions, response_conditions.text)

        await message.reply_text("Suas condições de saúde foram salvas! Seu plano será adaptado conforme necessário.")
    
    async def generate_monthly_report(self, user_id):
        progress_entries = get_monthly_progress(user_id)
        if not progress_entries:
            return "Não há atualizações de progresso para o último mês."

        # Exemplo de análise de progresso
        initial_weight = progress_entries[0].weight
        latest_weight = progress_entries[-1].weight
        weight_change = latest_weight - initial_weight

        insights = f"Relatório Mensal:\n\nPeso inicial: {initial_weight} kg\nPeso atual: {latest_weight} kg\n"
        insights += f"Variação de peso: {weight_change} kg\n"

        # Adicionar insights com base nas condições de saúde
        preferences = get_user_preferences(user_id)
        if preferences and "diabetes" in preferences.health_conditions.lower():
            insights += "\nDica: Continue monitorando o índice glicêmico dos alimentos para ajudar no controle da diabetes."

        insights += "\n\nContinue registrando seu progresso para ver mais resultados positivos!"

        return insights
    
    async def send_report_on_demand(self, client, message: Message):
        user_id = message.from_user.id
        report = await self.generate_monthly_report(user_id)
        await message.reply_text(report)
        
    
healthy_habits = [
    "Beber pelo menos 2 litros de água por dia",
    "Comer frutas e vegetais em todas as refeições",
    "Fazer exercícios físicos por 30 minutos",
    "Evitar alimentos processados e açucarados",
    "Dormir pelo menos 7-8 horas por noite",
    "Reduzir o consumo de bebidas açucaradas",
    "Praticar mindfulness ou meditação",
    "Evitar o uso excessivo de dispositivos eletrônicos à noite"
]
    
async def send_healthy_habits(self, client, message: Message):
    checklist = "Checklist de Hábitos Saudáveis:\n\n" + "\n".join([f"- {habit}" for habit in healthy_habits])
    await message.reply_text(checklist + "\n\nTente completar esses hábitos diariamente para uma saúde melhor!")
    
    async def complete_habit(self, client, message: Message):
        user_id = message.from_user.id

        await message.reply_text("Qual hábito você completou hoje? Envie o nome exato do hábito.")
        habit_response = await client.listen()  # Aguarda o hábito completado

        from database import save_user_habit
        save_user_habit(user_id, habit_response.text)

        await message.reply_text(f"Parabéns por completar o hábito '{habit_response.text}'! Continue assim!")
        
    async def view_habit_progress(self, client, message: Message):
        user_id = message.from_user.id
        habits = get_user_habits(user_id)

        if not habits:
            await message.reply_text("Você ainda não completou nenhum hábito.")
            return

        progress_message = "Progresso dos Hábitos Saudáveis:\n\n"
        for habit in habits:
            status = "Completado" if habit.completed else "Não completado"
            progress_message += f"- {habit.habit}: {status}\n"

        await message.reply_text(progress_message)

async def send_tip_on_demand(self, client, message: Message):
    user_id = message.from_user.id
    preferences = get_user_preferences(user_id)

    if not preferences or not preferences.goal:
        await message.reply_text("Por favor, configure suas preferências primeiro com o comando /definir_preferencias.")
        return

    tips = daily_tips.get(preferences.goal.lower(), [])
    if tips:
        tip = random.choice(tips)
        await message.reply_text(f"Dica para {preferences.goal}:\n\n{tip}")
    else:
        await message.reply_text("Ainda não há dicas disponíveis para o seu objetivo.")

def run(self):
    self.logger.info('Bot foi iniciado')
    self.app.run()