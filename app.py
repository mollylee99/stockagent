import streamlit as st
import google.generativeai as genai

st.set_page_config(page_title="Equity Research", layout="wide")
st.title("📈 AI Equity Research Analyst")

ticker_input = st.sidebar.text_input("분석할 티커 입력 (예: PLTR)", "PLTR")
api_key = st.sidebar.text_input("Gemini API Key", type="password")

if ticker_input and st.sidebar.button("분석 및 대시보드 생성"):
    if not api_key:
        st.warning("API Key를 입력해주세요.")
    else:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        with st.spinner('데이터 추출 및 분석 중...'):
            # 모델에게 데이터 조회를 직접 명령 (지침 2단계 반영)
            prompt = f"""
            {ticker_input}의 최신 기초 데이터를 검색하여 표로 정리해.
            [최신 주가, 시가총액, 총 발행 주식 수, EPS, 52주 최고/최저가]
            그 후, 지침에 따라 8단계 분석 프로세스를 즉시 수행해.
            모든 결과는 마크다운 표와 LaTeX 수식으로 출력할 것.
            """
            response = model.generate_content(prompt)
            st.markdown(response.text)
