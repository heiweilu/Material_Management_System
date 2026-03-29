"""分类树 CRUD 服务"""

import logging

from src.db.database import get_session
from src.db.models import Category

logger = logging.getLogger(__name__)


def get_all_categories() -> list[Category]:
    """获取所有分类（按树形层级顺序：父节点后紧跟其子节点）"""
    session = get_session()
    try:
        all_cats = session.query(Category).order_by(Category.sort_order, Category.name).all()
        session.expunge_all()

        # 构建 parent_id -> children 映射
        children_map: dict[int | None, list[Category]] = {}
        for cat in all_cats:
            children_map.setdefault(cat.parent_id, []).append(cat)

        # 递归展开为树形顺序
        result: list[Category] = []

        def _walk(parent_id: int | None):
            for cat in children_map.get(parent_id, []):
                result.append(cat)
                _walk(cat.id)

        _walk(None)
        return result
    finally:
        session.close()


def get_root_categories() -> list[Category]:
    """获取顶级分类"""
    session = get_session()
    try:
        results = session.query(Category).filter(
            Category.parent_id.is_(None)
        ).order_by(Category.sort_order, Category.name).all()
        session.expunge_all()
        return results
    finally:
        session.close()


def get_descendant_ids(category_id: int) -> list[int]:
    """获取某分类自身及其所有子孙分类的 ID 列表"""
    all_cats = get_all_categories()
    children_map: dict[int | None, list[Category]] = {}
    for cat in all_cats:
        children_map.setdefault(cat.parent_id, []).append(cat)

    result = [category_id]

    def _collect(pid: int):
        for cat in children_map.get(pid, []):
            result.append(cat.id)
            _collect(cat.id)

    _collect(category_id)
    return result


def get_children(parent_id: int) -> list[Category]:
    session = get_session()
    try:
        results = session.query(Category).filter(
            Category.parent_id == parent_id
        ).order_by(Category.sort_order, Category.name).all()
        session.expunge_all()
        return results
    finally:
        session.close()


def get_category_by_id(category_id: int) -> Category | None:
    session = get_session()
    try:
        return session.query(Category).get(category_id)
    finally:
        session.close()


def create_category(name: str, parent_id: int | None = None) -> Category:
    """新增分类"""
    session = get_session()
    try:
        level = 0
        if parent_id is not None:
            parent = session.query(Category).get(parent_id)
            if parent:
                level = parent.level + 1
        cat = Category(name=name, parent_id=parent_id, level=level)
        session.add(cat)
        session.commit()
        session.refresh(cat)
        logger.info("新增分类: %s (level=%d)", name, level)
        return cat
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def update_category(category_id: int, name: str) -> Category | None:
    session = get_session()
    try:
        cat = session.query(Category).get(category_id)
        if cat is None:
            return None
        cat.name = name
        session.commit()
        session.refresh(cat)
        logger.info("更新分类: id=%d name=%s", category_id, name)
        return cat
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def delete_category(category_id: int) -> bool:
    """删除分类（级联删除子分类）"""
    session = get_session()
    try:
        cat = session.query(Category).get(category_id)
        if cat is None:
            return False
        session.delete(cat)
        session.commit()
        logger.info("删除分类: id=%d", category_id)
        return True
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def ensure_category_path(path: str) -> Category:
    """确保分类路径存在（如 '电子元器件/电阻'），不存在则自动创建。返回叶子分类。"""
    parts = [p.strip() for p in path.split("/") if p.strip()]
    if not parts:
        raise ValueError("分类路径不能为空")

    session = get_session()
    try:
        parent_id = None
        current_cat = None
        for i, name in enumerate(parts):
            cat = session.query(Category).filter(
                Category.name == name,
                Category.parent_id == parent_id if parent_id else Category.parent_id.is_(None)
            ).first()
            if cat is None:
                cat = Category(name=name, parent_id=parent_id, level=i)
                session.add(cat)
                session.flush()
            parent_id = cat.id
            current_cat = cat
        session.commit()
        if current_cat:
            session.refresh(current_cat)
        return current_cat  # type: ignore[return-value]
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_category_tree() -> list[dict]:
    """获取完整分类树（嵌套字典格式）"""
    session = get_session()
    try:
        all_cats = session.query(Category).order_by(Category.sort_order, Category.name).all()
        cat_map: dict[int, dict] = {}
        for c in all_cats:
            cat_map[c.id] = {
                "id": c.id,
                "name": c.name,
                "parent_id": c.parent_id,
                "level": c.level,
                "children": [],
            }
        roots: list[dict] = []
        for c in all_cats:
            node = cat_map[c.id]
            if c.parent_id and c.parent_id in cat_map:
                cat_map[c.parent_id]["children"].append(node)
            else:
                roots.append(node)
        return roots
    finally:
        session.close()
