# AMCL TF Source Diagnostics

## sprint_type

micro

## 实际改动

- `onboard/scripts/o10_amcl_nav2_runtime_proof.py`
  - 在 `/initialpose` 与 `/amcl_pose` 后、慢 `tf2_echo` 前新增 `tf_source_probe`。
  - 新增稳定 artifact 字段：`tf_topics_observed`、`tf_static_observed`、`tf_frame_inventory`、`amcl_pose_frame_id`、`amcl_node_publishers`、`amcl_node_subscribers`、`amcl_tf_broadcast_param`、`amcl_frame_params`、`map_frame_observed`、`odom_frame_observed`、`amcl_tf_root_cause`。
  - `tf_chain_observed` 优先采信轻量 `/tf`、`/tf_static` inventory；只有缺边时才用短 `tf2_echo` 补充错误文本，避免 `tf2_echo odom base_link` 消耗主路径预算。
- `onboard/scripts/upper_robot_api.py`
  - timeout fallback、`/api/localize/reset` 与 `/api/localize/proof/latest` 透传 AMCL/TF source/timing 字段。
- `onboard/tests/test_nav2_runtime_proof_helper.py`
  - 增加 AMCL `map->odom` 未广播但 static TF 存在时的 source/root-cause 单元测试。
- `onboard/tests/test_upper_robot_api.py`
  - 增加 localization readback 对 AMCL/TF source/timing 字段的断言。
- `docs/navigation/fixed_route_workflow.md`
  - 记录 localization reset source snapshot 字段与 no-motion 边界。
- `docs/hardware/board_sensor_stack_smoke.md`
  - 记录 AMCL/TF source diagnostics 和 WAVE ROVER 安全边界。

## 设计取舍

- 不通过拉长 PC/upper budget 掩盖问题；保持 upper helper process timeout cap 不变。
- 把关键 source/timing 证据前置到慢诊断前：先看 `/tf`、`/tf_static`、AMCL node info 和 AMCL 参数，再决定是否需要短 `tf2_echo`。
- `/tf_static` 已能证明的 static edge 不再依赖 `tf2_echo`，避免上一轮卡在 `tf2_echo odom base_link` 后丢失更关键的 AMCL source 证据。
- 本轮不发布 `/cmd_vel`，不调用 `/api/base/*`，不触发 NavigateToPose，不打开 `/dev/ttyS5`，不发送 WAVE ROVER `T=1/T=13/T=130/T=131`。

## 验证结果

- 本地单元测试：
  - 命令：`cd /Users/m1/apps/rober && python3 -m unittest onboard.tests.test_upper_robot_api onboard.tests.test_nav2_runtime_proof_helper`
  - 结果：`Ran 42 tests in 2.166s`，`OK`。
- 本地语法检查：
  - 命令：`cd /Users/m1/apps/rober && python3 -m py_compile onboard/scripts/upper_robot_api.py onboard/scripts/o10_amcl_nav2_runtime_proof.py`
  - 结果：通过，无输出。
- diff whitespace：
  - 命令：`cd /Users/m1/apps/rober && git diff --check`
  - 结果：通过，无输出。

## 真实上位机 smoke

- 目标：`root@192.168.1.11 -p 37878`。
- 部署：`scp -P 37878 onboard/scripts/o10_amcl_nav2_runtime_proof.py onboard/scripts/upper_robot_api.py root@192.168.1.11:/root/rober/onboard/scripts/`。
- 远端语法检查：`cd /root/rober && python3 -m py_compile onboard/scripts/upper_robot_api.py onboard/scripts/o10_amcl_nav2_runtime_proof.py` 通过。
- `trashbot-upper-robot-api.service` 重启后 `systemctl is-active` 输出 `active`。
- direct `POST http://192.168.1.11:8787/api/localize/reset` 返回结构化 `blocked_with_root_cause`。
- direct `GET http://192.168.1.11:8787/api/localize/proof/latest` 返回同一份 AMCL/TF source/timing readback。
- 本地 artifacts：
  - `sprints/2026.06.11_04-45_amcl_tf_source/artifacts/remote_capture/localize_reset_response.final.json`
  - `sprints/2026.06.11_04-45_amcl_tf_source/artifacts/remote_capture/localize_proof_latest.final.json`
  - `sprints/2026.06.11_04-45_amcl_tf_source/artifacts/remote_capture/localization_reset_latest.final.remote.json`
  - `sprints/2026.06.11_04-45_amcl_tf_source/artifacts/remote_capture/final_process_device_check.log`

关键字段：

- `status=blocked_with_root_cause`
- `last_phase=interrupted`
- `last_successful_phase=tf_source_probe`
- `initialpose_published=true`
- `amcl_pose_observed=true`
- `localization_tf_observed.map_to_odom=false`
- `localization_tf_observed.map_to_base_link=false`
- `tf_chain_observed.map_to_odom=false`
- `tf_chain_observed.odom_to_base_link=false`
- `tf_chain_observed.base_link_to_laser_frame=false`
- `tf_chain_observed.map_to_base_link=false`
- `tf_topics_observed={"/tf": true, "/tf_static": true}`
- `tf_static_observed=false`
- `tf_frame_inventory.topic_types` 包含 `/tf`、`/tf_static`、`/amcl_pose`、`/map`、`/scan`、`/initialpose`
- `tf_frame_inventory.dynamic_edges=[]`
- `tf_frame_inventory.static_edges=[]`
- `tf_frame_inventory.command_statuses.topic_list=0`
- `tf_frame_inventory.command_statuses.tf_static=124`
- `amcl_pose_frame_id=map`
- `amcl_tf_broadcast_param=null`
- `amcl_frame_params.global_frame_id=null`
- `amcl_frame_params.odom_frame_id=null`
- `amcl_frame_params.base_frame_id=null`
- `map_frame_observed=false`
- `odom_frame_observed=false`
- `amcl_tf_root_cause=amcl_map_to_odom_tf_not_observed_on_tf`
- `tf_failure_classification.blocking_segment=map_to_odom`
- `tf_failure_classification.reason=amcl_map_to_odom_tf_not_observed_on_tf`
- `managed_runtime_started=true`
- `managed_runtime_cleanup_ok=false`
- `localization_reset_observed=false`
- 清场：`trashbot-upper-robot-api.service=active`；`pgrep` 只匹配本次检查命令本身；`/dev/ttyS5` 和 `/dev/ttyACM0` 的 `fuser/lsof` 无占用输出。

## 剩余风险

- 本轮仍未让 `map->odom` 或 `map->base_link` 变为 true。下一层 root cause 是 AMCL `/amcl_pose` 已发布且 frame 为 `map`，但 `/tf` source snapshot 没有观测到 `map -> odom` dynamic edge。
- `/tf_static` topic 存在，但 2 秒 transient-local echo 返回 124，未观测到 `odom -> base_link` 或 `base_link -> laser_frame` static edge；这是次级 blocker，优先级低于缺 `map->odom`。
- AMCL 参数 readback 为 `null`，因为本轮为保证 source 证据早于慢诊断，未再把 param/node info 放进前置阻塞窗口。下一轮若继续下钻，应使用 rclpy 轻量节点或更短独立 probe 获取 `/amcl` 参数，而不是串行 ROS CLI。
- helper 仍被 upper timeout 中断，`managed_runtime_cleanup_ok=false` 来自 helper partial；upper wrapper 和最终清场日志显示目标 ROS 进程、`/dev/ttyS5`、`/dev/ttyACM0` 已清场。
- 本轮仍未做运动、NavigateToPose、路径生成、HIL 或 delivery proof；安全字段保持 false。
