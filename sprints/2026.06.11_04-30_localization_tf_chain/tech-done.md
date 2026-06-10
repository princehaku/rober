# Localization TF Chain

## sprint_type

micro

## 实际改动

- `onboard/scripts/o10_amcl_nav2_runtime_proof.py`
  - 新增稳定 `tf_chain_observed` 字段，分段记录 `map_to_odom`、`odom_to_base_link`、`base_link_to_laser_frame`、`map_to_base_link`。
  - 新增 `tf_chain_diagnostics` 与 `tf_failure_classification`，把 `map->base_link` 失败下钻到缺 `map->odom`、缺 `odom->base_link`、frame 命名不一致或 tf2 timeout/timing。
  - 将 TF probe 改为每段结束后立即写 partial artifact；即使 upper timeout 打断后续 probe，也保留前序 TF 结果与 root cause。
  - 保持 managed runtime 的 static TF 发布边界：`odom -> base_link` 与 `base_link -> laser_frame`；不启动 controller、BT navigator、NavigateToPose 或运动链路。
- `onboard/scripts/upper_robot_api.py`
  - timeout fallback 保留 helper partial 中的 `tf_chain_observed`、`tf_chain_diagnostics`、`tf_failure_classification`。
  - `/api/localize/reset` 与 `/api/localize/proof/latest` 顶层 readback 同步暴露 TF 链诊断字段。
- `onboard/tests/test_nav2_runtime_proof_helper.py`
  - 增加 TF 链分类单元测试，覆盖缺 `odom->base_link` 与 frame 命名不一致。
- `onboard/tests/test_upper_robot_api.py`
  - 增加 localize reset/latest 对 `tf_chain_observed` 与 `tf_failure_classification` 的 readback 断言。
- `docs/navigation/fixed_route_workflow.md`
  - 记录 localization reset readback 的四段 TF 诊断字段与 no-motion 边界。
- `docs/hardware/board_sensor_stack_smoke.md`
  - 记录 `odom -> base_link`、`base_link -> laser_frame` static TF 诊断要求，以及 WAVE ROVER 底盘安全边界。

## 设计取舍

- 没有拉长 PC/upper 预算；`process_timeout_s` 仍由上位机限制在 42s，低于 PC proxy 46s。
- 优先把 TF source 和时序拆开：先观测 `map->odom` 与 `odom->base_link`，再判断完整 `map->base_link`，最后补 `base_link->laser_frame` static TF 诊断。
- 每段 TF probe 后立即写 partial，避免后续 `tf2_echo` 或 package 诊断被 timeout 时丢失前序证据。
- 本轮只允许 `/initialpose` 与 AMCL/TF 诊断；未发布 `/cmd_vel`，未调用 `/api/base/*`，未触发 NavigateToPose，未打开 `/dev/ttyS5`。

## 验证结果

- 本地单元测试：
  - 命令：`cd /Users/m1/apps/rober && python3 -m unittest onboard.tests.test_upper_robot_api onboard.tests.test_nav2_runtime_proof_helper`
  - 结果：`Ran 41 tests in 2.159s`，`OK`。
- 本地语法检查：
  - 命令：`cd /Users/m1/apps/rober && python3 -m py_compile onboard/scripts/upper_robot_api.py onboard/scripts/o10_amcl_nav2_runtime_proof.py`
  - 结果：通过，无输出。
- diff whitespace：
  - 命令：`cd /Users/m1/apps/rober && git diff --check`
  - 结果：通过，无输出。
- 真实上位机 smoke：
  - 目标：`root@192.168.1.11 -p 37878`。
  - 部署：`scp -P 37878 onboard/scripts/o10_amcl_nav2_runtime_proof.py onboard/scripts/upper_robot_api.py root@192.168.1.11:/root/rober/onboard/scripts/`。
  - 远端 `python3 -m py_compile onboard/scripts/upper_robot_api.py onboard/scripts/o10_amcl_nav2_runtime_proof.py` 通过。
  - `trashbot-upper-robot-api.service` 重启后 `systemctl is-active` 为 `active`。
  - direct `POST http://127.0.0.1:8787/api/localize/reset` 与 `GET http://127.0.0.1:8787/api/localize/proof/latest` 均返回结构化 readback。
  - 最终清场：`trashbot-upper-robot-api.service=active`，目标 ROS/managed runtime 进程无残留，`lsof/fuser /dev/ttyS5 /dev/ttyACM0` 无占用输出。

## 真实上位机关键字段

- artifact：
  - `sprints/2026.06.11_04-30_localization_tf_chain/artifacts/remote_capture/localize_reset_response.final.json`
  - `sprints/2026.06.11_04-30_localization_tf_chain/artifacts/remote_capture/localize_proof_latest.final.json`
  - `sprints/2026.06.11_04-30_localization_tf_chain/artifacts/remote_capture/localization_reset_latest.final.remote.json`
  - `sprints/2026.06.11_04-30_localization_tf_chain/artifacts/remote_capture/final_process_device_check.log`
- `status=blocked_with_root_cause`
- `last_phase=interrupted`
- `last_successful_phase=amcl_pose_probe`
- `initialpose_published=true`
- `amcl_pose_observed=true`
- `localization_tf_observed.map_to_odom=false`
- `localization_tf_observed.map_to_base_link=false`
- `tf_chain_observed.map_to_odom=false`
- `tf_chain_observed.odom_to_base_link=false`
- `tf_chain_observed.base_link_to_laser_frame=false`
- `tf_chain_observed.map_to_base_link=false`
- `tf_failure_classification.map_to_base_link=blocked_by_missing_map_to_odom`
- `tf_failure_classification.reason=frame_missing_or_name_mismatch`
- root cause 首项：`Localization TF / map_to_odom_not_observed / detail=frame_missing_or_name_mismatch`
- `blocked_commands_not_sent` 包含 `T=1/T=13/T=130/T=131`、`/cmd_vel`、`/api/base/manual`、`/api/nav2/start`、`/api/nav2/stop`、`navigate_to_pose`、`compute_path_to_pose`。
- `blocked_devices_not_opened=["/dev/ttyS5"]`

## 剩余风险

- 本轮没有让 `map->base_link` 变为 true；下一层 root cause 已从上一轮的 `map_to_base_link_not_observed` 下钻为 `map_to_odom_not_observed`，detail 为 `frame_missing_or_name_mismatch`。下一轮应聚焦 AMCL 是否实际广播 `map->odom`、`tf2_echo map odom` 的 frame/source/timing，而不是继续处理最终 `map->base_link` 布尔值。
- `managed_runtime_cleanup_ok=false` 来自 helper partial：helper 被 upper timeout 中断前未进入自身 cleanup phase。upper wrapper 的 cleanup_result 和最终 `final_process_device_check.log` 已证明本轮目标进程与 `/dev/ttyS5`、`/dev/ttyACM0` 清场成功。
- `base_link->laser_frame` 仍未形成最终 observed 证据，因为本轮在 `odom->base_link` probe 期间被 upper timeout 打断；不过 root cause 已优先落到更上游的 `map->odom` 缺失。
- 本轮仍未做运动、NavigateToPose、路径生成、HIL 或 delivery proof；安全字段保持 false。
