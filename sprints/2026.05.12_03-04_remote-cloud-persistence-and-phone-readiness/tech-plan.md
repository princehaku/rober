# Sprint 2026.05.12_03-04 Remote Cloud Persistence And Phone Readiness - Tech Plan

## 状态

- 阶段：tech-plan
- 时间：2026-05-12 Asia/Shanghai
- Product Owner：`product-okr-owner`
- 执行模式：两条工程线可并行，文件范围互不重叠时同轮启动；跨接口口径由 `robot-software-engineer` 做最终 Docker-only integration smoke
- 验收边界：targeted unittest、`py_compile`、scoped `git diff --check`；不做 broad regression

## 架构方向

02-03 sprint 已证明 local mock command/status/ack 的最小闭环。本轮在不接真实云、不接真实硬件的前提下，把 local mock cloud 的控制面推进到生产前必须具备的可靠性语义：

```text
phone/mock client -> operator HTTP mock cloud -> persisted queue/status/ack
                  -> remote_bridge outbound polling + cursor recovery
                  -> behavior adapter status/ack
```

关键约束：

- ACK 只代表 robot bridge 接受或提交命令，不代表送达完成。
- status 才是 phone 用户判断当前机器人状态的主要入口。
- cursor/last ack 必须可解释、可恢复，不能依赖字符串排序。
- bearer/auth readiness 只能暴露配置状态和错误类别，不能泄露真实 token。

## Owner 和文件范围

### Task A：mock cloud 持久化队列与 phone-readable readiness/status

- Owner：`full-stack-software-engineer`
- 允许改动：
  - `src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py`
  - `src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway.py`
  - `src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
  - `src/ros2_trashbot_behavior/test/test_operator_gateway_http.py`
  - `src/ros2_trashbot_behavior/test/test_operator_gateway_static.py`
  - `src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
  - `docs/product/remote_4g_mvp.md`
  - `docs/product/mobile_user_flow.md`
- 不允许改动：
  - 硬件配置、vendor 文件、WAVE ROVER 参数
  - `OKR.md`
  - 本 sprint 的 `tech-done.md`、`side2side_check.md`、`final.md` 之外的旧 sprint 文档
- 交付：
  - command queue/status/ack 的最小持久化策略，可以通过参数或环境变量指定本地 proof path。
  - phone-readable remote readiness/status 字段，例如 `remote_ready`、`cloud_reachable`、`last_command_ack`、`status_stale`、`retry_hint`、`auth_state`。
  - 文档同步说明：该入口仍是 local/mock cloud proof，不是正式生产手机 UI。
- 接口影响：
  - 不改变既有 command/status/ack API path。
  - 新字段必须向后兼容，旧 client 可忽略。

### Task B：remote_bridge 跨重启 cursor/status 边界与 Docker-only integration smoke

- Owner：`robot-software-engineer`
- 允许改动：
  - `src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge.py`
  - `src/ros2_trashbot_behavior/test/test_remote_bridge.py`
  - 必要时核对或小改已存在 bringup launch 参数；如果没有明确现有入口，不新增硬件参数
  - `docs/product/remote_4g_mvp.md`
- 不允许改动：
  - 硬件配置、vendor 文件、WAVE ROVER 参数
  - `OKR.md`
  - 无关 nav/vision/hardware 包
- 交付：
  - `remote_bridge` cursor/last ack 状态边界可跨重启恢复，未知 cursor 和 terminal ack 行为可解释。
  - Docker-only integration smoke 验证 command id 顺序、duplicate ack、malformed/expired command、busy collect ignored 与 status post 不互相冒充。
  - 文档明确 ACK 与 delivery result 的区别。
- 接口影响：
  - 不暴露 `/cmd_vel`。
  - 不接受 inbound 直连 robot。
  - 只调用 behavior-level command adapter。

### Task C：产品收口和 OKR 边界

- Owner：`product-okr-owner`
- 本任务计划阶段不执行；实现完成后再做。
- 允许改动：
  - `sprints/2026.05.12_03-04_remote-cloud-persistence-and-phone-readiness/tech-done.md`
  - `sprints/2026.05.12_03-04_remote-cloud-persistence-and-phone-readiness/side2side_check.md`
  - `sprints/2026.05.12_03-04_remote-cloud-persistence-and-phone-readiness/final.md`
  - 必要时保守更新 `OKR.md`
- 收口要求：
  - 区分 `software_proof_docker_only`、真实云、真实 4G、真实 HIL。
  - O6 可按证据保守更新；O5 只记录 phone-readable support，不因非正式 UI 大幅提升。
  - O1/HIL 不升级。

## 子 Agent 启动要求

实现阶段必须按 AGENTS.md 固定结构派发：

1. `[角色 System Prompt]`：完整复制对应 `.codex/agents/<role>.toml` 的 `prompt`；如果外部 prompt 文件缺失，按 `AGENTS.md` 角色定义补齐。
2. `[本轮任务]`：包含本 tech-plan 中对应 Task 的目标和证据边界。
3. `[文件范围]`：严格使用上方允许改动列表。
4. `[验收命令]`：复制下方对应 fenced 命令。
5. `[输出要求]`：返回改动文件、命令输出、失败定位、剩余风险。

Task A 与 Task B 文件范围互不重叠时必须并行启动；如果实现时发现共享 `docs/product/remote_4g_mvp.md` 冲突，由 `robot-software-engineer` 做最终集成验证，`full-stack-software-engineer` 只补 phone/status 口径。

## 验收命令

### Product planning docs validation

```bash
git diff --check -- sprints/2026.05.12_03-04_remote-cloud-persistence-and-phone-readiness/pre_start.md sprints/2026.05.12_03-04_remote-cloud-persistence-and-phone-readiness/prd.md sprints/2026.05.12_03-04_remote-cloud-persistence-and-phone-readiness/tech-plan.md
```

### Task A fenced validation

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest src/ros2_trashbot_behavior/test/test_operator_gateway_http.py src/ros2_trashbot_behavior/test/test_operator_gateway_static.py src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway.py src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py
git diff --check -- src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway.py src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py src/ros2_trashbot_behavior/test/test_operator_gateway_http.py src/ros2_trashbot_behavior/test/test_operator_gateway_static.py src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py docs/product/remote_4g_mvp.md docs/product/mobile_user_flow.md
```

### Task B fenced validation

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest src/ros2_trashbot_behavior/test/test_remote_bridge.py
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge.py
git diff --check -- src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge.py src/ros2_trashbot_behavior/test/test_remote_bridge.py docs/product/remote_4g_mvp.md
```

### Final integration smoke after Task A + Task B

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest src/ros2_trashbot_behavior/test/test_operator_gateway_http.py src/ros2_trashbot_behavior/test/test_operator_gateway_static.py src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py src/ros2_trashbot_behavior/test/test_remote_bridge.py
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway.py src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge.py
git diff --check -- src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway.py src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge.py src/ros2_trashbot_behavior/test/test_operator_gateway_http.py src/ros2_trashbot_behavior/test/test_operator_gateway_static.py src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py src/ros2_trashbot_behavior/test/test_remote_bridge.py docs/product/remote_4g_mvp.md docs/product/mobile_user_flow.md
```

## 验收标准

- P0：重启/恢复路径不会让已 terminal ack 的 command 被重复执行。
- P0：未知 cursor 策略明确，不按字符串大小比较 command id。
- P0：phone-readable readiness/status 不泄露 token、串口、ROS topic 或硬件参数。
- P0：文档明确 local mock cloud、Docker-only proof、真实云和真实 4G 的边界。
- P0：所有执行结果写入 `tech-done.md`，side-by-side 验收写入 `side2side_check.md`，最终 OKR 影响写入 `final.md`。

## 风险和阻塞

- 本机无真实硬件、无 `/dev/ttyUSB0`，本轮不能产生 `hil_pass`。
- 本机无真实云、SIM、HTTPS/TLS、公网入口，本轮不能证明生产 4G 可用。
- 如果持久化路径写入 repo 内临时文件，必须确保不会把 runtime state、token 或敏感数据提交。
- 如果 Task A 和 Task B 同时修改 `docs/product/remote_4g_mvp.md`，最终集成时只保留一个一致 contract，不留下重复或冲突段落。
