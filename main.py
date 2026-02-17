import streamlit as st
from database.connection import engine, Base, get_db
from utils.seed_data import seed_database
# Импорт конфигурации UI
from config.ui_config import set_app_theme, render_sidebar_header
# Импорт страниц
from views import dashboard, students, diagnostics, plan_builder, reports, lesson_log, library

def init_db():
    Base.metadata.create_all(bind=engine)

def main():
    # 1. Настройка страницы (Всегда первая!)
    st.set_page_config(
        page_title="ИОМ: Образовательные траектории", 
        page_icon="🎓", 
        layout="wide",
        initial_sidebar_state="expanded" # Принудительно разворачиваем меню
    )
    
    # 2. Применяем CSS стили
    set_app_theme()
    
    # 3. Инициализация БД
    init_db()

    # 4. Отрисовка шапки сайдбара (Логотип)
    render_sidebar_header()

    # 5. САМО МЕНЮ НАВИГАЦИИ
    with st.sidebar:
        page = st.radio(
            "Навигация:",
            [
                "🏠 Главная", 
                "👶 Ученики", 
                "🩺 Диагностика", 
                "🚀 Конструктор ИОМ", 
                "📚 Библиотека методик",
                "📅 Дневник занятий",   
                "🖨️ Отчеты"
            ]
        )
        
        st.markdown("---")
        # Кнопка администрирования (внизу сайдбара)
        with st.expander("⚙️ Администрирование"):
            if st.button("🛠 Пересоздать демо-данные"):
                db = next(get_db())
                seed_database(db)
                st.toast("База знаний обновлена!", icon="✅")

    # 6. РОУТИНГ (Вывод страниц в зависимости от выбора в меню)
    if page == "🏠 Главная":
        dashboard.show_dashboard()
    elif page == "👶 Ученики":
        students.show_students_page()
    elif page == "🩺 Диагностика":
        diagnostics.show_diagnostics_page()
    elif page == "🚀 Конструктор ИОМ":
        plan_builder.show_plan_builder()
    elif page == "📚 Библиотека методик":
        library.show_library_page()
    elif page == "📅 Дневник занятий":
        lesson_log.show_log_page()
    elif page == "🖨️ Отчеты":
        reports.show_reports_page()

if __name__ == "__main__":
    main()