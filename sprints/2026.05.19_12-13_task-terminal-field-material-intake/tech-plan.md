# Sprint 2026.05.19_12-13 Task Terminal Field Material Intake - Tech Plan

## 1. 目标

实现 `task_terminal_field_material_intake` Docker/local software-proof chain：

- Robot diagnostics 暴露 `robot_diagnostics_task_terminal_field_material_intake_summary`。
- mobile/web 展示只读“现场材料回填入口”panel，并保持 Start Delivery、Confirm Dropoff、Cancel gating 不扩大。
- Product closeout 更新 sprint、OKR 和 progress log，但不提高 O5/O1 真实进度。
- Autonomy 只读确认 route/elevator/Nav2 evidence fields 与 Objective 3 不冲突。

证据边界必须保持：`software_proof`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`、`safe_to_control=false`。

本轮不是 O5 external proof，不是 O1 HIL，不是 PR #4 route/elevator field pass，不证明真实手机、真实电梯、真实 Nav2/fixed-route、真实 dropoff/cancel completion、真实 delivery success 或 HIL。

## 2. OKR 最低优先级核对

1. 当前 `OKR.md` 4.1 完成度最低的 Objective 是 Objective 5，约 68%。
2. 本 sprint 不针对 Objective 5 completion。
3. 具体理由：Objective 5 下一步需要真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker/migration/cutover 或真实手机/browser external proof；当前本机只有 Docker，没有这些外部材料。继续做本地 O5 metadata wrapper 不能提高真实 O5 进度。
4. 下一低项是 Objective 1，约 81%。最新 `2026.05.19_10-11_hardware-real-material-escalation-request` 已完成 O1 硬件真实材料升级请求，并明确不能把 Docker/local `software_proof` 当真实 WAVE ROVER/UART/HIL、`feedback_T1001`、真实 `/odom` / `/imu` / `/battery` 或 PR #5 2D LiDAR / ToF 真实材料。再做第三个本地硬件 wrapper 触发重复 blocker 红线。
5. 本轮选择 Objective 2 / Objective 3 / Objective 4 的主链路可回填性：PR #4 和 PR #5 已把 elevator assisted delivery、route/elevator evidence 和硬件 baseline 纳入 MVP 主链；11-12 已完成 terminal action mainline 可观察性，但仍缺真实现场材料入口。本轮 `task_terminal_field_material_intake` 让后续真实 dropoff/cancel terminal materials、route/elevator field materials、real phone/browser evidence 有同一 safe `evidence_ref` 的 fail-closed 回填入口。
6. `final.md` 收口时需复核：是否仍未取得 O5 external proof 和 O1 real hardware/HIL materials；如真实材料已到位，下一轮必须优先切回对应最低 Objective。

## 3. 角色分工和文件范围

### robot-software-engineer

允许改动：

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
- `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
- `docs/interfaces/operator_gateway_diagnostics.md`
- 当前 sprint `tech-done.md` 中 Robot 段落

要求：

- 新增/暴露 `robot_diagnostics_task_terminal_field_material_intake_summary`。
- 只消费 sanitized terminal summary/material-intake payload；缺 payload、unsupported schema、unsafe copy、raw artifact、local path、checksum、credential、success wording、field-pass wording、HIL/pass wording、O5 external proof wording 均 fail closed。
- summary 至少包含 schema/status/source、safe `evidence_ref`、accepted safe refs、missing materials、next required evidence、phone-safe copy、evidence boundary。
- 固定保持 `software_proof`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`、`safe_to_control=false`。
- 不触发 ACK、commands、collect、dropoff、cancel、Nav2、route execution、HIL、terminal ACK、cursor advance 或 robot command。
- 代码新增技术注释必须使用中文，复杂逻辑说明为什么 fail closed。

验收命令：

```bash
python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py
python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
rg -n "task_terminal_field_material_intake|robot_diagnostics_task_terminal_field_material_intake_summary|software_proof|not_proven|delivery_success=false|primary_actions_enabled=false|safe_to_control=false|Objective 2|Objective 3|PR #4" onboard/src/ros2_trashbot_behavior docs/interfaces sprints/2026.05.19_12-13_task-terminal-field-material-intake
git diff --check -- onboard/src/ros2_trashbot_behavior docs/interfaces sprints/2026.05.19_12-13_task-terminal-field-material-intake
```

### full-stack-software-engineer

允许改动：

- `mobile/web/app.js`
- `mobile/web/styles.css`
- `mobile/web/test_mobile_web_entrypoint.py`
- `mobile/fixtures/mobile_web_status.fixture.json`
- `mobile/web/fixtures/status.json`
- `docs/product/mobile_user_flow.md`
- 当前 sprint `tech-done.md` 中 Full-Stack 段落

要求：

- mobile/web 新增只读“现场材料回填入口”panel。
- 优先消费 `robot_diagnostics_task_terminal_field_material_intake_summary`；缺失时 fail closed，不从 raw artifacts、ACK、cursor、old material status 或 completion summary 推导成功。
- 展示 intake status、safe `evidence_ref`、accepted safe refs、missing materials、next required evidence、phone-safe material intake copy、evidence boundary。
- 固定展示 `software_proof`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`、`safe_to_control=false`。
- 不扩大 Start Delivery、Confirm Dropoff、Cancel gating；不新增 ACK、cursor、diagnostics fetch、handoff route、review route、Nav2、HIL 或 robot command。
- 不展示 raw JSON、ROS topic、`/cmd_vel`、serial/UART path、baudrate、credential、local path、complete artifact、checksum、HIL/pass wording、delivery success wording、dropoff/cancel completion wording、route/elevator field-pass wording。
- 代码新增技术注释必须使用中文，解释用户安全边界和 fail-closed 原因。

验收命令：

```bash
python3 mobile/web/test_mobile_web_entrypoint.py
python3 -m py_compile mobile/web/test_mobile_web_entrypoint.py
node --check mobile/web/app.js
rg -n "task_terminal_field_material_intake|robot_diagnostics_task_terminal_field_material_intake_summary|现场材料回填入口|software_proof|not_proven|delivery_success=false|primary_actions_enabled=false|safe_to_control=false|Start Delivery|Confirm Dropoff|Cancel|Objective 4|PR #4" mobile/web mobile/fixtures docs/product/mobile_user_flow.md sprints/2026.05.19_12-13_task-terminal-field-material-intake
git diff --check -- mobile/web mobile/fixtures docs/product/mobile_user_flow.md sprints/2026.05.19_12-13_task-terminal-field-material-intake
```

### product-okr-owner

允许改动：

- `sprints/2026.05.19_12-13_task-terminal-field-material-intake/tech-done.md`
- `sprints/2026.05.19_12-13_task-terminal-field-material-intake/side2side_check.md`
- `sprints/2026.05.19_12-13_task-terminal-field-material-intake/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`

要求：

- 核对 Robot、Full-Stack 和 Autonomy 输出、验证日志和 docs 同步。
- 收口 Objective 5 不提高，Objective 1 不提高，Objective 2/3/4 只记录 `task_terminal_field_material_intake` 的主链路可回填性。
- 明确剩余风险：无真实 dropoff/cancel completion、无 delivery success、无真实电梯/Nav2/fixed-route、无真实手机、无 WAVE ROVER/UART/HIL、无 PR #5 真实材料、无 O5 external proof。
- 不能把 PRD、diagnostics summary、mobile panel、accepted safe refs、material intake status 或 ACK 写成真实完成。

验收命令：

```bash
test -f sprints/2026.05.19_12-13_task-terminal-field-material-intake/tech-done.md && test -f sprints/2026.05.19_12-13_task-terminal-field-material-intake/side2side_check.md && test -f sprints/2026.05.19_12-13_task-terminal-field-material-intake/final.md
rg -n "Objective 5|Objective 1|Objective 2|Objective 3|Objective 4|PR #4|PR #5|task_terminal_field_material_intake|robot_diagnostics_task_terminal_field_material_intake_summary|software_proof|not_proven|delivery_success=false|primary_actions_enabled=false|safe_to_control=false" OKR.md docs/process/okr_progress_log.md sprints/2026.05.19_12-13_task-terminal-field-material-intake
git diff --check -- OKR.md docs/process/okr_progress_log.md sprints/2026.05.19_12-13_task-terminal-field-material-intake
```

### autonomy-engineer

只读咨询，不写文件。

咨询范围：

- 确认 `task_terminal_field_material_intake` 的 route/elevator/Nav2 evidence fields 与 Objective 3 不冲突。
- 建议字段只作为 missing/next-required evidence，不使用 `route_passed`、`fixed_route_passed`、`nav2_passed`、`field_pass` 或 completion claim。
- 指出后续真实 Nav2/fixed-route runtime log、route completion signal、真实 task record、真实门状态、真实楼层确认、人工协助记录、dropoff/cancel material 回填时需要的字段。

输出要求：

- 只返回字段建议和风险；不得修改文件或运行实现/验收命令。

### hardware-engineer

本轮不写文件。

原因：

- 本轮不涉及 WAVE ROVER、ESP32、Orange Pi、UART、波特率、JSON 指令、速度映射、反馈协议、引脚、电压、固件或机械尺寸改动。
- PR #5 2D LiDAR / ToF 真实材料仍是独立 blocker，由现场 owner 后续补齐；本轮不得新增或猜测硬件事实。

## 4. 并行启动策略

本 sprint 是 Epic，跨 Robot、Full-Stack、Product 三个写 owner，并有 Autonomy 只读咨询。实现阶段必须并行启动至少 3 个 worker：

- `robot-software-engineer`
- `full-stack-software-engineer`
- `product-okr-owner`

建议同一轮并行再启动 `autonomy-engineer` 只读咨询，以免 Robot/Full-Stack 误把 route/elevator/Nav2 missing fields 写成 Objective 3 通过证据。

`product-okr-owner` 可先准备 closeout checklist 和 OKR 更新草案，但必须等 Robot / Full-Stack / Autonomy 输出返回后才能完成 `tech-done.md`、`side2side_check.md`、`final.md`、`OKR.md` 和 `docs/process/okr_progress_log.md`。

## 5. 接口边界

- Robot diagnostics 是 `robot_diagnostics_task_terminal_field_material_intake_summary` 的唯一上游事实源。
- mobile/web 只能消费 sanitized summary，不得读取 raw artifact、从 ACK/material status 推导 completion，或把 accepted safe refs 写成真实材料通过。
- Product closeout 只能记录 software-proof 主链路可回填性，不得上调 O5 external proof、O1 HIL、真实 route/elevator field pass、真实手机或 delivery success。
- 缺字段、unsupported schema、unsafe copy、success wording、raw path、checksum、credential、HIL/pass wording、field-pass wording、O5 external proof wording、control grant 均必须 fail closed。

建议 summary 字段：

```json
{
  "schema": "trashbot.task_terminal_field_material_intake.v1",
  "summary_alias": "robot_diagnostics_task_terminal_field_material_intake_summary",
  "status": "blocked_missing_field_materials",
  "source": "software_proof",
  "safe_evidence_ref": "safe-terminal-field-material-ref",
  "accepted_safe_refs": [],
  "missing_materials": [
    "real_task_record",
    "real_dropoff_or_cancel_terminal_material",
    "real_route_elevator_field_material",
    "real_phone_browser_evidence"
  ],
  "next_required_evidence": [
    "同一 safe evidence_ref 的真实 task record",
    "真实 dropoff/cancel terminal materials",
    "真实 route/elevator field materials",
    "真实手机/browser evidence"
  ],
  "phone_safe_copy": "现场材料尚未回填，当前只能查看缺口和下一步证据要求。",
  "evidence_boundary": [
    "software_proof",
    "not_proven",
    "delivery_success=false",
    "primary_actions_enabled=false",
    "safe_to_control=false"
  ]
}
```

## 6. 风险和阻塞

- Docker-only 主机无法采集真实 dropoff/cancel completion、真实 route/elevator field pass、真实 Nav2/fixed-route runtime、真实手机/browser、WAVE ROVER/UART/HIL 或 O5 external proof。
- PR #4 真实现场材料仍是独立缺口；本轮 field material intake 不能替代现场材料。
- PR #5 2D LiDAR / ToF 真实材料仍 blocked；本轮不新增硬件假设。
- 若实现发现旧 mobile panel 或 diagnostics copy 暗示 completion，需要降级为 `not_proven`，不能保留 success wording。

## 7. 本 Product planning 验收命令

Product Owner 启动文档完成后必须运行：

```bash
test -f sprints/2026.05.19_12-13_task-terminal-field-material-intake/pre_start.md && test -f sprints/2026.05.19_12-13_task-terminal-field-material-intake/prd.md && test -f sprints/2026.05.19_12-13_task-terminal-field-material-intake/tech-plan.md
rg -n "sprint_type: epic|OKR 最低优先级核对|Objective 5|Objective 1|Objective 2|Objective 3|Objective 4|PR #4|PR #5|task_terminal_field_material_intake|robot_diagnostics_task_terminal_field_material_intake_summary|software_proof|not_proven|delivery_success=false|primary_actions_enabled=false|safe_to_control=false|robot-software-engineer|full-stack-software-engineer|product-okr-owner" sprints/2026.05.19_12-13_task-terminal-field-material-intake
git diff --check -- sprints/2026.05.19_12-13_task-terminal-field-material-intake
```
