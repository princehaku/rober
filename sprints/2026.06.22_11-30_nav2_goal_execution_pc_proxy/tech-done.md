# sprint_type: micro

## 实际改动

- 新增 `onboard/scripts/o11_nav2_goal_execution_proof.py`，用于显式 opt-in 的 bounded Nav2 `NavigateToPose` 执行 proof。helper 会托管启动 map/amcl、发布一次 `/initialpose`、等待 planner/controller/BT/behavior lifecycle active，再发送目标；超时会 cancel，结束后清理托管 runtime。
- 扩展上位机 `upper_robot_api.py`：
  - 新增 `POST /api/nav2/goal/execute`。
  - 新增 `GET /api/nav2/goal/execution/latest`。
  - 响应保留 `safe_to_control=false`、`primary_actions_enabled=false`、`delivery_success=false`，但允许本 endpoint 记录真实 `robot_control_executed/sends_motion_commands`。
- 扩展 PC workstation：
  - 新增固定代理 `POST /api/robot-control/nav2/goal/execute?baseUrl=...`。
  - `RobotControlConsolePanel` 的默认关闭高级诊断里新增 `执行导航目标（高级）`。
  - PC guard 对该固定 endpoint 放行预期的 `robot_control_executed/sends_motion_commands/sends_commands`，仍拦截 `safe_to_control=true`、`delivery_success=true`、`primary_actions_enabled=true` 等安全字段。
- 补齐 `onboard/src/ros2_trashbot_nav/config/nav2_params.yaml`：
  - AMCL 显式使用 `base_link/odom/map/scan`，避免默认 `base_footprint` 破坏定位 TF。
  - 补全 Humble Nav2 BT plugin library 清单，支持默认 BT XML 里的 `RecoveryNode` 等节点。
- 上车机环境补齐缺失 ROS 运行包：
  - `ros-humble-nav2-bt-navigator`
  - `ros-humble-nav2-behaviors`
  - 以及 apt 自动依赖 `ros-humble-nav2-behavior-tree`、`ros-humble-behaviortree-cpp-v3` 等。

## 验证结果

- 本地：
  - `python3 -m py_compile onboard/scripts/upper_robot_api.py onboard/scripts/o11_nav2_goal_execution_proof.py` 通过。
  - `python3 -m unittest onboard.tests.test_upper_robot_api` 通过，34 tests。
  - `cd pc-tools/workstation && npm test` 通过，99 tests。
  - `cd pc-tools/workstation && npm run lint` 通过。
  - `cd pc-tools/workstation && npm run build` 通过。
- 上车机：
  - `python3 -m py_compile /root/rober/onboard/scripts/upper_robot_api.py /root/rober/onboard/scripts/o11_nav2_goal_execution_proof.py` 通过。
  - `ros2 pkg prefix nav2_bt_navigator` 与 `nav2_behaviors` 均返回 `/opt/ros/humble`。
  - `GET http://192.168.1.11:8787/api/status` 返回 HTTP 200。
- 真实 PC proxy → 上位机 → Nav2 执行复验：
  - 请求：`POST http://127.0.0.1:8787/api/robot-control/nav2/goal/execute?baseUrl=http%3A%2F%2F192.168.1.11%3A8787`
  - body：`goal_frame_id=map, goal_x=0.8, goal_y=0, goal_yaw=0, result_timeout_s=4, confirm_navigation_execution=true`
  - PC 返回：`proxy_status=execution_forwarded`、`remote_http_status=200`、`hard_dangerous_true_fields=[]`。
  - key values：`status=goal_succeeded`、`nav2_goal_execution_proven=true`、`goal_accepted=true`、`result_received=true`、`result_status=succeeded`、`feedback_sample_count=8`、`robot_control_executed=true`、`delivery_success=false`。
  - 上位机 latest：`/api/nav2/goal/execution/latest` 读回 `status=goal_succeeded`、`action=/navigate_to_pose`、`managed_runtime.lifecycle_ready.source=lifecycle_manager_log`、`cleanup.ok=true`。
  - 结束后 `pgrep`/`lsof` 未发现 Nav2 runtime、ESP32 bridge、LiDAR driver 或 `/dev/ttyS5`/`/dev/ttyACM0` 残留占用。

## 剩余风险

- 本轮证明完整 Nav2 `NavigateToPose` 路线执行链路可从 PC 高级入口触发并成功返回，但它不是送达闭环；`delivery_success=false` 仍保持不变。
- delivery success 还需要路线任务到达、垃圾投放/到桶确认、现场 operator report 和交付结果收口，不能仅由 Nav2 goal succeeded 自动翻 true。
- AMCL 初始位姿日志仍可能出现一次短暂 TF 外推 warning，但本轮最终 lifecycle active、goal accepted/result succeeded，未阻塞路线执行。
