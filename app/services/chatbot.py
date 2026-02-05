"""
Chatbot Service

Provides medical chatbot functionality using:
- LangChain for LLM orchestration
- Pinecone for vector storage
- Sentence Transformers for embeddings
"""

import asyncio
import time
from typing import Any, Dict, List, Optional

from app.core.config import settings
from app.core.exceptions import LLMError, VectorStoreError
from app.core.logging import get_logger
from app.core.metrics import metrics


logger = get_logger(__name__)


class ChatbotService:
    """
    Medical chatbot service.

    Handles query processing using RAG (Retrieval-Augmented Generation)
    with Pinecone vector store and Llama 2 LLM.
    """

    def __init__(self):
        """Initialize chatbot service."""
        self._embeddings = None
        self._llm = None
        self._vector_store = None
        self._qa_chain = None
        self._initialized = False
        self._lock = asyncio.Lock()

    async def _initialize(self) -> None:
        """
        Lazy initialization of ML components.

        Loads models and establishes connections only when first needed.
        """
        if self._initialized:
            return

        async with self._lock:
            if self._initialized:
                return

            try:
                logger.info("Initializing chatbot service...")
                start_time = time.perf_counter()

                # Run initialization in thread pool to avoid blocking
                await asyncio.get_event_loop().run_in_executor(
                    None, self._sync_initialize
                )

                self._initialized = True
                init_time = time.perf_counter() - start_time
                logger.info(f"Chatbot service initialized in {init_time:.2f}s")

            except Exception as e:
                logger.error(f"Failed to initialize chatbot service: {str(e)}")
                raise LLMError(
                    message="Failed to initialize chatbot service",
                    details={"error": str(e)},
                )

    def _sync_initialize(self) -> None:
        """Synchronous initialization of ML components."""
        import os
        os.environ["PINECONE_API_KEY"] = settings.pinecone_api_key

        # Import ML libraries
        from langchain.chains import RetrievalQA
        from langchain.embeddings import HuggingFaceEmbeddings
        from langchain.llms import CTransformers
        from langchain.prompts import PromptTemplate
        from langchain_pinecone import PineconeVectorStore

        # Initialize embeddings
        logger.info("Loading embeddings model...")
        self._embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )

        # Initialize LLM
        logger.info("Loading LLM model...")
        self._llm = CTransformers(
            model=settings.llm_model_path,
            model_type=settings.llm_model_type,
            config={
                "max_new_tokens": settings.llm_max_tokens,
                "temperature": settings.llm_temperature,
                "context_length": settings.llm_context_length,
            },
        )

        # Initialize vector store
        logger.info("Connecting to Pinecone vector store...")
        self._vector_store = PineconeVectorStore.from_existing_index(
            index_name=settings.pinecone_index_name,
            namespace="default",
            embedding=self._embeddings,
        )

        # Create prompt template
        prompt_template = """
Use the following pieces of information to answer the user's question.
If you don't know the answer, just say that you don't know, don't try to make up an answer.

Context: {context}
Question: {question}

Only return the helpful answer below and nothing else.
Helpful answer:
"""

        prompt = PromptTemplate(
            template=prompt_template,
            input_variables=["context", "question"]
        )

        # Create QA chain
        self._qa_chain = RetrievalQA.from_chain_type(
            llm=self._llm,
            chain_type="stuff",
            retriever=self._vector_store.as_retriever(search_kwargs={"k": 2}),
            return_source_documents=True,
            chain_type_kwargs={"prompt": prompt},
        )

    async def process_query(
        self,
        query: str,
        session_id: Optional[str] = None,
        max_tokens: Optional[int] = None,
        include_sources: bool = False,
    ) -> Dict[str, Any]:
        """
        Process a chat query.

        Args:
            query: User's question
            session_id: Optional session ID for context
            max_tokens: Optional max tokens override
            include_sources: Whether to include source documents

        Returns:
            Dictionary with response and metadata

        Raises:
            LLMError: If processing fails
        """
        await self._initialize()

        start_time = time.perf_counter()
        model_name = "llama-2-7b"

        try:
            # Run inference in thread pool
            result = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self._qa_chain({"query": query}),
            )

            latency = time.perf_counter() - start_time

            # Track metrics
            metrics.track_llm_inference(
                model=model_name,
                operation="inference",
                latency=latency,
                success=True,
            )

            response = {
                "response": result.get("result", ""),
                "session_id": session_id,
            }

            # Include sources if requested
            if include_sources and result.get("source_documents"):
                sources = []
                for doc in result["source_documents"]:
                    sources.append({
                        "content": doc.page_content,
                        "metadata": doc.metadata,
                    })
                response["sources"] = sources
                metrics.documents_retrieved.observe(len(sources))

            return response

        except Exception as e:
            latency = time.perf_counter() - start_time
            metrics.track_llm_inference(
                model=model_name,
                operation="inference",
                latency=latency,
                success=False,
            )
            metrics.llm_errors_total.labels(
                model=model_name,
                error_type=type(e).__name__,
            ).inc()

            logger.error(f"Query processing failed: {str(e)}")
            raise LLMError(
                message="Failed to process query",
                details={"error": str(e)},
            )

    async def get_similar_documents(
        self,
        query: str,
        k: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve similar documents from vector store.

        Args:
            query: Query text
            k: Number of documents to retrieve

        Returns:
            List of similar documents

        Raises:
            VectorStoreError: If retrieval fails
        """
        await self._initialize()

        try:
            # Run search in thread pool
            docs = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self._vector_store.similarity_search_with_score(query, k=k),
            )

            results = []
            for doc, score in docs:
                results.append({
                    "content": doc.page_content,
                    "metadata": doc.metadata,
                    "score": float(score),
                })

            return results

        except Exception as e:
            logger.error(f"Document retrieval failed: {str(e)}")
            raise VectorStoreError(
                message="Failed to retrieve documents",
                details={"error": str(e)},
            )

    @property
    def is_initialized(self) -> bool:
        """Check if service is initialized."""
        return self._initialized
