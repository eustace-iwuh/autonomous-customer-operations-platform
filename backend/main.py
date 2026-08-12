from fastapi import FastAPI
from sqlalchemy import text

from backend.database.connection import engine


app = FastAPI(
    title="Autonomous Customer Operations Platform",
    version="0.1.0",
)


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