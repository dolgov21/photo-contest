import typing
import hashlib

from sqlalchemy import select, delete

from app.db.models.admin import AdminModel
from app.db.models.game import ContestModel, UserModel, RoundModel, MatchModel, VoteModel


if typing.TYPE_CHECKING:
    from app.web.app import Application


class AdminAccessor:
    def __init__(self, app: "Application"):
        self.app = app

    async def connect(self, app: "Application") -> None:
        admin_cfg = app.config.admin
        existing = await self.get_admin_by_login(admin_cfg.login)
        if not existing:
            await self.create_admin(admin_cfg.login, admin_cfg.password)

    async def create_admin(self, login: str, password: str) -> AdminModel:
        async with self.app.database.sessionmaker() as session:
            hashed_password = hashlib.md5(password.encode()).hexdigest()
            admin = AdminModel(
                login=login,
                password=hashed_password,
            )
            session.add(admin)
            await session.commit()
            await session.refresh(admin)
            return admin
        
    async def get_admin_by_login(self, login: str) -> AdminModel | None:
        async with self.app.database.sessionmaker() as session:
            query = select(AdminModel).where(AdminModel.login == login)
            result = await session.execute(query)
            return result.scalar_one_or_none()

    async def get_all_contests(self) -> list[ContestModel]:
        async with self.app.database.sessionmaker() as session:
            query = select(ContestModel).order_by(ContestModel.contest_id.desc())
            result = await session.execute(query)
            return list(result.scalars().all())
    
    async def create_user(
        self,
        user_id: int,
        first_name: str,
        photo_id: str,
        last_name: str | None = None,
        username: str | None = None,
    ) -> UserModel | None:
        async with self.app.database.sessionmaker() as session:
            user = UserModel(
                user_id=user_id,
                first_name=first_name,
                last_name=last_name,
                username=username,
                photo_id=photo_id,
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)
            return user

    async def get_contest_by_id(self, contest_id: int) -> ContestModel | None:
        return await self.app.store.db.get_contest_by_id(contest_id)

    async def remove_user_from_contest(self, user_id: int, contest_id: int) -> bool:
        return await self.app.store.db.remove_user_from_contest(user_id, contest_id)

    async def deactivate_contest(self, contest_id: int):
        return await self.app.store.db.deactivate_contest(contest_id)

    async def delete_contest(self, contest_id: int) -> bool:
        async with self.app.database.sessionmaker() as session:
            contest = await self.get_contest_by_id(contest_id)
            if not contest:
                return False
                
            await session.delete(contest)
            await session.commit()
            return True
