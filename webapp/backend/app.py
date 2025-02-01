from fastapi import FastAPI
from src.execution.broker import execute_trade

app = FastAPI()

@app.post("/execute-trade")
async def trade(symbol: str, action: str):
     execute_trade(symbol, action)
     return {"status": "success"}