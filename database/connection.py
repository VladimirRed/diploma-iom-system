from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

SQLALCHEMY_DATABASE_URL = "sqlite:///./app.db"

# --- ИСПРАВЛЕНИЕ ДЛЯ STREAMLIT CLOUD ---
# Добавлены connect_args для решения проблемы блокировки базы в облаке
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={
        "check_same_thread": False, # Отключаем проверку потоков
        "timeout": 15               # Ждем 15 секунд, если база занята
    }
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
