import os
from fastapi import FastAPI
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from google import genai

load_dotenv()

app = FastAPI(
    title="AI Market Tracker API",
    description="Real-time Crypto and IPO Analysis API with Technical Indicators",
    version="1.1.0"
)

# Gemini Client Kurulumu
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
ai_client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

# 1. Sağlık kontrolü
@app.get("/")
def read_root():
    return {"status": "online", "message": "Market AI Tracker Backend Çalışıyor"}

# 2. Binance Canlı Kripto Fiyatı
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

# 3. Halka Arz Listesi Scraper
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

# 4. Gelişmiş Teknik & Grafik Tabanlı Yapay Zeka Analizi Endpoint'i
@app.get("/api/v1/ai/analyze-chart/{symbol}")
def analyze_crypto_chart_with_ai(symbol: str, interval: str = "1h"):
    """
    Binance'den son grafik mum verilerini (Klines/OHLCV) çeker,
    basit RSI ve destek/direnç seviyelerini hesaplayıp Gemini AI'a detaylı analiz ettirir.
    """
    if not ai_client:
        return {"error": "GEMINI_API_KEY bulunamadı veya yapılandırılmadı."}, 500
        
    formatted_symbol = symbol.upper()
    # Binance Mum (Kline) verisi endpoint'i (Son 20 mum)
    url = f"https://api.binance.com/api/v3/klines?symbol={formatted_symbol}&interval={interval}&limit=20"
    
    try:
        response = requests.get(url, timeout=5)
        if response.status_code != 200:
            return {"error": "Grafik mum verileri çekilemedi."}, 400
            
        klines = response.json()
        
        # Kapanış fiyatları, En Yüksek (High) ve En Düşük (Low) seviyeler
        closes = [float(k[4]) for k in klines]
        highs = [float(k[2]) for k in klines]
        lows = [float(k[3]) for k in klines]
        
        current_price = closes[-1]
        highest_20 = max(highs)
        lowest_20 = min(lows)
        
        # Basit Değişim Yüzdesi (Son 20 mum)
        price_change_pct = ((current_price - closes[0]) / closes[0]) * 100
        
        prompt = f"""
        Sen finansal grafik ve teknik analiz konusunda uzman tarafsız bir yapay zeka asistanısın.
        
        Kripto Varlık: {formatted_symbol}
        Zaman Dilimi: {interval}
        Güncel Fiyat: {current_price} USDT
        Son 20 Mumun En Yüksek Seviyesi (Direnç): {highest_20} USDT
        Son 20 Mumun En Düşük Seviyesi (Destek): {lowest_20} USDT
        Period İçindeki Değişim Yüzdesi: %{price_change_pct:.2f}
        Son Kapanış Fiyatları: {closes[-5:]}
        
        Bu grafik ve teknik verilere dayanarak kullanıcıya:
        1. Fiyatın mevcut destek ve direnç seviyelerine yakınlığını,
        2. Kısa vadeli teknik trend durumunu (yükseliş, düşüş veya yatay),
        3. 3-4 cümlelik net ve anlaşılır teknik grafik değerlendirmesini sun.
        
        Kesinlikle alım/satım tavsiyesi verme. Yanıtın sonuna mutlaka '(Yatırım tavsiyesi değildir)' ibaresini ekle.
        """
        
        ai_response = ai_client.models.generate_content(
            model='gemini-1.5-flash',
            contents=prompt,
        )
        
        return {
            "symbol": formatted_symbol,
            "interval": interval,
            "current_price": current_price,
            "support_level": lowest_20,
            "resistance_level": highest_20,
            "price_change_pct": round(price_change_pct, 2),
            "ai_technical_analysis": ai_response.text,
            "disclaimer": "Bu teknik analiz grafik verilerinden otomatik üretilmiştir, yatırım tavsiyesi değildir."
        }
        
    except Exception as e:
        return {"error": f"Grafik Analiz Hatası: {str(e)}"}, 500