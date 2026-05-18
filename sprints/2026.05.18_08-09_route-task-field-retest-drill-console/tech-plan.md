# Sprint 2026.05.18_08-09 Route Task Field Retest Drill Console - Tech Plan

sprint_type: epic

## 1. 计划状态

本计划可直接进入实现阶段。实现必须按 AGENTS.md 并行派 3 个 worker：Autonomy、Robot、Full-stack。Product Owner 本阶段不写产品代码、测试代码或硬件配置。

本轮目标：从上一轮 `route_task_field_retest_operator_drill` 推进到 `route_task_field_retest_drill_console`，交付 `software_proof_docker_route_task_field_retest_drill_console_gate`，把 PR #4 route/elevator 现场材料演练变成可执行、可导出的控制台 software proof。

## 2. OKR 最低优先级核对

当前 `OKR.md` 4.1 完成度最低 Objective：

- Objective 5：约 68%。

下一低项：

- Objective 1：约 81%。

本 sprint 是否针对最低 Objective：

- 不直接针对 Objective 5。

具体理由：

- Objective 5 当前需要真实 external proof：公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker/migration/cutover 或真实手机/browser external evidence。本机没有真实 external cloud/4G/DB/queue/OSS/CDN/手机材料，继续堆本地 metadata depth 会重复消费同一 blocker。
- Objective 1 当前需要真实 WAVE ROVER/UART/HIL、`feedback_T1001.log`、`/odom`、`/imu/data`、`/battery`、operator HIL report，以及 PR #5 真实 2D LiDAR / ToF source、receipt、procurement、installation、wiring、power、calibration、HIL-entry 材料。本机没有真实硬件，不能用 Docker proof 继续包装 O1。
- PR #4 已把 elevator-assisted delivery 作为主链路必达能力，但 PR #4 无 runtime integration tests；最新 `2026.05.18_07-08_route-task-material-review-operator-drill/final.md` 指向继续做 PR #4 现场材料回填/演练层。因此本轮转向 Objective 2 / 3 / 4 的 route/elevator field material 路线。

## 3. PR / review 证据

- PR #4：`Add elevator-assisted delivery capability to agents, registry and OKR` 已合并，说明 elevator-assisted delivery 是主链路必达能力；PR body 的 testing 明确没有运行 runtime integration tests。
- PR #5 review P1：`docs/product/production_hardware_boundary.md` default hardware set 没有列出 2D LiDAR 或 ToF，但同文档后文把 `monocular + 2D LiDAR + ToF` 写成 mandatory baseline，存在 BOM/procurement 与 bringup 漏项风险。
- PR #5 review P2：mandatory sensor assumptions 引入 sensor mix 和 ToF channel count 等具体硬件假设，但缺少 `docs/vendor/` evidence citation，违反硬件事实需本地资料追溯的项目规则。
- 最新 final：`route_task_field_retest_operator_drill` 已消费 material callback review decision，但没有真实 route/elevator field pass；下一步应把 operator drill 带到 PR #4 现场材料回填或继续现场演练层。

## 4. 目标接口和证据边界

新增/目标 schema：

- `trashbot.route_task_field_retest_drill_console.v1`
- `trashbot.route_task_field_retest_drill_console_summary.v1`

目标 gate：

- `software_proof_docker_route_task_field_retest_drill_console_gate`

输入优先级：

1. `route_task_field_retest_operator_drill` artifact
2. `route_task_field_retest_operator_drill_summary`
3. diagnostics/status 中的 nested 或 top-level compatible wrapper

必须保留：

- `not_proven`
- `delivery_success=false`
- `primary_actions_enabled=false`
- 同一 safe `evidence_ref`
- copy/export whitelist-only

不得引入或声称：

- route/elevator field pass
- Nav2/fixed-route pass
- task record/completion signal completed
- dropoff/cancel completion
- delivery success
- HIL、WAVE ROVER/UART、真实串口
- 真实 phone/browser/device proof
- Objective 5 external proof

## 5. 并行 worker A：Autonomy Engineer

角色：`autonomy-engineer`

文件范围：

- `pc-tools/evidence/route_task_field_retest_drill_console.py`
- `pc-tools/evidence/README.md`
- `tests/test_route_task_field_retest_drill_console.py`
- `docs/product/mobile_user_flow.md` 中仅追加/更新 drill console 证据边界段落
- 当前 sprint 的 `tech-done.md` 中 Autonomy 小节

接口边界：

- 只消费上一轮 `route_task_field_retest_operator_drill` artifact / summary / wrapper。
- 输出 artifact 和 summary 必须使用 `trashbot.route_task_field_retest_drill_console.v1` / `_summary.v1`。
- 不调用 ROS、Nav2、串口、WAVE ROVER、浏览器、云、OSS/CDN 或真实硬件。
- 不写 Robot/mobile 文件。

验收命令：

```bash
python3 -m py_compile pc-tools/evidence/route_task_field_retest_drill_console.py
python3 -m unittest tests.test_route_task_field_retest_drill_console
rg -n "route_task_field_retest_operator_drill|route_task_field_retest_drill_console|software_proof_docker_route_task_field_retest_drill_console_gate|not_proven|delivery_success=false|primary_actions_enabled=false" pc-tools/evidence tests docs/product/mobile_user_flow.md sprints/2026.05.18_08-09_route-task-field-retest-drill-console
git diff --check -- pc-tools/evidence/route_task_field_retest_drill_console.py pc-tools/evidence/README.md tests/test_route_task_field_retest_drill_console.py docs/product/mobile_user_flow.md sprints/2026.05.18_08-09_route-task-field-retest-drill-console
```

## 6. 并行 worker B：Robot Platform Engineer

角色：`robot-software-engineer`

文件范围：

- `operator_gateway/operator_gateway_diagnostics.py`
- `tests/test_operator_gateway_diagnostics.py`
- `docs/product/mobile_user_flow.md` 中仅追加/更新 Robot diagnostics 只读消费说明
- 当前 sprint 的 `tech-done.md` 中 Robot 小节

接口边界：

- 只读发现 `route_task_field_retest_drill_console_summary` 和 compatible nested/top-level summaries。
- 输出 diagnostics alias 时必须保持 safe summary，不透出 raw artifact、local path、checksum、traceback、ROS topic、serial/UART、credentials。
- 不改变 Start Delivery、Confirm Dropoff、Cancel、ACK、cursor 或 robot command 授权。
- 不写 Autonomy CLI 或 mobile/web 文件。

验收命令：

```bash
python3 -m py_compile operator_gateway/operator_gateway_diagnostics.py
python3 -m unittest tests.test_operator_gateway_diagnostics
rg -n "route_task_field_retest_drill_console|software_proof_docker_route_task_field_retest_drill_console_gate|not_proven|delivery_success=false|primary_actions_enabled=false|robot_diagnostics_route_task_field_retest_drill_console_summary" operator_gateway tests docs/product/mobile_user_flow.md sprints/2026.05.18_08-09_route-task-field-retest-drill-console
git diff --check -- operator_gateway/operator_gateway_diagnostics.py tests/test_operator_gateway_diagnostics.py docs/product/mobile_user_flow.md sprints/2026.05.18_08-09_route-task-field-retest-drill-console
```

## 7. 并行 worker C：User Touchpoint Full-Stack Engineer

角色：`full-stack-software-engineer`

文件范围：

- `mobile/web/app.js`
- `mobile/web/styles.css`
- `mobile/web/index.html` 仅在必须挂载区域时修改
- `mobile/tests/test_mobile_web_entrypoint.py`
- `docs/product/mobile_user_flow.md` 中仅追加/更新 mobile/web drill console 面板说明
- 当前 sprint 的 `tech-done.md` 中 Full-stack 小节

接口边界：

- 只读展示 `route_task_field_retest_drill_console` / `_summary` / compatible summaries。
- 只显示 safe `evidence_ref`、console status、operator command groups、callback checklist、required outputs、rerun summary、safe copy、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。
- copy/export 只能 whitelist-only；缺 safe copy 时显示 blocked copy unavailable。
- 不改变 Start Delivery、Confirm Dropoff、Cancel gating，不发送新 robot command，不 fetch raw artifact。
- 不写 Autonomy CLI 或 Robot diagnostics 文件。

验收命令：

```bash
node --check mobile/web/app.js
python3 -m unittest mobile.tests.test_mobile_web_entrypoint
rg -n "route_task_field_retest_drill_console|software_proof_docker_route_task_field_retest_drill_console_gate|not_proven|delivery_success=false|primary_actions_enabled=false|blocked copy unavailable" mobile/web mobile/tests docs/product/mobile_user_flow.md sprints/2026.05.18_08-09_route-task-field-retest-drill-console
git diff --check -- mobile/web/app.js mobile/web/styles.css mobile/web/index.html mobile/tests/test_mobile_web_entrypoint.py docs/product/mobile_user_flow.md sprints/2026.05.18_08-09_route-task-field-retest-drill-console
```

## 8. Product closeout after workers

角色：`product-okr-owner`

文件范围：

- `OKR.md`
- `sprints/2026.05.18_08-09_route-task-field-retest-drill-console/tech-done.md`
- `sprints/2026.05.18_08-09_route-task-field-retest-drill-console/side2side_check.md`
- `sprints/2026.05.18_08-09_route-task-field-retest-drill-console/final.md`

验收命令：

```bash
rg -n "route_task_field_retest_operator_drill|route_task_field_retest_drill_console|software_proof_docker_route_task_field_retest_drill_console_gate|Objective 5|Objective 1|PR #4|PR #5|not_proven|delivery_success=false|primary_actions_enabled=false" OKR.md docs/product/mobile_user_flow.md sprints/2026.05.18_08-09_route-task-field-retest-drill-console
git diff --check -- OKR.md docs/product/mobile_user_flow.md sprints/2026.05.18_08-09_route-task-field-retest-drill-console
```

Product closeout 必须确认：

- docs/ 已由相关 owner 同步到最新状态。
- 新增代码技术注释使用中文且比例超过 20%；如不满足，退回对应 Engineer。
- `OKR.md` 只保守记录 software proof，不上调 Objective 5 或 Objective 1。
- 如果没有真实 route/elevator field pass、HIL、真实手机/browser 或 O5 external proof，不得提高对应完成度。

## 9. 集成顺序和冲突控制

- 三个 worker 必须并行启动，因为文件范围互不重叠，仅共享 `docs/product/mobile_user_flow.md` 和当前 sprint `tech-done.md` 的小节；共享文件需由各 worker 只改自己小节，Product closeout 最后整理。
- 若 `docs/product/mobile_user_flow.md` 发生冲突，由 Product closeout 保留三方证据边界，不删除任何 owner 的验证结果。
- 若任何 worker 的 fenced 验证失败，主节点必须把失败定位和重试任务派回对应 worker，不得直接由主节点修代码。

## 10. 本计划自身验收命令

```bash
rg -n "sprint_type: epic|route_task_field_retest_operator_drill|route_task_field_retest_drill_console|software_proof_docker_route_task_field_retest_drill_console_gate|Objective 5|Objective 1|PR #4|PR #5|not_proven|delivery_success=false|primary_actions_enabled=false|OKR 最低优先级核对" sprints/2026.05.18_08-09_route-task-field-retest-drill-console
git diff --check -- sprints/2026.05.18_08-09_route-task-field-retest-drill-console
```
