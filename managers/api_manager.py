# api_manager.py - Universal API Manager
import requests
import streamlit as st
from typing import Dict, Any, List, Optional
from google.genai import types
import json

class APIManager:
    """Tüm webhook API çağrılarını ve function handling'i yöneten tek sınıf"""
    
    def __init__(self, webhook_url: str = "http://localhost:8000"):
        self.webhook_url = webhook_url
        self.available_functions = {}
        self.function_declarations = []
        self._load_functions()
    
    def _load_functions(self):
        """Webhook'tan mevcut function'ları otomatik yükle"""
        try:
            response = requests.get(f"{self.webhook_url}/functions", timeout=5)
            if response.status_code == 200:
                functions_data = response.json()
                self.available_functions = functions_data.get("functions", {})
                self.function_declarations = functions_data.get("declarations", [])
                print(f"✅ API Manager: {len(self.available_functions)} function loaded")
            else:
                # Fallback: Manuel function tanımları
                self._load_fallback_functions()
        except Exception as e:
            print(f"⚠️ Could not load functions from webhook, using fallback: {str(e)}")
            self._load_fallback_functions()
    
    def _load_fallback_functions(self):
        """Webhook'a erişilemezse fallback function'lar"""
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
            }
        }
        
        # Manuel function declarations (mevcut kodunuzdan)
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
            )
        ]
        print(f"✅ API Manager: Fallback functions loaded")
    
    def get_function_declarations(self) -> List[types.FunctionDeclaration]:
        """Gemini için function declarations döndür"""
        return self.function_declarations
    
    def get_tools(self) -> List[types.Tool]:
        """Gemini için tools listesi döndür"""
        if self.function_declarations:
            return [types.Tool(function_declarations=self.function_declarations)]
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
            "declarations_loaded": len(self.function_declarations)
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