# O6 Cloud Archive API PRD

## 需求概述

本 sprint 建立 O6 MVP 的本地/mock file-backed archive API。它以 `trashbot.o6.cloud_archive.v1` 的响应形状，把任务记录、轨迹帧、事件和 evidence refs 存入本地状态文件，再通过列表和详情接口给 PC 端 / 后续 O7 功能消费。

本 PRD 只定义软件开发期的 O6-shaped 数据源，不定义真实云 DB、真实 OSS、生产部署、真实 4G、真实隧道、真实机器人控制或 HIL 验收。

## 目标用户

- PC 运营调试用户：需要从统一任务数据源查看历史任务、轨迹、事件和证据引用。
- O7 功能开发者：需要 route replay / labeling / voice / safe command 共用同一种 O6 archive task shape。
- Product / QA：需要能用本地 unittest 和状态文件证明接口语义，而不是靠手写 fixture 口头说明。

## 用户价值

1. 降低 O7 后续功能的返工：后续页面和 API 可以围绕同一个 O6 archive task shape 继续扩展。
2. 提高验证可信度：`POST /api/o6/archive/tasks` 写入后，`GET /api/o6/archive/tasks` 与详情接口能读回相同白名单摘要。
3. 保持安全边界：接口固定声明 `real_cloud_db_connected=false`、`real_oss_connected=false`、`robot_control_executed=false`，避免把 mock 能力包装成生产能力。

## 范围内功能

### P0：任务归档写入

- `POST /api/o6/archive/tasks` 接受小型 JSON payload。
- 必填字段：
  - `robot_id`
  - `task_id`
  - `started_at_ms`
  - `finished_at_ms`
  - `trajectory_frames[]`
  - `events[]`
- 可选字段：
  - `evidence_refs[]`
- 同一 `task_id` 采用 idempotent upsert：
  - 首次写入返回 created 语义。
  - 再次写入返回 updated 语义。
  - 不使用 `409 conflict` 阻断后续测试。

### P0：任务列表查询

- `GET /api/o6/archive/tasks` 返回当前 file-backed store 中的任务列表。
- 空 store 返回空列表，但仍必须返回完整 proof/status 边界。
- 列表摘要必须可供 O7 选择最新任务或指定任务。

### P0：任务详情查询

- `GET /api/o6/archive/tasks/<task_id>` 返回单个任务白名单详情。
- 未找到任务时 fail closed，不能返回随机 fixture 或 unsafe raw payload。

### P0：本地状态文件注入

- store 路径由 `TRASHBOT_O6_CLOUD_ARCHIVE_STATE` 注入。
- 未设置时可回落到系统临时目录默认文件。
- 该状态文件只是开发/测试用 local file-backed store，不是 production DB。

### P0：安全与边界字段

每个成功响应必须固定包含或等价表达：

- `schema=trashbot.o6.cloud_archive.v1`
- `source=local_mock_archive`
- `proof_status=not_proven`
- `safe_to_control=false`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `pc_only=true`
- `real_cloud_db_connected=false`
- `real_oss_connected=false`
- `connects_cloud_production=false`
- `robot_control_executed=false`

### P0：fail closed 输入保护

以下输入必须拒绝或安全降级：

- 坏 JSON。
- 缺少必填字段。
- `finished_at_ms < started_at_ms`。
- 数组过大。
- 包含 `Authorization`、`Bearer`、`token`、`/cmd_vel`、串口路径、`baudrate`、traceback 或带凭证 URL 的 unsafe content。
- 请求中的敏感内容不得在响应中原样回显。

## 范围外功能

- 不证明真实云 DB 接通。
- 不证明真实 OSS 接通。
- 不证明 production cloud、TLS、公网 4G 或隧道接入。
- 不实现真实标注提交、回滚或训练集导出。
- 不实现模型推理。
- 不发送 TTS、手控、寻路、停止或任何机器人控制命令。
- 不连接真实 WAVE ROVER、串口、Nav2、摄像头或硬件 HIL。

## KR 拆解

- KR-A：API contract 完整，三个 endpoint 均可通过单元测试证明。
- KR-B：file-backed store 可由 `TRASHBOT_O6_CLOUD_ARCHIVE_STATE` 指向临时测试文件，测试间互不污染。
- KR-C：idempotent upsert、空态、详情查询、缺字段、坏 JSON、unsafe content、数组上限均有测试。
- KR-D：`cloud-relay/README.md`、`docs/product/pc_tools_workstation.md`、`docs/interfaces/o6_cloud_archive_api.md` 同步说明 O6-shaped 数据源和 not-proven 边界。
- KR-E：最终收口前 `python3 -m unittest`、`py_compile`、`git diff --check` 通过；失败必须定位并修复后复跑。

## 优先级和验收口径

P0 必须全部满足后才允许进入代码提交判断：

- `POST /api/o6/archive/tasks` 可以写入最小 task。
- `GET /api/o6/archive/tasks` 可以列出刚写入 task。
- `GET /api/o6/archive/tasks/<task_id>` 可以返回该 task 详情。
- 响应和文档都包含 `TRASHBOT_O6_CLOUD_ARCHIVE_STATE`、`real_cloud_db_connected=false`、`real_oss_connected=false`。
- 测试命令包含并通过 `python3 -m unittest`。
- 文档明确该 API 只给 O7 route replay / labeling / voice / safe command 提供 O6-shaped 数据源，不证明真实云 DB/OSS/production。

P1 完成后才允许进入 sprint 收口：

- 工程实现更新 `tech-done.md`，列明实际改动、验证输出、失败定位和剩余风险。
- 若后续进入提交阶段，提交前必须先确认没有误改本 sprint 范围外文件或回滚用户已有改动。
- commit/push 只能在实现与验收通过后执行，且提交说明必须写明 evidence boundary 是 local/mock O6 archive software proof。

## 责任 Engineer

本轮执行交给 `full-stack-software-engineer` 单线闭环。原因：改动集中在 cloud relay HTTP API、PC/云文档和接口说明，不需要拆分给硬件、算法或 ROS2 平台并行 owner。

## 风险与阻塞

- 真实云后端仍是 O6 后续工作，不能把本地状态文件当生产数据库。
- evidence refs 只是对象引用形状，不证明 OSS 对象实际存在。
- O7 后续消费该接口时仍需各自页面或 API 做只读/提交/控制边界校验。
- CEO 要求最终 commit/push；本 PRD 阶段不提交，等工程实现、验证、验收文档齐全后再执行。
