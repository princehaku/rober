# Cloud Command Terminal Result Mainline Tech Done

## 1. Sprint 声明

- sprint_type: epic
- sprint_id: `2026.05.26_07-08_cloud-command-terminal-result-mainline`
- closeout 时间：2026-05-26 07:57 Asia/Shanghai
- Product closeout owner：`product-okr-owner`
- 证据边界：`software_proof_docker_cloud_command_terminal_result_gate`

## 2. 用户价值和产品北极星

本轮把 Objective 5 从“命令结果核对仍停在 `terminal_result_pending`”推进到“同一 `robot_id + command_id` 下 terminal result 可以写入、持久化、查询并在手机端展示”。北极星不变：普通手机用户不需要理解 ROS2、ACK、queue 或云端 store，也能看到命令是否已有机器人上报的终态结果，同时不会被本地 software proof 误导成真实送达成功。

## 3. OKR 映射

- Objective 5：直接推进，上一快照约 76%，本轮 Product 判断可保守提升到约 80%。
- Objective 1：保持约 83%，本轮不触碰 WAVE ROVER、UART、HIL、2D LiDAR / ToF 或硬件协议。
- Objective 2：保持约 99%，本轮不证明真实送达、dropoff/cancel field completion、route/elevator field pass 或 delivery success。
- Objective 3：保持约 99%，本轮不证明 Nav2/fixed-route runtime、真实路线采集或 route completion signal。
- Objective 4：保持约 99%，mobile/web 有展示改进，但仍不是 true phone/browser proof。

## 4. Worker 成果核对

### Robot Software Engineer

实际改动文件：

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py`
- `onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py`
- `cloud-relay/README.md`
- `docs/product/remote_4g_mvp.md`
- `docs/product/cloud_4g_infrastructure.md`

实现结果：

- 新增 robot-facing `POST /robots/{robot_id}/commands/{command_id}/terminal-result`。
- 新增 `trashbot.cloud_command_terminal_result.v1` / `cloud_command_terminal_result`。
- result query schema 升级为 `trashbot.cloud_command_result_reconciliation.v2`。
- file-backed 和 SQLite-backed store 均能持久化 terminal result。
- result reconciliation 返回 `terminal_result_recorded`。
- ACK-only 仍返回 `terminal_result_pending`。
- conflict、missing、store_unavailable 均 fail-closed。

验证结果：

- `python3 -m py_compile .../remote_cloud_relay.py`：exit 0。
- focused unittest：`Ran 10 tests in 7.167s OK`。
- scoped `git diff --check`：exit 0。

### User Touchpoint Full-Stack Engineer

实际改动文件：

- `mobile/web/app.js`
- `mobile/web/test_mobile_web_entrypoint.py`
- `mobile/web/fixtures/robot_diagnostics_cloud_command_result_reconciliation.json`
- `mobile/web/fixtures/robot_diagnostics_cloud_command_terminal_result.json`
- `docs/product/mobile_user_flow.md`

实现结果：

- 现有“命令结果核对”面板展示 `terminal_result_recorded`。
- 展示 result type、result code、error code、safe `command_id`、safe `evidence_ref` 和 `next_required_evidence`。
- pending、conflict、missing、store_unavailable 均有中文 fail-closed copy。
- 主操作不会因为 `terminal_result_recorded` 自动启用。

验证结果：

- `node --check mobile/web/app.js`：passed。
- focused unittest：`Ran 5 tests OK`。
- scoped `git diff --check`：passed。

## 5. Product closeout 判断

本轮不是 metadata-only wrapper。它覆盖 API、store、query 和 UI 主链路，因此 Objective 5 可以从约 76% 小幅提升到约 80%。提升理由是 `cloud_command_terminal_result` 让上一轮 `cloud_command_result_reconciliation` 的 `terminal_result_pending` 有了可写入、可持久化、可查询、可展示的终态路径。

仍然必须保留以下 false-state：

- `delivery_success=false`
- `safe_to_control=false`
- `primary_actions_enabled=false`
- `real_world_delivery_proven=false`

## 6. 偏差和剩余风险

本轮没有失败重试项。剩余风险全部来自外部真实环境和现场材料：

- 不证明公网 HTTPS/TLS。
- 不证明真实 4G/SIM。
- 不证明 OSS/CDN live traffic。
- 不证明 production DB/queue、production worker/cutover、多实例一致性、queue ordering、transaction isolation 或 backup/recovery。
- 不证明 true phone/browser proof、真实 iPhone/Android 设备或 production app。
- 不证明 WAVE ROVER/UART、HIL、2D LiDAR / ToF 安装材料或 PR #5 resolution。
- 不证明 Nav2/fixed-route runtime、真实电梯、真实 route/elevator field pass、dropoff/cancel field completion 或 delivery success。
