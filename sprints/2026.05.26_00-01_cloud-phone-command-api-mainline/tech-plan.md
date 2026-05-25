# Cloud Phone Command API Mainline Tech Plan

## OKR 最低优先级核对

1. 当前 `OKR.md` 4.1 完成度最低 Objective：Objective 5，约 68%。
2. 本 sprint 直接针对 Objective 5。
3. 选择理由：历史 O5 多轮停留在 external evidence / review / handoff / escalation metadata，本轮改做真实可调用的 cloud phone command API，功能往前走。

## 方案

新增能力名：`cloud_phone_command_api`。

### Task A：Robot Software Engineer

文件范围：

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py`
- `onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py`
- `docs/product/remote_4g_mvp.md`
- `docs/product/cloud_4g_infrastructure.md`
- `cloud-relay/README.md`

实现要求：

- 在 independent relay 增加 bearer-gated phone command API，例如：
  - `POST /api/commands/collect`
  - `POST /api/commands/confirm-dropoff`
  - `POST /api/commands/cancel`
- API 从 body 读取 `robot_id`、可选 `idempotency_key` / `command_id`、任务 payload，并复用现有 store `submit_command()`。
- 返回 phone-safe receipt：`capability=cloud_phone_command_api`、`evidence_boundary=software_proof_docker_cloud_phone_command_api_gate`、`delivery_success=false`、`primary_actions_enabled=false`、`safe_to_control=false`、`ack_semantics=queued_not_delivery_success`。
- 不输出 Authorization、token、raw state path、ROS topic、`/cmd_vel`、serial/UART/WAVE ROVER 字段。

验收命令：

- `python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py`
- `PYTHONPATH=onboard/src/ros2_trashbot_behavior python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py -k cloud_phone_command_api`
- `git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py docs/product/remote_4g_mvp.md docs/product/cloud_4g_infrastructure.md cloud-relay/README.md`

### Task B：User Touchpoint Full-Stack Engineer

文件范围：

- `mobile/web/app.js`
- `mobile/web/test_mobile_web_entrypoint.py`
- `mobile/web/fixtures/robot_diagnostics_cloud_phone_command_api.json`
- `docs/product/mobile_user_flow.md`
- 可选：`pc-tools/workstation/src/**`、`pc-tools/workstation/test/**`、`docs/product/pc_tools_workstation.md`

实现要求：

- 让用户触点出现 `cloud_phone_command_api` 提交/receipt 展示，不再只是只读 metadata panel。
- UI 只能提交任务级动作，不暴露 raw `/robots/*`、ROS topic、`/cmd_vel`、serial/UART/WAVE ROVER 或 token。
- receipt/pending 状态必须明确“已入队/等待机器人处理，不是送达成功”。
- 如果无法安全处理 bearer/token，UI 先提供 PC workstation 本地配置提交面，mobile/web 展示同源 API receipt 结构和 disabled fallback。

验收命令：

- `node --check mobile/web/app.js`
- `PYTHONPATH=mobile python3 -m unittest mobile/web/test_mobile_web_entrypoint.py -k cloud_phone_command_api`
- 如改 PC workstation：`cd pc-tools/workstation && npm run build && npm run test`
- `git diff --check -- mobile/web mobile/fixtures docs/product/mobile_user_flow.md pc-tools/workstation docs/product/pc_tools_workstation.md`

## 接口影响

- 新增 phone/API 任务级命令提交面；现有 robot polling、ACK、status API 不破坏。
- `/robots/{robot_id}/commands` 仍保留给 robot/cloud 内部 contract；普通用户入口优先走 `/api/commands/*`。

## 风险

- Docker/local software proof 不能替代公网 HTTPS/TLS、真实 4G/SIM、OSS/CDN live traffic、production DB/queue 或真实送达。
- 命令入队不是机器人执行完成；所有 UI 和 receipt 必须保持 false-state。
- 如果真实 bearer 登录体系缺失，本轮只能证明同源 API contract 和本地 PC/operator 配置路径。
