# Financial Analytics Dashboard

Dashboard web de análisis financiero para explorar y comparar el comportamiento histórico de varias acciones. Presenta indicadores, tablas y gráficos interactivos, y permite descargar los datos analizados.

Este repositorio contiene el código fuente; no incluye una versión alojada en línea. El dashboard se ejecuta como una aplicación web local con Python, FastAPI y datos de Yahoo Finance obtenidos mediante `yfinance`.

> Los datos dependen de Yahoo Finance y de la conexión a Internet. Pueden tener retrasos, estar incompletos o cambiar. La aplicación es informativa y no constituye asesoramiento financiero ni una recomendación de inversión.

## Funcionalidades

- Selección y comparación de hasta diez acciones disponibles, con AAPL, NVDA y MSFT como selección inicial.
- Consulta de periodos de 1 mes, 6 meses, 1 año y 5 años.
- Comparación opcional con el índice S&P 500.
- Indicadores de rendimiento, volatilidad, ratio de Sharpe y máximo drawdown.
- Gráficos de precios históricos, inversión hipotética inicial de USD 1.000, correlación y distribución de retornos diarios.
- Exportación de precios a CSV y de precios, retornos y correlación a Excel.
- Opción de impresión del navegador para guardar la vista como PDF.

## Cómo utilizar el dashboard

1. En la parte superior, selecciona una o varias empresas y el periodo que quieres analizar. Al cambiar la selección, el dashboard actualiza los resultados.
2. Revisa las tarjetas de resumen, las tablas de rendimiento y estadísticas y los gráficos.
3. Activa los interruptores de S&P 500 para mostrar el índice de referencia en los gráficos de precios e inversión.
4. Usa el menú **Exportar** para descargar los precios en CSV o el análisis en Excel. La opción de impresión permite guardar la vista como PDF desde el navegador.

## Cómo interpretar las métricas

- **Rendimiento:** cambio porcentual entre el primer y el último precio disponible del periodo seleccionado.
- **Rendimiento promedio:** promedio de los rendimientos de las acciones seleccionadas; no representa el rendimiento de una cartera ponderada.
- **Volatilidad:** desviación estándar de los retornos diarios; sirve como referencia de variación histórica, no predice el riesgo futuro.
- **Ratio de Sharpe:** rendimiento ajustado por volatilidad, anualizado y calculado suponiendo una tasa libre de riesgo igual a cero.
- **Máximo drawdown:** mayor caída porcentual desde un máximo anterior dentro del periodo consultado.
- **Correlación:** relación histórica entre los retornos diarios de los activos; oscila entre -1 y 1 y no implica causalidad.
- **Inversión de USD 1.000:** simulación ilustrativa de cuánto habría variado esa cantidad siguiendo los precios del periodo; no incluye comisiones, impuestos ni otros costes.

El indicador de apertura de la bolsa usa el horario habitual de Nueva York y los días de la semana. No consulta un calendario de festivos bursátiles y debe tomarse como una estimación.

## Tecnologías

- Python y FastAPI para el servidor y las rutas web.
- Jinja2 para generar la interfaz HTML.
- pandas y NumPy para procesar datos y calcular métricas.
- yfinance para consultar precios históricos.
- Plotly para los gráficos interactivos.
- Bootstrap y Tom Select para componentes de la interfaz, servidos desde CDN.

La aplicación requiere acceso a Internet tanto para obtener los datos de mercado como para cargar las bibliotecas de interfaz externas.

## Requisitos

- Python 3.10 o posterior.
- pip.
- Acceso a Internet.

## Instalación local

Clona el repositorio y entra en la carpeta del proyecto:

```bash
git clone https://github.com/jhonedis0n/app_financiera.git
cd app_financiera
```

Crea un entorno virtual e instala las dependencias.

**Windows PowerShell**

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

**macOS / Linux**

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

## Ejecución

Desde la raíz del proyecto, inicia el servidor de desarrollo:

```bash
uvicorn app:app --reload
```

Abre <http://127.0.0.1:8000>. También se puede iniciar con `python app.py`.

## Rutas disponibles

| Ruta | Descripción |
| --- | --- |
| `/` | Dashboard principal. |
| `/health` | Estado del servidor para comprobaciones de disponibilidad. |
| `/export/csv?tickers=AAPL,NVDA,MSFT&period=1y` | Descarga de precios en CSV. |
| `/export/excel?tickers=AAPL,NVDA,MSFT&period=1y` | Descarga de precios, retornos y correlación en Excel. |
| `/docs` | Documentación interactiva de la API generada por FastAPI. |

## Estructura

```text
.
├── app.py                         # Punto de entrada para Uvicorn
├── financial_dashboard/
│   ├── __init__.py
│   ├── main.py                    # Configuración de FastAPI
│   ├── routes.py                  # Rutas web y exportaciones
│   └── analytics.py               # Consulta, métricas y gráficos
├── templates/
│   └── index.html                 # Interfaz del dashboard
├── requirements.txt               # Dependencias de Python
└── .gitignore                     # Exclusiones de archivos locales
```

## Licencia

Este repositorio todavía no incluye un archivo de licencia. Hacerlo público permite consultar el código, pero no concede automáticamente permiso para reutilizarlo, modificarlo o distribuirlo. Añade una licencia cuando hayas decidido esos permisos.