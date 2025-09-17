from fastapi import FastAPI

app = FastAPI(title="ProPlus")


@app.get("/")
def root():
    return {"status": "ok", "app": "ProPlus"}
