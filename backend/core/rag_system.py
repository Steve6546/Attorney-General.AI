"""
Attorney-General.AI - RAG System

This module implements the Retrieval Augmented Generation (RAG) system for the Attorney-General.AI backend.
It provides functionality for document processing, embedding, and retrieval.
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
import os
import json
import numpy as np
from pathlib import Path

from backend.config.settings import settings
from backend.core.llm_service import LLMService

logger = logging.getLogger(__name__)

class RAGSystem:
    """RAG system for document retrieval and generation."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the RAG system.
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        self.vector_db_path = self.config.get("vector_db_path", settings.VECTOR_DB_PATH)
        self.embedding_model = self.config.get("embedding_model", settings.EMBEDDING_MODEL)
        self.llm_service = LLMService()
        
        # Create vector DB directory if it doesn't exist
        os.makedirs(self.vector_db_path, exist_ok=True)
    
    async def process_document(self, document_path: str, document_id: str) -> Dict[str, Any]:
        """
        Process a document for RAG.
        
        Args:
            document_path: Path to the document file
            document_id: ID of the document
            
        Returns:
            Dict[str, Any]: Processing result
        """
        try:
            # Extract text from document (simplified for now)
            text = await self._extract_text(document_path)
            
            # Split text into chunks
            chunks = self._split_text(text)
            
            # Generate embeddings for chunks
            chunk_embeddings = await self._generate_embeddings(chunks)
            
            # Store embeddings
            await self._store_embeddings(document_id, chunks, chunk_embeddings)
            
            return {
                "document_id": document_id,
                "chunks_processed": len(chunks),
                "status": "success"
            }
        except Exception as e:
            logger.error(f"Error processing document: {str(e)}")
            return {
                "document_id": document_id,
                "status": "error",
                "error": str(e)
            }
    
    async def query(self, query: str, top_k: int = 3) -> Dict[str, Any]:
        """
        Query the RAG system.
        
        Args:
            query: The query string
            top_k: Number of top results to return
            
        Returns:
            Dict[str, Any]: Query results
        """
        try:
            # Generate embedding for query
            query_embedding = await self._generate_query_embedding(query)
            
            # Retrieve relevant chunks
            relevant_chunks = await self._retrieve_chunks(query_embedding, top_k)
            
            # Generate response
            response = await self._generate_response(query, relevant_chunks)
            
            return {
                "query": query,
                "response": response,
                "sources": [chunk["metadata"] for chunk in relevant_chunks]
            }
        except Exception as e:
            logger.error(f"Error querying RAG system: {str(e)}")
            return {
                "query": query,
                "status": "error",
                "error": str(e)
            }
    
    async def _extract_text(self, document_path: str) -> str:
        """
        Extract text from a document.
        
        Args:
            document_path: Path to the document file
            
        Returns:
            str: Extracted text
        """
        # This is a simplified implementation
        # In a real system, this would handle different file types (PDF, DOCX, etc.)
        
        file_extension = Path(document_path).suffix.lower()
        
        if file_extension in [".txt", ".md"]:
            # Read text file directly
            with open(document_path, "r", encoding="utf-8") as f:
                return f.read()
        else:
            # For other file types, we would use specialized libraries
            # For now, return a placeholder message
            return f"[Text extracted from {file_extension} file]"
    
    def _split_text(self, text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
        """
        Split text into chunks.
        
        Args:
            text: The text to split
            chunk_size: Maximum chunk size in characters
            overlap: Overlap between chunks in characters
            
        Returns:
            List[str]: List of text chunks
        """
        chunks = []
        
        if len(text) <= chunk_size:
            chunks.append(text)
        else:
            start = 0
            while start < len(text):
                end = min(start + chunk_size, len(text))
                
                # Try to find a good break point
                if end < len(text):
                    # Look for paragraph break
                    paragraph_break = text.rfind("\n\n", start, end)
                    if paragraph_break != -1 and paragraph_break > start + chunk_size // 2:
                        end = paragraph_break + 2
                    else:
                        # Look for line break
                        line_break = text.rfind("\n", start, end)
                        if line_break != -1 and line_break > start + chunk_size // 2:
                            end = line_break + 1
                        else:
                            # Look for sentence break
                            sentence_break = text.rfind(". ", start, end)
                            if sentence_break != -1 and sentence_break > start + chunk_size // 2:
                                end = sentence_break + 2
                
                chunks.append(text[start:end])
                start = end - overlap
        
        return chunks
    
    async def _generate_embeddings(self, chunks: List[str]) -> List[List[float]]:
        """
        Generate embeddings for text chunks.
        
        Args:
            chunks: List of text chunks
            
        Returns:
            List[List[float]]: List of embeddings
        """
        # In a real implementation, this would call an embedding API
        # For now, we'll return placeholder embeddings
        
        # Simulate embeddings with random vectors
        embeddings = []
        for _ in chunks:
            # Generate a random 1536-dimensional vector (common for embeddings)
            embedding = np.random.randn(1536).tolist()
            embeddings.append(embedding)
        
        return embeddings
    
    async def _generate_query_embedding(self, query: str) -> List[float]:
        """
        Generate embedding for a query.
        
        Args:
            query: The query string
            
        Returns:
            List[float]: Query embedding
        """
        # In a real implementation, this would call an embedding API
        # For now, we'll return a placeholder embedding
        
        # Simulate embedding with a random vector
        return np.random.randn(1536).tolist()
    
    async def _store_embeddings(self, document_id: str, chunks: List[str], embeddings: List[List[float]]) -> None:
        """
        Store embeddings in the vector database.
        
        Args:
            document_id: ID of the document
            chunks: List of text chunks
            embeddings: List of embeddings
        """
        # In a real implementation, this would store embeddings in a vector database
        # For now, we'll save them to a JSON file
        
        data = []
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            data.append({
                "id": f"{document_id}_{i}",
                "document_id": document_id,
                "chunk_index": i,
                "text": chunk,
                "embedding": embedding
            })
        
        # Save to file
        file_path = os.path.join(self.vector_db_path, f"{document_id}.json")
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    
    async def _retrieve_chunks(self, query_embedding: List[float], top_k: int) -> List[Dict[str, Any]]:
        """
        Retrieve relevant chunks for a query.
        
        Args:
            query_embedding: Query embedding
            top_k: Number of top results to return
            
        Returns:
            List[Dict[str, Any]]: List of relevant chunks with metadata
        """
        # In a real implementation, this would query a vector database
        # For now, we'll return placeholder results
        
        results = []
        
        # List all embedding files
        for file_name in os.listdir(self.vector_db_path):
            if file_name.endswith(".json"):
                file_path = os.path.join(self.vector_db_path, file_name)
                
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                
                for item in data:
                    # Calculate similarity (simplified)
                    similarity = 0.5 + np.random.random() * 0.5  # Random similarity between 0.5 and 1.0
                    
                    results.append({
                        "text": item["text"],
                        "similarity": similarity,
                        "metadata": {
                            "document_id": item["document_id"],
                            "chunk_index": item["chunk_index"]
                        }
                    })
        
        # Sort by similarity and take top_k
        results.sort(key=lambda x: x["similarity"], reverse=True)
        return results[:top_k]
    
    async def _generate_response(self, query: str, relevant_chunks: List[Dict[str, Any]]) -> str:
        """
        Generate a response based on the query and relevant chunks.
        
        Args:
            query: The query string
            relevant_chunks: List of relevant chunks
            
        Returns:
            str: Generated response
        """
        # Format context from relevant chunks
        context = "\n\n".join([f"[Document {i+1}]: {chunk['text']}" for i, chunk in enumerate(relevant_chunks)])
        
        # Create prompt
        prompt = f"""
        Based on the following context, please answer the query.
        
        Query: {query}
        
        Context:
        {context}
        
        Answer:
        """
        
        # Generate response using LLM
        response = await self.llm_service.generate_response(
            prompt=prompt,
            max_tokens=500,
            temperature=0.3
        )
        
        return response
