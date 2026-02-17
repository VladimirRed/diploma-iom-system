import os

class Config:
    # Путь к базе данных SQLite
    # При желании можно заменить на: 'postgresql://user:password@localhost/dbname'
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    DB_NAME = "app.db"
    DATABASE_URL = f"sqlite:///{os.path.join(BASE_DIR, DB_NAME)}"
    
    # Настройки приложения
    APP_TITLE = "ИОМ: Система построения образовательных траекторий"
    DEBUG = True