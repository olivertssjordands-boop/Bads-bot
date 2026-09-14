import time
import datetime
import requests
import pandas as pd
import numpy as np
import yfinance as yf

# ==========================================
# CONFIGURATION & PARAMETERS
# ==========================================
# Yahan apna Telegram Bot Token aur Chat ID dalein
TELEGRAM_BOT_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN_HERE"
TELEGRAM_CHAT_ID = "YOUR_TELEGRAM_CHAT_ID_HERE"

# Index symbols for Yahoo Finance
SYMBOLS = {
    "NIFTY 50": "^NSEI",
    "BANKNIFTY": "^NSEBANK",
    "SENSEX": "^BSESN"
}

# Scan timeframes (1m, 5m, 15m, 1h)
TIMEFRAMES = ["1m", "5m", "15m", "1h"]

# Cooldown record to avoid spamming same signal
last_signal_time = {}

# ==========================================
# TELEGRAM ALERT HELPER
# ==========================================
def send_telegram_alert(message):
    if TELEGRAM_BOT_TOKEN == "YOUR_TELEGRAM_BOT_TOKEN_HERE":
        print("[WARNING] Please set your TELEGRAM_BOT_TOKEN in app.py!")
        print(message)
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    try:
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code != 200:
            print(f"[ERROR] Telegram API Error: {response.text}")
    except Exception as e:
        print(f"[ERROR] Failed to send Telegram alert: {e}")

# ==========================================
# 10 STRATEGIES EVALUATOR ENGINE
# ==========================================
class StrategyEvaluator:
    def __init__(self, df):
        self.df = df

    def s1_ema_crossover(self):
        """1. EMA 9 / EMA 21 Trend & Cross"""
        ema9 = self.df['close'].ewm(span=9, adjust=False).mean()
        ema21 = self.df['close'].ewm(span=21, adjust=False).mean()
        if ema9.iloc[-1] > ema21.iloc[-1]:
            return 1
        elif ema9.iloc[-1] < ema21.iloc[-1]:
            return -1
        return 0

    def s2_rsi_momentum(self):
        """2. RSI Multi-zone Strength"""
        delta = self.df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / (loss + 1e-10)
        rsi = 100 - (100 / (1 + rs))
        val = rsi.iloc[-1]
        if val >= 55:
            return 1
        elif val <= 45:
            return -1
        return 0

    def s3_macd_signal(self):
        """3. MACD Histogram & Signal Cross"""
        exp1 = self.df['close'].ewm(span=12, adjust=False).mean()
        exp2 = self.df['close'].ewm(span=26, adjust=False).mean()
        macd = exp1 - exp2
        signal = macd.ewm(span=9, adjust=False).mean()
        if macd.iloc[-1] > signal.iloc[-1]:
            return 1
        elif macd.iloc[-1] < signal.iloc[-1]:
            return -1
        return 0

    def s4_bollinger_breakout(self):
        """4. Bollinger Bands Expansion / Touch"""
        sma = self.df['close'].rolling(20).mean()
        std = self.df['close'].rolling(20).std()
        upper = sma + (std * 2)
        lower = sma - (std * 2)
        cp = self.df['close'].iloc[-1]
        if cp > upper.iloc[-1]:
            return 1
        elif cp < lower.iloc[-1]:
            return -1
        return 0

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
