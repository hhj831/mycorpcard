import streamlit as st
import re
import pandas as pd
from datetime import datetime

# 1. 앱 페이지 설정 (메드트로닉 네이비 테마 반영)
st.set_page_config(page_title="Corporate Expense Manager", layout="centered")

# 메드트로닉 스타일 CSS 적용
st.markdown("""
    <style>
    .main { background-color: #ffffff; }
    .stMetric { background-color: #f0f2f6; padding: 15px; border-radius: 10px; border-left: 5px solid #002855; }
    div[data-testid="stMetricValue"] { color: #002855; }
    .stButton>button { background-color: #002855; color: white; border-radius: 5px; width: 100%; }
    .warning-text { color: #dc3545; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

st.title("💙 Medtronic Expense Tracker")
st.caption("법인비용 관리 시스템 (미팅 및 식대)")

# 2. 데이터 및 설정값 유지 (세션 상태)
if 'history' not in st.session_state:
    st.session_state.history = []
if 'limit_meeting' not in st.session_state:
    st.session_state.limit_meeting = 300000  # 기본값 30만 원

LIMIT_MEAL_TOTAL = 100000  # 개인식사 월 한도
LIMIT_MEAL_PER_USE = 15000 # 개인식사 건당 한도

# --- [사이드바] 한도 설정 및 관리 ---
with st.sidebar:
    st.header("⚙️ 관리자 설정")
    new_limit = st.number_input("대리점 미팅 월 한도 변경", value=st.session_state.limit_meeting, step=10000)
    if st.button("한도 적용하기"):
        st.session_state.limit_meeting = new_limit
        st.success("미팅 한도가 변경되었습니다.")
    
    st.divider()
    st.subheader("🧹 데이터 초기화")
    if st.button("대리점 미팅 내역만 삭제"):
        st.session_state.history = [i for i in st.session_state.history if i['항목'] != "대리점미팅"]
        st.rerun()
    if st.button("개인 식사 내역만 삭제"):
        st.session_state.history = [i for i in st.session_state.history if i['항목'] != "개인식사"]
        st.rerun()

# --- 상단 잔액 대시보드 ---
total_meeting = sum(item['금액'] for item in st.session_state.history if item['항목'] == "대리점미팅")
total_meal = sum(item['금액'] for item in st.session_state.history if item['항목'] == "개인식사")

rem_meeting = st.session_state.limit_meeting - total_meeting
rem_meal = LIMIT_MEAL_TOTAL - total_meal

col1, col2 = st.columns(2)

with col1:
    # 잔액 3만원 미만 시 빨간색 표시
    color_m = "normal" if rem_meeting > 30000 else "inverse"
    st.metric("🤝 대리점 미팅 잔액", f"{rem_meeting:,}원", delta=f"한도: {st.session_state.limit_meeting:,}", delta_color=color_m)
    if rem_meeting <= 30000:
        st.markdown("<span class='warning-text'>⚠️ 미팅 예산이 3만원 이하입니다!</span>", unsafe_allow_html=True)

with col2:
    color_f = "normal" if rem_meal > 30000 else "inverse"
    st.metric("🍚 개인 식사 잔액", f"{rem_meal:,}원", delta=f"한도: {LIMIT_MEAL_TOTAL:,}", delta_color=color_f)
    if rem_meal <= 30000:
        st.markdown("<span class='warning-text'>⚠️ 식사 예산이 3만원 이하입니다!</span>", unsafe_allow_html=True)

st.divider()

# --- 입력 섹션 ---
st.subheader("📥 내역 입력")
sms_input = st.text_area("카드 승인 문자를 붙여넣으세요", height=100)
category = st.radio("항목 선택", ["대리점미팅", "개인식사"], horizontal=True)

if st.button("내역 등록"):
    if sms_input:
        amount_match = re.search(r'([0-9,]+)원', sms_input)
        if amount_match:
            amount = int(amount_match.group(1).replace(',', ''))
            
            # 개인식사 건당 한도 체크
            if category == "개인식사" and amount > LIMIT_MEAL_PER_USE:
                st.error(f"🚨 경고: 개인식사 건당 한도(15,000원)를 초과했습니다! (결제금액: {amount:,}원)")
            
            new_entry = {
                "날짜": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "항목": category,
                "금액": amount,
                "비고": "건당초과" if (category == "개인식사" and amount > LIMIT_MEAL_PER_USE) else "-"
            }
            st.session_state.history.insert(0, new_entry)
            st.success("성공적으로 등록되었습니다.")
            st.rerun()
        else:
            st.error("금액 인식 실패. 문자 형식을 확인하세요.")

# --- 상세 내역 테이블 ---
st.subheader("📋 사용 상세 내역")
if st.session_state.history:
    df = pd.DataFrame(st.session_state.history)
    # 초과된 식사 내역 강조 스타일링 (생략 가능)
    st.dataframe(df, use_container_width=True)
else:
    st.info("등록된 내역이 없습니다.")
