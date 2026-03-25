import streamlit as st
import re
import pandas as pd
import os
from datetime import datetime

# 1. 앱 페이지 설정 (메드트로닉 네이비 테마)
st.set_page_config(page_title="Medtronic Expense Manager", layout="centered")

# 저장할 파일 이름
DATA_FILE = "expenses.csv"

# 파일에서 데이터 불러오기 함수
def load_data():
    if os.path.exists(DATA_FILE):
        return pd.read_csv(DATA_FILE)
    else:
        return pd.DataFrame(columns=["id", "날짜", "항목", "금액", "내용"])

# 파일에 데이터 저장하기 함수
def save_data(df):
    df.to_csv(DATA_FILE, index=False, encoding='utf-8-sig')

# 메드트로닉 스타일 CSS
st.markdown("""
    <style>
    .main { background-color: #ffffff; }
    .stMetric { background-color: #f0f2f6; padding: 15px; border-radius: 10px; border-left: 5px solid #002855; }
    div[data-testid="stMetricValue"] { color: #002855; }
    .stButton>button { background-color: #002855; color: white; border-radius: 5px; }
    .warning-text { color: #dc3545; font-weight: bold; font-size: 0.8rem; }
    </style>
    """, unsafe_allow_html=True)

st.title("💙 Medtronic Expense Tracker")

# 데이터 초기화 (파일에서 읽어옴)
df_history = load_data()

# 세션 상태에 한도 설정 유지
if 'limit_meeting' not in st.session_state:
    st.session_state.limit_meeting = 300000
if 'limit_product' not in st.session_state:
    st.session_state.limit_product = 5000000

LIMIT_MEAL_TOTAL = 100000
LIMIT_MEAL_PER_USE = 15000

# --- [사이드바] 한도 설정 및 관리 ---
with st.sidebar:
    st.header("⚙️ 관리 설정")
    st.session_state.limit_meeting = st.number_input("대리점 미팅 한도", value=st.session_state.limit_meeting, step=10000)
    st.session_state.limit_product = st.number_input("제품 설명회 한도", value=st.session_state.limit_product, step=100000)
    
    st.divider()
    st.subheader("🧹 항목별 전체 초기화")
    if st.button("대리점 미팅 내역 삭제"):
        df_history = df_history[df_history['항목'] != "대리점미팅"]
        save_data(df_history)
        st.rerun()
    if st.button("개인 식사 내역 삭제"):
        df_history = df_history[df_history['항목'] != "개인식사"]
        save_data(df_history)
        st.rerun()
    if st.button("제품 설명회 내역 삭제"):
        df_history = df_history[df_history['항목'] != "제품설명회"]
        save_data(df_history)
        st.rerun()

# --- 상단 잔액 대시보드 ---
# 숫자형 변환 확인 후 계산
df_history['금액'] = pd.to_numeric(df_history['금액'], errors='coerce').fillna(0)

total_meeting = df_history[df_history['항목'] == "대리점미팅"]['금액'].sum()
total_meal = df_history[df_history['항목'] == "개인식사"]['금액'].sum()
total_product = df_history[df_history['항목'] == "제품설명회"]['금액'].sum()

rem_meeting = st.session_state.limit_meeting - total_meeting
rem_meal = LIMIT_MEAL_TOTAL - total_meal
rem_product = st.session_state.limit_product - total_product

col1, col2 = st.columns(2)
with col1:
    st.metric("🤝 대리점 미팅 잔액", f"{int(rem_meeting):,}")
    if rem_meeting <= 30000: st.markdown("<p class='warning-text'>⚠️ 잔고 주의</p>", unsafe_allow_html=True)
with col2:
    st.metric("🍚 개인 식사 잔액", f"{int(rem_meal):,}")
    if rem_meal <= 30000: st.markdown("<p class='warning-text'>⚠️ 잔고 주의</p>", unsafe_allow_html=True)

st.write("")
st.metric("📦 제품 설명회 잔액", f"{int(rem_product):,}", delta=f"한도: {st.session_state.limit_product:,}")
if rem_product <= 30000: st.markdown("<p class='warning-text'>⚠️ 잔고 주의</p>", unsafe_allow_html=True)

st.divider()

# --- 입력 섹션 ---
st.subheader("📥 내역 입력")
sms_input = st.text_area("카드 문자를 붙여넣으세요", height=70)
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
                "내용": sms_input[:15] + ".."
            }])
            
            if category == "개인식사" and amount > LIMIT_MEAL_PER_USE:
                st.warning(f"⚠️ 식사 건당 한도(1.5만) 초과!")
            
            # 데이터 병합 및 저장
            df_history = pd.concat([new_entry, df_history], ignore_index=True)
            save_data(df_history)
            st.rerun()

# --- 상세 내역 및 개별 삭제 ---
st.subheader("📋 상세 내역 (최신순)")
if not df_history.empty:
    for index, row in df_history.iterrows():
        c1, c2, c3, c4 = st.columns([2, 2, 2, 1])
        c1.write(row["날짜"])
        c2.write(f"**{row['항목']}**")
        c3.write(f"{int(row['금액']):,}원")
        if c4.button("삭제", key=row["id"]):
            df_history = df_history.drop(index)
            save_data(df_history)
            st.rerun()
        st.divider()
else:
    st.info("내역이 없습니다.")
