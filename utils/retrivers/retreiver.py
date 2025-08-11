from llama_index.core import StorageContext, load_index_from_storage
from llama_index.embeddings.huggingface import HuggingFaceEmbedding

class AutomergingRetriverInit:
    def __init__(self, storage_contexts_by_category: dict, embed_model):
        """
        Args:
            storage_contexts_by_category: Dict of category -> StorageContext
            embed_model: Preloaded HuggingFaceEmbedding
        """
        self.storage_contexts = storage_contexts_by_category
        self.embed_model = embed_model

    def automerging_retrival_pipeline(self, query_str: str, category: str):
        """
        Retrieve relevant documents from the correct category index.
        Args:
            query_str: User query
            category: e.g., 'law_of_crimes'
        Returns:
            List of top matching text chunks
        """
        if category not in self.storage_contexts:
            raise ValueError(f"Category '{category}' not found in loaded storage contexts.")

        storage_context = self.storage_contexts[category]

        # Load index for the selected category
        base_index = load_index_from_storage(storage_context, embed_model=self.embed_model)

        # Run retrieval
        base_retriever = base_index.as_retriever(similarity_top_k=10)
        base_nodes = base_retriever.retrieve(query_str)

        return base_nodes

