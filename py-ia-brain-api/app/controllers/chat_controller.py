from fastapi import APIRouter, HTTPException
from app.models.chat_message import ChatMessage
from app.services.llm_service import LLMService

router = APIRouter()
llm_service = LLMService()

@router.post("/chat")
async def chat_bot(payload: ChatMessage):
    try:
        reply = await llm_service.process_chat(payload.message.strip())
        return {"reply": reply}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur du service LLM: {str(e)}")