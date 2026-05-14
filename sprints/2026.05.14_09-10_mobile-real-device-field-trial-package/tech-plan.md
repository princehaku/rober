# Sprint 2026.05.14_09-10 Mobile Real Device Field Trial Package - Tech Plan

## OKR 最低优先级核对

1. 当前 `OKR.md` 4.1 完成度最低的是 Objective 5，约 68%。
2. 本 sprint 不直接针对 Objective 5；本 sprint 针对 Objective 4 的真实设备/production app/PWA install prompt 主路径缺口。
3. 不针对 Objective 5 的理由：`OKR.md` 4.1 和最近 `2026.05.14_08-09_mobile-current-pwa-retest-browser-proof` final 均确认，本机只有 Docker/local Chromium proof，没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker/migration 或其他真实外部 O5 材料。继续增加 O5 本地 metadata 会重复消费同一 blocker，不能形成真实外部 proof。按 stop rule，本轮转向 Objective 4 的真实设备现场试跑入口，但边界仅为 `software_proof_docker_mobile_real_device_field_trial_package_gate`。

## 方案概览

新增 `mobile_real_device_field_trial_package*` phone-safe metadata family，为真实 iPhone/Android 或 production app 现场试跑提供复制入口。该 family 只记录当前设备/browser 可安全暴露的信息和人工 observation fields，不授予控制权，不触发机器人命令，不提升 Objective 5。

本轮必须并行启动 Task A 和 Task B。Task C 等 Task A/B 返回后再执行 closeout。

## Task A：Full-stack field trial package UI/logic/tests/docs

Owner：`full-stack-software-engineer`

允许改动：

- `mobile/web/index.html`
- `mobile/web/app.js`
- `mobile/web/styles.css`
- `mobile/test_mobile_web_entrypoint.py`
- `mobile/README.md`
- `docs/product/mobile_user_flow.md`
- `sprints/2026.05.14_09-10_mobile-real-device-field-trial-package/tech-done.md`

实现要求：

- 在 `mobile/web` 首屏新增“真实设备现场试跑包 / field trial package”panel。
- 自动采集 phone-safe runtime metadata：viewport CSS width/height、device pixel ratio、orientation、touch capability、display-mode、manifest link presence、service worker support/registration hint、offline shell hint、client timestamp、entry URL summary。
- 新增人工 observation fields：device type、OS/browser、production app observed、PWA install prompt observed、user choice、offline reload observed、touch target issue、visual issue、operator note、support note。
- 生成 `mobile_real_device_field_trial_package`、`mobile_real_device_field_trial_package_summary`、`mobile_real_device_field_trial_package_copy`。
- schema 使用 `trashbot.mobile_real_device_field_trial_package.v1`，evidence boundary 使用 `software_proof_docker_mobile_real_device_field_trial_package_gate`。
- copy package 必须 whitelist-only，必须保留 `safe_to_control=false`、`ack_semantics=accepted_processing_only_not_delivery_success`、`not_proven`。
- copy package 不得包含 token、Authorization、OSS AK/SK、root password、DB/queue URL、raw ROS topic、`/cmd_vel`、serial、baudrate、WAVE ROVER、local filesystem path、traceback、checksum、complete artifacts、raw robot responses 或 robot/internal technical fields。
- Start Delivery、Confirm Dropoff、Cancel 继续由既有 `command_safety`、readiness、operation log 和 action feedback gates 控制；field trial package 不得新增控制授予条件。
- 文档必须明确本轮是 Docker/local mobile software proof，不是真实 iPhone/Android、production app、真实 PWA install prompt/user choice、Objective 5 外部 proof、HIL 或 delivery success。

验收命令：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest mobile.test_mobile_web_entrypoint
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile mobile/test_mobile_web_entrypoint.py
node --check mobile/web/app.js
rg -n "software_proof_docker_mobile_real_device_field_trial_package_gate|mobile_real_device_field_trial_package|accepted_processing_only_not_delivery_success|not_proven|safe_to_control=false|真实设备现场试跑包" mobile/web/index.html mobile/web/app.js mobile/test_mobile_web_entrypoint.py mobile/README.md docs/product/mobile_user_flow.md
git diff --check -- mobile/web/index.html mobile/web/app.js mobile/web/styles.css mobile/test_mobile_web_entrypoint.py mobile/README.md docs/product/mobile_user_flow.md sprints/2026.05.14_09-10_mobile-real-device-field-trial-package/tech-done.md
```

## Task B：Robot metadata-only compatibility fence

Owner：`robot-software-engineer`

允许改动：

- `onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py`
- `onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py`
- `docs/interfaces/ros_contracts.md`
- `sprints/2026.05.14_09-10_mobile-real-device-field-trial-package/tech-done.md`

实现要求：

- 新增 `mobile_real_device_field_trial_package`、`mobile_real_device_field_trial_package_summary`、`mobile_real_device_field_trial_package_copy` 的 metadata-only / mixed valid-command fence。
- 证明无 command envelope 时，field trial package metadata 不触发 collect、confirm_dropoff、cancel、ACK POST、cursor advance、cursor persistence、terminal ACK、production readiness、HIL、dropoff success、cancel completed 或 delivery success。
- 证明 mixed valid-command response 仍只执行 `trashbot.remote.v1` command envelope，field trial package metadata 不进入 normalized command、ACK、status、cursor 或 terminal result。
- `docs/interfaces/ros_contracts.md` 必须明确该 metadata 只服务 phone/support/product field trial handoff，不是 robot command、ACK、cursor、terminal result、production readiness、HIL 或 delivery proof。

验收命令：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py
rg -n "mobile_real_device_field_trial_package|metadata-only|delivery success|HIL|production readiness|cursor|ACK" onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py docs/interfaces/ros_contracts.md
git diff --check -- onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py docs/interfaces/ros_contracts.md sprints/2026.05.14_09-10_mobile-real-device-field-trial-package/tech-done.md
```

## Task C：Product closeout

Owner：`product-okr-owner`

允许改动：

- `OKR.md`
- `docs/process/okr_progress_log.md`
- `sprints/2026.05.14_09-10_mobile-real-device-field-trial-package/tech-done.md`
- `sprints/2026.05.14_09-10_mobile-real-device-field-trial-package/side2side_check.md`
- `sprints/2026.05.14_09-10_mobile-real-device-field-trial-package/final.md`

实现要求：

- 等 Task A/B 返回后再更新 OKR 和 closeout。
- `tech-done.md` 汇总 Task A/B 实际改动、验证输出、失败定位、剩余风险。
- `side2side_check.md` 对照 PRD 验收：phone-safe package、fail-closed、Robot metadata-only fence、boundary wording。
- `final.md` 必须回顾 Objective 5 最低但不选的理由是否仍成立。
- 若 Task A/B 验证均通过，可保守上调 Objective 4；不得上调 Objective 5、Objective 1、Objective 2 或 Objective 3。
- `OKR.md` 和 `docs/process/okr_progress_log.md` 必须明确本轮边界是 `software_proof_docker_mobile_real_device_field_trial_package_gate`。

验收命令：

```bash
test -f sprints/2026.05.14_09-10_mobile-real-device-field-trial-package/tech-done.md && test -f sprints/2026.05.14_09-10_mobile-real-device-field-trial-package/side2side_check.md && test -f sprints/2026.05.14_09-10_mobile-real-device-field-trial-package/final.md
rg -n "software_proof_docker_mobile_real_device_field_trial_package_gate|Objective 5|Objective 4|not_proven|metadata-only|delivery success|真实设备现场试跑包|safe_to_control=false" OKR.md docs/process/okr_progress_log.md sprints/2026.05.14_09-10_mobile-real-device-field-trial-package
git diff --check -- OKR.md docs/process/okr_progress_log.md sprints/2026.05.14_09-10_mobile-real-device-field-trial-package
```

## 并行策略

Task A 和 Task B 文件范围互不重叠，必须在同一轮并行启动：

- Task A owns `mobile/web`、mobile tests、mobile docs。
- Task B owns remote bridge/protocol tests 和 ROS interface contract。
- Task C 不并行修改 OKR；只在 Task A/B 结果可核验后 closeout。

Codex 运行时必须用 `spawn_agent(agent_type=worker)` 派发 Task A/B，prompt 中分别完整复制 `.codex/agents/full-stack-software-engineer.toml` 与 `.codex/agents/robot-software-engineer.toml` 的 `prompt` 字段，并包含本轮任务、文件范围、验收命令、输出要求。

## 接口和证据边界

- 新 metadata family：`mobile_real_device_field_trial_package*`。
- 新 schema：`trashbot.mobile_real_device_field_trial_package.v1`。
- 新 boundary：`software_proof_docker_mobile_real_device_field_trial_package_gate`。
- 证据性质：Docker/local mobile software proof + Robot metadata-only fence。
- 明确不证明：真实手机设备行为、真实 iPhone/Android device behavior、production app、真实 PWA install prompt/user choice、真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、production worker/migration、Nav2/fixed-route、WAVE ROVER、HIL、真实 dropoff/cancel completion 或真实 delivery。

## 质量和验证围栏

- 验证只跑本轮相关 targeted tests、`node --check`、`py_compile`、`rg` boundary check 和 scoped `git diff --check`。
- 不跑 broad regression，不新增大范围测试矩阵。
- 代码技术注释如需新增必须使用中文，并满足项目注释规范。
- 文档更新必须同步 `docs/product/mobile_user_flow.md` 和 `docs/interfaces/ros_contracts.md`。

## 风险

- 本地 Chromium 对 display-mode、service worker、offline 的观测不等同于真实 Safari/Android Chrome/production app 行为。
- 人工 observation fields 可能填写不完整；package 必须保持 blocked/support metadata 语义。
- 如果 Task A/B 中任一验证失败，Task C 不得调整 OKR，只能记录失败定位和剩余风险。
