"""SQLAlchemy 2.0 async modellar."""
from datetime import datetime
from enum import Enum

from sqlalchemy import BigInteger, DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class UserRole(str, Enum):
    PARENT = "parent"
    STUDENT = "student"
    STAFF = "staff"


class AppealType(str, Enum):
    TAKLIF = "taklif"
    ETIROZ = "etiroz"


class AppealStatus(str, Enum):
    PENDING = "pending"      # Ko'rib chiqilmoqda
    ANSWERED = "answered"    # Javob berildi
    CLOSED = "closed"        # Yopildi


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    tg_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(255))
    phone: Mapped[str] = mapped_column(String(32))
    role: Mapped[str] = mapped_column(String(16), default=UserRole.PARENT.value)
    is_blocked: Mapped[bool] = mapped_column(default=False)  # botni bloklaganlar
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )

    appeals: Mapped[list["Appeal"]] = relationship(back_populates="user")


class Appeal(Base):
    __tablename__ = "appeals"

    id: Mapped[int] = mapped_column(primary_key=True)
    public_id: Mapped[str] = mapped_column(String(20), unique=True, index=True)  # TAK-2026-0001
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    type: Mapped[str] = mapped_column(String(10))          # taklif / etiroz
    status: Mapped[str] = mapped_column(
        String(10), default=AppealStatus.PENDING.value
    )
    text: Mapped[str] = mapped_column(Text)
    is_anonymous: Mapped[bool] = mapped_column(default=False)
    answer: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )
    answered_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    user: Mapped["User"] = relationship(back_populates="appeals")
