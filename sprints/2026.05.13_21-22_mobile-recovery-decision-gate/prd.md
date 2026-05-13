# Sprint 2026.05.13_21-22 Mobile Recovery Decision Gate - PRD

## 用户问题

上轮手机首屏已经能解释“能不能发车”，但用户在发车后或异常时仍缺少一个清晰答案：现在应该等待 ACK、重试刷新、打开诊断、请求人工接管，还是不要再按主操作。普通用户不应理解 ACK、cursor、remote bridge 或 ROS2 状态机细节。

## 产品目标

建立 `software_proof_docker_mobile_recovery_decision_gate`：手机首屏新增恢复决策摘要，把 `operation_log`、`phone_offline_resume_readiness`、`command_safety`、`phone_action_feedback`、`mobile_action_receipt`、support handoff 和 primary journey gate 汇总成一个用户可读的“下一步”。

## OKR 映射

- Objective 4 KR1：手机端最小流程继续补齐“查看状态 -> 处理异常”。
- Objective 4 KR5：普通用户不接触命令行、不理解 ROS2，也能知道失败时该怎么做。
- Objective 4 KR7：手机端主路径继续向可直接使用推进，但本轮仍只限 Docker/local software proof。

## 验收口径

- 首屏可见恢复决策 panel，显示状态、建议下一步、阻塞原因、支持入口、ACK 语义和证据边界。
- 缺少恢复决策 summary 时默认 fail closed，并从现有 phone-safe 字段派生 blocked-by-design 摘要。
- UI 不暴露 token、Authorization、OSS AK/SK、root password、DB/queue URL、raw ROS topic、`/cmd_vel`、serial device、baudrate、WAVE ROVER 参数、local path、traceback、checksum 或完整 artifact。
- robot 侧新增 metadata-only fence：`mobile_recovery_decision_gate` / `mobile_recovery_decision_summary` 不能触发 collect、confirm_dropoff、cancel、ACK、cursor 推进或 cursor 持久化。

## 非目标

- 不证明真实手机设备/browser、production app、真实 PWA install prompt。
- 不证明真实 cancel completed、dropoff completed、delivery success。
- 不证明 Objective 5 的真实公网/4G/OSS/CDN/production DB queue。
- 不改 WAVE ROVER、ESP32、Orange Pi、UART、launch 硬件参数或 HIL 工具。
