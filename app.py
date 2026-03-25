import streamlit as st
import re
import pandas as pd
import os
from datetime import datetime

# 1. 앱 페이지 설정 (심플 디자인)
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

# 디자인 커스텀 (이모티콘 제거 및 심플 네이비 테마)
st.markdown("""
    <style>
    .main { background-color: #ffffff; }
    .stMetric { background-color: #f8f9fa; padding: 15px; border-radius: 8px; border: 1px solid #dee2e6; }
    div[data-testid="stMetricValue"] { color: #002855; font-weight: bold; }
    .stButton>button { background-color: #002855; color: white; border-radius: 4px; border: none; }
    .warning-text { color: #dc3545; font-size: 0.85rem; margin-top: 5px; }
    .limit-text { color: #6c757d; font-size: 0.8rem; margin-top: 2px; }
    </style>
    """, unsafe_allow_html=True)

st.title("Medtronic Expense Tracker")

# 데이터 로드
df_history = load_data()

# 한도 설정 유지 (세션 상태)
if 'limit_meeting' not in st.session_state:
    st.session_state.limit_meeting = 300000
if 'limit_product' not in st.session_state:
    st.session_state.limit_product = 5000000

LIMIT_MEAL_TOTAL = 100000
LIMIT_MEAL_PER_USE = 15000

# --- [사이드바] 한도 설정 및 초기화 ---
with st.sidebar:
    st.subheader("Settings")
    st.session_state.limit_meeting = st.number_input("대리점 미팅 월 한도", value=st.session_state.limit_meeting, step=10000)
    st.session_state.limit_product = st.number_input("제품 설명회 월 한도", value=st.session_state.limit_product, step=100000)
    
    st.divider()
    st.subheader("Data Reset")
    if st.button("대리점 미팅 내역 초기화"):
        df_history = df_history[df_history['항목'] != "대리점미팅"]
        save_data(df_history)
        st.rerun()
    if st.button("개인 식사 내역 초기화"):
        df_history = df_history[df_history['항목'] != "개인식사"]
        save_data(df_history)
        st.rerun()
    if st.button("제품 설명회 내역 초기화"):
        df_history = df_history[df_history['항목'] != "제품설명회"]
        save_data(df_history)
        st.rerun()
    
    # 1. 전체 내역 초기화 버튼 추가
    if st.button("⚠️ 전체 내역 통합 초기화", help="모든 항목의 데이터를 삭제합니다."):
        df_history = pd.DataFrame(columns=["id", "날짜", "항목", "금액", "내용"])
        save_data(df_history)
        st.rerun()

# --- 상단 잔액 대시보드 (화살표 제거 및 심플 한도 표시) ---
df_history['금액'] = pd.to_numeric(df_history['금액'], errors='coerce').fillna(0)

total_meeting = df_history[df_history['항목'] == "대리점미팅"]['금액'].sum()
total_meal = df_history[df_history['항목'] == "개인식사"]['금액'].sum()
total_product = df_history[df_history['항목'] == "제품설명회"]['금액'].sum()

rem_meeting = st.session_state.limit_meeting - total_meeting
rem_meal = LIMIT_MEAL_TOTAL - total_meal
rem_product = st.session_state.limit_product - total_product

col1, col2 = st.columns(2)
with col1:
    st.metric("대리점 미팅 잔액", f"{int(rem_meeting):,}원")
    st.markdown(f"<p class='limit-text'>한도: {st.session_state.limit_meeting:,}원</p>", unsafe_allow_html=True)
    if rem_meeting <= 30000: st.markdown("<p class='warning-text'>잔액 부족 주의 (3만 이하)</p>", unsafe_allow_html=True)
with col2:
    st.metric("개인 식사 잔액", f"{int(rem_meal):,}원")
    st.markdown(f"<p class='limit-text'>한도: {LIMIT_MEAL_TOTAL:,}원</p>", unsafe_allow_html=True)
    if rem_meal <= 30000: st.markdown("<p class='warning-text'>잔액 부족 주의 (3만 이하)</p>", unsafe_allow_html=True)

st.write("")
# 제품설명회 잔액 (화살표 delta 제거)
st.metric("제품 설명회 잔액", f"{int(rem_product):,}원")
st.markdown(f"<p class='limit-text'>한도: {st.session_state.limit_product:,}원</p>", unsafe_allow_html=True)
if rem_product <= 30000: st.markdown("<p class='warning-text'>잔액 부족 주의 (3만 이하)</p>", unsafe_allow_html=True)

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
                st.error(f"개인식사 건당 한도(1.5만) 초과 내역입니다.")
            
            df_history = pd.concat([new_entry, df_history], ignore_index=True)
            save_data(df_history)
            st.rerun()

st.divider()

# --- 2. 상세 내역 필터링 메뉴 추가 ---
st.subheader("History")
filter_option = st.selectbox("조회할 항목 선택", ["전체 보기", "대리점미팅", "개인식사", "제품설명회"])

# 필터링 로직
if filter_option == "전체 보기":
    display_df = df_history
else:
    display_df = df_history[df_history['항목'] == filter_option]

if not display_df.empty:
    for index, row in display_df.iterrows():
        c1, c2, c3, c4 = st.columns([2, 2, 2, 1])
        c1.write(row["날짜"])
        c2.write(f"**{row['항목']}**")
        c3.write(f"{int(row['금액']):,}원")
        if c4.button("삭제", key=row["id"]):
            # 원본 데이터프레임에서 ID로 삭제
            df_history = df_history[df_history['id'] != row['id']]
            save_data(df_history)
            st.rerun()
else:
    st.info("표시할 내역이 없습니다.")
