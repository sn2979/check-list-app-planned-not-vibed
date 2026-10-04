from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from category.model import Category
from checklist.model import Checklist
from file.model import File
from item.model import Item


def create_checklist(session: Session, name: str) -> Checklist:
    checklist = Checklist(name=name)
    session.add(checklist)
    session.flush()
    return checklist


def list_checklists(session: Session) -> list[Checklist]:
    return list(session.scalars(select(Checklist).order_by(Checklist.id)))


def get_checklist(session: Session, checklist_id: int) -> Optional[Checklist]:
    return session.get(Checklist, checklist_id)


def get_checklist_contents(
    session: Session, checklist_id: int, *, include_file_content: bool = False
) -> Optional[Checklist]:
    """Load a checklist with all its categories, items and files in 4 queries.

    File bytes are only loaded when include_file_content is set (needed for copy).
    """
    item_files = selectinload(Checklist.categories).selectinload(Category.items).selectinload(Item.files)
    category_files = selectinload(Checklist.categories).selectinload(Category.files)
    if include_file_content:
        item_files = item_files.undefer(File.content)
        category_files = category_files.undefer(File.content)

    return session.scalars(
        select(Checklist).where(Checklist.id == checklist_id).options(item_files, category_files)
    ).one_or_none()


def delete_checklist(session: Session, checklist: Checklist) -> None:
    session.delete(checklist)
