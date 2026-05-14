# Sprint 2026.05.14_23-24 PC Route Debug Console - Tech Done

sprint_type: epic

## 用户价值

本轮把固定路线排障从 raw JSON、onboard 调试入口和零散复盘材料，推进到 PC 工作站可独立打开的只读 route debug console。现场操作员和开发者可以在一个页面/API 中查看当前位置、当前 checkpoint、目标点、匹配状态、失败原因、关键帧预检和最近任务状态；手机端只展示 PC console 可用性摘要，避免普通用户误以为手机获得了新的控制授权。

## OKR 映射

- Objective 3：主目标，补齐 KR5 的 PC 关键帧调试页面软件证据。
- Objective 2：支撑目标，把 recent task / task_record 摘要、失败原因和 `delivery_success=false` 接入路线调试复盘。
- Objective 5：不提升，本轮没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue 或 worker/migration 证据。
- Objective 1：不提升，本轮没有真实 WAVE ROVER、串口、UART、Nav2 实跑或 HIL。

## KR 拆解

- Objective 3 KR5：PC 页面/API 展示 `route_progress`、`keyframe_preflight`、`current_position`、`current_checkpoint`、`target`、`match_status`、`failure` 和 `recent_task`。
- Objective 2 KR5：recent task 状态、失败原因、`not_proven` 和 evidence boundary 进入 PC console、diagnostics 与 mobile 只读摘要。
- Objective 4 KR4：手机端可展示支持诊断摘要，但本轮不调整 Objective 4 进度，因为它不是新的手机主路径能力。

## 本轮核心抓手

`software_proof_docker_pc_route_debug_console_gate`。本轮证据只覆盖 Docker/local software proof：PC console schema、HTML/API、diagnostics metadata-only summary 和 mobile read-only availability；不证明真实 Nav2/fixed-route、真实路线采集、HIL、delivery success 或 Objective 5 外部证明。

## 责任 Engineer 与实际改动

### Task A - autonomy-engineer

实际改动：

- `pc-tools/route/route_debug_web.py`
- `pc-tools/route/test_route_debug_web.py`
- `pc-tools/route/README.md`
- `pc-tools/README.md`
- `docs/navigation/fixed_route_workflow.md`

交付内容：新增 PC route debug console，输出 `schema=trashbot.pc_route_debug_console.v1`、`evidence_boundary=software_proof_docker_pc_route_debug_console_gate`、`route_progress`、`keyframe_preflight`、`current_position`、`current_checkpoint`、`target`、`match_status`、`failure`、`recent_task`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`、`console_controls=read_only`。

验证结果：

- `PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile pc-tools/route/route_debug_web.py`：pass
- `PYTHONDONTWRITEBYTECODE=1 python3 pc-tools/route/test_route_debug_web.py`：`Ran 5 tests OK`
- `python3 pc-tools/route/route_debug_web.py --help`：pass
- `python3 pc-tools/route/route_debug_web.py --status-json <tmp> --task-record <tmp> --once-json`：pass
- required `rg`：pass
- scoped `git diff --check`：pass

### Task B - robot-software-engineer

实际改动：

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
- `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
- `docs/interfaces/ros_contracts.md`

交付内容：diagnostics 支持 `pc_route_debug_console_ref` 与 `TRASHBOT_PC_ROUTE_DEBUG_CONSOLE`。valid source 必须同时满足 `schema=trashbot.pc_route_debug_console.v1` 与 `evidence_boundary=software_proof_docker_pc_route_debug_console_gate`；missing、read_error、unsupported、blocked、unsafe copy 都保守降级，并保持控制边界 false。

验证结果：

- `PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile .../operator_gateway_diagnostics.py`：pass
- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard.src.ros2_trashbot_behavior.test.test_operator_gateway_diagnostics`：`Ran 53 tests OK`
- required `rg`：pass
- scoped `git diff --check`：pass

### Task C - full-stack-software-engineer

实际改动：

- `mobile/web/index.html`
- `mobile/web/app.js`
- `mobile/web/styles.css`
- `mobile/fixtures/mobile_web_status.fixture.json`
- `onboard/src/ros2_trashbot_behavior/test/test_mobile_web_entrypoint.py`
- `docs/product/mobile_user_flow.md`

交付内容：新增只读 PC route debug availability 面板；手机端不读取 PC 文件或 raw artifact，不改变 Start/Confirm/Cancel gating。

验证结果：

- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard.src.ros2_trashbot_behavior.test.test_mobile_web_entrypoint`：`Ran 4 tests OK`
- `python3 -m py_compile onboard/src/ros2_trashbot_behavior/test/test_mobile_web_entrypoint.py`：pass
- `node --check mobile/web/app.js`：pass
- required `rg`：pass
- scoped `git diff --check`：pass

## 验收口径

- PC console、diagnostics 和 mobile availability 都必须保留 `not_proven`。
- `delivery_success=false` 不能被写成真实 delivery success。
- `primary_actions_enabled=false`、`console_controls=read_only` 和 mobile Start/Confirm/Cancel gating 不得被 PC debug 材料改变。
- 本机只有 Docker/local software proof，不能写成真实 Nav2/fixed-route、真实路线采集、HIL、真实公网、4G、OSS/CDN 或 production DB/queue。

## 偏差

无产品范围偏差。Task A/B/C 均按 `tech-plan.md` 的 owner 和文件边界交付；本轮没有修改工程代码以外的未授权文件。

## 剩余风险

- 仍缺真实 Nav2/fixed-route 实跑、真实路线采集、关键帧实景证据和同一 `evidence_ref` 上车复账。
- 仍缺 WAVE ROVER、真实串口/UART、HIL、真实底盘运动、dropoff/cancel completion 和 delivery success。
- 仍缺 Objective 5 的真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker/migration。
- 手机端只是只读展示 PC console 可用性，不替代 PC console，也不构成真实手机设备/browser 验收。

## Sprint 文档

- 已完成：`pre_start.md`、`prd.md`、`tech-plan.md`、`tech-done.md`。
- Product closeout 需要继续完成：`side2side_check.md`、`final.md`、`OKR.md`、`docs/process/okr_progress_log.md`。
