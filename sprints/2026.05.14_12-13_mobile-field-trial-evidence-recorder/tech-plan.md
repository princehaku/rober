# Sprint 2026.05.14_12-13 Mobile Field Trial Evidence Recorder - Tech Plan

## OKR 最低优先级核对

1. 当前 `OKR.md` 4.1 节完成度最低的 Objective：Objective 5 云中转 + OSS/CDN 数据通路产品化，约 68%。
2. 本 sprint 是否针对该最低 Objective：否，本 sprint 主目标转向 Objective 4 手机用户体验与低成本量产边界。
3. 不针对 Objective 5 的具体理由：最新 `OKR.md` 4.1 与 `sprints/2026.05.14_11-12_mobile-field-trial-runbook-execution-gate/final.md` 均说明 Objective 5 仍缺真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker/migration 等外部材料。当前本机无法补齐这些材料，继续 O5 只会堆本地 metadata。按 stop rule，本轮转向 Objective 4 的可执行缺口：把上一轮“现场试跑执行清单”推进为 `mobile_real_device_field_trial_evidence_record*` 现场证据记录入口。
4. final.md 收口时必须回顾：若 A/B 期间拿到真实 O5 外部材料，Product closeout 需要重新评估 Objective 5；否则本轮只允许围绕 Objective 4 做谨慎进度判断。

## 证据边界和命名

统一 family：

- `mobile_real_device_field_trial_evidence_record`
- `mobile_real_device_field_trial_evidence_record_summary`
- `mobile_real_device_field_trial_evidence_record_copy`
- `mobile_real_device_field_trial_evidence_record_archive`

统一 evidence boundary：

- `software_proof_docker_mobile_real_device_field_trial_evidence_record_gate`

该 gate 只证明 Docker/local `mobile/web` 能结构化记录、展示、复制/归档 phone-safe 现场观察，并且 Robot remote bridge 将其保持为 metadata-only。它不证明真实手机设备通过、真实 iPhone/Android device behavior、production app 通过、真实 PWA install prompt/user choice 通过、真实公网 HTTPS/TLS、真实 4G/SIM、OSS/CDN live traffic、production DB/queue、WAVE ROVER、HIL、真实 dropoff/cancel completion 或 delivery success。

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

- 新增或推进首屏“现场证据记录”入口。
- 生成、展示、复制/归档 `mobile_real_device_field_trial_evidence_record*` package。
- 记录字段覆盖真实手机现场试跑的 real device、production app、PWA install prompt、user choice、offline、touch、visual、material redaction、operator note、support note。
- 保持 `safe_to_control=false`、`ack_semantics=accepted_processing_only_not_delivery_success`、`not_proven`、whitelist-only copy/archive。
- 不暴露 token、Authorization、OSS AK/SK、DB/queue URL、credential-bearing URL、raw ROS topic、`/cmd_vel`、serial/UART、baudrate、WAVE ROVER 参数、本地路径、traceback、checksum、完整 artifacts、raw robot response、raw intake JSON、robot/internal technical fields。
- Start Delivery、Confirm Dropoff、Cancel 继续 fail-closed，不能因为该 record 被启用。
- 代码新增或修改的技术注释必须使用中文，并保持有意义注释比例超过 20%。

接口边界：

- Task A 只能扩展手机端 phone/support metadata family，不改变 `/api/collect`、`/api/dropoff/confirm`、`/api/cancel` 的控制语义。
- 如果需要读取 status/diagnostics 中已有字段，只能消费 phone-safe metadata；缺失字段时生成 blocked/not_proven 的本地记录草案。
- Copy/archive package 必须采用 whitelist-only 字段，不保存原始截图、原始 URL query/hash、完整 artifact、credential-bearing material 或 raw robot response。

验收命令：

```bash
python3 -m unittest mobile.test_mobile_web_entrypoint
python3 -m py_compile mobile/test_mobile_web_entrypoint.py
node --check mobile/web/app.js
rg -n "现场证据记录|mobile_real_device_field_trial_evidence_record|software_proof_docker_mobile_real_device_field_trial_evidence_record_gate|safe_to_control=false|accepted_processing_only_not_delivery_success|not_proven" mobile/web mobile/test_mobile_web_entrypoint.py mobile/README.md docs/product/mobile_user_flow.md
git diff --check -- mobile/web/index.html mobile/web/app.js mobile/web/styles.css mobile/test_mobile_web_entrypoint.py mobile/README.md docs/product/mobile_user_flow.md
```

输出要求：

1. 实际改动文件列表。
2. 验证命令输出摘要。
3. 失败定位与修复记录。
4. 剩余风险，尤其是真实手机、production app、PWA prompt、user choice 未证明项。

### Task B - Robot Platform Engineer

Owner：`robot-software-engineer`

允许改动：

- `onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py`
- `onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py`
- `docs/interfaces/ros_contracts.md`

目标：

- 新增 `mobile_real_device_field_trial_evidence_record*` metadata-only family 围栏。
- 证明该 family 不触发 command、ACK、cursor、terminal ACK、production readiness、HIL、dropoff/cancel completion 或 delivery success。
- mixed valid-command payload 中只执行 `trashbot.remote.v1` command envelope；evidence record metadata 不改变 command 语义。
- `docs/interfaces/ros_contracts.md` 明确该 package 是 phone/support metadata，不是 robot command、ACK、cursor、terminal result、production readiness grant、HIL 或真实送达证据。
- 代码新增或修改的技术注释必须使用中文，并保持有意义注释比例超过 20%。

接口边界：

- Task B 不改变 remote command envelope、ACK contract、cursor persistence、terminal result 或 production readiness 判定。
- `mobile_real_device_field_trial_evidence_record*` 只能作为 metadata-only payload 被忽略或归类，不得进入 backend action、ACK POST、cursor advance/persistence、dropoff/cancel terminal ACK 或 delivery success 路径。
- mixed payload 测试必须证明 valid-command 和 metadata family 的分离：有效 `trashbot.remote.v1` command 仍可按既有逻辑执行，evidence record metadata 不改变 action、target、idempotency、ACK 或 cursor 语义。

验收命令：

```bash
python3 -m unittest onboard.src.ros2_trashbot_behavior.test.test_remote_bridge onboard.src.ros2_trashbot_behavior.test.test_remote_bridge_protocol
python3 -m py_compile onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py
rg -n "mobile_real_device_field_trial_evidence_record|software_proof_docker_mobile_real_device_field_trial_evidence_record_gate|metadata-only|accepted_processing_only_not_delivery_success|delivery success|HIL|terminal ACK" onboard/src/ros2_trashbot_behavior/test docs/interfaces/ros_contracts.md
git diff --check -- onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py docs/interfaces/ros_contracts.md
```

输出要求：

1. 实际改动文件列表。
2. 验证命令输出摘要。
3. 失败定位与修复记录。
4. 剩余风险，尤其是 metadata-only fence 覆盖边界。

## 集成顺序

1. 并行启动 Task A 与 Task B。
2. A/B 都返回后，Product Owner 核对 package family、evidence boundary、`safe_to_control=false`、ACK 非 delivery success、`not_proven`、whitelist-only copy/archive 和 metadata-only fence 是否一致。
3. 若 A/B 验证失败或证据不足，将失败定位交回对应 Engineer 重试。
4. A/B 验证通过后执行 Product closeout，更新 `tech-done.md`、`side2side_check.md`、`final.md`、`OKR.md` 和 `docs/process/okr_progress_log.md`。

## 验证围栏

本轮禁止 broad test suite。只运行各 owner 的 targeted unittest、`py_compile`、`node --check`、required `rg` 和 scoped `git diff --check`。

本计划文件自身验收命令：

```bash
test -f sprints/2026.05.14_12-13_mobile-field-trial-evidence-recorder/pre_start.md && test -f sprints/2026.05.14_12-13_mobile-field-trial-evidence-recorder/prd.md && test -f sprints/2026.05.14_12-13_mobile-field-trial-evidence-recorder/tech-plan.md
rg -n "sprint_type: epic|OKR 最低优先级核对|Objective 5|Objective 4|mobile_real_device_field_trial_evidence_record|safe_to_control=false|metadata-only|not_proven" sprints/2026.05.14_12-13_mobile-field-trial-evidence-recorder
git diff --check -- sprints/2026.05.14_12-13_mobile-field-trial-evidence-recorder
```

## 剩余风险和阻塞

- 真实 O5 外部材料仍缺：不能提升 Objective 5。
- Docker-only：不能证明真实手机、production app、真实 PWA install prompt/user choice、真实 4G/SIM、真实云、WAVE ROVER、HIL 或 delivery success。
- 文案风险：任何“现场证据记录”都不能写成“现场试跑已通过”。
- 解析风险：Robot fence 必须覆盖 metadata-only 和 mixed valid-command 两种路径，否则 package family 可能污染 command 语义。
- 归档风险：记录入口必须只归档脱敏后的 whitelist-only 字段，不能把原始敏感材料变成 repo 或 copy package 内容。
