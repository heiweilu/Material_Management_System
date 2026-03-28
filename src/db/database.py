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
            ("image_path", "VARCHAR(500)", "''"),
            ("supplier", "VARCHAR(200)", "''"),
        ]
        for col_name, sql_type, default in new_cols:
            if col_name not in cols:
                statements.append(
                    f"ALTER TABLE materials ADD COLUMN {col_name} {sql_type} DEFAULT {default}"
                )

        # v2 迁移：移除 material_code 和 default_supplier_id 列
        # SQLite 不支持 DROP COLUMN（3.35.0 之前），用重建表方式处理
        if "material_code" in cols or "default_supplier_id" in cols:
            _migrate_materials_v2()

    # ── 未来新增迁移在此追加 ──

    if not statements:
        return

    with _engine.begin() as conn:
        for stmt in statements:
            logger.info("执行迁移: %s", stmt)
            conn.execute(text(stmt))


def _migrate_materials_v2():
    """重建 materials 表，移除 material_code 和 default_supplier_id 列。"""
    logger.info("执行 v2 迁移：重建 materials 表（移除 material_code, default_supplier_id）")
    keep_cols = [
        "id", "material_name", "model", "package_type", "specification",
        "unit", "current_stock", "warning_threshold", "category_id",
        "storage_location", "supplier", "datasheet_path", "image_path",
        "remarks", "created_at", "updated_at",
    ]
    cols_csv = ", ".join(keep_cols)

    with _engine.begin() as conn:
        # 检查旧表实际拥有哪些列，只复制两边都有的
        inspector = inspect(_engine)
        old_cols = {c["name"] for c in inspector.get_columns("materials")}
        actual_cols = [c for c in keep_cols if c in old_cols]
        actual_csv = ", ".join(actual_cols)

        conn.execute(text(f"ALTER TABLE materials RENAME TO _materials_old"))
        # 通过 ORM 定义创建新表
        Base.metadata.tables["materials"].create(bind=_engine)
        conn.execute(text(
            f"INSERT INTO materials ({actual_csv}) SELECT {actual_csv} FROM _materials_old"
        ))
        conn.execute(text("DROP TABLE _materials_old"))
    logger.info("v2 迁移完成")


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
