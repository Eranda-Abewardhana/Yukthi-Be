import os
from llama_index.core import VectorStoreIndex, StorageContext, SimpleDirectoryReader
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.schema import Document

# Base directories
SOURCE_BASE_DIR = '../../data_sources'
PERSIST_BASE_DIR = '../../databases/llama_index_dbs'

# Embedding model
embed_model = HuggingFaceEmbedding(model_name="all-MiniLM-L6-v2")

# Parser that respects page boundaries
parser = SentenceSplitter(chunk_size=512, chunk_overlap=30)

# Loop through each category
for category in os.listdir(SOURCE_BASE_DIR):
    category_path = os.path.join(SOURCE_BASE_DIR, category)

    if os.path.isdir(category_path):
        print(f"\n📄 Indexing category: {category}")

        try:
            documents: list[Document] = SimpleDirectoryReader(
                input_dir=category_path,
                required_exts=[".pdf"]
            ).load_data()
        except ValueError as e:
            print(f"⚠️  Skipping {category}: {e}")
            continue

        all_nodes = []

        for doc in documents:
            # Set fallback file name
            file_name = doc.metadata.get("file_name") or os.path.basename(doc.metadata.get("source_path", "unknown.pdf"))
            doc.metadata["file_name"] = file_name

            # Get nodes from document
            doc_nodes = parser.get_nodes_from_documents([doc])

            for node in doc_nodes:
                # Inject metadata manually
                node.metadata["source_file"] = file_name

                # Extract page label or page number
                page = node.metadata.get("page_label") or node.metadata.get("page_number")
                try:
                    node.metadata["page_number"] = int(page)
                except:
                    node.metadata["page_number"] = str(page) if page else None

                # Optional: print for debug
                # print("✅ Node metadata:", node.metadata)

                all_nodes.append(node)

        # Persist index
        persist_path = os.path.join(PERSIST_BASE_DIR, category)
        os.makedirs(persist_path, exist_ok=True)

        storage_context = StorageContext.from_defaults()
        index = VectorStoreIndex(all_nodes, embed_model=embed_model, storage_context=storage_context)
        index.storage_context.persist(persist_path)

        print(f"✅ Finished indexing {len(all_nodes)} chunks → {persist_path}")
