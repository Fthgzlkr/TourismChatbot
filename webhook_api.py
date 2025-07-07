# webhook_api.py - Weather için Çok Dilli Destek
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
from typing import Optional, Dict, Any
import sys

# services klasörünü import path'e ekle
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Servisleri import et
from services.weather_service import WeatherService
from services.places_service import PlacesService
from services.currency_service import CurrencyService

# FastAPI uygulaması oluştur
app = FastAPI(title="RAG Chatbot Webhook API", version="3.2.0")

# Request modelleri
class WeatherRequest(BaseModel):
    city_name: str
    time_period: str = "bugün"
    language: str = "tr"  # ✅ Weather için çok dilli

class PlacesRequest(BaseModel):
    query: str
    location: Optional[str] = None
    language: str = "tr"  # ✅ Language parametresi eklendi

class CurrencyRequest(BaseModel):
    amount: float
    from_currency: str
    to_currency: str

class APIResponse(BaseModel):
    success: bool
    data: Optional[Dict[str, Any]] = None
    formatted_response: Optional[str] = None
    error: Optional[str] = None
    language: Optional[str] = None  # Sadece weather için

# Servisleri başlat
weather_service = WeatherService()
places_service = PlacesService()
currency_service = CurrencyService()

# Sadece Weather ve Places için çok dilli hata mesajları
PLACES_ERROR_MESSAGES = {
    "tr": {
        "places_error": "Yerler webhook hatası",
        "query_required": "Arama sorgusu gerekli"
    },
    "en": {
        "places_error": "Places webhook error",
        "query_required": "Search query required"
    },
    "de": {
        "places_error": "Orte-Webhook-Fehler",
        "query_required": "Suchanfrage erforderlich"
    },
    "fr": {
        "places_error": "Erreur webhook lieux",
        "query_required": "Requête de recherche requise"
    },
    "es": {
        "places_error": "Error webhook lugares",
        "query_required": "Consulta de búsqueda requerida"
    },
    "it": {
        "places_error": "Errore webhook luoghi",
        "query_required": "Query di ricerca richiesta"
    },
    "ja": {
        "places_error": "場所Webhookエラー",
        "query_required": "検索クエリが必要"
    },
    "ar": {
        "places_error": "خطأ webhook الأماكن",
        "query_required": "استعلام البحث مطلوب"
    },
    "ru": {
        "places_error": "Ошибка webhook мест",
        "query_required": "Требуется поисковый запрос"
    },
    "zh": {
        "places_error": "地点webhook错误",
        "query_required": "需要搜索查询"
    }
}

def get_places_error_message(language: str, key: str) -> str:
    """Places için dile göre hata mesajı al"""
    if language not in WEATHER_SUPPORTED_LANGUAGES:
        language = "en"
    return PLACES_ERROR_MESSAGES.get(language, PLACES_ERROR_MESSAGES["en"]).get(key, key)
WEATHER_ERROR_MESSAGES = {
    "tr": {
        "weather_error": "Hava durumu webhook hatası",
        "city_required": "Şehir adı gerekli",
        "invalid_language": "Geçersiz dil kodu"
    },
    "en": {
        "weather_error": "Weather webhook error",
        "city_required": "City name required",
        "invalid_language": "Invalid language code"
    },
    "de": {
        "weather_error": "Wetter-Webhook-Fehler",
        "city_required": "Stadtname erforderlich",
        "invalid_language": "Ungültiger Sprachcode"
    },
    "fr": {
        "weather_error": "Erreur webhook météo",
        "city_required": "Nom de ville requis",
        "invalid_language": "Code de langue invalide"
    },
    "es": {
        "weather_error": "Error webhook tiempo",
        "city_required": "Nombre de ciudad requerido",
        "invalid_language": "Código de idioma inválido"
    },
    "it": {
        "weather_error": "Errore webhook meteo",
        "city_required": "Nome città richiesto",
        "invalid_language": "Codice lingua non valido"
    },
    "ja": {
        "weather_error": "天気Webhookエラー",
        "city_required": "都市名が必要",
        "invalid_language": "無効な言語コード"
    },
    "ar": {
        "weather_error": "خطأ webhook الطقس",
        "city_required": "اسم المدينة مطلوب",
        "invalid_language": "رمز اللغة غير صالح"
    },
    "ru": {
        "weather_error": "Ошибка webhook погоды",
        "city_required": "Требуется название города",
        "invalid_language": "Неверный код языка"
    },
    "zh": {
        "weather_error": "天气webhook错误",
        "city_required": "需要城市名称",
        "invalid_language": "无效的语言代码"
    }
}

# Weather için desteklenen diller
WEATHER_SUPPORTED_LANGUAGES = ["tr", "en", "de", "fr", "es", "it", "ja", "ar", "ru", "zh"]

def get_weather_error_message(language: str, key: str) -> str:
    """Weather için dile göre hata mesajı al"""
    if language not in WEATHER_SUPPORTED_LANGUAGES:
        language = "en"
    return WEATHER_ERROR_MESSAGES.get(language, WEATHER_ERROR_MESSAGES["en"]).get(key, key)

def validate_weather_language(language: str) -> str:
    """Weather için dil kodunu doğrula"""
    if language not in WEATHER_SUPPORTED_LANGUAGES:
        return "en"
    return language

# --- ENDPOINTS ---

@app.get("/")
async def root():
    return {
        "message": "RAG Chatbot Webhook API", 
        "status": "running",
        "version": "3.2.0",
        "services": ["weather (multi-lang)", "places (multi-lang)", "currency"],
        "weather_languages": WEATHER_SUPPORTED_LANGUAGES,
        "places_languages": WEATHER_SUPPORTED_LANGUAGES  # Aynı diller
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "services": {
            "weather": "✅" if os.getenv("OPENWEATHER_API_KEY") else "❌",
            "places": "✅" if os.getenv("GOOGLE_PLACES_API_KEY") else "❌",
            "currency": "✅"
        },
        "weather_supported_languages": WEATHER_SUPPORTED_LANGUAGES
    }

@app.post("/api/weather", response_model=APIResponse)
async def get_weather(request: WeatherRequest):
    """Hava durumu endpoint - çok dilli destek"""
    try:
        # Dil kodunu doğrula
        language = validate_weather_language(request.language)
        
        if not request.city_name:
            error_msg = get_weather_error_message(language, "city_required")
            return APIResponse(
                success=False, 
                error=error_msg, 
                language=language
            )
            
        # Weather service'i language parametresi ile çağır
        result = weather_service.get_weather_data(
            request.city_name, 
            request.time_period, 
            language
        )
        
        if result.get("success"):
            formatted_response = weather_service.format_response(result)
            return APIResponse(
                success=True,
                data=result,
                formatted_response=formatted_response,
                language=language
            )
        else:
            return APIResponse(
                success=False, 
                error=result.get("error"), 
                language=language
            )
            
    except Exception as e:
        language = validate_weather_language(request.language)
        error_msg = f"{get_weather_error_message(language, 'weather_error')}: {str(e)}"
        return APIResponse(
            success=False, 
            error=error_msg, 
            language=language
        )

@app.post("/api/places", response_model=APIResponse)
async def get_places(request: PlacesRequest):
    """Places endpoint - çok dilli destek"""
    try:
        # Dil kodunu doğrula
        language = validate_weather_language(request.language)
        
        if not request.query:
            error_msg = get_places_error_message(language, "query_required")
            return APIResponse(
                success=False, 
                error=error_msg, 
                language=language
            )
            
        # Places service'i language parametresi ile çağır
        result = places_service.get_places_data(
            request.query, 
            request.location, 
            language
        )
        
        if result.get("success"):
            formatted_response = places_service.format_response(result)
            return APIResponse(
                success=True,
                data=result,
                formatted_response=formatted_response,
                language=language
            )
        else:
            return APIResponse(
                success=False, 
                error=result.get("error"), 
                language=language
            )
            
    except Exception as e:
        language = validate_weather_language(request.language)
        error_msg = f"{get_places_error_message(language, 'places_error')}: {str(e)}"
        return APIResponse(
            success=False, 
            error=error_msg, 
            language=language
        )

@app.post("/api/currency", response_model=APIResponse)
async def get_currency(request: CurrencyRequest):
    """Currency endpoint - tek dil (Türkçe)"""
    try:
        if not request.amount or not request.from_currency or not request.to_currency:
            return APIResponse(success=False, error="Para birimleri ve miktar gerekli")
            
        result = currency_service.get_currency_data(
            request.amount, 
            request.from_currency, 
            request.to_currency
        )
        
        if result.get("success"):
            formatted_response = currency_service.format_response(result)
            return APIResponse(
                success=True,
                data=result,
                formatted_response=formatted_response
            )
        else:
            return APIResponse(success=False, error=result.get("error"))
            
    except Exception as e:
        return APIResponse(success=False, error=f"Currency webhook hatası: {str(e)}")


# webhook_api.py dosyasına eklenecek kısım:

# Diğer endpoint'lerden sonra, main() fonksiyonundan önce ekle:

@app.get("/functions")
async def get_available_functions():
    """Mevcut tüm function'ları ve tanımlarını döndür"""
    
    # Mevcut function'lar
    functions = {
        "get_weather_data": {
            "endpoint": "/api/weather",
            "method": "POST",
            "params": ["city_name", "time_period", "language"],
            "description": "Get weather information for a city",
            "supported_languages": WEATHER_SUPPORTED_LANGUAGES
        },
        "get_currency_exchange": {
            "endpoint": "/api/currency", 
            "method": "POST",
            "params": ["amount", "from_currency", "to_currency"],
            "description": "Convert currency amounts",
            "supported_languages": ["tr", "en"]  # Currency için dil desteği sınırlı
        },
        "get_places_search": {
            "endpoint": "/api/places",
            "method": "POST",
            "params": ["query", "location", "additional_criteria"],
            "description": "Search for places and businesses",
            "supported_languages": WEATHER_SUPPORTED_LANGUAGES  # Places aynı dilleri destekliyor
        }
    }
    
    # Gemini için function declarations (opsiyonel)
    declarations = [
        {
            "name": "get_weather_data",
            "description": "Get weather information for a city",
            "parameters": {
                "type": "object",
                "properties": {
                    "city_name": {"type": "string", "description": "City name"},
                    "time_period": {
                        "type": "string",
                        "description": "Time period",
                        "enum": ["bugün", "yarın", "5gün", "hafta", "today", "tomorrow", "5days", "week"]
                    },
                    "language": {"type": "string", "description": "Language code"}
                },
                "required": ["city_name"]
            }
        },
        {
            "name": "get_currency_exchange",
            "description": "Convert currency amounts",
            "parameters": {
                "type": "object",
                "properties": {
                    "amount": {"type": "number", "description": "Amount to convert"},
                    "from_currency": {"type": "string", "description": "Source currency code"},
                    "to_currency": {"type": "string", "description": "Target currency code"}
                },
                "required": ["amount", "from_currency", "to_currency"]
            }
        },
        {
            "name": "get_places_search",
            "description": "Search for places and businesses",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"},
                    "location": {"type": "string", "description": "Location"},
                    "additional_criteria": {"type": "string", "description": "Additional criteria"}
                },
                "required": ["query", "location"]
            }
        }
    ]
    
    return {
        "status": "success",
        "total_functions": len(functions),
        "functions": functions,
        "declarations": declarations,
        "supported_languages": {
            "weather": WEATHER_SUPPORTED_LANGUAGES,
            "currency": ["tr", "en"],
            "places": WEATHER_SUPPORTED_LANGUAGES
        }
    }

# Ana çalıştırma
if __name__ == "__main__":
    import uvicorn
    
    # API anahtarlarını kontrol et
    weather_key = "✅" if os.getenv("OPENWEATHER_API_KEY") else "❌"
    places_key = "✅" if os.getenv("GOOGLE_PLACES_API_KEY") else "❌"
    
    print("🚀 Webhook API sunucusu başlatılıyor...")
    print("📍 URL: http://localhost:8000")
    print("📖 Docs: http://localhost:8000/docs")
    print(f"🔧 Servisler: Weather{weather_key}, Places{places_key}, Currency✅")
    print(f"🌍 Weather & Places çok dilli destek: {', '.join(WEATHER_SUPPORTED_LANGUAGES)}")
    
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False)