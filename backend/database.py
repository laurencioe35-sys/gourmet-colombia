import os
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.dialects import sqlite

# Railway provee DATABASE_URL automaticamente con PostgreSQL. Algunas
# configuraciones exponen la URL privada o publica con nombres alternativos.
# Localmente usa SQLite si ninguna URL fue configurada.
DATABASE_URL = (
    os.getenv("DATABASE_URL", "").strip()
    or os.getenv("DATABASE_PRIVATE_URL", "").strip()
    or os.getenv("DATABASE_PUBLIC_URL", "").strip()
    or "sqlite:///./gormet_pos.db"
)

# Railway a veces usa "postgres://" — SQLAlchemy necesita "postgresql://"
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Configuracion segun el motor
if "sqlite" in DATABASE_URL:
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False}
    )
else:
    # PostgreSQL (Railway)
    engine = create_engine(
        DATABASE_URL,
        pool_size=5,
        max_overflow=10,
        pool_pre_ping=True,
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def ensure_database_compatibility():
    """Adds missing columns to older SQLite/Postgres databases without dropping data."""
    try:
        inspector = inspect(engine)
    except Exception:
        return

    for table in Base.metadata.sorted_tables:
        table_name = table.name
        if not inspector.has_table(table_name):
            continue

        existing_columns = {col["name"] for col in inspector.get_columns(table_name)}
        for column in table.columns:
            if column.name in existing_columns:
                continue

            column_type = column.type.compile(dialect=sqlite.dialect())
            nullable = "NULL" if column.nullable else "NOT NULL"
            default = ""

            if column.default is not None and not callable(column.default.arg):
                default_value = column.default.arg
                if isinstance(default_value, str):
                    default = f"DEFAULT '{default_value}'"
                else:
                    default = f"DEFAULT {default_value}"
            elif column.default is not None and callable(column.default.arg):
                default = ""

            if column.primary_key:
                continue

            with engine.begin() as conn:
                conn.execute(
                    text(
                        f'ALTER TABLE "{table_name}" ADD COLUMN "{column.name}" {column_type} {nullable} {default}'.strip()
                    )
                )


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
