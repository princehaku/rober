# Sprint 2026.05.15_05-06 Route Task Completion Signal - Tech Done

sprint_type: epic

## 1. 实际改动

本 sprint 完成 `software_proof_docker_route_task_completion_signal_gate`，把上一轮 route/task reconciliation verdict 推进到 Docker/local completion signal 软件证据。三条 worker 线均已完成工程文件、测试围栏和对应 `docs/` 同步；Product closeout 仅更新 sprint 收口、OKR 和进度日志，不修改 worker 实现文件。

### Task A - Autonomy

- 新增 `pc-tools/evidence/route_task_completion_signal.py`。
- 新增 `pc-tools/evidence/test_route_task_completion_signal.py`。
- 更新 `pc-tools/README.md`。
- 更新 `docs/navigation/fixed_route_workflow.md`。

交付内容：dependency-free completion-signal CLI，输出 `schema=trashbot.route_task_completion_signal.v1`、`evidence_boundary=software_proof_docker_route_task_completion_signal_gate`、`same_evidence_ref_required=true`、`completion_verdict`、`dropoff_completion`、`cancel_completion`、failure/recovery reason、`operator_next_steps`、`not_proven`、`delivery_success=false` 和 `primary_actions_enabled=false`。

### Task B - Robot

- 更新 `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`。
- 更新 `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`。
- 更新 `docs/interfaces/ros_contracts.md`。

交付内容：diagnostics metadata-only 消费 `route_task_completion_signal` / summary，支持 explicit ref 和环境变量来源；缺失、坏 JSON、unsupported schema/boundary、unsafe fields、`delivery_success=true` 或 primary actions enabled 时均 fail closed。

### Task C - Full-stack

- 更新 `mobile/web/index.html`。
- 更新 `mobile/web/app.js`。
- 更新 `mobile/web/styles.css`。
- 更新 `mobile/test_mobile_web_entrypoint.py`。
- 更新 `docs/product/mobile_user_flow.md`。

交付内容：`mobile/web` 新增只读“路线任务完成信号”panel，展示 completion verdict、safe `evidence_ref`、dropoff/cancel completion status、failure/recovery reason、operator next steps、`delivery_success=false`、`primary_actions_enabled=false`、`not_proven` 和 evidence boundary；不改变 Start/Confirm/Cancel gating。

## 2. 验证结果

### Worker 验证

- Task A Autonomy：`python3 -m py_compile pc-tools/evidence/route_task_completion_signal.py pc-tools/evidence/test_route_task_completion_signal.py` pass；`python3 pc-tools/evidence/test_route_task_completion_signal.py` 输出 `Ran 8 tests in 0.016s OK`；CLI `--help` pass；required `rg` pass；scoped `git diff --check` pass。
- Task B Robot：`python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py` pass；`python3 onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py` 输出 `Ran 65 tests OK`；required `rg` pass；scoped `git diff --check` pass。
- Task C Full-stack：`python3 mobile/test_mobile_web_entrypoint.py` 输出 `Ran 36 tests OK`；`python3 -m py_compile mobile/test_mobile_web_entrypoint.py` pass；`node --check mobile/web/app.js` pass；required `rg` pass；scoped `git diff --check` pass。

### Product closeout 验证

- `test -f` closeout 三文档：pass。
- closeout required `rg`：pass。
- scoped `git diff --check`：pass。
- `git diff --check --cached`：pass。

Browser 补验未运行，原因是 worker 证据中 `iab unavailable`。因此本轮不计真实手机、真实浏览器、production app 或 PWA prompt/user choice 证明。

## 3. 失败定位

本轮 closeout 未收到需要 Product 介入修复的工程失败。已知缺口不是本轮失败，而是证据边界：本轮 completion signal 不访问 ROS graph、Nav2 runtime、hardware/serial/WAVE ROVER/cloud，也不触发 collect/dropoff/cancel/ACK/cursor/terminal ACK/Nav2/HIL/delivery success。

## 4. 剩余风险

- `completed_not_proven` 只能表示 Docker/local completion signal 材料形状足够进入人工复核，不能解释为真实 delivery success。
- 仍缺真实 Nav2/fixed-route 运行、真实路线采集、同一 `evidence_ref` 上车实机复账、真实 dropoff completion、真实 cancel completion、failure recovery 和真实送达。
- 仍缺 WAVE ROVER、真实串口/UART、`T=1001` feedback 和 HIL。
- 仍缺真实手机设备/browser、production app、真实 PWA prompt/user choice。
- Objective 5 仍缺真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、worker/migration 和外部 probe proof。

## 5. OKR 最低优先级回顾

启动时 `OKR.md` 4.1 中最低 Objective 为 Objective 2 和 Objective 3，均约 64%。本 sprint 直接针对该最低组合推进 completion signal，因此最低优先级选择仍成立。

本轮 completion signal 可以让 O2/O3 从 reconciliation verdict 前进到 completion verdict、dropoff/cancel completion status、failure/recovery reason 和 operator next steps 的软件证据链；但没有真实 Nav2/fixed-route、真实 dropoff/cancel completion、HIL、真实手机或 O5 external proof。因此 closeout 建议只将 Objective 2 和 Objective 3 各保守提升约 1pp，Objective 1 / 4 / 5 不提升。
