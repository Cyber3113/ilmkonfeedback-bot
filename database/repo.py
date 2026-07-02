"""Baza bilan ishlash uchun repository qatlami."""
from datetime import datetime

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import selectinload

from database.models import Appeal, AppealStatus, AppealType, Base, User


def make_session_pool(db_url: str) -> async_sessionmaker[AsyncSession]:
    engine = create_async_engine(db_url, echo=False)
    return async_sessionmaker(engine, expire_on_commit=False), engine


async def init_db(engine) -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


class Repo:
    def __init__(self, session: AsyncSession):
        self.session = session

    # ---------- Users ----------
    async def get_user(self, tg_id: int) -> User | None:
        res = await self.session.execute(select(User).where(User.tg_id == tg_id))
        return res.scalar_one_or_none()

    async def create_user(
        self, tg_id: int, full_name: str, phone: str, role: str
    ) -> User:
        user = User(tg_id=tg_id, full_name=full_name, phone=phone, role=role)
        self.session.add(user)
        await self.session.commit()
        return user

    async def all_active_user_ids(self) -> list[int]:
        res = await self.session.execute(
            select(User.tg_id).where(User.is_blocked == False)  # noqa: E712
        )
        return [row[0] for row in res.all()]

    async def mark_blocked(self, tg_id: int) -> None:
        await self.session.execute(
            update(User).where(User.tg_id == tg_id).values(is_blocked=True)
        )
        await self.session.commit()

    async def users_with_appeal_counts(self):
        res = await self.session.execute(
            select(User, func.count(Appeal.id))
            .outerjoin(Appeal, Appeal.user_id == User.id)
            .group_by(User.id)
            .order_by(func.count(Appeal.id).desc())
        )
        return res.all()

    # ---------- Appeals ----------
    async def next_public_id(self, appeal_type: str) -> str:
        prefix = "TAK" if appeal_type == AppealType.TAKLIF.value else "ETR"
        year = datetime.now().year
        res = await self.session.execute(
            select(func.count(Appeal.id)).where(Appeal.type == appeal_type)
        )
        count = res.scalar_one() + 1
        return f"{prefix}-{year}-{count:04d}"

    async def create_appeal(
        self, user: User, appeal_type: str, text: str, is_anonymous: bool
    ) -> Appeal:
        public_id = await self.next_public_id(appeal_type)
        appeal = Appeal(
            public_id=public_id,
            user_id=user.id,
            type=appeal_type,
            text=text,
            is_anonymous=is_anonymous,
        )
        self.session.add(appeal)
        await self.session.commit()
        return appeal

    async def get_appeal_by_public_id(self, public_id: str) -> Appeal | None:
        res = await self.session.execute(
            select(Appeal)
            .options(selectinload(Appeal.user))
            .where(Appeal.public_id == public_id)
        )
        return res.scalar_one_or_none()

    async def answer_appeal(self, appeal: Appeal, answer: str) -> None:
        appeal.answer = answer
        appeal.status = AppealStatus.ANSWERED.value
        appeal.answered_at = datetime.now()
        await self.session.commit()

    async def close_appeal(self, appeal: Appeal) -> None:
        appeal.status = AppealStatus.CLOSED.value
        await self.session.commit()

    async def my_appeals(self, user: User) -> list[Appeal]:
        res = await self.session.execute(
            select(Appeal)
            .where(Appeal.user_id == user.id)
            .order_by(Appeal.created_at.desc())
        )
        return list(res.scalars().all())

    async def all_appeals(self) -> list[Appeal]:
        res = await self.session.execute(
            select(Appeal)
            .options(selectinload(Appeal.user))
            .order_by(Appeal.created_at.desc())
        )
        return list(res.scalars().all())

    async def stats(self) -> dict:
        total_users = (
            await self.session.execute(select(func.count(User.id)))
        ).scalar_one()
        total = (
            await self.session.execute(select(func.count(Appeal.id)))
        ).scalar_one()
        by_type = {}
        for t in (AppealType.TAKLIF.value, AppealType.ETIROZ.value):
            by_type[t] = (
                await self.session.execute(
                    select(func.count(Appeal.id)).where(Appeal.type == t)
                )
            ).scalar_one()
        by_status = {}
        for s in (
            AppealStatus.PENDING.value,
            AppealStatus.ANSWERED.value,
            AppealStatus.CLOSED.value,
        ):
            by_status[s] = (
                await self.session.execute(
                    select(func.count(Appeal.id)).where(Appeal.status == s)
                )
            ).scalar_one()
        return {
            "total_users": total_users,
            "total_appeals": total,
            "by_type": by_type,
            "by_status": by_status,
        }
