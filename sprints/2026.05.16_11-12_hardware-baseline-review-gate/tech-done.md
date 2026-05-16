# Sprint 2026.05.16_11-12 Hardware Baseline Review Gate - Tech Done

sprint_type: epic

## 1. 实际改动

本轮由四个 Engineer worker 完成 `hardware_baseline_review` 闭环，Product closeout 只做验收、留档和 OKR 同步。

### Task A - Hardware

- 更新 `docs/product/production_hardware_boundary.md`。
- 修复 PR #5 review 指出的 `Default Hardware Set` 与 `Navigation/Sensing Baseline` 矛盾。
- 将 2D LiDAR / ToF 写为 Product Target / Procurement Validation Pending，而不是已采购、已安装、已接线、已标定或 HIL 通过。
- 保留 `hardware_material_pending`、`not_proven`、非 Objective 5 external proof 口径。

### Task C - Autonomy

- 新增 `pc-tools/evidence/hardware_baseline_review_gate.py` 与对应测试。
- 更新 `pc-tools/README.md` 和 `docs/navigation/fixed_route_workflow.md`。
- gate 输出 `software_proof_docker_hardware_baseline_review_gate`、`hardware_material_pending`、`delivery_success=false`、`primary_actions_enabled=false`。
- 传感器职责分层为：2D LiDAR 目标用于 SLAM/Nav2 主链，monocular 用于电梯门/楼层语义证据，ToF 用于近场 safety gate 且不是主建图输入。

### Task B - Robot

- 更新 `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`、对应测试和 `docs/interfaces/ros_contracts.md`。
- 新增 `hardware_baseline_review` / `hardware_baseline_review_summary` diagnostics metadata-only consumer。
- consumer 保持 fail-closed：不触发 collect/dropoff/cancel、ACK、cursor、Nav2、HIL、dropoff/cancel completion 或 delivery success。

### Task D - Full-stack

- 更新 `mobile/web/index.html`、`mobile/web/app.js`、`mobile/web/styles.css`、fixture、mobile test 和 `docs/product/mobile_user_flow.md`。
- 新增只读“硬件基线评审状态”panel，展示 product baseline、vendor coverage、`hardware_material_pending`、2D LiDAR / ToF responsibility、safe `evidence_ref`、`delivery_success=false`、`primary_actions_enabled=false` 和 `not_proven`。
- copy/export 保持 whitelist-only；Start / Confirm Dropoff / Cancel gating 未改变。

## 2. 验证结果

Worker 已返回的分任务验证：

- Task A Hardware：关键边界 `rg` 命中；`git diff --check -- docs/product/production_hardware_boundary.md` 通过。
- Task C Autonomy：`py_compile` 通过；`pc-tools/evidence/test_hardware_baseline_review_gate.py` `Ran 4 tests ... OK`；CLI `--help` 通过；required `rg` 与 scoped `git diff --check` 通过。
- Task B Robot：diagnostics unittest `Ran 93 tests ... OK`；`py_compile`、required `rg`、scoped `git diff --check` 通过。
- Task D Full-stack：`mobile/test_mobile_web_entrypoint.py` `Ran 52 tests ... OK`；`py_compile`、`node --check mobile/web/app.js`、required `rg`、scoped `git diff --check` 通过。

最终集成审查发现 PC gate compact summary schema 与 Robot diagnostics 白名单不一致：PC `--summary-output` 初始使用过已废弃的 gate-specific summary schema，Robot 只接收 `trashbot.hardware_baseline_review_summary.v1`。已修复为统一 summary schema，并新增 Robot 回归测试证明 PC summary handoff 不再返回 `unsupported_schema`：

- 修复后 `pc-tools/evidence/test_hardware_baseline_review_gate.py` 仍为 `Ran 4 tests ... OK`。
- 修复后 Robot diagnostics unittest 为 `Ran 94 tests ... OK`。
- 修复后 mobile unittest 仍为 `Ran 52 tests ... OK`。
- 修复后 `node --check mobile/web/app.js` 通过。
- 修复后 PC summary handoff proof 显示 input/diagnostics schema 均为 `trashbot.hardware_baseline_review_summary.v1`，`review_status.status=hardware_baseline_review_not_proven`，不是 `unsupported_schema`，且 `delivery_success=false`、`primary_actions_enabled=false`。

Product closeout 验收命令：

```bash
rg -n "hardware_baseline_review|software_proof_docker_hardware_baseline_review_gate|hardware_material_pending|not_proven|delivery_success=false|primary_actions_enabled=false|Objective 5|只有 Docker|PR #5|2D LiDAR|ToF" sprints/2026.05.16_11-12_hardware-baseline-review-gate OKR.md docs/process/okr_progress_log.md
git diff --check -- sprints/2026.05.16_11-12_hardware-baseline-review-gate OKR.md docs/process/okr_progress_log.md
```

## 3. 偏差与证据边界

- 最终审查发现并修复了 PC summary schema handoff 偏差；这是 contract 对齐修复，不改变 evidence boundary，也不把硬件基线提升为真实硬件证明。
- 本轮完成的是硬件基线 review gate 的 software proof 和 phone-safe/diagnostics 只读消费，不是真实硬件 review 通过。
- 2D LiDAR / ToF 仍是 Product Target / Procurement Validation Pending；`hardware_material_pending` 和 `not_proven` 必须保留。
- Objective 1 继续约 73%，因为没有真实 WAVE ROVER、UART、`T=1001` feedback、真实串口日志或 HIL。
- Objective 2 / Objective 3 不上调；本轮只间接支撑路线、电梯和 Nav2/SLAM 传感器职责边界，没有真实 route/elevator field pass、Nav2/fixed-route runtime log、task record、dropoff/cancel completion 或 delivery success。
- Objective 4 可从约 80% 保守上调到约 81%，因为 PR #5 的量产硬件边界矛盾、PC gate、Robot diagnostics metadata-only consumer 和手机只读 panel 形成闭环。
- Objective 5 保持约 66%；本机只有 Docker，且本轮没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/migration 或其他 Objective 5 external proof。

## 4. 剩余风险

- 仍需补真实 2D LiDAR SKU、vendor/source document、采购状态、机械安装、接线、标定和 HIL entry evidence。
- 仍需补真实 ToF 安全环数量、安装位、阈值、故障策略、接线、标定和 HIL entry evidence。
- 仍需真实手机设备、真实 iPhone/Android device behavior、production app 或真实 PWA prompt/user choice 验收。
- 仍需真实 WAVE ROVER/UART/HIL、真实 Nav2/fixed-route、真实 route/elevator field pass、真实 dropoff/cancel completion 和 delivery success。
- O5 外部证据仍阻塞：真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker/migration 均未补齐。
