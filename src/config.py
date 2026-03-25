"""全局配置管理"""

import shutil
import sys
from pathlib import Path

import yaml

# PyInstaller 打包后 sys._MEIPASS 指向临时解压目录
# 运行时数据（DB、日志等）应使用 exe 所在目录
if getattr(sys, "frozen", False):
    ROOT_DIR = Path(sys.executable).resolve().parent
    _BUNDLE_DIR = Path(sys._MEIPASS)  # type: ignore[attr-defined]
else:
    ROOT_DIR = Path(__file__).resolve().parent.parent
    _BUNDLE_DIR = ROOT_DIR

CONFIG_PATH = ROOT_DIR / "config.yaml"
CONFIG_EXAMPLE_PATH = _BUNDLE_DIR / "config.example.yaml"


def load_config() -> dict:
    """加载配置文件，不存在则从模板复制"""
    if not CONFIG_PATH.exists():
        if CONFIG_EXAMPLE_PATH.exists():
            shutil.copy(CONFIG_EXAMPLE_PATH, CONFIG_PATH)
        else:
            return _default_config()
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def save_config(config: dict):
    """保存配置文件"""
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        yaml.dump(config, f, allow_unicode=True, default_flow_style=False)


def _default_config() -> dict:
    """内置默认配置（兜底）"""
    return {
        "database": {"path": "data/mms.db"},
        "theme": "light",
        "backup": {
            "auto_backup": True,
            "max_backups": 10,
            "backup_dir": "data/backups",
        },
        "defaults": {
            "warning_threshold": 10,
            "unit": "个",
        },
        "log_level": "INFO",
    }
