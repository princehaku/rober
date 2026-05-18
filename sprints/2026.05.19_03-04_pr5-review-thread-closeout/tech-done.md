# Sprint 2026.05.19_03-04 PR5 Review Thread Closeout - Tech Done

## sprint_type: epic

更新时间：2026-05-19 03:22 CST。

## 用户价值和产品北极星

用户价值：PR #5 的 review thread closeout 现在有 repo-local、可复跑、可跨 PC gate / Robot diagnostics / mobile/web 对照的判定链。现场 owner 能区分哪些 thread 可基于 mainline docs 关闭，哪些仍因真实 2D LiDAR / ToF 材料缺失保持 open。

产品北极星：低成本 ROS2 trash delivery robot 的硬件边界必须可追溯、可审计、不会把文档修复误读成真实硬件完成。本轮只交付 `pr5_review_thread_closeout` 的 `software_proof`，保持 `not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。

## OKR 映射和本轮核心抓手

- Objective 1：本轮主要推进 PR #5 review closeout 可判定性。P1 hardware boundary thread 和 P2 OKR narrative/table thread 可判定为 `ready_to_close_on_mainline_docs`；P2 mandatory sensor citation/material thread 仍是 `blocked_pending_real_materials`。
- Objective 4：mobile/web 增加只读展示，让普通 owner 能看到 PR #5 每条 review thread 的 decision、当前证据、缺失真实材料和 owner handoff。
- Objective 5：不推进。没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover 或 external proof。
- Objective 2 / Objective 3：不推进。PR #4 route/elevator field evidence 仍是独立缺口；本轮不证明真实 route/elevator field pass、Nav2/fixed-route、dropoff/cancel completion 或 delivery success。

## KR 拆解或更新

1. Objective 1 evidence hygiene：新增 `pr5_review_thread_closeout` gate，把 PR #5 review thread 转为可复跑 decision / evidence / missing material / owner handoff。
2. Objective 4 KR3 / KR9：手机和量产硬件边界展示能区分 default hardware set、target 2D LiDAR / ToF baseline、vendor-source coverage 和 pending real materials。
3. Product closeout KR：OKR 只记录 review closeout 判定链进展，不上调真实 HIL、真实硬件、真实 field pass、真实手机或 O5 external proof。

## Hardware worker

### 实际改动

- `pc-tools/evidence/pr5_review_thread_closeout_gate.py`
  - 新增 `trashbot.pr5_review_thread_closeout.v1` / `trashbot.pr5_review_thread_closeout_summary.v1` gate。
  - 读取安全 PR #5 thread summary、`docs/product/production_hardware_boundary.md`、`docs/vendor/VENDOR_INDEX.md`、`OKR.md`，输出逐 thread closeout decision。
  - 对 P1 hardware boundary contradiction 输出 `ready_to_close_on_mainline_docs`；对 P2 OKR narrative/table mismatch 输出 `ready_to_close_on_mainline_docs`；对 P2 mandatory sensor citation/material thread 输出 `blocked_pending_real_materials`。
  - 保持 `software_proof`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`，并 fail closed unsafe / success / control 文案。
- `tests/test_pr5_review_thread_closeout_gate.py`
  - 覆盖三类 PR #5 thread decision、缺 mainline evidence、unsafe-claim detector、summary flags 和 rerun command。
- `docs/product/production_hardware_boundary.md`
  - 补齐 PR #5 closeout 所需的 default hardware set / target 2D LiDAR + ToF pending baseline / vendor-source attribution boundary。
- `docs/interfaces/evidence_contracts.md`
  - 补充 `pr5_review_thread_closeout` evidence contract 和安全边界。

### 验证结果

```bash
test -f docs/vendor/VENDOR_INDEX.md
# passed
```

```bash
python3 -m py_compile pc-tools/evidence/pr5_review_thread_closeout_gate.py
# passed
```

```bash
python3 -m unittest tests/test_pr5_review_thread_closeout_gate.py
# Ran 7 tests
# OK
```

```bash
rg -n "pr5_review_thread_closeout|PR #5|production_hardware_boundary|docs/vendor/VENDOR_INDEX.md|ready_to_close_on_mainline_docs|blocked_pending_real_materials|still_open_missing_current_evidence|software_proof|not_proven|delivery_success=false|primary_actions_enabled=false" pc-tools/evidence tests docs/product docs/interfaces sprints/2026.05.19_03-04_pr5-review-thread-closeout
# passed
```

```bash
git diff --check -- pc-tools/evidence tests docs/product docs/interfaces sprints/2026.05.19_03-04_pr5-review-thread-closeout
# passed
```

### 失败定位和修复

- 初始 unsafe-claim detector 把 contract examples 误判为 unsafe claim。
- 已修正 detector 作用域，保留对真实 success/control claim 的拦截，同时允许文档中的 fail-closed examples。

### 剩余风险

- 仅为 Docker-only / repo-local `software_proof`，不证明 GitHub reviewer 已真实关闭 thread。
- 不证明真实 2D LiDAR / ToF SKU/source/receipt/procurement/installation/wiring/power/calibration/HIL-entry。
- 不证明 WAVE ROVER/UART/HIL、route/elevator field pass、真实手机/browser、O5 external proof 或 delivery success。

## Robot worker

### 实际改动

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
  - 新增 `robot_diagnostics_pr5_review_thread_closeout_summary` safe alias。
  - 只读消费 Hardware gate 的 `trashbot.pr5_review_thread_closeout_summary.v1` / `trashbot.pr5_review_thread_closeout.v1`，并要求 direct artifact 携带 sanitized summary；缺 summary fail closed。
  - 保持 `software_proof`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`，并禁止 collect/dropoff/cancel、ACK、cursor、Nav2、HIL、`/cmd_vel` 和 production readiness。
  - 对 unsupported schema/boundary、unsafe copy/raw review body、success wording、`delivery_success=true`、`primary_actions_enabled=true`、弱 `evidence_ref` 做 fail-closed。
- `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
  - 新增 safe alias 正向测试，覆盖 summary wrapper、payload aliases、latest_status 去原始字段和控制路径全部 false。
  - 新增缺 summary、unsupported schema、unsafe success/control/raw review body 的 fail-closed 测试。
- `docs/interfaces/ros_contracts.md`
  - 补充 PR #5 review thread closeout diagnostics contract，明确 summary-only、metadata-only、software-proof 和禁止控制路径。

### 验证结果

```bash
python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py
# passed
```

```bash
python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
# Ran 194 tests in 0.453s
# OK
```

```bash
rg -n "robot_diagnostics_pr5_review_thread_closeout_summary|pr5_review_thread_closeout|PR #5|review thread|software_proof|not_proven|delivery_success=false|primary_actions_enabled=false" onboard/src/ros2_trashbot_behavior docs/interfaces sprints/2026.05.19_03-04_pr5-review-thread-closeout
# passed
```

```bash
git diff --check -- onboard/src/ros2_trashbot_behavior docs/interfaces sprints/2026.05.19_03-04_pr5-review-thread-closeout
# passed
```

### 失败定位和修复

- 第一轮 unittest 失败：`NameError: name '_dedupe_ordered' is not defined`，原因是新 summarizer 复用了不存在的 helper。
- 已修复：新增 `_dedupe_ordered`，保持 diagnostics 摘要字段顺序并去重。
- 第二轮 unittest 失败：正向 PR #5 summary 被判定为 `blocked_unsafe_pr5_review_thread_closeout_summary`，原因是 unsafe checker 把 `not_proven=["delivery_success"]` 误判为 success wording。
- 已修复：`_pr5_review_thread_closeout_has_unsafe_fields` 对 `not_proven` 列表跳过 unsafe 文案检查，同时仍拦截 raw/control/success fields。

### 剩余风险

- 只证明 Robot diagnostics 对 PR #5 closeout summary 的本地 `software_proof` 消费路径。
- 不证明 reviewer closeout、真实材料、HIL、Nav2/fixed-route、dropoff/cancel completion 或 delivery success。

## Full-Stack worker

### 实际改动

- `mobile/web/app.js`
  - 增加 PR #5 review closeout 只读 panel，展示每条 review thread 的 decision、当前证据、缺失真实材料和 owner handoff。
  - 缺 summary / unsupported schema fail closed 到 `still_open_missing_current_evidence`。
  - 不触发 Start Delivery、Confirm Dropoff、Cancel，不新增主动 diagnostics fetch。
- `mobile/web/styles.css`
  - 增加 PR #5 closeout panel 的只读状态样式。
- `mobile/web/test_mobile_web_entrypoint.py`
  - 覆盖 safe summary、missing summary、blocked pending materials、ready-to-close、unsupported schema 和 action gating 不变。
- `mobile/web/fixtures/status.json`、`mobile/fixtures/mobile_web_status.fixture.json`
  - 增加 safe PR #5 review closeout fixture。
- `docs/product/mobile_user_flow.md`
  - 补充手机端只读展示边界，明确不等于真实手机/browser、硬件或 delivery success。

### 验证结果

```bash
python3 mobile/web/test_mobile_web_entrypoint.py
# Ran 104 tests in 0.655s
# OK
```

```bash
python3 -m py_compile mobile/web/test_mobile_web_entrypoint.py
# passed
```

```bash
node --check mobile/web/app.js
# passed
```

```bash
rg -n "pr5_review_thread_closeout|PR #5|review thread|ready_to_close_on_mainline_docs|blocked_pending_real_materials|still_open_missing_current_evidence|software_proof|not_proven|delivery_success=false|primary_actions_enabled=false|Start Delivery|Confirm Dropoff|Cancel" mobile/web mobile/fixtures docs/product/mobile_user_flow.md sprints/2026.05.19_03-04_pr5-review-thread-closeout
# passed
```

```bash
git diff --check -- mobile/web mobile/fixtures docs/product/mobile_user_flow.md sprints/2026.05.19_03-04_pr5-review-thread-closeout
# passed
```

### 失败定位和修复

- Full-Stack worker 未报告失败；targeted validation 一次通过。

### 剩余风险

- static mobile/web + fixture `software_proof` only。
- 未接真实 ROS2/GitHub API、真实手机浏览器、真实硬件或真实 O5 external proof。

## Product closeout 待办

- 创建 `side2side_check.md` 和 `final.md`。
- 更新 `OKR.md` 4.1 当前快照、第 6 节最高优先级和 `docs/process/okr_progress_log.md`。
- Product closeout 只能记录 PR #5 review closeout 可判定性进展，不提高真实硬件/HIL/O5 external proof。
