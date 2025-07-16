# services/places_service.py - Multi-language Enhanced Version
import requests
import os
from typing import Dict, Any

class PlacesService:
    """Google Places API Servisi - Çok Dilli Destek"""
    
    def __init__(self):
        self.base_url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
        
        # Çok dilli UI metinleri
        self.ui_texts = {
            "tr": {
                "error_api_key": "GOOGLE_PLACES_API_KEY bulunamadı",
                "places_api_error": "Places API hatası",
                "unknown_error": "Bilinmeyen hata",
                "no_places_found": "için yer bulunamadı",
                "places_found": "için {} yer bulundu",
                "total_results": "toplam {} sonuçtan ilk {}",
                "rating": "Değerlendirme",
                "price": "Fiyat",
                "open": "Açık",
                "temporarily_closed": "Geçici kapalı", 
                "permanently_closed": "Kalıcı kapalı",
                "unknown_status": "Bilinmeyen durum"
            },
            "en": {
                "error_api_key": "GOOGLE_PLACES_API_KEY not found",
                "places_api_error": "Places API error",
                "unknown_error": "Unknown error",
                "no_places_found": "No places found for",
                "places_found": "Found {} places for",
                "total_results": "showing first {} of {} total results",
                "rating": "Rating",
                "price": "Price",
                "open": "Open",
                "temporarily_closed": "Temporarily closed",
                "permanently_closed": "Permanently closed",
                "unknown_status": "Unknown status"
            },
            "de": {
                "error_api_key": "GOOGLE_PLACES_API_KEY nicht gefunden",
                "places_api_error": "Places API Fehler",
                "unknown_error": "Unbekannter Fehler",
                "no_places_found": "Keine Orte gefunden für",
                "places_found": "{} Orte gefunden für",
                "total_results": "zeige erste {} von {} Gesamtergebnissen",
                "rating": "Bewertung",
                "price": "Preis",
                "open": "Geöffnet",
                "temporarily_closed": "Vorübergehend geschlossen",
                "permanently_closed": "Dauerhaft geschlossen",
                "unknown_status": "Unbekannter Status"
            },
            "fr": {
                "error_api_key": "GOOGLE_PLACES_API_KEY introuvable",
                "places_api_error": "Erreur API Places",
                "unknown_error": "Erreur inconnue",
                "no_places_found": "Aucun lieu trouvé pour",
                "places_found": "{} lieux trouvés pour",
                "total_results": "affichage des {} premiers sur {} résultats totaux",
                "rating": "Note",
                "price": "Prix",
                "open": "Ouvert",
                "temporarily_closed": "Temporairement fermé",
                "permanently_closed": "Fermé définitivement",
                "unknown_status": "Statut inconnu"
            },
            "es": {
                "error_api_key": "GOOGLE_PLACES_API_KEY no encontrada",
                "places_api_error": "Error API Places",
                "unknown_error": "Error desconocido",
                "no_places_found": "No se encontraron lugares para",
                "places_found": "Se encontraron {} lugares para",
                "total_results": "mostrando los primeros {} de {} resultados totales",
                "rating": "Calificación",
                "price": "Precio",
                "open": "Abierto",
                "temporarily_closed": "Temporalmente cerrado",
                "permanently_closed": "Cerrado permanentemente",
                "unknown_status": "Estado desconocido"
            },
            "it": {
                "error_api_key": "GOOGLE_PLACES_API_KEY non trovata",
                "places_api_error": "Errore API Places",
                "unknown_error": "Errore sconosciuto",
                "no_places_found": "Nessun luogo trovato per",
                "places_found": "Trovati {} luoghi per",
                "total_results": "mostrando i primi {} di {} risultati totali",
                "rating": "Valutazione",
                "price": "Prezzo",
                "open": "Aperto",
                "temporarily_closed": "Temporaneamente chiuso",
                "permanently_closed": "Chiuso permanentemente",
                "unknown_status": "Stato sconosciuto"
            },
            "ja": {
                "error_api_key": "GOOGLE_PLACES_API_KEYが見つかりません",
                "places_api_error": "Places APIエラー",
                "unknown_error": "不明なエラー",
                "no_places_found": "場所が見つかりません",
                "places_found": "{}件の場所が見つかりました",
                "total_results": "合計{}件中最初の{}件を表示",
                "rating": "評価",
                "price": "価格",
                "open": "営業中",
                "temporarily_closed": "一時休業",
                "permanently_closed": "閉業",
                "unknown_status": "不明"
            },
            "ar": {
                "error_api_key": "GOOGLE_PLACES_API_KEY غير موجود",
                "places_api_error": "خطأ في Places API",
                "unknown_error": "خطأ غير معروف",
                "no_places_found": "لم يتم العثور على أماكن لـ",
                "places_found": "تم العثور على {} أماكن لـ",
                "total_results": "عرض أول {} من {} نتيجة إجمالية",
                "rating": "التقييم",
                "price": "السعر",
                "open": "مفتوح",
                "temporarily_closed": "مغلق مؤقتاً",
                "permanently_closed": "مغلق نهائياً",
                "unknown_status": "حالة غير معروفة"
            },
            "ru": {
                "error_api_key": "GOOGLE_PLACES_API_KEY не найден",
                "places_api_error": "Ошибка Places API",
                "unknown_error": "Неизвестная ошибка",
                "no_places_found": "Места не найдены для",
                "places_found": "Найдено {} мест для",
                "total_results": "показаны первые {} из {} общих результатов",
                "rating": "Рейтинг",
                "price": "Цена",
                "open": "Открыто",
                "temporarily_closed": "Временно закрыто",
                "permanently_closed": "Закрыто навсегда",
                "unknown_status": "Неизвестный статус"
            },
            "zh": {
                "error_api_key": "未找到GOOGLE_PLACES_API_KEY",
                "places_api_error": "Places API错误",
                "unknown_error": "未知错误",
                "no_places_found": "未找到地点",
                "places_found": "找到{}个地点",
                "total_results": "显示总共{}个结果中的前{}个",
                "rating": "评分",
                "price": "价格",
                "open": "营业中",
                "temporarily_closed": "暂时关闭",
                "permanently_closed": "永久关闭",
                "unknown_status": "未知状态"
            }
        }
        
        # Dil koduyla Google Places API language mapping
        self.google_lang_map = {
            "tr": "tr", "en": "en", "de": "de", "fr": "fr",
            "es": "es", "it": "it", "ja": "ja", "ar": "ar",
            "ru": "ru", "zh": "zh"
        }
        
        # Dil bazlı anahtar kelime detection
        self.language_indicators = {
            "tr": ['müze', 'restoran', 'otel', 'hastane', 'eczane', 'market', 'bank', 'cafe', 'park', 'plaj', 'nerede', 'hangi', 'en iyi', 'yakın'],
            "en": ['museum', 'restaurant', 'hotel', 'hospital', 'pharmacy', 'market', 'bank', 'cafe', 'park', 'beach', 'where', 'which', 'best', 'near'],
            "de": ['museum', 'restaurant', 'hotel', 'krankenhaus', 'apotheke', 'markt', 'bank', 'cafe', 'park', 'strand', 'wo', 'welche', 'beste', 'nahe'],
            "fr": ['musée', 'restaurant', 'hôtel', 'hôpital', 'pharmacie', 'marché', 'banque', 'café', 'parc', 'plage', 'où', 'quel', 'meilleur', 'près'],
            "es": ['museo', 'restaurante', 'hotel', 'hospital', 'farmacia', 'mercado', 'banco', 'café', 'parque', 'playa', 'dónde', 'cuál', 'mejor', 'cerca'],
            "it": ['museo', 'ristorante', 'hotel', 'ospedale', 'farmacia', 'mercato', 'banca', 'caffè', 'parco', 'spiaggia', 'dove', 'quale', 'migliore', 'vicino'],
            "ja": ['博物館', 'レストラン', 'ホテル', '病院', '薬局', '市場', '銀行', 'カフェ', '公園', 'ビーチ', 'どこ', 'どの', '最高', '近い'],
            "ar": ['متحف', 'مطعم', 'فندق', 'مستشفى', 'صيدلية', 'سوق', 'بنك', 'مقهى', 'حديقة', 'شاطئ', 'أين', 'أي', 'أفضل', 'قريب'],
            "ru": ['музей', 'ресторан', 'отель', 'больница', 'аптека', 'рынок', 'банк', 'кафе', 'парк', 'пляж', 'где', 'какой', 'лучший', 'рядом'],
            "zh": ['博物馆', '餐厅', '酒店', '医院', '药店', '市场', '银行', '咖啡厅', '公园', '海滩', '哪里', '哪个', '最好', '附近']
        }
    
    def get_places_data(self, query: str, location: str = None, language: str = "tr") -> Dict[str, Any]:
        """Akıllı yer arama - çok dilli destek"""
        api_key = os.getenv("GOOGLE_PLACES_API_KEY")
        if not api_key:
            return {
                "success": False, 
                "error": self.ui_texts[language]["error_api_key"]
            }
        
        # SMART QUERY BUILDING with language support
        final_query = self._build_smart_query(query, location, language)
        
        # Google Places API language
        google_lang = self.google_lang_map.get(language, "en")
        
        params = {
            "query": final_query,
            "key": api_key,
            "language": google_lang,
            "region": self._get_region_for_language(language)
        }
        
        try:
            response = requests.get(self.base_url, params=params, timeout=15)
            response.raise_for_status()
            data = response.json()
            
            if data.get("status") == "OK":
                return self._process_places_data(data, final_query, language)
            else:
                error_msg = f"{self.ui_texts[language]['places_api_error']}: {data.get('status')} - {data.get('error_message', self.ui_texts[language]['unknown_error'])}"
                return {"success": False, "error": error_msg}
                
        except Exception as e:
            error_msg = f"{self.ui_texts[language]['places_api_error']}: {str(e)}"
            return {"success": False, "error": error_msg}
    
    def _get_region_for_language(self, language: str) -> str:
        """Dile göre region bias ayarla"""
        region_map = {
            "tr": "tr", "en": "us", "de": "de", "fr": "fr",
            "es": "es", "it": "it", "ja": "jp", "ar": "sa",
            "ru": "ru", "zh": "cn"
        }
        return region_map.get(language, "us")
    
    def _build_smart_query(self, query: str, location: str = None, language: str = "tr") -> str:
        """Dil bazlı akıllı query oluşturma"""
        if not location:
            return query
        
        # Dil bazlı query formatı
        if language == "tr":
            if not any(suffix in location.lower() for suffix in ["'da", "'de", "'ta", "'te"]):
                return f"{location}'da {query}"
            else:
                return f"{query} {location}"
        elif language in ["en", "de", "fr", "es", "it"]:
            return f"{query} in {location}"
        elif language == "ja":
            return f"{location}の{query}"
        elif language == "ar":
            return f"{query} في {location}"
        elif language == "ru":
            return f"{query} в {location}"
        elif language == "zh":
            return f"{location}的{query}"
        else:
            return f"{query} in {location}"
    
    def _detect_query_language(self, query: str) -> str:
        """Query'den dil algıla"""
        query_lower = query.lower()
        for lang, indicators in self.language_indicators.items():
            if any(indicator in query_lower for indicator in indicators):
                return lang
        return "en"  # Default
    
    def _process_places_data(self, data: Dict, query: str, language: str) -> Dict[str, Any]:
        """Places verilerini işle - çok dilli"""
        places = []
        for place in data.get("results", [])[:5]:  # İlk 5 sonuç
            place_info = {
                "name": place.get("name"),
                "rating": place.get("rating"),
                "price_level": place.get("price_level"),
                "types": place.get("types", [])[:3],
                "status": place.get("business_status", "UNKNOWN"),
                "place_id": place.get("place_id"),
                "geometry": place.get("geometry", {}).get("location", {})
            }
            places.append(place_info)
        
        return {
            "success": True,
            "places": places,
            "total_results": len(data.get("results", [])),
            "query": query,
            "language": language,
            "search_metadata": {
                "enhanced_query": query,
                "results_count": len(places),
                "api_status": data.get("status"),
                "language_used": language
            }
        }
    
    def format_response(self, data: Dict[str, Any]) -> str:
        """Çok dilli response formatting"""
        language = data.get("language", "tr")
        ui_text = self.ui_texts.get(language, self.ui_texts["en"])
        
        if not data.get("success"):
            return f"⚠️ {data.get('error', ui_text['unknown_error'])}"
        
        places = data.get("places", [])
        if not places:
            return f"📍 **'{data.get('query', '')}'** {ui_text['no_places_found']}."
        
        total_results = data.get("total_results", len(places))
        response = f"📍 **'{data.get('query', '')}'** {ui_text['places_found'].format(len(places))}"
        
        if total_results > len(places):
            response += f" ({ui_text['total_results'].format(len(places), total_results)})"
        
        response += ":\n\n"
        
        for i, place in enumerate(places, 1):
            response += f"**{i}. {place['name']}**\n"
           
            if place.get('rating'):
                response += f"   ⭐ {ui_text['rating']}: {place['rating']}/5\n"
            if place.get('price_level') is not None:
                price_symbols = "💰" * (place['price_level'] + 1)
                response += f"   💸 {ui_text['price']}: {price_symbols}\n"
            if place.get('types'):
                response += f"   🏷️ {', '.join(place['types'])}\n"
            
            # İş durumu - çok dilli
            status = place.get('status')
            if status == 'OPERATIONAL':
                response += f"   ✅ {ui_text['open']}\n"
            elif status == 'CLOSED_TEMPORARILY':
                response += f"   ⏳ {ui_text['temporarily_closed']}\n"
            elif status == 'CLOSED_PERMANENTLY':
                response += f"   ❌ {ui_text['permanently_closed']}\n"
            else:
                response += f"   ❓ {ui_text['unknown_status']}\n"
            
            response += "\n"
        
        return response