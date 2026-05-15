# Sprint 2026.05.15_13-14 Elevator Field Rehearsal Execution Pack - Tech Done

sprint_type: epic

## Task A - Autonomy execution pack CLI

Run time: 2026-05-16 00:05:35 CST

### 自主能力目标和本轮抓手

- 目标：把上一轮 `trashbot.elevator_field_run_review.v1` / summary 转成可交给现场同学执行的 `trashbot.elevator_field_run_execution_pack.v1` 和 `trashbot.elevator_field_run_execution_pack_summary.v1`。
- 抓手：新增 Docker/local software proof gate `software_proof_docker_elevator_field_rehearsal_execution_pack_gate`，将 review decision、blocked categories、operator next steps、commands to rerun 和 capture checklist 整理成受控电梯演练 manifest、材料模板、first-run/rerun 命令和 operator handoff。

### 实际改动和接口影响

- `pc-tools/evidence/elevator_field_run_execution_pack.py` 新增 CLI，支持 `--review-json`、`--output` 和 `--once-json`，只读上一轮 review artifact/summary，不访问 ROS graph、Nav2 runtime、serial/UART、WAVE ROVER、真实电梯、外部云、OSS/CDN、DB/queue 或 4G。
- CLI 输出固定包含 `same_evidence_ref_required=true`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`；缺 review、坏 JSON、unsupported schema/boundary、unsafe copy、success/control claim 和 blocked review 全部 fail closed。
- `pc-tools/evidence/test_elevator_field_run_execution_pack.py` 覆盖 ready、summary input、blocked review、missing/bad/unsupported input、success/control claim、success 文案和 unsafe redaction。
- `pc-tools/README.md`、`docs/product/elevator_assisted_delivery.md`、`docs/navigation/fixed_route_workflow.md` 同步记录 CLI 用法、schema、字段、边界和 not-proven 口径。
- 接口影响：新增 PC evidence artifact/summary schema，不改变 ROS2 action、`TrashStatus`、Robot diagnostics 控制动作或 mobile Start/Confirm/Cancel gating。

### 验证结果

- `PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile pc-tools/evidence/elevator_field_run_execution_pack.py pc-tools/evidence/test_elevator_field_run_execution_pack.py`：通过，无输出。
- `PYTHONDONTWRITEBYTECODE=1 python3 pc-tools/evidence/test_elevator_field_run_execution_pack.py`：通过，`Ran 7 tests in 0.026s`，`OK`。
- `python3 pc-tools/evidence/elevator_field_run_execution_pack.py --help`：通过，显示 `--review-json`、`--output` 和 `--once-json`。
- `rg -n "elevator_field_run_execution_pack|software_proof_docker_elevator_field_rehearsal_execution_pack_gate|delivery_success=false|primary_actions_enabled=false|not_proven" pc-tools/evidence pc-tools/README.md docs/product/elevator_assisted_delivery.md`：通过，命中 CLI、测试、README 和 product 文档；输出较长。
- `git diff --check -- pc-tools/evidence/elevator_field_run_execution_pack.py pc-tools/evidence/test_elevator_field_run_execution_pack.py pc-tools/README.md docs/product/elevator_assisted_delivery.md docs/navigation/fixed_route_workflow.md`：通过，无输出。

### 数据、样本或调试输出变化

- 新 artifact 生成 `controlled_rehearsal_manifest`、七类 `required_material_templates`、`first_run_commands`、`rerun_commands`、`operator_handoff` 和 phone-safe summary。
- `evidence_ref` 只保留安全引用，路径会降级为 basename；raw artifact、ROS topic、serial/UART、WAVE ROVER、credential 和成功文案不会进入可放行状态。

### 剩余风险

- 本任务只证明 execution pack CLI/schema/test/docs 在 Docker/local Python 环境可验证；不证明真实电梯门状态、真实目标楼层确认、真实人工协助、真实 Nav2/fixed-route runtime、WAVE ROVER/UART/HIL、真实 dropoff/cancel completion、真实手机设备或 delivery success。
- 仍需 Robot diagnostics 与 mobile panel 消费同一 summary，并由 Product closeout 统一更新 OKR/进度记录；Autonomy Task A 不更新 `OKR.md`、`side2side_check.md`、`final.md` 或 Product closeout 文件。

## Task B - Robot diagnostics metadata-only consumer

Run time: 2026-05-15 12:17:04 CST
复核补充时间：2026-05-16 00:06:11 CST

### 实际改动

- `operator_gateway_diagnostics.py` 新增 `elevator_field_run_execution_pack` / `elevator_field_run_execution_pack_summary` diagnostics 只读摘要。
- 支持 explicit ref、`TRASHBOT_ELEVATOR_FIELD_RUN_EXECUTION_PACK` 和 `TRASHBOT_ELEVATOR_FIELD_RUN_EXECUTION_PACK_SUMMARY`。
- 严格校验 `trashbot.elevator_field_run_execution_pack.v1` / summary wrapper、`software_proof_docker_elevator_field_rehearsal_execution_pack_gate`、`same_evidence_ref_required=true` 和 unsafe/redaction 边界。
- 固定 `metadata_only=true`、`delivery_success=false`、`primary_actions_enabled=false`，并保留 collect/dropoff/cancel、ACK、cursor、terminal ACK、Nav2、HIL、production readiness、dropoff/cancel completion 全部 false。
- `test_operator_gateway_diagnostics.py` 覆盖 artifact 直读、summary env、missing、unsupported schema/boundary、unsafe fields。
- `docs/interfaces/ros_contracts.md` 同步记录 diagnostics contract、env 名称、白名单字段和不触发动作链边界。
- 复核补充：`same_evidence_ref_required` 现在只接受 JSON boolean `true`；字符串 `"false"` 等弱类型会 fail closed 为 `unsafe_fields`，避免误放行同一 `evidence_ref` 约束。

### 验证结果

- `PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`：通过，无输出。
- `PYTHONDONTWRITEBYTECODE=1 python3 onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`：通过，复核后 `Ran 79 tests in 0.078s`，`OK`。
- `rg -n "elevator_field_run_execution_pack|software_proof_docker_elevator_field_rehearsal_execution_pack_gate|TRASHBOT_ELEVATOR_FIELD_RUN_EXECUTION_PACK|delivery_success|primary_actions_enabled" onboard/src/ros2_trashbot_behavior docs/interfaces/ros_contracts.md`：通过，命中新 contract、env、测试和文档；输出较长。
- `git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py docs/interfaces/ros_contracts.md`：通过，无输出。

### 剩余风险

- 本任务只证明 Robot diagnostics 可只读消费软件 artifact/summary；不证明真实电梯门状态、目标楼层、Nav2/fixed-route runtime、WAVE ROVER/UART/HIL、ACK、dropoff/cancel completion 或 delivery success。
- 需要 Autonomy Task A 产出的真实 `elevator_field_run_execution_pack` artifact，以及 Full-Stack Task C 的 mobile panel 消费，才能形成完整本轮 pack 展示闭环。

## Task C - Mobile read-only execution pack panel

Run time: 2026-05-16 00:05:36 CST

### 实际改动

- `mobile/web/app.js` 新增只读“电梯演练执行包” panel，兼容 top-level、`phone_readiness`、`diagnostics.summary`、`diagnostics.diagnostics_summary`、nested diagnostics summary 和 status diagnostics summary 中的 `elevator_field_run_execution_pack*`。
- panel 展示 `execution_pack_verdict`、safe `evidence_ref`、controlled rehearsal manifest、required material templates、first-run/rerun command summary、operator handoff、`safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`、`not_proven` 和 `software_proof_docker_elevator_field_rehearsal_execution_pack_gate`。
- 新增 `UNSAFE_ELEVATOR_FIELD_EXECUTION_PACK_TEXT` 与 `safeElevatorFieldExecutionPackText`，过滤 raw ROS topic、`/cmd_vel`、serial/UART、WAVE ROVER、local path、credential、raw artifact、raw execution pack、checksum、traceback 和 success phrasing。
- `mobile/fixtures/mobile_web_status.fixture.json` 增加 top-level、`phone_readiness` 与 diagnostics summary execution pack fixture，全部固定 `safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`。
- `mobile/test_mobile_web_entrypoint.py` 增加 Task C phone-safe/read-only 覆盖，确认 panel 不调用 Start/Confirm/Cancel，也不主动 fetch diagnostics。
- `docs/product/mobile_user_flow.md` 同步记录 panel 来源、可展示字段、兼容输入、证据边界和未证明事项。

### 验证结果

- `PYTHONDONTWRITEBYTECODE=1 python3 mobile/test_mobile_web_entrypoint.py`：通过，`Ran 44 tests in 0.119s`，`OK`。
- `PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile mobile/test_mobile_web_entrypoint.py`：通过，无输出。
- `node --check mobile/web/app.js`：通过，无输出。
- `rg -n "elevator_field_run_execution_pack|software_proof_docker_elevator_field_rehearsal_execution_pack_gate|delivery_success|primary_actions_enabled|not_proven" mobile docs/product/mobile_user_flow.md`：通过，命中 mobile panel、fixture、测试和产品文档；输出较长。
- `git diff --check -- mobile/web/app.js mobile/test_mobile_web_entrypoint.py mobile/fixtures/mobile_web_status.fixture.json docs/product/mobile_user_flow.md`：通过，无输出。

### 剩余风险

- 本任务只证明 Docker/local `mobile/web` 能只读展示 execution pack phone-safe summary；不证明真实电梯、真实 Nav2/fixed-route、WAVE ROVER/UART/HIL、真实手机/browser、真实 dropoff/cancel completion、delivery success 或 Objective 5 external proof。
- Start Delivery、Confirm Dropoff、Cancel gating 未改变，仍依赖既有 command_safety、readiness、operation log 和 action feedback gate。

## Task D - Product closeout / OKR owner

Run time: 2026-05-16 00:18 CST

### 用户价值和产品北极星

- 用户价值：把上一轮“复核决策”进一步整理成现场同学能照着执行的受控电梯演练包，降低 raw JSON、路径、命令和材料清单之间人工拼接的出错率。
- 产品北极星：继续服务“普通手机用户可验证地完成跨楼层送垃圾”，但本轮只推进现场补证准备链，不把软件 artifact 当成真实电梯或真实送达结果。

### OKR 映射和 KR 拆解

- Objective 2：对应 KR6/KR7，把电梯 assisted delivery 的门状态、目标楼层、人工协助、失败/接管、同一 `evidence_ref` 和可回放材料要求整理为 execution pack。
- Objective 3：支撑 Nav2/fixed-route runtime log 与 task record、completion signal、diagnostics/mobile safe summary 使用同一 `evidence_ref` 的现场执行材料链。
- Objective 5：本轮没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity 或 production worker/migration；保持约 66%，not real Objective 5 external proof。

### 本轮核心抓手和责任 Engineer

- Autonomy Algorithm Engineer：`elevator_field_run_execution_pack` CLI/schema/test/docs。
- Robot Platform Engineer：operator diagnostics metadata-only consumption 与弱类型 fail-closed。
- User Touchpoint Full-Stack Engineer：mobile/web 只读“电梯演练执行包” panel 和 phone-safe copy。
- Product Manager / OKR Owner：补齐 `side2side_check.md`、`final.md`、`OKR.md` 4.1/6 和 `docs/process/okr_progress_log.md`。

### Product 验收口径

- 必须保留 `software_proof_docker_elevator_field_rehearsal_execution_pack_gate` 边界。
- 必须写明 `delivery_success=false`、`primary_actions_enabled=false`、`not_proven`、`same_evidence_ref_required=true`。
- 必须明确本轮不证明真实电梯、真实 Nav2/fixed-route、WAVE ROVER/UART/HIL、真实手机/browser、真实 dropoff/cancel completion、真实 delivery success 或 Objective 5 external proof。

### Product 剩余风险

- 真实现场材料仍未补齐：电梯门状态、目标楼层确认、人工协助记录、真实喇叭/TTS、Nav2/fixed-route runtime、task completion、失败恢复、dropoff/cancel completion 和 delivery success。
- O5 external blocker 仍未解除；下一轮只有拿到真实外部材料才应推进 Objective 5 completion，否则继续转向 O2/O3 现场补证或上车复账。
