import csv
import json
import re
from html import unescape
import os

class UNESCODataCleaner:
    def __init__(self):
        self.processed_sites = []
        self.statistics = {
            "total_processed": 0,
            "errors": [],
            "countries": set(),
            "categories": {},
            "regions": {},
            "year_range": {"min": 9999, "max": 0}
        }
    
    def clean_html_text(self, text):
        """HTML tag'leri ve entities'leri temizle - tüm text alanları için"""
        if not text:
            return ""
        
        # HTML tag'leri kaldır
        text = re.sub(r'<[^>]+>', ' ', text)
        
        # HTML entities'leri decode et (&amp; → &, &nbsp; → space, etc.)
        text = unescape(text)
        
        # Çoklu boşlukları tek boşluğa çevir
        text = re.sub(r'\s+', ' ', text)
        
        # Başlangıç/bitiş boşluklarını kaldır
        text = text.strip()
        
        return text
    
    def validate_record(self, row, row_number):
        """Kayıt validasyonu"""
        errors = []
        
        # Required fields check (HTML temizlendikten sonra kontrol et)
        clean_name = self.clean_html_text(row.get('Name', '')).strip()
        if not clean_name:
            errors.append(f"Row {row_number}: Missing name")
        
        if not row.get('Country name', '').strip():
            errors.append(f"Row {row_number}: Missing country")
        
        # Date validation
        try:
            year = int(row.get('date_inscribed', 0))
            if year < 1970 or year > 2024:
                errors.append(f"Row {row_number}: Invalid year {year}")
        except (ValueError, TypeError):
            errors.append(f"Row {row_number}: Invalid date format")
        
        # Category validation
        valid_categories = ['Cultural', 'Natural', 'Mixed']
        category = row.get('category_long', '').strip()
        if category not in valid_categories:
            errors.append(f"Row {row_number}: Invalid category '{category}'")
        
        return errors
    
    def extract_keywords(self, description):
        """Description'dan önemli keywords çıkar"""
        heritage_keywords = [
            # Architectural
            'castle', 'cathedral', 'temple', 'monastery', 'palace', 'church', 'mosque',
            'fort', 'fortress', 'citadel', 'tower', 'bridge', 'architecture',
            
            # Historical periods
            'ancient', 'medieval', 'prehistoric', 'roman', 'byzantine', 'gothic',
            'renaissance', 'baroque', 'neolithic', 'bronze age',
            
            # Natural features
            'national park', 'wildlife', 'ecosystem', 'biodiversity', 'forest',
            'mountain', 'volcano', 'lake', 'river', 'cave', 'coral reef',
            'rainforest', 'desert', 'wetland', 'marine',
            
            # Archaeological
            'archaeological', 'excavation', 'ruins', 'settlement', 'burial',
            'artifacts', 'inscription', 'petroglyph', 'fossil',
            
            # Cultural
            'cultural landscape', 'traditional', 'indigenous', 'historic',
            'pilgrimage', 'sacred', 'religious', 'ceremonial',

            #Religional
            'Christ','Jesus' ,'Muhammed' ,'Moses' 'Muslim' ,'Buddhist'
        ]
        
        found_keywords = []
        desc_lower = description.lower()
        
        for keyword in heritage_keywords:
            if keyword in desc_lower:
                found_keywords.append(keyword)
        
        return found_keywords
    
    def create_search_text(self, site_data):
        """RAG için optimize edilmiş search text oluştur"""
        search_parts = [
            site_data['name'],
            site_data['country'],
            site_data['category'],
            site_data['region'],
            site_data['description']
        ]
        
        # Keywords ekle
        keywords = self.extract_keywords(site_data['description'])
        search_parts.extend(keywords)
        
        # Birleştir ve normalize et
        search_text = ' '.join(filter(None, search_parts))
        return search_text.lower()
    
    def process_csv_file(self, csv_file_path):
        """Ana CSV processing fonksiyonu"""
        print(f"🔄 Processing file: {csv_file_path}")
        
        if not os.path.exists(csv_file_path):
            print(f"❌ File not found: {csv_file_path}")
            return False
        
        try:
            with open(csv_file_path, 'r', encoding='utf-8') as file:
                # CSV sniffer ile delimiter detect et
                sample = file.read(1024)
                file.seek(0)
                sniffer = csv.Sniffer()
                delimiter = sniffer.sniff(sample).delimiter
                
                reader = csv.DictReader(file, delimiter=delimiter)
                
                for row_number, row in enumerate(reader, start=2):  # Start from 2 (header = 1)
                    self.process_single_record(row, row_number)
            
            print(f"✅ Processing completed!")
            self.print_statistics()
            return True
            
        except Exception as e:
            print(f"❌ Error processing file: {str(e)}")
            return False
    
    def process_single_record(self, row, row_number):
        """Tek bir kaydı işle"""
        # Validation
        validation_errors = self.validate_record(row, row_number)
        if validation_errors:
            self.statistics["errors"].extend(validation_errors)
            return
        
        try:
            # Clean and structure data - NAME ve DESCRIPTION'ı temizle
            site = {
                "id": f"unesco_{row_number:04d}",
                "name": self.clean_html_text(row['Name']),  # ← Name'i de temizle
                "description": self.clean_html_text(row['short_description']),  # ← Fonksiyon adı değişti
                "country": row['Country name'].strip(),
                "year": int(row['date_inscribed']),
                "category": row['category_long'].strip(),
                "region": row['Region'].strip(),
            }
            
            # Search text oluştur
            site["search_text"] = self.create_search_text(site)
            
            # Metadata ekle
            site["metadata"] = {
                "word_count": len(site["description"].split()),
                "keywords": self.extract_keywords(site["description"]),
                "source_row": row_number
            }
            
            self.processed_sites.append(site)
            
            # Statistics güncelle
            self.update_statistics(site)
            
        except Exception as e:
            error_msg = f"Row {row_number}: Processing error - {str(e)}"
            self.statistics["errors"].append(error_msg)
    
    def update_statistics(self, site):
        """İstatistikleri güncelle"""
        stats = self.statistics
        stats["total_processed"] += 1
        stats["countries"].add(site["country"])
        
        # Category count
        category = site["category"]
        stats["categories"][category] = stats["categories"].get(category, 0) + 1
        
        # Region count
        region = site["region"]
        stats["regions"][region] = stats["regions"].get(region, 0) + 1
        
        # Year range
        year = site["year"]
        stats["year_range"]["min"] = min(stats["year_range"]["min"], year)
        stats["year_range"]["max"] = max(stats["year_range"]["max"], year)
    
    def print_statistics(self):
        """İstatistikleri yazdır"""
        stats = self.statistics
        print(f"\n📊 PROCESSING STATISTICS:")
        print(f"✅ Total processed: {stats['total_processed']}")
        print(f"🌍 Countries: {len(stats['countries'])}")
        print(f"📅 Year range: {stats['year_range']['min']} - {stats['year_range']['max']}")
        
        print(f"\n📂 Categories:")
        for category, count in stats["categories"].items():
            print(f"  - {category}: {count}")
        
        print(f"\n🌎 Regions:")
        for region, count in stats["regions"].items():
            print(f"  - {region}: {count}")
        
        if stats["errors"]:
            print(f"\n⚠️ Errors ({len(stats['errors'])}):")
            for error in stats["errors"][:5]:  # Show first 5 errors
                print(f"  - {error}")
            if len(stats["errors"]) > 5:
                print(f"  ... and {len(stats['errors']) - 5} more errors")
    
    def save_to_json(self, output_file="unesco_cleaned_data.json"):
        """Temizlenmiş veriyi JSON'a kaydet"""
        final_data = {
            "metadata": {
                "total_sites": len(self.processed_sites),
                "countries": list(self.statistics["countries"]),
                "categories": self.statistics["categories"],
                "regions": self.statistics["regions"],
                "year_range": self.statistics["year_range"],
                "processing_errors": len(self.statistics["errors"])
            },
            "sites": self.processed_sites
        }
        
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(final_data, f, ensure_ascii=False, indent=2)
            
            print(f"💾 Data saved to: {output_file}")
            print(f"📁 File size: {os.path.getsize(output_file) / 1024:.1f} KB")
            return True
            
        except Exception as e:
            print(f"❌ Error saving file: {str(e)}")
            return False
    
    def preview_sample_data(self, count=3):
        """İşlenmiş veriden sample göster"""
        print(f"\n🔍 SAMPLE PROCESSED DATA ({count} records):")
        
        for i, site in enumerate(self.processed_sites[:count]):
            print(f"\n--- Record {i+1} ---")
            print(f"ID: {site['id']}")
            print(f"Name: {site['name']}")
            print(f"Country: {site['country']} ({site['region']})")
            print(f"Category: {site['category']} ({site['year']})")
            print(f"Description: {site['description'][:100]}...")
            print(f"Keywords: {', '.join(site['metadata']['keywords'][:5])}")
    
    def analyze_html_content(self, csv_file_path, sample_size=10):
        """CSV'deki HTML content'i analiz et"""
        print(f"🔍 Analyzing HTML content in: {csv_file_path}")
        
        try:
            with open(csv_file_path, 'r', encoding='utf-8') as file:
                sample = file.read(1024)
                file.seek(0)
                sniffer = csv.Sniffer()
                delimiter = sniffer.sniff(sample).delimiter
                
                reader = csv.DictReader(file, delimiter=delimiter)
                
                name_html_examples = []
                desc_html_examples = []
                
                for i, row in enumerate(reader):
                    if i >= sample_size:
                        break
                    
                    name = row.get('Name', '')
                    desc = row.get('short_description', '')
                    
                    # HTML tag'leri kontrol et
                    if re.search(r'<[^>]+>', name):
                        name_html_examples.append(f"Row {i+2}: {name[:100]}...")
                    
                    if re.search(r'<[^>]+>', desc):
                        desc_html_examples.append(f"Row {i+2}: {desc[:100]}...")
                
                print(f"\n📝 HTML in Name field ({len(name_html_examples)} found):")
                for example in name_html_examples[:3]:
                    print(f"  {example}")
                
                print(f"\n📝 HTML in Description field ({len(desc_html_examples)} found):")
                for example in desc_html_examples[:3]:
                    print(f"  {example}")
                
        except Exception as e:
            print(f"❌ Error analyzing file: {str(e)}")

# Usage example
if __name__ == "__main__":
    # Initialize cleaner
    cleaner = UNESCODataCleaner()
    
    # CSV dosya adını buraya yazın
    csv_file_path = "unesco_heritages.csv"
    
    # Önce HTML content'i analiz et (opsiyonel)
    cleaner.analyze_html_content(csv_file_path, sample_size=20)
    
    # Ana processing
    if cleaner.process_csv_file(csv_file_path):
        # Sample data göster
        cleaner.preview_sample_data(3)
        
        # JSON'a kaydet
        cleaner.save_to_json("unesco_cleaned_data.json")
        
        print(f"\n🎉 SUCCESS! Ready for RAG implementation.")
        print(f"📋 Next step: Test the JSON file and proceed to RAG setup.")
    else:
        print(f"\n❌ FAILED! Please check your CSV file and try again.")