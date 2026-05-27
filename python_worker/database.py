from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, Text, BigInteger


DATABASE_URL = "postgresql+asyncpg://postgres:password@localhost/english_bot"

engine = create_async_engine(DATABASE_URL, echo=False)
async_session = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


class UserWord(Base):
    __tablename__ = "user_words"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    telegram_id: Mapped[int] = mapped_column(
        BigInteger, index=True
    )
    word: Mapped[str] = mapped_column(String(100))
    definition: Mapped[str] = mapped_column(Text)
    example: Mapped[str] = mapped_column(Text, nullable=True)


async def init_db():
    """Создает таблицы при запуске"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
