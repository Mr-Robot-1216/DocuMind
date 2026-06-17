from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.db import chroma_client, fts, history

router = APIRouter(prefix="/collections", tags=["collections"])


class CreateCollectionRequest(BaseModel):
    name: str


@router.post("")
async def create_collection(request: CreateCollectionRequest) -> dict:
    return history.create_collection(request.name)


@router.get("")
async def list_collections() -> list[dict]:
    return history.list_collections()


@router.get("/{collection_id}")
async def get_collection(collection_id: str) -> dict:
    collection = history.get_collection(collection_id)
    if collection is None:
        raise HTTPException(status_code=404, detail="Collection not found")
    return collection


@router.delete("/{collection_id}", status_code=204)
async def delete_collection(collection_id: str) -> None:
    if history.get_collection(collection_id) is None:
        raise HTTPException(status_code=404, detail="Collection not found")
    chroma_client.delete_collection(collection_id)
    fts.delete_collection_chunks(collection_id)
    history.delete_collection(collection_id)


@router.get("/{collection_id}/messages")
async def get_messages(collection_id: str) -> list[dict]:
    if history.get_collection(collection_id) is None:
        raise HTTPException(status_code=404, detail="Collection not found")
    return history.get_messages(collection_id, limit=100)
