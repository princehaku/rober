# Sprint 2026.05.15_00-01 Route Task Field Run Readiness - Tech Plan

sprint_type: epic

## 目标

实现 `software_proof_docker_route_task_field_run_readiness_gate`：把 PC route debug console summary、route_task operator review、execution bundle 和兼容 diagnostics summary 汇总为下一次真实路线-任务联跑前的可执行 readiness handoff。

本轮只做 Docker/local software proof；不得宣称真实路线、真实 Nav2/fixed-route、真实 WAVE ROVER/串口、HIL、dropoff/cancel completion、delivery success 或 Objective 5 external proof。

## OKR 最低优先级核对

- 当前 `OKR.md` 4.1 节完成度最低的 Objective：Objective 5，约 68%。
- 本 sprint 是否针对该 Objective：否。
- 不针对理由：Objective 5 继续推进 completion 需要真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity 或 production worker/migration。当前本机是 Docker-only，缺这些外部材料；继续叠加本地 metadata 不能上调 O5。
- 其他低位 Objective：Objective 1 约 75%，但缺真实 WAVE ROVER、串口/UART、`T=1001` feedback、HIL 或底盘实机样本，本轮不能推进硬件完成度。
- 本 sprint 选择 Objective 2 / Objective 3。理由：最新 `sprints/2026.05.14_23-24_pc-route-debug-console/final.md` 建议无 O5 外部材料时转向 O2/O3，把 PC console software proof 连接到真实路线/任务证据；本轮通过 `route_task_field_run_readiness` 把下一次真实联跑前的同一 `evidence_ref` 要求、缺失材料、命令和 not_proven 边界变成可执行 handoff。
- final.md 收口时需复核：O5 外部材料是否仍缺失；本轮是否只保守更新 Objective 2/3；Objective 5 是否保持不提升。

## 架构边界

- Task A 产出 PC-local readiness artifact / CLI，读取已有 route debug / operator review / execution bundle 类 JSON 材料，输出安全 summary。
- Task B 在 diagnostics 里 metadata-only 消费 readiness artifact，不触发控制动作。
- Task C 在 `mobile/web` 只读展示 readiness availability / next evidence，不读取 raw artifact，不改变 Start/Confirm/Cancel gating。
- Task D 在工程完成后做 Product closeout，更新 sprint 收口、OKR 和 progress log；不得把计划文档当作业务结果。
- 三个工程任务文件范围互不重叠，后续实现必须并行派发 `autonomy-engineer`、`robot-software-engineer`、`full-stack-software-engineer` 3 个 worker；Product closeout 待工程返回后执行。
- 技术注释必须使用中文，新增/改动代码注释比例必须超过 20%，注释解释为什么这样做。

## Task A - Autonomy：route-task field-run readiness artifact

责任 Engineer：`autonomy-engineer`

### 文件范围

- `pc-tools/evidence/route_task_field_run_readiness.py`
- `pc-tools/evidence/README.md`
- `pc-tools/README.md`
- `docs/navigation/fixed_route_workflow.md`
- 必要时新增 `pc-tools/evidence/test_route_task_field_run_readiness.py`

不得修改 Task B / Task C 文件范围。

### 实现要求

- 新增或更新 dependency-light CLI，不强依赖 ROS2，不 import `ros2_trashbot_*`。
- 支持输入：
  - PC route debug console summary：`trashbot.pc_route_debug_console.v1` 或兼容字段。
  - route_task operator review：`trashbot.route_task_rehearsal_operator_review.v1` 或兼容字段。
  - execution bundle / manifest：`trashbot.route_task_rehearsal_execution_bundle.v1` 或兼容字段。
  - 可选显式 `--evidence-ref`，用于强制下一次真实联跑同一 `evidence_ref`。
- 输出 JSON：
  - `schema=trashbot.route_task_field_run_readiness.v1`
  - `schema_version=1`
  - `evidence_boundary=software_proof_docker_route_task_field_run_readiness_gate`
  - `overall_status`：`ready_for_field_run_materials` / `blocked_missing_material` / `blocked_unsupported_schema`
  - `evidence_ref` 和 `same_evidence_ref_required=true`
  - `source_materials`：只列 schema、status、safe ref，不列完整本机路径、checksum 或 raw payload。
  - `required_field_run_materials`：至少包含 route status、task record、PC route debug summary、operator review、execution bundle、Nav2/fixed-route runtime log、robot-side task evidence、support-safe mobile summary。
  - `missing_materials` 和 `commands_to_run`：给下一次真实路线-任务联跑前可执行命令。
  - `phone_support_safe_summary`：允许 diagnostics/mobile 消费的 whitelist-only 摘要。
  - `not_proven`：必须包含真实 Nav2/fixed-route、真实路线采集、WAVE ROVER、真实串口/UART、HIL、dropoff/cancel completion、delivery success、Objective 5 external proof。
  - `delivery_success=false`
  - `primary_actions_enabled=false`
- 安全边界：
  - 不输出 token、Authorization、OSS AK/SK、DB/queue URL、credential-bearing URL、ROS topic、`/cmd_vel`、serial/UART、baudrate、WAVE ROVER 参数、本机完整路径、traceback、checksum、complete artifacts 或 raw robot responses。
  - 异常输入、缺文件、unsupported schema 或 unsafe copy 时保守输出 blocked/not_proven。
- 文档更新：
  - README 写明它是下一次 field run readiness handoff，不是 HIL、真实路线、delivery success 或 O5 proof。
  - `docs/navigation/fixed_route_workflow.md` 写清同一 `evidence_ref` field-run material chain。

### 验收命令

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile pc-tools/evidence/route_task_field_run_readiness.py
PYTHONDONTWRITEBYTECODE=1 python3 pc-tools/evidence/test_route_task_field_run_readiness.py
python3 pc-tools/evidence/route_task_field_run_readiness.py --help
python3 pc-tools/evidence/route_task_field_run_readiness.py --pc-route-debug <临时 pc_route_debug_console.json> --operator-review <临时 operator_review.json> --execution-bundle <临时 execution_bundle.json> --evidence-ref <临时 evidence_ref> --once-json
rg -n "route_task_field_run_readiness|software_proof_docker_route_task_field_run_readiness_gate|same_evidence_ref|required_field_run_materials|not_proven|delivery_success=false|HIL|Docker" pc-tools/evidence pc-tools/README.md docs/navigation/fixed_route_workflow.md
git diff --check -- pc-tools/evidence/route_task_field_run_readiness.py pc-tools/evidence/test_route_task_field_run_readiness.py pc-tools/evidence/README.md pc-tools/README.md docs/navigation/fixed_route_workflow.md
```

如果未创建可选 test 或 README 文件，worker 必须从对应 `git diff --check` 参数中移除该路径并说明原因。

## Task B - Robot：diagnostics metadata-only readiness consumption

责任 Engineer：`robot-software-engineer`

### 文件范围

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
- `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
- `docs/interfaces/ros_contracts.md`

不得修改 Task A / Task C 文件范围。

### 实现要求

- 在 diagnostics 中消费 `route_task_field_run_readiness` artifact 或 explicit ref / 环境变量。
- 只接受 `schema=trashbot.route_task_field_run_readiness.v1` 和 `evidence_boundary=software_proof_docker_route_task_field_run_readiness_gate`。
- 输出 `route_task_field_run_readiness` / `route_task_field_run_readiness_summary` phone/support-safe metadata：
  - availability / overall_status
  - evidence_ref
  - same evidence ref required
  - next evidence / missing material summary
  - commands summary
  - `not_proven`
  - `delivery_success=false`
  - `primary_actions_enabled=false`
- metadata-only 要求：
  - 不触发 `/api/collect`、dropoff、cancel、ACK POST、cursor/persistence、terminal ACK、Nav2、WAVE ROVER、HIL 或 delivery success。
  - 不把 readiness summary 写成 command/status/ACK robot contract。
  - 缺文件、read error、unsupported schema、boundary mismatch 或 unsafe fields 时保守降级为 blocked/not_proven。
- 更新 `docs/interfaces/ros_contracts.md`，写清该字段只是 readiness/support metadata，不代表真实 fixed-route、HIL、delivery success 或 O5 external proof。

### 验收命令

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard.src.ros2_trashbot_behavior.test.test_operator_gateway_diagnostics
rg -n "route_task_field_run_readiness|software_proof_docker_route_task_field_run_readiness_gate|metadata-only|not_proven|delivery success|HIL|Docker" onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py docs/interfaces/ros_contracts.md
git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py docs/interfaces/ros_contracts.md
```

## Task C - Full-stack：mobile/web read-only readiness panel

责任 Engineer：`full-stack-software-engineer`

### 文件范围

- `mobile/web/index.html`
- `mobile/web/app.js`
- `mobile/web/styles.css`
- `mobile/fixtures/mobile_web_status.fixture.json`
- `onboard/src/ros2_trashbot_behavior/test/test_mobile_web_entrypoint.py`
- `docs/product/mobile_user_flow.md`

不得修改 Task A / Task B 文件范围。

### 实现要求

- 在 `mobile/web` 增加只读 “route-task field-run readiness availability / next evidence” 面板。
- 输入优先级：
  - `route_task_field_run_readiness`
  - `route_task_field_run_readiness_summary`
  - 兼容嵌套在 `phone_readiness` 或 `/api/diagnostics` 的 safe summary。
- 面板展示：
  - readiness availability / overall_status
  - evidence_ref
  - same evidence ref required
  - next evidence / missing material summary
  - commands summary 的 phone-safe 文案
  - `not_proven`
  - `evidence_boundary=software_proof_docker_route_task_field_run_readiness_gate`
- 严禁：
  - 手机端读取 raw artifact、local filesystem path、complete execution bundle、checksum、traceback、raw robot responses。
  - 展示 token、Authorization、OSS AK/SK、DB/queue URL、ROS topic、`/cmd_vel`、serial/UART、baudrate、WAVE ROVER 参数。
  - 改变 Start Delivery、Confirm Dropoff、Cancel gating；缺 summary 时显示 blocked/not_proven，不放行控制。
- 测试覆盖：
  - summary 可见。
  - 缺失时 blocked/not_proven。
  - unsafe/raw 字段被过滤或不渲染。
  - Start/Confirm/Cancel 原 gating 不变。
- 更新 `docs/product/mobile_user_flow.md`，写明该面板只是下一次 field run readiness availability，不是 HIL、真实路线、delivery success 或 O5 external proof。

### 验收命令

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard.src.ros2_trashbot_behavior.test.test_mobile_web_entrypoint
python3 -m py_compile onboard/src/ros2_trashbot_behavior/test/test_mobile_web_entrypoint.py
node --check mobile/web/app.js
rg -n "route_task_field_run_readiness|software_proof_docker_route_task_field_run_readiness_gate|not_proven|delivery success|HIL|Start|Confirm|Cancel|Docker" mobile/web mobile/fixtures/mobile_web_status.fixture.json onboard/src/ros2_trashbot_behavior/test/test_mobile_web_entrypoint.py docs/product/mobile_user_flow.md
git diff --check -- mobile/web/index.html mobile/web/app.js mobile/web/styles.css mobile/fixtures/mobile_web_status.fixture.json onboard/src/ros2_trashbot_behavior/test/test_mobile_web_entrypoint.py docs/product/mobile_user_flow.md
```

## Task D - Product：收口 OKR/progress/sprint docs

责任 Owner：`product-okr-owner`

### 文件范围

- `sprints/2026.05.15_00-01_route-task-field-run-readiness/tech-done.md`
- `sprints/2026.05.15_00-01_route-task-field-run-readiness/side2side_check.md`
- `sprints/2026.05.15_00-01_route-task-field-run-readiness/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`

### 收口要求

- 只在 Task A/B/C 工程 worker 返回并通过验收后执行。
- 汇总实际改动、验证结果、失败定位和剩余风险。
- `OKR.md` 只允许基于真实工程证据保守更新 Objective 2 / Objective 3。
- Objective 5 不提升，除非本轮另外取得真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity 或 production worker/migration；当前计划默认没有。
- Objective 1 不提升，除非取得真实 WAVE ROVER、串口/UART、HIL 或真实底盘 feedback；当前计划默认没有。
- `final.md` 必须明确本轮不证明真实路线、HIL、delivery success、dropoff/cancel completion 或 O5 external proof。

### 验收命令

```bash
rg -n "2026.05.15_00-01_route-task-field-run-readiness|software_proof_docker_route_task_field_run_readiness_gate|Objective 2|Objective 3|Objective 5|not_proven|delivery success|HIL|Docker" OKR.md docs/process/okr_progress_log.md sprints/2026.05.15_00-01_route-task-field-run-readiness
git diff --check -- OKR.md docs/process/okr_progress_log.md sprints/2026.05.15_00-01_route-task-field-run-readiness/tech-done.md sprints/2026.05.15_00-01_route-task-field-run-readiness/side2side_check.md sprints/2026.05.15_00-01_route-task-field-run-readiness/final.md
```

## 集成验收

三个工程 worker 返回后，主会话只做集成验收和 sprint 留档：

```bash
rg -n "route_task_field_run_readiness|software_proof_docker_route_task_field_run_readiness_gate|Objective 2|Objective 3|Objective 5|not_proven|delivery success|HIL|Docker" pc-tools docs/navigation docs/interfaces docs/product mobile/web mobile/fixtures onboard/src/ros2_trashbot_behavior sprints/2026.05.15_00-01_route-task-field-run-readiness
git diff --check -- pc-tools/evidence/route_task_field_run_readiness.py pc-tools/evidence/test_route_task_field_run_readiness.py pc-tools/evidence/README.md pc-tools/README.md docs/navigation/fixed_route_workflow.md onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py docs/interfaces/ros_contracts.md mobile/web/index.html mobile/web/app.js mobile/web/styles.css mobile/fixtures/mobile_web_status.fixture.json onboard/src/ros2_trashbot_behavior/test/test_mobile_web_entrypoint.py docs/product/mobile_user_flow.md sprints/2026.05.15_00-01_route-task-field-run-readiness/tech-done.md
```

如果某个可选文件未创建，集成验收需要移除对应 `git diff --check` 路径并在 `tech-done.md` 说明。

## 子 agent 派发要求

后续实现必须在同一轮并行派发 3 个 engineer worker：

- `autonomy-engineer` 执行 Task A。
- `robot-software-engineer` 执行 Task B。
- `full-stack-software-engineer` 执行 Task C。

每个 worker prompt 必须包含对应角色 System Prompt、本轮任务、文件范围、验收命令和输出要求。Product closeout 不得抢 Engineer 的实现、测试或修复工作。

## 风险和证据边界

- 本轮证明 readiness artifact、diagnostics summary 和 mobile read-only panel 可以在 Docker/local 软件环境中形成下一次 field run handoff。
- 本轮不证明真实 Nav2/fixed-route、真实路线采集、WAVE ROVER、真实串口/UART、HIL、同一 `evidence_ref` 上车复账、dropoff/cancel completion 或 delivery success。
- 本轮不证明 Objective 5 的真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity 或 production worker/migration。
- 如果工程 worker 只产出文档或 summary，而没有可运行 artifact / diagnostics / mobile tests，本轮不能作为 O2/O3 completion 提升依据。
