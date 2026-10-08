import io
from pathlib import Path

import pandas as pd
from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, Response
from fastapi.templating import Jinja2Templates

from financial_dashboard.analytics import DEFAULT_TICKERS, fetch_and_process_data

router = APIRouter()
templates = Jinja2Templates(
    directory=str(Path(__file__).resolve().parent.parent / "templates")
)


@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    context = fetch_and_process_data(DEFAULT_TICKERS, period="1y")
    return templates.TemplateResponse(
        request=request, name="index.html", context=context
    )


@router.post("/consultar", response_class=HTMLResponse)
async def consultar(
    request: Request,
    tickers_selected: list[str] = Form(default=DEFAULT_TICKERS),
    period: str = Form("1y"),
):
    if not tickers_selected:
        tickers_selected = DEFAULT_TICKERS

    context = fetch_and_process_data(tickers_selected, period=period)
    return templates.TemplateResponse(
        request=request, name="index.html", context=context
    )


@router.get("/export/csv")
def export_csv(tickers: str = "AAPL,NVDA,MSFT", period: str = "1y"):
    ticker_list = tickers.split(",")
    data = fetch_and_process_data(ticker_list, period=period)

    stream = io.StringIO()
    data["precios_raw"].to_csv(stream)

    return Response(
        content=stream.getvalue(),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=analisis_financiero_{period}.csv"
        },
    )


@router.get("/export/excel")
def export_excel(tickers: str = "AAPL,NVDA,MSFT", period: str = "1y"):
    ticker_list = tickers.split(",")
    data = fetch_and_process_data(ticker_list, period=period)

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        data["precios_raw"].to_excel(writer, sheet_name="Precios Cierre")
        data["retornos_raw"].to_excel(writer, sheet_name="Retornos Diarios")
        data["corr_raw"].to_excel(writer, sheet_name="Correlacion")

    return Response(
        content=output.getvalue(),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f"attachment; filename=analisis_financiero_{period}.xlsx"
        },
    )