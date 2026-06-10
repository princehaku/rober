# Localization Preflight Budget

## sprint_type

micro

## 实际改动

- `onboard/scripts/o10_amcl_nav2_runtime_proof.py`
  - 将定位 reset 主证据路径重排为：managed runtime start/wait -> `ros2` 轻量 preflight -> `/initialpose` -> `/amcl_pose` -> localization TF -> package/graph/lifecycle 诊断。
  - 将 package check 从逐包 `ros2 pkg prefix` 改为单次 source 后的 `ros2 pkg list` 批量诊断；若主定位路径先消耗完预算，partial artifact 会保留 `package_check_mode=deferred_after_localization_main_path` 和每个期望包的 unknown availability。
  - 将 managed runtime wait 从慢 lifecycle CLI 改为轻量 `ros2 node list` 轮询，完整 lifecycle 只作为后续诊断。
  - 将 TF probe 改为短窗口 `tf2_echo`，并在 TF 失败或中断时写入 `Localization TF` 下层 root cause。
- `onboard/scripts/upper_robot_api.py`
  - timeout fallback 保留 helper partial artifact 中的 package availability/check mode 字段，`/api/localize/proof/latest` 顶层 readback 同步暴露这些字段。
- `onboard/tests/test_nav2_runtime_proof_helper.py`
  - 增加/更新 package check 单次 `ros2 pkg list`、initialpose 优先于 package/graph/topic 诊断、timeout partial 保留 package 字段的测试。
- `onboard/tests/test_upper_robot_api.py`
  - 更新 localize latest partial readback 的 package 字段断言。
- `docs/navigation/fixed_route_workflow.md`
  - 记录 localization reset phase artifact 新字段与 package 诊断延后策略。
- `docs/hardware/board_sensor_stack_smoke.md`
  - 记录 no-motion 定位 reset 不触碰 WAVE ROVER 底盘 UART 的边界，以及 package preflight 不再阻塞主定位路径。

## 验证结果

- 本地单元测试：
  - 命令：`cd /Users/m1/apps/rober && python3 -m unittest onboard.tests.test_upper_robot_api onboard.tests.test_nav2_runtime_proof_helper`
  - 结果：`Ran 39 tests in 2.162s`，`OK`。
- 本地语法检查：
  - 命令：`cd /Users/m1/apps/rober && python3 -m py_compile onboard/scripts/upper_robot_api.py onboard/scripts/o10_amcl_nav2_runtime_proof.py`
  - 结果：通过，无输出。
- diff whitespace：
  - 命令：`cd /Users/m1/apps/rober && git diff --check`
  - 结果：通过，无输出。
- 真实上位机 smoke：
  - 部署：`scp -P 37878 onboard/scripts/o10_amcl_nav2_runtime_proof.py onboard/scripts/upper_robot_api.py root@192.168.1.11:/root/rober/onboard/scripts/`，远端 `python3 -m py_compile` 通过，`trashbot-upper-robot-api.service` 重启后为 `active`。
  - 调用：`POST http://127.0.0.1:8787/api/localize/reset`，随后 `GET http://127.0.0.1:8787/api/localize/proof/latest`。
  - 最终本地 evidence：
    - `sprints/2026.06.11_04-05_localization_preflight_budget/artifacts/remote_capture/localize_reset_response_final2.json`
    - `sprints/2026.06.11_04-05_localization_preflight_budget/artifacts/remote_capture/localize_proof_latest_final2.json`
    - `sprints/2026.06.11_04-05_localization_preflight_budget/artifacts/remote_capture/localization_reset_latest.final2.remote.json`
    - `sprints/2026.06.11_04-05_localization_preflight_budget/artifacts/remote_capture/final_process_device_check_final2.log`
  - 关键字段：`status=blocked_with_root_cause`，`last_phase=interrupted`，`last_successful_phase=amcl_pose_probe`，`current_command=ros2 pkg list`，`initialpose_publish_attempted=true`，`initialpose_published=true`，`amcl_pose_observed=true`，`localization_tf_observed.map_to_odom=true`，`localization_tf_observed.map_to_base_link=false`，`managed_runtime_started=true`，`managed_runtime_cleanup_ok=false`。
  - package 字段：`package_check_mode=deferred_after_localization_main_path`，`package_availability` 中 5 个期望包为 `null`，表示 package 诊断被主定位证据路径延后且未在外层预算内完成；早期同轮验证 `localization_reset_latest.rerun.remote.json` 已证明批量 package 诊断可返回 5 个包均为 true。
  - root causes：`Localization TF: map_to_base_link_not_observed`，`helper process: sigint_before_final_artifact`，`upper API helper process: helper_process_timeout_after_partial_artifact`。
  - 清场：`final_process_device_check_final2.log` 显示 `service=active`，目标 ROS/managed runtime 进程无残留，`/dev/ttyS5` 与 `/dev/ttyACM0` 的 `lsof/fuser` 无占用输出。

## 剩余风险

- 本轮已经解决 package preflight 阻塞主定位证据路径的问题：真实 smoke 已从 `ros2 pkg prefix nav2_amcl` 前进到 `/initialpose`、`/amcl_pose` 和 TF。
- 当前下一层 blocker 是 localization TF：`map->odom` 在最终 readback 中被判定 observed，但 `map->base_link` 未观测；下一轮应聚焦 AMCL TF 输出、static `odom->base_link` 与 `tf2_echo`/buffer timing，而不是继续处理 package preflight。
- 为保持 PC/upper timeout 预算，package availability 在最终 canonical artifact 中被标记为 deferred；若下一轮需要 package 诊断与 TF 诊断同时完整收口，应进一步减少 managed runtime wait/CLI 启动成本，不能简单拉长超过 PC proxy 可等待预算。
- 本轮未发送 `/cmd_vel`，未调用 `/api/base/*`，未触发 `NavigateToPose`，未打开 `/dev/ttyS5`，未发送 WAVE ROVER `T=1/T=13/T=130/T=131`。
