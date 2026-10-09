# backend/app/api/routes_chat.py
from fastapi import APIRouter
from app.models import ChatRequest
from app.services.chat_service import execute_chat_turn

router = APIRouter()


@router.post("/chat")
async def chat_with_talent(req: ChatRequest):
    msg = (req.message or "").strip()
    result = execute_chat_turn(message=msg, history=req.history)

    return {
        "answer": result["answer"],
        "candidates": result["candidates"]
    }
