from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth import get_current_user
from ..db import get_db
from ..llm.providers import ProviderConfig, ProviderError, test_connection
from ..models import ModelProvider, User
from ..schemas import ProviderIn, ProviderOut

router = APIRouter(prefix="/api/models", tags=["models"])


def to_out(row: ModelProvider) -> ProviderOut:
    return ProviderOut(id=row.id, name=row.name, kind=row.kind, base_url=row.base_url,
                       model=row.model, has_key=bool(row.api_key), is_default=row.is_default)


def cfg_of(row: ModelProvider) -> ProviderConfig:
    return ProviderConfig(kind=row.kind, base_url=row.base_url, model=row.model, api_key=row.api_key or None)


async def owned_provider(provider_id: int, user: User, db: AsyncSession) -> ModelProvider:
    row = (await db.execute(select(ModelProvider).where(
        ModelProvider.id == provider_id, ModelProvider.user_id == user.id))).scalar_one_or_none()
    if row is None:
        raise HTTPException(404, "Model provider not found")
    return row


@router.get("")
async def list_providers(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    rows = (await db.execute(select(ModelProvider).where(ModelProvider.user_id == user.id))).scalars().all()
    return [to_out(r) for r in rows]


@router.post("", response_model=ProviderOut, status_code=201)
async def create_provider(payload: ProviderIn, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    row = ModelProvider(user_id=user.id, name=payload.name, kind=payload.kind, base_url=payload.base_url,
                        api_key=payload.api_key or None, model=payload.model, is_default=payload.is_default)
    if payload.is_default:
        existing = (await db.execute(select(ModelProvider).where(ModelProvider.user_id == user.id))).scalars().all()
        for other in existing:
            other.is_default = False
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return to_out(row)


@router.delete("/{provider_id}", status_code=204)
async def delete_provider(provider_id: int, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    row = await owned_provider(provider_id, user, db)
    await db.delete(row)
    await db.commit()


@router.post("/{provider_id}/test")
async def test_provider(provider_id: int, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    row = await owned_provider(provider_id, user, db)
    try:
        return await test_connection(cfg_of(row))
    except ProviderError as exc:
        return {"ok": False, "error": str(exc)}
