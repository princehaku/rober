# Sprint 2026.05.19_03-04 PR5 Review Thread Closeout - Tech Plan

## OKR 最低优先级核对

1. Live `OKR.md` 4.1 当前完成度最低的是 Objective 5，约 68%。
2. 本 sprint 不针对 Objective 5。理由：本机是 Docker-only，仍缺真实 HTTPS/TLS、公网 4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker/migration/cutover 和 real external proof；继续本地 O5 metadata wrapper 不能推进 O5 completion。
3. 次低 Objective 1 约 81%，本 sprint 针对 Objective 1 的 PR #5 review closeout 可行动缺口。理由：PR #5 仍有 unresolved review thread，且当前 mainline 已有 `production_hardware_boundary` 和 vendor/source boundary 文档，可在 Docker-only 环境产出 thread closeout decision；但真实 WAVE ROVER/UART/HIL 和 2D LiDAR / ToF materials 仍保持 `not_proven`。
4. PR #4 没有 review comments，但 Objective 2 / Objective 3 / Objective 4 仍缺真实 route/elevator/phone field evidence；本 sprint 不把 PR #5 closeout gate 写成 PR #4 field pass。

## 技术目标

实现 `pr5_review_thread_closeout` software-proof gate，并让 Robot diagnostics / mobile/web 只读展示其 sanitized summary：

- Hardware gate 读取安全 PR #5 thread summary、`docs/product/production_hardware_boundary.md`、`docs/vendor/VENDOR_INDEX.md`、`OKR.md`，输出 artifact/summary。
- 每条 review thread 输出 closeout decision：`ready_to_close_on_mainline_docs`、`blocked_pending_real_materials` 或 `still_open_missing_current_evidence`。
- Robot diagnostics 暴露 `robot_diagnostics_pr5_review_thread_closeout_summary` safe alias。
- Mobile/web 增加只读 PR #5 review closeout panel 和 fixture。
- 所有层保留 `software_proof`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。

## 接口契约草案

建议 summary 结构如下；worker 可按现有代码风格微调字段名，但语义不得放宽：

```json
{
  "schema": "trashbot.pr5_review_thread_closeout_summary.v1",
  "source": "software_proof",
  "overall_status": "not_proven",
  "pr": {
    "number": 5,
    "title": "Make elevator-assisted delivery mandatory; update agents, OKR and hardware baseline"
  },
  "thread_decisions": [
    {
      "thread_key": "p1_production_hardware_boundary_default_vs_mandatory_sensor_baseline",
      "severity": "P1",
      "decision": "ready_to_close_on_mainline_docs",
      "current_evidence_refs": [
        "docs/product/production_hardware_boundary.md#Default Hardware Set",
        "docs/product/production_hardware_boundary.md#Vendor/Source Attribution Boundary",
        "docs/vendor/VENDOR_INDEX.md#Complete Material Coverage"
      ],
      "missing_real_materials": [
        "real_2d_lidar_sku_source_receipt",
        "real_tof_sku_source_receipt",
        "real_install_wiring_power_calibration",
        "real_hil_entry"
      ],
      "owner_handoff": "Hardware Engineer closes only if reviewer accepts mainline docs; real materials stay open."
    }
  ],
  "not_proven": [
    "real_2d_lidar",
    "real_tof",
    "hil_pass",
    "route_elevator_field_pass",
    "delivery_success",
    "objective_5_external_proof"
  ],
  "delivery_success": false,
  "primary_actions_enabled": false
}
```

Decision rules:

- `ready_to_close_on_mainline_docs`：当前 mainline 文档已经解决 review thread 指出的文档矛盾、narrative mismatch 或 citation boundary，且 thread 不要求真实材料已到。
- `blocked_pending_real_materials`：当前 mainline 已清楚说明边界，但 thread 本质要求真实 SKU/source/receipt/procurement/install/wiring/power/calibration/HIL-entry 材料。
- `still_open_missing_current_evidence`：当前 mainline 仍缺 thread 要求的 repo-local evidence 或文档仍自相矛盾。

Fail-closed rules:

- 缺少 `docs/product/production_hardware_boundary.md`、`docs/vendor/VENDOR_INDEX.md`、`OKR.md`、thread summary 或 schema mismatch，必须输出 blocked / still open，不得默认 ready。
- `delivery_success` 和 `primary_actions_enabled` 必须是布尔 false。
- 出现 HIL success、field pass、real procurement success、O5 external proof、control enabled、raw credential、complete local path 或 traceback 必须 fail closed。

## 文件范围和 owner 分工

| Owner | 允许改动范围 | 任务 |
| --- | --- | --- |
| hardware-engineer | `pc-tools/evidence/pr5_review_thread_closeout_gate.py`、`tests/test_pr5_review_thread_closeout_gate.py` 或现有 evidence test 位置、`docs/product/production_hardware_boundary.md` 的必要 gate 段落、`docs/interfaces/**` 的必要 contract 文档、本 sprint `tech-done.md` 中自己的小节 | 实现 gate、fixture / safe thread summary、focused test、summary artifact 和 docs contract |
| robot-software-engineer | `onboard/src/ros2_trashbot_behavior/**`、相关 Robot tests、`docs/interfaces/**` 的 diagnostics contract、本 sprint `tech-done.md` 中自己的小节 | 增加 `robot_diagnostics_pr5_review_thread_closeout_summary` safe alias，只读消费 summary |
| full-stack-software-engineer | `mobile/web/**`、`mobile/fixtures/**`、`docs/product/mobile_user_flow.md`、本 sprint `tech-done.md` 中自己的小节 | 增加只读 PR #5 review closeout panel、fixture 和 targeted validation |
| product-okr-owner | `OKR.md`、`docs/process/okr_progress_log.md`、本 sprint `side2side_check.md` / `final.md`（实现完成后） | 验收边界和 OKR closeout；本 planning 阶段只写三份 planning docs |
| autonomy-engineer | 无本轮写范围 | PR #4 route/elevator field pass 保持后续独立缺口 |

进入实现阶段时，Hardware、Robot、Full-Stack 文件范围互不重叠，必须在同一轮并行启动三个 worker。Product 只在实现完成后做验收和 OKR closeout。

## 子 agent 执行提示

实现阶段主节点必须按 AGENTS 固定结构派发 worker，prompt 需包含对应 `.codex/agents/<role>.toml` 的完整 System Prompt，并明确“你不是独自在代码库中工作，不要回滚其他 worker 或用户改动”。

Hardware worker 必须先读 `docs/vendor/VENDOR_INDEX.md` 和 `docs/product/production_hardware_boundary.md`。涉及 vendor/source 或硬件材料时，只能引用本地 vendor boundary，不得凭记忆补 SKU、引脚、电压、UART、波特率、机械尺寸或 HIL 事实。

## 验收命令

### Hardware worker

```bash
test -f docs/vendor/VENDOR_INDEX.md
python3 -m py_compile pc-tools/evidence/pr5_review_thread_closeout_gate.py
python3 -m unittest tests/test_pr5_review_thread_closeout_gate.py
rg -n "pr5_review_thread_closeout|PR #5|production_hardware_boundary|docs/vendor/VENDOR_INDEX.md|ready_to_close_on_mainline_docs|blocked_pending_real_materials|still_open_missing_current_evidence|software_proof|not_proven|delivery_success=false|primary_actions_enabled=false" pc-tools/evidence tests docs/product docs/interfaces sprints/2026.05.19_03-04_pr5-review-thread-closeout
git diff --check -- pc-tools/evidence tests docs/product docs/interfaces sprints/2026.05.19_03-04_pr5-review-thread-closeout
```

### Robot worker

```bash
python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py
python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
rg -n "robot_diagnostics_pr5_review_thread_closeout_summary|pr5_review_thread_closeout|PR #5|review thread|software_proof|not_proven|delivery_success=false|primary_actions_enabled=false" onboard/src/ros2_trashbot_behavior docs/interfaces sprints/2026.05.19_03-04_pr5-review-thread-closeout
git diff --check -- onboard/src/ros2_trashbot_behavior docs/interfaces sprints/2026.05.19_03-04_pr5-review-thread-closeout
```

### Full-Stack worker

```bash
python3 mobile/web/test_mobile_web_entrypoint.py
python3 -m py_compile mobile/web/test_mobile_web_entrypoint.py
node --check mobile/web/app.js
rg -n "pr5_review_thread_closeout|PR #5|review thread|ready_to_close_on_mainline_docs|blocked_pending_real_materials|still_open_missing_current_evidence|software_proof|not_proven|delivery_success=false|primary_actions_enabled=false|Start Delivery|Confirm Dropoff|Cancel" mobile/web mobile/fixtures docs/product/mobile_user_flow.md sprints/2026.05.19_03-04_pr5-review-thread-closeout
git diff --check -- mobile/web mobile/fixtures docs/product/mobile_user_flow.md sprints/2026.05.19_03-04_pr5-review-thread-closeout
```

### Product planning gate

```bash
test -f sprints/2026.05.19_03-04_pr5-review-thread-closeout/pre_start.md && test -f sprints/2026.05.19_03-04_pr5-review-thread-closeout/prd.md && test -f sprints/2026.05.19_03-04_pr5-review-thread-closeout/tech-plan.md
rg -n "sprint_type: epic|Objective 5|Objective 1|PR #5|PR #4|review thread|production_hardware_boundary|docs/vendor/VENDOR_INDEX.md|software_proof|not_proven|delivery_success=false|primary_actions_enabled=false|OKR 最低优先级核对" sprints/2026.05.19_03-04_pr5-review-thread-closeout
git diff --check -- sprints/2026.05.19_03-04_pr5-review-thread-closeout
```

## 风险和 fail-closed 规则

- 不得把 `ready_to_close_on_mainline_docs` 写成真实硬件、真实采购、真实安装、HIL、field pass 或 delivery success。
- 不得在 Robot diagnostics 或 mobile/web 中启用 primary actions、ACK、cursor、command、Start Delivery、Confirm Dropoff 或 Cancel。
- 不得暴露 raw GitHub token、raw review body、credential、完整本机路径、raw ROS topic、serial/UART path、baudrate、traceback 或完整内部日志。
- 如果 `OKR.md` table 与 narrative 冲突，必须输出 `still_open_missing_current_evidence`，不得 Product 自行解释为 ready。
- 如果 `production_hardware_boundary.md` 未分离 default hardware set 与 target LiDAR/ToF pending baseline，P1 thread 必须保持 open。
- 如果 `docs/vendor/VENDOR_INDEX.md` 不能证明 2D LiDAR / ToF real material，必须列入 `missing_real_materials`。

## 实现后收口要求

- Worker 必须在 `tech-done.md` 写明实际改动、验证命令输出、失败定位和剩余风险。
- Product 验收时创建 `side2side_check.md` 和 `final.md`，并更新 `OKR.md` 与 `docs/process/okr_progress_log.md`。
- OKR closeout 只能记录 PR #5 review closeout decision gate 的 software-proof 进展；不得提高 Objective 1 的真实 HIL / hardware pass，也不得提高 Objective 5 external proof。
- 若实现只完成部分 owner 范围，final 必须明确未完成项和不能关闭的 review thread。
