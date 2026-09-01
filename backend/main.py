from fastapi import FastAPI
from sqlalchemy import text

from backend.api.cases import router as cases_router
from backend.api.customers import router as customers_router
from backend.database.connection import engine
from backend.api.auth import router as auth_router

app = FastAPI(
    title="Autonomous Customer Operations Platform",
    version="0.1.0",
)

app.include_router(auth_router)
app.include_router(customers_router)
app.include_router(cases_router)


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "customer-operations-api",
    }


@app.get("/database-health")
def database_health():
    with engine.connect() as connection:
        result = connection.execute(text("SELECT 1"))
        value = result.scalar()

    return {
        "database": "connected",
        "result": value,
    }