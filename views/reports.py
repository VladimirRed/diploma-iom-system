import streamlit as st
from database.connection import get_db
from services.student_service import StudentService
from database.models import EducationalPlan, PlanStatus
from services.log_service import LogService # <--- Импортируем сервис логов
from utils.report_generator import generate_word_report

def show_reports_page():
    st.header("🖨️ Отчетность и Экспорт")

    db = next(get_db())
    student_service = StudentService(db)
    # Инициализируем сервис логов
    log_service = LogService(db)

    students = student_service.get_all_students()
    if not students:
        st.warning("Нет учеников."); return

    student_options = {s.id: f"{s.full_name}" for s in students}
    selected_student_id = st.selectbox("Ученик:", list(student_options.keys()), format_func=lambda x: student_options[x])

    # Ищем активный план
    current_plan = db.query(EducationalPlan)\
        .filter(EducationalPlan.student_id == selected_student_id)\
        .filter(EducationalPlan.status == PlanStatus.ACTIVE)\
        .order_by(EducationalPlan.created_at.desc())\
        .first()

    if not current_plan:
        st.info("У ученика нет активного плана."); return

    # Данные плана
    items = current_plan.items
    
    # НОВОЕ: Получаем историю журнала
    logs = log_service.get_all_logs_for_plan(current_plan.id)

    st.markdown("---")
    st.subheader(f"План: {current_plan.goal_description}")
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Упражнений", len(items))
    c2.metric("Проведено занятий", len(set([l.date for l in logs]))) # Уникальные даты
    # Средняя оценка
    avg_score = sum([l.performance_score for l in logs]) / len(logs) if logs else 0
    c3.metric("Средний балл", f"{avg_score:.1f}")

    # Предпросмотр журнала
    with st.expander("Предпросмотр данных журнала"):
        if logs:
            for log in logs[:5]: # Показываем последние 5
                st.write(f"{log.date}: {log.item.exercise.title} — {log.performance_score}")
        else:
            st.write("Журнал пуст.")

    # Генерация
    student = student_service.get_student_by_id(selected_student_id)
    
    if st.button("📄 Скачать полный отчет (.docx)"):
        # Передаем logs в генератор
        file_buffer = generate_word_report(student, current_plan, items, logs)
        
        st.download_button(
            label="Скачать файл",
            data=file_buffer,
            file_name=f"Report_{student.full_name}.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )