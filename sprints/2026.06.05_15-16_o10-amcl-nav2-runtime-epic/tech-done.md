# Tech Done: O10 AMCL/Nav2 Runtime Collector Epic

## sprint_type

sprint_type: epic

## 实际改动

Robot Software Engineer 本轮完成 O10 `KR-O10-AMCL-Nav2-Runtime-Collector`
最小功能切片：

- 新增 `onboard/scripts/o10_amcl_nav2_runtime_proof.py`，作为 no-motion AMCL/Nav2
  runtime proof collector。它基于 canonical map proof
  `/root/rober/onboard/runtime/map_lifecycle_latest.json` 和 map artifacts
  `/root/rober/onboard/runtime/maps`，只读采集 ROS2 graph 中的 map server、AMCL、
  planner/controller lifecycle、`/scan`、`/map`、`/amcl_pose`、`/initialpose`
  边界和 path generation readiness。
- 修复 lifecycle parser 的 fail-closed 判断：不能用 `"active" in text` 判断状态，
  因为 `inactive` 包含 `active` 子串；现在只接受精确 `active` 形态。
- 更新 `onboard/scripts/upper_robot_api.py`，新增：
  - `POST /api/nav2/proof/refresh`
  - `GET /api/nav2/proof/latest`
  - `/api/nav2/status` 中暴露 `proof_refresh` / `proof_latest` route。
- 更新 `onboard/scripts/test_upper_robot_api.py`，覆盖 Nav2 proof refresh/latest HTTP
  route 不返回 405、blocked artifact 可 readback、以及 no-motion 安全字段保持 false。
- 更新 `docs/navigation/nav2_map_quality_metrics.md`，记录 O10 no-motion
  AMCL/Nav2 proof artifact 边界。

## 验证结果

本地验证：

- `python3 -m compileall -q onboard/scripts onboard/src`：通过，exit 0，无输出。
- `python3 -m unittest onboard.scripts.test_upper_robot_api`：通过，
  `Ran 39 tests`，`OK (skipped=4)`。
- `python3 -m unittest discover -s onboard/scripts -p 'test_*.py'`：通过，
  `Ran 88 tests`，`OK (skipped=4)`。
- `git diff --check -- onboard/scripts docs/navigation docs/interfaces sprints/2026.06.05_15-16_o10-amcl-nav2-runtime-epic`：
  通过，exit 0。

远端部署与 live 验证：

- `scp -P 37878 onboard/scripts/upper_robot_api.py onboard/scripts/o10_amcl_nav2_runtime_proof.py root@192.168.1.11:/root/rober/onboard/scripts/`：
  通过，exit 0，无输出。
- `ssh root@192.168.1.11 -p 37878 'systemctl restart trashbot-upper-robot-api.service && systemctl is-active trashbot-upper-robot-api.service'`：
  通过，输出 `active`。
- `curl -sS -X POST http://192.168.1.11:8787/api/nav2/proof/refresh`：
  HTTP 回包成功，`status=blocked_with_root_cause`，
  `proof_state=blocked_with_root_cause`，`latest_readback_http_status=200`。
- `curl -sS http://192.168.1.11:8787/api/nav2/proof/latest`：
  HTTP 回包成功，artifact `status=loaded`，path 为
  `/root/rober/onboard/runtime/nav2_lifecycle_latest.json`。

远端关键证据边界：

- canonical map inputs ready：latest map proof 已加载，
  `source_evidence_type=robot_runtime_material`，
  `source_evidence_ref=o3-map-lifecycle-1780633643849`；
  YAML/PGM 分别为
  `/root/rober/onboard/runtime/maps/trashbot_map.yaml` 和
  `/root/rober/onboard/runtime/maps/trashbot_map.pgm`。
- AMCL/Nav2 runtime blocked root cause：
  - `nav2_amcl_missing`
  - `nav2_planner_missing`
  - `nav2_controller_missing`
  - `map_server_lifecycle_not_active`
  - `amcl_lifecycle_not_active`
  - `planner_lifecycle_not_active`
  - `controller_lifecycle_not_active`
  - `/scan_once_not_observed`
  - `/map_once_not_observed`
  - `/amcl_pose_once_not_observed`
- 远端 `ros2` 本身可用：`/opt/ros/humble/bin/ros2`。
- 远端当前 ROS graph 只有 `/parameter_events` 和 `/rosout`；`ros2 node list` 为空。

## 安全字段

本轮本地和远端 payload 均固定 no-motion 边界：

- `safe_to_control=false`
- `sends_base_motion_commands=false`
- `publishes_cmd_vel=false`
- `calls_base_manual=false`
- `robot_control_executed=false`
- `hil_pass=false`

collector 不打开 `/dev/ttyS5`，不调用 `/api/base/manual`，不发布 `/cmd_vel`，
不发布 `/initialpose`，不发送 Nav2 goal，不执行 fixed route。

## 剩余风险

- 本轮完成 O10 no-motion AMCL/Nav2 proof collector 和 live blocker artifact，
  但没有证明 AMCL 定位、Nav2 消费 `/scan` + map、路径生成、路径执行或 delivery success。
- 远端缺 `nav2_amcl`、`nav2_planner`、`nav2_controller` 包，且没有 map_server、AMCL、
  planner、controller lifecycle runtime；需要 Autonomy/Robot Software 后续补齐
  Nav2 runtime install/launch。
- 当前 map inputs ready 只证明 canonical map artifact 可作为 collector 输入，不证明 map
  quality pass 或 fixed-route 可跑。
- 没有 HIL、WAVE ROVER ACK、`/odom`、`/imu/data`、`/battery`、PC WASD 或 stop-first
  现场材料；O1/O3/O10 只能按 no-motion blocker artifact 边界评估。

## 协同需求

- Product/OKR：建议只把本轮计为 O10 no-motion runtime collector + blocked root cause
  证据，不应把 O10 写成可导航或送达闭环完成；可考虑 O10 小幅上涨，O3 不因
  AMCL/Nav2 runtime blocked 而上涨。
- Autonomy：需要补齐 Nav2 AMCL/planner/controller 安装、launch 和 lifecycle bringup。
- Hardware：本轮不需要硬件协同，且不允许在未授权现场条件下把 blocked artifact
  升级为 HIL。
- Full-Stack：后续可读取 `/api/nav2/proof/latest` 做 PC 状态灯，但不能展示为
  `safe_to_control=true` 或可发车。
