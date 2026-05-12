# Sprint 2026.05.12_22-23 Phone Support Bundle Gate - Tech Plan

## 状态

- 阶段：tech-plan
- Product Owner：`product-okr-owner`
- 主线 Objective：O5 手机体验与量产边界
- Evidence boundary：`software_proof_docker_phone_support_bundle_gate`
- 执行模式：tech-plan 完成后进入 implementation，由对应 worker 执行；主节点不直接改产品代码或测试代码。

## 总体方案

在现有 operator gateway phone readiness 之上新增 support bundle / handoff package。它是 phone-safe summary，不是 raw diagnostics dump：

- API 层：新增 `phone_support_bundle` helper，复用已有 status、diagnostics、phone_readiness、command_safety、ACK 和 O6 phone-safe summaries。
- 状态层：`/api/status` 顶层、`phone_readiness.phone_support_bundle` 和 `/api/diagnostics.phone_support_bundle` 使用同一 schema。
- UI 层：首屏新增 support/handoff 入口，允许用户在失败或 blocked 状态下复制普通中文摘要。
- 兼容层：remote bridge command/status/ack envelope、cursor、ACK 语义、robot action 触发不变。

## 接口 contract

新增对象：

```text
schema=trashbot.phone_support_bundle.v1
schema_version=1
evidence_boundary=software_proof_docker_phone_support_bundle_gate
```

必备字段：

- `bundle_id`：本地可追踪 id；不得包含 token、路径或硬件细节。
- `generated_at`：生成时间。
- `support_level`：`phone_ready`、`local_fallback`、`remote_waiting_ack`、`support_required`、`human_takeover_required` 等。
- `status_summary`：普通用户状态摘要，来自 phone readiness/local delivery。
- `failure_summary`：失败或阻塞摘要；无失败时说明当前没有 terminal failure。
- `next_steps`：用户下一步和支持人员下一步。
- `ack_semantics`：ACK 只代表 accepted/processing evidence，不等于 delivery success。
- `support_refs`：脱敏引用，例如 map/route/software version、task id、failure code、safe diagnostic keys；不得包含 local path、token 或完整 artifact。
- `safe_copy`：可复制给支持人员的普通中文摘要。
- `not_proven`：production app、real phone device、real cloud/4G、OSS/CDN live traffic、Nav2/fixed-route、WAVE ROVER、HIL、delivery success 等未证明能力。

## Task A - Full-Stack 主实现

Owner：`full-stack-software-engineer`

允许改动文件范围：

- `src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py`
- `src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_static.py`
- `src/ros2_trashbot_behavior/test/test_operator_gateway_http.py`
- `src/ros2_trashbot_behavior/test/test_operator_gateway_static.py`
- `docs/product/mobile_user_flow.md`
- `docs/interfaces/ros_contracts.md`
- `sprints/2026.05.12_22-23_phone-support-bundle-gate/tech-done.md`

实现要求：

- 新增 `trashbot.phone_support_bundle.v1` summary builder，尽量复用已有 phone readiness / diagnostics helper，避免 `/api/status` 和 `/api/diagnostics` 口径漂移。
- `/api/status` 顶层新增 `phone_support_bundle`，并在 `phone_readiness.phone_support_bundle` 中引用同口径对象。
- `/api/diagnostics` 新增 `phone_support_bundle`。
- 本地 fallback HTML 首屏加入 support/handoff 入口；主操作被 command safety 阻断时，support/diagnostics 仍可打开。
- `safe_copy` 文案中文优先，且明确 ACK 不是送达成功。
- 过滤敏感字段：token、Authorization、OSS AK/SK、root password、DB/queue URL、raw ROS topic、`/cmd_vel`、serial device、baudrate、WAVE ROVER 参数、local path、traceback、checksum、完整 artifact。
- 文档同步 `docs/product/mobile_user_flow.md` 和 `docs/interfaces/ros_contracts.md`。
- 代码新增或修改的技术注释必须使用中文，并保持注释比例满足项目规范。
- 不改 remote bridge 生产行为；不新增硬件参数；不触碰 OKR。

验收命令：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest src/ros2_trashbot_behavior/test/test_operator_gateway_http.py src/ros2_trashbot_behavior/test/test_operator_gateway_static.py
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_static.py
git diff --check -- src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_static.py src/ros2_trashbot_behavior/test/test_operator_gateway_http.py src/ros2_trashbot_behavior/test/test_operator_gateway_static.py docs/product/mobile_user_flow.md docs/interfaces/ros_contracts.md sprints/2026.05.12_22-23_phone-support-bundle-gate/tech-done.md
```

## Task B - Robot Compatibility Fence

Owner：`robot-software-engineer`

允许改动文件范围：

- `src/ros2_trashbot_behavior/test/test_remote_bridge.py`
- `src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
- `sprints/2026.05.12_22-23_phone-support-bundle-gate/tech-done.md`

实现要求：

- 增加或调整最小兼容性围栏，确认新增 `phone_support_bundle` metadata 不污染 `trashbot.remote.v1` command/status/ack envelope。
- 确认 metadata-only blocked response 不触发 robot action、不 ACK、不推进或持久化 cursor。
- 确认 ACK 文案/字段仍不等于 delivery success。
- 确认 diagnostics support bundle 不暴露 raw ROS topic、serial、baudrate、token、Authorization、OSS/DB/queue URL 或 local path。
- 只做围栏验证；不改 production remote bridge 行为，除非测试暴露真实兼容性 bug 且在本范围内能修。
- 代码新增或修改的技术注释必须使用中文，并保持注释比例满足项目规范。

验收命令：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest src/ros2_trashbot_behavior/test/test_remote_bridge.py src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge.py src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py
git diff --check -- src/ros2_trashbot_behavior/test/test_remote_bridge.py src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py sprints/2026.05.12_22-23_phone-support-bundle-gate/tech-done.md
```

## Product Closeout

Owner：`product-okr-owner`

允许改动文件范围：

- `OKR.md`
- `sprints/2026.05.12_22-23_phone-support-bundle-gate/side2side_check.md`
- `sprints/2026.05.12_22-23_phone-support-bundle-gate/final.md`

收口要求：

- 对照本 PRD 和 tech-plan 核查 Task A / Task B 证据。
- 确认 `docs/product/mobile_user_flow.md` 和 `docs/interfaces/ros_contracts.md` 已同步，且引用路径真实存在。
- 确认 O5 进度只按 `software_proof_docker_phone_support_bundle_gate` 保守更新；不得声明真实手机设备、production app、真实云/4G、OSS/CDN 实流量、Nav2/fixed-route、WAVE ROVER、HIL 或真实送达。
- 写入 `side2side_check.md` 和 `final.md`。
- 更新 automation memory，并在 durable work 完成后提交和推送。

验收命令：

```bash
git diff --check -- OKR.md sprints/2026.05.12_22-23_phone-support-bundle-gate/side2side_check.md sprints/2026.05.12_22-23_phone-support-bundle-gate/final.md
```

## 并行派发规则

Task A 与 Task B 文件范围互不重叠，implementation 阶段必须在同一条消息里并行派发：

- `full-stack-software-engineer` 执行 Task A。
- `robot-software-engineer` 执行 Task B。

Product closeout 必须等待 Task A / Task B 返回实际改动和验证结果后执行。

## 本阶段验收

本阶段只创建 sprint 前三份文档，不创建 `tech-done.md`、`side2side_check.md` 或 `final.md`。

```bash
git diff --check -- sprints/2026.05.12_22-23_phone-support-bundle-gate/pre_start.md sprints/2026.05.12_22-23_phone-support-bundle-gate/prd.md sprints/2026.05.12_22-23_phone-support-bundle-gate/tech-plan.md
```

