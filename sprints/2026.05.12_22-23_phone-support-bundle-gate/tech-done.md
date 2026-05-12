# Sprint 2026.05.12_22-23 Phone Support Bundle Gate - Tech Done

## Task A - Full-Stack 主实现

- Owner：`full-stack-software-engineer`
- 完成时间：2026-05-12 20:26:12 CST
- Evidence boundary：`software_proof_docker_phone_support_bundle_gate`

### 实际改动

- `operator_gateway_http.py`
  - 新增 `trashbot.phone_support_bundle.v1` builder：`/api/status.phone_support_bundle`、`/api/status.phone_readiness.phone_support_bundle`、`/api/diagnostics.phone_support_bundle` 共用同一套生成与脱敏逻辑。
  - Support bundle 复用现有 status、`phone_readiness`、`command_safety`、diagnostics 摘要；不触发 robot action，不改变 remote bridge command/status/ACK envelope。
  - `safe_copy` 为中文优先，明确 ACK 只代表 accepted/processing evidence，不能代表送达成功。
  - 增加敏感字段过滤：token、Authorization、OSS AK/SK、root password、DB/queue URL、raw ROS topic、`/cmd_vel`、serial device、baudrate、WAVE ROVER 参数、local path、traceback、checksum、完整 artifact。
  - 本地 fallback HTML 新增 `Support Handoff` 入口、脱敏摘要复制区和刷新入口；Start/Confirm/Cancel 被 command safety 阻断时，Support Handoff 与 Diagnostics 仍可打开。
- `operator_gateway_static.py`
  - 新增静态锚点模块，给 support handoff HTML id 和 ACK 文案提供 py_compile/static-test 检查目标。
- `test_operator_gateway_http.py`
  - 增加 `/api/status`、`/api/diagnostics`、builder 脱敏、HTML support handoff 的回归断言。
- `test_operator_gateway_static.py`
  - 增加 support bundle schema、evidence boundary、入口 id、复制入口和静态锚点断言。
- `docs/product/mobile_user_flow.md`
  - 同步 support handoff 用户旅程、脱敏范围、可复制摘要和 command safety blocked 下仍可打开的行为。
- `docs/interfaces/ros_contracts.md`
  - 同步 `phone_support_bundle` 字段、schema、API 位置、ACK 语义、脱敏红线和不触发 robot action 的契约。

### 用户旅程变化和触点收益

- 失败、blocked、等待 ACK 或需要人工接管时，用户不用截图 raw JSON，也不用懂 ROS2/串口/硬件细节；首屏可打开 Support Handoff，复制一段中文脱敏摘要给家人、售后或工程支持。
- 主操作被 command safety 禁用时，用户仍能进入 Diagnostics/Support Handoff 收集复现信息，避免“按钮灰了但不知道怎么求助”。
- 摘要明确 ACK 不是送达成功，防止把远程 command accepted/processing 误读为真实送达、HIL 或底盘运动成功。

### 接口影响

- `/api/status` 新增顶层 `phone_support_bundle`。
- `/api/status.phone_readiness` 新增 `phone_support_bundle`，与顶层对象同口径。
- `/api/diagnostics` 新增 `phone_support_bundle`，同 builder 生成，并可补充 diagnostics 中的脱敏 failure context。
- 未改 `remote_bridge.py`、`remote_bridge_protocol.py`、硬件参数、OKR 或生产 remote bridge 行为。

### 验证结果

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest src/ros2_trashbot_behavior/test/test_operator_gateway_http.py src/ros2_trashbot_behavior/test/test_operator_gateway_static.py
................................................
----------------------------------------------------------------------
Ran 48 tests in 20.053s

OK
```

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_static.py
exit 0
```

### 失败定位

- 首轮单测失败 2 项，原因是新增测试断言写成“不代表送达成功”，而既有运行时 ACK 文案是“不能代表送达成功”。已修正测试锚点，保持运行时 ACK 语义不变。
- 第二轮单测失败 1 项，原因是 `/api/status` 本身没有 diagnostics 的 `software_version`；已改为断言 status support refs 中存在 `current_step`，diagnostics support bundle 仍覆盖 `software_version`。

### 剩余风险

- 本轮是 local/Docker software proof；没有真实手机设备、production app、真实云/4G、OSS/CDN 实流量、Nav2/fixed-route、WAVE ROVER、HIL 或真实送达证据。
- Clipboard 自动复制依赖浏览器权限；权限不可用时页面会聚焦 textarea，用户需手动选择文本。
- Task B 的 remote bridge 兼容性围栏由 `robot-software-engineer` 并行验证，本段只记录 Task A 范围。

## Task B - Robot Compatibility Fence

- Owner：`robot-software-engineer`
- 完成时间：2026-05-12 20:43:19 CST
- Evidence boundary：`software_proof_docker_phone_support_bundle_gate`

### 实际改动

- `test_remote_bridge.py`
  - 增加 `phone_support_bundle` metadata 兼容性围栏，确认云端 status/command/ACK response 的 support bundle 字段不会进入 robot `trashbot.remote.v1` ACK envelope。
  - 增加 metadata-only blocked response 围栏，确认只有 `phone_support_bundle`、没有 command envelope 时，不触发 robot backend action、不 ACK、不推进 `last_ack_id`、不持久化 cursor。
  - 明确 ACK payload 不接受 `delivery_success`、`DELIVERED` 或 `trigger_robot_action` 等手机支持元数据。
- `test_operator_gateway_diagnostics.py`
  - 移除临时 skip，改为直接覆盖 `/api/diagnostics` 已接线 wrapper 生成的 `phone_support_bundle`。
  - 断言 diagnostics support bundle schema/evidence boundary 正确，保留 `software_version`、`map_version`、`route_version`、`source` 等安全引用。
  - 断言 `support_refs` 不包含 raw ROS topic、serial、baudrate、token、Authorization、DB/queue URL 或 local path，输出正文不包含 `/cmd_vel`、`/dev/ttyUSB0`、Bearer/token、`postgres://` 或 `/tmp/robot/status.json`。
  - 保留 core diagnostics payload 不信任 latest_status 里预置 support bundle 的围栏，确保 HTTP wrapper 重新生成脱敏对象。

### 验证结果

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest src/ros2_trashbot_behavior/test/test_remote_bridge.py src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
Ran 76 tests in 18.878s
OK
```

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge.py src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py
exit 0
```

### 失败定位

- 第一轮 finalization 单测失败 1 项：断言把 `not_proven` 中的 `hardware_or_serial_details` 当成 serial device 泄露。已收紧为结构化检查 `support_refs` 不含敏感 key，并继续禁止真实串口路径、topic、凭证、URL 和 local path 出现在 bundle 输出中。

### 剩余风险

- 本轮仍是 local software proof；没有真实手机设备、production app、真实云/4G、OSS/CDN 实流量、Nav2/fixed-route、WAVE ROVER、HIL 或真实送达证据。
- Robot compatibility fence 只验证 support bundle 不污染 remote command/status/ACK envelope；不改变 production remote bridge 行为。
