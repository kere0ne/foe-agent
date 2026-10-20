import json

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth import get_current_user
from ..db import get_db
from ..llm.providers import ProviderConfig, ProviderError, stream_chat
from ..models import Conversation, Message, ModelProvider, User
from ..schemas import ChatIn, ConversationIn

router = APIRouter(prefix="/api/conversations", tags=["chat"])


async def owned_conversation(conversation_id: int, user: User, db: AsyncSession) -> Conversation:
    row = (await db.execute(select(Conversation).where(
        Conversation.id == conversation_id, Conversation.user_id == user.id))).scalar_one_or_none()
    if row is None:
        raise HTTPException(404, "Conversation not found")
    return row


async def provider_config(provider_id: int, user: User, db: AsyncSession) -> ProviderConfig:
    row = (await db.execute(select(ModelProvider).where(
        ModelProvider.id == provider_id, ModelProvider.user_id == user.id))).scalar_one_or_none()
    if row is None:
        raise HTTPException(404, "Model provider not found")
    return ProviderConfig(kind=row.kind, base_url=row.base_url, model=row.model, api_key=row.api_key or None)


@router.get("")
async def list_conversations(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    rows = (await db.execute(select(Conversation).where(Conversation.user_id == user.id).order_by(Conversation.created_at.desc()))).scalars().all()
    return [{"id": r.id, "title": r.title, "project_id": r.project_id} for r in rows]


@router.post("", status_code=201)
async def create_conversation(payload: ConversationIn, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    row = Conversation(user_id=user.id, project_id=payload.project_id, title=payload.title)
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return {"id": row.id, "title": row.title, "project_id": row.project_id}


@router.get("/{conversation_id}/messages")
async def messages(conversation_id: int, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    await owned_conversation(conversation_id, user, db)
    rows = (await db.execute(select(Message).where(Message.conversation_id == conversation_id).order_by(Message.id))).scalars().all()
    return [{"role": r.role, "content": r.content} for r in rows]


@router.post("/chat/stream")
async def chat_stream(payload: ChatIn, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    conversation = await owned_conversation(payload.conversation_id, user, db)
    cfg = await provider_config(payload.provider_id, user, db)
    history = (await db.execute(select(Message).where(Message.conversation_id == conversation.id).order_by(Message.id))).scalars().all()
    chat_messages = [{"role": m.role, "content": m.content} for m in history]
    chat_messages.append({"role": "user", "content": payload.content})
    db.add(Message(conversation_id=conversation.id, role="user", content=payload.content))
    await db.commit()

    async def event_stream():
        assistant = []
        try:
            async for chunk in stream_chat(cfg, chat_messages):
                assistant.append(chunk)
                yield f"data: {json.dumps({'chunk': chunk})}\n\n"
        except ProviderError as exc:
            yield f"data: {json.dumps({'error': str(exc)})}\n\n"
        finally:
            full = "".join(assistant)
            if full:
                db.add(Message(conversation_id=conversation.id, role="assistant", content=full))
                await db.commit()
            yield f"data: {json.dumps({'done': True})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")
