from fastapi import APIRouter, HTTPException
from sqlalchemy.orm import Session

from category import dao
from category.model import Category
from category.schema import CategoryCreate, CategoryRead, CategoryUpdate
from checklist import dao as checklist_dao
from database import SessionDep

router = APIRouter(prefix="/checklists/{checklist_id}/categories", tags=["categories"])


def _ensure_checklist_exists(session: Session, checklist_id: int) -> None:
    if checklist_dao.get_checklist(session, checklist_id) is None:
        raise HTTPException(404, "Checklist not found")


def _get_category_or_404(session: Session, checklist_id: int, category_id: int) -> Category:
    category = dao.get_category(session, checklist_id, category_id)
    if category is None:
        raise HTTPException(404, "Category not found")
    return category


@router.get("", response_model=list[CategoryRead])
def list_categories(checklist_id: int, session: SessionDep):
    _ensure_checklist_exists(session, checklist_id)
    return dao.list_categories(session, checklist_id)


@router.post("", response_model=CategoryRead, status_code=201)
def create_category(checklist_id: int, body: CategoryCreate, session: SessionDep):
    _ensure_checklist_exists(session, checklist_id)
    category = dao.create_category(session, checklist_id, body.name)
    session.commit()
    return category


@router.get("/{category_id}", response_model=CategoryRead)
def get_category(checklist_id: int, category_id: int, session: SessionDep):
    return _get_category_or_404(session, checklist_id, category_id)


@router.patch("/{category_id}", response_model=CategoryRead)
def update_category(checklist_id: int, category_id: int, body: CategoryUpdate, session: SessionDep):
    category = _get_category_or_404(session, checklist_id, category_id)
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(category, field, value)
    session.commit()
    return category


@router.delete("/{category_id}", status_code=204)
def delete_category(checklist_id: int, category_id: int, session: SessionDep):
    category = _get_category_or_404(session, checklist_id, category_id)
    dao.delete_category(session, category)
    session.commit()
