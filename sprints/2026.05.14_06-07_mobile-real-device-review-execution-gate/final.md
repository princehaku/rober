# Sprint 2026.05.14_06-07 Mobile Real Device Review Execution Gate - Final

## 结论

本 sprint 完成 `software_proof_docker_mobile_real_device_review_execution_gate`。Task A/B 已把真实设备验收材料从 review handoff package 推进到可记录执行状态的 review execution checklist/package，并用 robot metadata-only fence 证明该 metadata 不进入 command、ACK、cursor、terminal ACK、production readiness、HIL 或 delivery success 语义。

Objective 4 可从约 82% 谨慎上调到约 83%。Objective 5 仍约 68%，Objective 1/2/3 不调整。

## 用户价值和产品北极星

用户价值：人工评审和支持同学可以接收一份 phone-safe、可复制、带 review result/status、evidence items readiness、operator/reviewer notes、blocked reason、next evidence request 的 review execution package，不需要理解 raw JSON、ROS topic 或云端内部字段。

产品北极星：手机仍是普通用户唯一入口。本轮只推进手机验收材料的人工评审执行记录，不把 review execution 写成真实设备验收通过。

## OKR 映射和 KR 更新

- Objective 4 KR5：用户验收标准从 review handoff 推进到 review execution，能解释执行状态、blocker 和下一步 evidence。
- Objective 4 KR7：手机首屏新增 review execution checklist、review result/status、evidence items readiness、operator notes、reviewer notes、blocked reason、next evidence request、source boundary、ACK-not-delivery 和 `not_proven` 的可见口径。
- Objective 5：没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity 或 production worker/migration，不调整。
- Objective 1/2/3：没有硬件、导航、任务状态机、WAVE ROVER、串口、HIL、Nav2/fixed-route 或真实 delivery，不调整。

## 本轮核心抓手

核心抓手是 `mobile_real_device_review_execution*`。它把上一轮 `mobile_real_device_review_handoff*` 变成可记录人工评审执行状态的包，但不新增任何 robot control 语义，不放行 Start/Confirm/Cancel，也不把 ACK、HTTP accepted、review executed 或 execution-ready 解释为 delivery success。

## 实际改动文件

Task A Full-stack：

- `mobile/web/index.html`
- `mobile/web/app.js`
- `mobile/fixtures/mobile_web_status.fixture.json`
- `mobile/test_mobile_web_entrypoint.py`
- `mobile/README.md`
- `docs/product/mobile_user_flow.md`

Task B Robot：

- `onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py`
- `onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py`
- `docs/interfaces/ros_contracts.md`

Task C Product：

- `OKR.md`
- `docs/process/okr_progress_log.md`
- `sprints/2026.05.14_06-07_mobile-real-device-review-execution-gate/tech-done.md`
- `sprints/2026.05.14_06-07_mobile-real-device-review-execution-gate/side2side_check.md`
- `sprints/2026.05.14_06-07_mobile-real-device-review-execution-gate/final.md`

## 验收结果

Task A 返回：

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest mobile.test_mobile_web_entrypoint
Ran 27 tests in 0.021s
OK

py_compile pass
node --check mobile/web/app.js pass
rg pass
scoped diff check pass
```

Task B 返回：

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py
Ran 145 tests in 73.597s
OK

py_compile pass
rg pass
scoped diff check pass
```

Task C 本地验收：

```text
test -f tech-done.md && test -f side2side_check.md && test -f final.md
pass

rg -n "software_proof_docker_mobile_real_device_review_execution_gate|mobile_real_device_review_execution|Objective 5|Objective 4|not_proven|metadata-only|delivery success|review execution" OKR.md docs/process/okr_progress_log.md sprints/2026.05.14_06-07_mobile-real-device-review-execution-gate
pass

git diff --check -- OKR.md docs/process/okr_progress_log.md sprints/2026.05.14_06-07_mobile-real-device-review-execution-gate
pass
```

## 失败定位

- Task A 首次 unit run 因 fixture copy 出现英文 `artifact` 命中敏感词围栏，已改为中文安全摘要并复验通过。
- Task B 未返回失败。
- Task C 未发现 closeout 文档验收失败。

## 风险、阻塞和需要补齐的证据链

- review execution package 是人工评审执行记录，不是验收通过。
- `software_proof_docker_mobile_real_device_review_execution_gate` 只证明 Docker/local mobile software proof + robot metadata-only fence。
- 仍缺真实 iPhone/Android、真实手机浏览器行为、production app、真实 PWA install prompt/user choice。
- 仍缺真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker/migration。
- 仍缺 Nav2/fixed-route、WAVE ROVER、串口、HIL、真实 dropoff/cancel completion 和 delivery success。

## 下一步

如果继续没有 O5 外部材料，下一轮应使用本轮 review execution package 进入 Objective 4 的真实设备材料导入、真实 device behavior 记录、production app 或真实 PWA install prompt/user choice 实证。若拿到真实公网、4G/SIM、OSS/CDN、production DB/queue 或 worker/migration 材料，则回到 Objective 5。
