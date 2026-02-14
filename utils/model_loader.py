"""
Model Loader - Loads models from local directory or downloads from HuggingFace
"""

import os
import pickle
import joblib
from pathlib import Path
from huggingface_hub import hf_hub_download
from sentence_transformers import SentenceTransformer
from config.settings import HUGGINGFACE_REPO, MODEL_FILES, EMBEDDING_MODEL

class ModelLoader:
    def __init__(self):
        self.models_dir = Path("models")
        self.models_dir.mkdir(exist_ok=True)
        self.models = {}
        
        # Check for local models in parent directory
        parent_models_improved = Path(__file__).parent.parent.parent / "models_improved"
        parent_models = Path(__file__).parent.parent.parent / "models"
        
        if parent_models_improved.exists():
            self.local_models_path = parent_models_improved
            print(f"✅ Found local models at: {self.local_models_path}")
        elif parent_models.exists():
            self.local_models_path = parent_models
            print(f"✅ Found local models at: {self.local_models_path}")
        else:
            self.local_models_path = None
            print(f"ℹ️ No local models found, will download from HuggingFace")
        
    def download_models(self):
        """Load models from local directory or download from HuggingFace"""
        
        # Try loading from local directory first
        if self.local_models_path and self.local_models_path.exists():
            print(f"📂 Loading models from local directory: {self.local_models_path}")
            for model_file in MODEL_FILES:
                try:
                    local_path = self.local_models_path / model_file
                    if local_path.exists():
                        # Try joblib first (better for scikit-learn), then pickle
                        try:
                            self.models[model_file.replace('.pkl', '')] = joblib.load(local_path)
                            print(f"✅ Loaded (joblib): {model_file}")
                        except:
                            with open(local_path, 'rb') as f:
                                self.models[model_file.replace('.pkl', '')] = pickle.load(f)
                            print(f"✅ Loaded (pickle): {model_file}")
                    else:
                        print(f"⚠️ File not found locally: {model_file}")
                except Exception as e:
                    print(f"❌ Error loading {model_file}: {e}")
                    raise
        else:
            # Download from HuggingFace
            print(f"📥 Downloading models from {HUGGINGFACE_REPO}...")
            for model_file in MODEL_FILES:
                try:
                    local_path = hf_hub_download(
                        repo_id=HUGGINGFACE_REPO,
                        filename=model_file,
                        cache_dir=str(self.models_dir)
                    )
                    print(f"✅ Downloaded: {model_file}")
                    
                    # Load the model
                    with open(local_path, 'rb') as f:
                        self.models[model_file.replace('.pkl', '')] = pickle.load(f)
                        
                except Exception as e:
                    print(f"❌ Error downloading {model_file}: {e}")
                    raise
        
        # Load Sentence-BERT for duplicate detection
        print(f"📥 Loading Sentence-BERT model: {EMBEDDING_MODEL}...")
        self.models['sentence_bert'] = SentenceTransformer(EMBEDDING_MODEL)
        print("✅ Sentence-BERT loaded")
        
        print(f"✅ All models loaded successfully!")
        return self.models
    
    def get_models(self):
        """Get loaded models"""
        if not self.models:
            self.download_models()
        return self.models
