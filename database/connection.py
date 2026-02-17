from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from config.settings import Config

# Создаем движок
# connect_args={"check_same_thread": False} нужно только для SQLite + Streamlit
engine = create_engine(
    Config.DATABASE_URL, 
    connect_args={"check_same_thread": False} if "sqlite" in Config.DATABASE_URL else {}
)

# Фабрика сессий
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Базовый класс для моделей
Base = declarative_base()

def get_db():
    """
    Генератор сессии базы данных.
    Используется для безопасного получения и закрытия сессии.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()