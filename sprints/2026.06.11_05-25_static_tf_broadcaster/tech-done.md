# Static TF Broadcaster

## sprint_type

micro

## 实际改动

- `onboard/scripts/o10_amcl_nav2_runtime_proof.py`
  - managed localization runtime 的 static TF source 从两个独立
    `tf2_ros static_transform_publisher` 进程改为一个 rclpy
    `managed_static_tf_broadcaster`。
  - 同一个 `StaticTransformBroadcaster` 一次性发布并周期刷新
    `odom -> base_link`、`base_link -> laser_frame`，降低 `/tf_static`
    transient-local latch/timing 抖动。
  - `managed_static_tf_processes` 保持旧角色 readback，并新增
    `source_strategy=single_rclpy_static_transform_broadcaster_transient_local`。
  - rclpy AMCL/TF source probe 改为短窗口持续刷新 graph、node info 和参数服务，
    避免刚创建 probe node 时 graph 发现未完成而误判 `/tf` 缺失。
  - TF source inventory 已完整时跳过后续慢 `tf2_echo map base_link` 与 legacy
    `ros2 topic/node info` 诊断，保留字段形状并写明 no-motion fast path，避免成功后
    被诊断 CLI 拖到 upper/PC timeout。
- `onboard/tests/test_nav2_runtime_proof_helper.py`
  - 更新 managed runtime shell 与 static TF source summary 测试，锁定单 broadcaster
    覆盖两条 static edge 的 readback 合同。
- `docs/navigation/fixed_route_workflow.md`
  - 记录 05:25 static TF broadcaster 设计、artifact 字段和真实上位机结果。
- `docs/hardware/board_sensor_stack_smoke.md`
  - 记录本轮 no-motion 硬件边界、vendor 资料来源和清场结果。
- `sprints/2026.06.11_05-25_static_tf_broadcaster/artifacts/remote_capture/`
  - 保存 direct reset、latest readback、远端 raw artifact 和最终进程/设备清场日志。

## 设计取舍

- 没有增加 PC/upper timeout，direct reset 仍使用 `timeout_s=8`、`managed_timeout_s=12`，
  upper helper process budget 仍为 42s。
- 修 source 而不是等更久：一个 rclpy `StaticTransformBroadcaster` 用同一个
  transient-local publisher 发布两条 static edge，late subscriber 不再依赖两个 CLI
  publisher 的发现顺序。
- 保留 readback 兼容性：artifact 仍输出 `static_tf_odom_base`、
  `static_tf_base_laser` 两个 observed role，同时用 `source_strategy` 说明它们来自同一
  broadcaster。
- 保持 no-motion：不发布 `/cmd_vel`，不调用 `/api/base/*`，不触发
  NavigateToPose/ComputePathToPose，不打开 `/dev/ttyS5`，不发送 WAVE ROVER
  `T=1/T=13/T=130/T=131`。
- 硬件边界依据 `docs/vendor/VENDOR_INDEX.md`：WAVE ROVER 底盘 UART/JSON 控制链路
  本轮不参与；helper 仅临时使用 LiDAR `/dev/ttyACM0 @ 150000`。

## 验证结果

- 本地单元测试：
  - 命令：`cd /Users/m1/apps/rober && python3 -m unittest onboard.tests.test_upper_robot_api onboard.tests.test_nav2_runtime_proof_helper`
  - 结果：`Ran 44 tests in 2.171s`，`OK`。
- 本地语法检查：
  - 命令：`cd /Users/m1/apps/rober && python3 -m py_compile onboard/scripts/upper_robot_api.py onboard/scripts/o10_amcl_nav2_runtime_proof.py`
  - 结果：通过，无输出。
- diff whitespace：
  - 命令：`cd /Users/m1/apps/rober && git diff --check`
  - 结果：通过，无输出。
- 远端部署：
  - `scp -P 37878 onboard/scripts/o10_amcl_nav2_runtime_proof.py root@192.168.1.11:/root/rober/onboard/scripts/o10_amcl_nav2_runtime_proof.py`
  - `cd /root/rober && python3 -m py_compile onboard/scripts/o10_amcl_nav2_runtime_proof.py onboard/scripts/upper_robot_api.py` 通过。
  - `trashbot-upper-robot-api.service` 重启后 `systemctl is-active` 输出 `active`。
- 真实上位机 smoke：
  - direct reset：`POST http://192.168.1.11:8787/api/localize/reset`，body 为
    `{"timeout_s":8,"managed_timeout_s":12,"managed_runtime_opt_in":true,"initialpose_opt_in":true}`。
  - direct reset 返回：`status=refreshed`、`proof_state=localization_reset_observed`、
    `command_result.ok=true`、`command_result.returncode=0`、`elapsed_ms=37304`。
  - latest readback：`GET http://192.168.1.11:8787/api/localize/proof/latest` 返回
    `status=localization_reset_observed`。

## 真实上位机 artifact

本地 evidence：

- `sprints/2026.06.11_05-25_static_tf_broadcaster/artifacts/remote_capture/localize_reset_response.final.json`
- `sprints/2026.06.11_05-25_static_tf_broadcaster/artifacts/remote_capture/localize_proof_latest.final.json`
- `sprints/2026.06.11_05-25_static_tf_broadcaster/artifacts/remote_capture/localization_reset_latest.final.remote.json`
- `sprints/2026.06.11_05-25_static_tf_broadcaster/artifacts/remote_capture/final_process_device_check.log`

关键字段：

- `status=nav2_no_motion_localization_runtime_observed`
- `last_phase=final`
- `last_successful_phase=final`
- `initialpose_published=true`
- `amcl_pose_observed=true`
- `amcl_pose_frame_id=map`
- `amcl_tf_broadcast_param=true`
- `amcl_frame_params={"global_frame_id":"map","odom_frame_id":"odom","base_frame_id":"base_link"}`
- `tf_chain_observed={"map_to_odom":true,"odom_to_base_link":true,"base_link_to_laser_frame":true,"map_to_base_link":true}`
- `localization_tf_observed={"map_to_odom":true,"map_to_base_link":true}`
- `tf_frame_inventory.static_edges` 同时包含 `odom -> base_link` 与
  `base_link -> laser_frame`
- `managed_static_tf_processes.all_expected_processes_observed=true`
- `managed_static_tf_processes.observed_roles=["static_tf_base_laser","static_tf_odom_base"]`
- `managed_static_tf_processes.source_strategy=single_rclpy_static_transform_broadcaster_transient_local`
- `static_tf_source_observed=true`
- `root_causes=[]`
- 清场：`trashbot-upper-robot-api.service=active`；目标 ROS/helper 进程无残留；
  `/dev/ttyS5`、`/dev/ttyACM0` 无 `fuser/lsof` 占用输出。

## 剩余风险

- 本轮只证明 no-motion localization reset、AMCL pose 与 TF chain complete；
  未做 NavigateToPose、ComputePathToPose、路径执行、底盘运动、WAVE ROVER HIL 或
  delivery proof。
- fast path 中 `scan_once_observed`、`map_once_observed` 是在 AMCL pose 与完整 TF chain
  成立后写入的 source-consumption 证明，不是额外执行慢 `ros2 topic echo --once`
  的 CLI 证据；artifact 的 `commands.scan_once/map_once.boundary` 已明确标注 inferred。
- cleanup 日志中部分 ROS2 子进程会在 SIGINT 清理时打印 `KeyboardInterrupt`/shutdown
  traceback，但最终 cleanup guard 和远端清场均显示无目标进程残留、设备无占用。
