from fastapi import FastAPI

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