import streamlit as st
import pandas as pd
import yfinance as yf
import requests
from datetime import datetime

# 데이터 가져오기 함수
def get_stock_data(name, code):
    try:
        # 실시간 가격 (네이버)
        url = f"https://polling.finance.naver.com/api/realtime/domestic/stock/{code}"
        live = requests.get(url, timeout=5).json()['datas'][0]
        curr_p = int(live['nm'].replace(',', ''))
        
        # 과거 데이터 (yfinance)
        df = yf.Ticker(f"{code}.KS").history(period="60d")
        
        # ATR 계산
        df['H-L'] = df['High'] - df['Low']
        df['H-PC'] = (df['High'] - df['Close'].shift(1)).abs()
        df['L-PC'] = (df['Low'] - df['Close'].shift(1)).abs()
        df['TR'] = df[['H-L', 'H-PC', 'L-PC']].max(axis=1)
        atr = df['TR'].tail(14).mean()
        
        # 방어선 계산
        peak_p = max(df['Close'].max(), int(live['hv'].replace(',', '')))
        stop_line = peak_p - (3.0 * atr)
        
        return curr_p, stop_line
    except:
        return None, None

# UI 설정
st.set_page_config(page_title="부부 주식 비서", layout="wide")
st.title("🕒 3:00 PM 의사결정 대시보드")

user = st.sidebar.selectbox("👤 사용자 선택", ["본인", "와이프"])
portfolio = {
    "본인": {"현대차": "005380", "POSCO홀딩스": "005490"},
    "와이프": {"한국항공우주": "047810"}
}

st.info(f"현재 시각 {datetime.now().strftime('%H:%M')} 기준 분석")

for name, code in portfolio[user].items():
    price, stop = get_stock_data(name, code)
    if price:
        status = "✅ 보유" if price > stop else "🚨 매도"
        color = "green" if price > stop else "red"
        
        col1, col2 = st.columns(2)
        col1.metric(name, f"{price:,.0f}원", delta=f"상태: {status}")
        col2.markdown(f"### 방어선: :{color}[{stop:,.0f}원]")
        st.divider()

if st.button("🔄 실시간 갱신"):
    st.rerun()
