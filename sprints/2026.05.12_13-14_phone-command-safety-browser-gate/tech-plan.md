# Sprint 2026.05.12_13-14 Phone Command Safety Browser Gate - Tech Plan

## 状态

- 阶段：tech-plan
- Product Owner：`product-okr-owner`
- 主责 Engineer：`full-stack-software-engineer`
- 兼容性围栏：`robot-software-engineer`
- 计划结论：进入 implementation 时并行派 Full-stack 和 Robot；Full-stack 负责实现和 UI/API 围栏，Robot 只做 command/status/ack 兼容性验证。

## 技术方案

在现有 `operator_gateway` 本地 phone-first HTML、`/api/status.phone_readiness`、`remote_readiness`、`action_permissions` 和 diagnostics summary 上增加 command safety/browser gate。核心不是新增大量测试，而是让用户触点的按钮状态直接消费 readiness 结论。

建议实现形态：

- 在 `/api/status.phone_readiness` 或 operator 页面派生一个明确的 command safety summary，例如 `command_safety` 或等价结构。
- Start/Confirm/Cancel/Diagnostics 的可用性由 `phone_readiness.primary_state`、`can_continue`、`next_action`、`action_permissions`、`remote_readiness.degradation_state`、pending ACK、status freshness、manifest summary 共同决定。
- HTML 首屏只显示普通用户文案、按钮状态和下一步提示，不显示 raw JSON、ROS topic、serial、baudrate、`/cmd_vel`、OSS object key、checksum、本地路径或 secret。
- ACK 后状态必须保持在“命令已受理/等待执行结果”语义，不把 ACK 渲染成 delivery success。
- Diagnostics 可以保持可进入，但应解释当前阻断原因；不能因为 diagnostics 可用就让 Start/Confirm 变 green。
- Robot bridge API shape 不变；Robot worker 只验证 command/status/ack/cursor 没有退化。

## Owner 和并行派工

### Full-stack worker

角色：`full-stack-software-engineer`

允许改动范围：

- `src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway.py`
- `src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py`
- `src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`（仅当 diagnostics summary 需要补安全状态时）
- `src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py`（仅当复用 remote readiness/manifest helper 必须调整时）
- `src/ros2_trashbot_behavior/test/test_operator_gateway_http.py`
- `src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
- `src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py`（仅当 helper contract 变化）
- `docs/product/mobile_user_flow.md`
- `docs/product/remote_4g_mvp.md`
- `docs/product/cloud_4g_infrastructure.md`（仅当 O6 证据边界或 cloud wording 变化）
- `sprints/2026.05.12_13-14_phone-command-safety-browser-gate/tech-done.md`

必须交付：

- 按钮状态 gate：Start/Confirm/Cancel/Diagnostics。
- ACK != delivery success 的用户文案。
- `status_stale`、`command_pending`、`auth_failed`、`cloud_unreachable`、`malformed_response`、manifest `missing/invalid/stale` 场景的最小覆盖。
- targeted tests、py_compile、browser/API smoke 或等价最小可复查证据。
- 产品文档同步和 `tech-done.md`。

### Robot worker

角色：`robot-software-engineer`

允许改动范围：

- `src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py`（原则上只读或补兼容断言）
- `src/ros2_trashbot_behavior/test/test_remote_bridge.py`（原则上只读或补兼容断言）
- `sprints/2026.05.12_13-14_phone-command-safety-browser-gate/tech-done.md`（只追加验证片段，或交给 Full-stack 汇总）

必须交付：

- remote bridge command/status/ack/cursor compatibility fence 结果。
- 如发现退化，定位到具体 command/status/ack/cursor 行为，并交回 Full-stack 或 Robot 按职责修复。

### Product owner

允许改动范围：

- `sprints/2026.05.12_13-14_phone-command-safety-browser-gate/side2side_check.md`
- `sprints/2026.05.12_13-14_phone-command-safety-browser-gate/final.md`
- `OKR.md`（仅在实现、验收和 final 证据充分后更新；本轮规划阶段不更新）

## 接口影响

- `/api/status` 可以新增 `phone_readiness.command_safety` 或等价字段；旧客户端可忽略。
- `/api/status.action_permissions` 语义不得破坏；新增 gate 应优先组合现有字段。
- `/api/diagnostics` 可以补充 phone-safe blocking reason，但不得输出 secret、raw traceback 或硬件参数。
- `/api/collect`、`/api/dropoff/confirm`、`/api/cancel` 语义不变。
- remote `commands/status/ack` HTTP shape 不变。
- ACK 语义不变：ACK 只表示 command envelope 的 robot bridge 处理结果，不代表 delivery success、Nav2/fixed-route success、WAVE ROVER movement、HIL 或真实云成功。

## 验收命令

Full-stack targeted tests：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest \
  src/ros2_trashbot_behavior/test/test_operator_gateway_http.py \
  src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
```

如调整 remote helper：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py
```

Python 编译围栏：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile \
  src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway.py \
  src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py \
  src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py \
  src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py
```

Robot compatibility fence：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest \
  src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py \
  src/ros2_trashbot_behavior/test/test_remote_bridge.py
```

Browser/API 最小围栏由 Full-stack 根据实现选择其一，并在 `tech-done.md` 记录实际命令：

```bash
# 选项 A：若已有本地 gateway 启动方式可用，启动后用 curl/浏览器 smoke 验证首屏和 API。
# 选项 B：若无稳定 server 入口，用现有 HTTP handler/unit test 覆盖渲染 HTML 中的按钮状态和文案。
```

范围和空白检查：

```bash
git diff --check -- \
  src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway.py \
  src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py \
  src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py \
  src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py \
  src/ros2_trashbot_behavior/test/test_operator_gateway_http.py \
  src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py \
  src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py \
  src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py \
  src/ros2_trashbot_behavior/test/test_remote_bridge.py \
  docs/product/mobile_user_flow.md \
  docs/product/remote_4g_mvp.md \
  docs/product/cloud_4g_infrastructure.md \
  sprints/2026.05.12_13-14_phone-command-safety-browser-gate/tech-done.md
```

本计划文档自身验收：

```bash
git diff --check -- \
  sprints/2026.05.12_13-14_phone-command-safety-browser-gate/pre_start.md \
  sprints/2026.05.12_13-14_phone-command-safety-browser-gate/prd.md \
  sprints/2026.05.12_13-14_phone-command-safety-browser-gate/tech-plan.md
```

## 证据边界

- 本轮目标证据：`software_proof_docker_phone_command_safety_browser_gate`。
- 可证明：Docker/local API、operator 首屏或最小 browser smoke 能正确约束手机按钮状态并解释 ACK 语义。
- 不可证明：真实手机 app、真实手机设备验收、真实云、HTTPS/TLS 公网、真实 4G/SIM、真实 OSS upload、STS、CDN origin fetch、生产 DB/queue、Nav2/fixed-route、WAVE ROVER movement、HIL、真实垃圾送达。
- `software_proof` 不得升级为 `hil_pass` 或真实生产 evidence。

## 工程质量要求

- 新增或修改代码中的技术注释必须使用中文，并保持有意义注释比例超过 20%。
- 注释重点解释为什么某些状态禁用操作、为什么 ACK 不是送达成功、为什么 local/browser proof 不等于真实云/4G/HIL。
- 不允许在代码、测试 fixture、文档或日志样例中写真实 AK/SK、Authorization、bearer token、root password、serial、baudrate、ROS topic、`/cmd_vel` 或 WAVE ROVER 参数。

## 风险和阻塞

- 如果现有 HTML 是 dependency-free 字符串渲染，browser smoke 可能只能以 handler/unit test 形式验证；必须在 `tech-done.md` 说明限制。
- 如果 command safety 字段新增过多，旧客户端仍应可忽略；不得破坏现有 `/api/status` shape。
- 如果 Robot compatibility fence 失败，先定位 command/status/ack/cursor 语义，再由对应 owner 修复；不能把失败当成产品收口。
- 当前无真实硬件，不能执行 O1/HIL 或真实送达验证。

## 完成后收口要求

- `tech-done.md` 写清实际改动、验证结果、browser/API 围栏、偏差和未证明事项。
- `side2side_check.md` 对照 PRD P0 验收按钮状态、ACK 文案、redaction、remote compatibility 和证据边界。
- `final.md` 明确是否建议 O5/O6 小幅上调；如果没有 browser/API 可复查证据，不更新 OKR 进度。
