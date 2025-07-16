# api_manager.py - Universal API Manager with Directions Support - FIXED
import requests
import streamlit as st
from typing import Dict, Any, List, Optional
from google.genai import types
import json

class APIManager:
    """Tüm webhook API çağrılarını ve function handling'i yöneten tek sınıf - Directions desteği eklendi"""
    
    def __init__(self, webhook_url: str = "http://localhost:8000"):
        self.webhook_url = webhook_url
        self.available_functions = {}
        self.function_declarations = []
        self._load_functions()
    
    def _load_functions(self):
        """Webhook'tan mevcut function'ları otomatik yükle - FİX: Declarations format"""
        try:
            print(f"🔧 DEBUG: Trying to load functions from {self.webhook_url}/functions")
            response = requests.get(f"{self.webhook_url}/functions", timeout=5)
            if response.status_code == 200:
                functions_data = response.json()
                self.available_functions = functions_data.get("functions", {})
                
                # 🔧 FİX: Webhook'tan gelen declarations'ları doğru formata çevir
                webhook_declarations = functions_data.get("declarations", [])
                print(f"🔧 DEBUG: Webhook returned {len(webhook_declarations)} declarations")
                
                self.function_declarations = []
                for decl in webhook_declarations:
                    try:
                        # Webhook'tan gelen JSON format'ını types.FunctionDeclaration'a çevir
                        func_decl = self._convert_webhook_declaration_to_types(decl)
                        if func_decl:
                            self.function_declarations.append(func_decl)
                            print(f"✅ DEBUG: Converted declaration: {decl.get('name', 'unknown')}")
                        else:
                            print(f"❌ DEBUG: Failed to convert declaration: {decl.get('name', 'unknown')}")
                    except Exception as e:
                        print(f"❌ DEBUG: Error converting declaration {decl.get('name', 'unknown')}: {e}")
                
                print(f"✅ API Manager: {len(self.available_functions)} functions loaded, {len(self.function_declarations)} declarations converted")
                
                # Eğer hiç declaration convert edilmemişse fallback kullan
                if not self.function_declarations:
                    print("⚠️ No declarations converted, using fallback")
                    self._load_fallback_functions()
            else:
                print(f"❌ DEBUG: Webhook returned status {response.status_code}")
                self._load_fallback_functions()
        except Exception as e:
            print(f"⚠️ Could not load functions from webhook, using fallback: {str(e)}")
            self._load_fallback_functions()
    
    def _convert_webhook_declaration_to_types(self, webhook_decl: Dict[str, Any]) -> Optional[types.FunctionDeclaration]:
        """Webhook'tan gelen JSON declaration'ı types.FunctionDeclaration'a çevir"""
        try:
            name = webhook_decl.get("name")
            description = webhook_decl.get("description", "")
            parameters = webhook_decl.get("parameters", {})
            
            if not name:
                return None
            
            # Parameters'ı types.Schema'ya çevir
            schema = self._convert_parameters_to_schema(parameters)
            
            return types.FunctionDeclaration(
                name=name,
                description=description,
                parameters=schema
            )
        except Exception as e:
            print(f"❌ Declaration conversion error: {e}")
            return None
    
    def _convert_parameters_to_schema(self, params: Dict[str, Any]) -> types.Schema:
        """Parameters dict'ini types.Schema'ya çevir"""
        try:
            # Default schema
            if not params or params.get("type") != "object":
                return types.Schema(type=types.Type.OBJECT)
            
            properties = {}
            props = params.get("properties", {})
            
            for prop_name, prop_def in props.items():
                prop_type = prop_def.get("type", "string")
                prop_desc = prop_def.get("description", "")
                prop_enum = prop_def.get("enum")
                
                # Type mapping
                type_map = {
                    "string": types.Type.STRING,
                    "number": types.Type.NUMBER,
                    "integer": types.Type.INTEGER,
                    "boolean": types.Type.BOOLEAN,
                    "array": types.Type.ARRAY,
                    "object": types.Type.OBJECT
                }
                
                gemini_type = type_map.get(prop_type, types.Type.STRING)
                
                if prop_enum:
                    properties[prop_name] = types.Schema(
                        type=gemini_type,
                        description=prop_desc,
                        enum=prop_enum
                    )
                else:
                    properties[prop_name] = types.Schema(
                        type=gemini_type,
                        description=prop_desc
                    )
            
            required_fields = params.get("required", [])
            
            return types.Schema(
                type=types.Type.OBJECT,
                properties=properties,
                required=required_fields
            )
        except Exception as e:
            print(f"❌ Schema conversion error: {e}")
            return types.Schema(type=types.Type.OBJECT)
    
    def _load_fallback_functions(self):
        """Webhook'a erişilemezse fallback function'lar - Directions eklendi"""
        print("🔧 DEBUG: Loading fallback functions...")
        
        self.available_functions = {
            "get_weather_data": {
                "endpoint": "/api/weather",
                "method": "POST",
                "params": ["city_name", "time_period", "language"]
            },
            "get_currency_exchange": {
                "endpoint": "/api/currency", 
                "method": "POST",
                "params": ["amount", "from_currency", "to_currency"]
            },
            "get_places_search": {
                "endpoint": "/api/places",
                "method": "POST", 
                "params": ["query", "location", "additional_criteria"]
            },
            # YENİ: Directions API eklendi
            "get_directions": {
                "endpoint": "/api/directions",
                "method": "POST",
                "params": ["origin", "destination", "travel_mode", "language"]
            }
        }
        
        # Manuel function declarations (directions eklendi)
        self.function_declarations = [
            types.FunctionDeclaration(
                name="get_weather_data",
                description="Get weather information for a city",
                parameters=types.Schema(
                    type=types.Type.OBJECT,
                    properties={
                        "city_name": types.Schema(type=types.Type.STRING, description="City name"),
                        "time_period": types.Schema(
                            type=types.Type.STRING, 
                            description="Time period",
                            enum=["bugün", "yarın", "5gün", "hafta", "today", "tomorrow", "5days", "week"]
                        )
                    },
                    required=["city_name"]
                )
            ),
            types.FunctionDeclaration(
                name="get_currency_exchange",
                description="Convert currency amounts",
                parameters=types.Schema(
                    type=types.Type.OBJECT,
                    properties={
                        "amount": types.Schema(type=types.Type.NUMBER, description="Amount to convert"),
                        "from_currency": types.Schema(type=types.Type.STRING, description="Source currency code"),
                        "to_currency": types.Schema(type=types.Type.STRING, description="Target currency code")
                    },
                    required=["amount", "from_currency", "to_currency"]
                )
            ),
            types.FunctionDeclaration(
                name="get_places_search",
                description="Search for places and businesses in a specific location",
                parameters=types.Schema(
                    type=types.Type.OBJECT,
                    properties={
                        "query": types.Schema(
                            type=types.Type.STRING, 
                            description="Type of place to search for (hotel, restaurant, museum, etc.)"
                        ),
                        "location": types.Schema(
                            type=types.Type.STRING, 
                            description="City or location name"
                        ),
                        "additional_criteria": types.Schema(
                            type=types.Type.STRING,
                            description="Additional search criteria (optional)"
                        )
                    },
                    required=["query", "location"]
                )
            ),
            # YENİ: Directions function declaration
            types.FunctionDeclaration(
                name="get_directions",
                description="Get driving, walking, or transit directions between two locations. Perfect for navigation in Gaziantep and route planning.",
                parameters=types.Schema(
                    type=types.Type.OBJECT,
                    properties={
                        "origin": types.Schema(
                            type=types.Type.STRING, 
                            description="Starting location (e.g., 'Gaziantep Castle', 'my current location', 'hotel')"
                        ),
                        "destination": types.Schema(
                            type=types.Type.STRING, 
                            description="Destination location (e.g., 'Zeugma Museum', 'İmam Çağdaş Restaurant')"
                        ),
                        "travel_mode": types.Schema(
                            type=types.Type.STRING,
                            description="Mode of transportation",
                            enum=["driving", "walking", "transit", "cycling"]
                        )
                    },
                    required=["origin", "destination"]
                )
            )
        ]
        print(f"✅ API Manager: {len(self.function_declarations)} fallback functions loaded (including directions)")
    
    def get_function_declarations(self) -> List[types.FunctionDeclaration]:
        """Gemini için function declarations döndür"""
        return self.function_declarations
    
    def get_tools(self) -> List[types.Tool]:
        """Gemini için tools listesi döndür - FİX: Debug ile beraber"""
        print(f"🔧 DEBUG: get_tools() called, have {len(self.function_declarations)} declarations")
        
        if self.function_declarations:
            for i, decl in enumerate(self.function_declarations):
                print(f"🔧 DEBUG: Declaration {i}: {decl.name}")
            
            # TÜM function declarations'ları tek Tool'da topla
            tool = types.Tool(function_declarations=self.function_declarations)
            print(f"🔧 DEBUG: Created tool with {len(tool.function_declarations)} declarations")
            return [tool]
        else:
            print("❌ DEBUG: No function declarations available")
            return []
    
    def call_webhook_universal(self, endpoint: str, payload: Dict[str, Any], timeout: int = 10) -> Dict[str, Any]:
        """Universal webhook çağrısı - tüm API'ler için tek fonksiyon"""
        try:
            url = f"{self.webhook_url}{endpoint}"
            response = requests.post(url, json=payload, timeout=timeout)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"success": False, "error": f"API hatası: {str(e)}"}
    
    def handle_function_call(self, function_name: str, function_args: Dict[str, Any], current_language: str = "tr") -> str:
        """Tek function handler - tüm API çağrılarını yönetir"""
        
        if function_name not in self.available_functions:
            return f"⚠️ Bilinmeyen fonksiyon: {function_name}"
        
        function_info = self.available_functions[function_name]
        endpoint = function_info["endpoint"]
        
        try:
            # Function'a göre özel işlemler ve payload hazırlama
            if function_name == "get_weather_data":
                return self._handle_weather(function_args, current_language, endpoint)
            
            elif function_name == "get_currency_exchange":
                return self._handle_currency(function_args, endpoint)
            
            elif function_name == "get_places_search":
                return self._handle_places(function_args, endpoint)
            
            # YENİ: Directions handler eklendi
            elif function_name == "get_directions":
                return self._handle_directions(function_args, current_language, endpoint)
            
            else:
                # Genel işlem - yeni API'ler için
                return self._handle_generic(function_args, endpoint, function_name)
                
        except Exception as e:
            return f"❌ {function_name} hatası: {str(e)}"
    
    def _handle_weather(self, args: Dict[str, Any], language: str, endpoint: str) -> str:
        """Weather API işlemi"""
        city = args.get("city_name")
        time_period = args.get("time_period", "bugün")
        
        if not city:
            return "⚠️ Şehir adı gerekli"
        
        st.info(f"🌤️ Getting weather data for **{city}**...")
        
        payload = {
            "city_name": city,
            "time_period": time_period,
            "language": language
        }
        
        result = self.call_webhook_universal(endpoint, payload)
        return self._format_response(result, "Weather")
    
    def _handle_currency(self, args: Dict[str, Any], endpoint: str) -> str:
        """Currency API işlemi"""
        amount = args.get("amount")
        from_curr = args.get("from_currency")
        to_curr = args.get("to_currency")
        
        if not all([amount, from_curr, to_curr]):
            return "⚠️ Miktar ve para birimleri gerekli"
        
        st.info(f"💱 Converting **{amount} {from_curr} → {to_curr}**...")
        
        payload = {
            "amount": float(amount),
            "from_currency": from_curr.upper(),
            "to_currency": to_curr.upper()
        }
        
        result = self.call_webhook_universal(endpoint, payload)
        return self._format_response(result, "Currency")
    
    def _handle_places(self, args: Dict[str, Any], endpoint: str) -> str:
        """Places API işlemi"""
        query = args.get("query")
        location = args.get("location")
        additional_criteria = args.get("additional_criteria")
        
        if not query or not location:
            return "⚠️ Arama sorgusu ve lokasyon gerekli"
        
        # Additional criteria'yı query'ye ekle
        if additional_criteria:
            enhanced_query = f"{additional_criteria} {query}"
        else:
            enhanced_query = query
        
        st.info(f"📍 Searching for **{enhanced_query}** in **{location}**...")
        
        payload = {
            "query": f"{enhanced_query} {location}",
            "location": location,
            "location_bias": location
        }
        
        result = self.call_webhook_universal(endpoint, payload, timeout=15)
        return self._format_response(result, "Places")
    
    # YENİ: Directions handler
    def _handle_directions(self, args: Dict[str, Any], language: str, endpoint: str) -> str:
        """Directions API işlemi - Yol tarifi"""
        origin = args.get("origin")
        destination = args.get("destination")
        travel_mode = args.get("travel_mode", "driving")
        
        if not origin or not destination:
            if language == "tr":
                return "⚠️ Başlangıç ve varış noktası gerekli"
            else:
                return "⚠️ Origin and destination required"
        
        # Travel mode'u düzelt
        if travel_mode.lower() not in ["driving", "walking", "transit", "cycling"]:
            travel_mode = "driving"
        
        # Türkçe modları İngilizce'ye çevir
        mode_translations = {
            "araba": "driving",
            "arabayla": "driving", 
            "yürüyerek": "walking",
            "yürüyüş": "walking",
            "toplu taşıma": "transit",
            "otobüs": "transit",
            "bisiklet": "cycling",
            "bisikletle": "cycling"
        }
        
        travel_mode = mode_translations.get(travel_mode.lower(), travel_mode)
        
        # UI için mode simgesi
        mode_icons = {
            "driving": "🚗",
            "walking": "🚶",
            "transit": "🚌", 
            "cycling": "🚴"
        }
        
        mode_icon = mode_icons.get(travel_mode, "🗺️")
        
        st.info(f"{mode_icon} Getting directions from **{origin}** to **{destination}** ({travel_mode})...")
        
        payload = {
            "origin": origin,
            "destination": destination,
            "travel_mode": travel_mode,
            "language": language
        }
        
        result = self.call_webhook_universal(endpoint, payload, timeout=15)
        return self._format_response(result, "Directions")
    
    def _handle_generic(self, args: Dict[str, Any], endpoint: str, function_name: str) -> str:
        """Genel API işlemi - yeni API'ler için"""
        st.info(f"🔧 Calling {function_name}...")
        
        # Tüm args'ları payload olarak gönder
        payload = dict(args)
        
        result = self.call_webhook_universal(endpoint, payload)
        return self._format_response(result, function_name.replace("get_", "").title())
    
    def _format_response(self, webhook_result: Dict[str, Any], api_type: str) -> str:
        """Response formatla"""
        if not webhook_result.get("success"):
            return f"⚠️ {webhook_result.get('error', f'{api_type} hatası')}"
        
        if webhook_result.get("formatted_response"):
            return webhook_result["formatted_response"]
        
        return f"✅ {api_type} verisi alındı"
    
    def get_stats(self) -> Dict[str, Any]:
        """API Manager istatistikleri"""
        return {
            "webhook_url": self.webhook_url,
            "available_functions": len(self.available_functions),
            "function_names": list(self.available_functions.keys()),
            "declarations_loaded": len(self.function_declarations),
            "directions_enabled": "get_directions" in self.available_functions
        }
    
    def reload_functions(self):
        """Function'ları yeniden yükle"""
        self._load_functions()
        print("🔄 API Manager functions reloaded")
    
    def add_custom_function(self, function_name: str, endpoint: str, declaration: types.FunctionDeclaration):
        """Runtime'da yeni function ekle"""
        self.available_functions[function_name] = {
            "endpoint": endpoint,
            "method": "POST",
            "custom": True
        }
        self.function_declarations.append(declaration)
        print(f"➕ Custom function added: {function_name}")

# Singleton instance - bir kere oluştur, her yerden kullan
_api_manager_instance = None

def get_api_manager(webhook_url: str = "http://localhost:8000") -> APIManager:
    """APIManager singleton instance döndür"""
    global _api_manager_instance
    if _api_manager_instance is None:
        _api_manager_instance = APIManager(webhook_url)
    return _api_manager_instance