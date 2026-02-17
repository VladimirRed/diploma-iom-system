import streamlit as st
import pandas as pd
from database.connection import get_db
from services.exercise_service import ExerciseService
from config.constants import MEDICAL_TAGS

def sync_rating(source_key, target_key):
    if source_key in st.session_state:
        st.session_state[target_key] = st.session_state[source_key]

def show_library_page():
    st.header("📚 Библиотека методик и упражнений")
    
    # --- БЛОК ОТОБРАЖЕНИЯ УВЕДОМЛЕНИЙ ---
    if "lib_msg" in st.session_state:
        st.success(st.session_state["lib_msg"], icon="✅")
        del st.session_state["lib_msg"]
    # ------------------------------------
    
    db = next(get_db())
    service = ExerciseService(db)

    tab1, tab2, tab3 = st.tabs(["📋 Список", "➕ Создать", "✏️ Редактировать"])

    # --- Вкладка 1: Список ---
    with tab1:
        exercises = service.get_all_exercises()
        if not exercises:
            st.info("База знаний пуста.")
        else:
            cols = st.columns([0.5, 3, 2, 1, 1, 2, 0.5])
            headers = ["ID", "Название", "Навык", "Сложн.", "Рейтинг", "Инвентарь", ""]
            for col, h in zip(cols, headers): col.markdown(f"**{h}**")
            st.markdown("---")

            for ex in exercises:
                c1, c2, c3, c4, c5, c6, c7 = st.columns([0.5, 3, 2, 1, 1, 2, 0.5])
                c1.write(str(ex.id))
                c2.write(ex.title)
                c3.write(ex.skill.name if ex.skill else "—")
                c4.write(str(ex.difficulty_level))
                c5.write(f"{ex.effectiveness_score} ⭐")
                c6.write(ex.materials)
                
                if c7.button("❌", key=f"del_ex_{ex.id}", help="Удалить"):
                    service.delete_exercise(ex.id)
                    st.session_state["lib_msg"] = "Методика удалена из базы."
                    st.rerun()
                
                if ex.contraindications: st.caption(f"⛔ {ex.contraindications}")
                st.markdown("---")

    # --- Вкладка 2: Создание ---
    with tab2:
        st.subheader("Новая методика")
        skills = service.get_all_skills()
        if not skills:
            st.error("Сначала создайте навыки.")
        else:
            skill_opts = {s.id: f"{s.name}" for s in skills}

            c1, c2 = st.columns(2)
            with c1:
                title = st.text_input("Название *", key="new_title")
                skill_id = st.selectbox("Навык", list(skill_opts.keys()), format_func=lambda x: skill_opts[x], key="new_skill")
                diff = st.slider("Сложность", 1, 5, 3, key="new_diff")
            with c2:
                mat = st.text_input("Инвентарь", key="new_mat")
                dur = st.number_input("Мин.", 1, 120, 15, key="new_dur")
                
                st.write("Рейтинг эффективности:")
                cc1, cc2 = st.columns([1, 4])
                with cc1:
                    st.number_input("Рейтинг", 0.0, 10.0, step=0.5, key="num_new_score", on_change=sync_rating, args=("num_new_score", "slide_new_score"), label_visibility="collapsed")
                with cc2:
                    st.slider("Рейтинг", 0.0, 10.0, step=0.5, key="slide_new_score", on_change=sync_rating, args=("slide_new_score", "num_new_score"), label_visibility="collapsed")

            contras = st.multiselect("⛔ Противопоказания", options=MEDICAL_TAGS, key="new_contras")
            desc = st.text_area("Описание", key="new_desc")

            if st.button("Сохранить методику", type="primary"):
                if not title:
                    st.error("Название методики обязательно!")
                else:
                    score = st.session_state["num_new_score"]
                    new_ex = service.create_exercise(title, desc, skill_id, diff, mat, dur, score)
                    new_ex.contraindications = ",".join(contras)
                    db.commit()
                    
                    st.session_state["lib_msg"] = f"Методика '{title}' успешно добавлена!"
                    st.rerun()

    # --- Вкладка 3: Редактирование ---
    with tab3:
        st.subheader("Редактирование")
        ex_opts = {e.id: e.title for e in service.get_all_exercises()}
        if not ex_opts:
            st.info("Нет методик.")
        else:
            sel_id = st.selectbox("Выберите методику:", list(ex_opts.keys()), format_func=lambda x: ex_opts[x])
            target_ex = [x for x in service.get_all_exercises() if x.id == sel_id][0]
            
            c1, c2 = st.columns(2)
            with c1:
                e_title = st.text_input("Название", value=target_ex.title, key="e_title")
                e_diff = st.slider("Сложность", 1, 5, value=target_ex.difficulty_level, key="e_diff")
            with c2:
                e_mat = st.text_input("Инвентарь", value=target_ex.materials, key="e_mat")
                if "num_e_score" not in st.session_state: st.session_state["num_e_score"] = float(target_ex.effectiveness_score)
                if "slide_e_score" not in st.session_state: st.session_state["slide_e_score"] = float(target_ex.effectiveness_score)

                cc1, cc2 = st.columns([1, 4])
                with cc1: st.number_input("Р", 0.0, 10.0, step=0.5, key="num_e_score", on_change=sync_rating, args=("num_e_score", "slide_e_score"))
                with cc2: st.slider("Р", 0.0, 10.0, step=0.5, key="slide_e_score", on_change=sync_rating, args=("slide_e_score", "num_e_score"), label_visibility="collapsed")

            cur_con = [x for x in (target_ex.contraindications.split(",") if target_ex.contraindications else []) if x in MEDICAL_TAGS]
            e_contras = st.multiselect("⛔ Противопоказания", options=MEDICAL_TAGS, default=cur_con, key="e_contras")
            e_desc = st.text_area("Описание", value=target_ex.description, key="e_desc")

            if st.button("💾 Сохранить изменения"):
                if not e_title:
                    st.error("Название не может быть пустым")
                else:
                    service.update_exercise(
                        target_ex.id, e_title, e_desc, target_ex.skill_id, e_diff, e_mat, 
                        target_ex.duration_minutes, st.session_state["num_e_score"], e_contras
                    )
                    st.session_state["lib_msg"] = "Данные методики обновлены!"
                    st.rerun()