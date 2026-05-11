# Sprint 2026.05.12_08-09 Remote Cloud SQLite State Proof - Tech Plan

## 状态

- 阶段：tech-plan
- 创建时间：2026-05-12 Asia/Shanghai
- Product Owner：`product-okr-owner`
- 主责 Engineer：`full-stack-software-engineer`
- 支撑 Engineer：`robot-software-engineer`
- 证据边界：目标为 `software_proof_docker_sqlite_state_store`

## 用户价值和产品北极星

技术计划服务于一个产品目标：在真实云、4G、OSS/CDN 和生产 DB/queue 接入前，用 Docker-only 环境先证明 independent relay 的 commands/status/acks 能在 SQLite-backed state store 下恢复。北极星仍是普通手机用户通过云端入口使用小车；本轮只做 SQLite state proof，不做真实生产部署。

## OKR 映射

| Objective/KR | 技术抓手 |
| --- | --- |
| O6 KR1 | 在不改变 `trashbot.remote.v1` commands/status/ack API shape 的前提下增加 SQLite state backend。 |
| O6 KR2 | 为后续 staging/production 提供单实例数据库形态 proof，但不声明生产云 ready。 |
| O6 KR5 | SQLite/preflight 输出保持 secret-safe，不泄露 bearer、Authorization header 或敏感路径。 |
| O6 KR6 | 对 backend missing/unwritable/recovery failure 输出 phone-safe blocked/warning，并保持 graceful degradation。 |
| O5 支撑 | 输出用户可读 readiness/retry hint，不做正式 UI。 |

## 技术方案

### Task A - SQLite-backed state store proof

- Owner：`full-stack-software-engineer`
- 目标：
  - 在 independent relay 中增加 SQLite-backed state store proof。
  - 支持 `TRASHBOT_REMOTE_CLOUD_STATE_BACKEND=sqlite` 或等价配置。
  - 覆盖 commands/status/acks 在 store reopen 或 relay restart 后可恢复。
  - 不改变既有 HTTP API shape，不改变 command/status/ack envelope 字段语义。
- 允许改动范围：
  - remote cloud relay 相关实现文件。
  - remote cloud relay 相关 targeted tests。
  - remote cloud relay 相关 smoke/script 文件。
  - `docs/product/cloud_4g_infrastructure.md`
  - `docs/product/remote_4g_mvp.md`
  - `sprints/2026.05.12_08-09_remote-cloud-sqlite-state-proof/tech-done.md`
- 接口影响：
  - 可新增内部 state store adapter、SQLite 文件配置、preflight check 字段。
  - 不改变 `POST /commands`、robot poll、status、ack 的既有 response shape。
  - 不暴露 `/cmd_vel`、ROS topic、串口、baudrate、WAVE ROVER 参数或底层速度入口。
- 必须覆盖的恢复场景：
  - command 入队后重启/reopen，robot 可按既有语义取到 command。
  - status 写入后重启/reopen，phone/API 可读最近 status。
  - ack 写入后重启/reopen，terminal ACK/cursor 语义保持。
  - SQLite path 缺失、不可写、初始化失败时输出 phone-safe reason。

### Task B - Remote bridge compatibility acceptance

- Owner：`robot-software-engineer`
- 目标：
  - 只做 remote bridge compatibility acceptance，不参与 state backend 实现。
  - 确认 status-command-ack 主路径未变。
  - 确认 cursor/ACK conservative semantics 未变：ACK 不是 delivery result，auth/cloud/malformed 失败不推进 cursor，不触发本地 action。
  - 确认 SQLite backend 和 preflight blocked 不改变 robot polling 主路径。
- 允许改动范围：
  - remote bridge protocol/client 相关 targeted tests。
  - 如确有必要，remote bridge protocol/client 实现文件。
  - 当前 sprint `tech-done.md`
- 接口影响：
  - 不改变 robot polling 主路径。
  - 不把 SQLite state proof 写成 robot delivery success。

### Task C - Product acceptance and OKR closure

- Owner：`product-okr-owner`
- 目标：
  - 在 Engineer 验收后更新 `OKR.md` 和 sprint 收口文档。
  - O6 只能保守小幅提升。
  - O5/O1/O2/O3/O4 不提升。
  - `side2side_check.md` 和 `final.md` 必须记录 evidence boundary、验证命令、缺口和不得宣称事项。
- 允许改动范围：
  - `OKR.md`
  - `sprints/2026.05.12_08-09_remote-cloud-sqlite-state-proof/tech-done.md`
  - `sprints/2026.05.12_08-09_remote-cloud-sqlite-state-proof/side2side_check.md`
  - `sprints/2026.05.12_08-09_remote-cloud-sqlite-state-proof/final.md`
- 接口影响：
  - 无代码接口影响。
  - 只做产品证据边界和 OKR 收口。

## 执行顺序和 team 分工

1. `full-stack-software-engineer` 单线主责 Task A，因为 SQLite backend、relay state adapter、preflight state check 和 phone-safe output 共享实现边界。
2. `robot-software-engineer` 执行 Task B compatibility acceptance；如 Task A 输出接口不稳定，先只读复核协议事实，待接口稳定后运行验收命令。
3. `product-okr-owner` 在 Task A/B 验收后执行 Task C，保守更新 OKR 和 sprint 收口。
4. 如果 SQLite proof 因生产 DB/queue、真实云或多实例缺失返回 warning/blocked，Engineer 需要记录阻断原因和剩余证据，不要把 warning/blocked 改成 production pass。

## 验收命令

执行同学必须按“测试只围栏”原则运行 targeted checks，不做宽泛回归矩阵。具体文件名可由 Engineer 按实现落点收敛，但验收必须覆盖以下最小面。

### Task A targeted validation

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest \
  src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py
```

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile \
  src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py
```

```bash
git diff --check -- \
  src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py \
  src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py \
  docs/product/cloud_4g_infrastructure.md \
  docs/product/remote_4g_mvp.md \
  sprints/2026.05.12_08-09_remote-cloud-sqlite-state-proof/tech-done.md
```

### SQLite state store smoke

具体命令由 Engineer 根据实际 gate/backend 入口写入 `tech-done.md`，但必须覆盖：

```text
1. Set TRASHBOT_REMOTE_CLOUD_STATE_BACKEND=sqlite and explicit SQLite state path.
2. Start or instantiate relay with SQLite backend.
3. Create command, reopen/restart store, confirm robot poll returns the same command under existing shape.
4. Post status, reopen/restart store, confirm latest status remains readable under existing shape.
5. Post ack, reopen/restart store, confirm ACK/cursor semantics remain conservative.
6. Run preflight with SQLite backend and confirm evidence_boundary=software_proof_docker_sqlite_state_store or equivalent.
7. Confirm preflight warns/blocks production DB/queue, multi-instance, backup and disaster-recovery gaps.
8. Confirm output does not contain bearer token, Authorization header, OSS secret, root password, ROS topic, serial port, baudrate, WAVE ROVER parameters or /cmd_vel.
```

### Task B robot compatibility validation

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest \
  src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py \
  src/ros2_trashbot_behavior/test/test_remote_bridge.py
```

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile \
  src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge_protocol.py \
  src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge.py
```

```bash
git diff --check -- \
  src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge_protocol.py \
  src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge.py \
  src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py \
  src/ros2_trashbot_behavior/test/test_remote_bridge.py \
  sprints/2026.05.12_08-09_remote-cloud-sqlite-state-proof/tech-done.md
```

### Product plan document validation

```bash
git diff --check -- \
  sprints/2026.05.12_08-09_remote-cloud-sqlite-state-proof/pre_start.md \
  sprints/2026.05.12_08-09_remote-cloud-sqlite-state-proof/prd.md \
  sprints/2026.05.12_08-09_remote-cloud-sqlite-state-proof/tech-plan.md
```

```bash
ls -la sprints/2026.05.12_08-09_remote-cloud-sqlite-state-proof
```

## 验收标准

- SQLite backend 在 Docker-only 主机可显式启用。
- commands/status/acks 在 SQLite backend 下能跨 store reopen 或 relay restart 恢复。
- Existing command/status/ack HTTP API shape 不变。
- Robot remote bridge status-command-ack 和 cursor/ACK conservative semantics 不退化。
- Preflight 能识别 SQLite backend，并输出 `software_proof_docker_sqlite_state_store` 或等价边界。
- Preflight 明确生产 DB/queue、多实例一致性、备份、灾备和真实云仍缺，不把 SQLite pass 写成 production ready。
- `tech-done.md` 写清实际改动、命令输出、失败定位和剩余风险。
- 验收后 `OKR.md` 只允许 O6 保守小幅提升，O5/O1/O2/O3/O4 不提升。

## 风险和回滚边界

- 若 SQLite backend 需要真实云资源才能运行，说明设计过重；应回退为 Docker-only 可运行、真实资源缺失时 warning/blocked 的实现。
- 若 SQLite proof 改变 HTTP API shape，必须优先恢复兼容性，再继续验收。
- 若 ACK/cursor 被解释成真实 delivery result，必须纠正为 command envelope evidence。
- 若 preflight 输出泄露 secret 或硬件/ROS 底层细节，必须优先修复脱敏。
- 若 tests 变宽或耗时过高，应收缩到 remote cloud relay、SQLite state proof 和 robot compatibility 围栏。
