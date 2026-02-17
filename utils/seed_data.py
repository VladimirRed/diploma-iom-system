from sqlalchemy.orm import Session
from database.models import SkillCategory, Exercise, User, UserRole
from config.constants import MEDICAL_TAGS

def seed_database(db: Session):
    if db.query(SkillCategory).first():
        print("База данных уже содержит данные.")
        return

    print("Начинаем масштабное наполнение базы данных...")

    # 1. Админ
    admin = User(username="admin", password_hash="admin123", full_name="Администратор", role=UserRole.ADMIN)
    db.add(admin)

    # 2. Категории
    cat_cognitive = SkillCategory(name="Когнитивное развитие")
    cat_motor = SkillCategory(name="Моторное развитие")
    cat_social = SkillCategory(name="Социально-коммуникативное")
    db.add_all([cat_cognitive, cat_motor, cat_social])
    db.commit()

    # Навыки
    s_memory = SkillCategory(name="Слухоречевая память", parent_id=cat_cognitive.id)
    s_attention = SkillCategory(name="Концентрация внимания", parent_id=cat_cognitive.id)
    s_logic = SkillCategory(name="Логическое мышление", parent_id=cat_cognitive.id)
    
    s_fine = SkillCategory(name="Мелкая моторика", parent_id=cat_motor.id)
    s_gross = SkillCategory(name="Крупная моторика (координация)", parent_id=cat_motor.id)
    s_balance = SkillCategory(name="Баланс и вестибулярный аппарат", parent_id=cat_motor.id)

    db.add_all([s_memory, s_attention, s_logic, s_fine, s_gross, s_balance])
    db.commit()

    # 3. Упражнения с ПРОТИВОПОКАЗАНИЯМИ
    # Используем теги из config/constants.py
    
    exercises = [
        # --- БЛОК 1: ВНИМАНИЕ (Компьютерные и визуальные) ---
        Exercise(
            title="Интерактивная игра 'Найди отличие' (На планшете)",
            description="Ребенок ищет отличия на ярком мигающем экране.",
            skill_id=s_attention.id,
            difficulty_level=2,
            materials="Планшет",
            effectiveness_score=8.0,
            # ОПАСНО ДЛЯ ЭПИЛЕПСИКОВ и СЛАБОВИДЯЩИХ
            contraindications="Эпилепсия/Судорожная готовность,Нарушение зрения" 
        ),
        Exercise(
            title="Корректурная проба (Бумажная)",
            description="Зачеркивать определенные буквы в тексте.",
            skill_id=s_attention.id,
            difficulty_level=3,
            materials="Бланк, карандаш",
            effectiveness_score=7.5,
            contraindications="" # Безопасно
        ),

        # --- БЛОК 2: КРУПНАЯ МОТОРИКА (Активные) ---
        Exercise(
            title="Прыжки на батуте",
            description="Серия прыжков с выполнением команд.",
            skill_id=s_gross.id,
            difficulty_level=4,
            materials="Батут",
            effectiveness_score=9.5,
            # ОПАСНО ПРИ НОДА и СЕРДЦЕ
            contraindications="Нарушения опорно-двигательного аппарата (НОДА),Порок сердца / Кардиология"
        ),
        Exercise(
            title="Полоса препятствий (Ползание)",
            description="Проползти под стульями, перешагнуть кубики.",
            skill_id=s_gross.id,
            difficulty_level=2,
            materials="Мебель, кубики",
            effectiveness_score=8.0,
            contraindications="Нарушения опорно-двигательного аппарата (НОДА)" # Менее опасно, но все же
        ),

        # --- БЛОК 3: БАЛАНС ---
        Exercise(
            title="Балансир 'Сова' (Качели)",
            description="Удержание равновесия на неустойчивой платформе.",
            skill_id=s_balance.id,
            difficulty_level=5,
            materials="Доска-балансир",
            effectiveness_score=9.0,
            contraindications="Эпилепсия/Судорожная готовность,Нарушения опорно-двигательного аппарата (НОДА)"
        ),
        Exercise(
            title="Ходьба по линии",
            description="Пройти по скотчу, наклееному на полу.",
            skill_id=s_balance.id,
            difficulty_level=1,
            materials="Скотч",
            effectiveness_score=6.0,
            contraindications="" # Безопасно для всех
        ),

        # --- БЛОК 4: МЕЛКАЯ МОТОРИКА ---
        Exercise(
            title="Сортировка мелких бусин",
            description="Разложить бисер пинцетом.",
            skill_id=s_fine.id,
            difficulty_level=4,
            materials="Бисер, пинцет",
            effectiveness_score=7.0,
            # ОПАСНО ПРИ ПЛОХОМ ЗРЕНИИ (сильная нагрузка)
            contraindications="Нарушение зрения"
        ),
        Exercise(
            title="Лепка из пластилина",
            description="Катание шариков и колбасок.",
            skill_id=s_fine.id,
            difficulty_level=1,
            materials="Пластилин",
            effectiveness_score=8.5,
            contraindications=""
        ),

        # --- БЛОК 5: ДЫХАНИЕ И ПАМЯТЬ ---
        Exercise(
            title="Дыхательная гимнастика 'Надуй шар'",
            description="Интенсивное надувание шаров на скорость.",
            skill_id=s_memory.id, # Косвенно (снабжение мозга кислородом)
            difficulty_level=3,
            materials="Шарики",
            effectiveness_score=6.5,
            # ОПАСНО ПРИ АСТМЕ И СЕРДЦЕ
            contraindications="Бронхиальная астма,Порок сердца / Кардиология"
        ),
        Exercise(
            title="Заучивание четверостиший",
            description="Повторение стихов за педагогом.",
            skill_id=s_memory.id,
            difficulty_level=3,
            materials="Карточки",
            effectiveness_score=8.0,
            contraindications=""
        )
    ]

    db.add_all(exercises)
    db.commit()
    print("База наполнена 10 методиками с системой противопоказаний!")