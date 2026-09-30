from fastapi import FastAPI

app = FastAPI(title="MediStock API")

@app.get("/")
async def root():
    return {"message": "Welcome to MediStock API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
