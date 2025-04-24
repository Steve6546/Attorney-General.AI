"""
RAG (Retrieval-Augmented Generation) System for Attorney-General.AI.

This module provides functionality for document indexing, retrieval, and augmented generation.
"""

import logging
import os
import json
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
import uuid
from datetime import datetime
import asyncio

from backend.core.llm_service import LLMService
from backend.data.models import Document, DocumentChunk
from backend.data.repository import DocumentRepository, DocumentChunkRepository
from backend.config.settings import settings

# Configure logging
logger = logging.getLogger(__name__)

class RAGSystem:
    """Retrieval-Augmented Generation System."""
    
    def __init__(self, db: Session, llm_service: Optional[LLMService] = None):
        """
        Initialize the RAG system.
        
        Args:
            db: Database session
            llm_service: LLM service instance
        """
        self.db = db
        self.llm_service = llm_service or LLMService()
        self.document_repo = DocumentRepository(db)
        self.chunk_repo = DocumentChunkRepository(db)
        
        # Chunk size settings
        self.chunk_size = settings.RAG_CHUNK_SIZE
        self.chunk_overlap = settings.RAG_CHUNK_OVERLAP
        
        logger.info("RAG System initialized")
    
    async def index_document(self, document_id: str) -> Dict[str, Any]:
        """
        Index a document for retrieval.
        
        Args:
            document_id: Document ID
            
        Returns:
            Dict[str, Any]: Indexing result
        """
        try:
            # Get document
            document = self.document_repo.get_by_id(document_id)
            if not document:
                return {
                    "document_id": document_id,
                    "status": "error",
                    "message": "Document not found"
                }
            
            # Check if file exists
            if not os.path.exists(document.file_path):
                return {
                    "document_id": document_id,
                    "status": "error",
                    "message": "Document file not found"
                }
            
            # Read document content
            with open(document.file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Delete existing chunks
            self.chunk_repo.delete_by_document_id(document_id)
            
            # Create chunks
            chunks = self._create_chunks(content)
            
            # Create embeddings for chunks
            chunk_objects = []
            for i, chunk in enumerate(chunks):
                # Generate embedding
                embedding = await self.llm_service.generate_embeddings_async(chunk)
                
                # Create chunk object
                chunk_object = DocumentChunk(
                    id=str(uuid.uuid4()),
                    document_id=document_id,
                    chunk_index=i,
                    content=chunk,
                    embedding=embedding,
                    created_at=datetime.utcnow()
                )
                
                chunk_objects.append(chunk_object)
            
            # Save chunks to database
            for chunk_object in chunk_objects:
                self.chunk_repo.create(chunk_object)
            
            # Update document processed status
            self.document_repo.update_processed_status(document_id, True)
            
            return {
                "document_id": document_id,
                "chunks_created": len(chunk_objects),
                "status": "success",
                "message": f"Document indexed successfully with {len(chunk_objects)} chunks"
            }
        except Exception as e:
            logger.error(f"Error indexing document: {str(e)}")
            return {
                "document_id": document_id,
                "status": "error",
                "message": f"Error indexing document: {str(e)}"
            }
    
    def _create_chunks(self, content: str) -> List[str]:
        """
        Create chunks from document content.
        
        Args:
            content: Document content
            
        Returns:
            List[str]: List of chunks
        """
        chunks = []
        
        # Split content into paragraphs
        paragraphs = [p for p in content.split('\n\n') if p.strip()]
        
        current_chunk = ""
        for paragraph in paragraphs:
            # If adding this paragraph would exceed chunk size, save current chunk and start a new one
            if len(current_chunk) + len(paragraph) > self.chunk_size:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                
                # Start new chunk with overlap from previous chunk if possible
                if current_chunk and self.chunk_overlap > 0:
                    words = current_chunk.split()
                    overlap_words = words[-min(len(words), self.chunk_overlap):]
                    current_chunk = ' '.join(overlap_words) + '\n\n' + paragraph
                else:
                    current_chunk = paragraph
            else:
                # Add paragraph to current chunk
                if current_chunk:
                    current_chunk += '\n\n' + paragraph
                else:
                    current_chunk = paragraph
        
        # Add the last chunk if it's not empty
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks
    
    async def retrieve_relevant_chunks(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """
        Retrieve relevant chunks for a query.
        
        Args:
            query: Query text
            top_k: Number of chunks to retrieve
            
        Returns:
            List[Dict[str, Any]]: List of relevant chunks with metadata
        """
        try:
            # Generate query embedding
            query_embedding = await self.llm_service.generate_embeddings_async(query)
            if not query_embedding:
                return []
            
            # Get all chunks
            all_chunks = self.db.query(DocumentChunk).all()
            if not all_chunks:
                return []
            
            # Calculate similarity scores
            chunk_scores = []
            for chunk in all_chunks:
                if not chunk.embedding:
                    continue
                
                # Calculate cosine similarity
                similarity = self._cosine_similarity(query_embedding, chunk.embedding)
                
                # Add to scores
                chunk_scores.append({
                    "chunk": chunk,
                    "score": similarity
                })
            
            # Sort by score and get top_k
            chunk_scores.sort(key=lambda x: x["score"], reverse=True)
            top_chunks = chunk_scores[:top_k]
            
            # Format results
            results = []
            for item in top_chunks:
                chunk = item["chunk"]
                document = self.document_repo.get_by_id(chunk.document_id)
                
                results.append({
                    "chunk_id": chunk.id,
                    "document_id": chunk.document_id,
                    "document_name": document.filename if document else "Unknown",
                    "content": chunk.content,
                    "score": item["score"]
                })
            
            return results
        except Exception as e:
            logger.error(f"Error retrieving relevant chunks: {str(e)}")
            return []
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """
        Calculate cosine similarity between two vectors.
        
        Args:
            vec1: First vector
            vec2: Second vector
            
        Returns:
            float: Cosine similarity
        """
        vec1 = np.array(vec1)
        vec2 = np.array(vec2)
        
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)
    
    async def generate_augmented_response(self, query: str, user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate an augmented response for a query.
        
        Args:
            query: Query text
            user_id: User ID for filtering documents
            
        Returns:
            Dict[str, Any]: Augmented response
        """
        try:
            # Retrieve relevant chunks
            relevant_chunks = await self.retrieve_relevant_chunks(query, top_k=settings.RAG_TOP_K)
            
            if not relevant_chunks:
                # No relevant chunks found, generate response without augmentation
                response = await self.llm_service.generate_response_async(
                    prompt=f"Question: {query}\n\nAnswer:",
                    max_tokens=settings.RAG_MAX_TOKENS,
                    temperature=settings.RAG_TEMPERATURE
                )
                
                return {
                    "query": query,
                    "response": response,
                    "sources": [],
                    "augmented": False
                }
            
            # Prepare context from chunks
            context = "Context information:\n\n"
            sources = []
            
            for i, chunk in enumerate(relevant_chunks):
                context += f"[{i+1}] {chunk['content']}\n\n"
                
                # Add source
                sources.append({
                    "document_id": chunk["document_id"],
                    "document_name": chunk["document_name"],
                    "score": chunk["score"]
                })
            
            # Generate augmented response
            prompt = f"{context}\nQuestion: {query}\n\nAnswer based on the provided context:"
            
            response = await self.llm_service.generate_response_async(
                prompt=prompt,
                max_tokens=settings.RAG_MAX_TOKENS,
                temperature=settings.RAG_TEMPERATURE
            )
            
            return {
                "query": query,
                "response": response,
                "sources": sources,
                "augmented": True
            }
        except Exception as e:
            logger.error(f"Error generating augmented response: {str(e)}")
            
            # Fallback to non-augmented response
            try:
                response = await self.llm_service.generate_response_async(
                    prompt=f"Question: {query}\n\nAnswer:",
                    max_tokens=settings.RAG_MAX_TOKENS,
                    temperature=settings.RAG_TEMPERATURE
                )
            except Exception:
                response = "I apologize, but I encountered an error processing your request. Please try again later."
            
            return {
                "query": query,
                "response": response,
                "sources": [],
                "augmented": False,
                "error": str(e)
            }
