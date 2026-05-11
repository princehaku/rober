# Sprint 2026.05.12_09-10 Remote Cloud Backup Restore Drill - Tech Plan

## 状态

- 阶段：tech-plan
- 创建时间：2026-05-12 Asia/Shanghai
- Product Owner：`product-okr-owner`
- 主责 Engineer：`full-stack-software-engineer`
- 支撑 Engineer：`robot-software-engineer`
- 证据边界：目标为 `software_proof_docker_backup_restore_drill`

## 用户价值和产品北极星

技术计划服务于一个产品目标：在真实云、4G、OSS/CDN、生产 DB/queue 和多实例接入前，用 Docker-only 环境先证明 SQLite-backed relay state 可以被备份、恢复，并在恢复后保留 commands/status/acks 的既有语义。北极星仍是普通手机用户通过云端入口使用小车；本轮只做 backup/restore/DR drill 软件证明，不做真实生产灾备。

## OKR 映射

| Objective/KR | 技术抓手 |
| --- | --- |
| O6 KR1 | Restore 后保持 `trashbot.remote.v1` commands/status/ack API shape 和 command envelope 语义不变。 |
| O6 KR2 | 为后续 staging/production 提供单实例 backup/restore drill 软件证据，但不声明生产云 ready。 |
| O6 KR5 | Backup artifact、restore output 和 preflight 保持 secret-safe，不泄露 bearer、Authorization header 或敏感路径。 |
| O6 KR6 | 对 artifact missing、schema mismatch、checksum/metadata mismatch、restore failure 输出 phone-safe blocked/warning。 |
| O5 支撑 | 输出用户可读 restore status/retry hint，不做正式 UI。 |

## 技术方案

### Task A - Backup/restore drill implementation

- Owner：`full-stack-software-engineer`
- 目标：
  - 在 independent relay 或相邻 CLI 中增加 SQLite state backup artifact 生成能力。
  - 增加 restore drill：从 backup artifact 恢复到新的 SQLite state path。
  - 验证 restore 后 commands/status/acks 仍按既有 HTTP shape 可读。
  - 在 preflight 或 CLI gate 中输出 backup/restore/DR drill 状态。
  - 输出 `evidence_boundary=software_proof_docker_backup_restore_drill` 或等价边界。
- 允许改动范围：
  - `src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py`
  - `src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py`
  - `scripts/remote_cloud_relay_docker_smoke.sh`
  - `docs/product/cloud_4g_infrastructure.md`
  - `sprints/2026.05.12_09-10_remote-cloud-backup-restore-drill/tech-done.md`
- 接口影响：
  - 可新增内部 helper、CLI 参数、artifact format/version 和 preflight check 字段。
  - 不改变 `POST /commands`、robot poll、status、ack 的既有 response shape。
  - 不暴露 `/cmd_vel`、ROS topic、串口、baudrate、WAVE ROVER 参数或底层速度入口。
- 必须覆盖的恢复场景：
  - command 入队后生成 backup，restore 到新 state，robot 可按既有语义取到 command。
  - status 写入后生成 backup，restore 到新 state，phone/API 可读最近 status。
  - ack 写入后生成 backup，restore 到新 state，ACK/cursor 语义保持。
  - artifact 缺失、schema mismatch、metadata/checksum 不匹配或 restore 失败时输出 phone-safe reason。

### Task B - Remote bridge compatibility acceptance

- Owner：`robot-software-engineer`
- 目标：
  - 只做 remote bridge compatibility acceptance，不参与 backup/restore 实现。
  - 确认 status-command-ack 主路径未变。
  - 确认 cursor/ACK conservative semantics 未变：ACK 不是 delivery result，auth/cloud/malformed/restore blocked 失败不推进 cursor，不触发本地 action。
  - 确认 backup/restore/preflight blocked 不改变 robot polling 主路径。
- 允许改动范围：
  - `src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py`
  - `src/ros2_trashbot_behavior/test/test_remote_bridge.py`
  - 如确有必要：`src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge_protocol.py`
  - 如确有必要：`src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge.py`
  - `sprints/2026.05.12_09-10_remote-cloud-backup-restore-drill/tech-done.md`
- 接口影响：
  - 不改变 robot polling 主路径。
  - 不把 backup/restore drill 写成 robot delivery success。

### Task C - Product acceptance and OKR closure

- Owner：`product-okr-owner`
- 目标：
  - 在 Engineer 验收后更新 `OKR.md` 和 sprint 收口文档。
  - O6 只能保守小幅提升。
  - O5/O1/O2/O3/O4 不提升。
  - `side2side_check.md` 和 `final.md` 必须记录 evidence boundary、验证命令、缺口和不得宣称事项。
- 允许改动范围：
  - `OKR.md`
  - `sprints/2026.05.12_09-10_remote-cloud-backup-restore-drill/tech-done.md`
  - `sprints/2026.05.12_09-10_remote-cloud-backup-restore-drill/side2side_check.md`
  - `sprints/2026.05.12_09-10_remote-cloud-backup-restore-drill/final.md`
- 接口影响：
  - 无代码接口影响。
  - 只做产品证据边界和 OKR 收口。

## 执行顺序和 team 分工

1. `full-stack-software-engineer` 单线主责 Task A，因为 backup artifact、restore drill、preflight state check 和 phone-safe output 共享实现边界。
2. `robot-software-engineer` 执行 Task B compatibility acceptance；如 Task A 输出接口不稳定，先只读复核协议事实，待接口稳定后运行验收命令。
3. `product-okr-owner` 在 Task A/B 验收后执行 Task C，保守更新 OKR 和 sprint 收口。
4. 如果 backup/restore drill 因生产 DB/queue、多实例、真实云或真实灾备缺失返回 warning/blocked，Engineer 需要记录阻断原因和剩余证据，不要把 warning/blocked 改成 production pass。

## 验收命令

执行同学必须按“测试只围栏”原则运行 targeted checks，不做宽泛回归矩阵。具体子命令可由 Engineer 按实际 CLI 落点收敛，但验收必须覆盖以下最小面。

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
  scripts/remote_cloud_relay_docker_smoke.sh \
  docs/product/cloud_4g_infrastructure.md \
  sprints/2026.05.12_09-10_remote-cloud-backup-restore-drill/tech-done.md
```

### Backup/restore smoke

具体命令由 Engineer 根据实际 gate/backend 入口写入 `tech-done.md`，但必须覆盖：

```text
1. Set TRASHBOT_REMOTE_CLOUD_STATE_BACKEND=sqlite and explicit SQLite state path.
2. Create command, status, and ack records through existing relay API or state helper.
3. Generate backup artifact from the populated SQLite state.
4. Restore backup artifact into a fresh SQLite state path.
5. Start or instantiate relay with the restored state path.
6. Confirm robot poll returns the restored command under existing shape.
7. Confirm latest status remains readable under existing shape.
8. Confirm ACK/cursor semantics remain conservative after restore.
9. Run preflight or CLI gate and confirm evidence_boundary=software_proof_docker_backup_restore_drill or equivalent.
10. Confirm production DB/queue, multi-instance consistency, production backup policy, and real disaster recovery remain warning/blocked.
11. Confirm output does not contain bearer token, Authorization header, OSS secret, root password, raw local state path, ROS topic, serial port, baudrate, WAVE ROVER parameters or /cmd_vel.
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
  sprints/2026.05.12_09-10_remote-cloud-backup-restore-drill/tech-done.md
```

### Product plan document validation

```bash
ls -la sprints/2026.05.12_09-10_remote-cloud-backup-restore-drill
```

```bash
git diff --check -- \
  sprints/2026.05.12_09-10_remote-cloud-backup-restore-drill/pre_start.md \
  sprints/2026.05.12_09-10_remote-cloud-backup-restore-drill/prd.md \
  sprints/2026.05.12_09-10_remote-cloud-backup-restore-drill/tech-plan.md
```

## 验收标准

- SQLite state 可生成 backup artifact。
- Backup artifact 可 restore 到新的 SQLite state path。
- Restore 后 command/status/ack HTTP API shape 不变。
- Robot remote bridge status-command-ack 和 cursor/ACK conservative semantics 不退化。
- Preflight 或 CLI gate 能识别 backup/restore drill，并输出 `software_proof_docker_backup_restore_drill` 或等价边界。
- Preflight 或 CLI gate 明确生产 DB/queue、多实例一致性、生产备份策略、真实灾备和真实云仍缺，不把 drill pass 写成 production ready。
- `tech-done.md` 写清实际改动、命令输出、失败定位和剩余风险。
- 验收后 `OKR.md` 只允许 O6 保守小幅提升，O5/O1/O2/O3/O4 不提升。

## 风险和回滚边界

- 若 backup/restore drill 需要真实云资源才能运行，说明设计过重；应回退为 Docker-only 可运行、真实资源缺失时 warning/blocked 的实现。
- 若 restore 改变 HTTP API shape，必须优先恢复兼容性，再继续验收。
- 若 ACK/cursor 被解释成真实 delivery result，必须纠正为 command envelope evidence。
- 若 backup artifact 或 preflight 输出泄露 secret、原始 state path 或硬件/ROS 底层细节，必须优先修复脱敏。
- 若 tests 变宽或耗时过高，应收缩到 remote cloud relay、backup/restore drill 和 robot compatibility 围栏。
