# Sprint 2026.05.19_20-21 Real Material Readiness Board - Tech Plan

## 1. 技术目标

实现 `real_material_readiness_board` 的跨端 software-proof 主链路：

- PC/evidence gate 生成统一 readiness artifact。
- Robot diagnostics 暴露只读 summary。
- mobile/web 展示只读 “真实材料就绪看板”。
- docs 同步说明该 board 只是 routing surface，不是 proof surface。

所有实现必须保留：

- `software_proof`
- `not_proven`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `safe_to_control=false`

## 2. OKR 最低优先级核对

1. 当前 `OKR.md` 4.1 中数字最低的是 Objective 5，约 68%。
2. 本 sprint 不直接推进 O5 completion，而是把 O5 external readiness 纳入统一 board。
3. 不直接针对 O5 的理由：当前 Docker-only 主机没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker/migration/cutover 或真实 external proof。继续新增 O5 local metadata depth 会重复消费已 blocked 的 O5 blocker。
4. 下一低项 Objective 1 约 81%，也无法直接提高：PR #5 `PRRT_kwDOSWB9286CJ3tX` 仍 unresolved / blocked_pending_real_materials，且缺真实 WAVE ROVER/UART/HIL 与真实 2D LiDAR / ToF SKU/source/receipt/procurement/installation/wiring/power/calibration/HIL-entry。
5. PR #4 route/elevator 和 O4 mobile 近期都已多轮消费真实材料缺口；本轮选择统一 board，是为了把下一步真实材料采集路由清楚，而不是创建第四个 mobile wrapper 或第三个 route/elevator wrapper。

## 3. 架构设计

`real_material_readiness_board` 采用单向只读链路：

1. PC/evidence gate 汇总 repo-local known blockers、sample material states 和 PR/review evidence。
2. Robot diagnostics 将 artifact 转换为 safe summary alias。
3. mobile/web 读取 fixture/status 中的 summary，并渲染只读 board。
4. Product closeout 只记录 software-proof routing readiness，不改变 OKR completion。

数据模型建议：

```json
{
  "schema": "trashbot.real_material_readiness_board.v1",
  "status": "not_proven",
  "source": "software_proof",
  "delivery_success": false,
  "primary_actions_enabled": false,
  "safe_to_control": false,
  "material_groups": [
    {
      "group_id": "o5_external",
      "owner": "product-okr-owner",
      "blocking_reason": "missing_real_external_proof",
      "next_required_evidence": ["public_https_tls", "4g_sim", "oss_cdn_live_traffic", "production_db_queue"],
      "source_refs": ["Objective 5", "OKR.md 4.1"]
    }
  ]
}
```

## 4. 文件范围和 owner

### Hardware Infra Engineer

允许改动：

- `pc-tools/evidence/real_material_readiness_board.py`
- `tests/test_real_material_readiness_board.py`
- `docs/interfaces/real_material_readiness_board.md`

职责：

- 建立 PC-side artifact builder。
- 将 Objective 1 / PR #5 hardware group 写入 board。
- 硬件相关事实必须以 `docs/vendor/VENDOR_INDEX.md` 为入口，不写未经本地资料支撑的 SKU/电气细节。
- 保留 `PR #5`、`PRRT_kwDOSWB9286CJ3tX`、`not_proven`。

验收命令：

```bash
test -f docs/vendor/VENDOR_INDEX.md
python3 -m py_compile pc-tools/evidence/real_material_readiness_board.py
python3 -m unittest tests/test_real_material_readiness_board.py
python3 pc-tools/evidence/real_material_readiness_board.py --output sprints/2026.05.19_20-21_real-material-readiness-board/evidence/real_material_readiness_board.json --summary-output sprints/2026.05.19_20-21_real-material-readiness-board/evidence/real_material_readiness_board_summary.json
rg -n "real_material_readiness_board|Objective 5|Objective 1|Objective 4|PR #4|PR #5|PRRT_kwDOSWB9286CJ3tX|software_proof|not_proven|delivery_success=false|primary_actions_enabled=false|safe_to_control=false" pc-tools/evidence tests docs/interfaces sprints/2026.05.19_20-21_real-material-readiness-board/evidence
git diff --check -- pc-tools/evidence tests docs/interfaces sprints/2026.05.19_20-21_real-material-readiness-board
```

### Autonomy Algorithm Engineer

允许改动：

- `pc-tools/evidence/real_material_readiness_board.py`
- `tests/test_real_material_readiness_board.py`
- `docs/interfaces/real_material_readiness_board.md`

职责：

- 在同一 artifact 中补 PR #4 route/elevator material group。
- 明确缺真实 Nav2/fixed-route runtime log、route completion signal、task record、elevator door/floor/human-assist、dropoff/cancel completion、delivery result。
- 不引入控制行为，不声明 field pass。

验收命令：同 Hardware Infra Engineer，重点确认 `PR #4` 和 route/elevator missing materials 出现在 artifact 与 summary。

### Robot Platform Engineer

允许改动：

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
- `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
- `docs/interfaces/operator_gateway_diagnostics.md`
- `docs/interfaces/ros_contracts.md`

职责：

- 增加 `robot_diagnostics_real_material_readiness_board_summary` safe alias。
- Robot diagnostics 只读消费 summary，不改变 action gating。
- 保证 `delivery_success=false`、`primary_actions_enabled=false`、`safe_to_control=false` 原样透传。

验收命令：

```bash
PYTHONPATH=onboard/src/ros2_trashbot_behavior python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py
PYTHONPATH=onboard/src/ros2_trashbot_behavior python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
rg -n "robot_diagnostics_real_material_readiness_board_summary|real_material_readiness_board|software_proof|not_proven|delivery_success=false|primary_actions_enabled=false|safe_to_control=false" onboard/src/ros2_trashbot_behavior docs/interfaces
git diff --check -- onboard/src/ros2_trashbot_behavior docs/interfaces
```

### User Touchpoint Full-Stack Engineer

允许改动：

- `mobile/web/app.js`
- `mobile/web/styles.css`
- `mobile/web/test_mobile_web_entrypoint.py`
- `mobile/fixtures/mobile_web_status.fixture.json`
- `mobile/web/fixtures/status.json`
- `docs/product/mobile_user_flow.md`

职责：

- 增加只读 “真实材料就绪看板”。
- 展示 O5 external、O1 / PR #5 hardware、PR #4 route/elevator、O4 real phone 四类 group。
- 文案中文优先，面向现场 owner，不暴露 raw ROS topic 或 raw JSON。
- Start Delivery、Confirm Dropoff、Cancel gating 不变。

验收命令：

```bash
python3 mobile/web/test_mobile_web_entrypoint.py
python3 -m py_compile mobile/web/test_mobile_web_entrypoint.py
node --check mobile/web/app.js
rg -n "real_material_readiness_board|真实材料就绪看板|Objective 5|Objective 1|Objective 4|PR #4|PR #5|PRRT_kwDOSWB9286CJ3tX|software_proof|not_proven|delivery_success=false|primary_actions_enabled=false|safe_to_control=false" mobile docs/product/mobile_user_flow.md
git diff --check -- mobile docs/product/mobile_user_flow.md
```

### Product Manager / OKR Owner

允许改动：

- `sprints/2026.05.19_20-21_real-material-readiness-board/tech-done.md`
- `sprints/2026.05.19_20-21_real-material-readiness-board/side2side_check.md`
- `sprints/2026.05.19_20-21_real-material-readiness-board/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`

职责：

- 工程 worker 返回后做 closeout。
- 仅在证据支持时更新 OKR；预期本轮不提高 O5/O1/O2/O3/O4 百分比。
- 明确 board 是 routing readiness，不是真实 proof。

验收命令：

```bash
test -f sprints/2026.05.19_20-21_real-material-readiness-board/tech-done.md && test -f sprints/2026.05.19_20-21_real-material-readiness-board/side2side_check.md && test -f sprints/2026.05.19_20-21_real-material-readiness-board/final.md
rg -n "real_material_readiness_board|Objective 5|Objective 1|Objective 4|PR #4|PR #5|PRRT_kwDOSWB9286CJ3tX|software_proof|not_proven|delivery_success=false|primary_actions_enabled=false|safe_to_control=false" sprints/2026.05.19_20-21_real-material-readiness-board OKR.md docs/process/okr_progress_log.md
git diff --check -- sprints/2026.05.19_20-21_real-material-readiness-board OKR.md docs/process/okr_progress_log.md
```

## 5. 并行启动要求

本轮不是单 owner micro sprint。工程执行阶段必须并行启动 3-4 个 worker：

- Hardware Infra Engineer 与 Autonomy Algorithm Engineer 共同负责 PC/evidence gate，但必须在同一文件上协同，建议由 Hardware 主责、Autonomy 只读事实补充，避免 merge 冲突。
- Robot Platform Engineer 独立负责 diagnostics。
- User Touchpoint Full-Stack Engineer 独立负责 mobile/web。
- Product Manager / OKR Owner 在工程完成后 closeout。

如果运行时不能并行，`final.md` 必须解释降级原因。

## 6. 风险控制

- 所有 material group 默认 `not_proven`。
- 不允许任何 board 状态启用 `primary_actions_enabled`。
- 不允许 board 生成 `delivery_success=true`。
- 不允许 board 写入 `safe_to_control=true`。
- 不允许关闭 PR #5 `PRRT_kwDOSWB9286CJ3tX`。
- 不允许把 PR #4 route/elevator software-proof handoff 写成真实 field pass。
- 不允许把 Objective 4 mobile/web software-proof panel 写成真实手机验收。

## 7. 本 planning 阶段验收

本阶段只创建三份规划文档，并运行：

```bash
test -f sprints/2026.05.19_20-21_real-material-readiness-board/pre_start.md && test -f sprints/2026.05.19_20-21_real-material-readiness-board/prd.md && test -f sprints/2026.05.19_20-21_real-material-readiness-board/tech-plan.md
rg -n "real_material_readiness_board|Objective 5|Objective 1|Objective 4|PR #4|PR #5|PRRT_kwDOSWB9286CJ3tX|software_proof|not_proven|delivery_success=false|primary_actions_enabled=false|safe_to_control=false|OKR 最低优先级核对" sprints/2026.05.19_20-21_real-material-readiness-board
git diff --check -- sprints/2026.05.19_20-21_real-material-readiness-board
```
