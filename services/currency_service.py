# services/currency_service.py
import requests
from typing import Dict, Any

class CurrencyService:
    """Currency Exchange API Servisi"""
    
    def __init__(self):
        self.base_url = "https://api.exchangerate-api.com/v4/latest"
    
    def get_currency_data(self, amount: float, from_currency: str, to_currency: str) -> Dict[str, Any]:
        """Para birimi çevirme"""
        try:
            url = f"{self.base_url}/{from_currency.upper()}"
            
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            to_currency_upper = to_currency.upper()
            
            if to_currency_upper in data.get("rates", {}):
                exchange_rate = data["rates"][to_currency_upper]
                converted_amount = round(amount * exchange_rate, 2)
                
                return {
                    "success": True,
                    "amount": amount,
                    "from_currency": from_currency.upper(),
                    "to_currency": to_currency_upper,
                    "exchange_rate": exchange_rate,
                    "converted_amount": converted_amount,
                    "date": data.get("date")
                }
            else:
                return {
                    "success": False,
                    "error": f"'{to_currency}' para birimi desteklenmiyor"
                }
                
        except Exception as e:
            return {"success": False, "error": f"Currency API hatası: {str(e)}"}
    
    def format_response(self, data: Dict[str, Any]) -> str:
        """Response formatla"""
        if not data.get("success"):
            return f"⚠️ Para birimi çevirme hatası: {data.get('error', 'Bilinmeyen hata')}"
        
        return (
            f"💱 **Para Birimi Çevirme**\n"
            f"💰 {data['amount']} {data['from_currency']} = **{data['converted_amount']} {data['to_currency']}**\n"
            f"📊 Kur: 1 {data['from_currency']} = {data['exchange_rate']} {data['to_currency']}\n"
            f"📅 Tarih: {data.get('date', 'Bilinmiyor')}"
        )