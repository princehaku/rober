# Sprint 2026.05.12_07-08 Remote Cloud Production Preflight - Tech Plan

## 状态

- 阶段：tech-plan
- 创建时间：2026-05-12 Asia/Shanghai
- Product Owner：`product-okr-owner`
- 主责 Engineer：`full-stack-software-engineer`
- 支撑 Engineer：`robot-software-engineer`
- 证据边界：目标为 `software_proof_docker_preflight_gate`

## 用户价值和产品北极星

技术计划服务于一个产品目标：在真实云、4G、OSS/CDN 和生产 state store 接入前，用 Docker-only 环境先形成 production preflight gate，拦截配置缺失、凭证泄露、TLS/公网未准备、OSS/CDN 缺口、state store 不可写和 phone-safe 输出不合格的问题。北极星仍是普通手机用户通过云端入口使用小车；本轮只做上线前 gate，不做真实生产部署。

## OKR 映射

| Objective/KR | 技术抓手 |
| --- | --- |
| O6 KR1 | Gate 只检查和包装 `trashbot.remote.v1` deployment readiness，不改变 commands/status/ack 语义。 |
| O6 KR2 | 检查 public base URL、HTTPS/TLS、ingress/firewall、profile 和 service readiness。 |
| O6 KR3 | 检查 OSS bucket/region/prefix/credential mode，明确真实上传仍未验证。 |
| O6 KR4 | 检查 CDN base URL 和公开/私有数据边界，明确 CDN 不承担私有任务数据。 |
| O6 KR5 | 检查 secret provisioning、env 注入、`.env.example` 占位和输出脱敏。 |
| O6 KR6 | 输出 phone-safe blocked/warning/pass，支撑 graceful degradation 和后续手机提示。 |
| O5 支撑 | 输出用户可读 readiness/retry hint，不做正式 UI。 |

## 技术方案

### Task A - Production preflight gate

- Owner：`full-stack-software-engineer`
- 目标：
  - 为 remote cloud relay 增加可执行 production preflight gate，形态可以是脚本、CLI 子命令或 endpoint，但必须能在 Docker-only 主机运行。
  - Gate 汇总配置完整性、凭证注入、TLS/公网入口、OSS/CDN、state store 和 phone-safe 输出。
  - Gate 输出 machine-readable JSON 或等价结构，并提供 safe summary/retry hint。
- 允许改动范围：
  - remote cloud relay 相关实现文件。
  - remote cloud relay 相关 targeted tests。
  - remote cloud relay 相关 smoke/script 文件。
  - `docs/product/cloud_4g_infrastructure.md`
  - `docs/product/remote_4g_mvp.md`
  - `sprints/2026.05.12_07-08_remote-cloud-production-preflight/tech-done.md`
- 接口影响：
  - 可新增 preflight endpoint、CLI 或 script。
  - 不改变既有 command/status/ack response shape。
  - 不暴露 `/cmd_vel`、ROS topic、串口、baudrate、WAVE ROVER 参数或底层速度入口。

### Task B - Secret, TLS/public, OSS/CDN and state checks

- Owner：`full-stack-software-engineer`
- 目标：
  - Secret check：识别占位 token、缺失 token、真实 secret 泄露风险和 `.env.example` 边界。
  - TLS/public check：识别 Docker local、HTTP-only、TLS missing、public ingress missing、firewall unverified。
  - OSS/CDN check：校验 bucket、region、prefix、CDN base URL、credential mode 和私有数据边界。
  - State check：校验 state path 可写、恢复边界，并输出 file-backed proof 与 production DB/queue 的差距。
- 允许改动范围：
  - 与 Task A 相同，优先同一文件集内完成，避免扩大范围。
- 接口影响：
  - 输出可新增 checks 列表字段。
  - 失败输出必须 phone-safe，不回显 secret、raw traceback 或硬件/ROS 细节。

### Task C - Robot compatibility and conservative semantics fence

- Owner：`robot-software-engineer`
- 目标：
  - 验证 preflight gate 不改变 `RemoteCloudClient.post_status -> get_next_command -> post_ack` 兼容性。
  - 确认 ACK 仍只代表 command envelope 处理，不代表真实送达。
  - 确认 auth failed、malformed response、cloud unreachable、preflight blocked 不推进 cursor、不触发本地 action、不伪造 terminal ACK。
- 允许改动范围：
  - remote bridge protocol/client 相关 targeted tests。
  - 如确有必要，remote bridge protocol/client 实现文件。
  - 当前 sprint `tech-done.md`
- 接口影响：
  - 不改变 robot polling 主路径。
  - 不把 gate blocked 写成 robot delivery failure。

## 执行顺序和 team 分工

1. `full-stack-software-engineer` 单线主责 Task A/B，因为 gate、配置、凭证、TLS、OSS/CDN、state 和 phone-safe 输出共享实现边界。
2. `robot-software-engineer` 在 Task A/B 输出稳定后做 Task C compatibility fence；如实现文件不重叠，可并行做只读协议事实复核。
3. `product-okr-owner` 不写产品代码，只验收 O6/O5/O1-O4 边界、sprint 留档和后续 OKR 保守更新。
4. 若 gate 因真实云、TLS、OSS/CDN 或生产 DB 缺失返回 blocked，Engineer 需要记录阻断原因和剩余证据，不要把 blocked 改成 pass。

## 验收命令

执行同学必须按“测试只围栏”原则运行 targeted checks，不做宽泛回归矩阵。具体文件名可由 Engineer 按实现落点收敛，但验收必须覆盖以下最小面。

### Task A / Task B targeted validation

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
  sprints/2026.05.12_07-08_remote-cloud-production-preflight/tech-done.md
```

### Production preflight smoke

具体命令由 Engineer 根据实际 gate 入口写入 `tech-done.md`，但必须覆盖：

```text
1. Docker/local relay service uses explicit env placeholders.
2. Run preflight with local-only Docker config and confirm blocked/warning reasons.
3. Run preflight with missing/placeholder secret and confirm secret-safe output.
4. Run preflight with TLS/public ingress missing and confirm production-ready=false.
5. Run preflight with OSS/CDN placeholders and confirm no real object-link success is claimed.
6. Run preflight with state store writable/unwritable scenarios when feasible.
7. Confirm output contains evidence_boundary=software_proof_docker_preflight_gate or equivalent.
8. Confirm output does not contain bearer token, Authorization header, OSS secret, root password, ROS topic, serial port, baudrate, WAVE ROVER parameters or /cmd_vel.
```

### Task C robot compatibility validation

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
  sprints/2026.05.12_07-08_remote-cloud-production-preflight/tech-done.md
```

### Product preflight document validation

```bash
git diff --check -- \
  sprints/2026.05.12_07-08_remote-cloud-production-preflight/pre_start.md \
  sprints/2026.05.12_07-08_remote-cloud-production-preflight/prd.md \
  sprints/2026.05.12_07-08_remote-cloud-production-preflight/tech-plan.md
```

```bash
ls -la sprints/2026.05.12_07-08_remote-cloud-production-preflight
```

## 验收标准

- Gate 在 Docker-only 主机可执行，并能输出 `pass`、`blocked`、`warning` 或等价状态。
- Gate 能覆盖配置、凭证、TLS/公网、OSS/CDN、state store 和 phone-safe 输出。
- Gate blocked 能准确说明缺真实云、TLS、OSS/CDN、生产 DB 或生产 secret provisioning，且不被包装成生产通过。
- 敏感字段不进入输出、state file、示例 env 或手机可见文案。
- command/status/ack 和 robot client compatibility 不退化。
- `tech-done.md` 写清实际改动、命令输出、失败定位和剩余风险。
- 不把本轮结果写成真实云、真实 4G、OSS/CDN 实流量、HIL、Nav2/fixed-route、WAVE ROVER 或正式手机 UI 完成。

## 风险和回滚边界

- 若 preflight gate 需要真实云资源才能运行，说明设计过重；应回退为 Docker-only 可运行、真实资源缺失时返回 blocked 的实现。
- 若 gate 输出泄露 secret 或硬件/ROS 底层细节，必须优先修复脱敏，再继续功能验收。
- 若 gate 改坏 command/status/ack 契约，必须回滚接口影响，保留 preflight 为旁路检查。
- 若 tests 变宽或耗时过高，应收缩到 remote cloud relay、preflight gate 和 robot compatibility 围栏。
