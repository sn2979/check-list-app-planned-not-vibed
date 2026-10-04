from typing import TYPE_CHECKING

from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base

if TYPE_CHECKING:
    from category.model import Category


class Checklist(Base):
    __tablename__ = "checklists"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]

    categories: Mapped[list["Category"]] = relationship(
        back_populates="checklist", cascade="all, delete-orphan", order_by="Category.id"
    )

    def copy(self) -> "Checklist":
        return Checklist(name=self.name, categories=[c.copy() for c in self.categories])
