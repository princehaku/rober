# Sprint 2026.05.18_20-21 OKR Evidence Rerank Real Material Escalation - Tech Plan

## 1. Plan 状态

- sprint_type: epic
- 本轮主题：`okr_evidence_rerank_real_material_escalation`
- 目标边界：`source=software_proof`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`
- 执行原则：本轮只建立真实材料升级 / 改道决策，不写产品代码，不新增测试文件，不继续包装同一 route/elevator 或 hardware blocker。
- 验证原则：测试只围栏；只跑 `rg`、文件存在检查、scoped `git diff --check`。若后续进入实现，Engineer 只跑各自 focused unittest / `py_compile` / `node --check` / scoped diff check。

## OKR 最低优先级核对

1. `OKR.md` 4.1 当前数字最低 Objective 是 Objective 5，约 68%。
2. 本 sprint 不直接推进 Objective 5。原因：本机没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker/migration/cutover 或真实手机/browser external proof。按 O5 stop rule，不能继续堆本地 metadata depth。
3. 下一低项 Objective 1 约 81%。本 sprint 不直接推进 Objective 1。原因：本机没有真实 WAVE ROVER/UART/HIL、`feedback_T1001.log`、`/odom`、`/imu/data`、`/battery` 或 operator HIL report；PR #5 真实 2D LiDAR / ToF 材料也不存在。5/16 硬件链路已经消费过该缺口，不能继续本地包装同一 hardware blocker。
4. Objective 2 / Objective 3 / Objective 4 约 99%，但 18-19 与 19-20 两轮已连续收口到缺 PR #4 真实 route/elevator field materials。本轮不得第三次消费该 blocker。
5. 本 sprint 选择升级 / 改道决策：如果 CEO 能提供真实材料，下一轮按对应 owner 直接进入材料 intake / review；如果不能提供真实材料，下一轮必须选择不依赖 O5/O1/PR #4/PR #5 真实材料的新功能切口，或明确暂停对应 KR 完成度上调。

## 2. 同一 Blocker 红线

最近两轮结论：

- `sprints/2026.05.18_18-19_route-task-acceptance-execution-rerun-result-review-decision/final.md`：缺真实 route/elevator field materials。
- `sprints/2026.05.18_19-20_route-task-acceptance-execution-rerun-result-review-handoff/final.md`：仍缺真实电梯门状态、楼层确认、人工协助记录、Nav2/fixed-route runtime log、task record/completion signal、dropoff/cancel completion 或 delivery result。

因此本轮不得继续创建 `route_task_field_retest_acceptance_execution_rerun_result_*` 的下一层本地 wrapper。若 CEO 明确要求继续同一 blocker，必须在新的 `pre_start.md` 引用 CEO 原话后计数重置。

## 3. PR #4 / PR #5 证据

- PR #4 已合并：电梯 assisted delivery 成为主链能力。下一步必须补真实现场材料，而不是再证明 metadata 层可流转。
- PR #5 review：
  - P1：Default Hardware Set 与 mandatory `monocular + 2D LiDAR + ToF` baseline 曾矛盾。
  - P2：OKR 最低项叙述曾漂移。
  - P2：mandatory sensor 假设缺 `docs/vendor/` source。
- 当前 `docs/product/production_hardware_boundary.md` 已记录：本地 vendor tree 不证明项目 2D LiDAR / ToF 已采购、安装、接线、标定或 HIL；相关材料保持 `hardware_material_pending`、`not_proven`。

## 4. Owner Work Orders

### Task A - Product Manager / OKR Owner

文件范围：

- `sprints/2026.05.18_20-21_okr-evidence-rerank-real-material-escalation/tech-done.md`
- `sprints/2026.05.18_20-21_okr-evidence-rerank-real-material-escalation/side2side_check.md`
- `sprints/2026.05.18_20-21_okr-evidence-rerank-real-material-escalation/final.md`
- 如进入真实材料路径，后续可更新 `OKR.md` 与 `docs/process/okr_progress_log.md`；本轮 planning 不更新完成度。

需要做什么：

- 汇总本轮升级结论：O5/O1/PR #4/PR #5 哪些材料缺失、谁负责、拿到材料后进入哪条 intake / review 链路。
- 若后续仍无真实材料，明确下一轮改道候选，不允许继续同一 blocker。
- 收口时不得上调 OKR。

验收命令：

```bash
rg -n "Objective 5|Objective 1|PR #4|PR #5|同一 Blocker|Docker-only|source=software_proof|not_proven|delivery_success=false|primary_actions_enabled=false" sprints/2026.05.18_20-21_okr-evidence-rerank-real-material-escalation
git diff --check -- sprints/2026.05.18_20-21_okr-evidence-rerank-real-material-escalation
```

### Task B - Hardware Infra Engineer

文件范围：

- 本轮只读咨询：`docs/vendor/VENDOR_INDEX.md`
- 本轮只读咨询：`docs/product/production_hardware_boundary.md`
- 后续若 CEO 提供真实材料，才允许在新的 sprint 中更新硬件 intake/review artifact 或 docs。

需要做什么：

- 输出 O1 / PR #5 真实材料清单：WAVE ROVER/UART/HIL packet、`feedback_T1001.log`、`odom_once.jsonl`、`imu_once.jsonl`、`battery_once.jsonl`、operator HIL report、2D LiDAR / ToF SKU/source/receipt/procurement/installation/wiring/power/calibration/HIL-entry。
- 明确 `docs/vendor/VENDOR_INDEX.md` 当前只证明 Orange Pi / WAVE ROVER / UART JSON / firmware / mechanical / vendor app coverage，不证明 2D LiDAR / ToF 项目材料。

验收命令：

```bash
rg -n "Orange Pi Zero 3|WAVE ROVER|UART|newline-delimited JSON|2D LiDAR|ToF|not prove|hardware_material_pending" docs/vendor/VENDOR_INDEX.md docs/product/production_hardware_boundary.md
```

### Task C - Autonomy Algorithm Engineer

文件范围：

- 本轮只读咨询：`sprints/2026.05.18_18-19_route-task-acceptance-execution-rerun-result-review-decision/final.md`
- 本轮只读咨询：`sprints/2026.05.18_19-20_route-task-acceptance-execution-rerun-result-review-handoff/final.md`
- 后续若 CEO 提供真实材料，才允许在新的 sprint 中回填 route/elevator material intake 或 review artifact。

需要做什么：

- 输出 PR #4 真实 route/elevator field material 最小包：door state、target floor confirmation、human assistance note、Nav2/fixed-route runtime log、route completion signal、task record、dropoff/cancel completion、delivery result、diagnostics/mobile safe summary，同一 safe `evidence_ref`。
- 明确不能再增加本地 route wrapper 来替代真实材料。

验收命令：

```bash
rg -n "真实电梯门状态|真实楼层确认|人工协助记录|Nav2/fixed-route runtime log|task record|completion signal|dropoff/cancel completion|delivery result|same.*evidence_ref|software_proof" sprints/2026.05.18_18-19_route-task-acceptance-execution-rerun-result-review-decision/final.md sprints/2026.05.18_19-20_route-task-acceptance-execution-rerun-result-review-handoff/final.md OKR.md
```

### Task D - User Touchpoint Full-Stack Engineer

文件范围：

- 本轮只读咨询：`docs/product/mobile_user_flow.md`
- 本轮只读咨询：`mobile/web/app.js`
- 后续若 CEO 提供真实手机材料，才允许在新的 sprint 中进入 mobile real-device intake / review / acceptance session 更新。

需要做什么：

- 输出 O4 真实手机材料清单：真实 iPhone/Android device behavior、production app URL/release summary、真实 PWA prompt/user choice、真实截图/observer note、真实 browser metadata。
- 确认 Start Delivery、Confirm Dropoff、Cancel 继续由 command safety / readiness / action feedback 等 gate fail-closed，不因材料清单变绿。

验收命令：

```bash
rg -n "mobile_real_device|production app|PWA install prompt|user choice|safe_to_control=false|not_proven|Start Delivery|Confirm Dropoff|Cancel" docs/product/mobile_user_flow.md mobile/web/app.js
```

## 5. 集成验收口径

本轮收口必须满足：

- fresh sprint 目录存在，且 `pre_start.md`、`prd.md`、`tech-plan.md` 都含 `sprint_type: epic`。
- 每条下一步建议都有具体证据：PR #4、PR #5 review、`OKR.md` 4.1、最近两轮 `final.md`、`docs/product/production_hardware_boundary.md`。
- 明确 O5/O1 为什么不能在 Docker-only 主机继续本地包装。
- 明确最近两轮 PR #4 route/elevator blocker 已连续消费，第三轮必须升级或改道。
- 不上调 OKR，不新增 product code，不新增测试文件。

集成围栏：

```bash
test -f sprints/2026.05.18_20-21_okr-evidence-rerank-real-material-escalation/pre_start.md && test -f sprints/2026.05.18_20-21_okr-evidence-rerank-real-material-escalation/prd.md && test -f sprints/2026.05.18_20-21_okr-evidence-rerank-real-material-escalation/tech-plan.md
rg -n "sprint_type: epic|PR #4|PR #5|Objective 5|Objective 1|Docker-only|同一 Blocker|OKR 最低优先级核对|验收命令|owner|source=software_proof|not_proven|delivery_success=false|primary_actions_enabled=false" sprints/2026.05.18_20-21_okr-evidence-rerank-real-material-escalation
git diff --check -- sprints/2026.05.18_20-21_okr-evidence-rerank-real-material-escalation
```

## 6. 剩余风险

- 没有真实外部云材料时，Objective 5 仍不能上调。
- 没有真实 WAVE ROVER/UART/HIL 或真实 2D LiDAR / ToF 材料时，Objective 1 仍不能上调。
- 没有真实 route/elevator field materials 时，Objective 2 / 3 不能从 99% 变成真实完成。
- 没有真实 iPhone/Android / production app / PWA prompt/user choice 时，Objective 4 不能写成真实手机验收完成。
