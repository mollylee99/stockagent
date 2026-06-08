import streamlit as st
import yfinance as yf
import google.generativeai as genai

st.set_page_config(page_title="Equity Research", layout="wide")
st.title("📈 AI Equity Research Analyst")

ticker_input = st.sidebar.text_input("Enter Ticker (e.g., PLTR)", "PLTR")
api_key = st.sidebar.text_input("Gemini API Key", type="password")

if ticker_input:
    # 1. 기초 데이터 가져오기
    stock = yf.Ticker(ticker_input)
    info = stock.info
    
    # 대시보드 생성
    st.subheader(f"{ticker_input} 기초 데이터 대시보드")
    col1, col2, col3 = st.columns(3)
    
    col1.metric("최신 주가", f"${info.get('currentPrice', 'N/A')}")
    col2.metric("시가총액", f"${info.get('marketCap', 0):,}")
    col3.metric("52주 최고가", f"${info.get('fiftyTwoWeekHigh', 'N/A')}")
    
    st.write(f"**총 발행 주식 수:** {info.get('sharesOutstanding', 'N/A'):,}")
    st.write(f"**주당순이익(EPS):** {info.get('trailingEps', 'N/A')}")

    # 2. 제미나이 정밀 분석
    if st.sidebar.button("정밀 분석 시작"):
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-pro')
        with st.spinner('분석 중...'):
            prompt = f"{ticker_input}에 대해 지침에 따라 8단계 분석을 수행해."
            response = model.generate_content(prompt)
            st.markdown(response.text)
