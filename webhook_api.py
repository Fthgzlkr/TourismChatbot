# webhook_api.py - Weather, Places, Currency + Directions için Çok Dilli Destek
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
# YENİ: Directions service eklendi
from services.directions_service import DirectionsService

# FastAPI uygulaması oluştur
app = FastAPI(title="RAG Chatbot Webhook API", version="4.0.0")

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

# YENİ: Directions request modeli
class DirectionsRequest(BaseModel):
    origin: str
    destination: str
    travel_mode: str = "driving"
    language: str = "tr"

class APIResponse(BaseModel):
    success: bool
    data: Optional[Dict[str, Any]] = None
    formatted_response: Optional[str] = None
    error: Optional[str] = None
    language: Optional[str] = None

# Servisleri başlat
weather_service = WeatherService()
places_service = PlacesService()
currency_service = CurrencyService()
# YENİ: Directions service başlat
directions_service = DirectionsService()

# Çok dilli hata mesajları - Directions eklendi
DIRECTIONS_ERROR_MESSAGES = {
    "tr": {
        "directions_error": "Yol tarifi webhook hatası",
        "locations_required": "Başlangıç ve varış noktası gerekli",
        "invalid_travel_mode": "Geçersiz seyahat modu"
    },
    "en": {
        "directions_error": "Directions webhook error", 
        "locations_required": "Origin and destination required",
        "invalid_travel_mode": "Invalid travel mode"
    },
    "de": {
        "directions_error": "Wegbeschreibung Webhook-Fehler",
        "locations_required": "Start und Ziel erforderlich",
        "invalid_travel_mode": "Ungültiger Reisemodus"
    },
    "fr": {
        "directions_error": "Erreur webhook itinéraire",
        "locations_required": "Origine et destination requises",
        "invalid_travel_mode": "Mode de voyage invalide"
    },
    "es": {
        "directions_error": "Error webhook direcciones",
        "locations_required": "Origen y destino requeridos", 
        "invalid_travel_mode": "Modo de viaje inválido"
    },
    "it": {
        "directions_error": "Errore webhook indicazioni",
        "locations_required": "Origine e destinazione richieste",
        "invalid_travel_mode": "Modalità di viaggio non valida"
    },
    "ja": {
        "directions_error": "道順Webhookエラー",
        "locations_required": "出発地と目的地が必要",
        "invalid_travel_mode": "無効な移動手段"
    },
    "ar": {
        "directions_error": "خطأ webhook الاتجاهات",
        "locations_required": "نقطة البداية والوجهة مطلوبة",
        "invalid_travel_mode": "وضع السفر غير صالح"
    },
    "ru": {
        "directions_error": "Ошибка webhook маршрутов",
        "locations_required": "Требуется начальная и конечная точки",
        "invalid_travel_mode": "Неверный режим передвижения"
    },
    "zh": {
        "directions_error": "路线webhook错误",
        "locations_required": "需要起点和终点",
        "invalid_travel_mode": "无效的出行方式"
    }
}

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

# Desteklenen diller (tüm servisler için)
WEATHER_SUPPORTED_LANGUAGES = ["tr", "en", "de", "fr", "es", "it", "ja", "ar", "ru", "zh"]

def get_places_error_message(language: str, key: str) -> str:
    """Places için dile göre hata mesajı al"""
    if language not in WEATHER_SUPPORTED_LANGUAGES:
        language = "en"
    return PLACES_ERROR_MESSAGES.get(language, PLACES_ERROR_MESSAGES["en"]).get(key, key)

def get_weather_error_message(language: str, key: str) -> str:
    """Weather için dile göre hata mesajı al"""
    if language not in WEATHER_SUPPORTED_LANGUAGES:
        language = "en"
    return WEATHER_ERROR_MESSAGES.get(language, WEATHER_ERROR_MESSAGES["en"]).get(key, key)

def get_directions_error_message(language: str, key: str) -> str:
    """Directions için dile göre hata mesajı al"""
    if language not in WEATHER_SUPPORTED_LANGUAGES:
        language = "en"
    return DIRECTIONS_ERROR_MESSAGES.get(language, DIRECTIONS_ERROR_MESSAGES["en"]).get(key, key)

def validate_weather_language(language: str) -> str:
    """Dil kodunu doğrula"""
    if language not in WEATHER_SUPPORTED_LANGUAGES:
        return "en"
    return language

# --- ENDPOINTS ---

@app.get("/")
async def root():
    return {
        "message": "RAG Chatbot Webhook API", 
        "status": "running",
        "version": "4.0.0",
        "services": ["weather (multi-lang)", "places (multi-lang)", "currency", "directions (multi-lang)"],
        "weather_languages": WEATHER_SUPPORTED_LANGUAGES,
        "places_languages": WEATHER_SUPPORTED_LANGUAGES,
        "directions_languages": WEATHER_SUPPORTED_LANGUAGES,  # YENİ
        "new_features": ["🗺️ Google Maps Directions API", "🧭 Gaziantep Navigation Support"]
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "services": {
            "weather": "✅" if os.getenv("OPENWEATHER_API_KEY") else "❌",
            "places": "✅" if os.getenv("GOOGLE_PLACES_API_KEY") else "❌",
            "currency": "✅",
            "directions": "✅" if os.getenv("GOOGLE_MAPS_API_KEY") else "❌"  # YENİ
        },
        "weather_supported_languages": WEATHER_SUPPORTED_LANGUAGES,
        "api_keys_status": {
            "google_maps": "✅" if os.getenv("GOOGLE_MAPS_API_KEY") else "❌ Required for directions"
        }
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

# YENİ: Directions endpoint
@app.post("/api/directions", response_model=APIResponse)
async def get_directions(request: DirectionsRequest):
    """Directions endpoint - çok dilli yol tarifi desteği"""
    try:
        language = validate_weather_language(request.language)
        
        if not request.origin or not request.destination:
            error_msg = get_directions_error_message(language, "locations_required")
            return APIResponse(success=False, error=error_msg, language=language)
        
        # Travel mode doğrulama
        valid_modes = ["driving", "walking", "transit", "cycling"]
        if request.travel_mode.lower() not in valid_modes:
            error_msg = get_directions_error_message(language, "invalid_travel_mode")
            return APIResponse(success=False, error=error_msg, language=language)
            
        # Directions service çağrısı
        result = directions_service.get_directions_data(
            request.origin, 
            request.destination, 
            request.travel_mode.lower(), 
            language
        )
        
        if result.get("success"):
            formatted_response = directions_service.format_response(result)
            return APIResponse(
                success=True, 
                data=result, 
                formatted_response=formatted_response, 
                language=language
            )
        else:
            return APIResponse(success=False, error=result.get("error"), language=language)
            
    except Exception as e:
        language = validate_weather_language(request.language)
        error_msg = f"{get_directions_error_message(language, 'directions_error')}: {str(e)}"
        return APIResponse(success=False, error=error_msg, language=language)

@app.get("/functions")
async def get_available_functions():
    """Mevcut tüm function'ları ve tanımlarını döndür - Directions eklendi"""
    
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
        },
        # YENİ: Directions function
        "get_directions": {
            "endpoint": "/api/directions",
            "method": "POST", 
            "params": ["origin", "destination", "travel_mode", "language"],
            "description": "Get driving, walking, transit, or cycling directions between locations",
            "supported_languages": WEATHER_SUPPORTED_LANGUAGES,
            "travel_modes": ["driving", "walking", "transit", "cycling"],
            "gaziantep_optimized": True
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
        },
        # YENİ: Directions declaration
        {
            "name": "get_directions",
            "description": "Get driving, walking, transit, or cycling directions between two locations. Perfect for navigation in Gaziantep and route planning.",
            "parameters": {
                "type": "object",
                "properties": {
                    "origin": {
                        "type": "string", 
                        "description": "Starting location (e.g., 'Gaziantep Castle', 'current location', 'hotel')"
                    },
                    "destination": {
                        "type": "string", 
                        "description": "Destination location (e.g., 'Zeugma Museum', 'İmam Çağdaş Restaurant')"
                    },
                    "travel_mode": {
                        "type": "string",
                        "description": "Mode of transportation", 
                        "enum": ["driving", "walking", "transit", "cycling"]
                    }
                },
                "required": ["origin", "destination"]
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
            "places": WEATHER_SUPPORTED_LANGUAGES,
            "directions": WEATHER_SUPPORTED_LANGUAGES  # YENİ
        },
        "new_in_v4": ["🗺️ Google Maps Directions API", "🧭 Multi-language navigation", "🏛️ Gaziantep optimization"]
    }

# Ana çalıştırma
if __name__ == "__main__":
    import uvicorn
    
    # API anahtarlarını kontrol et
    weather_key = "✅" if os.getenv("OPENWEATHER_API_KEY") else "❌"
    places_key = "✅" if os.getenv("GOOGLE_PLACES_API_KEY") else "❌"
    maps_key = "✅" if os.getenv("GOOGLE_MAPS_API_KEY") else "❌"  # YENİ
    
    print("🚀 Webhook API sunucusu başlatılıyor...")
    print("📍 URL: http://localhost:8000")
    print("📖 Docs: http://localhost:8000/docs")
    print(f"🔧 Servisler: Weather{weather_key}, Places{places_key}, Currency✅, Directions{maps_key}")
    print(f"🌍 Çok dilli destek: {', '.join(WEATHER_SUPPORTED_LANGUAGES)}")
    print(f"🗺️ YENİ: Google Maps Directions API - Gaziantep optimized!")
    
    if maps_key == "❌":
        print("⚠️  GOOGLE_MAPS_API_KEY environment variable missing for directions")
        print("   Add it to your .env file: GOOGLE_MAPS_API_KEY=your_api_key_here")
    
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False)