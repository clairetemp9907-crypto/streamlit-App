import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

st.set_page_config(
    page_title="Global Top10 Market Cap Dashboard",
    page_icon="📈",
    layout="wide"
)

st.title("📈 Global Market Cap Top10 Stock Dashboard")
st.caption("최근 1년간 글로벌 시가총액 Top10 기업의 주가 변화")

# 시가총액 Top10 (2025 기준)
stocks = {
    "Apple": "AAPL",
    "Microsoft": "MSFT",
    "NVIDIA": "NVDA",
    "Amazon": "AMZN",
    "Alphabet": "GOOGL",
    "Meta": "META",
    "Saudi Aramco": "2222.SR",
    "Broadcom": "AVGO",
    "TSMC": "TSM",
    "Tesla": "TSLA"
}

selected = st.multiselect(
    "종목 선택",
    list(stocks.keys()),
    default=list(stocks.keys())
)

if len(selected) == 0:
    st.warning("하나 이상의 종목을 선택하세요.")
    st.stop()

end = datetime.today()
start = end - timedelta(days=365)

prices = pd.DataFrame()

for name in selected:
    ticker = stocks[name]

    df = yf.download(
        ticker,
        start=start,
        end=end,
        progress=False,
        auto_adjust=True
    )

    if not df.empty:
        prices[name] = df["Close"]

# 정규화(100 기준)
normalized = prices / prices.iloc[0] * 100

fig = px.line(
    normalized,
    x=normalized.index,
    y=normalized.columns,
    labels={
        "value": "Normalized Price (100)",
        "index": "Date"
    },
    title="1-Year Stock Performance (Normalized)"
)

fig.update_layout(
    height=700,
    hovermode="x unified"
)

st.plotly_chart(fig, use_container_width=True)

st.divider()

st.subheader("현재 가격 및 1년 수익률")

cols = st.columns(len(selected))

for i, stock in enumerate(selected):

    price = prices[stock].iloc[-1]
    ret = (prices[stock].iloc[-1] / prices[stock].iloc[0] - 1) * 100

    cols[i].metric(
        stock,
        f"${price:.2f}",
        f"{ret:.2f}%"
    )

st.divider()

selected_stock = st.selectbox(
    "개별 종목 상세",
    selected
)

ticker = stocks[selected_stock]

detail = yf.download(
    ticker,
    start=start,
    end=end,
    auto_adjust=True,
    progress=False
)

fig2 = px.area(
    detail,
    x=detail.index,
    y="Close",
    title=f"{selected_stock} - 최근 1년"
)

fig2.update_layout(height=500)

st.plotly_chart(fig2, use_container_width=True)

st.dataframe(
    detail.tail(20),
    use_container_width=True
)
