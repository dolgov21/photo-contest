from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base, TimestampMixin

__all__ = ("AdminModel",)


class AdminModel(Base, TimestampMixin):
    __tablename__ = "admins"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    login: Mapped[str] = mapped_column(unique=True, nullable=False)
    password: Mapped[str] = mapped_column(nullable=False)
