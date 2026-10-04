from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from file.model import File

# Files are created through Category.add_file / Item.add_file, not here.


def list_category_files(session: Session, category_id: int) -> list[File]:
    return list(session.scalars(select(File).where(File.category_id == category_id).order_by(File.id)))


def list_item_files(session: Session, item_id: int) -> list[File]:
    return list(session.scalars(select(File).where(File.item_id == item_id).order_by(File.id)))


def get_category_file(session: Session, category_id: int, file_id: int) -> Optional[File]:
    return session.scalars(
        select(File).where(File.id == file_id, File.category_id == category_id)
    ).one_or_none()


def get_item_file(session: Session, item_id: int, file_id: int) -> Optional[File]:
    return session.scalars(select(File).where(File.id == file_id, File.item_id == item_id)).one_or_none()


def delete_file(session: Session, file: File) -> None:
    session.delete(file)
