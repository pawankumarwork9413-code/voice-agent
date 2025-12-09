from __future__ import annotations

import asyncio
import contextlib
import os
from functools import lru_cache
from typing import AsyncGenerator, Tuple, Optional

from agno.models.openrouter import OpenRouter
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException, Query
import base64
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.db.sqlite import SqliteDb
from agno.memory import MemoryManager

from prompts import instructions_description, instructions_prompt


from get_chat_Data import get_session_ids_by_username, get_chats_by_session, delete_session



APP_TITLE = "AI Assistant API"

# Read the content file
content_file_path = os.path.join(os.path.dirname(__file__), "scrapper", "get_contents", "contentfile.txt")
with open(content_file_path, "r", encoding="utf-8") as f:
    content = f.read()
    
    
class ChatRequest(BaseModel):
    session_id: str = Field(..., description="Client-managed chat session identifier")
    username: str = Field(..., description="Username to associate with the session")
    prompt: str = Field(..., description="User's latest prompt for the travel agent")


class SessionSummary(BaseModel):
    session_id: str
    first_message: str


class ChatEntry(BaseModel):
    user_prompt: str
    assistant_response: str
    timestamp: Optional[str] = None


class ChatResponse(BaseModel):
    text: str = Field(..., description="Text response from the assistant")



def _build_agent(*, user_id: str, session_id: str) -> Agent:
    """Create a configured agent instance for the provided identifiers."""

    db = SqliteDb(db_file="agno.db")
    memory_manager = MemoryManager(db=db)
    
    res = Agent(
        name="Milberg Intake Assistant",
        model=OpenAIChat(
        id="gpt-4.1-mini-2025-04-14",
        api_key='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',
        max_tokens=100,
        
    ),
        description=instructions_description(),
        instructions=instructions_prompt(content=content),
        markdown=True,
        add_datetime_to_context=True,
        timezone_identifier="Asia/Kolkata",
        user_id=user_id,
        session_id=session_id,
        db=db,
        memory_manager=memory_manager,
        enable_user_memories=True,
        add_history_to_context=True, 
        num_history_runs=10,
        cache_session=True,
    )
    return res


router = APIRouter()


def create_app() -> FastAPI:
    app = FastAPI(title=APP_TITLE)
    # Allow browser clients from any origin for easier local testing
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(router)
    return app


@router.post("/chat")
async def chat(request: ChatRequest) -> ChatResponse:
    print("prompt ", request.prompt, "Building agent with user_id:", request.username, "session_id:", request.session_id)
    agent = _build_agent(user_id=request.username, session_id=request.session_id)
    res = agent.run(request.prompt)
    
    # Prepare response with text and audio
    response_data = {
        "text": res.content,
        
    }
    return ChatResponse(**response_data)

@router.get("/sessions/{username}")
async def get_sessions(username: str) -> list[SessionSummary]:
    sessions_data = get_session_ids_by_username(username)
    return [SessionSummary(**session) for session in sessions_data]


@router.get("/sessions/{username}/{session_id}/chats")
async def get_chats(username: str, session_id: str) -> list[ChatEntry]:
    chats = get_chats_by_session(session_id, username)
    return [
        ChatEntry(
            user_prompt=chat.get("user_prompt", ""),
            assistant_response=chat.get("assistant_response", ""),
            timestamp=str(chat.get("timestamp")) if chat.get("timestamp") is not None else None,
        )
        for chat in chats
    ]
    
@router.delete("/sessions/{username}/{session_id}")
async def delete_session_endpoint(username: str, session_id: str) -> dict:

    success = delete_session(session_id, username)
    return {"success": success}


app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "fast_api_building:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", "8000")),
        reload=os.getenv("RELOAD", "1").lower() in {"1", "true", "yes"},
    )