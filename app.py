import streamlit as st
import requests
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime

# 1. 실시간 시세 로직 (Naver API)
def get_realtime(ticker):
    url = f"https://polling.finance.naver.com/api/realtime/domestic/stock/{ticker}"
    data = requests.get(url).json()['datas'][0]
    return {
        'price': int(data['nm'].replace(',', '')),
        'high': int(data['hv'].replace(',', '')),
        'diff': int(data['cv'].replace(',', '')),
        'vol': int(data['aq'].replace(',', ''))
    }

# 2. 지표 계산 함수
def analyze_stock(ticker, code):
    # 과거 데이터 로드
    df = yf.Ticker(f"{code}.KS").history(period="70d")
    rt = get_realtime(code)
    
    # 지표 산출
    df.loc[datetime.now(), 'Close'] = rt['price']
    df['S'] = (df['Close'].diff() * df['Volume']).rolling(3).mean() / df['Volume'].mean()
    z_score = (df['S'].iloc[-1] - df['S'].tail(60).mean()) / df['S'].tail(60).std()
    
    # ATR 계산
    df['TR'] = np.maximum(df['High']-df['Low'], np.maximum(abs(df['High']-df['Close'].shift()), abs(df['Low']-df['Close'].shift())))
    atr = df['TR'].tail(14).mean()
    
    peak = df['Close'].max()
    stop_line = peak - (3.0 * atr)
    
    return rt['price'], z_score, stop_line

# 3. UI 구성
st.set_page_config(page_title="부부 주식 비서", layout="centered")
st.title("🕒 3:00 PM 의사결정 대시보드")

user = st.sidebar.selectbox("👤 사용자 선택", ["나(본인)", "와이프"])

# 포트폴리오 설정
portfolio = {
    "나(본인)": {"현대차": "005380", "POSCO홀딩스": "005490"},
    "와이프": {"한국항공우주": "047810"}
}

st.subheader(f"📊 {user}의 실시간 감시 현황")

for name, code in portfolio[user].items():
    price, z, stop = analyze_stock(name, code)
    status = "✅ 보유" if price > stop else "🚨 매도"
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(name, f"{price:,.0f}원")
    with col2:
        st.metric("수급(Z)", f"{z:.2f}", delta="강력" if z >= 1.5 else "보통")
    with col3:
        st.metric("방어선", f"{stop:,.0f}원", delta=status, delta_color="normal" if price > stop else "inverse")
    st.divider()

if st.button("🔄 실시간 데이터 갱신"):
    st.rerun()
