import streamlit as st
import datetime
import pandas as pd
from database.connection import get_db
from database.models import EducationalPlan, PlanStatus, Exercise
from services.student_service import StudentService
from services.trajectory_service import TrajectoryService

def show_plan_builder():
    st.header("🚀 Конструктор траектории (ИОМ)")

    db = next(get_db())
    student_service = StudentService(db)
    trajectory_service = TrajectoryService(db)

    # Выбор ученика
    students = student_service.get_all_students()
    if not students:
        st.warning("Нет учеников."); return

    student_options = {s.id: f"{s.full_name}" for s in students}
    
    # При смене ученика ключи интерфейса обновятся
    selected_student_id = st.selectbox(
        "Выберите ученика:", 
        options=list(student_options.keys()), 
        format_func=lambda x: student_options[x],
        key="pb_student_select"
    )

    st.markdown("---")

    # --- УПРАВЛЕНИЕ СОСТОЯНИЕМ (State Management) ---
    session_key = f"plan_data_{selected_student_id}"

    # Если данных в памяти нет, пытаемся загрузить АКТИВНЫЙ план из БД
    if session_key not in st.session_state:
        active_plan = db.query(EducationalPlan).filter(
            EducationalPlan.student_id == selected_student_id,
            EducationalPlan.status == PlanStatus.ACTIVE
        ).order_by(EducationalPlan.created_at.desc()).first() # Берем самый свежий

        if active_plan:
            # Превращаем сохраненный план в список для редактора
            loaded_data = []
            for item in active_plan.items:
                ex = item.exercise
                loaded_data.append({
                    "id": ex.id,
                    "title": ex.title,
                    "skill": ex.skill.name if ex.skill else "—",
                    "score": ex.effectiveness_score,
                    "materials": ex.materials,
                    "selected": True # Они выбраны, так как уже в плане
                })
            st.session_state[session_key] = loaded_data
            st.info(f"📂 Загружен текущий план: {len(loaded_data)} упражнений.")
        else:
            st.session_state[session_key] = [] # Плана нет

    # --- КНОПКИ ---
    col1, col2 = st.columns([1, 3])
    with col1:
        # Если список пуст - кнопка "Сгенерировать". Если не пуст - "Пересоздать"
        has_data = len(st.session_state[session_key]) > 0
        label = "♻️ Пересоздать (Новый поиск)" if has_data else "🤖 Сгенерировать рекомендации"
        
        if st.button(label, type="primary"):
            # Запускаем алгоритм
            weak_points = trajectory_service.analyze_diagnostic(selected_student_id, threshold=3.5)
            
            if not weak_points:
                st.warning("Дефицитов не найдено или нет диагностики.")
                st.session_state[session_key] = []
            else:
                # Получаем новые рекомендации
                recs_objects = trajectory_service.get_recommendations(selected_student_id, list(weak_points.keys()))
                
                # Конвертируем в данные для таблицы
                new_data = []
                for ex in recs_objects:
                    new_data.append({
                        "id": ex.id,
                        "title": ex.title,
                        "skill": ex.skill.name if ex.skill else "—",
                        "score": ex.effectiveness_score,
                        "materials": ex.materials,
                        "selected": True # По умолчанию предлагаем все
                    })
                st.session_state[session_key] = new_data
                st.toast(f"Алгоритм предложил {len(new_data)} вариантов", icon="🤖")
                st.rerun()

    # --- ТАБЛИЦА ---
    current_data = st.session_state[session_key]

    if current_data:
        st.subheader("Состав программы")
        
        # Форма сохранения
        with st.form("plan_save_form"):
            c1, c2 = st.columns(2)
            with c1:
                goal = st.text_input("Цель программы *", value="Коррекция дефицитов")
                start_d = st.date_input("Начало", datetime.date.today())
            with c2:
                dur = st.slider("Длительность (месяцев)", 1, 6, 3)
                end_d = start_d + datetime.timedelta(days=30*dur)
                st.write(f"Окончание: {end_d}")

            # Таблица
            df = pd.DataFrame(current_data)
            
            edited_df = st.data_editor(
                df,
                column_config={
                    "selected": st.column_config.CheckboxColumn("Вкл.", default=True),
                    "id": None,
                    "score": st.column_config.NumberColumn("Рейтинг", format="%.1f ⭐")
                },
                disabled=["title", "skill", "score", "materials"],
                hide_index=True,
                use_container_width=True
            )

            # --- ЛОГИКА СОХРАНЕНИЯ С ВАЛИДАЦИЕЙ ---
            if st.form_submit_button("💾 Сохранить активный план"):
                
                # 1. Валидация дат
                if start_d >= end_d:
                    st.error("Ошибка: Дата окончания должна быть позже даты начала!")
                    st.stop() # Останавливаем выполнение, чтобы не сохранять ошибочные данные
                
                # 2. Валидация цели
                if not goal:
                    st.error("Ошибка: Укажите цель программы.")
                    st.stop()

                # 3. Валидация выбора упражнений
                selected_rows = edited_df[edited_df["selected"] == True]
                ids_to_save = selected_rows["id"].tolist()
                
                if not ids_to_save:
                    st.error("Ошибка: План пуст. Выберите хотя бы одно упражнение.")
                else:
                    # Загружаем "живые" объекты из БД для сохранения
                    final_objs = db.query(Exercise).filter(Exercise.id.in_(ids_to_save)).all()
                    
                    # Сохраняем (старые уйдут в архив автоматически)
                    trajectory_service.create_educational_plan(
                        selected_student_id, 1, goal, start_d, end_d, final_objs
                    )
                    
                    st.toast(f"План успешно сохранен! ({len(final_objs)} упр.)", icon="🚀")
                    
                    # Обновляем session_state, оставляя только выбранные (чтобы галочки не сбрасывались)
                    updated_view = [row for row in current_data if row["id"] in ids_to_save]
                    st.session_state[session_key] = updated_view
                    st.rerun()