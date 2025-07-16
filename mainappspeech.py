import streamlit as st
from google import genai
from google.genai import types
import json
from datetime import datetime
import os
from langdetect import detect, DetectorFactory
from dotenv import load_dotenv
import azure.cognitiveservices.speech as speechsdk
import base64

from managers.instruction_manager import InstructionManager, get_comprehensive_system_instruction
from managers.api_manager import get_api_manager  

load_dotenv()

st.set_page_config(page_title="Tourism Chatbot with Azure Speech", page_icon="🤖", layout="centered")

# Configuration
GOOGLE_CLOUD_PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT_ID")
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "http://localhost:8000")
MODEL_NAME = os.getenv("MODEL_NAME", "gemini-2.0-flash-lite-001")
AZURE_SPEECH_KEY = os.getenv("AZURE_SPEECH_KEY")
AZURE_SPEECH_REGION = os.getenv("AZURE_SPEECH_REGION")

if not GOOGLE_CLOUD_PROJECT_ID:
    st.error(" Missing GOOGLE_CLOUD_PROJECT_ID")
    st.stop()

if not AZURE_SPEECH_KEY or not AZURE_SPEECH_REGION:
    st.warning(" Azure Speech not configured. Voice features disabled.")

DetectorFactory.seed = 0

# Azure destekli diller ve ses konfigürasyonu
SUPPORTED_LANGUAGES = {
    'tr': {'name': 'Türkçe', 'voice_name': 'tr-TR-EmelNeural','speech_language': 'tr-TR'},
    'en': {'name': 'English', 'voice_name': 'en-US-AriaNeural','speech_language': 'en-US'},
    'de': {'name': 'Deutsch', 'voice_name': 'de-DE-KatjaNeural','speech_language': 'de-DE'},
    'fr': {'name': 'Français', 'voice_name': 'fr-FR-DeniseNeural','speech_language': 'fr-FR'},
    'es': {'name': 'Español', 'voice_name': 'es-ES-ElviraNeural','speech_language': 'es-ES'},
    'it': {'name': 'Italiano', 'voice_name': 'it-IT-ElsaNeural','speech_language': 'it-IT'},
    'ja': {'name': '日本語', 'voice_name': 'ja-JP-NanamiNeural','speech_language': 'ja-JP'},
    'ar': {'name': 'العربية', 'voice_name': 'ar-SA-ZariyahNeural','speech_language': 'ar-SA'},
    'ru': {'name': 'Русский', 'voice_name': 'ru-RU-SvetlanaNeural','speech_language': 'ru-RU'},
    'zh': {'name': '中文', 'voice_name': 'zh-CN-XiaoxiaoNeural','speech_language': 'zh-CN'}
}

class AzureVoiceManager:
    def __init__(self):
        self.speech_key = AZURE_SPEECH_KEY
        self.speech_region = AZURE_SPEECH_REGION
        self.enabled = bool(self.speech_key and self.speech_region)
        
        if self.enabled:
            self.speech_config = speechsdk.SpeechConfig(self.speech_key, self.speech_region)
            self.speech_config.set_speech_synthesis_output_format(
                speechsdk.SpeechSynthesisOutputFormat.Audio16Khz32KBitRateMonoMp3)
    
    def speech_to_text_continuous(self, language='tr'):
        if not self.enabled:
            return None
        try:
            lang_config = SUPPORTED_LANGUAGES.get(language, SUPPORTED_LANGUAGES['tr'])
            speech_config = speechsdk.SpeechConfig(self.speech_key, self.speech_region)
            speech_config.speech_recognition_language = lang_config['speech_language']
            
            audio_config = speechsdk.audio.AudioConfig(use_default_microphone=True)
            speech_recognizer = speechsdk.SpeechRecognizer(speech_config, audio_config)
            result = speech_recognizer.recognize_once()
            
            return result.text if result.reason == speechsdk.ResultReason.RecognizedSpeech else None
        except:
            return None
    
    def text_to_speech(self, text, language='tr'):
        if not self.enabled or not text.strip():
            return None
        try:
            lang_config = SUPPORTED_LANGUAGES.get(language, SUPPORTED_LANGUAGES['tr'])
            speech_config = speechsdk.SpeechConfig(self.speech_key, self.speech_region)
            speech_config.speech_synthesis_voice_name = lang_config['voice_name']
            speech_config.set_speech_synthesis_output_format(
                speechsdk.SpeechSynthesisOutputFormat.Audio16Khz32KBitRateMonoMp3)
            
            synthesizer = speechsdk.SpeechSynthesizer(speech_config, None)
            result = synthesizer.speak_text_async(text).get()
            
            return result.audio_data if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted else None
        except:
            return None

def detect_language(text):
    try:
        if len(text.strip()) < 5:
            return 'tr'
        detected = detect(text)
        return detected if detected in SUPPORTED_LANGUAGES else 'tr'
    except:
        return 'tr'

class GeminiRAGWithMemory:
    def __init__(self):
        self.project_id =  GOOGLE_CLOUD_PROJECT_ID
        self.client = genai.Client(vertexai=True, project=self.project_id, location="global")
        self.model = MODEL_NAME
        self.conversation_history = []
        self.memory_file = "conversation_memory.json"
        self.webhook_url = WEBHOOK_URL
        self.current_language = 'tr'
        
        self.voice_manager = AzureVoiceManager()
        self.instruction_manager = InstructionManager()
        self.api_manager = get_api_manager(self.webhook_url)
        
        self.load_memory()
    
    def detect_and_set_language(self, user_query):
        detected_lang = detect_language(user_query)
        if detected_lang != self.current_language:
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
        except:
            pass

    def load_memory(self):
        try:
            if os.path.exists(self.memory_file):
                with open(self.memory_file, 'r', encoding='utf-8') as f:
                    memory_data = json.load(f)
                    
                if isinstance(memory_data, list):
                    self.conversation_history = memory_data
                    self.current_language = 'tr'
                else:
                    self.conversation_history = memory_data.get('conversation_history', [])
                    self.current_language = memory_data.get('current_language', 'tr')
            else:
                self.conversation_history = []
                self.current_language = 'tr'
        except:
            self.conversation_history = []
            self.current_language = 'tr'
    
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
    
    def build_contents_with_memory(self, user_query):
        contents = []
        for msg in self.conversation_history:
            role = "user" if msg["role"] == "user" else "model"
            contents.append(types.Content(role=role, parts=[types.Part(text=msg["content"])]))
        
        contents.append(types.Content(role="user", parts=[types.Part(text=user_query)]))
        return contents
    
    def generate_with_memory(self, user_query):
        detected_lang = self.detect_and_set_language(user_query)
        contents = self.build_contents_with_memory(user_query)
        
        system_instruction = get_comprehensive_system_instruction(detected_lang, self.instruction_manager)
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
                model=self.model, contents=contents, config=generate_content_config)

            for chunk in response_stream:
                if chunk.candidates and chunk.candidates[0].content and chunk.candidates[0].content.parts:
                    for part in chunk.candidates[0].content.parts:
                        if part.function_call:
                            function_call = part.function_call
                            function_name = function_call.name
                            function_args = {k: v for k, v in function_call.args.items()}

                            api_data = self.api_manager.handle_function_call(
                                function_name, function_args, self.current_language)
                            
                            full_response_content += api_data + "\n\n"
                            yield api_data + "\n\n"
                        else:
                            chunk_text = part.text
                            full_response_content += chunk_text
                            yield chunk_text
            
            self.add_to_memory("user", user_query)
            self.add_to_memory("model", full_response_content)
            
        except Exception as e:
            error_msg = f"❌ Error occurred: {str(e)}"
            yield error_msg
            self.add_to_memory("user", user_query)
            self.add_to_memory("model", error_msg)

def render_message(role, content, message_id=None):
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
        
        col1, col2, col3, col4, col5 = st.columns([0.1, 0.1, 0.1, 0.1, 0.7])
        
        with col1:
            if st.button("🔊", key=f"speak_{message_id}", help="Listen", use_container_width=False):
                if AZURE_SPEECH_KEY and content.strip():
                    with st.spinner("♪"):
                        current_lang = getattr(st.session_state.rag_bot, 'current_language', 'tr')
                        audio_bytes = st.session_state.rag_bot.voice_manager.text_to_speech(content, current_lang)
                        if audio_bytes:
                            create_audio_player(audio_bytes)

def create_audio_player(audio_bytes):
    if audio_bytes:
        audio_b64 = base64.b64encode(audio_bytes).decode()
        audio_html = f'''
        <audio controls autoplay style="width: 200px; height: 30px; margin: 5px 0;">
            <source src="data:audio/mp3;base64,{audio_b64}" type="audio/mp3">
        </audio>
        '''
        st.markdown(audio_html, unsafe_allow_html=True)

def main():
    st.title("🤖 Tourism Chatbot with Azure Speech")
    st.markdown("*Speak or type in any language - Click 🎤 to speak, 🔊 to listen*")
    
    if AZURE_SPEECH_KEY:
        st.success("✅ Azure Speech connected - Free tier active")
    else:
        st.error("❌ Azure Speech not configured")
    
    if 'rag_bot' not in st.session_state:
        with st.spinner("🔧 Setting up system..."):
            try:
                st.session_state.rag_bot = GeminiRAGWithMemory()
                st.success("✅ System ready!")
            except Exception as e:
                st.error(f"❌ System setup error: {str(e)}")
                st.stop()
    
    if 'messages' not in st.session_state:
        st.session_state.messages = [
            {"role": "assistant", "content": "🌟 Hello! I can help you in any language - speak or type!\n\nMerhaba! Size Azure Speech ile sesli veya yazılı yardımcı olabilirim!"}
        ]
    
    for i, message in enumerate(st.session_state.messages):
        render_message(message["role"], message["content"], message_id=i)
    
    # Input section with voice buttons
    col1, col2 = st.columns([0.9, 0.1])
    
    with col1:
        user_input = st.chat_input("Type your message here...", key="main_input")
    
    with col2:
        if st.button("🎤", help="Speak", use_container_width=False, key="voice_button"):
            if not AZURE_SPEECH_KEY:
                st.toast("❌ Azure Speech not configured", icon="❌")
            else:
                with st.spinner("🎤 Listening..."):
                    try:
                        current_lang = getattr(st.session_state.rag_bot, 'current_language', 'tr')
                        text = st.session_state.rag_bot.voice_manager.speech_to_text_continuous(current_lang)
                        if text:
                            st.toast(f"🎤 Heard: {text[:30]}...", icon="🎤")
                            st.session_state.voice_input = text
                            st.rerun()
                        else:
                            st.toast("❌ Could not understand speech", icon="❌")
                    except Exception as e:
                        st.toast("❌ Voice input failed", icon="❌")
    
    # Handle voice input
    if hasattr(st.session_state, 'voice_input') and st.session_state.voice_input:
        user_input = st.session_state.voice_input
        st.session_state.voice_input = None
    
    if user_input:
        st.session_state.messages.append({"role": "user", "content": user_input})
        render_message("user", user_input)
        
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
        
        if full_response:
            st.session_state.messages.append({"role": "assistant", "content": full_response})
            st.rerun()

if __name__ == "__main__":
    main()