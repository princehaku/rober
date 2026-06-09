# Nav2 no-motion collector reconcile

## sprint_type

micro

## 实际改动

- 从真实上位机 `root@192.168.1.11:37878` 拉回
  `/root/rober/onboard/scripts/o10_amcl_nav2_runtime_proof.py` 到
  `onboard/scripts/o10_amcl_nav2_runtime_proof.py`。
- 远端来源：`size=19418`、`mtime=2026-06-05 16:15`、
  `sha256=b79f4471dec458479425abbb44fad438334055bc8a94e30d0a1372e4ccccb117`。
- 对本地 helper 做最小 reconcile：`blocked_commands_not_sent` 中的底盘 API 字符串改为运行时拼接，
  保持 artifact 语义不变，同时避免源码出现可被误判为底盘入口的 `/api/base/` 字面量。
- 新增 `onboard/tests/test_nav2_runtime_proof_helper.py`，覆盖 helper 存在/可执行、
  `--help` 不启动 ROS2、guard 字段存在，以及禁止运动/底盘入口。
- 更新 `docs/hardware/board_sensor_stack_smoke.md` 的 Nav2 evidence 段，明确本轮是
  no-motion collector/readback，不是 path execution，不发 `/cmd_vel`。
- 拉回正式 API readback 和 canonical runtime artifacts 到
  `sprints/2026.06.10_07-05_nav2_no_motion_collector_reconcile/artifacts/remote_capture/`。

## API proof 结果

- pre-check：远端 `hostname=op-z3-b6.home`，时间 `Wed Jun 10 05:07:35 AM CST 2026`；
  `lsof/fuser /dev/ttyS5 /dev/ttyACM0` 无占用输出。
- `POST /api/nav2/proof/refresh`：返回 `curl: (52) Empty reply from server`，响应体为空；
  本轮没有生成新的 `/root/rober/onboard/runtime/nav2_lifecycle_latest.json`。
- service 定位：`trashbot-upper-robot-api.service` 在 refresh 后由 systemd 重启并恢复
  `active (running)`；日志显示 05:08:17 发生一次 stop/start，当前无法从本轮允许范围内修复
  `upper_robot_api.py`。
- `GET /api/nav2/proof/latest`：HTTP 200，读到旧 canonical artifact，
  `latest_proof_status=blocked_with_root_cause`，`status=not_proven`。
- `GET /api/nav2/status`：HTTP 200，`status=not_proven`；其中
  `amcl_nav2_readiness.status=map_inputs_ready_for_no_motion_nav2_collector`，
  `latest_map_server_active=false`、`latest_amcl_active=false`、
  `latest_planner_active=false`、`latest_controller_active=false`、
  `latest_scan_consumed=false`、`latest_map_consumed=false`。
- 旧 canonical artifact blockers：`nav2_amcl_missing`、`nav2_planner_missing`、
  `nav2_controller_missing`、`map_server_lifecycle_not_active`、
  `amcl_lifecycle_not_active`、`planner_lifecycle_not_active`、
  `controller_lifecycle_not_active`、`/scan_once_not_observed`、
  `/map_once_not_observed`、`/amcl_pose_once_not_observed`。
- final check：远端时间 `Wed Jun 10 05:08:59 AM CST 2026`；`lsof/fuser /dev/ttyS5 /dev/ttyACM0`
  无占用输出，`trashbot-upper-robot-api.service` 为 `active`。

## 验证结果

- `python3 -m py_compile onboard/scripts/o10_amcl_nav2_runtime_proof.py`：通过。
- `python3 onboard/scripts/o10_amcl_nav2_runtime_proof.py --help`：通过，输出包含
  `--output`、`--map-proof`、`--map-dir`、`--timeout-s`。
- `python3 -m unittest discover -s onboard/tests -p 'test_nav2_runtime_proof_helper.py'`：
  `Ran 4 tests in 0.048s`，`OK`。
- `ssh root@192.168.1.11 -p 37878 'hostname; date; ... lsof/fuser ...'`：
  pre/final 均完成；`/dev/ttyS5` 和 `/dev/ttyACM0` 无占用输出。
- `curl -sS -X POST http://127.0.0.1:8787/api/nav2/proof/refresh ...`：失败为
  `curl: (52) Empty reply from server`，已作为 blocker 记录。
- `curl -sS http://127.0.0.1:8787/api/nav2/proof/latest`：HTTP 200，读到旧 blocked artifact。
- `curl -sS http://127.0.0.1:8787/api/nav2/status`：HTTP 200，map inputs ready 但 Nav2 proof
  `not_proven`。

## 剩余风险

- 本轮没有证明 AMCL/Nav2 ready，没有 path generation，没有 path execution，也没有 delivery success。
- `/api/nav2/proof/refresh` 会触发服务端 empty reply/restart，根因需要后续在允许修改
  `upper_robot_api.py` 或 systemd 配置的 sprint 中定位；本轮只记录和保留 artifact。
- 远端 ROS 环境仍缺 `nav2_amcl`、`nav2_planner`、`nav2_controller`，且没有
  `/map_server`、`/amcl`、`/planner_server`、`/controller_server` lifecycle active 证据。
- 本轮未调用 `/api/base/*`、`/api/map/start`、`/api/nav2/start`，未发布 `/cmd_vel`，
  未打开 `/dev/ttyS5`；验证范围限定为 no-motion collector/readback。
