import streamlit as st
import datetime
from database.connection import get_db
from services.student_service import StudentService
from services.log_service import LogService
from database.models import LogStatus

STATUS_MAPPING = {"completed": "Выполнено", "failed": "Не справился", "skipped": "Пропущено"}
REVERSE_STATUS_MAPPING = {v: k for k, v in STATUS_MAPPING.items()}

def sync_log_score(source, target):
    if source in st.session_state:
        st.session_state[target] = st.session_state[source]

def show_log_page():
    st.header("📅 Дневник занятий (Недельный вид)")
    
    db = next(get_db())
    student_service = StudentService(db)
    log_service = LogService(db)

    students = student_service.get_all_students()
    if not students:
        st.warning("Нет учеников."); return

    # 1. Выбор ученика и Недели
    col1, col2 = st.columns([1, 2])
    with col1:
        s_opts = {s.id: s.full_name for s in students}
        selected_student_id = st.selectbox("Ученик:", list(s_opts.keys()), format_func=lambda x: s_opts[x], key="log_stu")
    
    with col2:
        # Пользователь выбирает любую дату, мы вычисляем понедельник этой недели
        picked_date = st.date_input("Выберите любую дату недели:", datetime.date.today())
        
        # Магия Python: находим понедельник выбранной недели
        # weekday(): 0=Пн, 6=Вс
        start_of_week = picked_date - datetime.timedelta(days=picked_date.weekday())
        end_of_week = start_of_week + datetime.timedelta(days=6)
        
        st.caption(f"Показана неделя: **{start_of_week.strftime('%d.%m')} — {end_of_week.strftime('%d.%m')}**")

    # 2. Получение плана
    active_plan = log_service.get_active_plan(selected_student_id)
    if not active_plan:
        st.info("Нет активного плана. Создайте его в 'Конструкторе'."); return

    st.markdown("---")

    # 3. Генерация вкладок по дням недели
    # Список названий вкладок
    days_ru = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"]
    
    # Создаем 7 вкладок
    tabs = st.tabs([f"{day} ({ (start_of_week + datetime.timedelta(days=i)).strftime('%d.%m') })" for i, day in enumerate(days_ru)])

    # 4. Наполняем каждую вкладку
    for i, tab in enumerate(tabs):
        with tab:
            # Вычисляем дату для этой конкретной вкладки
            current_date = start_of_week + datetime.timedelta(days=i)
            
            # Проверяем, будущее ли это (опционально, можно разрешить планировать вперед)
            is_future = current_date > datetime.date.today()
            if is_future:
                st.caption("⚠️ Это дата в будущем. Вы можете заполнить план заранее.")

            # Загружаем логи именно для ЭТОГО дня
            day_logs = log_service.get_logs_for_date(active_plan.id, current_date)
            
            # --- РИСУЕМ ФОРМУ ДЛЯ ОДНОГО ДНЯ ---
            # Важно: используем current_date в ключах (key), чтобы виджеты были уникальны для каждой вкладки
            
            with st.container():
                cnt = 0
                for item in active_plan.items:
                    ex = item.exercise
                    
                    # Данные из базы или дефолт
                    if item.id in day_logs:
                        l = day_logs[item.id]
                        status_val = STATUS_MAPPING.get(l.status.value, "Выполнено")
                        score_val = l.performance_score
                        note_val = l.teacher_notes or ""
                    else:
                        status_val = "Выполнено"
                        score_val = 5
                        note_val = ""

                    # Уникальные ключи: ID_Упражнения + ДАТА
                    bk = f"{item.id}_{current_date}"
                    
                    # Инициализация
                    if f"num_{bk}" not in st.session_state: st.session_state[f"num_{bk}"] = score_val
                    if f"slide_{bk}" not in st.session_state: st.session_state[f"slide_{bk}"] = score_val

                    c1, c2, c3, c4 = st.columns([2, 1.5, 2, 3])
                    with c1:
                        st.write(f"**{ex.title}**")
                        st.caption(f"{ex.materials or ''}")
                    with c2:
                        st.selectbox("Статус", list(STATUS_MAPPING.values()), 
                                     index=list(STATUS_MAPPING.values()).index(status_val), 
                                     key=f"stat_{bk}", label_visibility="collapsed")
                    with c3:
                        # Оценка
                        col_n, col_s = st.columns([1,2])
                        col_n.number_input("Б", 1, 5, key=f"num_{bk}", on_change=sync_log_score, args=(f"num_{bk}", f"slide_{bk}"), label_visibility="collapsed")
                        col_s.slider("Б", 1, 5, key=f"slide_{bk}", on_change=sync_log_score, args=(f"slide_{bk}", f"num_{bk}"), label_visibility="collapsed")
                    with c4:
                        st.text_input("Заметка", value=note_val, key=f"note_{bk}", placeholder="Комментарий...", label_visibility="collapsed")
                    
                    st.divider()
                    cnt += 1
                
                # Кнопка сохранения для конкретного дня
                if st.button(f"💾 Сохранить за {days_ru[i]}", key=f"save_btn_{current_date}"):
                    saved_count = 0
                    try:
                        for item in active_plan.items:
                            bk = f"{item.id}_{current_date}"
                            # Берем из стейта (с проверкой на наличие ключа)
                            if f"stat_{bk}" in st.session_state:
                                s_ru = st.session_state[f"stat_{bk}"]
                                score = st.session_state[f"num_{bk}"]
                                note = st.session_state[f"note_{bk}"]
                                
                                log_service.save_daily_log(
                                    item.id, current_date, REVERSE_STATUS_MAPPING[s_ru], score, note
                                )
                                saved_count += 1
                        
                        st.toast(f"Сохранено {saved_count} записей за {days_ru[i]}!", icon="📝")
                    except Exception as e:
                        st.error(f"Ошибка при сохранении: {e}")