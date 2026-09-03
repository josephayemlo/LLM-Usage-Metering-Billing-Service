from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def root():
    return {"message": "Usage Metering and Billing API"}

@app.get("/health")
def health():
    return {"status": "healthy"}