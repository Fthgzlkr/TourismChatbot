import json
import pickle
import numpy as np
from typing import List, Dict, Tuple, Optional
from sentence_transformers import SentenceTransformer
import faiss
import os

class SimpleRAGSystem:
    """
    Basit ama güvenilir RAG sistemi.
    FAISS + Sentence Transformers kullanır.
    """
    
    def __init__(self, 
                 data_path: str = "./data/unesco_cleaned_data.json",
                 model_name: str = "paraphrase-multilingual-MiniLM-L12-v2",
                 cache_dir: str = "./rag_cache"):
        
        self.data_path = data_path
        self.model_name = model_name
        self.cache_dir = cache_dir
        
        # Core components
        self.model = None
        self.sites = []
        self.embeddings = None
        self.index = None
        
        # Cache files
        self.embeddings_file = os.path.join(cache_dir, "embeddings.pkl")
        self.index_file = os.path.join(cache_dir, "faiss.index")
        self.sites_file = os.path.join(cache_dir, "sites.pkl")
        
        # Create cache directory
        os.makedirs(cache_dir, exist_ok=True)
        
        print(f"🤖 Simple RAG System initialized")
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
            
            print("✅ RAG system ready!")
            return True
            
        except Exception as e:
            print(f"❌ Setup error: {e}")
            return False
    
    def _load_data(self) -> bool:
        """UNESCO data'yı yükle"""
        
        try:
            print(f"📖 Loading UNESCO data...")
            
            with open(self.data_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.sites = data.get('sites', [])
            print(f"✅ Loaded {len(self.sites)} UNESCO sites")
            
            # Cache sites
            with open(self.sites_file, 'wb') as f:
                pickle.dump(self.sites, f)
            
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
                
                if len(self.embeddings) == len(self.sites):
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
            print(f"🏗️ Creating embeddings for {len(self.sites)} sites...")
            
            # Document texts hazırla
            documents = []
            for site in self.sites:
                doc_text = self._prepare_document(site)
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
    
    def _prepare_document(self, site: Dict) -> str:
        """Site'ı document text'e çevir"""
        
        # Öncelik sırası: search_text > manual combination
        if 'search_text' in site and site['search_text']:
            return site['search_text']
        
        # Manual combination
        parts = [
            site.get('name', ''),
            site.get('country', ''),
            site.get('category', ''),
            site.get('description', ''),
        ]
        
        # Keywords ekle
        if 'metadata' in site and 'keywords' in site['metadata']:
            keywords = site['metadata']['keywords']
            if keywords:
                parts.append(' '.join(keywords))
        
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
    
    def search(self, query: str, top_k: int = 20, threshold: float = 0.1) -> List[Dict]:
        """Ana arama fonksiyonu"""
        
        if not self.model or not self.index:
            print("❌ RAG system not initialized!")
            return []
        
        try:
            print(f"🔍 Searching: '{query}' (top-{top_k})")
            
            # Query embedding
            query_embedding = self.model.encode([query], convert_to_numpy=True)
            faiss.normalize_L2(query_embedding)  # Normalize for cosine similarity
            
            # FAISS search
            similarities, indices = self.index.search(query_embedding, top_k)
            
            # Results formatla
            results = []
            for i, (similarity, idx) in enumerate(zip(similarities[0], indices[0])):
                
                if similarity < threshold:
                    print(f"⚠️ Threshold altı: {similarity:.3f} < {threshold}")
                    continue
                
                site = self.sites[idx]
                result = {
                    'site': site,
                    'similarity': float(similarity),
                    'rank': i + 1
                }
                results.append(result)
                
                print(f"📊 {i+1}. {site['name']} - Similarity: {similarity:.3f}")
            
            print(f"✅ Found {len(results)} results above threshold")
            return results
            
        except Exception as e:
            print(f"❌ Search error: {e}")
            return []
    
    def format_for_gemini(self, results: List[Dict], max_context: int = 3000) -> str:
        """Sonuçları Gemini için formatla"""
        
        if not results:
            return "İlgili UNESCO sitesi bulunamadı."
        
        context_parts = []
        total_length = 0
        
        for i, result in enumerate(results, 1):
            site = result['site']
            similarity = result['similarity']
            
            formatted_site = f"""
{i}. 📍 **{site.get('name', 'N/A')}** ({site.get('country', 'N/A')}, {site.get('year', 'N/A')})
   🏷️ {site.get('category', 'N/A')} | {site.get('region', 'N/A')}
   📖 {site.get('description', 'N/A')[:300]}
   🔎 Benzerlik: {similarity:.1%}
"""
            
            if total_length + len(formatted_site) > max_context:
                break
            
            context_parts.append(formatted_site.strip())
            total_length += len(formatted_site)
        
        return "\n\n".join(context_parts)
    
    def get_stats(self) -> Dict:
        """Sistem istatistikleri"""
        
        return {
            'sites_count': len(self.sites) if self.sites else 0,
            'embedding_shape': self.embeddings.shape if self.embeddings is not None else None,
            'index_vectors': self.index.ntotal if self.index else 0,
            'model_name': self.model_name,
            'cache_dir': self.cache_dir
        }

# Test fonksiyonu
def test_simple_rag():
    """Simple RAG'ı test et"""
    
    print("🧪 Simple RAG Test başlıyor...")
    
    # RAG sistemi oluştur
    rag = SimpleRAGSystem()
    
    # Setup
    if not rag.setup():
        print("❌ Setup failed!")
        return
    
    # Stats göster
    stats = rag.get_stats()
    print(f"\n📊 Stats: {stats}")
    
    # Test queries
    test_queries = [
        "Turkey UNESCO sites",
        "Türkiye UNESCO siteleri", 
        "France cultural heritage",
        "ancient castles",
        "national parks",
        "Istanbul Turkey",
        "doğal miras"
    ]
    
    print(f"\n🔍 Testing {len(test_queries)} queries...")
    
    for query in test_queries:
        print(f"\n{'='*60}")
        print(f"Query: {query}")
        print('='*60)
        
        results = rag.search(query, top_k=15, threshold=0.1)
        
        if results:
            context = rag.format_for_gemini(results)
            print(f"\n📄 Gemini Context Preview:")
            print(context[:500] + "..." if len(context) > 500 else context)
        else:
            print("❌ No results found")

if __name__ == "__main__":
    test_simple_rag()