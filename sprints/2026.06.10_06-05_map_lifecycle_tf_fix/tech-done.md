# 2026-06-10 06:05 map lifecycle TF fix

sprint_type: micro

## 实际改动

- `onboard/scripts/o3_map_lifecycle_proof.py`：在 no-motion LiDAR+SLAM runtime 的 `learn.launch.py` command 中显式加入 `static_laser_tf_enabled:=true`，与既有 `no_motion_static_odom_tf:=true` 一起补齐 `odom -> base_link -> laser_frame` smoke-only TF 链。
- `onboard/tests/test_map_lifecycle_proof_helper.py`：新增静态测试，锁定 helper command 同时包含 `static_laser_tf_enabled:=true`、`no_motion_static_odom_tf:=true`、`lidar_enabled:=true`、`lidar_publish_raw_packets:=true`，并继续禁止 `/api/base/*`、`/api/map/start`、`/api/nav2/*`、`/dev/ttyS5` 和 `base_enabled:=true`。
- `docs/hardware/board_sensor_stack_smoke.md`：补充 06:05 no-motion laser TF 修正说明，明确这是 smoke-only TF，不是机械标定，也不等同于可导航地图。

## 验证结果

- `python3 -m py_compile onboard/scripts/o3_map_lifecycle_proof.py`：通过。
- `python3 onboard/scripts/o3_map_lifecycle_proof.py --help`：通过，help 只展示 argparse 参数，未启动 ROS2 runtime。
- `python3 -m unittest discover -s onboard/tests -p 'test_map_lifecycle_proof_helper.py'`：通过，`Ran 4 tests in 0.046s OK`。
- `git diff --check`：通过，无 whitespace error。
- `rg -n "static_laser_tf_enabled|no_motion_static_odom_tf|publishes_cmd_vel|calls_base_manual|uses_base_uart|delivery_success" ...`：通过，helper/test/doc/sprint 均能检索到本轮 TF 参数和安全 guard。

远端候选验证：

- SSH `root@192.168.1.11 -p 37878` 可达，`hostname=op-z3-b6.home`，初始 `lsof /dev/ttyS5 /dev/ttyACM0` 无输出。
- 已把候选 helper 复制到 `/tmp/rober_o3_map_lifecycle_proof_candidate.py`，未覆盖 `/root/rober/onboard/scripts/o3_map_lifecycle_proof.py`。
- 第一轮候选在默认 ROS domain 下 `candidate_rc=0`，但远端存在历史 `map_recorder` 进程，因此只作为辅助材料保留。
- 第二轮使用 `ROS_DOMAIN_ID=77` 和 `/tmp/rober_candidate_maps_domain77` 隔离运行，`candidate_rc=0`。
- 隔离候选 artifact：`sprints/2026.06.10_06-05_map_lifecycle_tf_fix/artifacts/remote_candidate/domain77/rober_map_lifecycle_candidate_domain77.json`。
- 隔离候选 runtime command 包含 `static_laser_tf_enabled:=true` 与 `no_motion_static_odom_tf:=true`，并使用 `lidar_serial_port:=/dev/ttyACM0`。
- 隔离候选结果：`status=map_once_artifact_metadata_observed`、`scan_once_observed=true`、`map_once_observed=true`、`map_metadata_observed=true`、`map_file_observed=true`、`root_causes=[]`。
- 隔离 map metadata：`frame_id=map`、`resolution=0.05000000074505806`、`width=230`、`height=130`。
- 隔离 save map response：`Map saved to /tmp/rober_candidate_maps_domain77/trashbot_map.pgm`。
- 安全 guard 保持：`publishes_cmd_vel=false`、`calls_base_manual=false`、`uses_base_uart=false`、`safe_to_control=false`、`delivery_success=false`。
- 运行前、运行中、运行后、最终复核 `lsof /dev/ttyS5 /dev/ttyACM0` 均无输出；最终 `fuser -v /dev/ttyS5 /dev/ttyACM0` 也无输出。未观察到 WAVE ROVER/base UART `/dev/ttyS5` 被打开。

## 剩余风险

- 本修正已证明候选 helper 在隔离 ROS domain 下能让 `/map` once、metadata 和 map file 出现；但这仍只是 no-motion SLAM proof，不等同于可导航地图。
- `static_laser_tf_enabled` 使用默认零位姿，仅用于 smoke proof；真实机械外参、地图质量、AMCL/Nav2 readiness、fixed route 和 delivery proof 仍需后续验证。
- 本轮禁止触碰 WAVE ROVER/base UART `/dev/ttyS5`，因此不包含任何运动、底盘反馈或可导航结论。
- 远端默认 ROS graph 里存在历史 `map_recorder` 进程，本轮未清理范围外进程；后续若通过正式 `/api/map/proof/refresh` 验证，应先处理或隔离这些环境残留，避免 service/topic 污染。
