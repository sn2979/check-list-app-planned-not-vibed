from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from item.model import Item


def create_item(session: Session, category_id: int, name: str) -> Item:
    item = Item(category_id=category_id, name=name)
    session.add(item)
    session.flush()
    return item


def list_items(session: Session, category_id: int) -> list[Item]:
    return list(session.scalars(select(Item).where(Item.category_id == category_id).order_by(Item.id)))


def get_item(session: Session, category_id: int, item_id: int) -> Optional[Item]:
    return session.scalars(
        select(Item).where(Item.id == item_id, Item.category_id == category_id)
    ).one_or_none()


def delete_item(session: Session, item: Item) -> None:
    session.delete(item)
