from sqlalchemy import Column, ForeignKey, Table

from .base_model import Base

user_pet_association = Table(
    "user_pet_association",
    Base.metadata,
    Column("user_id", ForeignKey("users.id"), primary_key=True),
    Column("pet_id", ForeignKey("pets.id"), primary_key=True),
)
