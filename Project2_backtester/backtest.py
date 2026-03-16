from datetime import timedelta

import numpy as np
import pandas as pd

import config
import fetch_data
import indicators as ind
import strategy


STOCKLIST = [
    "AAPL", "MSFT", "AMZN", "GOOG", "META", "NVDA",
    "XOM", "CVX", "COP", "EOG", "SLB",
    "SPY", "DIA", "QQQ", "XLK", "VGT", "SOXX", "SMH", "XLE", "VDE", "IYE", "XOP",
]

INITIAL_CAPITAL = 10000.0
MAX_POSITIONS = 20
MIN_ENTRY_CAPITAL = 1000.0
DAY_PROGRESS_EVERY = 25


def _safe_fetch(stock, start_date, end_date):
    try:
        return fetch_data.fetch_data(stock, start_date, end_date)
    except Exception:
        return pd.DataFrame()


def _safe_latest_price(df):
    if df.empty or "Close" not in df.columns:
        return None
    value = df["Close"].iloc[-1]
    if value is None or np.isnan(value):
        return None
    return float(value)


def _slice_until(df, end_day):
    if df.empty:
        return df
    return df.loc[df.index <= pd.Timestamp(end_day)]


def _prefetch_data(start_date, end_date, days_w, r_days_w):
    warmup_days = int(max(days_w * 1.5, r_days_w * 1.5))
    preload_start = (pd.to_datetime(start_date) - timedelta(days=warmup_days)).strftime("%Y-%m-%d")
    preload_end = (pd.to_datetime(end_date) + timedelta(days=1)).strftime("%Y-%m-%d")

    data_cache = {}
    total = len(STOCKLIST)
    for idx, stock in enumerate(STOCKLIST, start=1):
        print(f"Prefetching {stock} ({idx}/{total})...", flush=True)
        stock_df = _safe_fetch(stock, preload_start, preload_end)
        data_cache[stock] = stock_df
        if stock_df.empty:
            print(f"  -> {stock}: no rows downloaded", flush=True)
        else:
            print(
                f"  -> {stock}: {len(stock_df)} rows ({stock_df.index.min().date()} to {stock_df.index.max().date()})",
                flush=True,
            )

    non_empty = sum(1 for df in data_cache.values() if not df.empty)
    print(f"Prefetch complete: {non_empty}/{total} symbols have data", flush=True)
    return data_cache


def _portfolio_is_viable(capital, positions, latest_prices):
    if not np.isfinite(capital) or capital < 0:
        return False, capital

    if len(positions) > MAX_POSITIONS:
        return False, capital

    total_value = float(capital)
    for stock, info in positions.items():
        shares = info.get("shares", 0)
        if shares <= 0:
            return False, total_value

        mark_price = latest_prices.get(stock)
        if mark_price is None:
            mark_price = info.get("entry_price", 0)
        total_value += float(shares) * float(mark_price)

    if (not np.isfinite(total_value)) or total_value <= 0:
        return False, total_value

    return True, total_value


def _compute_daily_equity(cash, positions, latest_prices, last_known_prices):
    positions_value = 0.0
    for stock, info in positions.items():
        shares = float(info.get("shares", 0))
        mark_price = latest_prices.get(stock)
        if mark_price is None:
            mark_price = last_known_prices.get(stock)
        if mark_price is None:
            mark_price = float(info.get("entry_price", 0.0))
        positions_value += shares * float(mark_price)

    equity = float(cash) + positions_value
    return positions_value, equity


def _compute_max_drawdown(equity_values):
    if not equity_values:
        return 0.0

    peak = equity_values[0]
    max_dd = 0.0
    for equity in equity_values:
        if equity > peak:
            peak = equity
        if peak > 0:
            drawdown = (equity / peak) - 1.0
            if drawdown < max_dd:
                max_dd = drawdown
    return max_dd * 100.0


def _compute_spy_total_return_pct(data_cache, start_date, end_date):
    spy_df = data_cache.get("SPY", pd.DataFrame())
    if spy_df.empty:
        return 0.0

    period_df = spy_df.loc[
        (spy_df.index >= pd.Timestamp(start_date)) & (spy_df.index <= pd.Timestamp(end_date))
    ]
    if period_df.empty or len(period_df) < 2:
        return 0.0

    start_price = float(period_df["Close"].iloc[0])
    end_price = float(period_df["Close"].iloc[-1])
    if start_price <= 0:
        return 0.0
    return ((end_price / start_price) - 1.0) * 100.0


def compute_metrics(equity_curve, trade_pnls, start_capital, start_date, end_date, spy_total_return_pct):
    if not equity_curve:
        final_value = float(start_capital)
        total_return_pct = 0.0
        cagr_pct = 0.0
        max_drawdown_pct = 0.0
        sharpe_ratio = 0.0
    else:
        final_value = float(equity_curve[-1]["equity"])
        total_return_pct = ((final_value / float(start_capital)) - 1.0) * 100.0 if start_capital > 0 else 0.0

        duration_days = max((pd.to_datetime(end_date) - pd.to_datetime(start_date)).days, 1)
        years = duration_days / 365.25
        if years > 0 and start_capital > 0 and final_value > 0:
            cagr_pct = (((final_value / float(start_capital)) ** (1.0 / years)) - 1.0) * 100.0
        else:
            cagr_pct = 0.0

        equity_values = [float(row["equity"]) for row in equity_curve]
        max_drawdown_pct = _compute_max_drawdown(equity_values)

        equity_series = pd.Series(equity_values)
        daily_returns = equity_series.pct_change().dropna()
        if daily_returns.empty or float(daily_returns.std()) == 0.0:
            sharpe_ratio = 0.0
        else:
            sharpe_ratio = float((daily_returns.mean() / daily_returns.std()) * np.sqrt(252))

    wins = [x for x in trade_pnls if x > 0]
    losses = [x for x in trade_pnls if x < 0]
    closed_trades = len(trade_pnls)

    if closed_trades > 0:
        win_rate_pct = (len(wins) / closed_trades) * 100.0
    else:
        win_rate_pct = 0.0

    avg_win = float(np.mean(wins)) if wins else 0.0
    avg_loss = float(np.mean(losses)) if losses else 0.0

    gross_profit = float(np.sum(wins)) if wins else 0.0
    gross_loss_abs = abs(float(np.sum(losses))) if losses else 0.0
    if gross_loss_abs > 0:
        profit_factor = gross_profit / gross_loss_abs
    elif gross_profit > 0:
        profit_factor = float("inf")
    else:
        profit_factor = 0.0

    alpha_pct = total_return_pct - spy_total_return_pct

    return {
        "final_portfolio_value": final_value,
        "total_return_pct": total_return_pct,
        "cagr_pct": cagr_pct,
        "max_drawdown_pct": max_drawdown_pct,
        "sharpe_ratio": sharpe_ratio,
        "win_rate_pct": win_rate_pct,
        "average_win": avg_win,
        "average_loss": avg_loss,
        "profit_factor": profit_factor,
        "spy_total_return_pct": spy_total_return_pct,
        "alpha_pct": alpha_pct,
        "closed_trades": closed_trades,
    }


def summary_report(stage_name, metrics):
    print("-" * 72, flush=True)
    print(f"[{stage_name}] SUMMARY REPORT", flush=True)
    print(f"Final Portfolio Value: {metrics['final_portfolio_value']:.2f}", flush=True)
    print(f"Total Return %: {metrics['total_return_pct']:.2f}%", flush=True)
    print(f"CAGR: {metrics['cagr_pct']:.2f}%", flush=True)
    print(f"Max Drawdown: {metrics['max_drawdown_pct']:.2f}%", flush=True)
    print(f"Sharpe Ratio (rf=0): {metrics['sharpe_ratio']:.4f}", flush=True)
    print(f"Win Rate: {metrics['win_rate_pct']:.2f}% ({metrics['closed_trades']} closed trades)", flush=True)
    print(f"Average Win: {metrics['average_win']:.2f}", flush=True)
    print(f"Average Loss: {metrics['average_loss']:.2f}", flush=True)
    if np.isinf(metrics["profit_factor"]):
        print("Profit Factor: inf", flush=True)
    else:
        print(f"Profit Factor: {metrics['profit_factor']:.4f}", flush=True)
    print(f"SPY Total Return %: {metrics['spy_total_return_pct']:.2f}%", flush=True)
    print(f"Strategy Alpha %: {metrics['alpha_pct']:.2f}%", flush=True)
    print("-" * 72, flush=True)


def _compute_signals(stock, history_df, prev_df):
    if history_df.empty or len(history_df) < 2:
        return None

    dr_df = ind.compute_daily_returns(history_df, stock)
    if dr_df.empty:
        return None

    try:
        prev_dr_df = ind.compute_daily_returns(prev_df, stock)
    except Exception:
        prev_dr_df = dr_df

    temp_ma, temp_cp = ind.compute_moving_average(history_df, int(config.day_range), stock)

    mab_s = strategy.ma_band_signal(temp_ma, temp_cp)

    try:
        rsi_c = strategy.RSI_Check(dr_df, prev_dr_df)
    except Exception:
        rsi_c = 0

    return {
        "mab_s": mab_s,
        "rsi_c": rsi_c,
        "current_price": float(temp_cp),
    }


def run_backtest_window(start_date, end_date, starting_capital, starting_positions, data_cache, stage_name):
    capital = float(starting_capital)
    stage_start_capital = float(starting_capital)
    positions = {k: dict(v) for k, v in starting_positions.items()}
    equity_curve = []
    trade_pnls = []
    last_known_prices = {}

    days_w = int(config.day_range)

    trading_days = pd.date_range(start=start_date, end=end_date, freq="B")
    print("=" * 72, flush=True)
    print(f"Running {stage_name} from {start_date} to {end_date} ({len(trading_days)} days)...", flush=True)
    print(f"{stage_name} starting capital: {capital:.2f}", flush=True)
    print(f"{stage_name} starting open positions: {len(positions)}", flush=True)

    for day_idx, current_day in enumerate(trading_days, start=1):
        today_str = current_day.strftime("%Y-%m-%d")
        prev_day = current_day - timedelta(days=1)

        if day_idx % DAY_PROGRESS_EVERY == 0 or day_idx == 1 or day_idx == len(trading_days):
            print(
                f"{stage_name} day {day_idx}/{len(trading_days)} ({today_str}) | cash={capital:.2f} | open_positions={len(positions)}",
                flush=True,
            )

        latest_prices = {}

        for stock in STOCKLIST:
            stock_df = data_cache.get(stock, pd.DataFrame())
            if stock_df.empty:
                continue

            up_to_today = _slice_until(stock_df, current_day)
            history_df = up_to_today.tail(int(days_w * 1.5) + 5)
            prev_df = _slice_until(stock_df, prev_day).tail(int(days_w * 1.5) + 5)

            signals = _compute_signals(stock, history_df, prev_df)
            if signals is None:
                continue

            current_price = signals["current_price"]
            latest_prices[stock] = current_price
            last_known_prices[stock] = current_price
            mab_s = signals["mab_s"]
            rsi_c = signals["rsi_c"]

            if mab_s != 0:
                if stock not in positions and capital >= MIN_ENTRY_CAPITAL and len(positions) < MAX_POSITIONS:
                    if mab_s == 1:
                        denom = current_price * config.stop_loss
                        if denom <= 0:
                            continue

                        shares = int((capital * config.RPT) / denom)
                        if shares <= 0:
                            continue

                        buy_price = shares * current_price
                        if buy_price > capital:
                            continue

                        positions[stock] = {
                            "entry_price": current_price,
                            "shares": shares,
                            "entry date": today_str,
                        }
                        capital -= buy_price
                        print(
                            f"[{stage_name}] BUY {stock} | shares={shares} | price={current_price:.2f} | cash={capital:.2f} | date={today_str}",
                            flush=True,
                        )

                elif stock in positions:
                    trade_info = positions[stock]
                    entry = float(trade_info["entry_price"])
                    shares = int(trade_info["shares"])

                    pnl_ratio = (current_price - entry) / entry if entry > 0 else 0
                    exit_signal = (
                        (mab_s == -1 and rsi_c == -1)
                        or (pnl_ratio <= -config.stop_loss)
                        or (pnl_ratio >= config.TPM)
                    )

                    if exit_signal:
                        pnl_value = (current_price - entry) * shares
                        trade_pnls.append(pnl_value)
                        capital += current_price * shares
                        print(
                            f"[{stage_name}] SELL {stock} | shares={shares} | price={current_price:.2f} | pnl={pnl_value:.2f} | cash={capital:.2f} | date={today_str}",
                            flush=True,
                        )
                        del positions[stock]

        positions_value, equity = _compute_daily_equity(capital, positions, latest_prices, last_known_prices)
        total_return_pct = ((equity / stage_start_capital) - 1.0) * 100.0 if stage_start_capital > 0 else 0.0
        equity_row = {
            "date": today_str,
            "cash": float(capital),
            "positions_value": float(positions_value),
            "equity": float(equity),
            "return_pct": float(total_return_pct),
        }
        equity_curve.append(equity_row)
        print(
            f"[{stage_name}] {today_str} | cash={capital:.2f} | positions_value={positions_value:.2f} | equity={equity:.2f} | return={total_return_pct:.2f}%",
            flush=True,
        )

        is_viable, total_value = _portfolio_is_viable(capital, positions, latest_prices)
        if not is_viable:
            print(
                f"{stage_name} failed viability on {today_str} | cash={capital:.2f} | total_value={total_value:.2f} | open_positions={len(positions)}",
                flush=True,
            )
            spy_total_return_pct = _compute_spy_total_return_pct(data_cache, start_date, today_str)
            metrics = compute_metrics(
                equity_curve=equity_curve,
                trade_pnls=trade_pnls,
                start_capital=stage_start_capital,
                start_date=start_date,
                end_date=today_str,
                spy_total_return_pct=spy_total_return_pct,
            )
            summary_report(stage_name, metrics)
            return {
                "success": False,
                "capital": capital,
                "positions": positions,
                "total_value": total_value,
                "failed_on": today_str,
                "equity_curve": equity_curve,
                "trade_pnls": trade_pnls,
                "metrics": metrics,
            }

    final_prices = {}
    for stock in positions:
        stock_df = data_cache.get(stock, pd.DataFrame())
        final_df = _slice_until(stock_df, pd.to_datetime(end_date))
        final_prices[stock] = _safe_latest_price(final_df)

    _, final_value = _portfolio_is_viable(capital, positions, final_prices)
    spy_total_return_pct = _compute_spy_total_return_pct(data_cache, start_date, end_date)
    metrics = compute_metrics(
        equity_curve=equity_curve,
        trade_pnls=trade_pnls,
        start_capital=stage_start_capital,
        start_date=start_date,
        end_date=end_date,
        spy_total_return_pct=spy_total_return_pct,
    )
    print(
        f"{stage_name} complete | ending_cash={capital:.2f} | ending_value={final_value:.2f} | open_positions={len(positions)}",
        flush=True,
    )
    summary_report(stage_name, metrics)
    return {
        "success": True,
        "capital": capital,
        "positions": positions,
        "total_value": final_value,
        "failed_on": None,
        "equity_curve": equity_curve,
        "trade_pnls": trade_pnls,
        "metrics": metrics,
    }


def run_backtest_pipeline():
    positions = {}
    capital = INITIAL_CAPITAL
    days_w = int(config.day_range)
    r_days_w = days_w + (config.rv_window - 1)

    print("Starting global prefetch for full pipeline window...", flush=True)
    data_cache = _prefetch_data("2012-01-01", "2025-12-31", days_w, r_days_w)

    training = run_backtest_window("2012-01-01", "2022-12-31", capital, positions, data_cache, "TRAINING")
    if not training["success"]:
        print("TRAINING_BACKTEST_FAILED")
        return training

    validation = run_backtest_window("2023-01-01", "2024-12-31", training["capital"], training["positions"], data_cache, "VALIDATION")
    if not validation["success"]:
        print("VALIDATION_FAILED")
        return validation

    out_of_sample = run_backtest_window("2025-01-01", "2025-12-31", validation["capital"], validation["positions"], data_cache, "OUT_OF_SAMPLE")
    if not out_of_sample["success"]:
        print("OUT_OF_SAMPLE_FAILED")
        return out_of_sample

    print(
        f"BACKTEST_PIPELINE_SUCCESS | final_cash={out_of_sample['capital']:.2f} | final_value={out_of_sample['total_value']:.2f} | open_positions={len(out_of_sample['positions'])}",
        flush=True,
    )
    return out_of_sample


if __name__ == "__main__":
    run_backtest_pipeline()
