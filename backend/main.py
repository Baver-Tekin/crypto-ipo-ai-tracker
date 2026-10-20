from fastapi import FastAPI
import requests

app = FastAPI(
    title="AI Market Tracker API",
    description="Real-time Crypto and IPO Analysis API",
    version="1.0.0"
)

# Sağlık kontrolü endpoint'i
@app.get("/")
def read_root():
    return {"status": "online", "message": "Market AI Tracker Backend Çalışıyor"}

# Binance Canlı Kripto Fiyatı Endpoint'i
@app.get("/api/v1/crypto/{symbol}")
def get_crypto_price(symbol: str):
    """
    Binance API üzerinden belirtilen sembolün (Örn: BTCUSDT) güncel fiyatını çeker.
    """
    formatted_symbol = symbol.upper()
    url = f"https://api.binance.com/api/v3/ticker/price?symbol={formatted_symbol}"
    
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            return {
                "symbol": data.get("symbol"),
                "price": float(data.get("price")),
                "currency": "USDT"
            }
        return {"error": "Sembol bulunamadı veya Binance API yanıt vermedi."}, 400
    except Exception as e:
        return {"error": str(e)}, 500