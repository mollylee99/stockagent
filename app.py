import streamlit as st
import google.generativeai as genai

# 시스템 지침을 로드하여 모델에게 주입
SYSTEM_INSTRUCTION = """
[지침: 전문 에퀴티 리서치 애널리스트]
당신은 글로벌 헤지펀드 수석 애널리스트입니다. 
분석 대상 기업의 티커를 입력받으면 다음 8단계 프로세스를 엄격히 수행하십시오.
1. 데이터 식별 및 신뢰성 검증
2. 매크로 및 산업 사이클 분석
3. 연결재무제표 정밀 분석 (LaTeX 및 엑셀 수식 필수)
4. 다차원 주식가치평가
5. 다면적 위험 분석
6. 비정형 데이터(뉴스/리포트) 분석
7. 투자 의사결정 선언
8. 구글 문서/시트 연동 및 결과 출력
"""

def setup_model(api_key):
    genai.configure(api_key=api_key)
    return genai.GenerativeModel('gemini-2.5-flash', system_instruction=SYSTEM_INSTRUCTION)

# Streamlit UI 구성
st.title("Equity Research Analyst Agent")
api_key = st.sidebar.text_input("Gemini API Key", type="password")
ticker = st.text_input("분석할 티커 입력 (예: PLTR)")

if st.button("분석 실행"):
    model = setup_model(api_key)
    with st.spinner("전문 분석 리포트 생성 중..."):
        response = model.generate_content(f"{ticker} 분석을 시작해.")
        st.markdown(response.text)
        # 구글 문서 저장 로직은 추후 Google API 인증 추가 필요
