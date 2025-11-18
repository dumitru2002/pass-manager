from fastapi import FastAPI
app = FastAPI(title="Audit Service")

logs = []

@app.post("/log")
def log(event: dict):
    logs.append(event)
    return {"status": "logged"}

@app.get("/logs")
def get_logs():
    return logs