from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from category.schema import CategoryDetail


class ChecklistCreate(BaseModel):
    name: str = Field(min_length=1)


class ChecklistUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1)

    @field_validator("name")
    @classmethod
    def name_not_null(cls, value: Optional[str]) -> str:
        # Omitting name leaves it unchanged; sending null would try to clear it, which isn't allowed.
        if value is None:
            raise ValueError("name cannot be null")
        return value


class ChecklistRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


class ChecklistDetail(ChecklistRead):
    categories: list[CategoryDetail]
