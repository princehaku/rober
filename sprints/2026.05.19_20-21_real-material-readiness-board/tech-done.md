# Sprint 2026.05.19_20-21 Real Material Readiness Board - Tech Done

## 1. Sprint 类型

sprint_type: epic

## 2. 实际改动

Hardware / Autonomy worker 完成 PC gate 和真实材料分组：

- 新增/更新 `pc-tools/evidence/real_material_readiness_board.py`。
- 新增/更新 `tests/test_real_material_readiness_board.py`。
- 新增/更新 `docs/interfaces/real_material_readiness_board.md`。
- 生成 `sprints/2026.05.19_20-21_real-material-readiness-board/evidence/real_material_readiness_board.json`。
- 生成 `sprints/2026.05.19_20-21_real-material-readiness-board/evidence/real_material_readiness_board_summary.json`。
- 硬件事实入口已按要求读取 `docs/vendor/VENDOR_INDEX.md` 及其指向的 WAVE ROVER 本地资料；本轮只记录 vendor source coverage，不证明真实采购、安装、接线、标定、HIL-entry 或 field pass。
- board 纳入 Objective 5 external、Objective 1 / PR #5 hardware、PR #4 route/elevator、Objective 4 real phone 四类 material group。
- PR #5 thread `PRRT_kwDOSWB9286CJ3tX` 保持 unresolved / `blocked_pending_real_materials`。

Robot worker 完成 Robot diagnostics 只读 summary：

- 新增/更新 `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`。
- 新增/更新 `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`。
- 新增/更新 `docs/interfaces/operator_gateway_diagnostics.md` 与 `docs/interfaces/ros_contracts.md`。
- 增加 `robot_diagnostics_real_material_readiness_board_summary` safe alias。
- Robot diagnostics 只读消费 summary，不改变 Start Delivery、Confirm Dropoff、Cancel、底盘控制或 action result gating。

Full-Stack worker 完成 mobile/web 只读看板：

- 新增/更新 `mobile/web/app.js`、`mobile/web/styles.css`、`mobile/web/test_mobile_web_entrypoint.py`。
- 新增/更新 `mobile/fixtures/mobile_web_status.fixture.json`、`mobile/web/fixtures/status.json`。
- 新增/更新 `docs/product/mobile_user_flow.md`。
- 增加只读“真实材料就绪看板”，展示四类材料缺口、owner、blocking reason、next_required_evidence 和证据边界。
- 手机端文案保持中文优先，不暴露 raw ROS topic、raw JSON、local path、credentials、checksum 或控制 payload。

Autonomy read-only consult 确认 PR #4 route/elevator 仍缺真实材料：

- 真实 elevator door state。
- 真实 target floor confirmation。
- 真实 human assistance record。
- 真实 Nav2/fixed-route runtime log。
- 真实 field task record。
- 真实 route completion signal。
- 真实 dropoff/cancel material。
- 真实 delivery_result。

Product closeout 本轮补齐：

- `sprints/2026.05.19_20-21_real-material-readiness-board/tech-done.md`
- `sprints/2026.05.19_20-21_real-material-readiness-board/side2side_check.md`
- `sprints/2026.05.19_20-21_real-material-readiness-board/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`

## 3. 验证结果

Hardware / Autonomy PC gate worker 已验证：

```text
test -f docs/vendor/VENDOR_INDEX.md
passed

python3 -m py_compile pc-tools/evidence/real_material_readiness_board.py
passed

python3 -m unittest tests/test_real_material_readiness_board.py
Ran 5 tests OK

python3 pc-tools/evidence/real_material_readiness_board.py --output sprints/2026.05.19_20-21_real-material-readiness-board/evidence/real_material_readiness_board.json --summary-output sprints/2026.05.19_20-21_real-material-readiness-board/evidence/real_material_readiness_board_summary.json
artifact generation passed

required rg
passed

scoped git diff --check
passed
```

Robot worker 已验证：

```text
PYTHONPATH=onboard/src/ros2_trashbot_behavior python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py
passed

PYTHONPATH=onboard/src/ros2_trashbot_behavior python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
Ran 213 tests OK

required rg
passed

scoped git diff --check
passed
```

Full-Stack worker 已验证：

```text
python3 mobile/web/test_mobile_web_entrypoint.py
Ran 137 tests ... OK

python3 -m py_compile mobile/web/test_mobile_web_entrypoint.py
passed

node --check mobile/web/app.js
passed

required rg
passed

scoped git diff --check
passed
```

Product closeout 验收已通过：

```text
test -f .../tech-done.md && test -f .../side2side_check.md && test -f .../final.md
passed

rg -n "real_material_readiness_board|Objective 5|Objective 1|Objective 4|PR #4|PR #5|PRRT_kwDOSWB9286CJ3tX|software_proof|not_proven|delivery_success=false|primary_actions_enabled=false|safe_to_control=false|Ran 5 tests|Ran 213 tests|Ran 137 tests" sprints/... OKR.md docs/process/okr_progress_log.md
matched required closeout terms across sprint docs, OKR.md, and docs/process/okr_progress_log.md

git diff --check -- sprints/... OKR.md docs/process/okr_progress_log.md
passed
```

## 4. 证据边界

本轮证据边界是 `software_proof_docker_real_material_readiness_board_gate`。

必须保持：

- `source=software_proof`
- `software_proof`
- `not_proven`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `safe_to_control=false`

本轮 `real_material_readiness_board` 只是 routing readiness / software proof，只能说明 repo-local summary 能把真实材料缺口统一路由到 owner 和 next_required_evidence。它不证明真实外部云、真实硬件材料、真实电梯、真实 Nav2/fixed-route、真实手机、真实 dropoff/cancel completion、delivery success、HIL 或 safe-to-control grant。

## 5. 偏差和失败定位

未收到工程 worker 报告的未修复失败。

已知边界不是失败：本轮没有新增真实 external proof、真实 WAVE ROVER/UART/HIL、真实 2D LiDAR / ToF materials、真实 PR #4 route/elevator field packet 或真实手机/browser acceptance，因此 OKR 百分比保守不提高。

## 6. 剩余风险

- Objective 5 仍缺真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker/migration/cutover 或其他 real external proof。
- Objective 1 仍缺真实 WAVE ROVER/UART/HIL、真实 `feedback_T1001.log`、真实 `/odom`、`/imu/data`、`/battery`、operator HIL report；PR #5 `PRRT_kwDOSWB9286CJ3tX` 仍 unresolved / `blocked_pending_real_materials`，缺真实 2D LiDAR / ToF SKU/source/receipt/procurement/installation/wiring/power/calibration/HIL-entry。
- Objective 2 / Objective 3 仍缺 PR #4 route/elevator field materials、真实 elevator door state、target floor confirmation、human assistance record、Nav2/fixed-route runtime log、field task record、route completion signal、dropoff/cancel material 和 delivery_result。
- Objective 4 仍缺真实 iPhone/Android device behavior、production app、真实 PWA prompt/userChoice、true phone/browser acceptance 和现场手机验收材料。
