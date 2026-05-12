# Sprint 2026.05.13_00-01 Phone Offline Resume Gate - Tech Plan

## 状态

- 阶段：tech-plan
- 创建时间：2026-05-13 00:01 Asia/Shanghai
- Product Owner：`product-okr-owner`
- 主线 Objective：O5 手机体验与量产边界
- Evidence boundary：计划目标为 `software_proof_docker_phone_offline_resume_gate`

## 技术目标

在不引入真实手机、真实云、真实硬件或 HIL 声明的前提下，为 local/Docker fallback phone surface 增加 `phone_offline_resume_readiness` gate。该 gate 必须把 offline shell、恢复连接、status stale、pending ACK、command safety、support handoff 和 ACK 语义串成同一个 phone-safe contract。

## 文件范围

本 planning 任务只允许改动：

- `sprints/2026.05.13_00-01_phone-offline-resume-gate/pre_start.md`
- `sprints/2026.05.13_00-01_phone-offline-resume-gate/prd.md`
- `sprints/2026.05.13_00-01_phone-offline-resume-gate/tech-plan.md`

后续实现建议由 `full-stack-software-engineer` 在独立任务中改动：

- `src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py`
- `src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_static.py`
- `src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
- `src/ros2_trashbot_behavior/test/test_operator_gateway_http.py`
- `src/ros2_trashbot_behavior/test/test_operator_gateway_static.py`
- `src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
- `docs/product/mobile_user_flow.md`
- `docs/interfaces/ros_contracts.md`，仅当 schema/interface 文档需要同步时修改
- 当前 sprint 的 `tech-done.md`、`side2side_check.md`、`final.md`

如 remote command/status/ACK envelope 受影响，再由 `robot-software-engineer` 只读或补围栏：

- `src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge.py`
- `src/ros2_trashbot_behavior/test/test_remote_bridge.py`
- `src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py`

## 接口方案

新增 phone-safe object：

```json
{
  "schema": "trashbot.phone_offline_resume_readiness.v1",
  "schema_version": 1,
  "evidence_boundary": "software_proof_docker_phone_offline_resume_gate",
  "connection_state": "offline",
  "can_resume": false,
  "primary_actions_enabled": false,
  "support_entry_enabled": true,
  "next_action": "wait_reconnect",
  "safe_phone_copy": "手机当前离线，不能发车或确认投放。请恢复连接后刷新状态。",
  "recovery_hint": "恢复网络后等待小车上报最新状态，再继续操作。",
  "ack_semantics": "ACK 只表示命令已被接收或处理中，不代表送达成功。",
  "not_proven": [
    "real_phone_device",
    "production_app",
    "real_cloud_or_4g",
    "oss_cdn_live_traffic",
    "nav2_or_fixed_route_delivery",
    "wave_rover_motion",
    "hil",
    "delivery_success"
  ]
}
```

输出位置：

- `/api/status.phone_offline_resume_readiness`
- `/api/status.phone_readiness.phone_offline_resume_readiness`
- `/api/diagnostics.phone_offline_resume_readiness`
- fallback HTML 首屏的 offline/resume panel
- offline shell 只读 copy，不写入任何控制命令缓存

## 任务分工

### Task A：Phone offline/resume gate implementation

- Owner：`full-stack-software-engineer`
- 类型：implementation
- 目标：实现 `trashbot.phone_offline_resume_readiness.v1`，更新 API、diagnostics、HTML/offline shell 和产品文档。
- 文件范围：见后续实现建议文件范围中的 operator gateway、test、docs/product、docs/interfaces 和当前 sprint 收口文档。
- 验收命令：

```bash
python3 -m unittest src/ros2_trashbot_behavior/test/test_operator_gateway_http.py src/ros2_trashbot_behavior/test/test_operator_gateway_static.py src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
python3 -m py_compile src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_static.py src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py
git diff --check -- src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_static.py src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py src/ros2_trashbot_behavior/test/test_operator_gateway_http.py src/ros2_trashbot_behavior/test/test_operator_gateway_static.py src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py docs/product/mobile_user_flow.md docs/interfaces/ros_contracts.md
```

### Task B：Remote/robot compatibility fence

- Owner：`robot-software-engineer`
- 类型：compatibility fence，只有 Task A 改动 remote metadata 或 command/status/ACK envelope 时执行。
- 目标：确认 offline/resume metadata 不触发 robot action、不污染 `trashbot.remote.v1` envelope、不 ACK、不推进 cursor、不把 ACK 解释成 delivery success。
- 文件范围：remote bridge 相关测试和必要文档；不得改 phone UI 主实现。
- 验收命令：

```bash
python3 -m unittest src/ros2_trashbot_behavior/test/test_remote_bridge.py src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py
python3 -m py_compile src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge.py
git diff --check -- src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge.py src/ros2_trashbot_behavior/test/test_remote_bridge.py src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py
```

## 验收口径

P0 必须满足：

- `phone_offline_resume_readiness` 三处同口径输出：top-level status、nested phone_readiness、diagnostics。
- Offline shell 和 fallback 首屏不缓存、不伪造、不发送控制请求；离线时 Start/Confirm/Cancel disabled。
- Recovering/status stale/pending ACK/manual takeover/support required 场景下，按钮状态由 command safety 最终阻断。
- Diagnostics/Support Handoff 在 primary actions blocked 时仍可进入。
- ACK copy 全链路保持 accepted/processing only。
- Redaction 不泄露 token、Authorization、OSS AK/SK、root password、DB/queue URL、ROS topic、`/cmd_vel`、serial、baudrate、local path、checksum 或 complete artifact。
- 文档明确 `software_proof_docker_phone_offline_resume_gate` 不等于真实手机、production app、真实云/4G、OSS/CDN 实流量、Nav2/fixed-route、WAVE ROVER、HIL 或真实送达。

P1 可选：

- 复用或扩展现有 browser acceptance fixture，覆盖 mobile viewport 下 offline/resume copy、disabled buttons、Diagnostics/Support Handoff 入口和无重叠。

## Planning 验收命令

本 Product planning 任务必须运行：

```bash
test -f sprints/2026.05.13_00-01_phone-offline-resume-gate/pre_start.md && test -f sprints/2026.05.13_00-01_phone-offline-resume-gate/prd.md && test -f sprints/2026.05.13_00-01_phone-offline-resume-gate/tech-plan.md
git diff --check -- sprints/2026.05.13_00-01_phone-offline-resume-gate/pre_start.md sprints/2026.05.13_00-01_phone-offline-resume-gate/prd.md sprints/2026.05.13_00-01_phone-offline-resume-gate/tech-plan.md
```

## 风险边界

- 本轮 planning 不更新 `OKR.md`；实现和 final 证据落地后再保守更新。
- 不读取或修改硬件/vendor 配置；本轮不涉及 WAVE ROVER、ESP32、Orange Pi UART、引脚、电压、底盘协议或机械尺寸。
- 不把 local/Docker offline/resume proof 说成真实手机设备、production app、真实云/4G、真实 OSS/CDN、真实硬件、HIL 或真实送达。
- 不允许 service worker 缓存控制类 API 或 command/ACK 请求。
- 不允许 support handoff 输出 raw diagnostics、完整 artifact 或敏感字段。
