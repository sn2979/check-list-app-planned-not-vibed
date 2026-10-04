from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from category.model import Category


def create_category(session: Session, checklist_id: int, name: str) -> Category:
    category = Category(checklist_id=checklist_id, name=name)
    session.add(category)
    session.flush()
    return category


def list_categories(session: Session, checklist_id: int) -> list[Category]:
    return list(
        session.scalars(
            select(Category).where(Category.checklist_id == checklist_id).order_by(Category.id)
        )
    )


def get_category(session: Session, checklist_id: int, category_id: int) -> Optional[Category]:
    return session.scalars(
        select(Category).where(Category.id == category_id, Category.checklist_id == checklist_id)
    ).one_or_none()


def delete_category(session: Session, category: Category) -> None:
    session.delete(category)
