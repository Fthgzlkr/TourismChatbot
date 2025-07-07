# services/weather_service.py
import requests
import json
import os
from typing import Dict, Any

class WeatherService:
    """OpenWeather API Servisi - Çok Dilli Destek"""
    
    def __init__(self):
        self.base_url = "http://api.openweathermap.org/data/2.5/forecast"
        
        # Çok dilli hava durumu açıklamaları
        self.weather_descriptions = {
            "clear sky": {
                "tr": "açık",
                "en": "clear sky",
                "de": "klarer Himmel",
                "fr": "ciel dégagé",
                "es": "cielo despejado",
                "it": "cielo sereno",
                "ja": "快晴",
                "ar": "سماء صافية",
                "ru": "ясное небо",
                "zh": "晴空"
            },
            "few clouds": {
                "tr": "az bulutlu",
                "en": "few clouds",
                "de": "wenige Wolken",
                "fr": "quelques nuages",
                "es": "pocas nubes",
                "it": "poche nuvole",
                "ja": "薄曇り",
                "ar": "غيوم قليلة",
                "ru": "небольшая облачность",
                "zh": "少云"
            },
            "scattered clouds": {
                "tr": "parçalı bulutlu",
                "en": "scattered clouds",
                "de": "lockere Bewölkung",
                "fr": "nuages épars",
                "es": "nubes dispersas",
                "it": "nubi sparse",
                "ja": "雲り",
                "ar": "غيوم متناثرة",
                "ru": "рассеянные облака",
                "zh": "多云"
            },
            "broken clouds": {
                "tr": "çok bulutlu",
                "en": "broken clouds",
                "de": "aufgelockerte Bewölkung",
                "fr": "nuages fragmentés",
                "es": "nubes rotas",
                "it": "nubi frammentate",
                "ja": "曇り",
                "ar": "غيوم متكسرة",
                "ru": "переменная облачность",
                "zh": "多云"
            },
            "overcast clouds": {
                "tr": "kapalı",
                "en": "overcast",
                "de": "bedeckt",
                "fr": "couvert",
                "es": "nublado",
                "it": "coperto",
                "ja": "曇天",
                "ar": "غائم",
                "ru": "пасмурно",
                "zh": "阴天"
            },
            "shower rain": {
                "tr": "sağanak yağmurlu",
                "en": "shower rain",
                "de": "Schauer",
                "fr": "averses",
                "es": "chubascos",
                "it": "rovesci",
                "ja": "にわか雨",
                "ar": "زخات مطر",
                "ru": "ливневый дождь",
                "zh": "阵雨"
            },
            "rain": {
                "tr": "yağmurlu",
                "en": "rainy",
                "de": "regnerisch",
                "fr": "pluvieux",
                "es": "lluvioso",
                "it": "piovoso",
                "ja": "雨",
                "ar": "ممطر",
                "ru": "дождливо",
                "zh": "雨"
            },
            "light rain": {
                "tr": "hafif yağmurlu",
                "en": "light rain",
                "de": "leichter Regen",
                "fr": "pluie légère",
                "es": "lluvia ligera",
                "it": "pioggia leggera",
                "ja": "小雨",
                "ar": "مطر خفيف",
                "ru": "легкий дождь",
                "zh": "小雨"
            },
            "moderate rain": {
                "tr": "orta şiddetli yağmurlu",
                "en": "moderate rain",
                "de": "mäßiger Regen",
                "fr": "pluie modérée",
                "es": "lluvia moderada",
                "it": "pioggia moderata",
                "ja": "中雨",
                "ar": "مطر معتدل",
                "ru": "умеренный дождь",
                "zh": "中雨"
            },
            "heavy rain": {
                "tr": "şiddetli yağmurlu",
                "en": "heavy rain",
                "de": "starker Regen",
                "fr": "pluie forte",
                "es": "lluvia intensa",
                "it": "pioggia intensa",
                "ja": "大雨",
                "ar": "مطر غزير",
                "ru": "сильный дождь",
                "zh": "大雨"
            },
            "thunderstorm": {
                "tr": "gök gürültülü fırtınalı",
                "en": "thunderstorm",
                "de": "Gewitter",
                "fr": "orage",
                "es": "tormenta",
                "it": "temporale",
                "ja": "雷雨",
                "ar": "عاصفة رعدية",
                "ru": "гроза",
                "zh": "雷暴"
            },
            "snow": {
                "tr": "kar yağışlı",
                "en": "snowy",
                "de": "schneereich",
                "fr": "neigeux",
                "es": "nevado",
                "it": "nevoso",
                "ja": "雪",
                "ar": "ثلجي",
                "ru": "снежно",
                "zh": "雪"
            },
            "light snow": {
                "tr": "hafif kar yağışlı",
                "en": "light snow",
                "de": "leichter Schnee",
                "fr": "neige légère",
                "es": "nieve ligera",
                "it": "neve leggera",
                "ja": "小雪",
                "ar": "ثلج خفيف",
                "ru": "легкий снег",
                "zh": "小雪"
            },
            "mist": {
                "tr": "sisli",
                "en": "misty",
                "de": "neblig",
                "fr": "brumeux",
                "es": "con niebla",
                "it": "nebbioso",
                "ja": "霧",
                "ar": "ضبابي",
                "ru": "туманно",
                "zh": "薄雾"
            },
            "fog": {
                "tr": "sisli",
                "en": "foggy",
                "de": "nebelig",
                "fr": "brouillard",
                "es": "con niebla",
                "it": "nebbia",
                "ja": "霧",
                "ar": "ضباب",
                "ru": "туман",
                "zh": "雾"
            },
            "haze": {
                "tr": "puslu",
                "en": "hazy",
                "de": "dunstig",
                "fr": "brume",
                "es": "bruma",
                "it": "foschia",
                "ja": "霞",
                "ar": "ضباب خفيف",
                "ru": "дымка",
                "zh": "霾"
            }
        }
        
        # Çok dilli zaman ifadeleri
        self.time_periods = {
            "tr": {
                "current": "güncel",
                "today": "bugün",
                "tomorrow": "yarın",
                "5_day": "5 günlük",
                "week": "haftalık"
            },
            "en": {
                "current": "current",
                "today": "today",
                "tomorrow": "tomorrow",
                "5_day": "5-day",
                "week": "weekly"
            },
            "de": {
                "current": "aktuell",
                "today": "heute",
                "tomorrow": "morgen",
                "5_day": "5-Tage",
                "week": "wöchentlich"
            },
            "fr": {
                "current": "actuel",
                "today": "aujourd'hui",
                "tomorrow": "demain",
                "5_day": "5 jours",
                "week": "hebdomadaire"
            },
            "es": {
                "current": "actual",
                "today": "hoy",
                "tomorrow": "mañana",
                "5_day": "5 días",
                "week": "semanal"
            },
            "it": {
                "current": "attuale",
                "today": "oggi",
                "tomorrow": "domani",
                "5_day": "5 giorni",
                "week": "settimanale"
            },
            "ja": {
                "current": "現在",
                "today": "今日",
                "tomorrow": "明日",
                "5_day": "5日間",
                "week": "週間"
            },
            "ar": {
                "current": "حالي",
                "today": "اليوم",
                "tomorrow": "غداً",
                "5_day": "5 أيام",
                "week": "أسبوعي"
            },
            "ru": {
                "current": "текущий",
                "today": "сегодня",
                "tomorrow": "завтра",
                "5_day": "5 дней",
                "week": "недельный"
            },
            "zh": {
                "current": "当前",
                "today": "今天",
                "tomorrow": "明天",
                "5_day": "5天",
                "week": "每周"
            }
        }
        
        # Çok dilli UI metinleri
        self.ui_texts = {
            "tr": {
                "weather_forecast": "hava durumu tahmini",
                "temperature": "Sıcaklık",
                "feels_like": "Hissedilen",
                "humidity": "Nem",
                "wind_speed": "Rüzgar hızı",
                "error_api_key": "OpenWeather API anahtarı bulunamadı. Environment variable'ı kontrol edin.",
                "error_city_not_found": "Hava durumu bilgisi alınamadı. Lütfen şehir ismini doğru yazdığınızdan emin olun.",
                "error_network": "API isteği sırasında bir sorun oluştu. İnternet bağlantınızı kontrol edin.",
                "error_invalid_response": "Hava durumu API'sinden geçersiz bir yanıt alındı.",
                "error_unexpected": "Beklenmeyen bir hata oluştu"
            },
            "en": {
                "weather_forecast": "weather forecast",
                "temperature": "Temperature",
                "feels_like": "Feels like",
                "humidity": "Humidity",
                "wind_speed": "Wind speed",
                "error_api_key": "OpenWeather API key not found. Please check your environment variables.",
                "error_city_not_found": "Weather information could not be retrieved. Please make sure the city name is correct.",
                "error_network": "A problem occurred during API request. Please check your internet connection.",
                "error_invalid_response": "Invalid response received from weather API.",
                "error_unexpected": "An unexpected error occurred"
            },
            "de": {
                "weather_forecast": "Wettervorhersage",
                "temperature": "Temperatur",
                "feels_like": "Gefühlt wie",
                "humidity": "Luftfeuchtigkeit",
                "wind_speed": "Windgeschwindigkeit",
                "error_api_key": "OpenWeather API-Schlüssel nicht gefunden. Bitte überprüfen Sie Ihre Umgebungsvariablen.",
                "error_city_not_found": "Wetterinformationen konnten nicht abgerufen werden. Bitte stellen Sie sicher, dass der Stadtname korrekt ist.",
                "error_network": "Ein Problem ist bei der API-Anfrage aufgetreten. Bitte überprüfen Sie Ihre Internetverbindung.",
                "error_invalid_response": "Ungültige Antwort von der Wetter-API erhalten.",
                "error_unexpected": "Ein unerwarteter Fehler ist aufgetreten"
            },
            "fr": {
                "weather_forecast": "prévisions météo",
                "temperature": "Température",
                "feels_like": "Ressenti",
                "humidity": "Humidité",
                "wind_speed": "Vitesse du vent",
                "error_api_key": "Clé API OpenWeather introuvable. Veuillez vérifier vos variables d'environnement.",
                "error_city_not_found": "Les informations météo n'ont pas pu être récupérées. Veuillez vous assurer que le nom de la ville est correct.",
                "error_network": "Un problème est survenu lors de la requête API. Veuillez vérifier votre connexion Internet.",
                "error_invalid_response": "Réponse invalide reçue de l'API météo.",
                "error_unexpected": "Une erreur inattendue s'est produite"
            },
            "es": {
                "weather_forecast": "pronóstico del tiempo",
                "temperature": "Temperatura",
                "feels_like": "Sensación térmica",
                "humidity": "Humedad",
                "wind_speed": "Velocidad del viento",
                "error_api_key": "Clave API de OpenWeather no encontrada. Por favor verifique sus variables de entorno.",
                "error_city_not_found": "No se pudo obtener información del tiempo. Por favor asegúrese de que el nombre de la ciudad sea correcto.",
                "error_network": "Ocurrió un problema durante la petición API. Por favor verifique su conexión a Internet.",
                "error_invalid_response": "Respuesta inválida recibida de la API del tiempo.",
                "error_unexpected": "Ocurrió un error inesperado"
            },
            "it": {
                "weather_forecast": "previsioni meteo",
                "temperature": "Temperatura",
                "feels_like": "Percepita",
                "humidity": "Umidità",
                "wind_speed": "Velocità del vento",
                "error_api_key": "Chiave API OpenWeather non trovata. Controllare le variabili d'ambiente.",
                "error_city_not_found": "Impossibile recuperare informazioni meteo. Assicurarsi che il nome della città sia corretto.",
                "error_network": "Si è verificato un problema durante la richiesta API. Controllare la connessione Internet.",
                "error_invalid_response": "Risposta non valida ricevuta dall'API meteo.",
                "error_unexpected": "Si è verificato un errore imprevisto"
            },
            "ja": {
                "weather_forecast": "天気予報",
                "temperature": "気温",
                "feels_like": "体感温度",
                "humidity": "湿度",
                "wind_speed": "風速",
                "error_api_key": "OpenWeather APIキーが見つかりません。環境変数を確認してください。",
                "error_city_not_found": "天気情報を取得できませんでした。都市名が正しいことを確認してください。",
                "error_network": "API要求中に問題が発生しました。インターネット接続を確認してください。",
                "error_invalid_response": "天気APIから無効な応答を受信しました。",
                "error_unexpected": "予期しないエラーが発生しました"
            },
            "ar": {
                "weather_forecast": "توقعات الطقس",
                "temperature": "درجة الحرارة",
                "feels_like": "الشعور بـ",
                "humidity": "الرطوبة",
                "wind_speed": "سرعة الرياح",
                "error_api_key": "لم يتم العثور على مفتاح OpenWeather API. يرجى التحقق من متغيرات البيئة.",
                "error_city_not_found": "لا يمكن الحصول على معلومات الطقس. يرجى التأكد من صحة اسم المدينة.",
                "error_network": "حدثت مشكلة أثناء طلب API. يرجى التحقق من اتصال الإنترنت.",
                "error_invalid_response": "تم تلقي رد غير صالح من API الطقس.",
                "error_unexpected": "حدث خطأ غير متوقع"
            },
            "ru": {
                "weather_forecast": "прогноз погоды",
                "temperature": "Температура",
                "feels_like": "Ощущается как",
                "humidity": "Влажность",
                "wind_speed": "Скорость ветра",
                "error_api_key": "Ключ API OpenWeather не найден. Проверьте переменные окружения.",
                "error_city_not_found": "Не удалось получить информацию о погоде. Убедитесь, что название города указано правильно.",
                "error_network": "Возникла проблема при выполнении API запроса. Проверьте интернет-соединение.",
                "error_invalid_response": "Получен недействительный ответ от API погоды.",
                "error_unexpected": "Произошла неожиданная ошибка"
            },
            "zh": {
                "weather_forecast": "天气预报",
                "temperature": "温度",
                "feels_like": "体感温度",
                "humidity": "湿度",
                "wind_speed": "风速",
                "error_api_key": "未找到OpenWeather API密钥。请检查环境变量。",
                "error_city_not_found": "无法获取天气信息。请确保城市名称正确。",
                "error_network": "API请求期间出现问题。请检查您的网络连接。",
                "error_invalid_response": "从天气API收到无效响应。",
                "error_unexpected": "发生了意外错误"
            }
        }
    
    def get_weather_data(self, city_name: str, time_period: str = "bugün", language: str = "tr") -> Dict[str, Any]:
        """
        Belirtilen şehir için OpenWeatherMap Forecast API'sinden hava durumu verilerini çeker.
        language: "tr", "en", "de", "fr", "es", "it", "ja", "ar", "ru", "zh"
        """
        # API anahtarını environment'tan al
        api_key = os.getenv("OPENWEATHER_API_KEY")
        if not api_key:
            return {
                "success": False,
                "error": self.ui_texts[language]["error_api_key"]
            }
        
        # OpenWeatherMap API dil kodları (bazıları farklı)
        api_lang_map = {
            "tr": "tr", "en": "en", "de": "de", "fr": "fr", 
            "es": "es", "it": "it", "ja": "ja", "ar": "ar", 
            "ru": "ru", "zh": "zh_cn"
        }
        api_lang = api_lang_map.get(language, "en")
        
        URL = f"{self.base_url}?q={city_name}&appid={api_key}&units=metric&lang={api_lang}&cnt=40"
        
        try:
            response = requests.get(URL)
            response.raise_for_status()
            data = response.json()
            
            if data.get("cod") == "200":
                forecasts = data["list"]
                city_info = data["city"]
                
                # Zaman periyoduna göre veri seçimi
                if time_period.lower() in ["bugün", "şu an", "şimdi", "güncel", "today", "current", "heute", "aktuell", "aujourd'hui", "actuel", "hoy", "actual", "oggi", "attuale", "今日", "현재", "اليوم", "حالي", "сегодня", "текущий", "今天", "当前"]:
                    forecast = forecasts[0]
                    return self._format_single_day_weather(forecast, city_info, "current", language)
                    
                elif time_period.lower() in ["yarın", "ertesi gün", "tomorrow", "morgen", "demain", "mañana", "domani", "明日", "내일", "غداً", "завтра", "明天"]:
                    target_index = min(8, len(forecasts) - 1)
                    forecast = forecasts[target_index]
                    return self._format_single_day_weather(forecast, city_info, "tomorrow", language)
                    
                elif time_period.lower() in ["gelecek", "5gün", "hafta", "haftasonu", "5days", "week", "5tage", "woche", "5jours", "semaine", "5días", "semana", "5giorni", "settimana", "5日間", "週間", "5أيام", "أسبوع", "5дней", "неделя", "5天", "周"]:
                    return self._format_5day_weather(forecasts, city_info, language)
                    
                else:
                    # Default olarak bugün
                    forecast = forecasts[0]
                    return self._format_single_day_weather(forecast, city_info, "current", language)
                
            else:
                return {
                    "success": False,
                    "error": f"{self.ui_texts[language]['error_city_not_found']}: {data.get('message', '')}"
                }
                
        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "error": f"{self.ui_texts[language]['error_network']}: {e}"
            }
        except json.JSONDecodeError:
            return {
                "success": False,
                "error": self.ui_texts[language]["error_invalid_response"]
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"{self.ui_texts[language]['error_unexpected']}: {e}"
            }

    def _format_single_day_weather(self, forecast: Dict, city_info: Dict, period_key: str, language: str) -> Dict[str, Any]:
        """Tek gün hava durumu formatla"""
        main_data = forecast["main"]
        weather_data_info = forecast["weather"][0]
        wind_data = forecast["wind"]
        
        # Hava durumu açıklaması - önce API'den gelen description'ı kullan, bulamazsak çevir
        api_description = weather_data_info["description"].lower()
        description = self.weather_descriptions.get(api_description, {}).get(language, api_description)
        
        period_text = self.time_periods[language][period_key]
        
        return {
            "success": True,
            "type": "single_day",
            "language": language,
            "city": city_info["name"],
            "period": period_text,
            "description": description,
            "temperature": round(main_data["temp"], 1),
            "feels_like": round(main_data["feels_like"], 1),
            "humidity": main_data["humidity"],
            "wind_speed": round(wind_data["speed"], 1),
            "datetime": forecast["dt_txt"]
        }

    def _format_5day_weather(self, forecasts: list, city_info: Dict, language: str) -> Dict[str, Any]:
        """5 günlük hava durumu özeti"""
        daily_data = {}
        
        for forecast in forecasts:
            date = forecast["dt_txt"].split(" ")[0]
            
            if date not in daily_data:
                daily_data[date] = {
                    "temps": [],
                    "descriptions": [],
                    "humidity": [],
                    "wind": []
                }
            
            daily_data[date]["temps"].append(forecast["main"]["temp"])
            daily_data[date]["descriptions"].append(forecast["weather"][0]["description"])
            daily_data[date]["humidity"].append(forecast["main"]["humidity"])
            daily_data[date]["wind"].append(forecast["wind"]["speed"])
        
        # Her gün için ortalama hesapla
        summary = []
        for date, data in list(daily_data.items())[:5]:
            avg_temp = round(sum(data["temps"]) / len(data["temps"]), 1)
            most_common_desc = max(set(data["descriptions"]), key=data["descriptions"].count)
            avg_humidity = round(sum(data["humidity"]) / len(data["humidity"]))
            avg_wind = round(sum(data["wind"]) / len(data["wind"]), 1)
            
            # Açıklamayı çevir
            description = self.weather_descriptions.get(most_common_desc.lower(), {}).get(language, most_common_desc)
            
            summary.append({
                "date": date,
                "temperature": avg_temp,
                "description": description,
                "humidity": avg_humidity,
                "wind_speed": avg_wind
            })
        
        period_text = self.time_periods[language]["5_day"]
        
        return {
            "success": True,
            "type": "5_day",
            "language": language,
            "city": city_info["name"],
            "period": period_text,
            "summary": summary
        }

    def format_response(self, weather_result: Dict[str, Any]) -> str:
        """Hava durumu response'unu temiz format ile döner"""
        if not weather_result.get("success"):
            return f"⚠️ {weather_result.get('error', 'Unknown error')}"
        
        language = weather_result.get("language", "en")
        ui_text = self.ui_texts[language]
        
        if weather_result.get("type") == "5_day":
            # 5 günlük özet
            response = f"🌤️ **{weather_result['city']}** {weather_result['period']} {ui_text['weather_forecast']}:\n\n"
            for day in weather_result["summary"]:
                response += f"📅 **{day['date']}**\n"
                response += f"🌡️ {day['temperature']}°C\n"
                response += f"☁️ {day['description']}\n"
                response += f"💧 {ui_text['humidity']}: %{day['humidity']}\n"
                response += f"💨 {ui_text['wind_speed']}: {day['wind_speed']} m/s\n\n"
            return response
        
        else:
            # Tek gün
            return (
                f"🌤️ **{weather_result['city']}** {weather_result['period']}:\n"
                f"🌡️ {ui_text['temperature']}: {weather_result['temperature']}°C\n"
                f"🤚 {ui_text['feels_like']}: {weather_result['feels_like']}°C\n"
                f"☁️ {weather_result['description']}\n"
                f"💧 {ui_text['humidity']}: %{weather_result['humidity']}\n"
                f"💨 {ui_text['wind_speed']}: {weather_result['wind_speed']} m/s\n"
                f"⏰ {weather_result['datetime']}"
            )