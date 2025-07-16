# instruction_manager.py - ULTRA MINIMAL VERSION
import json
import os
from datetime import datetime

class InstructionManager:
    """Ultra minimal instruction manager"""
    
    def __init__(self, instruction_file="gaziantep_system_instructions.json"):
        # JSON dosyasına gerek yok artık - hardcoded minimal instruction
        pass
    
    def get_minimal_instruction(self, language):
        """Ultra minimal instruction - maksimum 50-100 token"""
        
        if language == 'tr':
            return """Gaziantep turizm uzmanısın. Türkçe cevap ver.

API ZORUNLU:
• Para: get_currency_exchange()
• Hava: get_weather_data()
• Yer: get_places_search()
• Yol: get_directions()

Uzmanlık: Antep kebabı, baklava, künefe, İmam Çağdaş, Zeugma, Kale.

Sıcak, yerel bilgili. Geçmişi hatırla."""

        else:
            return """Gaziantep tourism expert. Respond in English.

MANDATORY API:
• Currency: get_currency_exchange()
• Weather: get_weather_data()
• Places: get_places_search()
• Directions: get_directions()

Expertise: Antep kebab, baklava, künefe, İmam Çağdaş, Zeugma, Castle.

Warm, local expert. Remember history."""

    def get_detailed_system_instruction(self, detected_language):
        """Ana fonksiyon"""
        return self.get_minimal_instruction(detected_language)
    
    def load_instructions(self):
        """Artık dosya yüklemeye gerek yok"""
        pass
    
    def get_simple_gaziantep_fallback_instruction(self, detected_language):
        """Fallback"""
        return self.get_minimal_instruction(detected_language)


# UPDATED FUNCTIONS - MINIMAL
def get_comprehensive_system_instruction(detected_language, instruction_manager=None):
    """Ultra minimal system instruction"""
    if instruction_manager is None:
        return get_simple_gaziantep_system_instruction(detected_language)
    
    return instruction_manager.get_minimal_instruction(detected_language)


def get_simple_gaziantep_system_instruction(detected_language):
    """Ultra minimal fallback"""
    
    if detected_language == 'tr':
        return """Gaziantep uzmanısın. Türkçe cevap ver.

API: Para→get_currency_exchange, Hava→get_weather_data, Yer→get_places_search, Yol→get_directions

Antep kebabı, baklava, künefe, İmam Çağdaş, Zeugma. Sıcak, yerel."""

    else:
        return """Gaziantep expert. English responses.

API: Currency→get_currency_exchange, Weather→get_weather_data, Places→get_places_search, Directions→get_directions

Antep kebab, baklava, künefe, İmam Çağdaş, Zeugma. Warm, local."""


# =============================================================================
# MINIMAL JSON DOSYASI İÇERİĞİ (İsteğe bağlı - artık kullanılmıyor)
# =============================================================================

MINIMAL_JSON_CONTENT = {
  "version": "3.0-minimal",
  "languages": {
    "tr": {
      "instruction": "Gaziantep uzmanısın. API: Para→get_currency_exchange, Hava→get_weather_data, Yer→get_places_search, Yol→get_directions. Antep kebabı, baklava, künefe."
    },
    "en": {
      "instruction": "Gaziantep expert. API: Currency→get_currency_exchange, Weather→get_weather_data, Places→get_places_search, Directions→get_directions. Antep kebab, baklava, künefe."
    }
  }
}

def create_minimal_json_file():
    """Minimal JSON dosyası oluştur (opsiyonel)"""
    try:
        with open("gaziantep_system_instructions.json", 'w', encoding='utf-8') as f:
            json.dump(MINIMAL_JSON_CONTENT, f, ensure_ascii=False, indent=2)
        print("✅ Minimal JSON created")
    except Exception as e:
        print(f"❌ Error creating JSON: {e}")

# Kullanım için JSON oluştur
if __name__ == "__main__":
    create_minimal_json_file()