#Importações e ferramentas

import time
import plotly.graph_objects as go

import pandas as pd
import streamlit as st
from binance import Client

client = Client("", "") # Aspas vazias porque só dados públicos serão utilizados
 
def get_all_symbols():
    
    try:
        info = client.get_exchange_info()
        symbols = sorted([
            s["symbol"]
            for s in info["symbols"]
            if s['status'] == "TRADING" and s["quoteAsset"] == "USDT"
        ])
        return symbols

    except Exception as e:
       
        print(f"Error to find assets: {e}")
        return ["BTCUSDT", "ETHUSDT"]

# @st.cache_data(ttl=3600) 
def get_historical_data(symbol):
    
    try:
        
        klines = client.get_historical_klines(
            symbol=symbol, 
            interval=Client.KLINE_INTERVAL_1HOUR,
            limit=100
        )
        
        df = pd.DataFrame(klines, columns=[
            "Open Time", "Open", "High", "Low", "Close", "Volume", "Close Time", 
            "Quote Asset Volume", "Number of Trades", "Taker Buy Base Asset Volume", 
            "Taker Buy Quote Asset Volume", "Ignore"
        ])
        
        df["Close"] = df["Close"].astype(float)
        df["Open Time"] = pd.to_datetime(df["Open Time"], unit="ms") 
        df["SMA_50"] = df["Close"].rolling(window=50).mean()
        
        return df[["Open Time", "Open", "High", "Low", "Close", "SMA_50"]].set_index("Open Time")
    
    except Exception as e:
       
        print(f"Failed to load {symbol} history: {e}")
        return pd.DataFrame() 
    
def get_recent_trades(symbol):
    try:
        trades = client.get_recent_trades(symbol=symbol)

        return trades
    
    except Exception as e:
        print(f"Failed to get recent trades for {symbol}: {e}")
        return []
    
    
# --- Interface do usuário ---

def update_price(symbol):
       try:
           ticker = client.get_symbol_ticker(symbol=symbol)
           return float(ticker["price"])
       
       except Exception as e:
           st.error(f"Update failed: {e}")
           return None
       
def create_candlestick_chart(df):
    candlestick = go.Candlestick(
        x=df.index,      
        open=df["Open"], 
        high=df["High"],
        low=df["Low"],
        close=df["Close"],
        name="Price"
    )
    sma_line = go.Scatter(
        x=df.index,
        y=df["SMA_50"],
        line=dict(color="orange", width=1),
        name="SMA 50"
    )
    fig = go.Figure(data=[candlestick, sma_line])

    fig.update_layout(
        title_text="Price Analysis and Movel Avarage (1h Candles)",
        xaxis_rangeslider_visible=False,
        height=550
        )
    
    return fig

AVAILABLE_ASSETS = get_all_symbols()

st.title("Crypto Tracker")
st.markdown("---") 

selected_symbol = st.sidebar.selectbox(
    "Choose Asset:",
    AVAILABLE_ASSETS,
    index=AVAILABLE_ASSETS.index('BTCUSDT') if 'BTCUSDT' in AVAILABLE_ASSETS else 0 
)

placeholder_metric = st.empty() 

st.subheader(f"{selected_symbol} Price History (Last 100h)")
historical_df = get_historical_data(selected_symbol)

if not historical_df.empty:
    plotly_fig = create_candlestick_chart(historical_df)
    st.plotly_chart(plotly_fig, use_container_width=True)
else:
    st.warning("No historical data available.") 

st.subheader(f"Recent Trades for {selected_symbol}")
trades = get_recent_trades(selected_symbol)
df_trades = pd.DataFrame(trades)
df_trades['time'] = pd.to_datetime(df_trades['time'], unit='ms')
st.dataframe(df_trades)

while True:
    price = update_price(selected_symbol)
    
    if price is not None:
        with placeholder_metric.container():
            st.metric(
                label=f"Current Price {selected_symbol}", 
                value=f"${price:,.2f}",
                delta=f"Last Update: {time.strftime("%H:%M:%S")}" 
            )
    time.sleep(5)





