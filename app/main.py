from fastapi import FastAPI

app = FastAPI(title="Youtube Sentiment Analyzer", version="0.1.0")

@app.get("/healthz")
async def healthz():
    return {"status": "ok"}
