import streamlit as st
import re
import pandas as pd
import os
from datetime import datetime

# --- [보안 설정] 두 분이서 공유할 비밀번호를 여기에 설정하세요 ---
APP_PASSWORD = "3411" # <-- 원하시는 숫자나 문자로 바꾸세요!

def check_password():
    """비밀번호 확인 함수"""
    if "password_correct" not in st.session_state:
        st.session_state.password_correct = False

    if not st.session_state.password_correct:
        st.title("🔒 Access Required")
        password_input = st.text_input("비밀번호를 입력하세요", type="password")
        if st.button("접속하기"):
            if password_input == APP_PASSWORD:
                st.session_state.password_correct = True
                st.rerun()
            else:
                st.error("❌ 비밀번호가 틀렸습니다.")
        return False
    return True

# 비밀번호 통과 시에만 아래 코드 실행
if check_password():
    # 1. 앱 페이지 설정
    st.set_page_config(page_title="Medtronic Expense Manager", layout="centered")

    DATA_FILE = "expenses.csv"

    def load_data():
        if os.path.exists(DATA_FILE):
            try:
                return pd.read_csv(DATA_FILE)
            except:
                return pd.DataFrame(columns=["id", "날짜", "항목", "금액", "내용"])
        else:
            return pd.DataFrame(columns=["id", "날짜", "항목", "금액", "내용"])

    def save_data(df):
        df.to_csv(DATA_FILE, index=False, encoding='utf-8-sig')

    # 디자인 커스텀
    st.markdown("""
        <style>
        .main { background-color: #ffffff; }
        .stMetric { background-color: #f8f9fa; padding: 15px; border-radius: 8px; border: 1px solid #dee2e6; }
        div[data-testid="stMetricValue"] { color: #002855; font-size: 1.8rem !important; font-weight: bold; }
        div[data-testid="stMetricLabel"] { font-size: 1rem !important; color: #333; }
        .stButton>button { background-color: #002855; color: white; border-radius: 4px; border: none; }
        .warning-text { color: #dc3545; font-size: 0.85rem; margin-top: 5px; font-weight: bold; }
        </style>
        """, unsafe_allow_html=True)

    st.title("Medtronic Expense Tracker")

    if 'df_history' not in st.session_state:
        st.session_state.df_history = load_data()

    if 'limit_meeting' not in st.session_state:
        st.session_state.limit_meeting = 300000
    if 'limit_product' not in st.session_state:
        st.session_state.limit_product = 5000000

    LIMIT_MEAL_TOTAL = 100000
    LIMIT_MEAL_PER_USE = 15000

    # --- [사이드바] 설정 및 초기화 ---
    with st.sidebar:
        st.subheader("Settings")
        st.session_state.limit_meeting = st.number_input("대리점 미팅 월 한도", value=st.session_state.limit_meeting, step=10000)
        st.session_state.limit_product = st.number_input("제품 설명회 월 한도", value=st.session_state.limit_product, step=100000)
        
        st.divider()
        st.subheader("Data Reset")
        if st.button("대리점 미팅 내역 초기화"):
            st.session_state.df_history = st.session_state.df_history[st.session_state.df_history['항목'] != "대리점미팅"]
            save_data(st.session_state.df_history)
            st.rerun()
        if st.button("개인 식사 내역 초기화"):
            st.session_state.df_history = st.session_state.df_history[st.session_state.df_history['항목'] != "개인식사"]
            save_data(st.session_state.df_history)
            st.rerun()
        if st.button("제품 설명회 내역 초기화"):
            st.session_state.df_history = st.session_state.df_history[st.session_state.df_history['항목'] != "제품설명회"]
            save_data(st.session_state.df_history)
            st.rerun()
        if st.button("⚠️ 전체 내역 통합 초기화"):
            st.session_state.df_history = pd.DataFrame(columns=["id", "날짜", "항목", "금액", "내용"])
            save_data(st.session_state.df_history)
            st.rerun()
        
        st.divider()
        if st.button("로그아웃"):
            st.session_state.password_correct = False
            st.rerun()

    # --- 상단 잔액 대시보드 ---
    df = st.session_state.df_history
    df['금액'] = pd.to_numeric(df['금액'], errors='coerce').fillna(0)

    total_meeting = df[df['항목'] == "대리점미팅"]['금액'].sum()
    total_meal = df[df['항목'] == "개인식사"]['금액'].sum()
    total_product = df[df['항목'] == "제품설명회"]['금액'].sum()

    rem_meeting = st.session_state.limit_meeting - total_meeting
    rem_meal = LIMIT_MEAL_TOTAL - total_meal
    rem_product = st.session_state.limit_product - total_product

    col1, col2 = st.columns(2)
    with col1:
        st.metric(f"대리점 미팅 (한도:{st.session_state.limit_meeting:,}원)", f"{int(rem_meeting):,}원")
        if rem_meeting <= 30000: st.markdown("<p class='warning-text'>잔액 부족 주의</p>", unsafe_allow_html=True)
    with col2:
        st.metric(f"개인 식사 (한도:{LIMIT_MEAL_TOTAL:,}원)", f"{int(rem_meal):,}원")
        if rem_meal <= 30000: st.markdown("<p class='warning-text'>잔액 부족 주의</p>", unsafe_allow_html=True)

    st.write("")
    st.metric(f"제품 설명회 (한도:{st.session_state.limit_product:,}원)", f"{int(rem_product):,}원")
    if rem_product <= 30000: st.markdown("<p class='warning-text'>잔액 부족 주의</p>", unsafe_allow_html=True)

    st.divider()

    # --- 입력 섹션 ---
    st.subheader("Input")
    sms_input = st.text_area("카드 승인 문자를 붙여넣으세요", height=70)
    category = st.radio("항목 선택", ["대리점미팅", "개인식사", "제품설명회"], horizontal=True)

    if st.button("내역 등록", use_container_width=True):
        if sms_input:
            amount_match = re.search(r'([0-9,]+)원', sms_input)
            if amount_match:
                amount = int(amount_match.group(1).replace(',', ''))
                new_entry = pd.DataFrame([{
                    "id": datetime.now().strftime("%Y%m%d%H%M%S%f"),
                    "날짜": datetime.now().strftime("%m/%d %H:%M"),
                    "항목": category,
                    "금액": amount,
                    "내용": sms_input[:20].replace('\n', ' ') + ".."
                }])
                if category == "개인식사" and amount > LIMIT_MEAL_PER_USE:
                    st.error(f"개인식사 건당 한도(1.5만) 초과!")
                st.session_state.df_history = pd.concat([new_entry, st.session_state.df_history], ignore_index=True)
                save_data(st.session_state.df_history)
                st.rerun()

    st.divider()

    # --- 상세 내역 필터링 ---
    st.subheader("History")
    filter_option = st.selectbox("조회할 항목 선택", ["전체 보기", "대리점미팅", "개인식사", "제품설명회"])

    display_df = st.session_state.df_history if filter_option == "전체 보기" else st.session_state.df_history[st.session_state.df_history['항목'] == filter_option]

    if not display_df.empty:
        for index, row in display_df.iterrows():
            c1, c2, c3, c4 = st.columns([2, 2, 2, 1])
            c1.write(row["날짜"])
            c2.write(f"**{row['항목']}**")
            c3.write(f"{int(row['금액']):,}원")
            if c4.button("삭제", key=row["id"]):
                st.session_state.df_history = st.session_state.df_history[st.session_state.df_history['id'] != row['id']]
                save_data(st.session_state.df_history)
                st.rerun()
    else:
        st.info("표시할 내역이 없습니다.")
