import os
from llama_index.core import StorageContext
from llama_index.embeddings.huggingface import HuggingFaceEmbedding

# Base directory containing one folder per legal category
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.abspath(os.path.join(CURRENT_DIR, "../../databases/llama_index_dbs"))

# Dictionary to hold storage contexts by legal category
storage_contexts_by_category = {}

# Shared embedding model for all categories
# Load model name from env
model_name = os.getenv("EMBEDDING_MODEL_NAME", "all-MiniLM-L6-v2")
embed_model = HuggingFaceEmbedding(model_name=model_name)

# Walk through category directories
for category in os.listdir(BASE_DIR):
    category_path = os.path.join(BASE_DIR, category)
    if os.path.isdir(category_path):
        storage_contexts_by_category[category] = StorageContext.from_defaults(persist_dir=category_path)

def get_data_sources():
    """
    Returns:
        - storage_contexts_by_category: dict like {'law_of_crimes': StorageContext(...) }
        - embed_model: initialized embedding model
    """
    return storage_contexts_by_category, embed_model
