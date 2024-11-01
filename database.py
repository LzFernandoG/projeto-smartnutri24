# database.py
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine, Column, Integer, String, Date, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
from sqlalchemy import func
from datetime import datetime, timedelta
from sqlalchemy import Boolean

# Conectando ao banco SQLite (ou use outro db_path se preferir um arquivo)
DATABASE_URL = 'sqlite:///smartnutri.db'
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Modelo de Cliente para armazenar metas e preferências
class UserPreferences(Base):
    __tablename__ = 'user_preferences'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, unique=True, index=True)
    dietary_restrictions = Column(String, index=True)
    goal = Column(String, index=True)  # Meta do usuário (ex.: perda de peso)
    preference = Column(String, index=True)  # Preferências alimentares (ex.: vegetariano)
    restrictions = Column(String, index=True)  # Restrições alimentares (ex.: intolerância a lactose)
    health_conditions = Column(String, index=True)  # Novo campo para condições de saúde

# Criação da tabela no banco
def init_db():
    Base.metadata.create_all(bind=engine)

# Função para salvar preferências do usuário
def save_user_preferences(user_id, goal,  dietary_restrictions, preference, restrictions):
    session = SessionLocal()
    user_prefs = UserPreferences(user_id=user_id, goal=goal, preference=preference, restrictions=restrictions, dietary_restrictions=dietary_restrictions)
    session.merge(user_prefs)  # Atualiza se já existir
    session.commit()
    session.close()

# Função para buscar preferências de um usuário
def get_user_preferences(user_id):
    session = SessionLocal()
    prefs = session.query(UserPreferences).filter(UserPreferences.user_id == user_id).first()
    session.close()
    return prefs
  
# No database.py

def get_all_user_ids():
    session = SessionLocal()
    user_ids = session.query(UserPreferences.user_id).all()
    session.close()
    return [user_id[0] for user_id in user_ids]  # Extrai o ID de cada tupla retornada

class UserProgress(Base):
    __tablename__ = 'user_progress'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('user_preferences.user_id'))
    date = Column(Date, default=datetime.utcnow)
    weight = Column(Integer)  # Peso do usuário
    comments = Column(String)  # Comentários ou atualizações do usuário
    
    user = relationship("UserPreferences")

def init_db():
    Base.metadata.create_all(bind=engine)

def save_user_progress(user_id, weight, comments):
    session = SessionLocal()
    progress = UserProgress(user_id=user_id, weight=weight, comments=comments)
    session.add(progress)
    session.commit()
    session.close()
    
def get_monthly_progress(user_id):
    session = SessionLocal()
    # Obtém o progresso do último mês
    one_month_ago = datetime.utcnow() - timedelta(days=30)
    progress_entries = session.query(UserProgress).filter(
        UserProgress.user_id == user_id,
        UserProgress.date >= one_month_ago
    ).all()
    session.close()
    return progress_entries

class UserHabit(Base):
    __tablename__ = 'user_habits'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    habit = Column(String, index=True)
    completed = Column(Boolean, default=False)

def save_user_habit(user_id, habit):
    session = SessionLocal()
    user_habit = UserHabit(user_id=user_id, habit=habit, completed=True)
    session.merge(user_habit)
    session.commit()
    session.close()
    
def get_user_habits(user_id):
    session = SessionLocal()
    habits = session.query(UserHabit).filter(UserHabit.user_id == user_id).all()
    session.close()
    return habits
