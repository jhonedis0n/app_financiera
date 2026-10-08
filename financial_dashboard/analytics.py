from datetime import datetime

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import pytz
import yfinance as yf

COMPANIES = {
    "AAPL": "Apple",
    "MSFT": "Microsoft",
    "NVDA": "NVIDIA",
    "AMZN": "Amazon",
    "GOOGL": "Google",
    "META": "Meta",
    "TSLA": "Tesla",
    "NFLX": "Netflix",
    "AMD": "AMD",
    "INTC": "Intel",
}

DEFAULT_TICKERS = ["AAPL", "NVDA", "MSFT"]


def get_market_status():
    """Verifica si la bolsa de NY (NYSE/NASDAQ) esta abierta en tiempo real."""
    timezone = pytz.timezone("America/New_York")
    now = datetime.now(timezone)

    if now.weekday() >= 5:
        return {"status": "Bolsa Cerrada", "is_open": False}

    market_open = now.replace(hour=9, minute=30, second=0, microsecond=0)
    market_close = now.replace(hour=16, minute=0, second=0, microsecond=0)
    is_open = market_open <= now <= market_close
    return {
        "status": "Bolsa Abierta" if is_open else "Bolsa Cerrada",
        "is_open": is_open,
    }


def calculate_financial_metrics(prices):
    """Calcula el ratio de Sharpe anualizado y el maximo drawdown."""
    returns = prices.pct_change().dropna()
    sharpe = (returns.mean() / returns.std()) * np.sqrt(252)

    cumulative_returns = (1 + returns).cumprod()
    peak = cumulative_returns.cummax()
    drawdown = (cumulative_returns - peak) / peak
    max_drawdown = drawdown.min() * 100

    return sharpe, max_drawdown, returns


def fetch_and_process_data(
    tickers: list[str], period: str = "1y", include_benchmark: bool = True
):
    benchmark_ticker = "^GSPC"
    download_tickers = list(
        set(tickers + ([benchmark_ticker] if include_benchmark else []))
    )
    data = yf.download(download_tickers, period=period)

    if data.empty:
        return None

    close_data = data["Close"]
    if isinstance(close_data, pd.Series):
        close_data = close_data.to_frame()

    prices = close_data[tickers].dropna()
    benchmark_data = (
        close_data[benchmark_ticker].dropna()
        if include_benchmark and benchmark_ticker in close_data
        else None
    )
    visible_names = {ticker: COMPANIES.get(ticker, ticker) for ticker in tickers}
    named_prices = prices.rename(columns=visible_names)

    initial_price = named_prices.iloc[0]
    final_price = named_prices.iloc[-1]
    performance_pct = ((final_price - initial_price) / initial_price * 100).round(2)

    performance_rows = []
    for company in named_prices.columns:
        start = initial_price[company]
        end = final_price[company]
        percentage = performance_pct[company]
        if percentage >= 0:
            badge = (
                '<span class="kpi-badge badge-success"><i class="bi '
                f'bi-arrow-up-short"></i> +{percentage:.2f}%</span>'
            )
        else:
            badge = (
                '<span class="kpi-badge badge-danger"><i class="bi '
                f'bi-arrow-down-short"></i> {percentage:.2f}%</span>'
            )

        performance_rows.append(
            {
                "Empresa": company,
                "Precio Inicial": f"${start:,.2f}",
                "Precio Actual": f"${end:,.2f}",
                "Rendimiento": badge,
            }
        )

    performance_html = pd.DataFrame(performance_rows).to_html(
        classes="table custom-table align-middle", escape=False, index=False
    )

    description = named_prices.describe().round(2)
    sharpe, max_drawdown, returns = calculate_financial_metrics(named_prices)
    index_names = {
        "count": "Registros",
        "mean": "Promedio",
        "std": "Desv. Estándar",
        "min": "Mínimo",
        "25%": "Percentil 25%",
        "50%": "Mediana (50%)",
        "75%": "Percentil 75%",
        "max": "Máximo",
    }
    description = description.rename(index=index_names)
    description.loc["Ratio de Sharpe"] = sharpe.round(2)
    description.loc["Max Drawdown"] = max_drawdown.round(2)

    formatted_description = pd.DataFrame(index=description.index)
    for column in description.columns:
        formatted_values = []
        for index in description.index:
            value = description.loc[index, column]
            if index == "Registros":
                formatted_values.append(f"{int(value)}")
            elif index == "Ratio de Sharpe":
                formatted_values.append(f"{value:.2f}")
            elif index == "Max Drawdown":
                formatted_values.append(f"{value:.2f}%")
            else:
                formatted_values.append(f"${value:,.2f}")
        formatted_description[column] = formatted_values

    stats_html = formatted_description.to_html(classes="table custom-table align-middle")

    top_performer = performance_pct.idxmax()
    top_performer_value = performance_pct.max()
    average_performance = performance_pct.mean()
    volatility = (returns.std() * 100).round(2)
    most_volatile = volatility.idxmax()
    most_volatile_value = volatility.max()
    kpis = {
        "top_performer": top_performer,
        "top_performer_val": (
            f"+{top_performer_value:.2f}%"
            if top_performer_value >= 0
            else f"{top_performer_value:.2f}%"
        ),
        "avg_performance": (
            f"+{average_performance:.2f}%"
            if average_performance >= 0
            else f"{average_performance:.2f}%"
        ),
        "avg_performance_is_pos": average_performance >= 0,
        "most_volatile": most_volatile,
        "most_volatile_val": f"{most_volatile_value:.2f}%",
    }

    common_layout = dict(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, sans-serif", color="#94A3B8"),
        hovermode="x unified",
        height=360,
        hoverlabel=dict(
            bgcolor="#1E293B",
            bordercolor="#334155",
            font_size=13,
            font_family="Inter, sans-serif",
            font_color="#F8FAFC",
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.08,
            xanchor="right",
            x=1,
            title_text="",
            font=dict(color="#F8FAFC"),
        ),
        xaxis=dict(
            gridcolor="#334155",
            showline=False,
            zeroline=False,
            rangeselector=dict(
                buttons=[
                    dict(count=1, label="1D", step="day", stepmode="backward"),
                    dict(count=7, label="1W", step="day", stepmode="backward"),
                    dict(count=1, label="1M", step="month", stepmode="backward"),
                    dict(count=6, label="6M", step="month", stepmode="backward"),
                    dict(count=1, label="YTD", step="year", stepmode="todate"),
                    dict(count=1, label="1Y", step="year", stepmode="backward"),
                    dict(count=5, label="5Y", step="year", stepmode="backward"),
                    dict(step="all", label="MAX"),
                ],
                bgcolor="#1E293B",
                activecolor="#3B82F6",
                font=dict(color="#F8FAFC", size=10),
            ),
        ),
        yaxis=dict(
            gridcolor="#334155", showline=False, zeroline=False, tickprefix="$"
        ),
    )

    price_figure = px.line(
        named_prices,
        labels={"Date": "Fecha", "value": "Precio (USD)", "variable": "Empresa"},
        color_discrete_sequence=px.colors.qualitative.Bold,
    )
    for trace in price_figure.data:
        trace.fillcolor = (
            trace.line.color.replace("rgb", "rgba").replace(")", ", 0.08)")
            if "rgb" in str(trace.line.color)
            else None
        )

    if benchmark_data is not None:
        price_figure.add_trace(
            go.Scatter(
                x=benchmark_data.index,
                y=benchmark_data,
                mode="lines",
                name="S&P 500 (^GSPC)",
                line=dict(dash="dash", color="#94A3B8", width=1.5),
                visible="legendonly",
            )
        )

    price_figure.update_traces(hovertemplate="%{y:$.2f}")
    price_figure.update_layout(**common_layout, margin=dict(l=20, r=20, t=50, b=20))
    price_chart = price_figure.to_html(
        full_html=False, include_plotlyjs="cdn", config={"displayModeBar": False}
    )

    investment = (named_prices / named_prices.iloc[0]) * 1000
    investment_figure = px.line(
        investment,
        labels={"Date": "Fecha", "value": "Valor (USD)", "variable": "Empresa"},
        color_discrete_sequence=px.colors.qualitative.Bold,
    )
    for trace in investment_figure.data:
        trace.fillcolor = (
            trace.line.color.replace("rgb", "rgba").replace(")", ", 0.08)")
            if "rgb" in str(trace.line.color)
            else None
        )

    if benchmark_data is not None:
        benchmark_investment = (benchmark_data / benchmark_data.iloc[0]) * 1000
        investment_figure.add_trace(
            go.Scatter(
                x=benchmark_investment.index,
                y=benchmark_investment,
                mode="lines",
                name="S&P 500 (^GSPC)",
                line=dict(dash="dash", color="#94A3B8", width=1.5),
                visible="legendonly",
            )
        )

    investment_figure.update_traces(hovertemplate="%{y:$.2f}")
    investment_figure.update_layout(
        **common_layout, margin=dict(l=20, r=20, t=50, b=20)
    )
    investment_chart = investment_figure.to_html(
        full_html=False, include_plotlyjs=False, config={"displayModeBar": False}
    )

    correlation = returns.corr().round(2)
    correlation_figure = px.imshow(
        correlation,
        text_auto=True,
        color_continuous_scale="RdBu_r",
        zmin=-1,
        zmax=1,
    )
    correlation_figure.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, sans-serif", color="#94A3B8"),
        height=280,
        margin=dict(l=10, r=10, t=10, b=10),
    )
    correlation_chart = correlation_figure.to_html(
        full_html=False, include_plotlyjs=False, config={"displayModeBar": False}
    )

    volatility_figure = go.Figure()
    for column in returns.columns:
        volatility_figure.add_trace(
            go.Box(y=returns[column] * 100, name=column, boxpoints="outliers")
        )
    volatility_figure.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, sans-serif", color="#94A3B8"),
        height=280,
        margin=dict(l=20, r=20, t=20, b=20),
        yaxis=dict(gridcolor="#334155", title="Retorno Diario (%)", ticksuffix="%"),
    )
    volatility_chart = volatility_figure.to_html(
        full_html=False, include_plotlyjs=False, config={"displayModeBar": False}
    )

    return {
        "stats_html": stats_html,
        "rendimientos_html": performance_html,
        "chart_precios": price_chart,
        "chart_inversion": investment_chart,
        "chart_corr": correlation_chart,
        "chart_box": volatility_chart,
        "selected_tickers": tickers,
        "period": period,
        "companies": COMPANIES,
        "kpis": kpis,
        "market_status": get_market_status(),
        "tickers_query": ",".join(tickers),
        "precios_raw": named_prices,
        "retornos_raw": returns,
        "corr_raw": correlation,
    }