import streamlit as st
import pandas as pd
import plotly.express as px
from database.connection import get_db
from services.student_service import StudentService
from services.diagnostic_service import DiagnosticService
from database.models import DiagnosticType

# Словарь для перевода
TYPE_MAPPING = {
    "primary": "Первичная",
    "intermediate": "Промежуточная",
    "final": "Итоговая"
}

# --- Вспомогательная функция для синхронизации ---
def sync_input(source_key, target_key):
    """
    Копирует значение из одного виджета в другой.
    Вызывается при изменении значения (on_change).
    """
    if source_key in st.session_state:
        st.session_state[target_key] = st.session_state[source_key]

def show_diagnostics_page():
    st.header("🩺 Диагностика и Профиль развития")

    db = next(get_db())
    student_service = StudentService(db)
    diagnostic_service = DiagnosticService(db)

    # 1. Выбор ученика
    students = student_service.get_all_students()
    if not students:
        st.warning("Сначала добавьте учеников в разделе 'Ученики'.")
        return

    student_options = {s.id: f"{s.full_name} ({s.birth_date})" for s in students}
    
    selected_student_id = st.selectbox(
        "Выберите ученика:", 
        options=list(student_options.keys()), 
        format_func=lambda x: student_options[x],
        key="diag_student_selector"
    )

    tab1, tab2 = st.tabs(["📝 Новая диагностика", "📊 Динамика развития (График)"])

    # --- Вкладка 1: Ввод данных ---
    with tab1:
        st.subheader("Оценка навыков")
        skills = diagnostic_service.get_assessment_skills()
        
        if not skills:
            st.error("Справочник навыков пуст.")
        else:
            # МЫ УБРАЛИ st.form, чтобы работала синхронизация
            c1, c2 = st.columns(2)
            with c1:
                selected_type_ru = st.selectbox("Тип диагностики", list(TYPE_MAPPING.values()))
                d_type = [k for k, v in TYPE_MAPPING.items() if v == selected_type_ru][0]
            with c2:
                st.info("Изменение ползунка автоматически меняет число и наоборот.")

            # Словарь для сбора итоговых значений
            # Мы будем собирать их из st.session_state при нажатии кнопки
            current_group = None
            
            # Контейнер для списка навыков
            for skill in skills:
                # Группировка
                group_name = skill.parent.name if skill.parent else "Общие навыки"
                if group_name != current_group:
                    st.markdown(f"#### {group_name}")
                    current_group = group_name

                # Уникальные ключи
                base_key = f"{selected_student_id}_{skill.id}"
                num_key = f"num_{base_key}"
                slide_key = f"slide_{base_key}"

                # Инициализация значений (по умолчанию 0)
                if num_key not in st.session_state:
                    st.session_state[num_key] = 0
                if slide_key not in st.session_state:
                    st.session_state[slide_key] = 0

                # Верстка в одну строку
                col_input, col_slider = st.columns([1, 4])
                
                with col_input:
                    st.number_input(
                        label="Балл",
                        min_value=0, max_value=5,
                        label_visibility="collapsed",
                        key=num_key,
                        on_change=sync_input,
                        args=(num_key, slide_key) 
                    )
                
                with col_slider:
                    st.slider(
                        label=skill.name,
                        min_value=0, max_value=5,
                        label_visibility="visible",
                        key=slide_key,
                        on_change=sync_input,
                        args=(slide_key, num_key)
                    )

            st.markdown("---")
            comment = st.text_area("Заключение специалиста")
            
            # Кнопка сохранения (Обычная, не внутри формы)
            save_clicked = st.button("💾 Сохранить результаты", type="primary")

            if save_clicked:
                # ВАЛИДАЦИЯ (например, проверка на пустой комментарий - опционально)
                
                input_scores = {}
                for skill in skills:
                    key = f"num_{selected_student_id}_{skill.id}"
                    input_scores[skill.id] = st.session_state[key]

                diagnostic_service.save_diagnostic(
                    student_id=selected_student_id,
                    teacher_id=1,
                    d_type=d_type,
                    scores=input_scores,
                    summary=comment
                )
                
                # КРАСИВОЕ УВЕДОМЛЕНИЕ
                st.toast("Результаты диагностики успешно сохранены!", icon="🩺")
                st.rerun()

    # --- Вкладка 2: Сравнительный график ---
    with tab2:
        st.subheader("Мониторинг динамики")
        
        all_diags = diagnostic_service.get_all_diagnostics(selected_student_id)
        
        if not all_diags:
            st.info("Нет данных диагностики.")
        else:
            # --- ЛОГИКА ФИЛЬТРАЦИИ ---
            # Оставляем только ПОСЛЕДНЮЮ запись каждого типа
            latest_diagnostics_map = {}
            for diag in all_diags:
                latest_diagnostics_map[diag.type] = diag
            
            filtered_diags = list(latest_diagnostics_map.values())
            
            # Сортировка порядка слоев (Первичная -> Промежуточная -> Итоговая)
            order = ["primary", "intermediate", "final"]
            filtered_diags.sort(key=lambda x: order.index(x.type.value) if x.type.value in order else 99)

            # Данные для Plotly
            chart_data = []
            for diag in filtered_diags:
                type_name = TYPE_MAPPING.get(diag.type.value, diag.type.value)
                legend_label = f"{type_name} ({diag.date.strftime('%d.%m')})"
                
                for res in diag.results:
                    chart_data.append({
                        "Навык": res.skill.name,
                        "Баллы": res.score,
                        "Этап": legend_label,
                        "Группа": res.skill.parent.name if res.skill.parent else "Общее"
                    })
            
            if chart_data:
                df = pd.DataFrame(chart_data)
                
                # Построение графика
                fig = px.line_polar(
                    df, 
                    r='Баллы', 
                    theta='Навык', 
                    color='Этап', 
                    line_close=True,
                    range_r=[0, 5],
                    title=f"Динамика развития: {student_options[selected_student_id]}",
                    markers=True
                )
                
                fig.update_traces(fill='toself', opacity=0.1) # Чуть прозрачнее заливка
                st.plotly_chart(fig, use_container_width=True)
                
                # Текстовая история
                with st.expander("Детальная история (Показаны последние срезы)"):
                    for diag in filtered_diags:
                        type_ru = TYPE_MAPPING.get(diag.type.value, diag.type.value)
                        st.markdown(f"**{type_ru} — {diag.date}**")
                        st.write(f"_{diag.summary if diag.summary else 'Без комментария'}_")
            else:
                st.warning("Данные есть, но результаты пустые.")