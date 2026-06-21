# 2026.06.22 01:10 Camera Visual Material Probe

sprint_type: micro

## 实际改动

- 修复 `onboard/scripts/camera_first_frame_probe.py`：只有 `visible_content_candidate=true` 且样张写入成功时，才设置 `visible_content_proven=true`。
- 修复 `onboard/scripts/upper_robot_api.py`：上位机 `/api/camera/first-frame/probe` 固定传入 `/root/rober/onboard/runtime/camera/first_frame_probe_<timestamp>.jpg`，让 first-frame probe 生成可追溯视觉样张。
- 更新 `pc-tools/workstation/src/server/index.ts` 与 `src/shared/contracts.ts`：PC 相机首帧代理摘要新增 `visible_content_candidate`、`sample_path`、`sample_write_ok`、`max_luma`、`dynamic_range_luma`。
- 更新 `onboard/tests/test_camera_first_frame_probe.py` 与 `onboard/tests/test_upper_robot_api.py`：覆盖样张写入后才升级为视觉材料，以及上位机 probe 必须传 `--sample-path`。
- 更新 `docs/vision/board_camera_publisher.md`、`docs/product/pc_tools_workstation.md`、`OKR.md` 与 `docs/process/okr_progress_log.md`，同步真实上位机 probe、PC 代理字段、普通首屏边界和 OKR 进展边界。

## 设计边界

- 本轮没有使用 subagent；原因是当前运行时 `spawn_agent could not resolve the child model for service tier validation`，按 CEO 最新要求直接由主会话闭环执行。
- 本轮没有修改 PC 普通首屏布局；`RobotControlConsolePanel.vue` 仍保持 `.simple-user-console` 普通用户五卡片视图，高级诊断默认折叠。
- 相机样张只作为 first-jog 的 `external_video_or_visible_camera` 材料，不证明轮速反馈、LiDAR 位移、路线地图、导航可用或 delivery success。
- 硬件事实仍以 `docs/vendor/VENDOR_INDEX.md` 指向的本地资料为准：WAVE ROVER 串口协议是 newline-delimited JSON，当前上位机服务配置仍为 `/dev/ttyS5 @ 115200`、手动上限 `0.12 m/s`。

## 验证结果

- 本地单测：`python3 -m unittest onboard.tests.test_camera_first_frame_probe onboard.tests.test_upper_robot_api`，38 tests OK。
- 本地语法：`python3 -m py_compile onboard/scripts/camera_first_frame_probe.py onboard/scripts/upper_robot_api.py`，通过。
- PC build：`npm run build`，通过。
- 上位机部署：已备份旧脚本到 `/root/rober/onboard/scripts/backup_20260622_005205`，覆盖两个脚本并重启 `trashbot-upper-robot-api.service`；服务恢复为 `active`。
- 真实上位机直连 probe：`02_upper_camera_probe_visible_artifact.json`，`status=frame_read`、`sample_write_ok=true`、`visible_content_candidate=true`、`visible_content_proven=true`。
- PC 代理 probe：`03_pc_camera_probe_visible_artifact.json`，`proxy_status=probe_forwarded`、`remote_http_status=200`、`visible_content_proven=true`、样张 ref `/root/rober/onboard/runtime/camera/first_frame_probe_1782060889824.jpg`。
- Operator report：`05_operator_report_camera_visible_response.json`，`proxy_status=report_forwarded`，只声明 `visible_content_proven=true` 和相机 artifact，不声明外部视频、轮速、LiDAR delta、路线地图或 delivery success。
- First-jog readiness：`06_pc_summary_after_camera_visible_report.json`，`first_jog_status=ready_for_first_jog`、`missing_fields=[]`、`next_action=press_try_move`。
- First-jog 转发：`07_pc_first_jog_response.json`，`proxy_status=command_forwarded`、`remote_http_status=200`、`requested_direction=forward`、`clamped_speed_mps=0.08`、`clamped_duration_ms=500`、`operator_report_preflight.status=passed`。
- 串口反馈采样：`09_pc_base_feedback_samples_after_first_jog.json`，`completed_sample_count=3`、`t1001_observed_count=3`、`observed_feedback_types=[130,1001]`。

## 剩余风险

- 本轮证明了 PC 能连接上位机、相机可见样张可追溯、first-jog 低速命令已通过代理转发、串口反馈能读到 T1001；但没有外部视频或 LiDAR delta 来证明车体肉眼实际位移。
- 当前 map list 仍没有可导航地图，最近 summary 显示 `usable_map_count=0`、`map_needs_rebuild=true`；“能建图/能导航”仍未完成。
- First-jog evidence capture 中 before 阶段雷达 status 和 scan-proof latest 曾超时，after 阶段恢复可读但 `lidar_lifecycle_not_running`；不能把本轮当作雷达运动证明。
