import json
import pickle
import numpy as np
from typing import List, Dict, Tuple, Optional
from sentence_transformers import SentenceTransformer
import faiss
import os

class GaziantepRAGSystem:
    """
    Gaziantep turizm verileri için basit ama güvenilir RAG sistemi.
    FAISS + Sentence Transformers kullanır.
    """
    
    def __init__(self, 
                 data_path: str = "./data/antep.json",
                 model_name: str = "paraphrase-multilingual-MiniLM-L12-v2",
                 cache_dir: str = "./antep_rag_cache"):
        
        self.data_path = data_path
        self.model_name = model_name
        self.cache_dir = cache_dir
        
        # Core components
        self.model = None
        self.places = []  # sites -> places değişti
        self.embeddings = None
        self.index = None
        
        # Cache files
        self.embeddings_file = os.path.join(cache_dir, "antep_embeddings.pkl")
        self.index_file = os.path.join(cache_dir, "antep_faiss.index")
        self.places_file = os.path.join(cache_dir, "antep_places.pkl")
        
        # Create cache directory
        os.makedirs(cache_dir, exist_ok=True)
        
        print(f"🏛️ Gaziantep RAG System initialized")
        print(f"📁 Data: {data_path}")
        print(f"🧠 Model: {model_name}")
        print(f"💾 Cache: {cache_dir}")
    
    def setup(self) -> bool:
        """RAG sistemini kur"""
        
        try:
            # 1. Load model
            print("🧠 Loading embedding model...")
            self.model = SentenceTransformer(self.model_name)
            print(f"✅ Model loaded: {self.model.get_sentence_embedding_dimension()} dim")
            
            # 2. Load data
            if not self._load_data():
                return False
            
            # 3. Load or create embeddings
            if not self._load_or_create_embeddings():
                return False
            
            # 4. Setup FAISS index
            if not self._setup_faiss_index():
                return False
            
            print("✅ Gaziantep RAG system ready!")
            return True
            
        except Exception as e:
            print(f"❌ Setup error: {e}")
            return False
    
    def _load_data(self) -> bool:
        """Gaziantep turizm verilerini yükle"""
        
        try:
            print(f"📖 Loading Gaziantep tourism data...")
            
            with open(self.data_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # JSON yapısına göre places listesini al
            self.places = data.get('places', [])
            self.metadata = data.get('metadata', {})
            
            print(f"✅ Loaded {len(self.places)} Gaziantep places")
            
            # Kategorileri göster
            categories = {}
            for place in self.places:
                cat = place.get('category', 'unknown')
                categories[cat] = categories.get(cat, 0) + 1
            print(f"📊 Categories: {categories}")
            
            # Cache places
            with open(self.places_file, 'wb') as f:
                pickle.dump(self.places, f)
            
            return True
            
        except Exception as e:
            print(f"❌ Data loading error: {e}")
            return False
    
    def _load_or_create_embeddings(self) -> bool:
        """Embeddings'i yükle veya oluştur"""
        
        # Cache'den yüklemeyi dene
        if os.path.exists(self.embeddings_file):
            try:
                print("💾 Loading cached embeddings...")
                with open(self.embeddings_file, 'rb') as f:
                    self.embeddings = pickle.load(f)
                
                if len(self.embeddings) == len(self.places):
                    print(f"✅ Loaded {len(self.embeddings)} cached embeddings")
                    return True
                else:
                    print("⚠️ Cache size mismatch, recreating...")
            except Exception as e:
                print(f"⚠️ Cache loading failed: {e}, recreating...")
        
        # Embeddings'i oluştur
        return self._create_embeddings()
    
    def _create_embeddings(self) -> bool:
        """Embeddings'i oluştur"""
        
        try:
            print(f"🏗️ Creating embeddings for {len(self.places)} places...")
            
            # Document texts hazırla
            documents = []
            for place in self.places:
                doc_text = self._prepare_document(place)
                documents.append(doc_text)
            
            print("🧠 Encoding documents...")
            
            # Batch encoding
            self.embeddings = self.model.encode(
                documents,
                batch_size=32,
                show_progress_bar=True,
                convert_to_numpy=True
            )
            
            print(f"✅ Created embeddings: {self.embeddings.shape}")
            
            # Cache'e kaydet
            with open(self.embeddings_file, 'wb') as f:
                pickle.dump(self.embeddings, f)
            
            print("💾 Embeddings cached")
            return True
            
        except Exception as e:
            print(f"❌ Embedding creation error: {e}")
            return False
    
    def _prepare_document(self, place: Dict) -> str:
        """Place'i document text'e çevir - Gaziantep özelleştirilmiş"""
        
        # search_text varsa öncelik ver
        if 'search_text' in place and place['search_text']:
            return place['search_text'].lower()
        
        # Manual combination - Gaziantep için özelleştirilmiş
        parts = [
            place.get('name', ''),
            place.get('description', ''),
            place.get('category', ''),
            place.get('subcategory', ''),
        ]
        
        # Location bilgilerini ekle
        if 'location' in place:
            location = place['location']
            if isinstance(location, dict):
                parts.append(location.get('district', ''))
                parts.append(location.get('address', ''))
        
        # Features ekle
        if 'features' in place:
            features = place['features']
            if isinstance(features, list):
                parts.extend(features)
        
        # Ingredients ekle (yemekler için)
        if 'ingredients' in place:
            ingredients = place['ingredients']
            if isinstance(ingredients, list):
                parts.extend(ingredients)
        
        # Main ingredients ekle
        if 'main_ingredients' in place:
            main_ingredients = place['main_ingredients']
            if isinstance(main_ingredients, list):
                parts.extend(main_ingredients)
        
        # Specialties ekle (restoranlar için)
        if 'specialties' in place:
            specialties = place['specialties']
            if isinstance(specialties, list):
                parts.extend(specialties)
        
        # Price range'i text olarak ekle
        if 'price_range' in place:
            parts.append(place['price_range'])
        
        # Amenities ekle (oteller için)
        if 'amenities' in place:
            amenities = place['amenities']
            if isinstance(amenities, list):
                parts.extend(amenities)
        
        # Highlights ekle
        if 'highlights' in place:
            highlights = place['highlights']
            if isinstance(highlights, list):
                parts.extend(highlights)
        
        return ' '.join(filter(None, parts)).lower()
    
    def _setup_faiss_index(self) -> bool:
        """FAISS index'i kur"""
        
        try:
            # Cache'den yüklemeyi dene
            if os.path.exists(self.index_file):
                print("💾 Loading cached FAISS index...")
                self.index = faiss.read_index(self.index_file)
                print(f"✅ Loaded FAISS index: {self.index.ntotal} vectors")
                return True
            
            # Index oluştur
            print("🔍 Creating FAISS index...")
            
            embedding_dim = self.embeddings.shape[1]
            
            # Cosine similarity için normalize et
            faiss.normalize_L2(self.embeddings)
            
            # Inner product index (normalized vectors için cosine similarity)
            self.index = faiss.IndexFlatIP(embedding_dim)
            
            # Embeddings'i ekle
            self.index.add(self.embeddings)
            
            print(f"✅ FAISS index created: {self.index.ntotal} vectors")
            
            # Cache'e kaydet
            faiss.write_index(self.index, self.index_file)
            print("💾 FAISS index cached")
            
            return True
            
        except Exception as e:
            print(f"❌ FAISS setup error: {e}")
            return False
    
    def search(self, query: str, top_k: int = 15, threshold: float = 0.1, 
               category_filter: Optional[str] = None) -> List[Dict]:
        """Ana arama fonksiyonu - kategori filtresi eklendi"""
        
        if not self.model or not self.index:
            print("❌ RAG system not initialized!")
            return []
        
        try:
            print(f"🔍 Searching: '{query}' (top-{top_k})")
            if category_filter:
                print(f"🏷️ Category filter: {category_filter}")
            
            # Query embedding
            query_embedding = self.model.encode([query], convert_to_numpy=True)
            faiss.normalize_L2(query_embedding)  # Normalize for cosine similarity
            
            # FAISS search - daha fazla sonuç al ki filtreleyebilelim
            search_k = min(top_k * 3, len(self.places))
            similarities, indices = self.index.search(query_embedding, search_k)
            
            # Results formatla ve filtrele
            results = []
            for i, (similarity, idx) in enumerate(zip(similarities[0], indices[0])):
                
                if similarity < threshold:
                    continue
                
                place = self.places[idx]
                
                # Category filtresi uygula
                if category_filter and place.get('category') != category_filter:
                    continue
                
                result = {
                    'place': place,  # site -> place değişti
                    'similarity': float(similarity),
                    'rank': len(results) + 1
                }
                results.append(result)
                
                print(f"📊 {len(results)}. {place['name']} ({place.get('category', 'N/A')}) - Similarity: {similarity:.3f}")
                
                # İstenen sayıya ulaştık mı?
                if len(results) >= top_k:
                    break
            
            print(f"✅ Found {len(results)} results above threshold")
            return results
            
        except Exception as e:
            print(f"❌ Search error: {e}")
            return []
    
    def get_categories(self) -> List[str]:
        """Mevcut kategorileri listele"""
        categories = set()
        for place in self.places:
            if 'category' in place:
                categories.add(place['category'])
        return sorted(list(categories))
    
    def search_by_category(self, category: str, top_k: int = 10) -> List[Dict]:
        """Kategoriye göre direkt arama"""
        category_places = [place for place in self.places if place.get('category') == category]
        
        results = []
        for i, place in enumerate(category_places[:top_k]):
            result = {
                'place': place,
                'similarity': 1.0,  # Exact match
                'rank': i + 1
            }
            results.append(result)
        
        print(f"✅ Found {len(results)} places in category '{category}'")
        return results
    
    def format_for_gemini(self, results: List[Dict], max_context: int = 3000) -> str:
        """Sonuçları Gemini için formatla - Gaziantep özelleştirilmiş"""
        
        if not results:
            return "Aradığınız kriterlere uygun yer bulunamadı."
        
        context_parts = []
        total_length = 0
        
        for i, result in enumerate(results, 1):
            place = result['place']
            similarity = result['similarity']
            
            # Kategori ikonları
            category_icon = {
                'historic_places': '🏛️',
                'museums': '🏛️',
                'religious_sites': '🕌',
                'shopping': '🛍️',
                'food_drinks': '🍽️',
                'restaurants': '🏪',
                'accommodation': '🏨',
                'local_products': '🎁',
                'festivals': '🎉',
                'nature_parks': '🌳'
            }.get(place.get('category'), '📍')
            
            # Location bilgisi
            location_info = ""
            if 'location' in place:
                location = place['location']
                if isinstance(location, dict):
                    district = location.get('district', '')
                    if district:
                        location_info = f"({district})"
            
            # Özel alanlar (kategori bazlı)
            extra_info = ""
            if place.get('category') == 'food_drinks':
                price = place.get('price_range', '')
                if price:
                    extra_info = f"\n   💰 Fiyat: {price}"
            elif place.get('category') == 'restaurants':
                specialties = place.get('specialties', [])
                if specialties and isinstance(specialties, list):
                    extra_info = f"\n   🍽️ Uzmanlik: {', '.join(specialties[:3])}"
            elif place.get('category') == 'accommodation':
                stars = place.get('star_rating', '')
                if stars:
                    extra_info = f"\n   ⭐ {stars} yıldız"
            
            formatted_place = f"""
{i}. {category_icon} **{place.get('name', 'N/A')}** {location_info}
   📖 {place.get('description', 'N/A')[:250]}
   🏷️ {place.get('category', 'N/A')}{extra_info}
   🔎 Benzerlik: {similarity:.1%}
"""
            
            if total_length + len(formatted_place) > max_context:
                break
            
            context_parts.append(formatted_place.strip())
            total_length += len(formatted_place)
        
        return "\n\n".join(context_parts)
    
    def get_stats(self) -> Dict:
        """Sistem istatistikleri"""
        
        # Kategori istatistikleri
        categories_count = {}
        for place in self.places:
            category = place.get('category', 'unknown')
            categories_count[category] = categories_count.get(category, 0) + 1
        
        return {
            'places_count': len(self.places),  # sites_count -> places_count
            'categories': categories_count,
            'embedding_shape': self.embeddings.shape if self.embeddings is not None else None,
            'index_vectors': self.index.ntotal if self.index else 0,
            'model_name': self.model_name,
            'cache_dir': self.cache_dir
        }

# Test fonksiyonu
def test_gaziantep_rag():
    """Gaziantep RAG'ı test et"""
    
    print("🧪 Gaziantep RAG Test başlıyor...")
    
    # RAG sistemi oluştur
    rag = GaziantepRAGSystem()
    
    # Setup
    if not rag.setup():
        print("❌ Setup failed!")
        return
    
    # Stats göster
    stats = rag.get_stats()
    print(f"\n📊 Stats: {stats}")
    
    # Kategorileri listele
    categories = rag.get_categories()
    print(f"\n🏷️ Available categories: {categories}")
    
    # Test queries - Gaziantep özelleştirilmiş
    test_queries = [
        "Antep kebabı nerede yenir",
        "baklava tarihi",
        "tarihi camiler", 
        "lüks oteller",
        "geleneksel çarşı",
        "künefe",
        "fıstık ürünleri",
        "müze gezisi",
        "konaklama önerileri",
        "yerel lezzetler"
    ]
    
    print(f"\n🔍 Testing {len(test_queries)} queries...")
    
    for query in test_queries:
        print(f"\n{'='*60}")
        print(f"Query: {query}")
        print('='*60)
        
        results = rag.search(query, top_k=5, threshold=0.1)
        
        if results:
            context = rag.format_for_gemini(results)
            print(f"\n📄 Gemini Context Preview:")
            print(context[:600] + "..." if len(context) > 600 else context)
        else:
            print("❌ No results found")
    
    # Kategori bazlı test
    print(f"\n{'='*60}")
    print("Category-based search test")
    print('='*60)
    
    for category in categories[:3]:
        print(f"\n🏷️ Category: {category}")
        results = rag.search_by_category(category, top_k=3)
        for result in results:
            place = result['place']
            print(f"  - {place['name']}")

if __name__ == "__main__":
    test_gaziantep_rag()