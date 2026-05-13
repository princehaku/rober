# Sprint 2026.05.14_03-04 Mobile Real Device Evidence Intake Gate - Side2Side Check

## 对照结论

本 sprint 验收通过，证据边界为 `software_proof_docker_mobile_real_device_evidence_intake_gate`。它证明当前 Docker/local `mobile/web` PWA 可以收集、导入、脱敏、展示和复制真实设备验收材料摘要，并且 Robot metadata-only fence 不把这些材料误当作控制、ACK、cursor、production readiness、HIL 或 delivery success。

## 用户价值对照

- PRD 要求：真实设备验收材料进入统一 schema、脱敏和判定入口。
  - 结果：Full-stack 已新增“真实设备验收材料”首屏 panel，支持 JSON 导入、本地 blocked package 生成和 redacted phone-safe package 复制。
- PRD 要求：材料覆盖真实 iPhone/Android、production app、PWA install prompt/user choice、截图/URL 摘要和 `not_proven`。
  - 结果：Task A fixture、UI、unittest 和 `docs/product/mobile_user_flow.md` 已覆盖这些字段，并保持 `overall_status=blocked`、`safe_to_control=false`。
- PRD 要求：Robot 侧必须证明 intake materials 是 metadata-only。
  - 结果：Task B targeted tests 证明 metadata-only response 不触发 collect、confirm_dropoff、cancel、ACK POST、cursor advance/persistence、terminal ACK、production readiness、HIL、dropoff/cancel success 或 delivery success。

## OKR 对照

- Objective 4：可谨慎从约 79% 上调到约 80%。本轮不是证明真实设备已通过，而是把真实设备验收材料入口和 robot 兼容围栏做成软件证明。
- Objective 5：保持约 68%。本轮没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker/migration 或 production app 运行证据。
- Objective 1/2/3：不调整。本轮未接触 WAVE ROVER、UART、Nav2/fixed-route、task_orchestrator、真实送达或 HIL。

## 证据边界

已证明：

- `mobile/web` 首屏存在真实设备验收材料 intake surface。
- redacted phone-safe package 不应包含 token、Authorization、OSS AK/SK、root password、DB/queue URL、ROS topic、`/cmd_vel`、serial、WAVE ROVER、本地路径、traceback、checksum、完整 artifact 或 raw robot response。
- ACK 语义保持 `accepted_processing_only_not_delivery_success`。
- Robot compatibility fence 保持 metadata-only，不污染 command/status/ACK/cursor 或 delivery result。

未证明：

- 真实手机设备、真实 iPhone/Android device behavior、production app、真实 PWA install prompt/user choice。
- 真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、production worker/migration。
- Nav2/fixed-route、WAVE ROVER、HIL、真实 dropoff/cancel completion 或真实 delivery。

## 验收命令摘录

Task A：

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest mobile.test_mobile_web_entrypoint
Ran 24 tests in 0.014s
OK

py_compile pass
node --check mobile/web/app.js pass
rg intake/redaction/not_proven references pass
scoped diff check pass
```

Task B：

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py
Ran 133 tests in 67.780s
OK

py_compile pass
rg metadata-only references pass
scoped diff check pass
```

## Product 验收判断

本轮达成 PRD P0/P1 目标，可以收口为 Objective 4 的软件入口能力进展。后续若要继续提升 Objective 4，需要拿到真实手机/browser 或 production app/PWA prompt 材料并用本 intake gate 归档；若要提升 Objective 5，需要真实外部云/4G/OSS/CDN/DB/queue/worker/migration 证据。
