import sys
import subprocess

# -------------------------------------------------------------------
# 1. AUTO-INSTALADOR DE LIBRERÍAS
# -------------------------------------------------------------------
REQUIRED_PACKAGES = {
    "fastapi": "fastapi",
    "uvicorn": "uvicorn",
    "jinja2": "jinja2",
    "yfinance": "yfinance",
    "pandas": "pandas",
    "plotly": "plotly",
    "multipart": "python-multipart"
}

def check_and_install_packages():
    for module_name, pip_name in REQUIRED_PACKAGES.items():
        try:
            __import__(module_name)
        except ImportError:
            print(f"[!] Instalando la librería faltante: {pip_name}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", pip_name])

check_and_install_packages()

from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import yfinance as yf
import pandas as pd
import plotly.express as px

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

def fetch_and_process_data(tickers: list[str], period: str = "1y"):
    datos = yf.download(tickers, period=period)
    
    if datos.empty:
        return None
    
    if len(tickers) == 1:
        precios = pd.DataFrame(datos['Close'])
        precios.columns = tickers
    else:
        precios = datos['Close']
        
    precios = precios.dropna(how='all')

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
        
        # Badge con color e icono
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

    # --- 2. RESUMEN ESTADÍSTICO FORMATEADO (USD) ---
    desc = precios_renombrados.describe().round(2)
    # Mapeo explicito de etiquetas en español
    index_map = {
        'count': 'Registros', 'mean': 'Promedio', 'std': 'Desv. Estándar',
        'min': 'Mínimo', '25%': 'Percentil 25%', '50%': 'Mediana (50%)',
        '75%': 'Percentil 75%', 'max': 'Máximo'
    }
    desc = desc.rename(index=index_map)
    
    # Formatear números con signo $
    desc_formatted = desc.copy()
    for col in desc_formatted.columns:
        desc_formatted[col] = desc_formatted[col].apply(lambda x: f"${x:,.2f}")
        
    stats_html = desc_formatted.to_html(classes="table custom-table align-middle")

    # --- 3. MÉTRICAS TARJETAS KPI ---
    top_performer = rendimiento_pct.idxmax()
    top_performer_val = rendimiento_pct.max()
    avg_performance = rendimiento_pct.mean()
    volatilidad = (precios_renombrados.pct_change().std() * 100).round(2)
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

    # --- 4. GRÁFICOS PULIDOS CON HOVER UNIFICADO Y ÁREA ---
    # Layout común
    common_layout = dict(
        template="plotly_dark",  # Aplica el tema oscuro de Plotly por defecto
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(family="Inter, sans-serif", color="#94A3B8"),
        hovermode="x unified",  # Cursor unificado sobre el eje X
        hoverlabel=dict(
            bgcolor="#1E293B",       # Fondo del cuadro tooltip (Slate 800)
            bordercolor="#334155",   # Borde tenue
            font_size=13,
            font_family="Inter, sans-serif",
            font_color="#F8FAFC"     # Texto blanco/claro (Slate 50)
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            title_text="",
            font=dict(color="#F8FAFC")
        ),
        xaxis=dict(gridcolor='#334155', showline=False, zeroline=False),
        yaxis=dict(gridcolor='#334155', showline=False, zeroline=False, tickprefix="$")
    )

    # Gráfico 1: Cotización Histórica
    fig_precios = px.area(
        precios_renombrados,
        labels={"Date": "Fecha", "value": "Precio (USD)", "variable": "Empresa"},
        color_discrete_sequence=px.colors.qualitative.Bold
    )
    fig_precios.update_traces(hovertemplate="%{y:$.2f}")
    fig_precios.update_layout(**common_layout, margin=dict(l=20, r=20, t=40, b=20))
    chart_precios = fig_precios.to_html(full_html=False, include_plotlyjs='cdn', config={'displayModeBar': False})

    # Gráfico 2: Inversión Base 1000 USD
    inversion = (precios_renombrados / precios_renombrados.iloc[0]) * 1000
    fig_inversion = px.area(
        inversion,
        labels={"Date": "Fecha", "value": "Valor (USD)", "variable": "Empresa"},
        color_discrete_sequence=px.colors.qualitative.Bold
    )
    fig_inversion.update_traces(hovertemplate="%{y:$.2f}")
    fig_inversion.update_layout(**common_layout, margin=dict(l=20, r=20, t=40, b=20))
    chart_inversion = fig_inversion.to_html(full_html=False, include_plotlyjs=False, config={'displayModeBar': False})

    return {
        "stats_html": stats_html,
        "rendimientos_html": rendimientos_html,
        "chart_precios": chart_precios,
        "chart_inversion": chart_inversion,
        "selected_tickers": tickers,
        "period": period,
        "companies": COMPANIES,
        "kpis": kpis
    }

# -------------------------------------------------------------------
# 3. RUTAS
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)