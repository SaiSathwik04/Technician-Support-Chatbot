from rag_system import RAGSystem

if __name__ == "__main__":
    rag = RAGSystem(
        vector_store_path="knowledge_base/vector_store",
        documents_path="knowledge_base/technician_manuals"
    )
    success = rag.index_documents()
    print("Indexing successful!" if success else "Indexing failed.")

