from enum import Enum as PyEnum
from datetime import datetime
from sqlalchemy import String, DateTime, Boolean, Enum, func
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base

class UserRole(PyEnum):
    ADMIN = "admin"
    ANALYST = "analyst"
    READ_ONLY = "read_only"

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(150), unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole), nullable=False, default=UserRole.READ_ONLY
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )