"""
Chat Endpoints

Provides medical chatbot functionality:
- Chat query processing
- Conversation history
- Session management
"""

import time
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import (
    get_current_user,
    get_db,
    get_request_id,
    rate_limit_dependency,
)
from app.api.schemas import (
    ChatRequest,
    ChatResponse,
    ConversationHistory,
    SourceDocument,
)
from app.core.config import settings
from app.core.exceptions import LLMError, ValidationError
from app.core.logging import audit_logger, get_logger
from app.core.metrics import metrics
from app.core.security import InputSanitizer, TokenData
from app.services.chatbot import ChatbotService


logger = get_logger(__name__)
router = APIRouter(prefix="/chat", tags=["Chat"])


# Chatbot service instance (initialized lazily)
_chatbot_service: Optional[ChatbotService] = None


def get_chatbot_service() -> ChatbotService:
    """Get or create chatbot service instance."""
    global _chatbot_service
    if _chatbot_service is None:
        _chatbot_service = ChatbotService()
    return _chatbot_service


@router.post(
    "/query",
    response_model=ChatResponse,
    summary="Send Chat Query",
    description="Send a medical query to the chatbot and receive a response",
    dependencies=[Depends(rate_limit_dependency)],
)
async def chat_query(
    chat_request: ChatRequest,
    request_id: str = Depends(get_request_id),
    current_user: Optional[TokenData] = Depends(get_current_user),
    db=Depends(get_db),
) -> ChatResponse:
    """
    Process a chat query and return AI response.

    Args:
        chat_request: Chat query request
        request_id: Unique request identifier
        current_user: Optional authenticated user
        db: Database connection

    Returns:
        ChatResponse with AI-generated answer

    Raises:
        LLMError: If LLM processing fails
        ValidationError: If input validation fails
    """
    start_time = time.perf_counter()

    # Sanitize input
    sanitized_query = InputSanitizer.sanitize_query(chat_request.query)

    # Check for potential security issues
    if not InputSanitizer.is_safe_input(sanitized_query):
        threats = InputSanitizer.detect_injection_attempt(sanitized_query)
        logger.warning(
            f"Potential injection attempt detected: {threats}",
            extra={"extra_data": {"query": sanitized_query[:100], "threats": threats}}
        )

    # Generate or use provided session ID
    session_id = chat_request.session_id or str(uuid.uuid4())

    try:
        # Get chatbot service
        chatbot = get_chatbot_service()

        # Process query
        result = await chatbot.process_query(
            query=sanitized_query,
            session_id=session_id,
            max_tokens=chat_request.max_tokens,
            include_sources=chat_request.include_sources,
        )

        latency_ms = (time.perf_counter() - start_time) * 1000

        # Track metrics
        metrics.track_chat_query(
            query_length=len(sanitized_query),
            response_length=len(result["response"]),
            success=True,
        )

        # Audit logging
        user_id = current_user.sub if current_user else None
        audit_logger.log_prediction(
            user_id=user_id,
            query=sanitized_query,
            response_length=len(result["response"]),
            latency_ms=latency_ms,
            success=True,
        )

        # Store conversation in database
        await store_conversation(
            db=db,
            session_id=session_id,
            query=sanitized_query,
            response=result["response"],
            user_id=user_id,
        )

        # Build source documents
        sources = []
        if chat_request.include_sources and result.get("sources"):
            for source in result["sources"]:
                sources.append(SourceDocument(
                    content=source.get("content", ""),
                    metadata=source.get("metadata", {}),
                    score=source.get("score"),
                ))

        return ChatResponse(
            response=result["response"],
            query=sanitized_query,
            session_id=session_id,
            sources=sources,
            latency_ms=round(latency_ms, 2),
            request_id=request_id,
        )

    except Exception as e:
        latency_ms = (time.perf_counter() - start_time) * 1000

        # Track failure metrics
        metrics.track_chat_query(
            query_length=len(sanitized_query),
            response_length=0,
            success=False,
        )

        user_id = current_user.sub if current_user else None
        audit_logger.log_prediction(
            user_id=user_id,
            query=sanitized_query,
            response_length=0,
            latency_ms=latency_ms,
            success=False,
        )

        logger.error(f"Chat query failed: {str(e)}")
        raise LLMError(
            message="Failed to process chat query",
            details={"error": str(e)},
        )


@router.get(
    "/history/{session_id}",
    response_model=ConversationHistory,
    summary="Get Conversation History",
    description="Retrieve conversation history for a session",
)
async def get_conversation_history(
    session_id: str,
    request_id: str = Depends(get_request_id),
    current_user: Optional[TokenData] = Depends(get_current_user),
    db=Depends(get_db),
) -> ConversationHistory:
    """
    Get conversation history for a session.

    Args:
        session_id: Session identifier
        request_id: Request identifier
        current_user: Optional authenticated user
        db: Database connection

    Returns:
        ConversationHistory with messages
    """
    conversations_collection = db["conversations"]

    conversation = await conversations_collection.find_one(
        {"session_id": session_id}
    )

    if not conversation:
        return ConversationHistory(
            session_id=session_id,
            messages=[],
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

    from app.api.schemas import ChatMessage, MessageRole

    messages = []
    for msg in conversation.get("messages", []):
        messages.append(ChatMessage(
            role=MessageRole(msg["role"]),
            content=msg["content"],
            timestamp=msg.get("timestamp"),
        ))

    return ConversationHistory(
        session_id=session_id,
        messages=messages,
        created_at=conversation.get("created_at", datetime.now(timezone.utc)),
        updated_at=conversation.get("updated_at", datetime.now(timezone.utc)),
    )


@router.delete(
    "/history/{session_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Conversation History",
    description="Delete conversation history for a session",
)
async def delete_conversation_history(
    session_id: str,
    request_id: str = Depends(get_request_id),
    current_user: Optional[TokenData] = Depends(get_current_user),
    db=Depends(get_db),
) -> None:
    """
    Delete conversation history for a session.

    Args:
        session_id: Session identifier
        request_id: Request identifier
        current_user: Optional authenticated user
        db: Database connection
    """
    conversations_collection = db["conversations"]
    await conversations_collection.delete_one({"session_id": session_id})

    user_id = current_user.sub if current_user else None
    audit_logger.log_access(
        user_id=user_id,
        resource_type="conversation",
        resource_id=session_id,
        action="delete",
        success=True,
    )


async def store_conversation(
    db,
    session_id: str,
    query: str,
    response: str,
    user_id: Optional[str] = None,
) -> None:
    """
    Store conversation turn in database.

    Args:
        db: Database connection
        session_id: Session identifier
        query: User query
        response: AI response
        user_id: Optional user ID
    """
    conversations_collection = db["conversations"]
    now = datetime.now(timezone.utc)

    # Create message documents
    user_message = {
        "role": "user",
        "content": query,
        "timestamp": now,
    }

    assistant_message = {
        "role": "assistant",
        "content": response,
        "timestamp": now,
    }

    # Upsert conversation
    await conversations_collection.update_one(
        {"session_id": session_id},
        {
            "$push": {
                "messages": {
                    "$each": [user_message, assistant_message]
                }
            },
            "$set": {
                "updated_at": now,
                "user_id": user_id,
            },
            "$setOnInsert": {
                "created_at": now,
            }
        },
        upsert=True,
    )
