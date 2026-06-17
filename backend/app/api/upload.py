import io
from pathlib import Path

from fastapi import APIRouter, HTTPException, UploadFile

from app.core.ingestion import ingest_document
from app.core.parsing import SUPPORTED_EXTENSIONS
from app.db import history

router = APIRouter(prefix="/collections", tags=["upload"])


@router.post("/{collection_id}/documents")
async def upload_document(collection_id: str, file: UploadFile) -> dict:
    if history.get_collection(collection_id) is None:
        raise HTTPException(status_code=404, detail="Collection not found")

    suffix = Path(file.filename).suffix.lower()
    if suffix not in SUPPORTED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {suffix}")

    contents = await file.read()
    chunk_count = await ingest_document(collection_id, io.BytesIO(contents), file.filename)

    if chunk_count == 0:
        raise HTTPException(status_code=400, detail="No extractable text found in document")

    return history.add_document(collection_id, file.filename, chunk_count)
