# Free-Roam Runtime 所见即所得

sprint_type: micro

## 实际改动

- 修正上位机 `GET /api/free-roam/autonomy/latest` 和 `/api/status.free_roam_autonomy`：当 runtime artifact 是 `trashbot.free_roam_autonomy.runtime.v1` 且成功读取时，显式返回 `free_roam_runtime_artifact_proven=true`、`free_roam_state_machine_observed=true`、`ros2_runtime_proven=true`。
- PC summary 的 `readback_summary.free_roam` 同步新增 `runtime_artifact_proven/state_machine_observed/ros2_runtime_proven`，区分“状态机已在写 runtime”和“当前是否发布 /cmd_vel”。
- 已部署到上车端 `/root/rober/onboard/scripts/upper_robot_api.py`，备份在 `/root/rober/runtime/deploy_backups/upper_api_runtime_wysiwyg_20260626_223441/upper_robot_api.py`，并由 `trashbot-upper-robot-api.service` 接管 8787。

## 验证结果

- 通过：`python3 -m unittest onboard/tests/test_upper_robot_api.py`，`Ran 53 tests in 0.112s OK`。
- 通过：`python3 -m py_compile onboard/scripts/upper_robot_api.py`。
- 通过：`cd pc-tools/workstation && npm test -- catalog.test.ts`，`106 passed`。
- 通过：`cd pc-tools/workstation && npm run build`，client/server TypeScript 与 Vite build 均通过；仅保留 Vite chunk size 提示。
- 通过：`git diff --check`。
- 通过：远端 `python3 -m py_compile /root/rober/onboard/scripts/upper_robot_api.py`。
- 通过：远端 `systemctl restart trashbot-upper-robot-api.service` 后，8787 监听进程由 systemd active 管理。
- 通过：`GET http://192.168.1.11:8787/api/free-roam/autonomy/latest` 返回 `free_roam_state_machine_observed=true`、`ros2_runtime_proven=true`、`artifact_only=true`、`cmd_vel_publish_enabled=false`、`safe_to_control=false`。
- 通过：`GET http://192.168.1.11:8787/api/status` 中 `free_roam_autonomy` 返回 `status=artifact_loaded`、`free_roam_state_machine_observed=true`、`ros2_runtime_proven=true`。
- 通过：重启本机 PC Node 到 `0.0.0.0:7001` 后，`GET http://127.0.0.1:7001/api/robot-control/summary?baseUrl=http://192.168.1.11:8787` 返回 Robot API `readable`、`readback_summary.free_roam.state_machine_observed=true`、`ros2_runtime_proven=true`、`artifact_only=true`、`cmd_vel_publish_enabled=false`。

## 剩余风险

- 本轮是只读 WYSIWYG 修正，不发 start，不发布 `/cmd_vel`，也不证明 wheel raw L/R 非零。
- 当前 live 仍显示摄像头首帧失败、雷达 lifecycle stopped/free-roam `artifact_only=true`，最终“可建图”验收仍要修相机首帧和雷达新鲜度。
