# Sprint 2026.05.14_07-08 Mobile Real Device Retest Request Gate - Final

## Sprint 类型

- sprint_type: epic
- sprint 状态：完成
- 证据边界：`software_proof_docker_mobile_real_device_retest_request_gate`

## 用户价值和产品北极星

本轮把真实设备验收从 review execution 推进到 retest request：验收人员下一轮可以按 missing evidence、material readiness/status、owner/next action、blocked/rejection reason、redaction/source boundary 和 `not_proven` 执行复测材料补齐。

产品北极星保持不变：手机是普通用户唯一入口。本轮只是把真实设备复测材料请求软件化、可复制、可脱敏、可对账，不把 request package 包装成真实手机验收、production app、PWA prompt/user choice、O5 外部 proof、HIL 或 delivery success。

## OKR 结果

- Objective 4：约 83% -> 约 84%。理由是 `mobile/web` 已把 review execution 转成 retest request checklist/package，并由 phone-safe copy、`not_proven`、ACK-not-delivery 和 Robot metadata-only fence 约束。
- Objective 5：保持约 68%。没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker/migration 或其他真实外部材料。
- Objective 1/2/3：不调整。本轮没有新增真实 WAVE ROVER、串口、HIL、Nav2/fixed-route、任务状态机或真实送达证据。

## 实际改动

- Task A Full-stack：新增 `mobile_real_device_retest_request*` UI、fixture、copy package、mobile tests 和 `mobile/README.md` / `docs/product/mobile_user_flow.md` 更新。
- Task B Robot：新增 `mobile_real_device_retest_request*` metadata-only / valid-command mixed fences，并同步 `docs/interfaces/ros_contracts.md`。
- Task C Product：更新 `OKR.md` 4.1、`docs/process/okr_progress_log.md` 顶部、本 sprint `tech-done.md`，并新增 `side2side_check.md` 和 `final.md`。

## 验证结果

Task A 已通过：

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest mobile.test_mobile_web_entrypoint
Ran 28 tests in 0.029s
OK

PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile mobile/test_mobile_web_entrypoint.py
exit code 0

node --check mobile/web/app.js
exit code 0

rg retest request/mobile boundary checks
exit code 0

git diff --check scoped to Task A files
exit code 0
```

Task B 已通过：

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py
Ran 149 tests in 76.425s
OK

PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py
exit code 0

rg metadata-only / delivery success / production readiness / HIL checks
exit code 0

git diff --check scoped to Task B files
exit code 0
```

Task C closeout 已通过：

```text
test -f tech-done.md && test -f side2side_check.md && test -f final.md
exit code 0

rg closeout boundary checks
exit code 0

git diff --check scoped to OKR/progress/sprint closeout files
exit code 0
```

## 失败定位

- Task A 首次 `node --check mobile/web/app.js` 失败：`terminalActionGateFromStatus` 中重复声明 `mobileRealDeviceRetestRequest`。已删除重复声明并复验通过。
- Task A 首次 unit run 失败：新增断言要求 `Objective 5 外部材料` 明确出现在 runtime contract 中，而 `app.js` 只保留 `objective5_external_materials` 字段名。已补中文边界锚点并复验通过。
- Task B 未发现验证失败。
- Task C 未发现验证失败。

## Objective 5 最低但不选的复盘

Objective 5 仍是当前最低 Objective，约 68%。本轮不选 O5 的理由仍成立：本机只有 Docker，没有真实公网/4G/OSS/CDN/production DB/queue/worker 外部材料。继续做 O5 metadata 会重复消费同一 blocker，不能形成真实外部 proof。

本轮选择 O4 是为了把上一轮 review execution 进一步转成真实设备复测请求包，帮助下一轮真实设备验收直接补材料，而不是继续堆本地 O5 metadata。

## 剩余风险

- retest request package 是下一轮真实设备复测材料请求，不是验收通过。
- 未证明真实手机设备、真实 iPhone/Android device behavior、production app、真实 PWA install prompt/user choice。
- 未证明真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、production worker/migration。
- 未证明 Nav2/fixed-route、WAVE ROVER、真实串口、HIL、真实 dropoff/cancel completion 或真实 delivery。
- ACK、HTTP accepted、receipt、review execution package 和 retest request package 仍只是 accepted/processing/support metadata，不是 delivery success。

## 下一步

下一轮如果仍没有 Objective 5 外部材料，应优先补 Objective 4 的真实 iPhone/Android device behavior、production app、真实 PWA install prompt/user choice 或主路径真实移动设备验收材料。若拿到真实公网/4G/OSS/CDN/production DB/queue/worker 证据，再回到 Objective 5 completion。
