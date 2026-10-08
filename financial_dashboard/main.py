from fastapi import FastAPI

from financial_dashboard.routes import router

app = FastAPI(title="Financial Analytics Dashboard")
app.include_router(router)