"""Minimal signal bot: Binance Spot public data only. No API keys, no auto-trade."""
import json
import urllib.request

BASE = "https://api.binance.com"
SYMBOL = "BTCUSDT"
INTERVAL = "1h"
LIMIT = 100


def get_json(url, timeout=20):
    req = urllib.request.Request(url, headers={"User-Agent": "signal-bot/0.1"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)


def fetch_klines(symbol=SYMBOL, interval=INTERVAL, limit=LIMIT):
    url = f"{BASE}/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}"
    raw = get_json(url)
    closes = [float(c[4]) for c in raw]
    return closes


def sma(values, period):
    if len(values) < period:
        return None
    return sum(values[-period:]) / period


def rsi(values, period=14):
    if len(values) < period + 1:
        return None
    gains, losses = 0.0, 0.0
    for i in range(len(values) - period, len(values)):
        diff = values[i] - values[i - 1]
        if diff >= 0:
            gains += diff
        else:
            losses += -diff
    if losses == 0:
        return 100.0
    rs = gains / losses
    return 100 - (100 / (1 + rs))


def decide(closes):
    fast = sma(closes, 20)
    slow = sma(closes, 50)
    r = rsi(closes, 14)
    price = closes[-1]
    if fast is None or slow is None or r is None:
        return {"signal": "WAIT", "reason": "not enough data", "price": price}
    if fast > slow and r < 70:
        return {"signal": "BUY_BIAS", "reason": "trend up, not overbought", "price": price, "sma20": fast, "sma50": slow, "rsi14": r}
    if fast < slow and r > 30:
        return {"signal": "SELL_BIAS", "reason": "trend down, not oversold", "price": price, "sma20": fast, "sma50": slow, "rsi14": r}
    return {"signal": "WAIT", "reason": "no edge", "price": price, "sma20": fast, "sma50": slow, "rsi14": r}


if __name__ == "__main__":
    closes = fetch_klines()
    out = decide(closes)
    out["symbol"] = SYMBOL
    out["interval"] = INTERVAL
    print(json.dumps(out, indent=2))
