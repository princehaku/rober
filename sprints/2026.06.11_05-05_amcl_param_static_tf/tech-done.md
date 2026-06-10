# AMCL Param And Static TF Source

## sprint_type

micro

## 实际改动

- `onboard/scripts/o10_amcl_nav2_runtime_proof.py`
  - 新增 rclpy AMCL 参数、node graph、TF topic inventory probe，避免用多条 ROS CLI 串行消耗 upper/PC 主路径预算。
  - 新增并填实 `amcl_param_probe_ok`、`amcl_node_info_observed`、`amcl_log_tail`、`managed_static_tf_processes`、`static_tf_source_observed`、`tf_source_root_cause_detail`、`amcl_broadcast_conditions`。
  - managed runtime 启动日志按 role 记录 LiDAR、static TF、map_server、amcl、lifecycle_manager；cleanup 前记录 static TF publisher 进程。
  - managed wait 改为 rclpy graph 查询，避免 `ros2 node list` 在真实板上多次 2s timeout。
- `onboard/scripts/upper_robot_api.py`
  - timeout fallback、`/api/localize/reset`、`/api/localize/proof/latest` 透传新增 AMCL/static TF source 字段。
- `onboard/tests/test_nav2_runtime_proof_helper.py`
  - 增加 AMCL rclpy 参数覆盖空 CLI marker、static TF 进程角色识别、managed shell role 日志断言。
- `docs/navigation/fixed_route_workflow.md`
  - 记录 05:05 后 `/api/localize/reset` 的 AMCL 参数、broadcast 条件和 static TF source readback 合同。
- `docs/hardware/board_sensor_stack_smoke.md`
  - 记录 no-motion AMCL params/static TF source 诊断字段和 WAVE ROVER 安全边界。

## 设计取舍

- 不延长 upper/PC helper timeout；把慢 `ros2 param`、`ros2 node info`、`ros2 topic echo /tf*` 迁移为短生命周期 rclpy probe。
- AMCL 参数通过 `/amcl/get_parameters` 读取，graph publisher/subscriber 和 `/tf`、`/tf_static` 通过 rclpy graph/subscription 获取。
- static TF 不只看 topic 结果，同时记录 managed process group 中两个 `static_transform_publisher` 角色，区分“进程没启动”和“进程存在但 transient-local 采样漏边”。
- 安全边界保持 no-motion：不发布 `/cmd_vel`，不调用 `/api/base/*`，不触发 NavigateToPose，不打开 `/dev/ttyS5`，不发送 WAVE ROVER `T=1/T=13/T=130/T=131`。

## 验证结果

- 本地单元测试：
  - 命令：`cd /Users/m1/apps/rober && python3 -m unittest onboard.tests.test_upper_robot_api onboard.tests.test_nav2_runtime_proof_helper`
  - 结果：`Ran 44 tests in 2.178s`，`OK`。
- 本地语法检查：
  - 命令：`cd /Users/m1/apps/rober && python3 -m py_compile onboard/scripts/upper_robot_api.py onboard/scripts/o10_amcl_nav2_runtime_proof.py`
  - 结果：通过，无输出。
- diff whitespace：
  - 命令：`cd /Users/m1/apps/rober && git diff --check`
  - 结果：通过，无输出。
- 远端部署：
  - `scp -P 37878 onboard/scripts/o10_amcl_nav2_runtime_proof.py onboard/scripts/upper_robot_api.py root@192.168.1.11:/root/rober/onboard/scripts/`
  - `cd /root/rober && python3 -m py_compile onboard/scripts/upper_robot_api.py onboard/scripts/o10_amcl_nav2_runtime_proof.py` 通过。
  - `trashbot-upper-robot-api.service` 重启后 `systemctl is-active` 输出 `active`。

## 真实上位机 smoke

- direct reset：`POST http://192.168.1.11:8787/api/localize/reset`，body 为 `{"timeout_s":8,"managed_timeout_s":12,"managed_runtime_opt_in":true,"initialpose_opt_in":true}`。
- readback：`GET http://192.168.1.11:8787/api/localize/proof/latest`。
- 本地 artifacts：
  - `sprints/2026.06.11_05-05_amcl_param_static_tf/artifacts/remote_capture/localize_reset_response.final.json`
  - `sprints/2026.06.11_05-05_amcl_param_static_tf/artifacts/remote_capture/localize_proof_latest.final.json`
  - `sprints/2026.06.11_05-05_amcl_param_static_tf/artifacts/remote_capture/localization_reset_latest.final.remote.json`
  - `sprints/2026.06.11_05-05_amcl_param_static_tf/artifacts/remote_capture/final_process_device_check.log`

关键字段：

- `status=blocked_with_root_cause`
- `last_phase=interrupted`
- `last_successful_phase=package_checks`
- `initialpose_published=true`
- `amcl_pose_observed=true`
- `amcl_pose_frame_id=map`
- `amcl_frame_params={"global_frame_id":"map","odom_frame_id":"odom","base_frame_id":"base_link"}`
- `amcl_tf_broadcast_param=true`
- `amcl_param_probe_ok=true`
- `amcl_node_info_observed=true`
- `amcl_node_publishers` 包含 `/amcl_pose`、`/particle_cloud`、`/tf`
- `amcl_node_subscribers` 包含 `/initialpose`、`/map`、`/scan`
- `managed_static_tf_processes.all_expected_processes_observed=true`
- `managed_static_tf_processes.observed_roles=["static_tf_base_laser","static_tf_odom_base"]`
- `static_tf_source_observed=true`
- `tf_topics_observed={"/tf":true,"/tf_static":true}`
- `tf_static_observed=true`
- `tf_frame_inventory.dynamic_edges` 包含 `map -> odom`
- `tf_frame_inventory.static_edges` 本轮最终只包含 `base_link -> laser_frame`
- `amcl_tf_root_cause=odom_to_base_link_static_tf_not_observed`
- `localization_tf_observed.map_to_odom=true`
- `localization_tf_observed.map_to_base_link=false`
- `tf_chain_observed.map_to_odom=true`
- `tf_chain_observed.base_link_to_laser_frame=true`
- `tf_chain_observed.odom_to_base_link=false`
- `tf_chain_observed.map_to_base_link=false`
- 清场：`trashbot-upper-robot-api.service=active`；`pgrep` 只匹配本次检查命令本身；`/dev/ttyS5`、`/dev/ttyACM0` 无 `fuser/lsof` 占用输出。

## 剩余风险

- `map->odom` 已修复/观测，AMCL 参数实际生效；本轮没有完成完整 `map->base_link`，因为最终 `/tf_static` transient-local 采样只观测到一个 static edge。
- 两个 `static_transform_publisher` 进程都存在，日志也显示启动；最终 root cause 已从 AMCL broadcast 下钻为 static TF source timing/QoS/采样一致性：`odom->base_link` 本轮未进入 `/tf_static` inventory。
- helper 仍被 upper timeout 打断在后续诊断阶段，artifact 为 partial + wrapper fallback；但关键 AMCL/static TF source 字段已在打断前落盘。
- 本轮仍未做运动、NavigateToPose、路径生成、HIL 或 delivery proof；安全字段保持 false。
