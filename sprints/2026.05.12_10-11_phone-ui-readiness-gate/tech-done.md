# Sprint 2026.05.12_10-11 Phone UI Readiness Gate - Tech Done

## 状态

- 阶段：tech-done
- 更新时间：2026-05-12 10:58 Asia/Shanghai
- 主责 Engineer：`full-stack-software-engineer`
- 证据边界：`software_proof_docker_local_phone_ui_readiness_gate`

## 实际改动

- `src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py`
  - 新增 `trashbot.phone_readiness.v1` 聚合 schema。
  - `/api/status` 兼容保留原字段，并新增 `phone_readiness`。
  - `phone_readiness` 聚合 local delivery status、action permissions、local/mock `remote_readiness`、可选 `cloud_preflight` 和可选 `backup_restore`。
  - 首屏新增 phone readiness panel，直接显示是否可继续、恢复提示、支持等级和 local/Docker proof 边界。
- `src/ros2_trashbot_behavior/test/test_operator_gateway_http.py`
  - 覆盖 `/api/status.phone_readiness` 输出。
  - 覆盖 `status_stale`、`command_pending`、`auth_failed`、`cloud_unreachable`、`malformed_response` 分类。
  - 覆盖 ACK 不等于 delivery success：即使 `degradation_state=ok`，local delivery state 不会被写成 `completed`，仍保留 `nav2_or_fixed_route_delivery` 未证明项。
- `src/ros2_trashbot_behavior/test/test_operator_gateway_static.py`
  - 增加 schema/helper/API/UI 字符串静态检查。
- `docs/product/mobile_user_flow.md`
  - 记录首屏 phone readiness gate、字段含义、ACK 边界和未证明项。
- `docs/product/remote_4g_mvp.md`
  - 记录 local operator fallback 的 `/api/status.phone_readiness` 与远程控制边界。
- `docs/interfaces/ros_contracts.md`
  - 记录 `/api/status.phone_readiness` 接口 contract、状态枚举、兼容性和 ACK 语义。

## 用户旅程变化

- 用户打开本地 operator 页面后，首屏不再必须从 raw JSON 或 diagnostics 推断状态。
- 首屏直接回答：
  - 现在能不能继续：`can_continue` + badge。
  - 为什么不能继续：`primary_state` + `safe_phone_copy`。
  - 下一步做什么：`next_action` + `recovery_hint`。
- local fallback 与 remote readiness 分离表达：例如本地按钮可继续但远程状态 stale 时，显示 `local_ready_remote_status_waiting`，不会把本地 Docker proof 写成生产远程 ready。
- 支持人员仍能在 raw status/diagnostics 里看到完整机器可读字段，但普通用户首屏先看到恢复路径。

## API/UI 影响和兼容性

- 兼容性：`/api/status` 原有字段保留；新增 `phone_readiness` 对旧客户端是可忽略字段。
- 新增字段：
  - `schema=trashbot.phone_readiness.v1`
  - `schema_version=1`
  - `evidence_boundary=software_proof_docker_local_phone_ui_readiness_gate`
  - `primary_state`
  - `can_continue`
  - `next_action`
  - `safe_phone_copy`
  - `recovery_hint`
  - `support_level`
  - `local_delivery`
  - `action_permissions`
  - `remote_readiness`
  - `cloud_preflight`
  - `backup_restore`
  - `not_proven`
- `remote_readiness` 分类覆盖：
  - `ok`
  - `status_stale`
  - `command_pending`
  - `auth_failed`
  - `cloud_unreachable`
  - `malformed_response`
- ACK 边界：ACK 只表示 command envelope 已处理，不表示送达完成、Nav2/fixed-route 成功、WAVE ROVER 运动或 HIL 通过。

## 验证输出

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py
exit 0, no output
```

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest src/ros2_trashbot_behavior/test/test_operator_gateway_static.py src/ros2_trashbot_behavior/test/test_operator_gateway_http.py src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
Ran 68 tests in 15.457s
OK
```

## 不做事项

- 未运行 hardware smoke、HIL、WAVE ROVER 串口验证。
- 未运行 broad `colcon build`。
- 未运行 Nav2/fixed-route 实跑。
- 未运行真实 4G/SIM、真实云、公网 HTTPS/TLS 或 OSS/CDN 实流量验证。
- 未改 `operator_gateway.py`、`operator_gateway_diagnostics.py`、`remote_cloud_relay.py`、硬件/vendor、Nav2、vision 或 launch 文件。

## 剩余风险和协作事项

- 当前证据仍是 local/Docker software proof，不提升真实手机 app、真实云、真实 4G、OSS/CDN、Nav2/fixed-route、WAVE ROVER 或 HIL 完成度。
- 若后续要把独立 relay `/preflightz`、backup/restore drill artifact 接入本地 operator 页面，需要 Robot/Full-stack 确认 artifact 输入路径和生命周期。
- 正式手机 UI 仍需按 `OKR.md` O5 KR7 和 `docs/product/mobile_user_flow.md` 补齐真实手机浏览器/设备验收：视觉系统、主路径 ≤ 3 步、中文优先文案、iPhone/Android 适配、最小可点击区域和首屏可交互时间。
