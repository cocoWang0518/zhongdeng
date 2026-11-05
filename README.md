# shifanxitong

## 项目说明
本项目为 Flask + Vue 的一体化应用，提供模型预测、结果查询与可视化接口。

## 文档

- [API 文档](docs/API.md)

## Docker 单容器部署（Python + MariaDB）

### 1. 构建镜像
```bash
docker build -t shifanxitong:latest .
```

构建过程包含：
- 使用 `pnpm`（华为云镜像）构建 `frontend`，并将产物覆盖到 `web`
- 使用 `uv`（清华镜像）安装 Python 依赖

### 2. 运行容器
```bash
docker run -d \
  --name shifanxitong \
  -p 11232:11232 \
  -p 3306:3306 \
  -v /path/to/model:/app/model \
  -v /path/to/file:/app/file \
  -v /path/to/sql:/app/sql \
  -v /path/to/mysql-data:/var/lib/mysql \
  -v /path/to/.env:/app/.env:ro \
  shifanxitong:latest
```

建议在 `.env` 中配置：
```env
DB_MODE=internal
DB_HOST=127.0.0.1
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=db
DB_CHARSET=utf8mb4
```

`DB_MODE` 说明：
- `internal`：默认值，启动容器内置 MariaDB（Python 连接容器内数据库）
- `external`：不启动内置 MariaDB，仅启动 Flask，按 `DB_HOST/DB_PORT` 连接外部数据库

## 数据库初始化页面

访问 `/init/db` 可打开数据库初始化页面。页面会列出 `sql/*.sql` 脚本，并支持：
- 单独运行某个 SQL 文件
- 查看后台运行状态、结束时间与错误日志尾部
- 取消正在运行的 SQL 导入
- 清空数据库，即执行 `DROP DATABASE IF EXISTS` 后重新 `CREATE DATABASE`

注意：清空数据库为高风险操作，会删除当前库内全部数据，请仅在受控环境使用。

### 后台任务接口

`GET /init/db/api/scripts`

返回当前数据库名、SQL 文件列表与正在运行的任务。

`POST /init/db/api/jobs`

启动后台任务。同一时间只允许一个数据库任务运行，已有任务运行时会返回 `409`。

运行 SQL 文件：
```json
{
  "action": "run_sql",
  "filename": "db.sql"
}
```

清空数据库：
```json
{
  "action": "clear_db"
}
```

`GET /init/db/api/jobs/<job_id>`

查询任务状态。

`POST /init/db/api/jobs/<job_id>/cancel`

请求取消任务。SQL 导入会终止 MariaDB client 进程，已执行成功的语句不会回滚。
