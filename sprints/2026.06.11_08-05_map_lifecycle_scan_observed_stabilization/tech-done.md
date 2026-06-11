# Map Lifecycle Scan Observed Stabilization Tech Done

sprint_type: micro

## 自主能力目标和本轮抓手

本轮目标是稳定真实上位机 no-motion map lifecycle：PC 或 upper API 触发
`map save` / `map start/save` 时，必须真实观测 `/scan`、观测 `/map`、保存并列出
YAML/PGM，而不是因为一次性 `/scan` echo 抖动导致 PC 代理 fail-closed。

抓手是修复 `o3_map_lifecycle_proof.py` 的 `/scan` clean proof 采样方式：保留
`scan_once_observed=true` 必须成立的要求，但改为 sensor_data QoS + 两次独立 echo
尝试，并把每次尝试写入 artifact。

安全边界：本轮没有发布 `/cmd_vel`，没有调用 `/api/base/manual`，没有打开 WAVE
ROVER UART `/dev/ttyS5`。LiDAR 使用 `/dev/ttyACM0 @ 150000`，该设备信息来自项目
真实上位机 evidence；WAVE ROVER/Orange Pi 硬件事实入口仍是
`docs/vendor/VENDOR_INDEX.md`。

## 实际改动

- `onboard/scripts/o3_map_lifecycle_proof.py`
  - 新增 `observe_topic_once(...)`。
  - `/scan` proof 从单次 `timeout 8 ros2 topic echo --once /scan` 改为最多 2 次
    `ros2 topic echo --once --qos-profile sensor_data /scan`。
  - artifact 新增 `attempts`、`attempt_count`、
    `stable_observation_strategy=retry_topic_echo_once`。
  - 移除不存在的 LiDAR vendor path 记录，改为保留 `docs/vendor/VENDOR_INDEX.md`
    并补充 `field_evidence_sources`。
- `onboard/scripts/upper_robot_api.py`
  - map lifecycle artifact expected material 补充 `/scan once`。
- `onboard/tests/test_map_lifecycle_proof_helper.py`
  - 新增静态测试，锁定 `/scan` 重试与 sensor_data QoS 采样策略。
- `docs/hardware/board_sensor_stack_smoke.md`
- `docs/navigation/fixed_route_workflow.md`
- `docs/product/pc_tools_workstation.md`
- `sprints/2026.06.11_08-05_map_lifecycle_scan_observed_stabilization/artifacts/*`

## 根因判断

上一轮综合 smoke 失败不是因为 SLAM 全链路不可用。失败 artifact
`sprints/2026.06.11_07-35_pc_integrated_real_evidence_smoke/artifacts/14_remote_map_proof_latest.json`
显示：

- `/scan` 已出现在 `ros2 topic list`。
- `/map` echo 成功。
- `save_map` 成功。
- `pc_integrated_smoke_20260611_0735.yaml/.pgm` 已生成。
- 只有单次 `timeout 8 ros2 topic echo --once /scan` 空输出超时。

因此根因是 `/scan_once_observed` 的一次性 echo 采样窗口对 DDS discovery、LiDAR
聚合首帧和进程启动时序过敏。修复后不绕过 `/scan_once_observed`，而是让 clean proof
在同一 runtime 内有两次真实 echo 机会，并显式使用 sensor_data QoS。

## 本地验证结果

```text
python3 -m unittest onboard.tests.test_upper_robot_api onboard.tests.test_map_lifecycle_proof_helper
Ran 24 tests in 0.089s
OK
```

```text
python3 -m py_compile onboard/scripts/upper_robot_api.py onboard/scripts/o3_map_lifecycle_proof.py
OK
```

```text
git diff --check
OK
```

## 真实上位机 direct smoke

部署目标：`root@192.168.1.11 -p 37878`。

- 同步文件：`onboard/scripts/o3_map_lifecycle_proof.py`、
  `onboard/scripts/upper_robot_api.py`。
- 远端 `python3 -m py_compile onboard/scripts/upper_robot_api.py onboard/scripts/o3_map_lifecycle_proof.py` 通过。
- `systemctl restart trashbot-upper-robot-api.service` 后
  `systemctl is-active trashbot-upper-robot-api.service` 返回 `active`。

direct smoke artifact：

- `artifacts/direct_map_save_before_fix.json`
  - 修复前本轮复现基线已 clean pass：`command_result.ok=true`，
    `scan_once_observed=true`，`map_once_observed=true`。
  - 该结果说明问题是抖动，不是持续性硬失败。
- `artifacts/direct_map_save_after_fix.json`
  - `map_name=scan_stabilize_fixed_20260611_0756`
  - `status=map_once_artifact_metadata_observed`
  - `command_result.ok=true`
  - `scan_once_observed=true`
  - `map_once_observed=true`
  - `map_file_observed=true`
  - `map_metadata_observed=true`
  - `commands.scan_once.command=timeout 8 ros2 topic echo --once --qos-profile sensor_data /scan`
  - `commands.scan_once.attempt_count=1`
  - `commands.scan_once.stable_observation_strategy=retry_topic_echo_once`
- `artifacts/direct_map_list_after_fix.json`
  - 列出 `scan_stabilize_fixed_20260611_0756.yaml`
  - 列出 `scan_stabilize_fixed_20260611_0756.pgm`

## PC proxy smoke

本地 workstation API 启动在 `http://127.0.0.1:8794`，对
`http://192.168.1.11:8787` 代理。

- `artifacts/pc_proxy_map_save_after_fix.json`
  - `map_name=pc_proxy_scan_stabilize_20260611_0758`
  - `proxy_status=lifecycle_forwarded`
  - `remote_http_status=200`
  - `command_result.executed=true`
  - `command_result.ok=true`
  - `blocked_reasons=[]`
- `artifacts/remote_map_proof_latest_after_proxy.json`
  - `scan_once_observed=true`
  - `map_once_observed=true`
  - `map_file_observed=true`
  - `map_metadata_observed=true`
  - `commands.scan_once.attempt_count=1`
- `artifacts/remote_map_list_after_proxy.json`
  - 远端完整 list 列出 `pc_proxy_scan_stabilize_20260611_0758.yaml`
  - 远端完整 list 列出 `pc_proxy_scan_stabilize_20260611_0758.pgm`
- `artifacts/pc_proxy_map_list_after_fix.json`
  - `proxy_status=lifecycle_forwarded`
  - `remote_http_status=200`
  - `map_count=18`
  - PC 摘要 `map_names` 列出新 YAML，但因摘要截断未列出新 PGM。

## cleanup/safety 证据

- `artifacts/remote_final_cleanup.log`
  - `trashbot-upper-robot-api.service=active`
  - `lsof /dev/ttyS5 /dev/ttyACM0` 无输出
  - `fuser -v /dev/ttyS5 /dev/ttyACM0` 无占用输出
  - `o3_map_lifecycle_proof.py`、`learn.launch`、`slam_toolbox`、
    `lidar_driver`、`static_transform_publisher` 无残留
- 本地 workstation API 8794 已关闭，端口无 LISTEN。

## 剩余风险和下一步建议

- PC proxy `map/list` 当前是截断摘要，地图数量多时可能无法同时显示新 YAML 与同名
  PGM；本轮未改 PC server，因为文件范围未包含该文件。完整 YAML/PGM 证据以远端
  `/api/map/list` 和 latest proof `proof.map_files` 为准。
- 本轮未评估地图质量，不证明地图可导航。
- 本轮未证明 AMCL、Nav2 planner/controller、fixed-route execution、真实运动、WAVE
  ROVER HIL、robot ACK 或 delivery success。
- 下一步建议：授权 PC server map list 摘要扩展，或继续推进同图 AMCL/Nav2 no-motion
  planner readiness，让 O3 现场验证 lane 消费本轮 clean map lifecycle material。
