# Sprint 2026.05.14_03-04 Mobile Real Device Evidence Intake Gate - Final

## 结论

本 sprint 收口为通过。`software_proof_docker_mobile_real_device_evidence_intake_gate` 已由 Full-stack 首屏 intake surface 与 Robot metadata-only compatibility fence 双侧证明。

## 实际改动

Task A Full-stack：

- `mobile/web/index.html`
- `mobile/web/app.js`
- `mobile/web/styles.css`
- `mobile/fixtures/mobile_web_status.fixture.json`
- `mobile/test_mobile_web_entrypoint.py`
- `docs/product/mobile_user_flow.md`
- `mobile/README.md`

Task B Robot：

- `onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py`
- `onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py`
- `docs/interfaces/ros_contracts.md`

Task C Product：

- `OKR.md`
- `docs/process/okr_progress_log.md`
- `sprints/2026.05.14_03-04_mobile-real-device-evidence-intake-gate/tech-done.md`
- `sprints/2026.05.14_03-04_mobile-real-device-evidence-intake-gate/side2side_check.md`
- `sprints/2026.05.14_03-04_mobile-real-device-evidence-intake-gate/final.md`

## 验证结果

Task A：

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest mobile.test_mobile_web_entrypoint
Ran 24 tests in 0.014s OK

PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile mobile/test_mobile_web_entrypoint.py
pass

node --check mobile/web/app.js
pass

rg software_proof_docker_mobile_real_device_evidence_intake_gate ... mobile docs/product/mobile_user_flow.md
pass

git diff --check -- mobile/... docs/product/mobile_user_flow.md mobile/README.md tech-done.md
pass
```

Task B：

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py
Ran 133 tests in 67.780s OK

PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py
pass

rg mobile_real_device_evidence_intake ... docs/interfaces/ros_contracts.md onboard/src/ros2_trashbot_behavior/test
pass

git diff --check -- onboard/... docs/interfaces/ros_contracts.md tech-done.md
pass
```

Task C：

```text
test -f tech-done.md && test -f side2side_check.md && test -f final.md
pass

rg software_proof_docker_mobile_real_device_evidence_intake_gate ... OKR.md docs/process/okr_progress_log.md sprints/2026.05.14_03-04_mobile-real-device-evidence-intake-gate
pass

git diff --check -- OKR.md docs/process/okr_progress_log.md sprints/2026.05.14_03-04_mobile-real-device-evidence-intake-gate
pass
```

## OKR 调整

Objective 4 从约 79% 谨慎上调到约 80%。理由是当前手机/PWA 首屏现在具备真实设备验收材料 intake、redaction、blocked package、phone-safe copy 和 robot metadata-only fence，后续真实 iPhone/Android、production app、PWA install prompt/user choice 材料可以按统一 schema 进入产品验收。

Objective 5 保持约 68%。理由是本轮没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker/migration 或其他真实外部 O5 材料。

Objective 1/2/3 不调整。

## 风险和下一步

剩余风险未关闭：真实手机设备、真实 iPhone/Android device behavior、production app、真实 PWA install prompt/user choice、真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、production worker/migration、Nav2/fixed-route、WAVE ROVER、HIL、真实 dropoff/cancel completion 和真实 delivery。

下一步：若仍没有 O5 外部材料，不要重复本地 O5 metadata depth；优先用本轮 intake gate 收集真实 iPhone/Android 或 production app/PWA prompt 材料，并保持 `not_proven` 与 ACK 非 delivery success 边界。
