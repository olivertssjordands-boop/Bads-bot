import os
import time
import datetime
import requests
import pandas as pd
import numpy as np
import yfinance as yf
from flask import Flask
from threading import Thread

# --- Web Server for Render Free Tier ---
app = Flask('')

@app.route('/')
def home():
    return "🤖 Index Trading Bot is Live and Running 24/7!"

def run_web():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run_web)
    t.daemon = True
    t.start()

# --- Secrets Ko Render Environment Variables Se Fetch Karna ---
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# --- Target Symbols ---
INDICES = {
    "NIFTY 50": "^NSEI",
    "BANKNIFTY": "^NSEBANK",
    "SENSEX": "^BSESN"
}

def send_telegram_alert(message):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("[ERROR] Telegram Credentials are missing in Environment Variables!")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"[ERROR] Failed to send alert: {e}")

def fetch_data(symbol, interval="5m", period="5d"):
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period=period, interval=interval)
        if df.empty:
            return None
        return df
    except Exception as e:
        print(f"[ERROR] Data fetch error for {symbol}: {e}")
        return None

def calculate_indicators(df):
    df['EMA9'] = df['Close'].ewm(span=9, adjust=False).mean()
    df['EMA21'] = df['Close'].ewm(span=21, adjust=False).mean()
    
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    return df

def scan_market():
    for name, symbol in INDICES.items():
        df = fetch_data(symbol, interval="5m", period="5d")
        if df is None or len(df) < 25:
            continue
            
        df = calculate_indicators(df)
        
        latest = df.iloc[-1]
        previous = df.iloc[-2]
        
        current_price = round(latest['Close'], 2)
        
        if previous['EMA9'] <= previous['EMA21'] and latest['EMA9'] > latest['EMA21']:
            sl = round(current_price * 0.997, 2)
            tp = round(current_price * 1.006, 2)
            msg = (
                f"🚨 *REAL-TIME BUY SIGNAL* 🚨\n\n"
                f"📊 *Index:* {name}\n"
                f"💵 *Price:* ₹{current_price}\n"
                f"📈 *RSI:* {round(latest['RSI'], 2)}\n"
                f"🎯 *Target:* ₹{tp}\n"
                f"🛑 *Stoploss:* ₹{sl}\n"
                f"⏰ *Time:* {datetime.datetime.now().strftime('%H:%M:%S IST')}"
            )
            send_telegram_alert(msg)

def main():
    print("🤖 Index Trading Telegram Bot Started...")
    send_telegram_alert("🚀 *Index Trading Bot Activated!* Live market scanning running securely on Render.")
    
    while True:
        try:
            print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Scanning Indices...")
            scan_market()
            time.sleep(60)
        except Exception as e:
            print(f"[ERROR] Loop Exception: {e}")
            time.sleep(15)

if __name__ == "__main__":
    keep_alive()
    main()
    while True:
        try:
            print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Scanning Indices...")
            scan_market()
            time.sleep(60)
        except Exception as e:
            print(f"[ERROR] Loop Exception: {e}")
            time.sleep(15)

if __name__ == "__main__":
    keep_alive()
    main()
    def s5_vwap_validation(self):
        """5. VWAP / Price Position"""
        typical_price = (self.df['high'] + self.df['low'] + self.df['close']) / 3
        vwap = (self.df['volume'] * typical_price).cumsum() / (self.df['volume'].cumsum() + 1e-10)
        if self.df['close'].iloc[-1] > vwap.iloc[-1]:
            return 1
        elif self.df['close'].iloc[-1] < vwap.iloc[-1]:
            return -1
        return 0

    def s6_supertrend_structure(self):
        """6. ATR-based Price Action Structure"""
        hl2 = (self.df['high'] + self.df['low']) / 2
        sma20 = hl2.rolling(10).mean()
        if self.df['close'].iloc[-1] > sma20.iloc[-1]:
            return 1
        elif self.df['close'].iloc[-1] < sma20.iloc[-1]:
            return -1
        return 0

    def s7_volume_spike(self):
        """7. Volume Spike Confirmation"""
        avg_vol = self.df['volume'].rolling(20).mean().iloc[-1]
        curr_vol = self.df['volume'].iloc[-1]
        is_green = self.df['close'].iloc[-1] > self.df['open'].iloc[-1]
        if curr_vol > (1.2 * avg_vol):
            return 1 if is_green else -1
        return 0

    def s8_stochastic_oscillator(self):
        """8. Stochastic %K and %D"""
        low_14 = self.df['low'].rolling(14).min()
        high_14 = self.df['high'].rolling(14).max()
        k = 100 * ((self.df['close'] - low_14) / (high_14 - low_14 + 1e-10))
        d = k.rolling(3).mean()
        if k.iloc[-1] > d.iloc[-1] and k.iloc[-1] < 80:
            return 1
        elif k.iloc[-1] < d.iloc[-1] and k.iloc[-1] > 20:
            return -1
        return 0

    def s9_candlestick_patterns(self):
        """9. Bullish/Bearish Engulfing Pattern"""
        p_open, p_close = self.df['open'].iloc[-2], self.df['close'].iloc[-2]
        c_open, c_close = self.df['open'].iloc[-1], self.df['close'].iloc[-1]
        
        if c_close > c_open and p_close < p_open and c_close >= p_open:
            return 1
        elif c_close < c_open and p_close > p_open and c_close <= p_open:
            return -1
        return 0

    def s10_atr_volatility(self):
        """10. ATR Expansion Confirmation"""
        high_low = self.df['high'] - self.df['low']
        atr = high_low.rolling(14).mean().iloc[-1]
        curr_range = self.df['high'].iloc[-1] - self.df['low'].iloc[-1]
        if curr_range > (1.1 * atr):
            return 1 if self.df['close'].iloc[-1] > self.df['open'].iloc[-1] else -1
        return 0

    def evaluate(self):
        """Runs all 10 strategies and returns scores."""
        scores = [
            self.s1_ema_crossover(),
            self.s2_rsi_momentum(),
            self.s3_macd_signal(),
            self.s4_bollinger_breakout(),
            self.s5_vwap_validation(),
            self.s6_supertrend_structure(),
            self.s7_volume_spike(),
            self.s8_stochastic_oscillator(),
            self.s9_candlestick_patterns(),
            self.s10_atr_volatility()
        ]
        buy_pass = sum([1 for score in scores if score == 1])
        sell_pass = sum([1 for score in scores if score == -1])
        return buy_pass, sell_pass

# ==========================================
# MARKET SCANNER & CALCULATIONS
# ==========================================
def scan_symbol(name, ticker, timeframe):
    try:
        period = "5d" if timeframe in ["1m", "5m"] else "1mo"
        df = yf.download(ticker, period=period, interval=timeframe, progress=False)
        
        if df.empty or len(df) < 30:
            return

        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
            
        df.columns = [c.lower() for c in df.columns]

        evaluator = StrategyEvaluator(df)
        buy_score, sell_score = evaluator.evaluate()

        current_price = round(float(df['close'].iloc[-1]), 2)
        
        high_low = df['high'] - df['low']
        atr = float(high_low.rolling(14).mean().iloc[-1])
        if np.isnan(atr) or atr == 0:
            atr = current_price * 0.005

        sl_distance = round(atr * 1.5, 2)
        tp_distance = round(atr * 2.7, 2)

        duration_map = {
            "1m": "10-25 Minutes",
            "5m": "30-60 Minutes",
            "15m": "1-3 Hours",
            "1h": "Intraday / Till Market Close"
        }
        est_time = duration_map.get(timeframe, "1-2 Hours")

        signal_key = f"{name}_{timeframe}"
        now = time.time()
        
        # Cooldown check: max 1 alert per 5 mins per timeframe
        if signal_key in last_signal_time and (now - last_signal_time[signal_key]) < 300:
            return

        # 8 out of 10 strategies MUST pass
        if buy_score >= 8:
            sl = round(current_price - sl_distance, 2)
            tp = round(current_price + tp_distance, 2)
            
            msg = (
                f"🚨 *HIGH-PROBABILITY BUY SIGNAL* 🚨\n\n"
                f"📊 *Index:* {name}\n"
                f"⏱ *Timeframe:* {timeframe}\n"
                f"🎯 *Strategy Score:* {buy_score}/10 Passed\n\n"
                f"💵 *Entry Price:* {current_price}\n"
                f"🎯 *Target (TP):* {tp}\n"
                f"🛑 *Stop Loss (SL):* {sl}\n\n"
                f"⏳ *Est. Target Time:* {est_time}\n"
                f"⏰ *Scan Time:* {datetime.datetime.now().strftime('%H:%M:%S IST')}\n"
                f"⚡ *Rule:* Trade only on candle confirmation!"
            )
            send_telegram_alert(msg)
            last_signal_time[signal_key] = now

        elif sell_score >= 8:
            sl = round(current_price + sl_distance, 2)
            tp = round(current_price - tp_distance, 2)
            
            msg = (
                f"🔻 *HIGH-PROBABILITY SELL SIGNAL* 🔻\n\n"
                f"📊 *Index:* {name}\n"
                f"⏱ *Timeframe:* {timeframe}\n"
                f"🎯 *Strategy Score:* {sell_score}/10 Passed\n\n"
                f"💵 *Entry Price:* {current_price}\n"
                f"🎯 *Target (TP):* {tp}\n"
                f"🛑 *Stop Loss (SL):* {sl}\n\n"
                f"⏳ *Est. Target Time:* {est_time}\n"
                f"⏰ *Scan Time:* {datetime.datetime.now().strftime('%H:%M:%S IST')}\n"
                f"⚡ *Rule:* Trade only on candle confirmation!"
            )
            send_telegram_alert(msg)
            last_signal_time[signal_key] = now

    except Exception as e:
        print(f"[ERROR] Error scanning {name} ({timeframe}): {e}")

# ==========================================
# MAIN LOOP
# ==========================================
def main():
    print("🤖 Index Trading Telegram Bot Started...")
    send_telegram_alert("🤖 *Index Trading Bot Activated!* Scanning 10 Strategies for Nifty, Bank Nifty & Sensex...")
    
    while True:
        try:
            for name, ticker in SYMBOLS.items():
                for tf in TIMEFRAMES:
                    scan_symbol(name, ticker, tf)
                    time.sleep(1)
            
            time.sleep(30)
            
        except KeyboardInterrupt:
            print("Bot Stopped by User.")
            break
        except Exception as e:
            print(f"[CRITICAL ERROR] Bot Loop Exception: {e}")
            time.sleep(10)

if __name__ == "__main__":
    main()
