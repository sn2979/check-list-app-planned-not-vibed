from fastapi import APIRouter, HTTPException
from sqlalchemy.orm import Session

from category import dao as category_dao
from database import SessionDep
from item import dao
from item.model import Item
from item.schema import ItemCreate, ItemRead, ItemUpdate

router = APIRouter(prefix="/checklists/{checklist_id}/categories/{category_id}/items", tags=["items"])


def _ensure_category_exists(session: Session, checklist_id: int, category_id: int) -> None:
    if category_dao.get_category(session, checklist_id, category_id) is None:
        raise HTTPException(404, "Category not found")


def _get_item_or_404(session: Session, checklist_id: int, category_id: int, item_id: int) -> Item:
    _ensure_category_exists(session, checklist_id, category_id)
    item = dao.get_item(session, category_id, item_id)
    if item is None:
        raise HTTPException(404, "Item not found")
    return item


@router.get("", response_model=list[ItemRead])
def list_items(checklist_id: int, category_id: int, session: SessionDep):
    _ensure_category_exists(session, checklist_id, category_id)
    return dao.list_items(session, category_id)


@router.post("", response_model=ItemRead, status_code=201)
def create_item(checklist_id: int, category_id: int, body: ItemCreate, session: SessionDep):
    _ensure_category_exists(session, checklist_id, category_id)
    item = dao.create_item(session, category_id, body.name)
    session.commit()
    return item


@router.get("/{item_id}", response_model=ItemRead)
def get_item(checklist_id: int, category_id: int, item_id: int, session: SessionDep):
    return _get_item_or_404(session, checklist_id, category_id, item_id)


@router.patch("/{item_id}", response_model=ItemRead)
def update_item(checklist_id: int, category_id: int, item_id: int, body: ItemUpdate, session: SessionDep):
    item = _get_item_or_404(session, checklist_id, category_id, item_id)
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(item, field, value)
    session.commit()
    return item


@router.delete("/{item_id}", status_code=204)
def delete_item(checklist_id: int, category_id: int, item_id: int, session: SessionDep):
    item = _get_item_or_404(session, checklist_id, category_id, item_id)
    dao.delete_item(session, item)
    session.commit()
