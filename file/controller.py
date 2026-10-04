from urllib.parse import quote

from fastapi import APIRouter, HTTPException, Response, UploadFile
from sqlalchemy.orm import Session

from category import dao as category_dao
from category.model import Category
from database import SessionDep
from file import dao
from file.model import MAX_UPLOAD_BYTES, File
from file.schema import FileRead, FileUpdate
from item import dao as item_dao
from item.model import Item

# Files can belong to a category or to an item, so this router serves both URL shapes.
CATEGORY_FILES = "/checklists/{checklist_id}/categories/{category_id}/files"
ITEM_FILES = "/checklists/{checklist_id}/categories/{category_id}/items/{item_id}/files"

router = APIRouter(tags=["files"])


def _get_category_or_404(session: Session, checklist_id: int, category_id: int) -> Category:
    category = category_dao.get_category(session, checklist_id, category_id)
    if category is None:
        raise HTTPException(404, "Category not found")
    return category


def _get_item_or_404(session: Session, checklist_id: int, category_id: int, item_id: int) -> Item:
    _get_category_or_404(session, checklist_id, category_id)
    item = item_dao.get_item(session, category_id, item_id)
    if item is None:
        raise HTTPException(404, "Item not found")
    return item


def _get_category_file_or_404(session: Session, checklist_id: int, category_id: int, file_id: int) -> File:
    _get_category_or_404(session, checklist_id, category_id)
    file = dao.get_category_file(session, category_id, file_id)
    if file is None:
        raise HTTPException(404, "File not found")
    return file


def _get_item_file_or_404(
    session: Session, checklist_id: int, category_id: int, item_id: int, file_id: int
) -> File:
    _get_item_or_404(session, checklist_id, category_id, item_id)
    file = dao.get_item_file(session, item_id, file_id)
    if file is None:
        raise HTTPException(404, "File not found")
    return file


def _read_upload(upload: UploadFile) -> tuple[str, bytes]:
    # Read one byte past the limit: if we get it, the file is too big.
    content = upload.file.read(MAX_UPLOAD_BYTES + 1)
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(413, f"File exceeds {MAX_UPLOAD_BYTES // (1024 * 1024)} MB")
    return upload.filename or "untitled", content


def _download(file: File) -> Response:
    return Response(
        content=file.content,
        media_type="application/octet-stream",
        headers={"Content-Disposition": f"attachment; filename*=utf-8''{quote(file.name)}"},
    )


def _apply_update(file: File, body: FileUpdate) -> None:
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(file, field, value)


# ---- Category files ----

@router.get(CATEGORY_FILES, response_model=list[FileRead])
def list_category_files(checklist_id: int, category_id: int, session: SessionDep):
    _get_category_or_404(session, checklist_id, category_id)
    return dao.list_category_files(session, category_id)


@router.post(CATEGORY_FILES, response_model=FileRead, status_code=201)
def upload_category_file(checklist_id: int, category_id: int, file: UploadFile, session: SessionDep):
    category = _get_category_or_404(session, checklist_id, category_id)
    name, content = _read_upload(file)
    new_file = category.add_file(name, content)
    session.commit()
    return new_file


@router.get(CATEGORY_FILES + "/{file_id}", response_class=Response)
def download_category_file(checklist_id: int, category_id: int, file_id: int, session: SessionDep):
    return _download(_get_category_file_or_404(session, checklist_id, category_id, file_id))


@router.patch(CATEGORY_FILES + "/{file_id}", response_model=FileRead)
def update_category_file(
    checklist_id: int, category_id: int, file_id: int, body: FileUpdate, session: SessionDep
):
    file = _get_category_file_or_404(session, checklist_id, category_id, file_id)
    _apply_update(file, body)
    session.commit()
    return file


@router.delete(CATEGORY_FILES + "/{file_id}", status_code=204)
def delete_category_file(checklist_id: int, category_id: int, file_id: int, session: SessionDep):
    file = _get_category_file_or_404(session, checklist_id, category_id, file_id)
    dao.delete_file(session, file)
    session.commit()


# ---- Item files ----

@router.get(ITEM_FILES, response_model=list[FileRead])
def list_item_files(checklist_id: int, category_id: int, item_id: int, session: SessionDep):
    _get_item_or_404(session, checklist_id, category_id, item_id)
    return dao.list_item_files(session, item_id)


@router.post(ITEM_FILES, response_model=FileRead, status_code=201)
def upload_item_file(checklist_id: int, category_id: int, item_id: int, file: UploadFile, session: SessionDep):
    item = _get_item_or_404(session, checklist_id, category_id, item_id)
    name, content = _read_upload(file)
    new_file = item.add_file(name, content)
    session.commit()
    return new_file


@router.get(ITEM_FILES + "/{file_id}", response_class=Response)
def download_item_file(checklist_id: int, category_id: int, item_id: int, file_id: int, session: SessionDep):
    return _download(_get_item_file_or_404(session, checklist_id, category_id, item_id, file_id))


@router.patch(ITEM_FILES + "/{file_id}", response_model=FileRead)
def update_item_file(
    checklist_id: int, category_id: int, item_id: int, file_id: int, body: FileUpdate, session: SessionDep
):
    file = _get_item_file_or_404(session, checklist_id, category_id, item_id, file_id)
    _apply_update(file, body)
    session.commit()
    return file


@router.delete(ITEM_FILES + "/{file_id}", status_code=204)
def delete_item_file(checklist_id: int, category_id: int, item_id: int, file_id: int, session: SessionDep):
    file = _get_item_file_or_404(session, checklist_id, category_id, item_id, file_id)
    dao.delete_file(session, file)
    session.commit()
