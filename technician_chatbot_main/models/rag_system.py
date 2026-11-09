import logging
import os
import pickle
from pathlib import Path

import numpy as np

from sklearn.neighbors import NearestNeighbors

# Try to import optional dependencies
try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    print("Warning: sentence-transformers not available. RAG system will use fallback.")

logger = logging.getLogger(__name__)

class RAGSystem:
    """Retrieval Augmented Generation system for technician knowledge base"""

    def __init__(
        self,
        vector_store_path="knowledge_base/vector_store",
        documents_path="knowledge_base/technician_manuals",
    ):
        self.vector_store_path = vector_store_path
        self.documents_path = documents_path
        self.embedding_model = None
        self.index = None  # sklearn NearestNeighbors instance
        self.documents = []
        self.metadata = []
        self.embeddings = None  # Storing computed embeddings

        # Initialize directories
        os.makedirs(vector_store_path, exist_ok=True)
        os.makedirs(documents_path, exist_ok=True)

        # Initialize system
        self._initialize_system()

    def _initialize_system(self):
        """Initialize the RAG system"""
        try:
            if SENTENCE_TRANSFORMERS_AVAILABLE:
                self.embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
                logger.info("Embedding model loaded successfully")
                self._load_vector_store() or self._create_fallback_system()
            else:
                self._create_fallback_system()
                logger.warning("sentence-transformers not available. Using fallback RAG system")
        except Exception as e:
            logger.error(f"Error initializing RAG system: {str(e)}")
            self._create_fallback_system()

    def _create_sample_documents(self):
        """Create sample technical documents for the knowledge base"""
        sample_docs = {...}  # Your sample doc dict unchanged (omitted here for brevity)
        for filename, content in sample_docs.items():
            file_path = os.path.join(self.documents_path, filename)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
        logger.info(f"Created {len(sample_docs)} sample documents")

    def index_documents(self, documents_path=None):
        """Index all documents in the knowledge base using sklearn KNN"""
        if not SENTENCE_TRANSFORMERS_AVAILABLE:
            logger.warning("Cannot index documents: sentence-transformers missing")
            return False
        try:
            path = documents_path or self.documents_path
            self.documents = []
            self.metadata = []

            for file_path in Path(path).glob("*.txt"):
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()
                    chunks = self._split_document(content, file_path.name)
                    self.documents.extend(chunks)
                    for i, chunk in enumerate(chunks):
                        self.metadata.append({
                            "filename": file_path.name,
                            "chunk_id": i,
                            "chunk_size": len(chunk),
                            "source": str(file_path),
                        })
                    logger.info(f"Indexed {len(chunks)} chunks from {file_path.name}")
                except Exception as e:
                    logger.error(f"Error processing {file_path}: {str(e)}")
            if not self.documents:
                logger.warning("No documents found to index")
                return False

            logger.info(f"Creating embeddings for {len(self.documents)} document chunks...")
            self.embeddings = self.embedding_model.encode(self.documents, show_progress_bar=False)
            # Build sklearn NearestNeighbors index
            self.index = NearestNeighbors(n_neighbors=5, metric="cosine")
            self.index.fit(self.embeddings)
            # Save vector store
            self._save_vector_store()
            logger.info(f"Successfully indexed {len(self.documents)} document chunks with sklearn KNN")
            return True
        except Exception as e:
            logger.error(f"Error indexing documents: {str(e)}")
            return False

    def _split_document(self, content, filename):
        paragraphs = content.split("\n\n")
        chunks = []
        current_chunk = ""
        max_chunk_size = 800  # characters
        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if not paragraph:
                continue
            if len(current_chunk) + len(paragraph) < max_chunk_size:
                current_chunk += paragraph + "\n\n"
            else:
                if current_chunk.strip():
                    chunks.append(current_chunk.strip())
                current_chunk = paragraph + "\n\n"
        if current_chunk.strip():
            chunks.append(current_chunk.strip())
        chunks = [chunk for chunk in chunks if len(chunk) > 50]
        return chunks

    def retrieve_context(self, query, k=3):
        """Retrieve relevant context for a query using sklearn NN or fallback"""
        if self.index is not None and self.embeddings is not None:
            try:
                query_emb = self.embedding_model.encode([query])
                distances, indices = self.index.kneighbors(query_emb, n_neighbors=k)
                results = []
                for i, idx in enumerate(indices[0]):
                    doc_text = self.documents[idx]
                    doc_metadata = self.metadata[idx]
                    sim_score = 1 - distances[0][i]
                    results.append({
                        "text": doc_text,
                        "metadata": doc_metadata,
                        "similarity_score": sim_score,
                        "rank": i + 1
                    })
                return results
            except Exception as e:
                logger.error(f"Error in sklearn NN retrieval: {str(e)}")
                return self._fallback_retrieve_context(query, k)
        # Fallback if index or embedding not available
        return self._fallback_retrieve_context(query, k)

    def _fallback_retrieve_context(self, query, k=3):
        """Fallback: keyword matching retrieval"""
        if not self.documents:
            return []
        try:
            query_words = set(query.lower().split())
            scored_docs = []
            for i, doc in enumerate(self.documents):
                doc_words = set(doc.lower().split())
                overlap = len(query_words.intersection(doc_words))
                if overlap > 0:
                    score = overlap / len(query_words.union(doc_words))
                    scored_docs.append({
                        "text": doc,
                        "metadata": self.metadata[i] if i < len(self.metadata) else {"filename": "unknown"},
                        "similarity_score": score,
                        "rank": len(scored_docs) + 1,
                    })
            scored_docs.sort(key=lambda x: x["similarity_score"], reverse=True)
            return scored_docs[:k]
        except Exception as e:
            logger.error(f"Error in fallback context retrieval: {str(e)}")
            return []

    def get_context_string(self, query, k=3):
        """Get context as a formatted string for LLM consumption"""
        results = self.retrieve_context(query, k)
        if not results:
            return ""
        context_parts = []
        for result in results:
            context_parts.append(
                f"Source: {result['metadata']['filename']}\n{result['text']}"
            )
        return "\n\n---\n\n".join(context_parts)

    def _save_vector_store(self):
        """Save the sklearn vector store to disk (using pickle)"""
        try:
            data_path = os.path.join(self.vector_store_path, "vector_store_sklearn.pkl")
            with open(data_path, "wb") as f:
                pickle.dump({
                    "documents": self.documents,
                    "metadata": self.metadata,
                    "embeddings": self.embeddings,
                    "knn": self.index,
                }, f)
            logger.info("Vector store saved successfully (sklearn KNN)")
        except Exception as e:
            logger.error(f"Error saving vector store: {str(e)}")

    def _load_vector_store(self):
        """Load existing sklearn vector store from disk (using pickle)"""
        try:
            data_path = os.path.join(self.vector_store_path, "vector_store_sklearn.pkl")
            if not os.path.exists(data_path):
                return False
            with open(data_path, "rb") as f:
                data = pickle.load(f)
            self.documents = data["documents"]
            self.metadata = data["metadata"]
            self.embeddings = data["embeddings"]
            self.index = data["knn"]
            logger.info(f"Loaded sklearn KNN vector store with {len(self.documents)} documents")
            return True
        except Exception as e:
            logger.error(f"Error loading vector store: {str(e)}")
            return False

    def _create_fallback_system(self):
        """Create a minimal fallback system"""
        logger.warning("Creating fallback RAG system")
        self.documents = [
            "Motor troubleshooting: Check power supply, overload relays, and mechanical binding.",
            "Pump problems: Verify priming, check for cavitation, inspect impeller condition.",
            "Electrical safety: Always use lockout/tagout procedures before maintenance.",
            "HVAC maintenance: Replace filters regularly, clean coils, check refrigerant levels.",
            "Safety procedures: Use proper PPE, follow LOTO protocols, verify zero energy state.",
        ]
        self.metadata = [
            {"filename": "fallback_motor.txt", "chunk_id": 0, "source": "internal"},
            {"filename": "fallback_pump.txt", "chunk_id": 0, "source": "internal"},
            {"filename": "fallback_electrical.txt", "chunk_id": 0, "source": "internal"},
            {"filename": "fallback_hvac.txt", "chunk_id": 0, "source": "internal"},
            {"filename": "fallback_safety.txt", "chunk_id": 0, "source": "internal"},
        ]

    def get_statistics(self):
        """Get statistics about the knowledge base"""
        unique_files = set(meta.get("filename", "unknown") for meta in self.metadata)
        return {
            "total_documents": len(unique_files),
            "total_chunks": len(self.documents),
            "average_chunk_size": np.mean([len(doc) for doc in self.documents]) if self.documents else 0,
            "vector_store_initialized": self.index is not None,
            "embedding_model": "all-MiniLM-L6-v2" if SENTENCE_TRANSFORMERS_AVAILABLE else "fallback",
            "dependencies_available": {
                "sentence_transformers": SENTENCE_TRANSFORMERS_AVAILABLE,
                "sklearn": True,
            },
        }
