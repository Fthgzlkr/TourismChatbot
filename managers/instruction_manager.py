# instruction_manager.py
# Detaylı instruction dosyasını yükleyip cache'leyen sistem

import json
import os
from datetime import datetime

class InstructionManager:
    """
    Detaylı instruction'ları dosyadan yükleyip cache için optimize eden sistem
    """
    
    def __init__(self, instruction_file="system_instructions.json"):
        self.instruction_file = instruction_file
        self.instructions_data = None
        self.load_instructions()
        
    def load_instructions(self):
        """Instruction dosyasını yükle"""
        try:
            if os.path.exists(self.instruction_file):
                with open(self.instruction_file, 'r', encoding='utf-8') as f:
                    self.instructions_data = json.load(f)
                print(f"✅ Instructions loaded from {self.instruction_file}")
                
                # Token count tahmini
                sample_instruction = self.get_detailed_system_instruction('tr')
                estimated_tokens = len(sample_instruction.split()) * 1.3
                print(f"📊 Estimated instruction tokens: {estimated_tokens:.0f}")
                
                if estimated_tokens >= 1024:
                    print("✅ Instructions are cache-eligible (1024+ tokens)")
                else:
                    print("⚠️ Instructions might be too short for caching")
                    
            else:
                print(f"❌ Instruction file not found: {self.instruction_file}")
                self.create_default_instructions()
                
        except Exception as e:
            print(f"❌ Error loading instructions: {e}")
            self.create_default_instructions()
    
    def create_default_instructions(self):
        """Default instruction dosyası oluştur"""
        print("🔧 Creating default instruction file...")
        
        # Minimal default data
        self.instructions_data = {
            "version": "2.0",
            "last_updated": datetime.now().strftime('%Y-%m-%d'),
            "base_template": "You are a comprehensive tourism assistant.",
            "languages": {
                "tr": {
                    "name": "Türkçe",
                    "instructions": "Sen kapsamlı bir turizm asistanısın. Türkçe cevap ver.",
                    "cultural_context": "Türk kültürünü anlıyorsun.",
                    "examples": [
                        "Kullanıcı: 'İstanbul'da ne yapabilirim?' → Sen: 'İstanbul'da muhteşem bir gezi sizi bekliyor!'"
                    ]
                },
                "en": {
                    "name": "English", 
                    "instructions": "You are a comprehensive tourism assistant. Always respond in English.",
                    "cultural_context": "You understand international travel customs.",
                    "examples": [
                        "User: 'What can I do in Istanbul?' → You: 'Istanbul offers amazing experiences!'"
                    ]
                }
            },
            "function_definitions": {
                "weather": {
                    "name": "get_weather_data",
                    "description": "Provides weather information",
                    "usage_guidelines": ["Always specify the city name clearly"]
                }
            },
            "behavioral_guidelines": {
                "conversation_flow": [
                    "Maintain natural, engaging conversations",
                    "Use conversation history intelligently"
                ]
            },
            "advanced_features": {
                "contextual_awareness": [
                    "Understand implicit references to previously mentioned locations"
                ]
            }
        }
        
        # Dosyaya kaydet
        try:
            with open(self.instruction_file, 'w', encoding='utf-8') as f:
                json.dump(self.instructions_data, f, ensure_ascii=False, indent=2)
            print(f"✅ Default instructions created: {self.instruction_file}")
        except Exception as e:
            print(f"❌ Error creating default file: {e}")
    
    def get_detailed_system_instruction(self, detected_language):
        """
        Detaylı, cache-ready system instruction oluştur
        """
        if not self.instructions_data:
            # Fallback to simple instruction
            return self.get_simple_fallback_instruction(detected_language)
        
        lang_data = self.instructions_data.get('languages', {}).get(detected_language)
        if not lang_data:
            # Fallback to English or Turkish
            lang_data = self.instructions_data.get('languages', {}).get('en') or \
                       self.instructions_data.get('languages', {}).get('tr')
        
        if not lang_data:
            return self.get_simple_fallback_instruction(detected_language)
        
        # Detaylı instruction oluştur
        instruction = self._build_comprehensive_instruction(detected_language, lang_data)
        
        return instruction
    
    def _build_comprehensive_instruction(self, language, lang_data):
        """
        Kapsamlı instruction'ı birleştir
        """
        lang_name = lang_data.get('name', language)
        
        # Base template
        base = self.instructions_data.get('base_template', '')
        
        # Language-specific instructions
        lang_instructions = lang_data.get('instructions', '')
        cultural_context = lang_data.get('cultural_context', '')
        examples = lang_data.get('examples', [])
        
        # Function definitions
        functions = self.instructions_data.get('function_definitions', {})
        
        # Behavioral guidelines
        behavior = self.instructions_data.get('behavioral_guidelines', {})
        
        # Advanced features
        advanced = self.instructions_data.get('advanced_features', {})
        
        # Response templates
        templates = self.instructions_data.get('response_templates', {})
        
        # Comprehensive instruction oluştur
        instruction = f"""TOURISM ASSISTANT SYSTEM v2.0 - COMPREHENSIVE INSTRUCTIONS

{base}

=== LANGUAGE CONFIGURATION ===
Target Language: {lang_name} ({language})
{lang_instructions}

=== CULTURAL CONTEXT ===
{cultural_context}

=== CONVERSATION EXAMPLES ==="""

        # Examples ekle
        for i, example in enumerate(examples[:3], 1):
            instruction += f"\n{i}. {example}"

        instruction += f"""

=== FUNCTION CAPABILITIES ==="""

        # Function definitions ekle
        for func_name, func_data in functions.items():
            instruction += f"""

{func_name.upper()}:
- Function: {func_data.get('name', '')}
- Description: {func_data.get('description', '')}
- Usage Guidelines:"""
            
            for guideline in func_data.get('usage_guidelines', [])[:3]:
                instruction += f"\n  • {guideline}"

        instruction += f"""

=== BEHAVIORAL GUIDELINES ==="""

        # Behavioral guidelines ekle
        for category, guidelines in behavior.items():
            instruction += f"""

{category.replace('_', ' ').title()}:"""
            for guideline in guidelines[:3]:
                instruction += f"\n• {guideline}"

        instruction += f"""

=== ADVANCED CAPABILITIES ==="""

        # Advanced features ekle
        for feature, details in advanced.items():
            instruction += f"""

{feature.replace('_', ' ').title()}:"""
            for detail in details[:2]:
                instruction += f"\n• {detail}"

        # Response templates ekle
        if templates:
            instruction += f"""

=== RESPONSE TEMPLATES ==="""
            
            greeting = templates.get('greeting_multilingual', {}).get(language, '')
            if greeting:
                instruction += f"""
Greeting Template: "{greeting}"
"""

        instruction += f"""

=== CRITICAL REQUIREMENTS ===
1. ALWAYS respond in {lang_name} language
2. Use natural, native-level fluency in {lang_name}
3. Remember conversation history and context
4. Extract location information from previous messages
5. Use appropriate cultural context for {lang_name} speakers
6. Provide specific, actionable information with details
7. Use function calls when appropriate for weather, currency, and places
8. Maintain helpful and friendly tone throughout interaction
9. Provide alternative suggestions when primary options unavailable
10. Include practical travel information (costs, timing, logistics)

=== SYSTEM METADATA ===
Version: {self.instructions_data.get('version', '2.0')}
Last Updated: {self.instructions_data.get('last_updated', datetime.now().strftime('%Y-%m-%d'))}
Language: {lang_name} ({language})
Token Optimization: Designed for efficient caching with 1024+ tokens
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Remember: Every response must be in {lang_name} language with perfect cultural adaptation!"""

        return instruction
    
    def get_simple_fallback_instruction(self, detected_language):
        """
        Basit fallback instruction (dosya yüklenmediğinde)
        """
        lang_names = {
            'tr': 'Türkçe',
            'en': 'English',
            'de': 'Deutsch',
            'fr': 'Français',
            'es': 'Español',
            'it': 'Italiano',
            'ja': '日本語',
            'ar': 'العربية',
            'ru': 'Русский',
            'zh': '中文'
        }
        
        lang_name = lang_names.get(detected_language, 'English')
        
        return f"""You are a helpful travel assistant with excellent memory and context awareness.

LANGUAGE INSTRUCTION:
- User's detected language: {lang_name} ({detected_language})
- ALWAYS respond in the user's detected language: {lang_name}
- Use natural, native-level fluency in {lang_name}
- All your responses must be in {lang_name} language

CONTEXT & MEMORY:
- Remember conversation history very well and use context
- If user mentioned a city before, remember and use it
- Words like "here/there/burada/orada/hier/là" refer to previously mentioned cities
- Historical places are connected to cities (Hagia Sophia=Istanbul, Cappadocia=Nevşehir)
- Don't ask unnecessary location questions, extract from conversation history

FUNCTION CALLS AVAILABLE:
1. get_weather_data(city_name, time_period) - Weather information
2. get_currency_exchange(amount, from_currency, to_currency) - Currency conversion  
3. get_places_search(query, location, additional_criteria) - Place search

BEHAVIOR:
- Have natural conversations, don't constantly ask for locations
- Only ask for missing information if really necessary
- Use context from previous messages intelligently
- Be helpful, friendly, and culturally appropriate for {lang_name} speakers

REMEMBER: Always respond in {lang_name} language!"""

    def get_instruction_stats(self):
        """
        Instruction istatistikleri
        """
        if not self.instructions_data:
            return {"status": "not_loaded"}
        
        sample = self.get_detailed_system_instruction('tr')
        
        return {
            "status": "loaded",
            "file_path": self.instruction_file,
            "languages_supported": len(self.instructions_data.get('languages', {})),
            "version": self.instructions_data.get('version', 'unknown'),
            "estimated_tokens": len(sample.split()) * 1.3,
            "character_count": len(sample),
            "cache_eligible": len(sample.split()) * 1.3 >= 1024
        }

    def update_instructions(self, new_data):
        """
        Instruction'ları güncelle ve dosyaya kaydet
        """
        try:
            if self.instructions_data:
                # Mevcut data ile birleştir
                self.instructions_data.update(new_data)
            else:
                self.instructions_data = new_data
            
            # Dosyaya kaydet
            with open(self.instruction_file, 'w', encoding='utf-8') as f:
                json.dump(self.instructions_data, f, ensure_ascii=False, indent=2)
            
            print(f"✅ Instructions updated and saved to {self.instruction_file}")
            return True
            
        except Exception as e:
            print(f"❌ Error updating instructions: {e}")
            return False

    def add_language(self, language_code, language_data):
        """
        Yeni dil desteği ekle
        """
        try:
            if not self.instructions_data:
                self.instructions_data = {"languages": {}}
            
            if "languages" not in self.instructions_data:
                self.instructions_data["languages"] = {}
            
            self.instructions_data["languages"][language_code] = language_data
            
            # Dosyaya kaydet
            with open(self.instruction_file, 'w', encoding='utf-8') as f:
                json.dump(self.instructions_data, f, ensure_ascii=False, indent=2)
            
            print(f"✅ Language {language_code} added successfully")
            return True
            
        except Exception as e:
            print(f"❌ Error adding language: {e}")
            return False

# Updated system instruction function
def get_comprehensive_system_instruction(detected_language, instruction_manager=None):
    """
    Ana kodda kullanılacak yeni instruction fonksiyonu
    """
    if instruction_manager is None:
        # Fallback basit instruction
        return get_simple_system_instruction(detected_language)
    
    return instruction_manager.get_detailed_system_instruction(detected_language)


def get_simple_system_instruction(detected_language):
    """
    Fallback basit instruction (eski versiyon)
    """
    lang_names = {
        'tr': 'Türkçe',
        'en': 'English', 
        'de': 'Deutsch',
        'fr': 'Français',
        'es': 'Español',
        'it': 'Italiano',
        'ja': '日本語',
        'ar': 'العربية',
        'ru': 'Русский',
        'zh': '中文'
    }
    
    lang_name = lang_names.get(detected_language, 'English')
    
    return f"""You are a helpful travel assistant with excellent memory and context awareness. 

LANGUAGE INSTRUCTION:
- User's detected language: {lang_name} ({detected_language})
- ALWAYS respond in the user's detected language: {lang_name}
- Use natural, native-level fluency in {lang_name}
- All your responses must be in {lang_name} language

CONTEXT & MEMORY:
- Remember conversation history very well and use context
- If user mentioned a city before, remember and use it
- Words like "here/there/burada/orada/hier/là" refer to previously mentioned cities
- Historical places are connected to cities (Hagia Sophia=Istanbul, Cappadocia=Nevşehir)
- Don't ask unnecessary location questions, extract from conversation history

FUNCTION CALLS AVAILABLE:
1. get_weather_data(city_name, time_period) - Weather information
2. get_currency_exchange(amount, from_currency, to_currency) - Currency conversion  
3. get_places_search(query, location, additional_criteria) - Place search

BEHAVIOR:
- Have natural conversations, don't constantly ask for locations
- Only ask for missing information if really necessary
- Use context from previous messages intelligently
- Be helpful, friendly, and culturally appropriate for {lang_name} speakers

REMEMBER: Always respond in {lang_name} language!"""