# Sprint 2026.05.12_02-03 Remote 4G Command Loop - Tech Plan

## 状态

- 阶段：tech-plan
- 时间：2026-05-12 02:03 Asia/Shanghai
- 主目标：O6-first，Docker-only 本地 mock cloud / remote bridge command loop
- 执行策略：两条工程线可并行；文件范围互不重叠时并行启动 `full-stack-software-engineer` 和 `robot-software-engineer`
- 验证围栏：targeted tests、`py_compile`、Docker/local smoke、scoped `git diff --check`

## 架构方案

最小链路：

```text
phone/web/script
  -> mock cloud API
  -> GET /robots/{robot_id}/commands/next?last_ack_id=<id>
  -> robot remote_bridge outbound polling
  -> behavior-level contract or mock adapter
  -> POST /robots/{robot_id}/commands/{command_id}/ack
  -> POST /robots/{robot_id}/status
  -> phone/web/script reads status + ack
```

本轮只实现控制面，不实现图片大对象、OSS/CDN、生产账号、真实 SIM、真实云部署或真实 HIL。

## 任务分工

### Task A：mock cloud API and phone-safe entry

- Owner：`full-stack-software-engineer`
- 目标：提供本地 mock cloud / cloud API 和最小 phone-safe command/status/ack 入口。
- 允许改动范围：
  - `src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py`
  - `src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway.py`
  - `src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
  - `src/ros2_trashbot_behavior/test/test_operator_gateway_http.py`
  - `src/ros2_trashbot_behavior/test/test_operator_gateway_static.py`
  - `docs/product/remote_4g_mvp.md`
  - `sprints/2026.05.12_02-03_remote-4g-command-loop/tech-done.md`
- 禁止改动：
  - WAVE ROVER、ESP32、UART、hardware、vendor、Nav2、HIL 相关文件。
  - 大 UI 重构、账号体系、OSS/CDN 实现。

#### 实现要求

- 新增或扩展 mock cloud API endpoints：
  - `POST /robots/{robot_id}/commands`
  - `GET /robots/{robot_id}/commands/next?last_ack_id=<id>`
  - `POST /robots/{robot_id}/status`
  - `GET /robots/{robot_id}/status`
  - `POST /robots/{robot_id}/commands/{command_id}/ack`
  - `GET /robots/{robot_id}/commands/{command_id}/ack`
- command contract 对齐 `docs/product/remote_4g_mvp.md`：
  - `protocol_version = trashbot.remote.v1`
  - `id`
  - `type` in `collect` / `confirm_dropoff` / `cancel`
  - `expires_at`
  - `payload`
- 最小 phone-safe 入口可以是现有 operator HTTP route 或脚本调用口径，必须能完成：
  - submit command
  - read status
  - read ack
- 不暴露 `/cmd_vel`、serial port、baudrate、硬件参数或 ROS2 原始 topic 给普通用户入口。

#### 验收命令

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest src/ros2_trashbot_behavior/test/test_operator_gateway_http.py src/ros2_trashbot_behavior/test/test_operator_gateway_static.py
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway.py src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py
git diff --check -- src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway.py src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py src/ros2_trashbot_behavior/test/test_operator_gateway_http.py src/ros2_trashbot_behavior/test/test_operator_gateway_static.py docs/product/remote_4g_mvp.md sprints/2026.05.12_02-03_remote-4g-command-loop/tech-done.md
```

### Task B：remote bridge outbound polling

- Owner：`robot-software-engineer`
- 目标：实现 robot `remote_bridge` outbound polling 和 command -> behavior-level adapter -> ack/status loop。
- 允许改动范围：
  - `src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge.py`
  - `src/ros2_trashbot_behavior/test/test_remote_bridge.py`
  - `src/ros2_trashbot_bringup/launch/*.launch.py`
  - `docs/product/remote_4g_mvp.md`
  - `sprints/2026.05.12_02-03_remote-4g-command-loop/tech-done.md`
- 禁止改动：
  - WAVE ROVER、ESP32、UART、hardware、vendor、Nav2 fixed-route 主线、HIL evidence scripts。

#### 实现要求

- 如果 `remote_bridge.py` 不存在，可在允许范围内创建。
- bridge 配置项：
  - `robot_id`
  - `cloud_base_url`
  - `bearer_token`
  - `poll_interval_sec`
  - `last_ack_id`
- bridge 行为：
  - outbound HTTP polling 获取 next command。
  - validate command contract。
  - duplicate command id 复用 cached ack，不重复提交。
  - expired command ack 为 `ignored` 或 `failed`，并写明确 message。
  - malformed command ack 为 `failed`。
  - busy 时新 `collect` ack 为 `ignored`。
  - accepted command 调用 behavior-level contract 或 mock adapter。
  - post ack 和 status。
- 安全边界：
  - 不接受 remote `/cmd_vel`。
  - 不把 cloud command 直接映射为底盘速度。
  - cloud outage 不自动停止已经运行的本地任务；只记录 status / retry 风险。

#### 验收命令

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest src/ros2_trashbot_behavior/test/test_remote_bridge.py
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge.py
git diff --check -- src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge.py src/ros2_trashbot_behavior/test/test_remote_bridge.py src/ros2_trashbot_bringup/launch docs/product/remote_4g_mvp.md sprints/2026.05.12_02-03_remote-4g-command-loop/tech-done.md
```

### Task C：integration smoke and sprint closure

- Owner：`robot-software-engineer` 主责集成，`product-okr-owner` 收口。
- 目标：证明 mock cloud + remote bridge + phone-safe entry 的最小闭环。
- 允许改动范围：
  - `sprints/2026.05.12_02-03_remote-4g-command-loop/tech-done.md`
  - `sprints/2026.05.12_02-03_remote-4g-command-loop/side2side_check.md`
  - `sprints/2026.05.12_02-03_remote-4g-command-loop/final.md`
- 工程集成 smoke 允许使用 Task A/B 已改文件范围内的测试工具或临时 `/tmp` 数据，不新增硬件配置。

#### 集成验收命令

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest src/ros2_trashbot_behavior/test/test_operator_gateway_http.py src/ros2_trashbot_behavior/test/test_operator_gateway_static.py src/ros2_trashbot_behavior/test/test_remote_bridge.py
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway.py src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge.py
git diff --check -- src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway.py src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge.py src/ros2_trashbot_behavior/test/test_operator_gateway_http.py src/ros2_trashbot_behavior/test/test_operator_gateway_static.py src/ros2_trashbot_behavior/test/test_remote_bridge.py docs/product/remote_4g_mvp.md sprints/2026.05.12_02-03_remote-4g-command-loop/tech-done.md sprints/2026.05.12_02-03_remote-4g-command-loop/side2side_check.md sprints/2026.05.12_02-03_remote-4g-command-loop/final.md
```

## 子 Agent 启动要求

实现阶段必须由子 agent 执行：

- `full-stack-software-engineer`：Task A。
- `robot-software-engineer`：Task B 和 Task C 工程集成。
- `product-okr-owner`：Task C 产品收口与 OKR 证据边界。

若 Task A 和 Task B 文件范围保持不重叠，应在同一轮并行启动。若两者都需要修改 `docs/product/remote_4g_mvp.md` 或同一测试文件，指定 `robot-software-engineer` 做主责集成，`full-stack-software-engineer` 先完成 API/入口侧事实输出再由主责合并。

## 验收边界

本轮可以声明：

- O6 从文档 contract 进入 Docker-only mock cloud command loop 的软件证明阶段。
- phone-safe 最小入口可支持 O6 command/status/ack 验证。
- remote bridge 使用 outbound polling，不要求小车被公网 inbound 访问。

本轮不能声明：

- 真实云部署已完成。
- 真实 4G/SIM/弱网已验证。
- 生产鉴权、STS、OSS/CDN 图片链路已完成。
- O1/HIL、真实 WAVE ROVER、真实 route replay 已通过。
- command ack 等于垃圾送达完成。

## 本计划文档验收命令

当前 Product 计划阶段只运行 scoped markdown diff check：

```bash
git diff --check -- sprints/2026.05.12_02-03_remote-4g-command-loop/pre_start.md sprints/2026.05.12_02-03_remote-4g-command-loop/prd.md sprints/2026.05.12_02-03_remote-4g-command-loop/tech-plan.md
```
