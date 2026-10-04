from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from file.schema import FileRead


class ItemCreate(BaseModel):
    name: str = Field(min_length=1)


class ItemUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1)

    @field_validator("name")
    @classmethod
    def name_not_null(cls, value: Optional[str]) -> str:
        # Omitting name leaves it unchanged; sending null would try to clear it, which isn't allowed.
        if value is None:
            raise ValueError("name cannot be null")
        return value


class ItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


class ItemDetail(ItemRead):
    files: list[FileRead]
