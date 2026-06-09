# Nav2 refresh stable rerun

sprint_type: micro

## 实际改动

- 新建 `sprints/2026.06.10_07-20_nav2_refresh_stable_rerun/artifacts/remote_capture/`，保存正式
  no-motion `/api/nav2/proof/refresh` 复跑证据。
- 新建本文件，记录本地稳定化验收、远端服务状态、API response、canonical runtime artifacts 和剩余 blocker。
- 未修改产品代码、测试代码、硬件配置或 launch 参数；本轮无需修复 `upper_robot_api.py`，因为复跑返回结构化 JSON，
  且服务没有再次断连接或重启。

## 本地验证结果

- `PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile onboard/scripts/upper_robot_api.py onboard/scripts/o10_amcl_nav2_runtime_proof.py`
  - 通过，无输出。
- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/tests/test_upper_robot_api.py`
  - `Ran 7 tests in 0.006s`
  - `OK`
- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s onboard/tests -p 'test_nav2_runtime_proof_helper.py'`
  - `Ran 4 tests in 0.045s`
  - `OK`
- `git diff --check`
  - 通过，无输出。

## 远端 no-motion rerun

目标：`root@192.168.1.11:37878`，远端 hostname 为 `op-z3-b6.home`。

### pre 状态

- `systemctl is-active trashbot-upper-robot-api.service`：`active`。
- `trashbot-upper-robot-api.service` 自 `Wed 2026-06-10 05:08:17 CST` 起保持 `active (running)`，
  `Main PID=115648`。
- `journalctl -u trashbot-upper-robot-api.service -n 80` 显示 05:08:17 有一次 stop/start，
  与上一轮 `map_proof_api_contract_harden` 部署窗口一致；05:08:18 后只有 API started 事件。
- `lsof /dev/ttyS5 /dev/ttyACM0` 和 `fuser -v /dev/ttyS5 /dev/ttyACM0`：无占用输出。

### API 调用结果

- `POST /api/nav2/proof/refresh -d '{"timeout_s":20}'`
  - curl exit：`0`
  - HTTP：`200`
  - response `status=blocked_with_root_cause`
  - response `proof_state=blocked_with_root_cause`
  - response `evidence_type=blocked_with_root_cause`
  - `command_result.ok=false`
  - `command_result.returncode=2`
  - `command_result.elapsed_ms=91800`
- `GET /api/nav2/proof/latest`
  - HTTP：`200`
  - top-level `status=not_proven`
  - `latest_result.status=blocked_with_root_cause`
  - `latest_result.proof.status=blocked_with_root_cause`
- `GET /api/nav2/status`
  - HTTP：`200`
  - `status=not_proven`
  - `amcl_nav2_readiness.status=map_inputs_ready_for_no_motion_nav2_collector`
  - `proof_latest.latest_proof_status=blocked_with_root_cause`

### post/final 状态

- `trashbot-upper-robot-api.service` 复跑后仍为 `active (running)`，仍是 `Main PID=115648`。
- `journalctl --since "2026-06-10 05:08:18"` 只有：
  `{"event": "upper_robot_api_started", "host": "0.0.0.0", "port": 8787}`。
- 未出现新的 Python traceback、systemd restart、`Empty reply from server` 或 curl 错误。
- post `lsof/fuser /dev/ttyS5 /dev/ttyACM0`：无占用输出。
- `/root/rober/onboard/runtime/nav2_lifecycle_latest.json` 已在 05:14 更新，大小 `12549` bytes。

## 当前 blockers

正式 artifact 证明本轮不是 Nav2 ready，只是 no-motion collector 成功返回结构化 blocker：

- ROS package 缺失：
  - `nav2_amcl_missing`
  - `nav2_planner_missing`
  - `nav2_controller_missing`
- lifecycle 未 active：
  - `map_server_lifecycle_not_active`
  - `amcl_lifecycle_not_active`
  - `planner_lifecycle_not_active`
  - `controller_lifecycle_not_active`
- topic/material 未观测：
  - `/scan_once_not_observed`
  - `/map_once_not_observed`
  - `/amcl_pose_once_not_observed`
- proof flags：
  - `map_server_active=false`
  - `amcl_active=false`
  - `planner_active=false`
  - `controller_active=false`
  - `scan_once_observed=false`
  - `map_once_observed=false`
  - `amcl_pose_observed=false`
  - `path_generation_ready=false`
  - `path_generated=false`
  - `publishes_cmd_vel=false`
  - `calls_base_manual=false`
  - `uses_base_uart=false`
  - `delivery_success=false`

## Artifact 清单

- `artifacts/remote_capture/pre_service_status.txt`
- `artifacts/remote_capture/pre_service_journal_tail.txt`
- `artifacts/remote_capture/pre_serial_occupancy.txt`
- `artifacts/remote_capture/api_nav2_proof_refresh_response.json`
- `artifacts/remote_capture/api_nav2_proof_refresh_response.stderr`
- `artifacts/remote_capture/api_nav2_proof_latest_response.json`
- `artifacts/remote_capture/api_nav2_proof_latest_response.stderr`
- `artifacts/remote_capture/api_nav2_status_response.json`
- `artifacts/remote_capture/api_nav2_status_response.stderr`
- `artifacts/remote_capture/post_service_status.txt`
- `artifacts/remote_capture/post_service_journal_tail.txt`
- `artifacts/remote_capture/post_service_journal_since_restart.txt`
- `artifacts/remote_capture/post_serial_occupancy.txt`
- `artifacts/remote_capture/runtime_artifact_listing_after_refresh.txt`
- `artifacts/remote_capture/onboard_runtime_nav2_lifecycle_latest.json`
- `artifacts/remote_capture/onboard_runtime_map_lifecycle_latest.json`
- `artifacts/remote_capture/scp_nav2_lifecycle_latest.log`
- `artifacts/remote_capture/scp_map_lifecycle_latest.log`

## 剩余风险

- 本轮没有证明 AMCL/Nav2 ready、path generation、path execution、fixed route execution、HIL 或 delivery success。
- `map_inputs_ready_for_no_motion_nav2_collector` 只说明 canonical map proof 可作为下一步 collector 输入；
  不代表 Nav2 runtime 可用。
- 远端缺 `nav2_amcl`、`nav2_planner`、`nav2_controller` 且没有相关 lifecycle active/topic 证据；
  下一步应先补齐或启动 Nav2 runtime 依赖，再复跑 no-motion collector。
- 本轮未调用 `/api/base/*`、`/api/map/start`、`/api/nav2/start`，未发布 `/cmd_vel`，
  未打开 `/dev/ttyS5`；验证范围限定为 no-motion API readback 和只读服务/串口占用检查。
