# Sprint 2026.05.18_23-24 Mobile Real Device Acceptance Execution Pack - Tech Plan

## 1. 技术目标

新增 `mobile_real_device_field_trial_acceptance_execution_pack*`，消费上一轮 `mobile_real_device_field_trial_acceptance_review_handoff*` handoff / summary / copy，输出真实手机现场验收执行包，并通过 mobile/web 只读 panel、Robot diagnostics safe alias、产品文档和接口文档暴露。

本轮所有结果保持 `software_proof`、`not_proven`、`safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`。不得把执行包写成真实手机验收、真实 route/elevator field pass、HIL、dropoff/cancel completion 或 delivery success。

## 2. OKR 最低优先级核对

当前 `OKR.md` 4.1 最新快照：

- Objective 5：约 68%，数字最低。
- Objective 1：约 81%，次低。
- Objective 2 / Objective 3 / Objective 4：约 99%。

本 sprint 不直接推进 Objective 5。原因：Objective 5 下一步只有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker/migration/cutover 或真实手机/browser external proof 才能形成有效进度；当前主机 Docker-only，无真实外部云 proof。继续新增本地 O5 metadata 会重复消费已知 blocker。

本 sprint 不直接推进 Objective 1。原因：Objective 1 需要真实 WAVE ROVER/UART/HIL、`feedback_T1001.log`、真实 `/odom`、`/imu/data`、`/battery`、operator HIL report；PR #5 还暴露 2D LiDAR / ToF 真实 SKU/source/receipt/procurement/installation/wiring/power/calibration/HIL-entry 材料缺口。当前主机没有真实硬件和真实串口，不能把本地软件包写成硬件进度。

本 sprint 选择 Objective 4。原因：20-21 final 已按 PR #4 / PR #5 / OKR 表格完成 rerank，21-22 完成 acceptance review decision，22-23 完成 acceptance review handoff；在没有 O5/O1/PR #4 真实材料时，最可执行的功能推进是把 Objective 4 handoff packet 继续推进为真实手机验收 execution package，让下一轮现场 owner 能采集真实 iPhone/Android / production app / PWA prompt/user choice 材料。

## 3. PR / Review 证据引用

- PR #5 P1：硬件边界文档默认硬件集与 mandatory `monocular + 2D LiDAR + ToF` baseline 曾矛盾，要求后续文档和 OKR 叙事不能把无材料硬件假设写成事实。
- PR #5 P2：sensor mix / ToF channel assumptions 缺 `docs/vendor/` source；本轮若触碰硬件事实必须查 `docs/vendor/VENDOR_INDEX.md`，但本 sprint 不改硬件配置。
- PR #5 P2：OKR lowest narrative 曾与表格不一致；本计划明确 Objective 5 数字最低但不可在 Docker-only 主机推进，Objective 1 次低但硬件材料不可得，Objective 4 是 actionable fallback。
- PR #4：elevator assisted delivery 已并入主线，后续缺真实 route/elevator field materials；本轮不把手机 execution pack 计作真实电梯、Nav2/fixed-route 或 delivery success。
- 20-21 final：确认 O5/O1 真实材料不可得，且 PR #4 route/elevator blocker 不应继续被本地 wrapper 重复消费，转向 Objective 4 真机材料链。
- 21-22 final：`mobile_real_device_field_trial_acceptance_review_decision*` 已完成，Start / Confirm / Cancel 继续 fail-closed。
- 22-23 final：`mobile_real_device_field_trial_acceptance_review_handoff*` 已完成，下一步建议把 handoff packet 带到真实手机现场执行并回填同一 safe `evidence_ref`。

## 4. 并行 owner 分工

### Owner A：User Touchpoint Full-Stack Engineer

- 角色：`full-stack-software-engineer`
- 主责：mobile/web + fixture + docs/product。
- 文件范围：
  - `mobile/web/app.js`
  - `mobile/fixtures/mobile_web_status.fixture.json`
  - `mobile/web/test_mobile_web_entrypoint.py`
  - `docs/product/mobile_user_flow.md`
- 实现要求：
  - 新增 `mobile_real_device_field_trial_acceptance_execution_pack*` fixture / summary / safe copy。
  - mobile/web 新增只读 execution pack panel，展示 owner checklist、evidence capture steps、redaction requirements、rerun commands、`next_required_evidence` 和 safe copy。
  - 保持 Start Delivery、Confirm Dropoff、Cancel gating 不变。
  - 不暴露 raw JSON、ROS topic、串口、云密钥或控制入口。
- 验收命令：
  - `node --check mobile/web/app.js`
  - `python3 -m unittest mobile.web.test_mobile_web_entrypoint`
  - `rg -n "mobile_real_device_field_trial_acceptance_execution_pack|source=software_proof|not_proven|delivery_success=false|primary_actions_enabled=false|safe_to_control=false" mobile/web/app.js mobile/fixtures/mobile_web_status.fixture.json docs/product/mobile_user_flow.md`
  - `git diff --check -- mobile/web/app.js mobile/fixtures/mobile_web_status.fixture.json mobile/web/test_mobile_web_entrypoint.py docs/product/mobile_user_flow.md`

### Owner B：Robot Platform Engineer

- 角色：`robot-software-engineer`
- 主责：Robot diagnostics safe alias + docs/interfaces。
- 文件范围：
  - `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
  - `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
  - `docs/interfaces/ros_contracts.md`
- 实现要求：
  - 新增 diagnostics safe alias，例如 `robot_diagnostics_mobile_real_device_field_trial_acceptance_execution_pack_summary`。
  - alias 只读暴露 execution pack 摘要和安全边界。
  - 保持 `delivery_success=false`、`primary_actions_enabled=false`、`safe_to_control=false`，不启用控制入口。
  - 接口文档说明字段来源、证据边界和不证明事项。
- 验收命令：
  - `PYTHONPATH=onboard/src/ros2_trashbot_behavior python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
  - `rg -n "mobile_real_device_field_trial_acceptance_execution_pack|robot_diagnostics_mobile_real_device_field_trial_acceptance_execution_pack_summary|source=software_proof|not_proven|delivery_success=false|primary_actions_enabled=false|safe_to_control=false" onboard/src/ros2_trashbot_behavior docs/interfaces/ros_contracts.md`
  - `git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py docs/interfaces/ros_contracts.md`

### Owner C：Product Manager / OKR Owner

- 角色：`product-okr-owner`
- 主责：sprint closeout + OKR/progress log。
- 文件范围：
  - `sprints/2026.05.18_23-24_mobile-real-device-acceptance-execution-pack/tech-done.md`
  - `sprints/2026.05.18_23-24_mobile-real-device-acceptance-execution-pack/side2side_check.md`
  - `sprints/2026.05.18_23-24_mobile-real-device-acceptance-execution-pack/final.md`
  - `OKR.md`
  - `docs/process/okr_progress_log.md`
- 实现要求：
  - 汇总 Full-stack / Robot 验证证据。
  - 保守更新 Objective 4 证据边界；没有真实手机材料时不得写成真实验收通过。
  - 明确 Objective 5、Objective 1、PR #4、PR #5 剩余缺口。
  - final 必须回顾本节“OKR 最低优先级核对”的理由是否仍成立。
- 验收命令：
  - `test -f sprints/2026.05.18_23-24_mobile-real-device-acceptance-execution-pack/tech-done.md && test -f sprints/2026.05.18_23-24_mobile-real-device-acceptance-execution-pack/side2side_check.md && test -f sprints/2026.05.18_23-24_mobile-real-device-acceptance-execution-pack/final.md`
  - `rg -n "mobile_real_device_field_trial_acceptance_execution_pack|Objective 5|Objective 1|Objective 4|PR #4|PR #5|software_proof|not_proven|delivery_success=false|primary_actions_enabled=false" sprints/2026.05.18_23-24_mobile-real-device-acceptance-execution-pack OKR.md docs/process/okr_progress_log.md`
  - `git diff --check -- sprints/2026.05.18_23-24_mobile-real-device-acceptance-execution-pack OKR.md docs/process/okr_progress_log.md`

### Owner D：Hardware Infra Engineer，只读事实补充

- 角色：`hardware-engineer`
- 主责：只读核对 PR #5 2D LiDAR / ToF 与 vendor/source/materials 缺口。
- 文件范围：只读 `docs/vendor/VENDOR_INDEX.md`、`docs/product/production_hardware_boundary.md`、`OKR.md`。
- 输出要求：
  - 明确当前 repo 是否已有真实 2D LiDAR / ToF SKU/source/receipt/procurement/installation/wiring/power/calibration/HIL-entry 材料。
  - 不修改硬件配置、launch、driver 或 vendor 文件。
- 验收命令：
  - `rg -n "2D LiDAR|ToF|monocular|VENDOR_INDEX|source|receipt|HIL-entry" docs/vendor docs/product/production_hardware_boundary.md OKR.md`

## 5. 并行启动和协作边界

- 默认并行启动 Full-stack、Robot、Product 三个 owner；Hardware 作为只读事实补充可并行启动。
- 每个 owner 只负责自己的文件范围，不独占整个仓库。
- 不得回滚、覆盖或格式化范围外文件。
- 如 owner 发现范围冲突，先报告 Product closeout，不自行扩大范围。
- 主节点只做派发、等待、验收、证据核对和 sprint 留档，不直接写产品代码、测试代码或硬件配置。

## 6. 集成验收围栏

实现阶段完成后，集成验收只跑以下围栏，不新增大测试堆：

```bash
node --check mobile/web/app.js
python3 -m unittest mobile.web.test_mobile_web_entrypoint
PYTHONPATH=onboard/src/ros2_trashbot_behavior python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
rg -n "mobile_real_device_field_trial_acceptance_execution_pack|source=software_proof|not_proven|safe_to_control=false|delivery_success=false|primary_actions_enabled=false" mobile/web mobile/fixtures onboard/src/ros2_trashbot_behavior docs/product docs/interfaces
git diff --check -- mobile/web/app.js mobile/fixtures/mobile_web_status.fixture.json mobile/web/test_mobile_web_entrypoint.py docs/product/mobile_user_flow.md onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py docs/interfaces/ros_contracts.md
```

Product closeout 额外跑：

```bash
test -f sprints/2026.05.18_23-24_mobile-real-device-acceptance-execution-pack/tech-done.md && test -f sprints/2026.05.18_23-24_mobile-real-device-acceptance-execution-pack/side2side_check.md && test -f sprints/2026.05.18_23-24_mobile-real-device-acceptance-execution-pack/final.md
rg -n "Objective 5|Objective 1|Objective 4|PR #4|PR #5|software_proof|not_proven|delivery_success=false|primary_actions_enabled=false" sprints/2026.05.18_23-24_mobile-real-device-acceptance-execution-pack OKR.md docs/process/okr_progress_log.md
git diff --check -- sprints/2026.05.18_23-24_mobile-real-device-acceptance-execution-pack OKR.md docs/process/okr_progress_log.md
```

## 7. 本规划文档验收命令

```bash
test -f sprints/2026.05.18_23-24_mobile-real-device-acceptance-execution-pack/pre_start.md && test -f sprints/2026.05.18_23-24_mobile-real-device-acceptance-execution-pack/prd.md && test -f sprints/2026.05.18_23-24_mobile-real-device-acceptance-execution-pack/tech-plan.md
rg -n "sprint_type: epic|OKR 最低优先级核对|PR #4|PR #5|Objective 5|Objective 1|Objective 4|software_proof|not_proven|delivery_success=false|primary_actions_enabled=false|mobile_real_device_field_trial_acceptance_execution_pack" sprints/2026.05.18_23-24_mobile-real-device-acceptance-execution-pack
git diff --check -- sprints/2026.05.18_23-24_mobile-real-device-acceptance-execution-pack
```

## 8. 剩余风险和不证明事项

- 本轮 planning 和后续 local software proof 都不证明真实手机、真实 iPhone/Android behavior、production app、真实 PWA prompt/user choice。
- 不证明真实 route/elevator field pass、真实 Nav2/fixed-route、真实 route completion signal、真实 task record、dropoff/cancel completion 或 delivery success。
- 不证明 WAVE ROVER、UART、HIL、`feedback_T1001.log`、真实 `/odom`、`/imu/data`、`/battery`。
- 不证明 PR #5 2D LiDAR / ToF SKU/source/receipt/procurement/installation/wiring/power/calibration/HIL-entry。
- 不证明 Objective 5 的公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue 或 worker/cutover。

