import streamlit as st
import pandas as pd
import plotly.express as px
from database.connection import get_db
from services.student_service import StudentService
from database.models import Exercise, SkillCategory, EducationalPlan

def show_dashboard():
    # Приветственный баннер
    st.markdown("""
    <div style="background-color: #4A90E2; padding: 20px; border-radius: 10px; color: white; margin-bottom: 25px;">
        <h2 style="color: white; margin:0;">👋 Добро пожаловать, Коллега!</h2>
        <p style="margin:5px 0 0 0;">Система готова к работе. Выберите действие в меню слева или просмотрите сводку ниже.</p>
    </div>
    """, unsafe_allow_html=True)
    
    db = next(get_db())
    student_service = StudentService(db)
    
    # Собираем статистику
    total_students = student_service.get_total_count()
    total_exercises = db.query(Exercise).count()
    total_skills = db.query(SkillCategory).filter(SkillCategory.parent_id != None).count()
    active_plans = db.query(EducationalPlan).filter(EducationalPlan.status == "active").count()
    
    # Визуализация метрик (KPI)
    c1, c2, c3, c4 = st.columns(4)
    
    with c1:
        st.metric(label="👶 Учеников", value=total_students, delta="Активные")
    with c2:
        st.metric(label="📚 Методик", value=total_exercises, delta="В базе")
    with c3:
        st.metric(label="🧠 Навыков", value=total_skills)
    with c4:
        st.metric(label="🚀 Активных планов", value=active_plans)

    st.markdown("---")

    # Быстрые действия и графики
    col_left, col_right = st.columns([2, 1])
    
    with col_left:
        st.subheader("📊 Распределение по диагнозам")
        students = student_service.get_all_students()
        if students:
            # Считаем диагнозы
            diag_counts = {}
            for s in students:
                d = s.diagnosis_code or "Не указан"
                diag_counts[d] = diag_counts.get(d, 0) + 1
            
            df_diag = pd.DataFrame(list(diag_counts.items()), columns=["Диагноз", "Количество"])
            
            fig = px.pie(df_diag, values='Количество', names='Диагноз', hole=0.4, color_discrete_sequence=px.colors.sequential.RdBu)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Нет данных для графика.")

    with col_right:
        st.subheader("⚡ Быстрый старт")
        with st.container():
            st.info("💡 **Совет дня:**\nРегулярное обновление дневника повышает точность отчетов.")
            
            st.markdown("#### Что сделать сейчас?")
            st.markdown("- [➕ Добавить ученика](#)")
            st.markdown("- [🩺 Провести диагностику](#)")
            st.markdown("- [📅 Заполнить журнал](#)")