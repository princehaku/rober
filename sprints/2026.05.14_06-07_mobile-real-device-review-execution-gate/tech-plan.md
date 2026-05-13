# Sprint 2026.05.14_06-07 Mobile Real Device Review Execution Gate - Tech Plan

## 目标

实现 `software_proof_docker_mobile_real_device_review_execution_gate`：基于上一轮 `software_proof_docker_mobile_real_device_review_handoff_gate`，把真实设备人工评审从 handoff package 推进到可记录执行状态的 review execution checklist/package，并用 Robot metadata-only fence 证明该 metadata 不会触发 robot command、ACK、cursor、terminal ACK、production readiness、HIL、dropoff/cancel success 或 delivery success。

## OKR 最低优先级核对

1. 当前 `OKR.md` 4.1 完成度最低的是 Objective 5，约 68%；Objective 4 当前约 82%。
2. 本 sprint 不直接针对 Objective 5，转向 Objective 4。
3. 理由：`OKR.md` 第 6 节明确要求，只有拿到真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity 或 production worker/migration 等真实外部材料时，才应继续推进 Objective 5 completion。当前本机只有 Docker，没有真实硬件、真实手机和 O5 外部材料；继续做本地 Objective 5 metadata 会重复消费同一外部证据 blocker。上一轮 Objective 4 已完成 `software_proof_docker_mobile_real_device_review_handoff_gate`，最新 final 明确下一步是在没有 O5 外部材料时进入 Objective 4 的真实设备人工验收执行、证据导入或真实 device behavior 记录。因此本轮选择 `software_proof_docker_mobile_real_device_review_execution_gate`，把 review handoff package 推进为执行记录，同时继续保留 `not_proven`。

## 任务拆分

### Task A - Full-stack：手机/PWA review execution gate

责任角色：`full-stack-software-engineer`

允许改动文件：

- `mobile/web/index.html`
- `mobile/web/app.js`
- `mobile/web/styles.css`
- `mobile/fixtures/mobile_web_status.fixture.json`
- `mobile/test_mobile_web_entrypoint.py`
- `mobile/README.md`
- `docs/product/mobile_user_flow.md`
- `sprints/2026.05.14_06-07_mobile-real-device-review-execution-gate/tech-done.md`

实现要求：

- 新增或派生 `mobile_real_device_review_execution`、`mobile_real_device_review_execution_summary`、`mobile_real_device_review_execution_package`。
- 支持从 `mobile_real_device_review_handoff`、`mobile_real_device_review_handoff_summary`、`mobile_real_device_review_handoff_package` 派生 review execution。
- 首屏展示 review execution checklist、review result/status、evidence items readiness、operator notes、reviewer notes、blocked reason、next evidence request、redaction status、source boundary、ACK-not-delivery 和 `not_proven`。
- copied package 必须过滤敏感字段：token、Authorization、OSS AK/SK、root password、DB/queue URL、raw ROS topic、`/cmd_vel`、serial、baudrate、WAVE ROVER、本地路径、traceback、checksum、complete artifact、raw robot response。
- 缺真实设备材料、production app 或真实 PWA install prompt/user choice 时，Start Delivery、Confirm Dropoff、Cancel 必须继续 fail closed。
- 文档必须说明 review execution package 只表示人工评审执行记录，不是真实设备验收通过、真实 PWA prompt、HIL、O5 外部 proof 或 delivery success。

验收命令：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest mobile.test_mobile_web_entrypoint
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile mobile/test_mobile_web_entrypoint.py
node --check mobile/web/app.js
rg -n "software_proof_docker_mobile_real_device_review_execution_gate|mobile_real_device_review_execution|review execution|review result|evidence items readiness|operator notes|reviewer notes|blocked reason|next evidence request|ACK|not_proven|PWA install prompt|production app" mobile docs/product/mobile_user_flow.md
git diff --check -- mobile/web/index.html mobile/web/app.js mobile/web/styles.css mobile/fixtures/mobile_web_status.fixture.json mobile/test_mobile_web_entrypoint.py mobile/README.md docs/product/mobile_user_flow.md sprints/2026.05.14_06-07_mobile-real-device-review-execution-gate/tech-done.md
```

### Task B - Robot：metadata-only response fence

责任角色：`robot-software-engineer`

允许改动文件：

- `onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py`
- `onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py`
- `docs/interfaces/ros_contracts.md`
- `sprints/2026.05.14_06-07_mobile-real-device-review-execution-gate/tech-done.md`

实现要求：

- 为 `mobile_real_device_review_execution`、`mobile_real_device_review_execution_summary`、`mobile_real_device_review_execution_package` 增加 metadata-only response fence。
- 证明无 command envelope 时不触发 collect、confirm_dropoff、cancel、ACK POST、cursor advance、cursor persistence、terminal ACK、production readiness、HIL、dropoff success、cancel completed 或 delivery success。
- 证明 valid command mixed metadata 时只执行 command envelope，review execution metadata 不进入 normalized command、ACK、status、cursor 或 terminal result。
- 文档明确该 metadata 只服务 phone/support/product review execution，不得写入 robot control semantics。

验收命令：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py
rg -n "mobile_real_device_review_execution|software_proof_docker_mobile_real_device_review_execution_gate|metadata-only|delivery success|cursor|terminal ACK|production readiness|HIL" onboard/src/ros2_trashbot_behavior/test docs/interfaces/ros_contracts.md
git diff --check -- onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py docs/interfaces/ros_contracts.md sprints/2026.05.14_06-07_mobile-real-device-review-execution-gate/tech-done.md
```

### Task C - Product：验收、OKR 和文档收口

责任角色：`product-okr-owner`

允许改动文件：

- `OKR.md`
- `docs/process/okr_progress_log.md`
- `sprints/2026.05.14_06-07_mobile-real-device-review-execution-gate/tech-done.md`
- `sprints/2026.05.14_06-07_mobile-real-device-review-execution-gate/side2side_check.md`
- `sprints/2026.05.14_06-07_mobile-real-device-review-execution-gate/final.md`

实现要求：

- 等 Task A/B 返回后核对验证证据，确认 `software_proof_docker_mobile_real_device_review_execution_gate` 是否成立。
- 若没有真实外部设备材料，不得声明真实 iPhone/Android、production app、PWA prompt/user choice、真实 delivery 或 Objective 5 外部证据通过。
- `OKR.md` 只允许在证据充分时谨慎更新 Objective 4；Objective 5 没有真实外部材料时保持约 68%。
- `docs/process/okr_progress_log.md` 必须记录本轮从 review handoff 到 review execution 的证据边界和未证明项。
- `side2side_check.md` 和 `final.md` 必须回顾 Objective 5 最低但不选的理由是否仍成立。
- 收口语言必须明确：review execution package 是人工评审执行记录，不是验收通过、HIL、真实 dropoff/cancel completion 或 delivery success。

验收命令：

```bash
test -f sprints/2026.05.14_06-07_mobile-real-device-review-execution-gate/tech-done.md && test -f sprints/2026.05.14_06-07_mobile-real-device-review-execution-gate/side2side_check.md && test -f sprints/2026.05.14_06-07_mobile-real-device-review-execution-gate/final.md
rg -n "software_proof_docker_mobile_real_device_review_execution_gate|mobile_real_device_review_execution|Objective 5|Objective 4|not_proven|metadata-only|delivery success|review execution" OKR.md docs/process/okr_progress_log.md sprints/2026.05.14_06-07_mobile-real-device-review-execution-gate
git diff --check -- OKR.md docs/process/okr_progress_log.md sprints/2026.05.14_06-07_mobile-real-device-review-execution-gate
```

## 并行执行规则

Task A 与 Task B 文件范围互不重叠，必须并行启动 `full-stack-software-engineer` 与 `robot-software-engineer`。Task C 在 A/B 返回后执行验收、OKR closeout 和 sprint 收口。Hardware 与 Autonomy 本轮无实现任务；若执行中发现需要硬件、Nav2 或 route 事实，只做只读事实补充，不扩大改动范围。

## 接口影响

- 新增 review execution metadata 字段，不新增 robot command。
- 不改变 `/api/collect`、`/api/dropoff/confirm`、`/api/cancel` 的控制语义。
- 不改变 ACK、cursor、delivery result、terminal result、production readiness、HIL 或 robot status 成功语义。
- 不引入云端生产依赖，不要求真实设备自动化测试环境。

## 风险边界

- 本轮最高证据等级是 Docker/local software proof + Robot metadata-only fence。
- review executed、review-ready、accepted-for-review 或 execution-ready 只表示人工评审执行记录存在，不等于真实设备通过。
- `not_proven` 必须保留真实手机设备、production app、真实 PWA install prompt/user choice、真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、Nav2/fixed-route、WAVE ROVER、HIL、真实 dropoff/cancel/delivery。
- 若导入材料未脱敏或包含敏感字段，必须输出 blocked/rejected 状态或等价 evidence blocker，而不是复制原文。

## 本规划验收命令

```bash
test -f sprints/2026.05.14_06-07_mobile-real-device-review-execution-gate/pre_start.md && test -f sprints/2026.05.14_06-07_mobile-real-device-review-execution-gate/prd.md && test -f sprints/2026.05.14_06-07_mobile-real-device-review-execution-gate/tech-plan.md
rg -n "sprint_type: epic|OKR 最低优先级核对|Objective 5|Objective 4|software_proof_docker_mobile_real_device_review_execution_gate|mobile_real_device_review_execution|metadata-only|not_proven" sprints/2026.05.14_06-07_mobile-real-device-review-execution-gate
git diff --check -- sprints/2026.05.14_06-07_mobile-real-device-review-execution-gate
```
