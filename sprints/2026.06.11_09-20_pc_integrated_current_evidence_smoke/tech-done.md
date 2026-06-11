# PC Integrated Current Evidence Smoke

sprint_type: micro

Owner: `full-stack-software-engineer`

Run time: 2026-06-11 09:20-09:35 CST

## 本轮目标

- 使用 PC workstation proxy `http://127.0.0.1:8795` 连接真实上位机 `http://192.168.1.11:8787`，重新采集 07:35 后已过时的综合实机 evidence。
- 覆盖普通用户首屏简洁 invariant、Camera、Radar、Map、Localization/Nav2 path、Stop/manual gate 和 cleanup。
- 本轮禁止任何真实非零运动、NavigateToPose、`/cmd_vel`、远端 `/api/base/manual` 绕过 gate。

## 实际改动

- 新增本 sprint 留档：
  - `sprints/2026.06.11_09-20_pc_integrated_current_evidence_smoke/tech-done.md`
- 新增 evidence artifacts：
  - `sprints/2026.06.11_09-20_pc_integrated_current_evidence_smoke/artifacts/**`
- 未修改 `pc-tools/workstation/src/**`、测试、`onboard/**`、`docs/vendor/**`、ROS2、硬件串口、launch、运动控制代码或 PC 普通首屏风格。
- 未更新 `docs/product/pc_tools_workstation.md` 或 `pc-tools/README.md`，因为本轮只采集当前 evidence，没有改变 UI/API 契约。

## 综合 Smoke 结果

入口汇总：

- `artifacts/70_integrated_current_evidence_summary.json`

结果：

| 项目 | 结果 | 关键证据 |
| --- | --- | --- |
| 首屏 invariant | pass | `52_chrome_cdp_retry_first_screen.json` |
| Camera | pass with near-black risk | `53_chrome_cdp_retry_camera_frame_opened.json`、`56_upper_camera_health_after_chrome_retry_close.json` |
| Radar | pass after direct long warmup | `41_pc_radar_after_direct_scan_proof_refresh.json`、`44_pc_radar_after_direct_compact_summary.json` |
| Map | pass | `31_retry_pc_map_save.json`、`32_retry_pc_map_list.json`、`33_retry_upper_map_proof_latest.json` |
| Localization/Nav2 path | pass | `34_retry_pc_nav2_proof_refresh.json`、`35_retry_upper_nav2_proof_latest.json` |
| Stop/manual gate | pass | `16_pc_base_stop.json`、`17_pc_manual_attempt_expected_reject.json` |
| Cleanup | pass | `68_final_cleanup_readback_clean.log`、`69_final_filtered_target_process_check.log` |

## 首屏简洁 Invariant

Chrome/CDP artifact：`52_chrome_cdp_retry_first_screen.json`

- 标题：`Rober 小车控制台`，通过。
- 五卡片：`小车连接`、`实时画面`、`雷达`、`地图`、`移动/导航`，全部可见。
- 默认 `高级诊断` 和 `高级工具` 均未展开。
- 默认首屏未出现工程词：`Route Debug`、`source=software_proof`、`proof_status=not_proven`、`safe_to_control=false`、`readback`、`HIL`、`cmd_vel`、`/api/base/manual`、`Nav2`、`检查路径`、`保存地图`、方向点动词。

## Camera

Artifacts：

- `53_chrome_cdp_retry_camera_frame_opened.json`
- `53_chrome_cdp_retry_camera_frame_canvas.png`
- `53_chrome_cdp_retry_camera_opened.png`
- `54_upper_camera_health_during_chrome_retry_open.json`
- `55_chrome_cdp_retry_camera_cleanup_after_close.json`
- `56_upper_camera_health_after_chrome_retry_close.json`
- `57_chrome_cdp_retry_camera_summary.json`

关键结果：

- Browser video 元素：
  - `srcObjectExists=true`
  - `readyState=4`
  - `videoWidth=640`
  - `videoHeight=480`
  - `requestVideoFrameCallbackObserved=true`
  - `presentedFrames=1`
- 上位机打开中：`active_peer_connections=1`。
- 关闭后：`active_peer_connections=0`、`active_peer_ids=[]`。
- 关闭后 video：`srcObjectExists=false`、`readyState=0`、`videoWidth=0`、`videoHeight=0`。

风险：

- Canvas 采样 `nonBlackPixels=0`、`averageRgbSum=1`，仍是近黑画面。结论只能是“真实 WebRTC video frame 到达浏览器 video 元素”，不能声明已看清现场内容。

## Radar

Artifacts：

- 第一轮 PC proxy：`11_pc_radar_scan_proof_refresh.json`
- retry PC proxy：`29_retry_pc_radar_scan_proof_refresh.json`
- direct 长 warmup 诊断：`37_direct_upper_radar_long_warmup_refresh.json`、`39_direct_radar_long_warmup_summary.json`
- direct 诊断后 PC proxy：`41_pc_radar_after_direct_scan_proof_refresh.json`、`44_pc_radar_after_direct_compact_summary.json`
- final cleanup：`68_final_cleanup_readback_clean.log`

关键结果：

- 第一轮和普通 retry 的 PC proxy `POST /api/robot-control/radar/scan-proof/refresh` 只证明了 `tf_observed=true`，`scan_once_observed=false`、`raw_packet_once_observed=false`、`scan_hz_observed=false`。
- direct upper 长 warmup 诊断 `POST /api/radar/scan-proof/refresh` with `runtime_warmup_s=15` 后，上位机状态变为：
  - `latest_scan_proof_state=scan_once_hz_raw_packet_tf_observed`
  - `scan_once=true`
  - `scan_hz=true`
  - `raw_packet_once=true`
  - `tf=true`
- 随后 PC proxy 重新执行 radar start -> scan-proof refresh -> radar stop：
  - `proxy_status=refresh_forwarded`
  - `remote_http_status=200`
  - `scan_once_observed=true`
  - `scan_hz_observed=true`
  - `raw_packet_once_observed=true`
  - `tf_observed=true`
  - `hard_dangerous_true_fields=[]`
- 清场后 `/dev/ttyACM0` 无 `lsof` / `fuser` 占用。

风险：

- PC proxy 固定 6s warmup 在冷态不稳定，首次未拿到 `/scan`/raw/hz。最终 PC proxy pass 依赖 direct 长 warmup 先刷新 fresh LiDAR proof；这不是运动风险，但说明 radar cold-start evidence window 仍需后续收敛。
- `blocked_reasons` 仍保留 `scan_continuity_not_observed`，本轮只证明一次性 scan/raw/hz/TF，不证明长时间连续雷达稳定。

## Map

Artifacts：

- 初始 map save：`13_pc_map_save.json`
- retry map save/list/proof：`31_retry_pc_map_save.json`、`32_retry_pc_map_list.json`、`33_retry_upper_map_proof_latest.json`
- final readback：`61_final_upper_map_list.json`、`62_final_upper_map_proof_latest.json`

关键结果：

- 初始安全 map name：`pc_integrated_current_20260611_0920`。初始 proxy save 返回 502/fail-closed，但后续 map list 已包含该 YAML。
- retry map name：`pc_integrated_current_retry_20260611_0920`。
- retry PC proxy map save：
  - `proxy_status=lifecycle_forwarded`
  - `remote_http_status=200`
  - `command_result.ok=true`
- PC proxy map list：
  - `proxy_status=lifecycle_forwarded`
  - `remote_http_status=200`
  - `map_count=22`
  - list 包含 `pc_integrated_current_20260611_0920.yaml` 和 `pc_integrated_current_retry_20260611_0920.yaml`
- latest proof：
  - `status=map_once_artifact_metadata_observed`
  - `scan_once_observed=true`
  - `map_once_observed=true`
  - `map_file_observed=true`
  - `map_metadata_observed=true`

## Localization / Nav2 Path

Artifacts：

- 初始 PC proxy：`15_pc_nav2_proof_refresh.json`
- retry PC proxy：`34_retry_pc_nav2_proof_refresh.json`
- retry direct latest：`35_retry_upper_nav2_proof_latest.json`
- final readback：`64_final_upper_nav2_proof_latest.json`

关键结果：

- 初始 PC proxy 已到 `planner_server_active=true`，但 `path_generated=false`。
- retry PC proxy clean pass：
  - `proxy_status=refresh_forwarded`
  - `remote_http_status=200`
  - `path_generated=true`
  - `path_generation_succeeded=true`
  - `path_point_count=31`
  - `planner_server_active=true`
  - `hard_dangerous_true_fields=[]`
- direct latest proof 同步显示：
  - `path_generated=true`
  - `path_generation_succeeded=true`
  - `path_point_count=31`
  - `planner_server_active=true`
- 禁止项未发生：
  - 未调用 `/cmd_vel`
  - 未调用 NavigateToPose
  - 未调用 `/api/base/manual`
  - 未调用 `/api/nav2/start`

## Stop / Manual Gate

Artifacts：

- `16_pc_base_stop.json`
- `17_pc_manual_attempt_expected_reject.json`
- `65_final_upper_operator_report.json`
- `66_final_upper_base_status.json`

关键结果：

- PC proxy stop：
  - `proxy_status=command_forwarded`
  - `remote_http_status=200`
  - `robot_control_executed=false`
  - `operator_report_preflight.status=not_required_for_stop`
- 低速 non-stop manual attempt：
  - request：`direction=forward`、`speed=0.05`、`duration_ms=400`、`confirm_hil_checklist=true`
  - HTTP 400
  - `proxy_status=command_rejected`
  - `failure_reason=operator_report_preflight_required`
  - `remote_http_status=null`
  - `robot_control_executed=false`
  - missing fields：`external_video_recorded`、`visible_content_proven`、`wheel_feedback_lr_nonzero_proven`、`physical_motion_lidar_delta_proven`

是否发生真实非零运动：no。

本轮没有远端 `/api/base/manual` 执行，没有 `/cmd_vel`，没有 NavigateToPose，没有任何真实非零运动。

## Cleanup

Artifacts：

- `58_final_upper_status.json`
- `59_final_upper_camera_health.json`
- `60_final_upper_radar_status.json`
- `61_final_upper_map_list.json`
- `62_final_upper_map_proof_latest.json`
- `63_final_upper_localize_proof_latest.json`
- `64_final_upper_nav2_proof_latest.json`
- `65_final_upper_operator_report.json`
- `66_final_upper_base_status.json`
- `68_final_cleanup_readback_clean.log`
- `69_final_filtered_target_process_check.log`

关键结果：

- 上位机 `trashbot-upper-robot-api.service=active`。
- Camera health：`status=ready`、`active_peer_connections=0`、`active_peer_ids=[]`。
- 本地 PC API `8795` 已关闭，`lsof -nP -iTCP:8795 -sTCP:LISTEN` 无输出。
- 目标机 helper filtered process check 无输出。
- `/dev/ttyS5`：`lsof` / `fuser` 无输出。
- `/dev/ttyACM0`：`lsof` / `fuser` 无输出。

## 验证命令和结果

- PC workstation API：
  - `PORT=8795 npm run api`
  - 输出：`pc-tools workstation API listening on http://127.0.0.1:8795`
- 真实 upper readbacks：
  - `/api/status`、`/api/camera/health`、`/api/radar/status`、`/api/map/list`、`/api/map/proof/latest`、`/api/localize/proof/latest`、`/api/nav2/proof/latest`、`/api/operator/report`、`/api/base/status`
  - final readbacks 全部 HTTP 200，见 `58_final_upper_readbacks_timing.log`。
- Browser/Chrome smoke：
  - Chrome/CDP 首屏 invariant、camera open frame evidence、canvas screenshot、cleanup 均已保存。
- PC proxy API calls：
  - radar start / scan-proof refresh / radar stop
  - map save / map list
  - nav2 proof refresh
  - base stop
  - low-speed manual attempt with checklist true, expected local reject
- SSH cleanup：
  - `root@192.168.1.11 -p 37878`
  - 见 `68_final_cleanup_readback_clean.log` 和 `69_final_filtered_target_process_check.log`。
- `git diff --check`：
  - 通过，无输出。

## 失败定位和剩余风险

- Camera：真实帧进入浏览器 video 元素，但画面近黑；需要现场检查 DV20 摄像头输入、遮挡、朝向、曝光或选择的 `/dev/video1` 是否正确。
- Radar：冷态 PC proxy 固定 6s warmup 未稳定采到 `/scan`/raw/hz；direct 15s warmup 后 PC proxy 能读到完整关键字段。后续应把 PC proxy/upper radar proof 的冷态窗口或 start/warmup 逻辑收敛，避免依赖人工 direct warmup。
- Radar 仍不证明长时间连续稳定，`scan_continuity_not_observed` 仍保留。
- Map：本轮只证明 YAML/PGM 和 map metadata 生成，不证明地图质量、闭环建图质量或可用于真实导航。
- Nav2：本轮只证明 managed no-motion path generation，`path_point_count=31`；不证明 NavigateToPose、控制器执行、避障、固定路线执行或送达成功。
- Manual gate：本轮证明 stop 可达和 non-stop manual 被本地 gate 拒绝；不证明真实 HIL pass。

## 完成前反思

- 文件范围符合本轮限制：只新增 sprint 目录和 artifacts，没有修改禁止范围。
- 需求覆盖：首屏、camera、radar、map、nav2、stop/manual gate、cleanup、upper readbacks、Chrome/CDP screenshots 和 `git diff --check` 均已覆盖。
- 没有隐藏失败：camera 近黑、radar cold-start 不稳定和 `scan_continuity_not_observed` 均保留为风险。
- 没有发生真实非零运动：final base/status 仍为 `robot_control_executed=false`、`safe_to_control=false`、`sends_motion_commands=false`。
