---
name: MMS_project
description: 本地个人物料管理系统 - 电子元器件管理专用（当前系统完整技术文档）
applyTo: "f:/生产力/DIY/Material_Management_System/**"
---

# 物料管理系统 · 项目文档

## 一、背景与目标

本系统服务于个人电子元器件物料管理，主管约50种电子元器件（电阻、电容、IC等）。
核心目标：替代手工Excel管理，提供物料信息集中管理、入库出库、库存预警、报表分析一体化工具。
纯本地运行，无需联网。

---

## 二、技术栈与运行环境

| 层次 | 技术 |
|---|---|
| UI 框架 | PyQt6（QTreeWidget 树形导航 + QStackedWidget 页面切换，支持 Light/Dark 主题） |
| ORM / DB | SQLAlchemy 2.x + SQLite（支持运行时 ALTER TABLE 迁移） |
| 图表 | matplotlib（FigureCanvas 嵌入 Qt） |
| 导入导出 | openpyxl（Excel）、csv |
| 配置 | PyYAML（config.yaml） |
| 打包 | PyInstaller 6+（one-folder 模式） |
| 加密 | PyArmor（源码加密保护） |
| 运行系统 | Windows，Python 3.12+，.venv 虚拟环境 |
| 仓库 | github.com/heiweilu/Material_Management_System，main 分支 |

---

## 三、项目目录结构

```
Material_Management_System/
├── main.py                          # 入口，启动 QApplication + 异常捕获
├── build.ps1                        # 一键打包脚本
├── MMS.spec                         # PyInstaller 打包规格
├── config.example.yaml              # 配置模板（随代码提交）
├── config.yaml                      # 运行时配置（gitignored）
├── requirements.txt                 # 依赖清单
├── README.md                        # 项目说明
├── data/
│   ├── mms.db                       # SQLite 数据库（gitignored）
│   ├── backups/                     # 数据库备份目录
│   └── logs/                        # 运行日志
├── src/
│   ├── __init__.py
│   ├── app.py                       # Application 工厂：加载配置→初始化DB→创建主窗口
│   ├── config.py                    # ROOT_DIR 定义、load_config / save_config
│   ├── core/                        # 业务逻辑层（Service）
│   │   ├── __init__.py
│   │   ├── material_service.py      # 物料 CRUD + 搜索
│   │   ├── category_service.py      # 分类树 CRUD + ensure_category_path
│   │   ├── inbound_service.py       # 入库操作 + 库存更新（事务）
│   │   ├── outbound_service.py      # 出库操作 + 库存校验 + 预警触发
│   │   ├── inventory_service.py     # 库存查询 + 预警扫描
│   │   ├── supplier_service.py      # 供应商 CRUD
│   │   ├── report_service.py        # 报表数据计算
│   │   ├── import_export_service.py # Excel/CSV 导入导出
│   │   └── backup_service.py        # 数据库备份与恢复
│   ├── db/
│   │   ├── __init__.py
│   │   ├── models.py                # SQLAlchemy ORM 模型（8张表）
│   │   └── database.py              # init_database + _run_sqlite_migrations
│   └── ui/
│       ├── __init__.py
│       ├── main_window.py           # 主窗口：树形侧边栏 + QStackedWidget
│       ├── pages/
│       │   ├── material_page.py     # 物料列表 + 搜索/筛选
│       │   ├── category_page.py     # 分类树管理
│       │   ├── inbound_page.py      # 入库操作 + 记录查询
│       │   ├── outbound_page.py     # 出库操作 + 记录查询
│       │   ├── inventory_page.py    # 库存总览 + 预警面板
│       │   ├── supplier_page.py     # 供应商管理
│       │   ├── report_page.py       # 报表统计 + 图表
│       │   ├── import_export_page.py # 导入导出
│       │   ├── backup_page.py       # 备份恢复
│       │   └── settings_page.py     # 系统设置
│       ├── dialogs/
│       │   ├── material_dialog.py   # 新增/编辑物料弹窗
│       │   ├── inbound_dialog.py    # 入库单详情弹窗
│       │   ├── outbound_dialog.py   # 出库单详情弹窗
│       │   └── supplier_dialog.py   # 新增/编辑供应商弹窗
│       ├── widgets/
│       │   ├── tree_nav.py          # 树形导航组件（QTreeWidget 封装）
│       │   ├── search_bar.py        # 搜索/筛选输入框
│       │   ├── toast.py             # 非阻塞 Toast 通知
│       │   └── stock_indicator.py   # 库存状态指示器
│       └── theme/
│           ├── style.qss            # Light 主题
│           └── dark.qss             # Dark 主题
├── .github/
│   ├── copilot-instructions.md
│   └── prompts/
│       └── MMS_project.prompt.md    # 本文件
└── .gitignore
```

---

## 四、数据模型（8张表）

### Material（物料主表）
```
id, material_code(UNIQUE), material_name, model, package_type, specification,
unit, current_stock, warning_threshold, category_id(FK), default_supplier_id(FK),
storage_location, datasheet_path, remarks, created_at, updated_at
```

### Category（分类树）
```
id, name, parent_id(自引用FK), level, sort_order, created_at, updated_at
```

### Supplier（供应商）
```
id, supplier_name(UNIQUE), contact_person, phone, email, address, website,
status(active/inactive), remarks, created_at, updated_at
```

### InboundOrder（入库单表头）+ InboundDetail（入库明细）
```
InboundOrder: id, inbound_no(UNIQUE), supplier_id(FK), inbound_date, remarks, created_at
InboundDetail: id, inbound_id(FK), material_id(FK), quantity, unit_price, remarks
```

### OutboundOrder（出库单表头）+ OutboundDetail（出库明细）
```
OutboundOrder: id, outbound_no(UNIQUE), outbound_date, recipient, remarks, created_at
OutboundDetail: id, outbound_id(FK), material_id(FK), quantity, remarks
```

### OperationLog（操作日志）
```
id, operation_type, target_type, target_id, description, created_at
```

---

## 五、树形导航结构

```
🏭 物料管理系统
├── 📋 物料管理
│   ├── 物料列表        → MaterialPage
│   └── 分类管理        → CategoryPage
├── 📥 入库管理          → InboundPage（QTabWidget: 新建入库单 | 入库历史）
├── 📤 出库管理          → OutboundPage（QTabWidget: 新建出库单 | 出库历史）
├── 📊 库存中心
│   ├── 库存总览        → InventoryPage（统计卡片 + 预警高亮表格）
│   └── 报表统计        → ReportPage（matplotlib 图表）
├── 🏢 供应商管理        → SupplierPage
├── 🔄 数据管理
│   ├── 导入导出        → ImportExportPage
│   └── 备份恢复        → BackupPage
└── ⚙️ 系统设置          → SettingsPage
```

---

## 六、编码规范与约定

1. **文件编码**：UTF-8，Windows 换行
2. **Python 版本特性**：使用 `X | Y` 类型注解（Python 3.10+）
3. **配置访问**：通过 `self.config` dict 传递，不从磁盘重复读
4. **Toast 通知**：轻量交互反馈用 `Toast(self, "消息", "success|warning|error")`
5. **日志**：使用 `logging.getLogger(__name__)`，日志文件 `data/logs/`
6. **样式**：QSS 集中在 `theme/style.qss` 和 `theme/dark.qss`
7. **数据库迁移**：所有 schema 变更通过 `database.py` 的 `_run_sqlite_migrations()` 函数
8. **事务安全**：入库/出库操作必须在数据库事务中完成，失败时回滚

---

## 七、打包发布

```powershell
.\build.ps1                      # 普通打包
.\build.ps1 -Version "1.0.0"    # 指定版本
.\build.ps1 -Clean               # 清理后重新打包
.\build.ps1 -Debug               # 保留控制台窗口
.\build.ps1 -NoZip               # 不生成 ZIP
```

产物：`dist/物料管理系统/` + ZIP 分发包。打包排除 data/ 和 config.yaml。

---

## 八、版本历史

| 版本 | 核心变更 |
|---|---|
| v0.1.0 | Phase 1: 项目骨架、DB 模型、配置管理、树形导航 UI 框架、所有页面骨架 |
