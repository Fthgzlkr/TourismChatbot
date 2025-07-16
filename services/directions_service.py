# services/directions_service.py - Gaziantep Sınırlı Yol Tarifi Servisi
import requests
import os
from typing import Dict, Any, List
from urllib.parse import quote

class DirectionsService:
    """Google Directions API Servisi - Sadece Gaziantep İçi Aramalar"""
    
    def __init__(self):
        self.base_url = "https://maps.googleapis.com/maps/api/directions/json"
        
        # Çok dilli UI metinleri
        self.ui_texts = {
            "tr": {
                "error_api_key": "GOOGLE_MAPS_API_KEY bulunamadı",
                "directions_api_error": "Directions API hatası",
                "unknown_error": "Bilinmeyen hata",
                "no_route_found": "için rota bulunamadı",
                "route_found": "rotası bulundu",
                "distance": "Mesafe",
                "duration": "Süre",
                "via": "üzerinden",
                "walking": "Yürüyerek",
                "driving": "Arabayla",
                "transit": "Toplu taşıma",
                "cycling": "Bisikletle",
                "steps": "Adımlar",
                "total_distance": "Toplam mesafe",
                "total_duration": "Toplam süre",
                "start_point": "Başlangıç",
                "end_point": "Varış",
                "map_links": "Harita Linkleri",
                "open_in_google_maps": "Google Maps'te Aç",
                "open_in_apple_maps": "Apple Maps'te Aç",
                "view_route": "Rotayı Görüntüle",
                "location_not_in_gaziantep": "Lokasyon Gaziantep sınırları dışında",
                "both_locations_must_be_in_gaziantep": "Her iki lokasyon da Gaziantep içinde olmalı"
            },
            "en": {
                "error_api_key": "GOOGLE_MAPS_API_KEY not found",
                "directions_api_error": "Directions API error",
                "unknown_error": "Unknown error",
                "no_route_found": "No route found for",
                "route_found": "route found",
                "distance": "Distance",
                "duration": "Duration",
                "via": "via",
                "walking": "Walking",
                "driving": "Driving",
                "transit": "Public transport",
                "cycling": "Cycling",
                "steps": "Steps",
                "total_distance": "Total distance",
                "total_duration": "Total duration",
                "start_point": "Start",
                "end_point": "End",
                "map_links": "Map Links",
                "open_in_google_maps": "Open in Google Maps",
                "open_in_apple_maps": "Open in Apple Maps",
                "view_route": "View Route",
                "location_not_in_gaziantep": "Location is outside Gaziantep boundaries",
                "both_locations_must_be_in_gaziantep": "Both locations must be within Gaziantep"
            }
        }
        
        # Dil koduyla Google Maps API language mapping
        self.google_lang_map = {
            "tr": "tr", "en": "en", "de": "de", "fr": "fr",
            "es": "es", "it": "it", "ja": "ja", "ar": "ar",
            "ru": "ru", "zh": "zh"
        }
        
        # Seyahat modları
        self.travel_modes = {
            "driving": "DRIVING",
            "walking": "WALKING", 
            "transit": "TRANSIT",
            "cycling": "BICYCLING"
        }
    
    def _resolve_gaziantep_location(self, location: str) -> str:
        """Lokasyonu Gaziantep formatına çevir"""
        if not location:
            return ""
            
        location_lower = location.lower().strip()
        
        # Gaziantep eklenmemişse ekle
        if "gaziantep" not in location_lower and "antep" not in location_lower:
            return f"{location}, Gaziantep, Turkey"
        
        return location
    
    def _is_location_in_gaziantep(self, location: str) -> bool:
        """Lokasyonun Gaziantep içinde olup olmadığını kontrol et"""
        location_lower = location.lower()
        
        # Gaziantep ile ilgili anahtar kelimeleri kontrol et
        gaziantep_keywords = [
            "gaziantep", "antep", "şahinbey", "şehitkamil", 
            "islahiye", "nizip", "nurdağı", "oğuzeli", "yavuzeli", "araban"
        ]
        
        return any(keyword in location_lower for keyword in gaziantep_keywords)
    
    def get_directions_data(self, origin: str, destination: str, travel_mode: str = "driving", language: str = "tr") -> Dict[str, Any]:
        """Gaziantep içi yol tarifi al"""
        api_key = os.getenv("GOOGLE_MAPS_API_KEY")
        if not api_key:
            return {
                "success": False, 
                "error": self.ui_texts[language]["error_api_key"]
            }
        
        # Orijinal query'leri sakla
        original_origin = origin
        original_destination = destination
        
        # Gaziantep lokasyonlarını çözümle
        resolved_origin = self._resolve_gaziantep_location(origin)
        resolved_destination = self._resolve_gaziantep_location(destination)
        
        # Gaziantep sınırları kontrolü
        if not self._is_location_in_gaziantep(resolved_origin):
            return {
                "success": False,
                "error": f"{self.ui_texts[language]['location_not_in_gaziantep']}: {origin}"
            }
        
        if not self._is_location_in_gaziantep(resolved_destination):
            return {
                "success": False,
                "error": f"{self.ui_texts[language]['location_not_in_gaziantep']}: {destination}"
            }
        
        # Google Maps API parametreleri
        google_lang = self.google_lang_map.get(language, "tr")
        mode = self.travel_modes.get(travel_mode.lower(), "DRIVING")
        
        params = {
            "origin": resolved_origin,
            "destination": resolved_destination,
            "mode": mode,
            "key": api_key,
            "language": google_lang,
            "units": "metric",
            "alternatives": True,
            "region": "TR"  # Türkiye bölgesi
        }
        
        try:
            response = requests.get(self.base_url, params=params, timeout=15)
            response.raise_for_status()
            data = response.json()
            
            if data.get("status") == "OK":
                return self._process_directions_data(
                    data, resolved_origin, resolved_destination, travel_mode, language, 
                    original_origin, original_destination
                )
            else:
                error_msg = f"{self.ui_texts[language]['directions_api_error']}: {data.get('status')} - {data.get('error_message', self.ui_texts[language]['unknown_error'])}"
                return {"success": False, "error": error_msg}
                
        except Exception as e:
            error_msg = f"{self.ui_texts[language]['directions_api_error']}: {str(e)}"
            return {"success": False, "error": error_msg}
    
    def _generate_map_links(self, origin: str, destination: str, travel_mode: str, language: str) -> Dict[str, str]:
        """Harita linklerini oluştur"""
        origin_encoded = quote(origin)
        destination_encoded = quote(destination)
        
        # Travel mode'u Google Maps format'ına çevir
        google_travel_mode = {
            "driving": "driving",
            "walking": "walking", 
            "transit": "transit",
            "cycling": "bicycling"
        }.get(travel_mode, "driving")
        
        # Apple Maps travel mode
        apple_travel_mode = {
            "driving": "d",
            "walking": "w",
            "transit": "r",
            "cycling": "b"
        }.get(travel_mode, "d")
        
        # Google Maps linkleri
        google_maps_url = f"https://www.google.com/maps/dir/{origin_encoded}/{destination_encoded}/"
        google_maps_travel = f"{google_maps_url}@/{google_travel_mode}"
        
        # Apple Maps linki
        apple_maps_url = f"https://maps.apple.com/?saddr={origin_encoded}&daddr={destination_encoded}&dirflg={apple_travel_mode}"
        
        # Google Maps Embed
        api_key = os.getenv("GOOGLE_MAPS_API_KEY", "")
        google_embed_url = f"https://www.google.com/maps/embed/v1/directions?key={api_key}&origin={origin_encoded}&destination={destination_encoded}&mode={google_travel_mode}&language={language}"
        
        return {
            "google_maps": google_maps_url,
            "google_maps_travel": google_maps_travel,
            "apple_maps": apple_maps_url,
            "google_embed": google_embed_url
        }
    
    def _process_directions_data(self, data: Dict, origin: str, destination: str, travel_mode: str, language: str, original_origin: str = None, original_destination: str = None) -> Dict[str, Any]:
        """Directions verilerini işle"""
        routes = data.get("routes", [])
        if not routes:
            return {
                "success": False,
                "error": f"{self.ui_texts[language]['no_route_found']} {origin} - {destination}"
            }
        
        # En iyi rotayı al
        best_route = routes[0]
        leg = best_route["legs"][0]
        
        # Harita linklerini oluştur
        map_links = self._generate_map_links(
            original_origin or origin, 
            original_destination or destination, 
            travel_mode, 
            language
        )
        
        # Temel bilgileri çıkar
        route_info = {
            "origin": leg["start_address"],
            "destination": leg["end_address"],
            "distance": leg["distance"]["text"],
            "duration": leg["duration"]["text"],
            "travel_mode": travel_mode,
            "steps": self._process_steps(leg["steps"], language),
            "total_distance_meters": leg["distance"]["value"],
            "total_duration_seconds": leg["duration"]["value"],
            "polyline": best_route["overview_polyline"]["points"],
            "bounds": best_route["bounds"],
            "map_links": map_links
        }
        
        # Alternatif rotalar
        alternative_routes = []
        for route in routes[1:3]:  # En fazla 2 alternatif
            if route["legs"]:
                alt_leg = route["legs"][0]
                alternative_routes.append({
                    "distance": alt_leg["distance"]["text"],
                    "duration": alt_leg["duration"]["text"],
                    "summary": route.get("summary", "Alternative route")
                })
        
        return {
            "success": True,
            "route": route_info,
            "alternatives": alternative_routes,
            "language": language,
            "search_metadata": {
                "origin_query": original_origin or origin,
                "destination_query": original_destination or destination,
                "mode": travel_mode,
                "total_routes_found": len(routes)
            }
        }
    
    def _process_steps(self, steps: List[Dict], language: str) -> List[Dict]:
        """Yol tarifi adımlarını işle"""
        processed_steps = []
        
        for i, step in enumerate(steps[:8]):  # En fazla 8 adım
            instruction = self._clean_html(step["html_instructions"])
            
            step_info = {
                "step_number": i + 1,
                "instruction": instruction,
                "distance": step["distance"]["text"],
                "duration": step["duration"]["text"],
                "maneuver": step.get("maneuver", ""),
                "travel_mode": step.get("travel_mode", "DRIVING")
            }
            processed_steps.append(step_info)
        
        return processed_steps
    
    def _clean_html(self, html_text: str) -> str:
        """HTML taglarını temizle"""
        import re
        clean = re.compile('<.*?>')
        return re.sub(clean, '', html_text)
    
    def format_response(self, data: Dict[str, Any]) -> str:
        """Response formatting"""
        language = data.get("language", "tr")
        ui_text = self.ui_texts.get(language, self.ui_texts["tr"])
        
        if not data.get("success"):
            return f"⚠️ {data.get('error', ui_text['unknown_error'])}"
        
        route = data.get("route", {})
        alternatives = data.get("alternatives", [])
        map_links = route.get("map_links", {})
        
        # Ana rota bilgisi
        travel_mode_text = ui_text.get(route.get("travel_mode", "driving"), route.get("travel_mode", ""))
        
        response = f"🗺️ **{route['origin']}** → **{route['destination']}**\n\n"
        response += f"🚗 **{travel_mode_text}**\n"
        response += f"📏 **{ui_text['distance']}:** {route['distance']}\n"
        response += f"⏱️ **{ui_text['duration']}:** {route['duration']}\n\n"
        
        # Harita linkleri
        if map_links:
            response += f"🗺️ **{ui_text.get('map_links', 'Harita Linkleri')}:**\n"
            
            if map_links.get("google_maps"):
                response += f"📍 [Google Maps'te Aç]({map_links['google_maps']})\n"
            
            if map_links.get("apple_maps"):
                response += f"🍎 [Apple Maps'te Aç]({map_links['apple_maps']})\n"
            
            response += "\n"
        
        # Yol tarifi adımları
        steps = route.get("steps", [])
        if steps:
            response += f"📋 **{ui_text['steps']}:**\n"
            for step in steps:
                response += f"{step['step_number']}. {step['instruction']}\n"
                response += f"   📏 {step['distance']} • ⏱️ {step['duration']}\n\n"
        
        # Alternatif rotalar
        if alternatives:
            response += f"🔄 **Alternatif Rotalar:**\n"
            for i, alt in enumerate(alternatives, 1):
                response += f"{i}. {alt['distance']} • {alt['duration']}\n"
                if alt.get('summary'):
                    response += f"   📝 {alt['summary']}\n"
        
        return response
    
    def get_gaziantep_route(self, from_place: str, to_place: str, mode: str = "walking", language: str = "tr") -> Dict[str, Any]:
        """Gaziantep özelleştirilmiş rota - kısa mesafeler için optimize"""
        
        # Gaziantep içi kısa mesafeler için yürüyüş modunu öner
        if mode == "driving":
            result = self.get_directions_data(from_place, to_place, mode, language)
            
            # Kısa mesafe ise yürüyüş öner
            if result.get("success") and result["route"]["total_distance_meters"] < 1000:
                ui_text = self.ui_texts.get(language, self.ui_texts["tr"])
                result["gaziantep_tip"] = f"💡 Bu mesafe çok kısa, {ui_text['walking']} tavsiye edilir."
            
            return result
        
        return self.get_directions_data(from_place, to_place, mode, language)