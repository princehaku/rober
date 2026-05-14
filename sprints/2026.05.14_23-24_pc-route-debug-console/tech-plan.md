# Sprint 2026.05.14_23-24 PC Route Debug Console - Tech Plan

sprint_type: epic

## 目标

实现 `software_proof_docker_pc_route_debug_console_gate`：把 PC 端 route debug console 从 onboard 调试入口推进到 `pc-tools/route/` 的可独立运行开发者/操作员工具，并把可用性摘要安全接入 diagnostics 与 mobile/web。

本轮只做 Docker/local software proof；不读取硬件、serial/UART、WAVE ROVER、Nav2 runtime 或 ROS graph，不声明 HIL、真实 fixed-route、dropoff/cancel completion 或 delivery success。

## OKR 最低优先级核对

1. 当前 `OKR.md` 4.1 完成度最低的 Objective 是 Objective 5，约 68%。Objective 1 约 75%，Objective 2 与 Objective 3 均约 81%。
2. 本 sprint 不针对 Objective 5。理由：`OKR.md` 6 明确只有拿到真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity 或 production worker/migration 证据时，才继续推进 O5 completion；本机只有 Docker，没有真实外部材料。
3. 本 sprint 不针对 Objective 1。理由：本机无真实硬件、串口、WAVE ROVER 或 HIL，不能推进真实硬件完成度。
4. 本 sprint 选择 Objective 3 / Objective 2。证据理由：最新 closed sprint `sprints/2026.05.14_22-03_route-task-rehearsal-operator-review/final.md` 明确外部 O5 不可用时，下一轮 O2/O3 应从 operator review 走向真实路线/任务材料或同一 `evidence_ref` 上车复账；`pc-tools/README.md` 明确 `pc-tools/route/` 仍未落地，`route_debug_web.py` 和 `route_csv_to_yaml.py` 仍在 onboard；`OKR.md` Objective 3 KR5 要求 PC 关键帧调试页面展示当前位置、目标点、匹配状态、失败原因和最近一次任务状态。

## 架构边界

- Task A 产出 PC-local `pc-tools/route/` 工具，读取 JSON 文件，提供只读 HTML 与 JSON API。
- Task B 只在 diagnostics 中暴露 metadata-only `pc_route_debug_console` 或 route_debug summary，不触发控制动作。
- Task C 只在 mobile/web 只读展示 availability/summary，不新增控制授权。
- 三个任务文件范围互不重叠，允许主会话并行派发 3 个 worker。
- 技术注释必须使用中文，新增/改动代码注释比例必须超过 20%，注释解释为什么这样做。

## Task A - Autonomy：PC route debug console/JSON API

责任 Engineer：`autonomy-engineer`

### 文件范围

- `pc-tools/route/route_debug_web.py`
- `pc-tools/route/README.md`
- 必要时创建 `pc-tools/route/__init__.py`
- 必要时创建 `pc-tools/route/test_route_debug_web.py`
- `pc-tools/README.md`
- `docs/navigation/fixed_route_workflow.md`

不得修改 Task B / Task C 文件范围。

### 实现要求

- 建立可独立运行的 PC route debug console；优先标准库或仓库已有轻量模式，不强依赖 ROS2，不 import `ros2_trashbot_*`。
- 输入：fixed_route debug status JSON、可选 task/task_record JSON 或 task_record dir、可选 output/status path。
- JSON API 至少输出：`schema=trashbot.pc_route_debug_console.v1`、`evidence_boundary=software_proof_docker_pc_route_debug_console_gate`、`route_progress`、`keyframe_preflight`、当前位置/当前 checkpoint、目标点、匹配状态、失败原因、recent task/task_record summary、`not_proven`、`delivery_success=false`。
- HTML 页面只读展示同一摘要，异常输入显示 blocked/not_proven，不显示凭证、本机完整路径、serial/UART、baudrate、WAVE ROVER 参数、ROS topic、`/cmd_vel`、traceback 或 checksum。
- 文档说明该工具运行在 PC 工作站，不上车、不进云、不读取硬件或 Nav2 runtime。

### 验收命令

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile pc-tools/route/route_debug_web.py
PYTHONDONTWRITEBYTECODE=1 python3 pc-tools/route/test_route_debug_web.py
python3 pc-tools/route/route_debug_web.py --help
python3 pc-tools/route/route_debug_web.py --status-json <临时 fixed_route_status.json> --task-record <临时 task_record.json> --once-json
rg -n "pc_route_debug_console|software_proof_docker_pc_route_debug_console_gate|route_progress|keyframe_preflight|not_proven|delivery_success=false" pc-tools/route pc-tools/README.md docs/navigation/fixed_route_workflow.md
git diff --check -- pc-tools/route/route_debug_web.py pc-tools/route/README.md pc-tools/route/__init__.py pc-tools/route/test_route_debug_web.py pc-tools/README.md docs/navigation/fixed_route_workflow.md
```

如果未创建某个可选文件，worker 需从对应 `git diff --check` 参数中移除该路径并说明原因。

## Task B - Robot：diagnostics metadata-only summary

责任 Engineer：`robot-software-engineer`

### 文件范围

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
- `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
- `docs/interfaces/ros_contracts.md`

不得修改 Task A / Task C 文件范围。

### 实现要求

- 在 diagnostics 中暴露 `pc_route_debug_console` 或 route_debug summary，支持 explicit ref 或环境变量配置，字段只允许 phone/support-safe 摘要。
- Summary 必须包含 schema/boundary、availability、route_debug status、recent task summary、`not_proven` 和固定控制边界。
- metadata-only：不得触发 `/api/collect`、dropoff、cancel、ACK POST、cursor/persistence、terminal ACK、Nav2、WAVE ROVER、HIL 或 delivery success。
- 异常输入、缺文件、unsupported schema、unsafe copy 时保守降级为 blocked/not_proven。
- 更新 ROS/API contract 文档，写清该字段不是 command/status/ACK，不代表真实 fixed-route 或 HIL。

### 验收命令

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard.src.ros2_trashbot_behavior.test.test_operator_gateway_diagnostics
rg -n "pc_route_debug_console|software_proof_docker_pc_route_debug_console_gate|metadata-only|not_proven|delivery success|HIL" onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py docs/interfaces/ros_contracts.md
git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py docs/interfaces/ros_contracts.md
```

## Task C - Full-stack：mobile/web read-only availability summary

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

- 在 `mobile/web` 只读展示 PC route debug console availability/summary，让支持人员知道 PC 工具是否有 route/task debug 材料。
- 不新增控制授权，不把 PC 工具变成手机主流程，不改变 Start/Confirm/Cancel 的 fail-closed gating。
- Copy 必须包含 `not_proven` 或等价边界，避免 “delivery success” 误读。
- fixture 增加安全摘要样例；测试覆盖 summary 可见、缺失时保守降级、控制按钮逻辑不变。
- 更新产品用户流程文档，说明手机只是展示 PC debug availability，不替代 PC console 或真实路线验收。

### 验收命令

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard.src.ros2_trashbot_behavior.test.test_mobile_web_entrypoint
python3 -m py_compile onboard/src/ros2_trashbot_behavior/test/test_mobile_web_entrypoint.py
node --check mobile/web/app.js
rg -n "pc_route_debug_console|software_proof_docker_pc_route_debug_console_gate|not_proven|delivery success|HIL|Start|Confirm|Cancel" mobile/web mobile/fixtures/mobile_web_status.fixture.json onboard/src/ros2_trashbot_behavior/test/test_mobile_web_entrypoint.py docs/product/mobile_user_flow.md
git diff --check -- mobile/web/index.html mobile/web/app.js mobile/web/styles.css mobile/fixtures/mobile_web_status.fixture.json onboard/src/ros2_trashbot_behavior/test/test_mobile_web_entrypoint.py docs/product/mobile_user_flow.md
```

## 集成验收

三个 worker 返回后，主会话只做集成验收和 sprint 留档：

```bash
rg -n "pc_route_debug_console|software_proof_docker_pc_route_debug_console_gate|Objective 3|Objective 2|not_proven|delivery success|HIL" pc-tools docs/navigation docs/interfaces docs/product mobile/web mobile/fixtures onboard/src/ros2_trashbot_behavior sprints/2026.05.14_23-24_pc-route-debug-console
git diff --check -- pc-tools/route/route_debug_web.py pc-tools/route/README.md pc-tools/route/test_route_debug_web.py pc-tools/README.md docs/navigation/fixed_route_workflow.md onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py docs/interfaces/ros_contracts.md mobile/web/index.html mobile/web/app.js mobile/web/styles.css mobile/fixtures/mobile_web_status.fixture.json onboard/src/ros2_trashbot_behavior/test/test_mobile_web_entrypoint.py docs/product/mobile_user_flow.md sprints/2026.05.14_23-24_pc-route-debug-console/tech-done.md
```

如果某个可选文件未创建，集成验收需要移除对应 `git diff --check` 路径并在 `tech-done.md` 说明。

## 风险和证据边界

- 本轮证明 PC route debug console schema、HTML/API、diagnostics summary 和 mobile 只读展示可以在 Docker/local 软件环境中被验证。
- 本轮不证明真实 Nav2/fixed-route、真实路线采集、WAVE ROVER、真实串口/UART、HIL、同一 `evidence_ref` 上车复账、dropoff/cancel completion 或 delivery success。
- 本轮不证明 Objective 5 的真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity 或 production worker/migration。

## 后续 sprint 文档要求

- 工程完成后更新 `tech-done.md`：记录三路 worker 实际改动、验证结果、偏差和剩余风险。
- Product 验收后更新 `side2side_check.md` 与 `final.md`。
- 最终由 Product Owner 根据真实工程证据更新 `OKR.md` 与必要的 `docs/process/okr_progress_log.md`。
