from .base_model import Base
from geoalchemy2 import Geometry
from sqlalchemy.orm import Mapped, mapped_column

class Lake(Base):
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str]
    geom: Mapped[Geometry] = mapped_column(Geometry('POINT'))
