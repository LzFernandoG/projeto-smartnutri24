from telegram import TelegramBot
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String
from database import init_db
from scheduler import start_scheduler
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

init_db()
logger.info("Banco de dados inicializado com sucesso.")

# Defina o caminho do banco de dados
db_path = 'sqlite:///smartnutri.db'

# Inicializa o bot e passa o db_path como argumento
bot = TelegramBot(db_path=db_path)
bot.run()
start_scheduler()
logger.info("Bot e agendador iniciados com sucesso.")

# Função para inicializar o banco de dados e criar a tabela 'message_store'
def initialize_database(db_path):
    engine = create_engine(db_path)
    metadata = MetaData()
    message_store = Table(
        'message_store', metadata,
        Column('id', Integer, primary_key=True),
        Column('session_id', String),
        Column('message', String),
    )
    metadata.create_all(engine)  # Cria a tabela se não existir

# Caminho do banco de dados
db_path = 'sqlite:///chat_history.db'
initialize_database(db_path)  # Inicializa o banco de dados com a tabela necessária

# Instancia e executa o bot
bot = TelegramBot(db_path=db_path)
bot.run()
