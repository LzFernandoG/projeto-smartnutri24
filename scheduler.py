import schedule
import time
from threading import Thread
from database import get_user_preferences
from telegram import TelegramBot
from database import get_all_user_ids
import random
import asyncio

def send_monthly_progress_request():
    bot = TelegramBot()
    user_ids = get_all_user_ids()  # Função que busca todos os IDs de usuários

    for user_id in user_ids:
        bot.app.send_message(user_id, "Olá! Estamos no fim do mês e gostaríamos de saber como foi seu progresso. Por favor, responda com seu peso atual e qualquer outro comentário sobre sua evolução."
                                        "Por favor, utilize o comando /atualizar_progresso para enviar seu peso atual e qualquer outro comentário sobre sua evolução.")
def start_scheduler():
    # Envio diário
    schedule.every().day.at("08:00").do(send_daily_messages)

    # Envio mensal (último dia do mês)
    schedule.every().month.at("08:00").do(send_monthly_progress_request)

    # Envio diário das dicas às 8h
    schedule.every().day.at("08:00").do(send_daily_tip)

    while True:
        schedule.run_pending()
        time.sleep(60)

# Função que envia a mensagem diária de acordo com as metas do cliente
def send_daily_messages():
    bot = TelegramBot()
    user_ids = [user.user_id for user in get_all_user_ids()]  # Pega todos os IDs de usuários no banco
    
    for user_id in user_ids:
        preferences = get_user_preferences(user_id)
        message = f"Olá! Aqui estão algumas dicas para alcançar seu objetivo de {preferences.goal}. Lembre-se de seguir seu plano alimentar e se manter hidratado!"
        bot.app.send_message(user_id, message)  # Envia a mensagem para cada usuário

def start_scheduler():
     # Envio diário
    schedule.every().day.at("08:00").do(send_daily_messages)

    # Envio do desafio mensal no primeiro dia de cada mês
    schedule.every().month.at("08:00").do(send_monthly_challenge)
    
    # Envio do relatório mensal no último dia do mês
    schedule.every().month.at("08:00").do(send_monthly_report)

    while True:
        schedule.run_pending()
        time.sleep(60)
    
challenges = [
    {"title": "Beber mais água", "description": "Beba pelo menos 8 copos de água por dia para melhorar sua hidratação e disposição."},
    {"title": "Aumentar ingestão de fibras", "description": "Inclua frutas, verduras e grãos integrais nas refeições para melhorar sua digestão."},
    {"title": "Reduzir o consumo de açúcar", "description": "Tente evitar alimentos com alto teor de açúcar e escolha opções mais saudáveis."},
    {"title": "Praticar exercícios leves diariamente", "description": "Realize 30 minutos de caminhada ou outra atividade física leve todos os dias."},
    # Adicione mais desafios se desejar
]

def get_monthly_challenge():
    return random.choice(challenges)

def send_monthly_challenge():
    bot = TelegramBot()
    user_ids = get_all_user_ids()  # Função que busca todos os IDs de usuários
    challenge = get_monthly_challenge()

    for user_id in user_ids:
        bot.app.send_message(
            user_id,
            f"Desafio do Mês: {challenge['title']}\n\n{challenge['description']}\n\n"
            "Este é o seu desafio para o mês! Use o comando /progresso_desafio para compartilhar seu progresso sempre que quiser."
        )

def send_monthly_report():
    bot = TelegramBot()
    user_ids = get_all_user_ids()  # Função que busca todos os IDs de usuários

    for user_id in user_ids:
        report = asyncio.run(bot.generate_monthly_report(user_id))
        bot.app.send_message(
            user_id,
            report
        )
        

daily_tips = {
    "perda de peso": [
        "Para o café da manhã, tente incluir alimentos ricos em fibras, como aveia e frutas.",
        "Beba água antes das refeições para ajudar na saciedade.",
        "Evite bebidas açucaradas e prefira sucos naturais ou água saborizada.",
        "Para o jantar, escolha uma refeição leve, como salada com proteínas magras."
    ],
    "ganho de massa": [
        "Inclua uma boa fonte de proteína em cada refeição, como ovos, frango ou peixe.",
        "Para o café da manhã, experimente um smoothie de frutas com whey protein.",
        "Após os treinos, consuma uma refeição rica em carboidratos e proteínas.",
        "Lanches com pasta de amendoim e aveia são ótimos para ganho de massa."
    ],
    "manutenção": [
        "Mantenha uma dieta equilibrada com frutas, vegetais e proteínas em cada refeição.",
        "Beba água regularmente ao longo do dia para manter a hidratação.",
        "Inclua lanches saudáveis, como iogurte com frutas ou castanhas.",
        "Para o almoço, escolha uma porção de carboidratos integrais, proteínas e salada."
    ]
}

# scheduler.py

def send_daily_tip():
    bot = TelegramBot()
    user_ids = get_all_user_ids()

    for user_id in user_ids:
        preferences = get_user_preferences(user_id)
        if preferences and preferences.goal:
            tips = daily_tips.get(preferences.goal.lower(), [])
            if tips:
                tip = random.choice(tips)
                bot.app.send_message(
                    user_id,
                    f"Bom dia! 🌞 Aqui está uma dica para {preferences.goal}:\n\n{tip}"
                )

# Inicia o agendador em uma nova thread
scheduler_thread = Thread(target=start_scheduler)
scheduler_thread.start()
