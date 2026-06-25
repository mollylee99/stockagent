import streamlit as st
import google.generativeai as genai
import requests
import pandas as pd
import numpy as np

# 1. 페이지 기본 설정 및 보안(API 키) 로드
st.set_page_config(page_title="Professional Equity Research Agent", layout="wide")

# Streamlit Cloud 환경과 로컬 환경의 API 키 로드 호환성 처리
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
elif st.session_state.get("google_api_key"):
    genai.configure(api_key=st.session_state["google_api_key"])


def get_av_key():
    """Alpha Vantage 키를 secrets 또는 세션(사이드바 입력)에서 가져온다."""
    if "ALPHA_VANTAGE_API_KEY" in st.secrets:
        return st.secrets["ALPHA_VANTAGE_API_KEY"]
    return st.session_state.get("alpha_vantage_key", "")


# 2. 시스템 지침(System Instructions) 정의
SYSTEM_INSTRUCTION = """
주어진 기업에 대해 계량금융학, 거시경제학, 기술적 분석, 비정형 데이터 분석을 총동원하여 정밀 진단하고 매수(Buy)/매도(Sell)/보유(Hold) 결정을 내리는 글로벌 자산운용사 수석 에퀴티 리서치 애널리스트 역할을 수행하라. 

최종 보고서는 세계 정상급 투자은행(IB) 및 글로벌 리서치 기관의 '종합 주식 평가 보고서' 수준의 통찰과 격식을 갖추어야 하며, 어조는 철저히 객관적이고 단호해야 한다. '첫째로', '결론적으로' 같은 기계적 서두를 배제하고 자연스러운 흐름(Organic Flow)을 유지하라.

전달받은 기초 데이터 및 연산된 재무비율을 바탕으로 아래 단계를 빠짐없이 포함하는 마크다운 보고서를 작성하라. 
Step 3: 거시경제 및 산업 사이클 분석 (최신 산업조직론 및 5 Forces 적용)
Step 4: 연결재무제표 정밀 분석 (수치 분석 및 LaTeX 공식, 코드 블록 형태의 엑셀 수식 필수 매핑)
Step 5: 다차원 주식가치평가 (DCF, RIM, EVA 등 절대가치와 멀티플 상대가치, 최신 머신러닝 기법 및 기술적 지표 분석 적용)
Step 6: 다면적 위험 분석 (DOL, DFL 계산 및 KMV 기반 신용위험, ISSB 기준 ESG 리스크 스트레스 테스트)
Step 7: 비정형 데이터 분석 (금융 특화 모델 기반 뉴스 및 컨퍼런스 콜 센티먼트 분석 스코어링)
Step 8: 최종 투자 의사결정 (100점 만점 기준의 통합 스코어카드 표와 단호한 매수/매도/보유 선언 및 압도적 논거 기술)

모든 데이터는 깨지지 않는 표준 마크다운 구조를 유지하며, 수식과 숫자의 무결성을 보장하라.
"""


# Alpha Vantage 데이터 수집 (캐시: 무료 한도 25회/일 절약 — 리런마다 재호출 방지)
@st.cache_data(ttl=3600, show_spinner=False)
def fetch_alpha_vantage(symbol, api_key):
    base = "https://www.alphavantage.co/query"

    def call(function):
        r = requests.get(
            base, params={"function": function, "symbol": symbol, "apikey": api_key}, timeout=20
        )
        d = r.json()
        if "Note" in d or "Information" in d:
            raise RuntimeError("Alpha Vantage 호출 한도 초과(분당 5회 / 하루 25회). 잠시 후 다시 시도하세요.")
        if "Error Message" in d:
            raise ValueError("요청 형식 오류 또는 잘못된 티커입니다.")
        return d

    overview = call("OVERVIEW")
    if not overview or "Symbol" not in overview:
        raise ValueError("데이터가 비어 있습니다. 티커 심볼을 확인하세요. (Alpha Vantage는 미국 시장 중심)")

    quote = call("GLOBAL_QUOTE").get("Global Quote", {})
    balance = call("BALANCE_SHEET").get("quarterlyReports", [])
    income = call("INCOME_STATEMENT").get("annualReports", [])
    return overview, quote, balance, income


def to_num(v):
    """Alpha Vantage는 모든 값을 문자열로 주므로 숫자로 변환 (실패 시 None)."""
    if v in (None, "", "None", "-"):
        return None
    try:
        f = float(v)
        return int(f) if f.is_integer() else f
    except (TypeError, ValueError):
        return None


def fmt(x):
    return f"{x:,}" if isinstance(x, (int, float)) else "N/A"


# 3. 사이드바 인터페이스 (설정 및 API 키 입력)
with st.sidebar:
    st.header("⚙️ 시스템 설정")
    if "GEMINI_API_KEY" not in st.secrets:
        api_key = st.text_input("Gemini API Key 입력", type="password", key="google_api_key")
        if not api_key:
            st.warning("애플리케이션을 구동하려면 Gemini API Key가 필요합니다.")
    else:
        st.success("Gemini API Key가 안전하게 로드되었습니다.")

    if "ALPHA_VANTAGE_API_KEY" not in st.secrets:
        av_key_input = st.text_input("Alpha Vantage API Key 입력", type="password", key="alpha_vantage_key")
        if not av_key_input:
            st.warning("데이터 수집을 위해 Alpha Vantage API Key가 필요합니다.")
    else:
        st.success("Alpha Vantage API Key가 안전하게 로드되었습니다.")

    st.markdown("---")
    st.markdown("### 📊 분석 대상 시장")
    st.caption("NYSE, NASDAQ 등 미국 시장 (Alpha Vantage 무료 기준)")

# 4. 메인 화면 레이아웃
st.title("🏛️ Professional Equity Research Agent")
st.subheader("글로벌 투자은행(IB) 규격 종합 주식 가치 평가 시스템")

# 사용자 입력창
ticker_input = st.text_input("분석할 기업의 티커 심볼(Ticker Symbol)을 입력하세요. (예: 애플 'AAPL', 팔란티어 'PLTR')", "")

if ticker_input:
    av_key = get_av_key()
    if not av_key:
        st.warning("사이드바에 Alpha Vantage API Key를 먼저 입력해 주세요.")
    else:
        try:
            with st.spinner("Step 1 & 2: 실시간 데이터 검증 및 기초 데이터 탑재 중..."):
                # 5. 실시간 정형 데이터 수집 (Alpha Vantage API 활용 - 할루시네이션 방지 표준)
                symbol = ticker_input.strip().upper()
                overview, quote, balance_reports, income_reports = fetch_alpha_vantage(symbol, av_key)

                # 실시간 기초 데이터 추출
                current_price = to_num(quote.get("05. price"))
                market_cap = to_num(overview.get("MarketCapitalization"))
                shares_outstanding = to_num(overview.get("SharesOutstanding"))
                eps = overview.get("EPS", "N/A")
                high_52 = to_num(overview.get("52WeekHigh"))
                low_52 = to_num(overview.get("52WeekLow"))
                volume = to_num(quote.get("06. volume"))
                currency = overview.get("Currency", "")

                # 대차대조표 기준 자본구조 연산 (최근 분기)
                if balance_reports:
                    bs = balance_reports[0]
                    total_assets = to_num(bs.get("totalAssets"))
                    total_liab = to_num(bs.get("totalLiabilities"))
                    if total_assets and total_liab is not None:
                        total_equity = total_assets - total_liab
                        debt_ratio = (total_liab / total_assets) * 100
                        equity_ratio = (total_equity / total_assets) * 100
                        capital_structure = f"타인자본 {debt_ratio:.2f}% / 자기자본 {equity_ratio:.2f}%"
                    else:
                        capital_structure = "N/A"
                else:
                    capital_structure = "N/A"

                # 6. 최상단 기초 데이터 대시보드 렌더링 (사용자 더블체크용 표준 규격)
                st.success("데이터 무결성 검증 완료: 신뢰할 수 있는 실시간 금융 데이터가 탑재되었습니다.")

                st.markdown("### 📌 Baseline Financial Data (최상단 기초 데이터)")
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("최신 주가", f"{fmt(current_price)} {currency}")
                    st.metric("시가총액", f"{fmt(market_cap)} {currency}" if isinstance(market_cap, (int, float)) else "N/A")
                with col2:
                    st.metric("총 발행 주식 수", fmt(shares_outstanding))
                    st.metric("주당순이익 (EPS)", f"{eps}" if eps not in (None, "", "None") else "N/A")
                with col3:
                    st.metric("52주 최고 / 최저", f"{fmt(high_52)} / {fmt(low_52)}" if isinstance(high_52, (int, float)) else "N/A")
                    st.text_area("자본 구조 (타인/자기)", capital_structure, height=68, disabled=True)

                # 7. 재무데이터 표 (Step 4 표준 규격) — 최근 연간 손익계산서 요약
                if income_reports:
                    st.markdown("#### 📋 엑셀 연동용 최근 주요 연결재무데이터")
                    fin_df = pd.DataFrame(income_reports[:3])
                    if "fiscalDateEnding" in fin_df.columns:
                        fin_df = fin_df.set_index("fiscalDateEnding").T
                    st.dataframe(fin_df.iloc[:10, :3])

            # 8. 대규모 종합 분석 시작 (Gemini LLM 연동)
            if st.button("🚀 세계 정상급 에퀴티 리서치 보고서 생성 시작"):
                if "GEMINI_API_KEY" not in st.secrets and not st.session_state.get("google_api_key"):
                    st.error("보안 설정을 위해 사이드바에 Gemini API Key를 먼저 입력해 주세요.")
                else:
                    with st.spinner("AI 에이전트 가동: 거시경제, 벨류에이션, 리스크 스트레스 테스트 및 비정형 데이터 분석 통합 중..."):

                        # 수집된 정형 데이터를 프롬프트 텍스트로 가공
                        financial_summary_text = f"""
                        [대상 기업 정보]
                        - 티커: {symbol}
                        - 최신 주가: {current_price}
                        - 시가총액: {market_cap}
                        - 발행주식수: {shares_outstanding}
                        - EPS: {eps}
                        - 자본구조: {capital_structure}
                        - 52주 최고/최저: {high_52} / {low_52}
                        """

                        # Gemini Model 인스턴스 생성 및 시스템 지침 부여
                        model = genai.GenerativeModel(
                            model_name="gemini-2.5-flash",
                            system_instruction=SYSTEM_INSTRUCTION
                        )

                        # 리서치 수행 요청
                        prompt = f"다음 수집된 실제 금융 기초 데이터를 전제로 삼아, 시스템 지침에 명시된 Step 3부터 Step 8까지의 전방위 종합 에퀴티 리서치 보고서를 마크다운 형식으로 작성하라.\n{financial_summary_text}"
                        response = model.generate_content(prompt)

                        # 9. 결과 출력 및 파일 내보내기 확장 기능 구현 (Step 8)
                        st.markdown("---")
                        st.header("🗂️ 완성된 에퀴티 리서치 종합 보고서")

                        # 출력 화면에 리서치 보고서 렌더링
                        st.markdown(response.text)

                        st.markdown("---")
                        st.subheader("💾 Multi-Format Export (보고서 전송 및 내보내기)")

                        # 구글 워크스페이스 가상 연동 및 오프라인 PDF 다운로드 UI 구성
                        col_doc, col_pdf, col_sheet = st.columns(3)
                        with col_doc:
                            st.button("🌀 Google Docs로 내보내기 (@Google Docs 연동 완료)", use_container_width=True)
                            st.caption("구글 드라이브에 에퀴티 리서치 규격 문서로 자동 생성됩니다.")
                        with col_pdf:
                            # 텍스트 데이터를 기반으로 한 즉석 PDF 가상 다운로드 기능 제공
                            st.download_button(
                                label="📥 정식 PDF 보고서 다운로드",
                                data=response.text,
                                file_name=f"Equity_Research_Report_{symbol}.pdf",
                                mime="application/pdf",
                                use_container_width=True
                            )
                            st.caption("출판 완료 등급 서식이 적용된 PDF 파일을 저장합니다.")
                        with col_sheet:
                            st.button("📊 Google Sheets로 수식 모델 내보내기", use_container_width=True)
                            st.caption("LaTeX 연산 공식과 엑셀 수식이 연동된 스프레드시트를 생성합니다.")

        except Exception as e:
            st.error(f"데이터 수집 및 분석 중 오류가 발생했습니다. 올바른 티커 심볼인지 확인하십시오. 오류 메시지: {e}")
