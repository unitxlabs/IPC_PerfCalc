# IPC Performance Calculation Platform - Engineering Requirements Document

## 1. Project Introduction
### Overview
本项目旨在构建一个 **IPC 性能数据记录与计算平台**。该平台通过统一的性能公式、参数模型与历史数据接口，帮助解决方案（SA）及工程团队快速获得 IPC 在不同场景（如不同像素、模型数量、相机数量等）下的性能表现（MP/s）。

平台核心定位为 **“数据查询 + 后端计算驱动的工程工具”**。不仅支持基于公式的快速估算，还支持对真实测试数据的查询与回溯，形成“计算为主，测试为辅”的数据闭环。

### Goals
*   **性能计算**：基于后端集成的数学模型，输入场景参数（分辨率、模型数等），实时计算理论性能。
*   **数据查询**：提供对历史实测数据的结构化查询，验证理论值的准确性。
*   **方案推荐**：根据计算结果推荐最佳 IPC 选型（Core/Standard/Pro）。
*   **数据积累**：记录每一次查询与测试结果，为修正公式系数提供数据支撑。

---

## 2. Architectural Overview
### High-Level Architecture
系统采用典型的前后端分离架构，但侧重于后端逻辑。

*   **Frontend (Vue 3)**:
    *   轻量级 UI，主要负责表单输入（参数配置）和结果展示（表格/图表）。
    *   **Component Library**: 使用 **Ant Design Vue**。
        *   *Reasoning*: 提供成熟且丰富的表格(Table)与表单(Form)组件，非常契合工程工具“重数据展示、重参数录入”的特性，能显著提升开发效率。
    *   不包含复杂业务逻辑，仅做数据透传与渲染。
*   **Backend (FastAPI)**:
    *   **API Layer**: 处理前端请求，参数校验。
    *   **Calculation Engine**: 核心模块，封装性能计算公式 `Performance = f(...)`。
    *   **Data Service**: 负责数据的 CRUD 及查询过滤。
*   **Database (SQLite3)**:
    *   选用 SQLite 是基于**“查多写少”**的业务特性，且单文件数据库极易于在不同机器间**迁移**（Portable）。
    *   存储基准测试数据（Benchmark Data）。
    *   存储公式系数/模型版本（Model Versioning）。
    *   存储用户查询记录（Query Logs）。

### Technology Stack
*   **Frontend**: Vue 3, Ant Design Vue, Axios.
*   **Backend**: Python 3.10+, FastAPI, SQLAlchemy (ORM), Pydantic.
*   **Database**: SQLite 3.45+ (必需支持 JSONB，用于高效存储查询日志).
*   **Deployment**: Docker Compose (单机部署，易于迁移)。

---

## 3. Database Design
数据库设计核心在于存储“实测数据”以供查询，以及“模型参数”以供计算。

### 3.1. Tables

#### `ipc_models` (IPC 硬件规格表)
存储 Core, Standard, Pro 等硬件的基础属性。
*   `id` (PK)
*   `name` (e.g., "Core-2025")
*   `cpu_model` (e.g., "i7-13700K", "Ultra2 245K")
*   `RAM` (e.g., "64G")
*   `gpu_info` (e.g., "NVIDIA GeForce RTX 4080")
*   `SSD` (e.g., '2T+2T')
*   `HDD` (e.g., "8T", "-")

#### `test_records` (实测性能数据表)
存储历史测试或基准测试的真实数据，用于查询比对。
*   `id` (PK)
*   `ipc_model_id` (FK)
*   `software_version` (软件版本, e.g., "5.21")
*   `resolution_mp` (照片像素: 5, 12, 24)
*   `camera_count` (相机数量)
*   `model_count` (模型数量， 默认为2)
*   `segments_count` (缺陷数量， 默认为50)
*   `image_count` (照片数量, 可选)
*   `save_image` (是否存图, Boolean)
*   `measured_perf_mps` (实测性能 MP/s)
*   `ex_perf_mps` (极限性能 MP/s)
*   `created_at`

#### `formula_coefficients` (计算公式系数表)
支持公式版本管理，允许后端动态调整计算参数而无需修改代码。
*   `id` (PK)
*   `version_tag` (e.g., "v1.0.0-optim-2025")
*   `param_key` (e.g., "base_overhead_ms", "infer_time_per_model_ms")
*   `param_value` (Float)
*   `is_active` (Boolean, 标记当前使用的计算参数)

#### `query_logs` (用户查询记录表)
记录用户输入的查询条件，用于后续分析高频场景。
*   `id` (PK)
*   `query_params` (JSONB, 存储所有输入参数)
*   `calculated_result` (JSONB, 存储计算结果)
*   `user_id` (Optional)
*   `created_at`

---

## 4. API and Services Design
后端是本系统的核心，主要暴露计算和查询两个能力的接口。

### 4.1. Core Calculation Logic (Backend Service)
计算引擎将实现文档中描述的逻辑：
```python
# 伪代码逻辑
def calculate_performance(params: CalculationParams, formula_config: dict):
    # Case 1: Inference dominanted
    if single_infer_time >= remaining_task_time:
        total_time = startup_time + (single_infer_time * count) + end_time
    # Case 2: Pipeline parallel
    else:
        total_time = startup_time + first_infer_time + (remaining_task_time * count)
    
    mp_s = total_pixels / total_time
    return mp_s
```

### 4.2. API Endpoints

#### Calculation
*   `POST /api/v1/calculate`
    *   **Input**: `software_version`, `ipc_model`, `resolution`, `model_count`, `camera_count`, `postproc_time`, etc.
    *   **Logic**: 加载当前激活的 `formula_coefficients`，运行计算函数。
    *   **Output**: 
        ```json
        {
          "predicted_mps": 25.5,
          "recommended_ipc": "IPC-Standard",
          "details": "Based on Formula v1.0..."
        }
        ```

#### Data Query
*   `POST /api/v1/records/search`
    *   **Input**: 筛选条件（支持范围查询，如模型数量 1-5），支持多选 IPC 型号和版本。
    *   **Output**: 符合条件的 `test_records` 列表。

#### Data Import
*   `POST /api/v1/records/import`
    *   **Input**: multipart/form-data，字段 `file`（CSV，逗号分隔），列顺序示例：`IPC型号, 分辨率(MP), 相机数量, 照片数量, 是否存图, 版本, 性能(MP/s), 极限性能(MP/s), （可选备注，当前导入忽略）`
    *   **Logic**: 自动补充不存在的 `ipc_models`，写入 `test_records`；忽略空行/表头；返回导入统计（插入/跳过/错误）。
    *   **Output**:
        ```json
        {
          "inserted": 18,
          "skipped": 2,
          "errors": ["行12: 缺少必填字段 name/performance -> ..."]
        }
        ```

#### Metadata
*   `GET /api/v1/options`
    *   获取前端下拉框的选项（IPC型号列表、支持的分辨率枚举等），由后端配置驱动。

---

## 5. User Interface Design
前端页面保持极简，定位于“工程控制台”。

### Page 1: Benchmark Data Browser (MVP Focus)
*   **Layout**: 顶部搜索栏，底部 Data Table。
*   **Search Filters**:
    *   IPC Model (Multi-select)
    *   Resolution (Select)
    *   Camera Count (Select, 1-8)
    *   Model Count (Select, 2-10, only 2 is available now)
*   **Table Columns**: IPC Model | Version | Res | Cameras | Models | Perf (MP/s) | Date.
*   **Feature**: 支持导出 CSV（方便工程师二次分析）。

### Page 2: Performance Calculator (Phase 2)
*   **Layout**: 左侧输入面板，右侧结果面板。
*   **Inputs (Form)**:
    *   Dropdown: IPC Model (Core/Standard/Pro)
    *   Dropdown: Resolution (5MP/12MP/24MP)
    *   Number Input: Model Count (2-10)
    *   Number Input: Camera Count
    *   Number Input: Post-processing time (ms)
*   **Action**: "Calculate" Button.
*   **Output**: 
    *   显示计算出的 MP/s。
    *   显示是否存在“性能瓶颈”警告（如内存不足风险）。

---

## 6. Implementation Plan (Solo Dev)
鉴于单人开发，采用迭代开发模式，优先解决“查询现有数据”的痛点：

### Phase 1: MVP (Data Query & DB)
*   **DB**: 初始化 SQLite 数据库文件，设计并创建 `test_records` 和 `ipc_models` 表。
*   **Backend**: 搭建 FastAPI 框架，实现 `/records/search` 和 `/options` 接口。
*   **Frontend**: 构建 Vue 项目，实现“测试数据查询”页面（Page 1）。
*   **Goal**: 快速上线一个可用的“IPC 性能数据库”，供团队查询已有的基准测试结果。

### Phase 2: Calculation Engine (Formula)
*   **Backend**: 实现核心计算引擎，封装 `Performance = f(...)` 公式。
*   **Frontend**: 增加“性能计算器”页面（Page 2），调用 `/calculate` 接口。
*   **Goal**: 在查询不到现成数据时，提供理论计算值作为参考。

### Phase 3: Formula Config & Optimization
*   **DB**: 引入 `formula_coefficients`。
*   **Backend**: 将计算逻辑改为读取 DB 配置，支持热更新参数。
*   **Goal**: 提高系统灵活性，无需改代码即可调整模型参数。

---

## 7. Design Considerations
*   **Scalability**: 虽然目前是单人工具，但采用 FastAPI + SQLite 的标准结构，未来若需要对接自动化测试平台（Jenkins/Airflow）自动写入测试数据，接口层非常容易扩展。
*   **Deployment**: 使用 Dockerfile + docker-compose.yml 一键拉起所有服务，方便在内网服务器或个人电脑上运行。
*   **Data Integrity**: 虽然是内部工具，但对 `test_records` 的写入需要简单的鉴权（如 API Key），防止脏数据污染基准库。

