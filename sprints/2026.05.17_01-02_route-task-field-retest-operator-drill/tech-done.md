# Sprint 2026.05.17_01-02 Route Task Field Retest Operator Drill - Tech Done

sprint_type: epic

## 1. 用户价值和产品北极星

本轮把上一轮“现场材料包已可校验”的状态，推进成现场人员可照着执行的 operator drill。产品北极星仍是普通手机用户把垃圾交给小车后，机器人能沿固定路线和电梯 assisted delivery 流程可验证地完成送达；本轮不宣称真实送达，而是把真实材料回填前的操作顺序、命令、缺口和回调清单固化，减少现场执行断裂。

## 2. OKR 映射与 KR 拆解

- Objective 2：把 PR #4 的 elevator-assisted delivery 证据链继续落到 operator drill，要求同一 `evidence_ref` 下串联 material pack、result intake、result reconciliation，并把门状态、目标楼层、人工协助、dropoff/cancel completion 和 delivery result 的缺口写成现场动作。
- Objective 3：把 fixed-route/Nav2 现场复测材料从“目录打包”推进到“下一步命令和输出文件清单”，降低真实 route runtime log、route completion signal、task record 回填时的操作风险。
- Objective 4：手机端只读解释“现场操作演练”，让现场支持能看懂下一条命令、缺失材料和 proof boundary；Start Delivery、Confirm Dropoff、Cancel 授权不变。
- Objective 5：保持约 66%。当前仍无真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker/migration；Docker-only operator drill 不能替代 O5 external proof。

## 3. 本轮核心抓手

核心抓手是 `software_proof_docker_route_task_field_retest_operator_drill_gate`：在 Docker/local software proof 边界内，生成 PC artifact / summary、Robot diagnostics metadata-only summary、mobile/web 只读 panel，统一保持 `not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。

## 4. 实际改动

Task A Autonomy changed:

- `pc-tools/evidence/route_task_field_retest_operator_drill.py`
- `pc-tools/evidence/test_route_task_field_retest_operator_drill.py`
- `pc-tools/README.md`
- `docs/navigation/fixed_route_workflow.md`

交付内容：新增 CLI `--material-pack-json`、`--evidence-ref`、`--output`、`--summary-output`、`--once-json`，支持 material pack artifact、summary、wrapper、nested JSON，输出 `trashbot.route_task_field_retest_operator_drill.v1` 与 summary。输出包含 material pack command、result intake command、result reconciliation command、required outputs、missing prompts、operator callback checklist、rerun notes 和 safe copy。

Task B Robot changed:

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
- `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
- `docs/interfaces/ros_contracts.md`

交付内容：新增 `route_task_field_retest_operator_drill` / `_summary` metadata-only diagnostics consumer，支持 env/ref loading、fail-closed schema/boundary/evidence/action/success checks、diagnostics payload aliases；不改变 collect、dropoff、cancel、ACK、Nav2、HIL 或 delivery success。

Task C Full-stack changed:

- `mobile/web/app.js`
- `mobile/web/styles.css`
- `mobile/web/test_mobile_web_entrypoint.py`
- `mobile/web/fixtures/status.json`
- `docs/product/mobile_user_flow.md`

交付内容：新增只读“现场操作演练” panel，消费 operator drill、summary、Robot diagnostics compatible summary，展示 drill status、safe evidence ref、next command labels、missing material prompts、callback checklist、boundary、`not_proven`；Start Delivery、Confirm Dropoff、Cancel gating 未改变。

Task D Product changed:

- `sprints/2026.05.17_01-02_route-task-field-retest-operator-drill/tech-done.md`
- `sprints/2026.05.17_01-02_route-task-field-retest-operator-drill/side2side_check.md`
- `sprints/2026.05.17_01-02_route-task-field-retest-operator-drill/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`

## 5. 验证结果

Task A Autonomy:

```text
py_compile exit 0
unittest: Ran 5 tests in 0.018s OK
CLI --help OK
required rg OK
scoped git diff --check exit 0
```

Task B Robot:

```text
py_compile PASS
diagnostics unittest: Ran 122 tests in 0.156s OK
required rg OK
scoped git diff --check PASS
```

Task C Full-stack:

```text
mobile unittest: Ran 24 tests ... OK
node --check mobile/web/app.js pass
required rg OK
scoped git diff --check PASS
```

Task D Product closeout:

```text
required rg PASS: matched route_task_field_retest_operator_drill, boundary, Objective 2/3/5, Docker-only, PR #4/#5 and fail-closed flags across sprint docs, OKR.md and docs/process/okr_progress_log.md
scoped git diff --check PASS
```

## 6. 失败定位

无 A/B/C worker 失败。Product closeout 未发现允许范围外改动要求；A/B/C 工程文件按用户要求未由 Product 修改。

## 7. 剩余风险和证据缺口

- 本轮仍是 Docker-only software proof，不是真实 route/elevator field pass。
- 仍缺真实 Nav2/fixed-route runtime log、真实 route completion signal、真实 task record、真实电梯门状态、真实目标楼层确认、真实人工协助记录、真实 dropoff/cancel completion、真实 delivery result 和同一 `evidence_ref` 的上车实机复账。
- 仍缺真实手机/browser、production app、真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker/migration、WAVE ROVER、真实串口/UART、HIL、2D LiDAR / ToF SKU/source/receipt/procurement/installation/wiring/power/calibration/HIL-entry 材料。
- 本轮不提升 Objective 5；继续本地 O5 wrapper 会重复消费 Docker-only blocker，下一步应优先等待真实外部 O5 材料或继续 O2/O3 现场材料实证链路。
