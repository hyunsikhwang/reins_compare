import yfinance as yf
import pandas as pd
from pyecharts import options as opts
from pyecharts.charts import Line
from pyecharts.globals import ThemeType
import streamlit as st
from streamlit_echarts import st_pyecharts

# Streamlit Page Config
st.set_page_config(page_title="Swiss Re vs RGA Comparison", layout="wide")

st.title("Swiss Re vs RGA: Market Cap & Return (2025-2026)")

# 1. 데이터 수집 함수
def get_market_data_final(ticker_symbol, start_date):
    ticker = yf.Ticker(ticker_symbol)
    hist = ticker.history(start=start_date, auto_adjust=False)
    if hist.empty: return None, None
    price = hist['Adj Close'] if 'Adj Close' in hist.columns else hist['Close']
    
    try:
        shares_data = ticker.get_shares_full(start=start_date)
        if shares_data is not None and not shares_data.empty:
            shares_series = pd.Series(shares_data)
            shares_series = shares_series[~shares_series.index.duplicated(keep='last')]
        else:
            shares_series = pd.Series([ticker.info.get('sharesOutstanding')], index=[price.index[0]])
    except:
        shares_series = pd.Series([ticker.info.get('sharesOutstanding')], index=[price.index[0]])

    shares_aligned = shares_series.reindex(price.index, method='ffill').bfill()
    return price, shares_aligned

# 2. 데이터 처리
start_date = "2025-01-01"

with st.spinner("금융 데이터를 수집 중입니다..."):
    sren_price, sren_shares = get_market_data_final("SREN.SW", start_date)
    rga_price, rga_shares = get_market_data_final("RGA", start_date)

    if sren_price is None or rga_price is None:
        st.error("데이터를 불러오는데 실패했습니다.")
        st.stop()

    # 환율 데이터
    fx_data = yf.Ticker("CHFUSD=X").history(start=start_date)['Close']

    # 시가총액 및 수익률 계산 (Billion USD)
    sren_mcap = (sren_price * sren_shares * fx_data.reindex(sren_price.index, method='ffill').bfill()) / 1e9
    rga_mcap = (rga_price * rga_shares) / 1e9

    df = pd.DataFrame({'SREN': sren_mcap, 'RGA': rga_mcap}).ffill().dropna()
    df_return = (df / df.iloc[0] - 1) * 100
    x_data = df.index.strftime('%Y-%m-%d').tolist()

# 3. pyecharts 시각화 설정
chart = (
    Line(init_opts=opts.InitOpts(width="100%", height="600px", theme=ThemeType.WHITE))
    .add_xaxis(xaxis_data=x_data)
    # 왼쪽 축: 시가총액
    .add_yaxis(
        "Swiss Re MCap (B USD)", 
        df['SREN'].round(2).tolist(), 
        yaxis_index=0, 
        color="#003366", 
        linestyle_opts=opts.LineStyleOpts(width=3)
    )
    .add_yaxis(
        "RGA MCap (B USD)", 
        df['RGA'].round(2).tolist(), 
        yaxis_index=0, 
        color="#C8102E", 
        linestyle_opts=opts.LineStyleOpts(width=3)
    )
    # 오른쪽 축 추가: 수익률
    .extend_axis(
        yaxis=opts.AxisOpts(
            name="Return (%)", 
            type_="value", 
            axislabel_opts=opts.LabelOpts(formatter="{value}%"),
            splitline_opts=opts.SplitLineOpts(is_show=False)
        )
    )
    .add_yaxis(
        "Swiss Re Return (%)", 
        df_return['SREN'].round(2).tolist(), 
        yaxis_index=1, 
        color="#003366", 
        is_symbol_show=False, 
        linestyle_opts=opts.LineStyleOpts(width=2, type_="dashed", opacity=0.5)
    )
    .add_yaxis(
        "RGA Return (%)", 
        df_return['RGA'].round(2).tolist(), 
        yaxis_index=1, 
        color="#C8102E", 
        is_symbol_show=False, 
        linestyle_opts=opts.LineStyleOpts(width=2, type_="dashed", opacity=0.5)
    )
    .set_global_opts(
        title_opts=opts.TitleOpts(title="Swiss Re vs RGA: Market Cap & Return (2025-2026)", pos_left="center"),
        tooltip_opts=opts.TooltipOpts(trigger="axis", axis_pointer_type="cross"),
        legend_opts=opts.LegendOpts(pos_top="10%"),
        xaxis_opts=opts.AxisOpts(boundary_gap=False),
        yaxis_opts=opts.AxisOpts(name="Market Cap (B USD)"),
        datazoom_opts=[opts.DataZoomOpts(), opts.DataZoomOpts(type_="inside")],
    )
)

# 4. Streamlit에서 출력
st_pyecharts(chart, height="600px")