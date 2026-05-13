# Sprint 2026.05.13_21-22 Mobile Recovery Decision Gate - Final

## 用户价值和产品北极星

本轮把手机端从“能否发车”推进到“异常时下一步怎么做”。普通用户不需要理解 ACK、cursor、remote bridge 或 ROS2 状态机，也能看到恢复状态、阻塞原因、支持入口和保守下一步。这服务于北极星：让不会电脑和硬件的用户用手机完成低成本垃圾投递机器人任务，并在失败时知道如何处理。

## OKR 映射和 KR 拆解

- Objective 4 KR1：手机端最小流程补齐“查看状态 -> 处理异常”。
- Objective 4 KR5：普通用户不接触命令行、不理解 ROS2，也能知道失败时该怎么做。
- Objective 4 KR7：手机端主路径继续向可直接使用推进，但证据仍限 Docker/local software proof。
- Objective 5：本轮未新增真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity 或 production worker/migration，因此不提升。

本轮 OKR 调整：Objective 4 从约 73% 谨慎上调到约 74%；Objective 5 保持约 68%；Objective 1/2/3 不调整。

## 本轮核心抓手

核心抓手是 `software_proof_docker_mobile_recovery_decision_gate`：在 `mobile/web/` 三步主路径之后加入只读恢复决策面板，并用 robot metadata-only fence 证明该 summary 不污染 command、ACK 或 cursor。

## 实际改动文件

- `OKR.md`
- `docs/process/okr_progress_log.md`
- `sprints/2026.05.13_21-22_mobile-recovery-decision-gate/tech-done.md`
- `sprints/2026.05.13_21-22_mobile-recovery-decision-gate/side2side_check.md`
- `sprints/2026.05.13_21-22_mobile-recovery-decision-gate/final.md`

A/B 已完成但不属于 Task C 改动范围的文件：`mobile/web/index.html`、`mobile/web/app.js`、`mobile/web/styles.css`、`mobile/fixtures/mobile_web_status.fixture.json`、`mobile/test_mobile_web_entrypoint.py`、`mobile/README.md`、`docs/product/mobile_user_flow.md`、`onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py`、`onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py`、`docs/interfaces/ros_contracts.md`。

## A/B 验证证据

Task A Full-stack：

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest mobile.test_mobile_web_entrypoint
Ran 17 tests in 0.007s
OK

py_compile exit 0
scoped diff check exit 0
node --check mobile/web/app.js passed
fixture JSON parse passed
```

Task B Robot：

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py
Ran 109 tests in 56.010s
OK

py_compile exit 0
scoped diff check exit 0
```

## Task C 验收命令

```text
test -f sprints/2026.05.13_21-22_mobile-recovery-decision-gate/tech-done.md && test -f sprints/2026.05.13_21-22_mobile-recovery-decision-gate/side2side_check.md && test -f sprints/2026.05.13_21-22_mobile-recovery-decision-gate/final.md
```

结果：exit 0。

```text
rg -n "software_proof_docker_mobile_recovery_decision_gate|Objective 4|Objective 5|ACK|cancel completed|not_proven" OKR.md docs/process/okr_progress_log.md sprints/2026.05.13_21-22_mobile-recovery-decision-gate
```

结果：exit 0，关键命中如下。

```text
OKR.md:159:| Objective 4 ... 约 74% | ... software_proof_docker_mobile_recovery_decision_gate ... ACK ... not_proven ... cancel completed ...
OKR.md:160:| Objective 5 ... 约 68% | ... Objective 5 保持约 68%，不因 software_proof_docker_mobile_recovery_decision_gate 上调 ...
OKR.md:162:本轮 OKR 口径：Objective 4 从约 73% 谨慎上调到约 74% ... ACK、HTTP accepted、receipt 和 recovery decision 仍只是 accepted/processing/support evidence ...
docs/process/okr_progress_log.md:15:... software_proof_docker_mobile_recovery_decision_gate ... ACK 语义 ... not_proven ... cancel completed ...
docs/process/okr_progress_log.md:19:该证据只支持 Objective 4 从约 73% 保守上调到约 74% ... Objective 5 保持约 68% ...
sprints/2026.05.13_21-22_mobile-recovery-decision-gate/tech-done.md:75:- not_proven ...
sprints/2026.05.13_21-22_mobile-recovery-decision-gate/side2side_check.md:27:- 本轮证据边界：software_proof_docker_mobile_recovery_decision_gate
```

```text
git diff --check -- OKR.md docs/process/okr_progress_log.md sprints/2026.05.13_21-22_mobile-recovery-decision-gate
```

结果：exit 0。

## OKR 最低优先级核对复盘

- tech-plan 中的最低完成度 Objective 是 Objective 5（约 68%）。
- 本轮没有针对 Objective 5，因为 A/B 没有拿到真实外部 O5 材料：真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity 或 production worker/migration。
- Objective 4 是 Docker-only 下最低可推进目标，本轮恢复决策补齐了手机异常处理与用户支持入口。
- 因此 final 维持 tech-plan 判断：Objective 5 保持约 68%，Objective 4 谨慎上调到约 74%。

## 风险和证据边界

- `software_proof_docker_mobile_recovery_decision_gate` 只证明 Docker/local 手机恢复决策和 robot metadata-only 围栏。
- `not_proven`：真实 iPhone/Android device behavior、production app、真实 PWA install prompt、真实 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、production worker/migration、Nav2/fixed-route、WAVE ROVER、HIL、真实 cancel completed、真实 dropoff completed、真实 delivery。
- ACK、HTTP accepted、receipt 和 recovery decision 只是 accepted/processing/support evidence，不是 delivery success、dropoff success 或 cancel completed。

## 下一步

下一轮若能提供真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity 或 production worker/migration，应回到 Objective 5。若仍没有外部材料，应继续推进 Objective 4 的真实 iPhone/Android device behavior、production app、真实 PWA install prompt 或真实移动设备验收。
