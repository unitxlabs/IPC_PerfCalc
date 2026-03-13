# IPC_PerfCalc - 快速上手与部署

## 1. 开发环境一键搭建（首次）
前置要求：
- Conda（用于 Python/SQLite）
- Node >= 20（推荐用 nvm，`frontend/.nvmrc` 为 20）

步骤：
```bash
# 1) Python 环境
conda create -n perf_calc -c conda-forge python=3.11 sqlite=3.51.2
conda activate perf_calc
pip install -r requirements.txt

# 2) 后端启动
uvicorn app.main:app --reload

# 3) 前端启动
cd frontend
nvm use            # 如果使用 nvm
npm install
npm run dev
```
访问：
- 前端：http://localhost:5173/
- 后端 API：http://localhost:8000/api/v1/...

说明：
- 前端会通过 `vite.config.ts` 代理 `/api` 到后端。
- 导入区默认隐藏，按 `Ctrl + Shift + Y` 可切换显示（状态存于本地存储）。

## 2. 构建镜像与本机部署（开发完成后）
一体化镜像会打包前端并由 FastAPI 提供静态页，访问端口为 3154。

### 2.1 使用 Compose
```bash
docker compose -f deploy/docker-compose.yml up --build
```
访问：
- 前端：http://localhost:3154/
- API：http://localhost:3154/api/v1/...

### 2.2 使用脚本
```bash
# 构建（默认 ipc-perfcalc:latest）
./scripts/build.sh

# 运行（默认端口 3154）
./scripts/run.sh
```
常用变量：
```bash
NO_CACHE=1 ./scripts/build.sh              # 强制无缓存构建
IMAGE_TAG=1.0 ./scripts/build.sh        # 指定镜像 Tag
IMAGE_TAG=1.0 ./scripts/run.sh          # 运行指定 Tag
HOST_PORT=3154 ./scripts/run.sh            # 修改映射端口
```

## 3. 分发产物（dist）在新机器部署
执行 `./scripts/build.sh` 后，会生成 `dist/`：
- `ipc-perfcalc_<tag>.tar`：镜像导出文件
- `ipc_perfcalc.db`：数据库快照（若项目根目录存在）
- `run_on_new_machine.sh`：一键导入并启动脚本

在新机器上使用（将 `dist/` 整个目录拷过去）：
```bash
cd dist
./run_on_new_machine.sh
```
可选变量：
```bash
IMAGE_NAME=ipc-perfcalc IMAGE_TAG=1.0 ./run_on_new_machine.sh
HOST_PORT=3154 CONTAINER_NAME=ipc-perfcalc ./run_on_new_machine.sh
DB_PATH=./ipc_perfcalc.db ./run_on_new_machine.sh
```

## 4. 镜像版本规范（推荐）
建议 Tag 命名：
- 阶段版：`phase1` / `phase2`
- 语义化：`v1.0.0` / `v1.1.0`
- 日期版：`2026.01.15`
- 候选版：`phase2-rc1`
