from llama_index.core import StorageContext,load_index_from_storage
from llama_index.core.retrievers import AutoMergingRetriever
from llama_index.embeddings.huggingface import HuggingFaceEmbedding


storage_context_vector = StorageContext.from_defaults(persist_dir='database/llamaindexDbs/all/vectorstoreall')
storage_context = StorageContext.from_defaults(persist_dir='database/llamaindexDbs/all/docstoreall')
embed_model = HuggingFaceEmbedding(model_name="all-MiniLM-L6-v2")

def get_data_sources_pg_num():
    return storage_context_vector,storage_context,embed_model