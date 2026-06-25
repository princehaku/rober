# PC Nav2 TF Static Transform Contract

sprint_type: micro

## 实际改动

- `onboard/scripts/o10_amcl_nav2_runtime_proof.py`：O10 no-motion helper 现在会在未 opt-in `/initialpose` 时仍只读现有 ROS graph 的 `/tf` 与 `/tf_static`，解析 TFMessage 数值，并在 partial/final artifact 中保留 `base_link_to_laser_frame_transform`。
- `onboard/scripts/upper_robot_api.py`：timeout fallback 会从 partial proof 的顶层、`tf_source_root_cause_detail` 或 `tf_frame_inventory` 提升 `base_link -> laser_frame` 外参，并在 `/api/nav2/proof/latest` 顶层只读输出。
- `pc-tools/workstation/src/server/robotControlSummary.ts`：PC summary 的外参合并从只看 `localize_proof_latest` 扩展为 `localize_proof_latest -> nav2_proof_latest -> nav2_status -> status`，仍只接受结构化 transform 数值。
- `docs/product/pc_tools_workstation.md`：补充 PC summary 对 Nav2 latest / `/tf_static` 外参 fallback 的安全边界。
- 真实上位机已部署并备份：
  - `/root/rober/onboard/scripts/backup_20260625_165105_o10_readonly_tf_source/`
  - `/root/rober/onboard/scripts/backup_20260625_165327_upper_tf_transform_contract/`
  - `/root/rober/onboard/scripts/backup_20260625_165446_nav2_latest_tf_contract/`

## 验证结果

- 本地 Python：`python3 -m unittest onboard.tests.test_upper_robot_api onboard.tests.test_nav2_runtime_proof_helper` 通过，76 tests。
- 本地 PC：`npm test` 通过，155 tests；`npm run lint` 通过；`npm run build` 通过。
- 远端部署：`ssh root@192.168.1.11 -p 37878` 成功，`trashbot-upper-robot-api.service` active，`0.0.0.0:8787` 由 PID `85019` 监听。
- 远端只读 proof：`GET http://127.0.0.1:8787/api/nav2/proof/latest` 返回 `safe_to_control=false`，`tf_chain_observed.base_link_to_laser_frame=true`，`base_link_to_laser_frame_transform.source=/tf_static`，translation/yaw 均为 0。
- 本机 PC：`npm run api:public` 已重启到 `0.0.0.0:7001`，PID `52613`；`GET /api/robot-control/summary?baseUrl=http://192.168.1.11:8787` 返回 `base_link_to_laser_frame={parent_frame_id:base_link, child_frame_id:laser_frame, x:0, y:0, yaw:0, source:/tf_static}`，`safe_to_control=false`，`delivery_success=false`。

## 剩余风险

- 本轮只证明 `/tf_static` 外参能进入 upper/PC readback；没有证明真实 `/scan` preview 点、机器人 map pose、完整 Nav2 路线执行、delivery success 或 wheel raw L/R 非零。
- O10 no-motion refresh 仍可能因后续 ROS2 CLI 阶段超时而返回 `blocked_with_root_cause`，但 partial artifact 已能保留 TF 链和雷达外参。
- 本轮未调用会让车动的接口：未调用 `/api/base/manual`、`/cmd_vel`、Nav2 NavigateToPose、delivery complete、radar start、map start/save/reset。
