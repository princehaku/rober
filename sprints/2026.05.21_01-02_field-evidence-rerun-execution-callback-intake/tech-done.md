# Field Evidence Rerun Execution Callback Intake Tech Done

## Worker 1 - Autonomy Algorithm Engineer

### 自主能力目标和本轮抓手

- 目标 capability：`field_evidence_rerun_execution_callback_intake`。
- 证据边界：`software_proof_docker_field_evidence_rerun_execution_callback_intake_gate`。
- 本轮抓手：新增 PC-only fail-closed gate，消费 `field_evidence_rerun_execution_pack` artifact/summary 和 field owner execution callback packet，把 `task_record`、`nav2_fixed_route_runtime_log`、`route_completion_signal`、`elevator_door_state`、`target_floor_confirmation`、`human_assistance_record`、`dropoff_completion`、`cancel_completion`、`delivery_result`、`phone_browser_evidence` 归类为 `accepted`、`missing`、`rejected`、`blocked`。

### 改动文件和接口影响

- `pc-tools/evidence/field_evidence_rerun_execution_callback_intake.py`
  - 新增 `build_field_evidence_rerun_execution_callback_intake(...)` 和 CLI。
  - 输出 `trashbot.field_evidence_rerun_execution_callback_intake.v1` artifact、`trashbot.field_evidence_rerun_execution_callback_intake_summary.v1` summary，以及 safe alias `robot_diagnostics_field_evidence_rerun_execution_callback_intake_summary`。
- `tests/test_field_evidence_rerun_execution_callback_intake.py`
  - 新增离线围栏测试，覆盖 ready、missing input、unsupported source、non-ready source、mismatch、weak same-ref、unknown category、invalid classification、missing/rejected/blocked material、unsafe copy、success claim、wrapper/nested JSON。
- `pc-tools/README.md`
  - 记录 CLI 用法、schema、required categories、status mapping、非真实现场证明边界。
- `docs/interfaces/evidence_contracts.md`
  - 记录 canonical artifact/summary contract、safe alias、fail-closed 映射和 non-claim 边界。

### 实现内容

- Gate 只接受 `source=software_proof`、`not_proven`、`safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false` 的 source execution pack 和 callback packet。
- Gate 校验 source execution pack boundary 为 `software_proof_docker_field_evidence_rerun_execution_pack_gate`，并要求 `execution_pack_status=ready_for_field_evidence_rerun_execution_pack_not_proven`。
- Gate 校验 CLI、source、packet 使用同一 safe `evidence_ref`，且 `same_evidence_ref_required` 必须是真布尔 `true`。
- Gate 递归脱敏并阻断 raw path、credential、ROS topic、`/cmd_vel`、serial/UART、WAVE ROVER、checksum、complete/raw artifact、traceback、success/control wording。
- Gate 输出 `accepted_materials`、`missing_materials`、`rejected_materials`、`blocked_materials`、`owner_handoff`、`next_required_evidence`、`safe_copy`，同时保持 `not_proven`、`safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`。

### 测试、dry-run 或上车验证结果

```text
python3 -m py_compile pc-tools/evidence/field_evidence_rerun_execution_callback_intake.py
# exit 0

python3 -m unittest tests.test_field_evidence_rerun_execution_callback_intake
......
----------------------------------------------------------------------
Ran 6 tests in 0.161s

OK

python3 pc-tools/evidence/field_evidence_rerun_execution_callback_intake.py --help
usage: field_evidence_rerun_execution_callback_intake.py [-h]
                                                         --execution-pack-json EXECUTION_PACK_JSON
                                                         --callback-packet-json CALLBACK_PACKET_JSON
                                                         [--evidence-ref EVIDENCE_REF]
                                                         [--output OUTPUT]
                                                         [--summary-output SUMMARY_OUTPUT]
                                                         [--once-json]
```

### 数据、样本或调试输出变化

- 新增 canonical artifact/summary schema，不新增真实材料样本、不读取真实材料目录、不访问 ROS graph/Nav2 runtime/电梯/手机/browser/硬件。
- `accepted` 只代表 execution callback packet 的材料分类可进入后续 review，不代表真实 field rerun、真实 Nav2/fixed-route、真实电梯、真实 phone/browser、WAVE ROVER/UART/HIL、O5 external proof、PR #5 resolved 或 `delivery_success`。

### 剩余风险和下一步能力建设建议

- 剩余风险：本 worker 只完成 PC gate 和 canonical contract；Robot diagnostics safe alias 与 mobile/web read-only panel 由其他 worker 并行交付。
- 剩余风险：验证范围是 Docker/local software proof；没有真实 field rerun、真实 Nav2/fixed-route runtime log、真实电梯门/楼层、真实手机/browser 或 HIL。
- 下一步建议：等待 Robot/mobile worker 合并 safe alias 和只读面板后，由 Product closeout 汇总三方验证并决定是否进入 execution callback review decision rung。

## Worker 2 - Robot Platform Engineer

### 机器人软件目标和本轮抓手

- 目标 capability：`field_evidence_rerun_execution_callback_intake` Robot diagnostics safe alias。
- 证据边界：`software_proof_docker_field_evidence_rerun_execution_callback_intake_gate`。
- 本轮抓手：新增 `robot_diagnostics_field_evidence_rerun_execution_callback_intake_summary`，只消费 canonical sanitized callback-intake summary，并在缺 summary、schema/boundary mismatch、raw artifact、unsafe field、success/control claim 时 fail closed。

### 改动文件和接口影响

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
  - 新增 execution callback intake schema/boundary 常量、default blocked summary、source contract、unsafe-field detector、`summarize_field_evidence_rerun_execution_callback_intake(...)`。
  - 在 `build_diagnostics_payload(...)` 中新增 `field_evidence_rerun_execution_callback_intake_ref`、env fallback、canonical summary、summary alias 和 `robot_diagnostics_field_evidence_rerun_execution_callback_intake_summary`。
  - 将同名 raw status keys 从 `latest_status` 剥离，避免下游暴露 raw callback material。
- `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
  - 新增 focused unittest，覆盖 canonical/nested summary、missing、unsupported、evidence_ref mismatch、unsafe fields、raw-only wrapper，以及 no Start/Confirm Dropoff/Cancel/ACK/cursor/Nav2/HIL action boundary。
- `docs/interfaces/ros_runtime_contracts.md`
  - 记录 Robot-visible allowlist、fail-closed 条件和 non-action boundary。

### 实现内容

- Alias 只保留 `safe_evidence_ref`、source execution pack status、callback packet status、same-ref status、accepted/missing/rejected/blocked material 分类、owner handoff、next required evidence 和 safe copy。
- Alias 递归阻断 raw artifacts、complete artifact bodies、ROS topic、`/cmd_vel`、serial/UART、WAVE ROVER、credential、local path、checksum、traceback、HIL/pass wording、ACK/cursor/control 和 delivery success wording。
- Alias 固定输出 `source=software_proof`、`not_proven`、`safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`、`metadata_only=true`。

### 测试、dry-run 或上车验证结果

```text
python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
# exit 0

PYTHONPATH=onboard/src/ros2_trashbot_behavior python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
Ran 241 tests in 0.815s
OK

rg -n "robot_diagnostics_field_evidence_rerun_execution_callback_intake_summary|field_evidence_rerun_execution_callback_intake|software_proof_docker_field_evidence_rerun_execution_callback_intake_gate|safe_to_control=false|delivery_success=false|primary_actions_enabled=false|not_proven" onboard/src/ros2_trashbot_behavior docs/interfaces/ros_runtime_contracts.md sprints/2026.05.21_01-02_field-evidence-rerun-execution-callback-intake
# exit 0; hits include Robot code, ROS runtime contract, and sprint docs.

git diff --check -- onboard/src/ros2_trashbot_behavior docs/interfaces/ros_runtime_contracts.md sprints/2026.05.21_01-02_field-evidence-rerun-execution-callback-intake
# exit 0
```

### 失败定位和修复

- First unittest run failed because the new diagnostics key still echoed raw `latest_status` input. Fixed by adding `field_evidence_rerun_execution_callback_intake*` keys to the existing safe status-stripping block before rebuilding the payload.

### 剩余风险和下一步能力建设建议

- 剩余风险：本 worker 只完成 Robot diagnostics safe alias；不触发 task_orchestrator、Start、Confirm Dropoff、Cancel、ACK、cursor、Nav2、HIL、dropoff/cancel completion、delivery result 或 primary actions。
- 剩余风险：验证范围是 local software proof；没有真实现场复跑、真实 Nav2/fixed-route runtime、电梯门/楼层、真实 phone/browser、WAVE ROVER/UART/HIL 或 delivery success。

## Worker 3 - User Touchpoint Full-Stack Engineer

### 用户触点目标和本轮抓手

- 目标 capability：mobile/web 只读消费 `field_evidence_rerun_execution_callback_intake`。
- 证据边界：`software_proof_docker_field_evidence_rerun_execution_callback_intake_gate`。
- 本轮抓手：新增“现场证据复跑执行回执入口”panel，面向现场 owner 和支持同学展示 execution callback intake 的 accepted/missing/rejected/blocked 材料状态，不开放任何主操作。

### 改动文件和接口影响

- `mobile/web/app.js`
  - 新增 callback-intake summary selection、fail-closed normalization、render hooks 和只读 panel。
  - 保持 Start Delivery、Confirm Dropoff、Cancel gating 不变。
- `mobile/web/fixtures/status.json`
  - 增加 safe fixture summary，覆盖 execution callback intake read-only 展示。
- `mobile/web/test_mobile_web_entrypoint.py`
  - 新增 focused fixture/render tests，覆盖 panel copy、boundary tokens 和 primary actions disabled。
- `docs/product/mobile_user_flow.md`
  - 记录“现场证据复跑执行回执入口”的用户可见状态、只读边界和 non-claim 口径。

### 实现内容

- Panel 优先消费 `robot_diagnostics_field_evidence_rerun_execution_callback_intake_summary`，只展示 safe `evidence_ref`、callback-intake status、accepted/missing/rejected/blocked material groups、owner handoff、next required evidence 和 fail-closed boundary。
- Panel 保留 `source=software_proof`、`not_proven`、`safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`。
- Panel 不 fetch raw artifact，不发送 Start Delivery、Confirm Dropoff、Cancel、ACK、cursor、diagnostics fetch、queue scheduling、execution scheduling、callback submission 或 robot command。

### 测试、dry-run 或上车验证结果

```text
node --check mobile/web/app.js
# exit 0

python3 -m unittest mobile/web/test_mobile_web_entrypoint.py
Ran 187 tests
OK

python3 -m json.tool mobile/web/fixtures/status.json >/dev/null
# exit 0
```

### 数据、样本或调试输出变化

- 新增 mobile/web safe fixture，不新增真实 phone/browser 材料、不访问真实设备、不提交现场 callback packet。
- “现场证据复跑执行回执入口”只说明 callback-intake software proof 状态；不证明真实手机通过、真实 PWA prompt/userChoice、真实 route/elevator field pass、HIL、真实投放、O5 external proof 或 delivery success。

### 剩余风险和下一步能力建设建议

- 剩余风险：本 worker 只完成 local static mobile/web read-only surface；没有真实 iPhone/Android device behavior、production app、真实 PWA prompt/userChoice 或现场手机验收。
- 下一步建议：进入 `field_evidence_rerun_execution_callback_review_decision` 前，需要现场 owner 提供同一 safe `evidence_ref` 的真实 execution callback packet，而不是把 fixture 当材料。

## Product Closeout

### 用户价值和产品北极星

产品北极星仍是普通手机用户把垃圾交给低成本 ROS2 小车后，小车能沿固定路线完成送达、电梯 assisted delivery、投放或人工取走，并且每一次结果都有可回放证据。本轮 closeout 的价值是把“现场复跑执行后的回执材料”变成可被 PC gate、Robot diagnostics 和 mobile/web 共同理解的只读分类入口，减少现场 owner 回填材料时的歧义。

### OKR 映射和 KR 更新

- Objective 5 仍约 68%：本轮没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover 或真实 phone/browser external proof。
- Objective 1 仍约 81%：本轮没有 WAVE ROVER/UART/HIL、真实 `feedback_T1001.log`、`/odom`、`/imu/data`、`/battery`、operator HIL report 或 PR #5 真实 2D LiDAR / ToF materials；PR #5 `PRRT_kwDOSWB9286CJ3tX` 仍 unresolved / material pending；PR #6 是 docs-only。
- Objectives 2/3/4 仍约 99%：本轮改进了 field evidence rerun execution callback intake 的软件证明和用户可见性，但仍不是真实现场材料、真实 route/elevator field pass、真实 phone/browser、HIL 或 delivery success。

### 本轮核心抓手和责任 Engineer

- Autonomy Algorithm Engineer：PC gate `field_evidence_rerun_execution_callback_intake`。
- Robot Platform Engineer：diagnostics safe alias `robot_diagnostics_field_evidence_rerun_execution_callback_intake_summary`。
- User Touchpoint Full-Stack Engineer：mobile/web 只读“现场证据复跑执行回执入口”panel。
- Product Manager / OKR Owner：更新 `OKR.md`、`docs/process/okr_progress_log.md`、`tech-done.md`、`side2side_check.md`、`final.md`，保守收口 OKR 和证据边界。

### Product closeout 验证结果

```text
test -f .../tech-done.md
test -f .../side2side_check.md
test -f .../final.md
# exit 0

rg -n "field_evidence_rerun_execution_callback_intake|software_proof_docker_field_evidence_rerun_execution_callback_intake_gate|safe_to_control=false|delivery_success=false|primary_actions_enabled=false|not_proven|Objective 5|Objective 1|PRRT_kwDOSWB9286CJ3tX|PR #6" OKR.md docs/process/okr_progress_log.md sprints/2026.05.21_01-02_field-evidence-rerun-execution-callback-intake
# exit 0

git diff --check -- OKR.md docs/process/okr_progress_log.md docs sprints/2026.05.21_01-02_field-evidence-rerun-execution-callback-intake
# exit 0
```

### 集成围栏复验结果

```text
python3 -m py_compile pc-tools/evidence/field_evidence_rerun_execution_callback_intake.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py mobile/web/test_mobile_web_entrypoint.py
# exit 0

python3 -m unittest tests.test_field_evidence_rerun_execution_callback_intake
Ran 6 tests
OK

PYTHONPATH=onboard/src/ros2_trashbot_behavior python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
Ran 241 tests
OK

node --check mobile/web/app.js
# exit 0

python3 -m unittest mobile/web/test_mobile_web_entrypoint.py
Ran 187 tests
OK

python3 -m json.tool mobile/web/fixtures/status.json >/dev/null
# exit 0

python3 pc-tools/evidence/field_evidence_rerun_execution_callback_intake.py --help
# exit 0

rg -n "robot_diagnostics_field_evidence_rerun_execution_callback_intake_summary|field_evidence_rerun_execution_callback_intake|software_proof_docker_field_evidence_rerun_execution_callback_intake_gate|safe_to_control=false|delivery_success=false|primary_actions_enabled=false|not_proven|现场证据复跑执行回执入口" pc-tools/evidence tests onboard/src/ros2_trashbot_behavior mobile/web docs/interfaces docs/product/mobile_user_flow.md sprints/2026.05.21_01-02_field-evidence-rerun-execution-callback-intake
# exit 0
```

### 剩余风险

- 本轮仍没有真实 field rerun、真实 Nav2/fixed-route runtime、真实 route completion signal、真实现场 task record、真实电梯门/楼层/人工协助、真实 dropoff/cancel completion、真实 delivery result、真实 phone/browser、WAVE ROVER/UART/HIL 或 O5 external proof。
- `accepted` 只表示 callback packet 的材料分类可进入后续 review，不表示材料真实、现场通过或交付成功。
