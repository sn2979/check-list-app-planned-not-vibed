from typing import TYPE_CHECKING, Optional

from sqlalchemy import CheckConstraint, ForeignKey, LargeBinary
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base

if TYPE_CHECKING:
    from category.model import Category
    from item.model import Item

MAX_UPLOAD_BYTES = 10 * 1024 * 1024


class File(Base):
    __tablename__ = "files"
    __table_args__ = (
        # A file belongs to exactly one parent: a category or an item.
        CheckConstraint("(category_id IS NULL) != (item_id IS NULL)", name="file_has_one_parent"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    category_id: Mapped[Optional[int]] = mapped_column(ForeignKey("categories.id"))
    item_id: Mapped[Optional[int]] = mapped_column(ForeignKey("items.id"))
    name: Mapped[str]
    size: Mapped[int]
    # Deferred so listing files doesn't load every file's bytes; it loads on first access.
    content: Mapped[bytes] = mapped_column(LargeBinary, deferred=True)

    category: Mapped[Optional["Category"]] = relationship(back_populates="files")
    item: Mapped[Optional["Item"]] = relationship(back_populates="files")

    def __init__(self, name: str, content: bytes):
        super().__init__(name=name, content=content, size=len(content))

    def copy(self) -> "File":
        return File(name=self.name, content=self.content)
