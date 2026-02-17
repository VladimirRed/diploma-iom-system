import streamlit as st

def set_app_theme():
    """
    Применяет кастомные стили CSS.
    """
    st.markdown("""
    <style>
        /* 1. Шрифты */
        h1, h2, h3 {
            color: #2C3E50;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }
        
        /* 2. Боковая панель */
        [data-testid="stSidebar"] {
            background-color: #F8F9FA;
            border-right: 1px solid #E9ECEF;
        }
        
        /* 3. Кнопки */
        .stButton > button {
            border-radius: 8px;
            border: none;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            transition: all 0.3s ease;
        }
        .stButton > button:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 6px rgba(0,0,0,0.15);
        }

        /* 4. Карточки */
        [data-testid="stMetric"] {
            background-color: #ffffff;
            padding: 15px;
            border-radius: 10px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.05);
            border: 1px solid #eee;
        }

        /* 5. Убираем только футер и меню настроек, НО ОСТАВЛЯЕМ ХЕДЕР */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        /* header {visibility: hidden;}  <-- ЭТУ СТРОКУ МЫ УБРАЛИ, ЧТОБЫ ВЕРНУТЬ КНОПКУ МЕНЮ */
        
        /* 6. Вкладки */
        .stTabs [data-baseweb="tab-list"] {
            gap: 10px;
        }
        .stTabs [data-baseweb="tab"] {
            height: 50px;
            white-space: pre-wrap;
            background-color: #ffffff;
            border-radius: 5px;
            color: #4A90E2;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }
        .stTabs [aria-selected="true"] {
            background-color: #4A90E2;
            color: white;
        }
    </style>
    """, unsafe_allow_html=True)

def render_sidebar_header():
    """
    Логотип в сайдбаре
    """
    with st.sidebar:
        st.markdown("""
        <div style="text-align: center; margin-bottom: 20px;">
            <div style="font-size: 60px;">🎓</div>
            <h1 style="color: #4A90E2; margin: 0; font-size: 24px;">ИОМ Система</h1>
            <p style="color: gray; font-size: 12px;">Версия 1.0 (MVP)</p>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("---")