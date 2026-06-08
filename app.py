import streamlit as st
import yfinance as yf
import google.generativeai as genai

st.set_page_config(page_title="Equity Research", layout="wide")
st.title("📈 AI Equity Research Analyst")

# 데이터를 캐싱하여 속도를 높이고 서버 요청 횟수를 줄임
@st.cache_data(ttl=3600) # 1시간 동안 데이터를 기억함
def get_stock_data(ticker):
    stock = yf.Ticker(ticker)
    return stock.info

ticker_input = st.sidebar.text_input("Enter Ticker (e.g., PLTR)", "PLTR")
api_key = st.sidebar.text_input("Gemini API Key", type="password")

if ticker_input:
    try:
        with st.spinner('데이터 로딩 중...'):
            info = get_stock_data(ticker_input)
            
            st.subheader(f"{ticker_input} 기초 데이터 대시보드")
            col1, col2, col3 = st.columns(3)
            
            col1.metric("최신 주가", f"${info.get('currentPrice', 'N/A')}")
            col2.metric("시가총액", f"${info.get('marketCap', 0):,}")
            col3.metric("52주 최고가", f"${info.get('fiftyTwoWeekHigh', 'N/A')}")
            
            st.write(f"**총 발행 주식 수:** {info.get('sharesOutstanding', 'N/A'):,}")
            st.write(f"**주당순이익(EPS):** {info.get('trailingEps', 'N/A')}")
    except Exception as e:
        st.error(f"데이터를 가져오는 중 오류가 발생했습니다. 잠시 후 다시 시도해 주세요: {e}")

    if st.sidebar.button("정밀 분석 시작"):
        if api_key:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-2.5-flesh')
            with st.spinner('분석 중...'):
                prompt = f"{ticker_input}에 대해 지침에 따라 8단계 분석을 수행해."
                response = model.generate_content(prompt)
                st.markdown(response.text)
        else:
            st.warning("API Key를 먼저 입력해주세요.")
