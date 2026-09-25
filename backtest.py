"""Backtest long-only SMA20/50 + RSI14 di BTCUSDT 1h, ~6 bulan. Stdlib only."""
import json
import urllib.request
from datetime import datetime, timezone, timedelta

BASE = "https://data-api.binance.vision"
SYMBOL = "BTCUSDT"
INTERVAL = "1h"
FEE = 0.001  # 0.1% per side


def get_json(url, timeout=30):
    req = urllib.request.Request(url, headers={"User-Agent": "signal-bot/0.1"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)


def fetch_klines_6mo(symbol=SYMBOL, interval=INTERVAL):
    end = datetime.now(timezone.utc)
    start = end - timedelta(days=180)
    start_ms = int(start.timestamp() * 1000)
    end_ms = int(end.timestamp() * 1000)
    all_k = []
    cur = start_ms
    while cur < end_ms:
        url = f"{BASE}/api/v3/klines?symbol={symbol}&interval={interval}&limit=1000&startTime={cur}"
        batch = get_json(url)
        if not batch:
            break
        all_k.extend(batch)
        cur = batch[-1][0] + 1
        if len(batch) < 1000:
            break
    candles = [{"t": k[0], "o": float(k[1]), "h": float(k[2]), "l": float(k[3]), "c": float(k[4])} for k in all_k]
    return candles


def sma_at(a, i, n):
    if i + 1 < n:
        return None
    return sum(a[i - n + 1:i + 1]) / n


def rsi_at(a, i, p=14):
    if i < p:
        return None
    g = l = 0.0
    for k in range(i - p + 1, i + 1):
        d = a[k] - a[k - 1]
        if d >= 0:
            g += d
        else:
            l += -d
    if l == 0:
        return 100.0
    return 100 - (100 / (1 + g / l))


def run():
    candles = fetch_klines_6mo()
    closes = [c["c"] for c in candles]
    n = len(closes)

    pos = 0.0  # BTC held
    cash = 1000.0
    entry = 0.0
    trades = []
    equity_curve = []
    peak = cash
    max_dd = 0.0

    for i in range(50, n):
        price = closes[i]
        s20 = sma_at(closes, i, 20)
        s50 = sma_at(closes, i, 50)
        r = rsi_at(closes, i, 14)
        buy = s20 > s50 and r < 70
        sell = s20 < s50 and r > 30

        if buy and pos == 0:
            pos = (cash * (1 - FEE)) / price
            entry = price
            entry_t = candles[i]["t"]
            cash = 0.0
        elif sell and pos > 0:
            cash = pos * price * (1 - FEE)
            ret = (price * (1 - FEE)) / (entry * (1 + FEE)) - 1 if entry else 0
            trades.append({"entry_t": entry_t, "exit_t": candles[i]["t"], "entry": entry, "exit": price, "ret": ret})
            pos = 0.0

        equity = cash if pos == 0 else pos * price
        equity_curve.append(equity)
        peak = max(peak, equity)
        dd = equity / peak - 1
        max_dd = min(max_dd, dd)

    # close open position at last price
    if pos > 0:
        price = closes[-1]
        cash = pos * price * (1 - FEE)
        ret = (price * (1 - FEE)) / (entry * (1 + FEE)) - 1 if entry else 0
        trades.append({"entry_t": entry_t, "exit_t": candles[-1]["t"], "entry": entry, "exit": price, "ret": ret, "open_exit": True})
        pos = 0.0

    wins = sum(1 for t in trades if t["ret"] > 0)
    total_ret = cash / 1000 - 1
    bh_ret = closes[-1] / closes[50] - 1
    avg_ret = sum(t["ret"] for t in trades) / len(trades) if trades else 0

    out = {
        "symbol": SYMBOL, "interval": INTERVAL,
        "candles": n,
        "from": datetime.fromtimestamp(candles[0]["t"] / 1000, tz=timezone.utc).isoformat(),
        "to": datetime.fromtimestamp(candles[-1]["t"] / 1000, tz=timezone.utc).isoformat(),
        "strategy": "long-only: BUY when SMA20>SMA50 & RSI<70, SELL when SMA20<SMA50 & RSI>30, fee 0.1%/side",
        "start_equity": 1000.0, "end_equity": round(cash, 2),
        "total_return_pct": round(total_ret * 100, 2),
        "buy_hold_return_pct": round(bh_ret * 100, 2),
        "trades": len(trades),
        "wins": wins,
        "win_rate_pct": round(wins / len(trades) * 100, 1) if trades else 0,
        "avg_trade_ret_pct": round(avg_ret * 100, 2),
        "max_drawdown_pct": round(max_dd * 100, 2),
        "last_trades": trades[-10:],
    }
    with open("backtest_result.json", "w") as f:
        json.dump(out, f, indent=2)
    print(json.dumps({k: v for k, v in out.items() if k != "last_trades"}, indent=2))
    if trades:
        print(f"\nLast trade exit: {datetime.fromtimestamp(trades[-1]['exit_t']/1000, tz=timezone.utc).isoformat()} ret={trades[-1]['ret']*100:.2f}%")


if __name__ == "__main__":
    run()
