from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base
from file.model import File

if TYPE_CHECKING:
    from category.model import Category


class Item(Base):
    __tablename__ = "items"

    id: Mapped[int] = mapped_column(primary_key=True)
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id"))
    name: Mapped[str]

    category: Mapped["Category"] = relationship(back_populates="items")
    files: Mapped[list["File"]] = relationship(
        back_populates="item", cascade="all, delete-orphan", order_by="File.id"
    )

    def copy(self) -> "Item":
        return Item(name=self.name, files=[f.copy() for f in self.files])

    def add_file(self, name: str, content: bytes) -> File:
        file = File(name=name, content=content)
        self.files.append(file)
        return file
