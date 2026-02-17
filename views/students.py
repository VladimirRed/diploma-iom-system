import streamlit as st
import pandas as pd
from datetime import date
from database.connection import get_db
from services.student_service import StudentService
from config.constants import MEDICAL_TAGS, DIAGNOSIS_MAPPING

def update_dynamic_tags(diag_key, tags_key):
    """Обновляет теги при изменении диагноза. Работает и для добавления, и для редактирования."""
    diag = st.session_state[diag_key]
    st.session_state[tags_key] = DIAGNOSIS_MAPPING.get(diag, [])

def show_students_page():
    st.header("📂 Картотека учеников")

    # --- УВЕДОМЛЕНИЯ ---
    if "student_msg" in st.session_state:
        st.success(st.session_state["student_msg"], icon="✅")
        del st.session_state["student_msg"]

    db = next(get_db())
    service = StudentService(db)

    # ТРЮК С КЛЮЧАМИ: Счетчик для принудительной очистки формы добавления
    if "add_form_counter" not in st.session_state:
        st.session_state["add_form_counter"] = 0

    tab1, tab2, tab3 = st.tabs(["📋 Список и Поиск", "➕ Добавить ученика", "✏️ Редактировать профиль"])

    # --- Вкладка 1: Список с ПОИСКОМ и ФИЛЬТРАМИ ---
    with tab1:
        students = service.get_all_students()
        
        if not students:
            st.info("В базе пока нет учеников.")
        else:
            with st.container():
                c_search, c_filter = st.columns([2, 1])
                with c_search:
                    search_query = st.text_input("🔍 Поиск", placeholder="Введите имя ребенка или родителя...", label_visibility="collapsed")
                with c_filter:
                    unique_diagnoses = sorted(list(set([s.diagnosis_code for s in students if s.diagnosis_code])))
                    selected_diags = st.multiselect("Фильтр по диагнозу", options=unique_diagnoses, placeholder="Все диагнозы", label_visibility="collapsed")

            filtered_students = students
            if search_query:
                query = search_query.lower()
                filtered_students = [
                    s for s in filtered_students 
                    if (query in s.full_name.lower()) or (s.parent_contact and query in s.parent_contact.lower())
                ]
            if selected_diags:
                filtered_students = [s for s in filtered_students if s.diagnosis_code in selected_diags]

            st.caption(f"Найдено записей: {len(filtered_students)} из {len(students)}")
            st.markdown("---")

            if not filtered_students:
                st.warning("По вашему запросу ничего не найдено.")
            else:
                cols = st.columns([0.5, 3, 1.5, 2, 2, 2, 0.5])
                fields = ["ID", "ФИО", "Дата рожд.", "Диагноз", "Противопоказания", "Родитель", ""]
                for col, field in zip(cols, fields):
                    col.markdown(f"**{field}**")
                
                for s in filtered_students:
                    cols = st.columns([0.5, 3, 1.5, 2, 2, 2, 0.5])
                    cols[0].write(str(s.id))
                    cols[1].write(s.full_name)
                    cols[2].write(s.birth_date.strftime('%d.%m.%Y'))
                    cols[3].caption(s.diagnosis_code)
                    
                    tags = s.medical_tags.split(",") if s.medical_tags else []
                    if tags:
                        cols[4].caption(", ".join(tags))
                    else:
                        cols[4].write("—")
                        
                    cols[5].write(s.parent_contact)
                    
                    if cols[6].button("❌", key=f"del_student_{s.id}", help="Удалить ученика"):
                        service.delete_student(s.id)
                        st.session_state["student_msg"] = f"Ученик {s.full_name} удален."
                        st.rerun()
                    st.markdown("---")

    # --- Вкладка 2: Добавление ---
    with tab2:
        st.subheader("Регистрация нового ребенка")
        
        # Динамические ключи на основе счетчика
        fk = st.session_state["add_form_counter"]
        k_name = f"add_name_{fk}"
        k_bdate = f"add_bdate_{fk}"
        k_diag = f"add_diag_{fk}"
        k_parent = f"add_parent_{fk}"
        k_tags = f"add_tags_{fk}"

        # Инициализация тегов для текущей итерации формы
        if k_tags not in st.session_state:
            first_diag = list(DIAGNOSIS_MAPPING.keys())[0]
            st.session_state[k_tags] = DIAGNOSIS_MAPPING.get(first_diag, [])
        
        c1, c2 = st.columns(2)
        with c1:
            new_name = st.text_input("ФИО ребенка *", key=k_name)
            new_bdate = st.date_input("Дата рождения *", min_value=date(2000, 1, 1), key=k_bdate)
            new_diag = st.selectbox(
                "Основной диагноз", 
                list(DIAGNOSIS_MAPPING.keys()), 
                key=k_diag,
                on_change=update_dynamic_tags,
                args=(k_diag, k_tags)
            )
            
        with c2:
            new_parent = st.text_input("ФИО Родителя / Телефон", key=k_parent)
            new_tags = st.multiselect(
                "⚠️ Медицинские противопоказания", 
                options=MEDICAL_TAGS, 
                key=k_tags,
                help="Противопоказания подставляются автоматически."
            )

        if st.button("💾 Сохранить в базу", type="primary", key=f"btn_add_{fk}"):
            if not new_name or len(new_name) < 2:
                st.error("Ошибка: ФИО должно содержать минимум 2 символа.")
            elif new_bdate > date.today():
                st.error("Ошибка: Дата рождения не может быть в будущем.")
            else:
                try:
                    service.create_student(new_name, new_bdate, new_diag, new_parent, new_tags)
                    st.session_state["student_msg"] = f"Ученик {new_name} успешно добавлен!"
                    
                    # ОЧИСТКА ФОРМЫ: просто увеличиваем счетчик.
                    # При перезагрузке Streamlit создаст виджеты с новыми ключами (они будут пустыми)
                    st.session_state["add_form_counter"] += 1
                    st.rerun()
                except Exception as e:
                    st.error(f"Ошибка базы данных: {e}")

    # --- Вкладка 3: Редактирование ---
    with tab3:
        st.subheader("Изменение данных")
        all_students = service.get_all_students()
        
        if not all_students:
            st.info("Нет учеников.")
        else:
            student_options = {s.id: s.full_name for s in all_students}
            selected_id = st.selectbox("Выберите ученика для редактирования:", list(student_options.keys()), format_func=lambda x: student_options[x], key="edit_selector")
            
            student = service.get_student_by_id(selected_id)
            if student:
                diag_key = f"edit_diag_{student.id}"
                tags_key = f"edit_tags_{student.id}"
                
                if tags_key not in st.session_state:
                    current_tags = [t for t in (student.medical_tags.split(",") if student.medical_tags else []) if t in MEDICAL_TAGS]
                    st.session_state[tags_key] = current_tags

                c1, c2 = st.columns(2)
                with c1:
                    e_name = st.text_input("ФИО ребенка", value=student.full_name, key=f"edit_name_{student.id}")
                    e_bdate = st.date_input("Дата рождения", value=student.birth_date, key=f"edit_bdate_{student.id}")
                    
                    diag_list = list(DIAGNOSIS_MAPPING.keys())
                    current_diag_index = diag_list.index(student.diagnosis_code) if student.diagnosis_code in diag_list else 0
                    
                    e_diag = st.selectbox(
                        "Основной диагноз", 
                        diag_list, 
                        index=current_diag_index, 
                        key=diag_key,
                        on_change=update_dynamic_tags,
                        args=(diag_key, tags_key)
                    )
                    
                with c2:
                    e_parent = st.text_input("ФИО Родителя", value=student.parent_contact or "", key=f"edit_parent_{student.id}")
                    e_tags = st.multiselect("⚠️ Противопоказания", options=MEDICAL_TAGS, key=tags_key)

                if st.button("💾 Обновить профиль", type="primary", key=f"btn_edit_{student.id}"):
                    if not e_name:
                        st.error("ФИО не может быть пустым.")
                    elif e_bdate > date.today():
                        st.error("Дата рождения не может быть в будущем.")
                    else:
                        service.update_student(student.id, e_name, e_bdate, e_diag, e_parent, e_tags)
                        st.session_state["student_msg"] = f"Данные {e_name} обновлены!"
                        st.rerun()
