# Sprint 2026.05.14_11-12 Mobile Field Trial Runbook Execution Gate - Tech Plan

## OKR 最低优先级核对

1. 当前 `OKR.md` 4.1 节完成度最低的 Objective：Objective 5 云中转 + OSS/CDN 数据通路产品化，约 68%。
2. 本 sprint 是否针对该最低 Objective：否，本 sprint 主目标转向 Objective 4 手机用户体验与低成本量产边界。
3. 不针对 Objective 5 的具体理由：`OKR.md` 第 6 节明确，只有拿到真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity 或 production worker/migration 材料时才继续 O5 completion。当前本机 Docker-only，没有这些真实外部材料；继续 O5 只会重复本地 metadata depth。最新 `2026.05.14_10-11_mobile-field-trial-evidence-review-gate/final.md` 建议在无 O5 外部材料时继续 Objective 4 的真实 iPhone/Android device behavior、production app、真实 PWA install prompt/user choice 或主路径真实移动设备验收。因此本轮转向 O4 的“现场试跑执行清单 / runbook execution package”。
4. final.md 收口时必须回顾：若 A/B 期间拿到真实 O5 外部材料，Product closeout 需要重新评估 Objective 5；否则本轮只允许围绕 Objective 4 做谨慎进度判断。

## 证据边界和命名

统一 family：

- `mobile_real_device_field_trial_runbook_execution`
- `mobile_real_device_field_trial_runbook_execution_summary`
- `mobile_real_device_field_trial_runbook_execution_copy`

统一 evidence boundary：

- `software_proof_docker_mobile_real_device_field_trial_runbook_execution_gate`

该 gate 只证明 Docker/local `mobile/web` 能生成 phone-safe 现场试跑执行清单和 copy package，并且 Robot remote bridge 将其保持为 metadata-only。它不证明真实手机、真实 iPhone/Android device behavior、production app、真实 PWA install prompt/user choice、真实云、真实 4G/SIM、OSS/CDN live traffic、production DB/queue、WAVE ROVER、HIL、真实 dropoff/cancel completion 或 delivery success。

## 并行任务拆分

### Task A - User Touchpoint Full-Stack Engineer

Owner：`full-stack-software-engineer`

允许改动：

- `mobile/web/index.html`
- `mobile/web/app.js`
- `mobile/web/styles.css`
- `mobile/test_mobile_web_entrypoint.py`
- `mobile/README.md`
- `docs/product/mobile_user_flow.md`

目标：

- 新增首屏“现场试跑执行清单”panel。
- 生成/展示/复制 `mobile_real_device_field_trial_runbook_execution*` package。
- 执行清单覆盖真实手机现场试跑下一次执行所需的 real device、production app、PWA install prompt、user choice、offline、touch、visual、material redaction。
- 保持 `safe_to_control=false`、`ack_semantics=accepted_processing_only_not_delivery_success`、`not_proven`、whitelist-only copy。
- 不暴露 token、Authorization、OSS AK/SK、DB/queue URL、credential-bearing URL、raw ROS topic、`/cmd_vel`、serial/UART、baudrate、WAVE ROVER 参数、本地路径、traceback、checksum、完整 artifacts、raw robot response、robot/internal technical fields。
- Start Delivery、Confirm Dropoff、Cancel 继续 fail-closed，不能因为该 package 被启用。
- 代码新增或修改的技术注释必须使用中文，并保持有意义注释比例超过 20%。

验收命令：

```bash
python3 -m unittest mobile.test_mobile_web_entrypoint
python3 -m py_compile mobile/test_mobile_web_entrypoint.py
node --check mobile/web/app.js
rg -n "现场试跑执行清单|mobile_real_device_field_trial_runbook_execution|software_proof_docker_mobile_real_device_field_trial_runbook_execution_gate|safe_to_control=false|accepted_processing_only_not_delivery_success|not_proven" mobile/web mobile/test_mobile_web_entrypoint.py mobile/README.md docs/product/mobile_user_flow.md
git diff --check -- mobile/web/index.html mobile/web/app.js mobile/web/styles.css mobile/test_mobile_web_entrypoint.py mobile/README.md docs/product/mobile_user_flow.md
```

输出要求：

1. 实际改动文件列表。
2. 验证命令输出摘要。
3. 失败定位与修复记录。
4. 剩余风险，尤其是真实手机/production app/PWA prompt 未证明项。

### Task B - Robot Platform Engineer

Owner：`robot-software-engineer`

允许改动：

- `onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py`
- `onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py`
- `docs/interfaces/ros_contracts.md`

目标：

- 新增 `mobile_real_device_field_trial_runbook_execution*` metadata-only family 围栏。
- 证明该 family 不触发 command、ACK、cursor、terminal ACK、production readiness、HIL、dropoff/cancel completion 或 delivery success。
- mixed valid-command payload 中只执行 `trashbot.remote.v1` command envelope；runbook execution metadata 不改变 command 语义。
- `docs/interfaces/ros_contracts.md` 明确该 package 是 phone/support metadata，不是 robot command、ACK、cursor、terminal result、production readiness grant 或真实送达证据。
- 代码新增或修改的技术注释必须使用中文，并保持有意义注释比例超过 20%。

验收命令：

```bash
python3 -m unittest onboard.src.ros2_trashbot_behavior.test.test_remote_bridge onboard.src.ros2_trashbot_behavior.test.test_remote_bridge_protocol
python3 -m py_compile onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py
rg -n "mobile_real_device_field_trial_runbook_execution|software_proof_docker_mobile_real_device_field_trial_runbook_execution_gate|metadata-only|accepted_processing_only_not_delivery_success|delivery success|HIL|terminal ACK" onboard/src/ros2_trashbot_behavior/test docs/interfaces/ros_contracts.md
git diff --check -- onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py docs/interfaces/ros_contracts.md
```

输出要求：

1. 实际改动文件列表。
2. 验证命令输出摘要。
3. 失败定位与修复记录。
4. 剩余风险，尤其是 metadata-only fence 覆盖边界。

### Task C - Product Closeout

Owner：`product-okr-owner`

允许改动：

- `sprints/2026.05.14_11-12_mobile-field-trial-runbook-execution-gate/tech-done.md`
- `sprints/2026.05.14_11-12_mobile-field-trial-runbook-execution-gate/side2side_check.md`
- `sprints/2026.05.14_11-12_mobile-field-trial-runbook-execution-gate/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`

目标：

- 汇总 Task A/B 的实际改动和验证证据。
- 更新 sprint closeout 和 OKR 进度。
- 明确 `software_proof_docker_mobile_real_device_field_trial_runbook_execution_gate` 只是 Docker/local mobile software proof。
- 若无真实 O5 外部材料，Objective 5 保持约 68%，只围绕 Objective 4 做谨慎评估。
- 最后提交并推送，提交前排除无关 local churn。

验收命令：

```bash
rg -n "software_proof_docker_mobile_real_device_field_trial_runbook_execution_gate|mobile_real_device_field_trial_runbook_execution|Objective 5|Objective 4|safe_to_control=false|accepted_processing_only_not_delivery_success|not_proven|现场试跑执行" OKR.md docs/process/okr_progress_log.md sprints/2026.05.14_11-12_mobile-field-trial-runbook-execution-gate
git diff --check -- OKR.md docs/process/okr_progress_log.md sprints/2026.05.14_11-12_mobile-field-trial-runbook-execution-gate
```

输出要求：

1. 实际改动文件列表。
2. 验证命令输出摘要。
3. 失败定位与修复记录。
4. 剩余风险和下一步建议。

## 集成顺序

1. 并行启动 Task A 与 Task B。
2. A/B 都返回后，Product Owner 核对 package family、evidence boundary、`safe_to_control=false`、ACK 非 delivery success、`not_proven`、whitelist-only copy 和 metadata-only fence 是否一致。
3. 若 A/B 验证失败或证据不足，将失败定位交回对应 Engineer 重试。
4. A/B 验证通过后执行 Task C closeout。

## 验证围栏

本轮禁止 broad test suite。只运行各 owner 的 targeted unittest、`py_compile`、`node --check`、required `rg` 和 scoped `git diff --check`。

本计划文件自身验收命令：

```bash
test -f sprints/2026.05.14_11-12_mobile-field-trial-runbook-execution-gate/pre_start.md && test -f sprints/2026.05.14_11-12_mobile-field-trial-runbook-execution-gate/prd.md && test -f sprints/2026.05.14_11-12_mobile-field-trial-runbook-execution-gate/tech-plan.md
rg -n "sprint_type: epic|OKR 最低优先级核对|Objective 5|Objective 4|software_proof_docker_mobile_real_device_field_trial|safe_to_control=false|accepted_processing_only_not_delivery_success|not_proven|现场试跑执行" sprints/2026.05.14_11-12_mobile-field-trial-runbook-execution-gate
git diff --check -- sprints/2026.05.14_11-12_mobile-field-trial-runbook-execution-gate
```

## 风险和阻塞

- 真实 O5 外部材料仍缺：不能提升 Objective 5。
- Docker-only：不能证明真实手机、production app、真实 PWA install prompt/user choice、真实 4G/SIM、真实云、WAVE ROVER、HIL 或 delivery success。
- 文案风险：任何“执行清单”都不能写成“现场试跑已通过”。
- 解析风险：Robot fence 必须覆盖 metadata-only 和 mixed valid-command 两种路径，否则 package family 可能污染 command 语义。
