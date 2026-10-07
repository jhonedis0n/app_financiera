import io
from datetime import datetime
import pytz

import numpy as np
import pandas as pd
import yfinance as yf
import plotly.express as px
import plotly.graph_objects as go
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, Response
from fastapi.templating import Jinja2Templates

# -------------------------------------------------------------------
# 2. CONFIGURACIÓN
# -------------------------------------------------------------------
app = FastAPI(title="Financial Analytics Dashboard")
templates = Jinja2Templates(directory="templates")

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
    "INTC": "Intel"
}

DEFAULT_TICKERS = ["AAPL", "NVDA", "MSFT"]

def get_market_status():
    """Verifica si la bolsa de NY (NYSE/NASDAQ) está abierta en tiempo real."""
    tz = pytz.timezone('America/New_York')
    now = datetime.now(tz)
    
    # Fines de semana
    if now.weekday() >= 5:
        return {"status": "Bolsa Cerrada", "is_open": False}
    
    # Horario regular NYSE: 9:30 AM - 4:00 PM EST
    market_open = now.replace(hour=9, minute=30, second=0, microsecond=0)
    market_close = now.replace(hour=16, minute=0, second=0, microsecond=0)
    
    is_open = market_open <= now <= market_close
    return {
        "status": "Bolsa Abierta" if is_open else "Bolsa Cerrada",
        "is_open": is_open
    }

def calculate_financial_metrics(precios_df):
    """Calcula Sharpe Ratio y Max Drawdown (MDD)."""
    retornos = precios_df.pct_change().dropna()
    
    # Sharpe Ratio (Anualizado, Asumiendo Rf = 0)
    sharpe = (retornos.mean() / retornos.std()) * np.sqrt(252)
    
    # Max Drawdown (MDD)
    cum_returns = (1 + retornos).cumprod()
    peak = cum_returns.cummax()
    drawdown = (cum_returns - peak) / peak
    mdd = drawdown.min() * 100
    
    return sharpe, mdd, retornos

def fetch_and_process_data(tickers: list[str], period: str = "1y", include_benchmark: bool = True):
    benchmark_ticker = "^GSPC"
    download_tickers = list(set(tickers + ([benchmark_ticker] if include_benchmark else [])))
    
    datos = yf.download(download_tickers, period=period)
    
    if datos.empty:
        return None
    
    close_data = datos['Close']
    if isinstance(close_data, pd.Series):
        close_data = close_data.to_frame()
        
    precios = close_data[tickers].dropna()
    benchmark_data = close_data[benchmark_ticker].dropna() if include_benchmark and benchmark_ticker in close_data else None

    # Renombrar columnas a nombres visibles
    nombres_visibles = {ticker: COMPANIES.get(ticker, ticker) for ticker in tickers}
    precios_renombrados = precios.rename(columns=nombres_visibles)

    # --- 1. RENDIMIENTOS Y BADGES ---
    precio_inicial = precios_renombrados.iloc[0]
    precio_final = precios_renombrados.iloc[-1]
    rendimiento_pct = ((precio_final - precio_inicial) / precio_inicial * 100).round(2)
    
    rendimiento_list = []
    for emp in precios_renombrados.columns:
        p_init = precio_inicial[emp]
        p_end = precio_final[emp]
        pct = rendimiento_pct[emp]
        
        if pct >= 0:
            badge_html = f'<span class="kpi-badge badge-success"><i class="bi bi-arrow-up-short"></i> +{pct:.2f}%</span>'
        else:
            badge_html = f'<span class="kpi-badge badge-danger"><i class="bi bi-arrow-down-short"></i> {pct:.2f}%</span>'
            
        rendimiento_list.append({
            "Empresa": emp,
            "Precio Inicial": f"${p_init:,.2f}",
            "Precio Actual": f"${p_end:,.2f}",
            "Rendimiento": badge_html
        })
    
    df_rend = pd.DataFrame(rendimiento_list)
    rendimientos_html = df_rend.to_html(classes="table custom-table align-middle", escape=False, index=False)

    # --- 2. RESUMEN ESTADÍSTICO FORMATEADO + SHARPE Y MAX DRAWDOWN ---
    desc = precios_renombrados.describe().round(2)
    sharpe, mdd, retornos = calculate_financial_metrics(precios_renombrados)
    
    index_map = {
        'count': 'Registros', 'mean': 'Promedio', 'std': 'Desv. Estándar',
        'min': 'Mínimo', '25%': 'Percentil 25%', '50%': 'Mediana (50%)',
        '75%': 'Percentil 75%', 'max': 'Máximo'
    }
    desc = desc.rename(index=index_map)
    
    desc.loc['Ratio de Sharpe'] = sharpe.round(2)
    desc.loc['Max Drawdown'] = mdd.round(2)
    
    desc_formatted = pd.DataFrame(index=desc.index)
    for col in desc.columns:
        formatted_col = []
        for idx in desc.index:
            val = desc.loc[idx, col]
            if idx == 'Registros':
                formatted_col.append(f"{int(val)}")
            elif idx == 'Ratio de Sharpe':
                formatted_col.append(f"{val:.2f}")
            elif idx == 'Max Drawdown':
                formatted_col.append(f"{val:.2f}%")
            else:
                formatted_col.append(f"${val:,.2f}")
        desc_formatted[col] = formatted_col
        
    stats_html = desc_formatted.to_html(classes="table custom-table align-middle")

    # --- 3. MÉTRICAS TARJETAS KPI ---
    top_performer = rendimiento_pct.idxmax()
    top_performer_val = rendimiento_pct.max()
    avg_performance = rendimiento_pct.mean()
    volatilidad = (retornos.std() * 100).round(2)
    most_volatile = volatilidad.idxmax()
    most_volatile_val = volatilidad.max()

    kpis = {
        "top_performer": top_performer,
        "top_performer_val": f"+{top_performer_val:.2f}%" if top_performer_val >= 0 else f"{top_performer_val:.2f}%",
        "avg_performance": f"+{avg_performance:.2f}%" if avg_performance >= 0 else f"{avg_performance:.2f}%",
        "avg_performance_is_pos": avg_performance >= 0,
        "most_volatile": most_volatile,
        "most_volatile_val": f"{most_volatile_val:.2f}%"
    }

    # --- 4. GRÁFICOS NO APILADOS CON BENCHMARK Y TIMEFRAMES ---
    common_layout = dict(
        template="plotly_dark",
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(family="Inter, sans-serif", color="#94A3B8"),
        hovermode="x unified",
        height=360,
        hoverlabel=dict(
            bgcolor="#1E293B",
            bordercolor="#334155",
            font_size=13,
            font_family="Inter, sans-serif",
            font_color="#F8FAFC"
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.08,
            xanchor="right",
            x=1,
            title_text="",
            font=dict(color="#F8FAFC")
        ),
        xaxis=dict(
            gridcolor='#334155', 
            showline=False, 
            zeroline=False,
            rangeselector=dict(
                buttons=list([
                    dict(count=1, label="1D", step="day", stepmode="backward"),
                    dict(count=7, label="1W", step="day", stepmode="backward"),
                    dict(count=1, label="1M", step="month", stepmode="backward"),
                    dict(count=6, label="6M", step="month", stepmode="backward"),
                    dict(count=1, label="YTD", step="year", stepmode="todate"),
                    dict(count=1, label="1Y", step="year", stepmode="backward"),
                    dict(count=5, label="5Y", step="year", stepmode="backward"),
                    dict(step="all", label="MAX")
                ]),
                bgcolor="#1E293B",
                activecolor="#3B82F6",
                font=dict(color="#F8FAFC", size=10)
            )
        ),
        yaxis=dict(gridcolor='#334155', showline=False, zeroline=False, tickprefix="$")
    )

    # Gráfico 1: Cotización Histórica
    fig_precios = px.line(
        precios_renombrados,
        labels={"Date": "Fecha", "value": "Precio (USD)", "variable": "Empresa"},
        color_discrete_sequence=px.colors.qualitative.Bold
    )
    for trace in fig_precios.data:
        trace.fillcolor = trace.line.color.replace('rgb', 'rgba').replace(')', ', 0.08)') if 'rgb' in str(trace.line.color) else None

    if benchmark_data is not None:
        fig_precios.add_trace(go.Scatter(
            x=benchmark_data.index,
            y=benchmark_data,
            mode='lines',
            name='S&P 500 (^GSPC)',
            line=dict(dash='dash', color='#94A3B8', width=1.5),
            visible='legendonly'
        ))

    fig_precios.update_traces(hovertemplate="%{y:$.2f}")
    fig_precios.update_layout(**common_layout, margin=dict(l=20, r=20, t=50, b=20))
    chart_precios = fig_precios.to_html(full_html=False, include_plotlyjs='cdn', config={'displayModeBar': False})

    # Gráfico 2: Inversión Base 1000 USD
    inversion = (precios_renombrados / precios_renombrados.iloc[0]) * 1000
    fig_inversion = px.line(
        inversion,
        labels={"Date": "Fecha", "value": "Valor (USD)", "variable": "Empresa"},
        color_discrete_sequence=px.colors.qualitative.Bold
    )
    for trace in fig_inversion.data:
        trace.fillcolor = trace.line.color.replace('rgb', 'rgba').replace(')', ', 0.08)') if 'rgb' in str(trace.line.color) else None

    if benchmark_data is not None:
        bm_inversion = (benchmark_data / benchmark_data.iloc[0]) * 1000
        fig_inversion.add_trace(go.Scatter(
            x=bm_inversion.index,
            y=bm_inversion,
            mode='lines',
            name='S&P 500 (^GSPC)',
            line=dict(dash='dash', color='#94A3B8', width=1.5),
            visible='legendonly'
        ))

    fig_inversion.update_traces(hovertemplate="%{y:$.2f}")
    fig_inversion.update_layout(**common_layout, margin=dict(l=20, r=20, t=50, b=20))
    chart_inversion = fig_inversion.to_html(full_html=False, include_plotlyjs=False, config={'displayModeBar': False})

    # Gráfico 3: Matriz de Correlación
    corr_df = retornos.corr().round(2)
    fig_corr = px.imshow(
        corr_df,
        text_auto=True,
        color_continuous_scale="RdBu_r",
        zmin=-1, zmax=1
    )
    fig_corr.update_layout(
        template="plotly_dark",
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(family="Inter, sans-serif", color="#94A3B8"),
        height=280,
        margin=dict(l=10, r=10, t=10, b=10)
    )
    chart_corr = fig_corr.to_html(full_html=False, include_plotlyjs=False, config={'displayModeBar': False})

    # Gráfico 4: Box Plot de Volatilidad
    fig_box = go.Figure()
    for col in retornos.columns:
        fig_box.add_trace(go.Box(
            y=retornos[col] * 100,
            name=col,
            boxpoints='outliers'
        ))
    fig_box.update_layout(
        template="plotly_dark",
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(family="Inter, sans-serif", color="#94A3B8"),
        height=280,
        margin=dict(l=20, r=20, t=20, b=20),
        yaxis=dict(gridcolor='#334155', title="Retorno Diario (%)", ticksuffix="%")
    )
    chart_box = fig_box.to_html(full_html=False, include_plotlyjs=False, config={'displayModeBar': False})

    return {
        "stats_html": stats_html,
        "rendimientos_html": rendimientos_html,
        "chart_precios": chart_precios,
        "chart_inversion": chart_inversion,
        "chart_corr": chart_corr,
        "chart_box": chart_box,
        "selected_tickers": tickers,
        "period": period,
        "companies": COMPANIES,
        "kpis": kpis,
        "market_status": get_market_status(),
        "tickers_query": ",".join(tickers),
        "precios_raw": precios_renombrados,
        "retornos_raw": retornos,
        "corr_raw": corr_df
    }

# -------------------------------------------------------------------
# 3. RUTAS Y ENDPOINTS DE EXPORTACIÓN
# -------------------------------------------------------------------
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    context = fetch_and_process_data(DEFAULT_TICKERS, period="1y")
    return templates.TemplateResponse(request=request, name="index.html", context=context)

@app.post("/consultar", response_class=HTMLResponse)
async def consultar(
    request: Request, 
    tickers_selected: list[str] = Form(default=DEFAULT_TICKERS),
    period: str = Form("1y")
):
    if not tickers_selected:
        tickers_selected = DEFAULT_TICKERS
        
    context = fetch_and_process_data(tickers_selected, period=period)
    return templates.TemplateResponse(request=request, name="index.html", context=context)

@app.get("/export/csv")
def export_csv(tickers: str = "AAPL,NVDA,MSFT", period: str = "1y"):
    ticker_list = tickers.split(",")
    data = fetch_and_process_data(ticker_list, period=period)
    
    stream = io.StringIO()
    data["precios_raw"].to_csv(stream)
    
    return Response(
        content=stream.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=analisis_financiero_{period}.csv"}
    )

@app.get("/export/excel")
def export_excel(tickers: str = "AAPL,NVDA,MSFT", period: str = "1y"):
    ticker_list = tickers.split(",")
    data = fetch_and_process_data(ticker_list, period=period)
    
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        data["precios_raw"].to_excel(writer, sheet_name="Precios Cierre")
        data["retornos_raw"].to_excel(writer, sheet_name="Retornos Diarios")
        data["corr_raw"].to_excel(writer, sheet_name="Correlacion")
        
    return Response(
        content=output.getvalue(),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename=analisis_financiero_{period}.xlsx"}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)