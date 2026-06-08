# O6 Cloud Archive API Tech Plan

## 计划状态

本文件完成后，设计阶段可以交给 `full-stack-software-engineer` 执行实现、测试、修复和 `tech-done.md` 留档。Product owner 本阶段不写产品代码。

## OKR 最低优先级核对

1. 当前 `OKR.md` 4.1 节里完成度最低的 Objective 是 O6：云端核心后端，进度 0%。
2. 本 sprint 直接针对 O6。
3. 选择理由：O6 是 O7 route replay / labeling / voice / safe command 的数据前提。本轮先把 local/mock file-backed archive API 做成可测试的 O6-shaped 数据源，避免 O7 继续依赖散落 fixture；同时明确不证明真实 DB、OSS 或 production cloud。

## 技术目标

在 `remote_cloud_relay.py` 中保留并完善 O6 local/mock cloud archive API：

- `POST /api/o6/archive/tasks`
- `GET /api/o6/archive/tasks`
- `GET /api/o6/archive/tasks/<task_id>`

该 API 使用 `TRASHBOT_O6_CLOUD_ARCHIVE_STATE` 指定本地状态文件。响应 schema 为 `trashbot.o6.cloud_archive.v1`，source 为 `local_mock_archive`，并固定：

- `real_cloud_db_connected=false`
- `real_oss_connected=false`
- `connects_cloud_production=false`
- `robot_control_executed=false`

## 执行 owner

- 主责：`full-stack-software-engineer`
- 执行方式：单 owner 单线闭环。
- 不并行原因：文件范围集中在 cloud relay API、相关测试和接口/产品文档；没有硬件事实、算法模型或 ROS2 主链路并行依赖。

## 允许 Engineer 改动范围

工程实现阶段允许 full-stack engineer 改动：

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py`
- `onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py`
- `cloud-relay/README.md`
- `docs/product/pc_tools_workstation.md`
- `docs/interfaces/o6_cloud_archive_api.md`
- `sprints/2026.06.09_01-02_o6-cloud-archive-api/tech-done.md`
- 必要时更新 `sprints/2026.06.09_01-02_o6-cloud-archive-api/side2side_check.md` 和 `final.md`

不得改动：

- 与本 API 无关的 ROS2 硬件、Nav2、mobile、PC UI 源码。
- `OKR.md`，除非 Product owner 在 final 收口后另行明确要求更新。
- vendor 硬件资料。
- 用户已有无关改动。

## 接口影响

### Request

`POST /api/o6/archive/tasks` 必须接受最小任务归档 payload：

- `robot_id`
- `task_id`
- `started_at_ms`
- `finished_at_ms`
- `trajectory_frames[]`
- `events[]`
- `evidence_refs[]` 可选

### Response

所有 O6 archive 成功响应必须让调用方可以判断：

- 当前是 local/mock archive。
- 当前没有真实云 DB。
- 当前没有真实 OSS。
- 当前不会执行机器人控制。
- 当前 task list / detail 只包含白名单字段，不回显 unsafe raw payload。

### O7 消费边界

O7 route replay / labeling / voice / safe command 后续可以把该 API 当 O6-shaped 数据源消费，但每个 O7 consumer 仍需保留自己的安全禁用字段，例如 `playback_available=false`、`submit_enabled=false`、`tts_send_enabled=false`、`command_dispatch_enabled=false`，直到真实后端和验收材料齐全。

## 实现要求

1. File-backed store：
   - 从 `TRASHBOT_O6_CLOUD_ARCHIVE_STATE` 读取状态路径。
   - 未配置时回落到临时目录默认文件。
   - 测试必须用临时路径隔离状态。
2. Upsert：
   - duplicate `task_id` 使用 idempotent upsert。
   - 新建和更新都必须可从列表和详情读回。
3. Fail closed：
   - 坏 JSON、缺字段、时间倒序、数组过大和 unsafe content 必须拒绝。
   - `Authorization`、`Bearer`、`token`、`/cmd_vel`、串口路径、`baudrate`、traceback、credentials URL 不得进入响应白名单。
4. 文档同步：
   - `cloud-relay/README.md` 说明如何启用 local/mock O6 archive API。
   - `docs/product/pc_tools_workstation.md` 说明 O7 后续如何消费 O6-shaped 数据源。
   - `docs/interfaces/o6_cloud_archive_api.md` 说明 request、response、fail-closed、not-proven 边界。
5. 注释规范：
   - 新增代码技术注释使用中文。
   - 对复杂安全过滤和 mock/prod 边界解释"为什么"。

## 验收命令

Engineer 必须运行并在 `tech-done.md` 记录输出：

```bash
python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py
```

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=onboard/src/ros2_trashbot_behavior python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py
```

```bash
git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py cloud-relay/README.md docs/interfaces/o6_cloud_archive_api.md docs/product/pc_tools_workstation.md sprints/2026.06.09_01-02_o6-cloud-archive-api
```

Product 设计阶段验收命令：

```bash
test -f sprints/2026.06.09_01-02_o6-cloud-archive-api/pre_start.md && test -f sprints/2026.06.09_01-02_o6-cloud-archive-api/prd.md && test -f sprints/2026.06.09_01-02_o6-cloud-archive-api/tech-plan.md
```

```bash
rg -n "sprint_type: epic|OKR 最低优先级核对|POST /api/o6/archive/tasks|GET /api/o6/archive/tasks|TRASHBOT_O6_CLOUD_ARCHIVE_STATE|real_cloud_db_connected=false|real_oss_connected=false|python3 -m unittest" sprints/2026.06.09_01-02_o6-cloud-archive-api
```

## 执行 Agent Prompt 边界

交给 `full-stack-software-engineer` 时，prompt 必须包含：

- 本轮目标：完善 O6 MVP local/mock file-backed archive API，给 O7 route replay / labeling / voice / safe command 提供 O6-shaped 数据源。
- 文件范围：只允许改动本 tech-plan 的工程实现范围。
- 验收命令：复制本文件的三条 Engineer 验收命令。
- 输出要求：实际改动文件、验证日志、失败定位、剩余风险。
- 红线：不得把 local/mock 写成真实云 DB/OSS/production；不得发送机器人控制；不得提交未验证代码。

## 收口与提交规则

- 工程实现通过后，必须先补 `tech-done.md`。
- 若进入验收阶段，再补 `side2side_check.md` 和 `final.md`。
- CEO 要求结束后 git commit 和 push；只有当实现、测试、文档、验收和 final 收口全部通过后，才允许提交。
- commit message 必须明确这是 O6 local/mock cloud archive API software proof，不证明真实 cloud DB/OSS/production。

## 剩余风险

- 本轮不会解决真实隧道接入、真实公网 HTTPS、production DB/queue、OSS live traffic 或 4G/SIM。
- 本轮不会证明模型推理、真实标注提交、实时视频/RTC、ASR/TTS 或安全命令链路。
- 本轮不会 SSH 上车或验证真实硬件，因此不触发 vendor 硬件资料二次确认要求。
