# 物料管理系统 (Material Management System)

> 本地个人电子元器件物料管理工具，基于 PyQt6 + SQLAlchemy + SQLite 构建。  
> 毛玻璃 (Frosted Glass) 主题，简约高效。

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![PyQt6](https://img.shields.io/badge/GUI-PyQt6-green)
![License](https://img.shields.io/badge/License-MIT-yellow)

## 功能概览

| 模块 | 功能 |
|------|------|
| 📋 物料管理 | 物料 CRUD、搜索筛选、分类管理（树形结构）、低库存高亮、图片/数据手册管理 |
| 📊 库存中心 | 库存总览（统计卡片）、低库存预警列表 |
| 🔄 数据管理 | Excel/CSV 导入导出、导入模板下载、SQLite 数据库备份/恢复 |
| ⚙️ 系统设置 | 4 种主题切换（毛玻璃亮/暗、毛毡垫、大理石）、默认参数配置、日志级别设置 |

## 截图

> 启动后默认展示物料列表页面，左侧为树形导航栏。

## 技术栈

- **界面**: PyQt6（QTreeWidget 树形导航 + QStackedWidget 页面切换）
- **数据库**: SQLAlchemy 2.x ORM + SQLite
- **导入导出**: openpyxl (Excel) + csv (CSV)
- **配置**: PyYAML (config.yaml)
- **主题**: 4 种风格（毛玻璃亮色/暗色、毛毡垫、大理石）QSS 样式表
- **打包**: PyInstaller 6+ (one-folder) + PyArmor (源码加密)

## 项目结构

```
Material_Management_System/
├── main.py                    # 入口文件
├── config.example.yaml        # 配置模板
├── config.yaml                # 运行时配置（自动生成，不入库）
├── MMS.spec                   # PyInstaller 打包规格
├── build.ps1                  # PowerShell 打包脚本
├── build.bat                  # 双击一键打包
├── requirements.txt           # Python 依赖
├── data/                      # 运行时数据（不入库）
│   ├── mms.db                 # SQLite 数据库
│   ├── backups/               # 备份文件
│   └── logs/                  # 日志
└── src/
    ├── app.py                 # 应用工厂
    ├── config.py              # 配置加载
    ├── core/                  # 业务服务层
    │   ├── material_service.py
    │   └── category_service.py
    ├── db/                    # 数据库层
    │   ├── models.py          # 3 张 ORM 表 (Category, Material, OperationLog)
    │   └── database.py        # 引擎初始化 + 迁移
    └── ui/                    # 界面层
        ├── main_window.py     # 主窗口（树形导航 + 内容区）
        ├── pages/             # 6 个功能页面
        ├── dialogs/           # 弹窗（物料编辑）
        ├── widgets/           # 通用组件（Toast/SearchBar/TreeNav）
        └── theme/             # QSS 主题（毛玻璃/毛毡垫/大理石）
```

## 快速开始

### 环境要求

- Python 3.10+
- Windows 10/11（已测试）

### 安装与运行

```bash
# 1. 克隆仓库
git clone https://github.com/heiweilu/Material_Management_System.git
cd Material_Management_System

# 2. 创建虚拟环境
python -m venv .venv

# 3. 激活虚拟环境
# Windows PowerShell:
.\.venv\Scripts\Activate.ps1
# Windows CMD:
.\.venv\Scripts\activate.bat

# 4. 安装依赖
pip install -r requirements.txt

# 5. 启动应用
python main.py
```

首次启动会自动：
- 从 `config.example.yaml` 生成 `config.yaml`
- 创建 `data/mms.db` 数据库并初始化 8 张表
- 创建 `data/backups/`、`data/logs/` 等目录

### 打包为 EXE

**方式一：双击打包（推荐）**

直接双击项目根目录下的 `build.bat`，会自动执行 PyArmor 源码加密 + PyInstaller 打包，产物在 `dist/物料管理系统/` 目录。

**方式二：PowerShell 命令行**

```powershell
# 默认打包（PyArmor 加密 + ZIP）
.\build.ps1

# 跳过加密，仅打包
.\build.ps1 -NoEncrypt

# 清理旧产物后重新打包
.\build.ps1 -Clean

# 调试模式（保留控制台窗口）
.\build.ps1 -Debug

# 指定版本号
.\build.ps1 -Version "1.0.0"
```

打包产物：
```
dist/
├── 物料管理系统/        # 可执行文件目录
│   ├── 物料管理系统.exe
│   ├── config.example.yaml
│   └── ...
└── 物料管理系统_v0.1.0.zip  # 分发包
```

## 数据库表结构

| 表名 | 说明 |
|------|------|
| `category` | 物料分类（支持无限层级树形结构） |
| `material` | 物料主数据（名称、型号、封装、规格、库存、图片、数据手册等） |
| `operation_log` | 操作日志 |

## 配置说明

配置文件 `config.yaml` 支持以下选项：

```yaml
database:
  path: data/mms.db        # 数据库路径

theme: frosted_light          # 主题: frosted_light / frosted_dark / felt / marble

backup:
  auto_backup: true         # 启动时自动备份
  max_backups: 20           # 最大备份数
  backup_dir: data/backups  # 备份目录

defaults:
  warning_threshold: 10     # 默认预警阈值
  unit: 个                  # 默认计量单位

log_level: INFO             # 日志级别
```

## 导入模板

通过 **数据管理 → 导入导出** 页面可下载 Excel 导入模板，支持以下字段：

| 列名 | 必填 | 说明 |
|------|------|------|
| material_name | ✅ | 物料名称 |
| unit | ✅ | 计量单位 |
| model | | 型号 |
| package_type | | 封装（如 0805, SOP-8） |
| specification | | 规格 |
| warning_threshold | | 预警阈值（默认 10） |
| storage_location | | 存放位置 |
| category_path | | 分类路径（如 `电阻/贴片电阻`，自动创建） |
| remarks | | 备注 |

## License

MIT
