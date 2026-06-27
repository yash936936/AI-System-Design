from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.core.config import get_settings
from app.db.models import Base

settings = get_settings()
engine = create_async_engine(settings.database_url, echo=settings.debug)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

async def init_db():
    """
    Dev-time schema sync.

    The previous implementation ran a raw `DO $$ ... DROP TABLE ... $$`
    block, which is PostgreSQL-only PL/pgSQL syntax. Since the default
    DATABASE_URL is SQLite, that statement raised
    `OperationalError: near "DO": syntax error` on every single startup —
    the app could never boot with the out-of-the-box config.

    `Base.metadata.drop_all` / `create_all` are pure SQLAlchemy Core and
    work identically against SQLite, Postgres, or any other supported
    dialect, so the app now boots regardless of which DB is configured.
    """
    async with engine.begin() as conn:
        print("⚠️  Dropping and recreating all database tables to match models...")
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
        print("✅ Database tables successfully recreated.")