"""数据库连接与初始化"""

import logging

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker, Session

from src.db.models import Base

logger = logging.getLogger(__name__)

_engine = None
_SessionFactory = None


def init_database(db_path: str):
    """初始化数据库引擎和表结构"""
    global _engine, _SessionFactory
    _engine = create_engine(f"sqlite:///{db_path}", echo=False)
    _SessionFactory = sessionmaker(bind=_engine)
    Base.metadata.create_all(_engine)
    _run_sqlite_migrations()
    logger.info("数据库初始化完成: %s", db_path)


def _run_sqlite_migrations():
    """为现有 SQLite 数据库补充新增列（运行时自动迁移）。
    新增字段时，在此函数中追加对应 ALTER TABLE 语句即可。
    """
    if _engine is None:
        return

    inspector = inspect(_engine)
    tables = set(inspector.get_table_names())
    statements: list[str] = []

    # ── materials 表迁移 ──
    if "materials" in tables:
        cols = {c["name"] for c in inspector.get_columns("materials")}
        new_cols = [
            ("storage_location", "VARCHAR(200)", "''"),
            ("datasheet_path", "VARCHAR(500)", "''"),
        ]
        for col_name, sql_type, default in new_cols:
            if col_name not in cols:
                statements.append(
                    f"ALTER TABLE materials ADD COLUMN {col_name} {sql_type} DEFAULT {default}"
                )

    # ── 未来新增迁移在此追加 ──

    if not statements:
        return

    with _engine.begin() as conn:
        for stmt in statements:
            logger.info("执行迁移: %s", stmt)
            conn.execute(text(stmt))


def get_session() -> Session:
    """获取数据库会话"""
    if _SessionFactory is None:
        raise RuntimeError("数据库未初始化，请先调用 init_database()")
    return _SessionFactory()


def get_engine():
    """获取数据库引擎（报表等场景直接用 engine 执行原生 SQL）"""
    if _engine is None:
        raise RuntimeError("数据库未初始化，请先调用 init_database()")
    return _engine
