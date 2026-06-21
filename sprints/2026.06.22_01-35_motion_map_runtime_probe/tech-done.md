# 2026.06.22 01:35 Motion And Map Runtime Probe

sprint_type: micro

## 实际改动

- 修复 `onboard/src/ros2_trashbot_nav/ros2_trashbot_nav/map_recorder.py` 的 PGM 保存语义：OccupancyGrid `0` 现在保存为 `254` free cell，`-1` 仍保存为 `205` unknown，occupied 仍保存为 `0`。
- 新增 `onboard/src/ros2_trashbot_nav/test/test_map_recorder_static.py`，锁定 free cell 不能再被写成 unknown。
- 已把修复同步到真实上位机 `/root/rober/onboard/src/ros2_trashbot_nav/.../map_recorder.py`；上位机 runtime import 确认 `free_254=true`、`free_205=false`。

## 真实验证

- PC 连接：`38_pc_summary_after_map_fix.json` 显示 `robot_api_connection.status=readable`、`loaded_count=13`、`blocked_count=0`、`dangerous_true_fields=[]`。
- 受控移动：`10_pc_first_jog_for_scan_delta.json` 和 `28_pc_first_jog_during_manual_mapping.json` 均为 `proxy_status=command_forwarded`、`remote_http_status=200`、`clamped_speed_mps=0.08`、`clamped_duration_ms=800`。
- LiDAR delta：`14_scan_delta_metrics.json` 显示 `paired_bins=162`、`median_abs_diff_m=1.735`、`changed_bin_ratio=1.0`，超过 `docs/hardware/field_hil_execution_pack.md` 的保守阈值。
- Operator report：`18_operator_report_lidar_delta_response.json` 已提交 `physical_motion_lidar_delta_proven=true` 和 `scan_delta_ref=/root/rober/onboard/runtime/scan_delta/20260622_0135/14_scan_delta_metrics.json`；仍保持 `wheel_feedback_lr_nonzero_proven=false`、`delivery_success=false`。
- 修复前地图：`23_field_first_jog_map.pgm` 与 `31_manual_motion_map.pgm` 都只有 occupied/unknown，没有 free cells。
- 修复后地图：`34_pc_map_list_after_free_pixel_fix.json` 显示 `map_quality_summary.status=has_usable_map`、`usable_map_count=1`、`map_usable_for_navigation=true`、`map_needs_rebuild=false`。
- 修复后像素复核：`37_fixed_free_cells_map_pixel_review.json` 显示 `free_pixel_count=394`、`occupied_pixel_count=48`、`unknown_pixel_count=32582`、`has_free_cells=true`。
- Runtime cleanup：手动建图 runtime 的 `slam_toolbox`、`map_recorder`、`lidar_driver` 子进程已清理，`/dev/ttyACM0` 已释放。

## 软件验证

- `python3 -m unittest onboard.src.ros2_trashbot_nav.test.test_map_recorder_static`：通过，确认 free cell 保存语义不会回退。
- `python3 -m py_compile onboard/src/ros2_trashbot_nav/ros2_trashbot_nav/map_recorder.py onboard/scripts/motion_evidence_material_review.py`：通过。
- `cd pc-tools/workstation && npm run test`：通过，2 个测试文件、99 个测试。
- `cd pc-tools/workstation && npm run build`：通过。
- `bash onboard/scripts/docker_humble_build.sh`：通过，`Summary: 6 packages finished [48.4s]`；该证据边界为 `software_proof_docker_only`，不等于真实 HIL。
- `python3 -m unittest discover onboard/src/ros2_trashbot_nav/test`：在 macOS Python 3.9 下失败，根因是既有测试链路导入 `route_contracts.py` 时遇到 Python 3.10 写法 `str | None`，不是本轮 `map_recorder.py` 改动引入；Docker/Humble 的 Python 3.10 构建已通过。

## 剩余风险

- `wheel_feedback_lr_nonzero_proven=false`：当前 `/api/base/feedback-samples/latest` 只保存 T1001 观察摘要，没有原始 L/R 轮速值，不能证明轮速非零。
- `delivery_success=false`：本轮只证明低速 first-jog、LiDAR delta 和可用 free-cell map，不证明真实路线导航或投放任务完成。
- 当前可用地图是小范围现场地图，只有 394 个 free pixels；后续仍需要更长路线采集、route.csv/keyframe、Nav2 path/runtime 验证。
