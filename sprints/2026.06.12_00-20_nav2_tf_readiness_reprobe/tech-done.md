# Nav2 TF Readiness Reprobe

sprint_type: micro

## 目标

本轮直接按 CEO 要求去掉 subagent 调用，由主会话闭环修复上位机 Nav2 no-motion proof 中
`/tf_topic_missing`、`map_to_odom_not_observed`、`base_link_to_laser_frame_not_observed`
误停在 source probe 窗口的问题。设计边界是只改 no-motion 证据采集，不改 PC 普通用户简易界面，
不请求 `/api/base/manual`、不发布 `/cmd_vel`、不打开 `/dev/ttyS5`。

硬件事实来源先读 `docs/vendor/VENDOR_INDEX.md`：WAVE ROVER 底盘控制是 UART newline JSON，
ROS2 Orange Pi 目标不能硬编码 vendor Raspberry Pi UART 路径。本轮只触碰 LiDAR/Nav2 proof，
不改底盘串口控制。

## 实际改动

- `onboard/scripts/o10_amcl_nav2_runtime_proof.py`
  - `collect_amcl_rclpy_probe()` 不再因为 `/amcl/get_parameters` 暂时不可用就提前返回；
    参数服务晚到时仍继续采样 graph、`/tf` 和 transient-local `/tf_static`。
  - source probe 窗口从 2s 提升为 4s；fallback `tf2_echo` 四段链路统一使用已有
    `TF_ECHO_SHELL_TIMEOUT_S` / `TF_ECHO_PROCESS_TIMEOUT_S` 宽窗口。
  - 保持 no-motion proof 边界：path generation 只调用 planner action，不调用 controller、
    NavigateToPose 或底盘串口。
- `onboard/tests/test_nav2_runtime_proof_helper.py`
  - 增加 AMCL 参数服务晚到时仍保留 `/tf_static` source 证据的回归测试。
  - 增加 TF fallback 宽窗口回归测试。
- `docs/product/pc_tools_workstation.md`
  - 追加真实上位机复测状态：TF/localization blocker 已推进到 planner empty path。

## 验证结果

- 本地单元测试：
  - `python3 -m unittest onboard.tests.test_nav2_runtime_proof_helper`
  - 结果：30 tests OK。
- 本地语法检查：
  - `python3 -m py_compile onboard/scripts/o10_amcl_nav2_runtime_proof.py onboard/tests/test_nav2_runtime_proof_helper.py`
  - 结果：通过。
- 上位机连通与部署：
  - `ssh -p 37878 root@192.168.1.11 'echo upper-ok && hostname && pwd'`
  - 结果：`upper-ok`，主机 `op-z3-b6.home`。
  - `scp -P 37878 onboard/scripts/o10_amcl_nav2_runtime_proof.py root@192.168.1.11:/root/rober/onboard/scripts/o10_amcl_nav2_runtime_proof.py`
  - 远端 `python3 -m py_compile onboard/scripts/o10_amcl_nav2_runtime_proof.py` 通过。
- 上位机 direct helper no-motion proof：
  - artifact：`sprints/2026.06.12_00-20_nav2_tf_readiness_reprobe/artifacts/02_direct_helper_nav2_after_tf_readiness_fix.clean.json`
  - 结果：`/tf=true`、`/tf_static=true`、`map_to_odom=true`、
    `odom_to_base_link=true`、`base_link_to_laser_frame=true`、`map_to_base_link=true`。
  - 结果：`amcl_param_probe_ok=true`，AMCL frame 参数为 `map/odom/base_link`，
    `amcl_tf_root_cause=source_inventory_observed`。
  - 结果：`path_generation_service_available=true`、goal accepted，但
    `path_generation_succeeded=false`、`path_point_count=0`。
  - 结果：`managed_runtime_cleanup_ok=true`、`safe_to_control=false`、
    `sends_motion_commands=false`、`uses_base_uart=false`。
- 上位机 API refresh/latest：
  - artifact：`sprints/2026.06.12_00-20_nav2_tf_readiness_reprobe/artifacts/03_upper_runtime_nav2_latest_after_api_refresh.json`
  - artifact：`sprints/2026.06.12_00-20_nav2_tf_readiness_reprobe/artifacts/04_upper_api_nav2_latest_after_tf_readiness_fix.json`
  - summary：`sprints/2026.06.12_00-20_nav2_tf_readiness_reprobe/artifacts/05_upper_api_nav2_latest_summary.json`
  - 结果：HTTP refresh 返回 200；latest artifact 与 direct helper 一致，TF 全链路通过。
- 清场：
  - `ps` 未发现 managed runtime 残留进程。
  - `fuser -v /dev/ttyS5 /dev/ttyACM0` 未显示占用者。

## 剩余风险

- 本轮没有证明真实导航移动或送达成功；proof 仍是 no-motion 软件证据。
- 当前 Nav2 新 blocker 已收敛为 `compute_path_to_pose_empty_path`，需要下一轮定位 planner/costmap
  为什么 goal accepted 但返回空 path。
- Camera 仍停在 first-frame timeout，没有证明 PC 可见实时图传。
- API `latest` 顶层仍按产品安全口径返回 `not_proven`；完整 root cause 在
  `latest_result.proof` 中，本轮未改接口形状。
