from llama_index.core import StorageContext,load_index_from_storage
from llama_index.core.retrievers import AutoMergingRetriever
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
# from llama_index.core.response.notebook_utils import display_source_node
from utils.retrivers.retriver_init_pg_num import *


class AutomergingRetriverPgNum():
    storage_context = None
    storage_context_vector = None
    embed_model = None

    def __init__(self,storage_context,storage_context_vector,embed_model):
        self.storage_context_vector = storage_context_vector
        self.storage_context = storage_context
        self.embed_model = embed_model
        
    

    def parse_delimited(self,text):
            if "=== METADATA START ===" in text and "=== METADATA END ===" in text:
                try:
                    parts = text.split("=== METADATA END ===", 1)
                    meta_block = parts[0]
                    content = parts[1].strip()

                    meta_lines = meta_block.splitlines()[1:]  # Skip "=== METADATA START ==="
                    metadata = {}
                    for line in meta_lines:
                        if ": " in line:
                            key, value = line.split(": ", 1)
                            metadata[key.strip().lower()] = value.strip()
                    return metadata
                except Exception as e:
                    print(f"[!] Failed to parse metadata block: {e}")
                    return {"content": text}
            else:
                return {"content": text}

    def automerging_retrival_pipeline(self, query_str):

        base_index = load_index_from_storage(storage_context_vector,embed_model=embed_model)

        base_retriever = base_index.as_retriever(similarity_top_k=6)
        retriever = AutoMergingRetriever(base_retriever, storage_context, verbose=True)


        nodes = retriever.retrieve(query_str)
        base_nodes = base_retriever.retrieve(query_str)


        base_texts = [node.text for node in base_nodes]
        metadata_list = []
        i = 0
        for text in base_texts:
            if i <= 2:
             meta = self.parse_delimited(text)
             metadata_list.append(meta)
             i = i +1
            
        return metadata_list
    


