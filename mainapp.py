import streamlit as st
from google import genai
from google.genai import types
from google.genai import caches
from simple_rag import SimpleRAGSystem
import json
from datetime import datetime
import os
import langdetect
from langdetect import detect, DetectorFactory

from managers.instruction_manager import InstructionManager, get_comprehensive_system_instruction
from managers.api_manager import get_api_manager  

# Streamlit config
st.set_page_config(
    page_title="Tourism Chatbot",
    page_icon="🤖",
    layout="centered"
)

# Configuration
GOOGLE_CLOUD_PROJECT_ID = "fast-haiku-463913-s9"
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "http://localhost:8000")
MODEL_NAME = "gemini-2.0-flash-lite-001"

# Dil algılama için seed ayarla
DetectorFactory.seed = 0

# Basit dil konfigürasyonu - sadece dil adları
SUPPORTED_LANGUAGES = {
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

# Load CSS
try:
    with open('custom.css') as f:
        css = f.read()
    st.markdown(f'<style>{css}</style>', unsafe_allow_html=True)
except FileNotFoundError:
    pass  # CSS olmasa da çalışsın

# Dil algılama fonksiyonu
def detect_language(text):
    """Metinden dili algıla"""
    try:
        if len(text.strip()) < 5:
            return 'tr'  # Varsayılan
        
        detected = detect(text)
        return detected if detected in SUPPORTED_LANGUAGES else 'tr'
            
    except Exception as e:
        return 'tr'  # Hata durumunda Türkçe


# --- Main RAG Class ---
class GeminiRAGWithMemory:
    def __init__(self, project_id="fast-haiku-463913-s9"):
        # Google Cloud Project API
        self.client = genai.Client(
            vertexai=True,
            project=project_id,
            location="global"
        )
        self.model = MODEL_NAME
        self.conversation_history = []
        self.memory_file = "conversation_memory.json"
        self.webhook_url = WEBHOOK_URL
        self.rag_system = None
        self.current_language = 'tr'  # Varsayılan dil
        
        #Yeni manager sınıf ları
        self.instruction_manager = InstructionManager()
        self.api_manager = get_api_manager(self.webhook_url)
        
        self.setup_rag()
        self.load_memory()
        
    def setup_rag(self):
        """RAG sistemini kur"""
        try:
            print("🤖 RAG sistemi kuruluyor...")
            self.rag_system = SimpleRAGSystem()
            
            if self.rag_system.setup():
                stats = self.rag_system.get_stats()
                print(f"✅ RAG hazır: {stats['sites_count']} UNESCO sitesi")
            else:
                print("❌ RAG kurulumu başarısız")
                self.rag_system = None
                
        except Exception as e:
            print(f"❌ RAG hatası: {str(e)}")
            self.rag_system = None
    
    def get_rag_context(self, user_query):
        """RAG sisteminden context al"""
        if not self.rag_system:
            return None
            
        try:
            results = self.rag_system.search(user_query, top_k=15, threshold=0.1)
            if results:
                context = self.rag_system.format_for_gemini(results)
                print(f"📚 RAG: {len(results)} sonuç bulundu")
                return context
            else:
                print("📚 RAG: İlgili sonuç bulunamadı")
                return None
                
        except Exception as e:
            print(f"❌ RAG arama hatası: {str(e)}")
            return None
    
    def detect_and_set_language(self, user_query):
        """Kullanıcı mesajından dili algıla ve ayarla"""
        detected_lang = detect_language(user_query)
        
        # Dil değişikliği kontrolü
        if detected_lang != self.current_language:
            lang_name = SUPPORTED_LANGUAGES.get(detected_lang, 'Türkçe')
            print(f"🌍 Dil değişikliği: {self.current_language} -> {detected_lang} ({lang_name})")
            self.current_language = detected_lang
        
        return detected_lang
        
    def save_memory(self):
        try:
            memory_data = {
                'conversation_history': self.conversation_history,
                'current_language': self.current_language
            }
            with open(self.memory_file, 'w', encoding='utf-8') as f:
                json.dump(memory_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Memory kaydetme hatası: {e}")

    def load_memory(self):
        try:
            if os.path.exists(self.memory_file):
                with open(self.memory_file, 'r', encoding='utf-8') as f:
                    memory_data = json.load(f)
                    
                # Eski format kontrolü
                if isinstance(memory_data, list):
                    self.conversation_history = memory_data
                    self.current_language = 'tr'
                else:
                    self.conversation_history = memory_data.get('conversation_history', [])
                    self.current_language = memory_data.get('current_language', 'tr')
                    
                print(f"📚 Memory yüklendi: {len(self.conversation_history)} mesaj")
            else:
                self.conversation_history = []
                self.current_language = 'tr'
                print("Memory dosyası bulunamadı, yeni başlatılıyor")
                
        except (FileNotFoundError, json.JSONDecodeError) as e:
            self.conversation_history = []
            self.current_language = 'tr'
            print(f"Memory yükleme hatası: {e}")

    def get_recent_location(self):
        """Son 3 mesajdan lokasyon çıkar - basit regex"""
        cities = []
        for msg in reversed(self.conversation_history[-3:]):
            content = msg.get('content', '').lower()
            
            # Basit şehir bulma - sadece temel kalıplar
            words = content.split()
            for word in words:
                # Basit şehir ismi kontrolü (3+ karakter, büyük harfle başlayan)
                if len(word) >= 3 and word[0].isupper() and word.isalpha():
                    cities.append(word)
        
        return cities[-1] if cities else None
    
    def add_to_memory(self, role, content):
        self.conversation_history.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "language": self.current_language
        })
        
        if len(self.conversation_history) > 25:
            self.conversation_history = self.conversation_history[-25:]
        
        self.save_memory()
        print(f"Memory'ye eklendi: {role} - {content[:50]}... [Lang: {self.current_language}]")
    
    def build_contents_with_memory(self, user_query, rag_context=None):
        contents = []
        
        processed_query = user_query
        
        # RAG context ekle
        if rag_context:
            processed_query = f"{processed_query}\n\n[UNESCO VERİLERİ]\n{rag_context}\n[/UNESCO VERİLERİ]"
        
        for msg in self.conversation_history:
            role = "user" if msg["role"] == "user" else "model"
            contents.append(
                types.Content(
                    role=role,
                    parts=[types.Part(text=msg["content"])]
                )
            )
        
        contents.append(
            types.Content(
                role="user",
                parts=[types.Part(text=processed_query)]
            )
        )
        
        return contents
    
    def generate_with_memory(self, user_query):
        # Dil algılama ve ayarlama
        detected_lang = self.detect_and_set_language(user_query)
        
        # RAG context kontrolü - basit anahtar kelimeler
        rag_context = None
        if any(keyword in user_query.lower() for keyword in ['unesco', 'heritage', 'miras', 'tarih', 'history', 'culture', 'kültür']):
            if self.rag_system:
                rag_context = self.get_rag_context(user_query)
        
        # Build contents for Gemini
        contents = self.build_contents_with_memory(user_query, rag_context)
        
        # ✅ Instruction Manager kullanarak sistem talimatı al
        system_instruction = get_comprehensive_system_instruction(detected_lang, self.instruction_manager)
        
        # ✅ YENİ: API Manager'dan tools al (50+ satır kod silindi!)
        tools = self.api_manager.get_tools()

        generate_content_config = types.GenerateContentConfig(
            temperature=0.3,
            top_p=0.95,
            tools=tools,
            system_instruction=system_instruction
        )
        
        try:
            full_response_content = ""
            
            response_stream = self.client.models.generate_content_stream(
                model=self.model,
                contents=contents,
                config=generate_content_config,
            )

            for chunk in response_stream:
                if chunk.candidates and chunk.candidates[0].content and chunk.candidates[0].content.parts:
                    for part in chunk.candidates[0].content.parts:
                        if part.function_call:
                            function_call = part.function_call
                            function_name = function_call.name
                            function_args = {k: v for k, v in function_call.args.items()}

                            # ✅ YENİ: Tek satır - tüm API'ler (100+ satır if-else silindi!)
                            api_data = self.api_manager.handle_function_call(
                                function_name, function_args, self.current_language
                            )
                            
                            full_response_content += api_data + "\n\n"
                            yield api_data + "\n\n"

                        else:
                            chunk_text = part.text
                            full_response_content += chunk_text
                            yield chunk_text
            
            self.add_to_memory("user", user_query)
            self.add_to_memory("model", full_response_content)
            
        except Exception as e:
            error_msg = f"❌ Error occurred / Bir hata oluştu: {str(e)}"
            yield error_msg
            self.add_to_memory("user", user_query)
            self.add_to_memory("model", error_msg)

# --- Streamlit App ---
def render_message(role, content):
    """Render chat messages"""
    if role == "user":
        st.markdown(f"""
        <div class="chat-message user-message">
            <div class="message-avatar user-avatar">👤</div>
            <div style="flex: 1;">{content}</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="chat-message bot-message">
            <div class="message-avatar bot-avatar">🤖</div>
            <div style="flex: 1;">{content}</div>
        </div>
        """, unsafe_allow_html=True)

def main():
    st.title("🤖 Tourism Chatbot")
    st.markdown("*Automatically detects and responds in your language*")
    
    # Initialize RAG bot
    if 'rag_bot' not in st.session_state:
        with st.spinner("🔧 Setting up system..."):
            try:
                st.session_state.rag_bot = GeminiRAGWithMemory()
                
                # ✅ Instruction Manager İstatistikleri
                stats = st.session_state.rag_bot.instruction_manager.get_instruction_stats()
                if stats["status"] == "loaded":
                    st.success(f"✅ System ready! Instructions: {stats['languages_supported']} languages, {stats['estimated_tokens']:.0f} tokens")
                else:
                    st.warning("⚠️ Instructions not fully loaded, using fallback")
                
                # ✅ YENİ: API Manager İstatistikleri
                api_stats = st.session_state.rag_bot.api_manager.get_stats()
                st.info(f"🔧 API Manager: {api_stats['available_functions']} functions loaded")
                
                # Debug bilgisi
                with st.expander("🔧 System Details"):
                    st.json({
                        "instructions": stats,
                        "api_manager": api_stats
                    })
                    
            except Exception as e:
                st.error(f"❌ System setup error: {str(e)}")
                st.stop()
    
    # Initialize messages
    if 'messages' not in st.session_state:
        st.session_state.messages = [
            {"role": "assistant", "content": "🌟 Hello! I can help you in any language - just start typing!\n\nMerhaba! Size herhangi bir dilde yardımcı olabilirim!\n\nHola! Puedo ayudarte en cualquier idioma!"}
        ]
    
    # Display chat messages
    for message in st.session_state.messages:
        render_message(message["role"], message["content"])
    
    # Chat input
    user_input = st.chat_input("Type in any language...")
    
    if user_input:
        # Add user message
        st.session_state.messages.append({"role": "user", "content": user_input})
        render_message("user", user_input)
        
        # Generate response
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            full_response = ""
            
            try:
                for chunk in st.session_state.rag_bot.generate_with_memory(user_input):
                    full_response += chunk
                    message_placeholder.markdown(full_response + "▌")
                
                message_placeholder.markdown(full_response)
                
            except Exception as e:
                error_msg = f"❌ An error occurred: {str(e)}"
                message_placeholder.markdown(error_msg)
                full_response = error_msg
        
        # Add assistant response to chat history
        if full_response:
            st.session_state.messages.append({"role": "assistant", "content": full_response})

if __name__ == "__main__":
    main()