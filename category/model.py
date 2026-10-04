from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base
from file.model import File

if TYPE_CHECKING:
    from checklist.model import Checklist
    from item.model import Item


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(primary_key=True)
    checklist_id: Mapped[int] = mapped_column(ForeignKey("checklists.id"))
    name: Mapped[str]

    checklist: Mapped["Checklist"] = relationship(back_populates="categories")
    items: Mapped[list["Item"]] = relationship(
        back_populates="category", cascade="all, delete-orphan", order_by="Item.id"
    )
    files: Mapped[list["File"]] = relationship(
        back_populates="category", cascade="all, delete-orphan", order_by="File.id"
    )

    def copy(self) -> "Category":
        return Category(
            name=self.name,
            items=[i.copy() for i in self.items],
            files=[f.copy() for f in self.files],
        )

    def add_file(self, name: str, content: bytes) -> File:
        file = File(name=name, content=content)
        self.files.append(file)
        return file
