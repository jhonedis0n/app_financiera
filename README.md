# Financial Analytics Dashboard

Dashboard web para consultar y comparar el rendimiento histórico de acciones. Presenta indicadores financieros, gráficos interactivos y exportación de datos a CSV y Excel.

Los precios históricos se obtienen desde Yahoo Finance mediante `yfinance`. Los datos dependen de ese servicio y pueden tener retrasos o estar sujetos a cambios.

## Requisitos

- Python 3.10 o posterior
- Acceso a Internet para descargar precios y recursos del dashboard

## Instalación

Clona el repositorio y entra en su carpeta:

```bash
git clone https://github.com/jhonedis0n/app_financiera
cd app_financiera
```

Crea un entorno virtual e instala las dependencias:

```powershell
# Windows PowerShell
py -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

```bash
# macOS / Linux
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

## Ejecución

Desde la carpeta raíz del proyecto, inicia el servidor de desarrollo:

```bash
uvicorn app:app --reload
```

Abre <http://127.0.0.1:8000> en el navegador. Para detener el servidor, pulsa `Ctrl+C` en la terminal.

## Funcionalidades

- Comparación de acciones y del índice S&P 500.
- Rendimiento, volatilidad, ratio de Sharpe y drawdown.
- Gráficos de precios, inversión, correlación y distribución de retornos.
- Descarga de precios en CSV o de un libro Excel.

## Estructura

```text
.
├── app.py              # Punto de entrada compatible con Uvicorn
├── financial_dashboard/
│   ├── __init__.py
│   ├── main.py          # Creación de la aplicación FastAPI
│   ├── routes.py        # Rutas HTTP y exportaciones
│   └── analytics.py     # Datos, métricas y gráficos
├── requirements.txt    # Dependencias de Python
├── templates/
│   └── index.html       # Interfaz del dashboard
└── README.md
```

## Publicar en GitHub

1. Crea un repositorio vacío en GitHub.
2. Desde esta carpeta, conecta el repositorio y publica la rama principal:

```bash
git remote add origin <URL_DEL_REPOSITORIO>
git branch -M main
git add .
git commit -m "Preparar proyecto para GitHub"
git push -u origin main
```

El archivo `.gitignore` excluye entornos virtuales, cachés y archivos locales. Si `__pycache__/app.cpython-314.pyc` ya está versionado, Git seguirá incluyéndolo hasta quitarlo del índice una vez con:

```bash
git rm --cached __pycache__/app.cpython-314.pyc
```

## Aviso

Este proyecto tiene fines informativos y educativos. No constituye asesoramiento financiero ni una recomendación de inversión.