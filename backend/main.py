import os
from fastapi import FastAPI
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from google import genai

load_dotenv()

app = FastAPI(
    title="AI Market Tracker API",
    description="Real-time Crypto and IPO Analysis API",
    version="1.0.0"
)

# Gemini Client Kurulumu
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
ai_client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

# 1. Sağlık kontrolü endpoint'i
@app.get("/")
def read_root():
    return {"status": "online", "message": "Market AI Tracker Backend Çalışıyor"}

# 2. Binance Canlı Kripto Fiyatı Endpoint'i
@app.get("/api/v1/crypto/{symbol}")
def get_crypto_price(symbol: str):
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

# 3. Halka Arz Listesi Scraper Endpoint'i
@app.get("/api/v1/ipo/list")
def get_ipo_list():
    url = "https://halkaarz.com/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            return {"error": "Halka arz verisi çekilemedi."}, 500
            
        soup = BeautifulSoup(response.text, "html.parser")
        ipo_items = []
        cards = soup.select("div.il-content, article.il-post")
        
        for card in cards[:10]:
            title_elem = card.select_one("h3, h2, .il-title")
            date_elem = card.select_one(".il-date, time, .il-date-info")
            
            if title_elem:
                title = title_elem.text.strip()
                date = date_elem.text.strip() if date_elem else "Tarih Belirtilmedi"
                ipo_items.append({
                    "company_name": title,
                    "status_or_date": date
                })
                
        return {
            "source": "halkaarz.com",
            "count": len(ipo_items),
            "data": ipo_items
        }
    except Exception as e:
        return {"error": str(e)}, 500

# 4. Yapay Zeka Market Analizi Endpoint'i
@app.get("/api/v1/ai/analyze/{symbol}")
def analyze_crypto_with_ai(symbol: str):
    """
    Binance'den alınan fiyatı Gemini AI modeline gönderip kısa bir tarafsız piyasa değerlendirmesi üretir.
    """
    if not ai_client:
        return {"error": "GEMINI_API_KEY bulunamadı veya yapılandırılmadı."}, 500
        
    crypto_data = get_crypto_price(symbol)
    if "error" in crypto_data:
        return crypto_data
        
    price = crypto_data.get("price")
    
    prompt = f"""
    Sen finansal veri analizi yapan tarafsız bir yapay zeka asistanısın.
    Kripto Para: {symbol.upper()}
    Güncel Fiyat: {price} USDT
    
    Bu veriye dayanarak kullanıcıya 2-3 cümlelik çok kısa, tarafsız bir piyasa durumu özeti çıkar.
    Kesinlikle yatırım tavsiyesi verme. Yanıtının sonuna mutlaka '(Yatırım tavsiyesi değildir)' notunu ekle.
    """
    
    try:
        response = ai_client.models.generate_content(
            model='gemini-3.8-flash',
            contents=prompt,
        )
        return {
            "symbol": symbol.upper(),
            "price": price,
            "ai_analysis": response.text,
            "disclaimer": "Bu analiz yapay zeka tarafından otomatik üretilmiştir, yatırım tavsiyesi içermez."
        }
    except Exception as e:
        return {"error": f"AI Analiz hatası: {str(e)}"}, 500