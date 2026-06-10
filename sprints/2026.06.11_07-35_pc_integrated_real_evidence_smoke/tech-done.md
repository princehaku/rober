# PC Integrated Real Evidence Smoke

sprint_type: micro

Owner: `full-stack-software-engineer`

Run time: 2026-06-11 07:35 CST

## 实际改动

- 新增本轮 evidence artifact 目录：`sprints/2026.06.11_07-35_pc_integrated_real_evidence_smoke/artifacts/`。
- 新增综合 smoke 汇总与解释：
  - `00_integrated_smoke_summary.json`
  - `17_interpretation_summary.json`
- 新增真实上位机与 PC 代理原始响应：
  - `01_summary_before.json` / `11_summary_after.json`
  - `02_remote_camera_health_before.json` / `12_remote_camera_health_after.json`
  - `03_remote_camera_devices.json`
  - `04_radar_start.json`
  - `05_radar_scan_proof_refresh.json`
  - `06_radar_stop.json`
  - `07_map_save.json`
  - `08_map_list.json`
  - `09_nav2_no_motion_proof_refresh.json`
  - `10_base_stop_only.json`
  - `13_remote_radar_status_after.json`
  - `14_remote_map_proof_latest.json`
  - `15_remote_nav2_proof_latest.json`
  - `16_remote_localize_proof_latest.json`
- 新增浏览器/DOM evidence：
  - `browser_dom_first_screen_and_advanced_tools.json`
  - `browser_camera_preview_state.json`
- 新增最终清场读回：
  - `final_cleanup_readback.log`

本轮没有修改 `pc-tools/workstation/src/**`、`pc-tools/workstation/test/**`、`docs/product/pc_tools_workstation.md` 或 `pc-tools/README.md`，因此不运行 PC build/test/lint。

## Smoke 结果

### UI first screen

- 通过。
- Browser DOM artifact：`browser_dom_first_screen_and_advanced_tools.json`。
- 默认首屏标题为 `Rober 小车控制台`。
- 默认首屏五卡片为：`小车连接`、`实时画面`、`雷达`、`地图`、`移动/导航`。
- `高级工具` 与 `高级诊断` 默认关闭。
- 默认可见文本未命中工程禁词：`Route Debug`、`source=software_proof`、`proof_status=not_proven`、`safe_to_control=false`、`readback`、`HIL`、`cmd_vel`、`开始建图`、`保存地图`、`前进/后退/左转/右转`。
- 展开 `高级工具` 后，工程 tabs `路线 / 控制台 / 预览 / 证据 / 硬件 / 数据 / 安全边界` 可见。

### Camera

- 部分通过，不能声明浏览器可见视频帧成功。
- Browser 页面真实执行 Start/Stop 后，详情区显示：
  - `preview_status=streaming`
  - `failure_reason=none`
  - `ice_connection_state=connected`
  - `video_track_state=live`
  - 有真实 `peer_id`
  - Stop 后 `preview_status=stopped_by_user`
  - Stop 后 `cleanup_status=peer_closed:closed`
- 远端 cleanup 后 `/api/camera/health` 返回：
  - `status=ready`
  - `active_peer_connections=0`
  - `active_peer_ids=[]`
- 远端 `/api/camera/devices` 返回 `/dev/video0`、`/dev/video1`、`/dev/video2` 可读写。
- 缺口：浏览器 `<video>` 在本轮采样中仍为 `hasSrcObject=false`、`videoWidth=0`、`videoHeight=0`，所以只证明 signaling/track state/peer cleanup，未证明页面可见画面帧。

### Radar

- 通过。
- PC 代理按顺序调用：
  - `POST /api/robot-control/radar/start`
  - `POST /api/robot-control/radar/scan-proof/refresh`
  - `POST /api/robot-control/radar/stop`
- 关键结果：
  - start `proxy_status=lifecycle_forwarded`，remote HTTP 200。
  - scan refresh `proxy_status=refresh_forwarded`。
  - scan key values：`scan_once_observed=true`、`scan_hz_observed=true`、`raw_packet_once_observed=true`、`tf_observed=true`。
  - stop `proxy_status=lifecycle_forwarded`，remote HTTP 200。
  - `hard_dangerous_true_fields=[]`。
- 非运动边界：本链路未调用 `/api/base/manual`、`/cmd_vel` 或底盘点动。

### Map

- 产物证明通过；PC lifecycle save 正确 fail-closed。
- PC 代理调用 `POST /api/robot-control/map/save`，`map_name=pc_integrated_smoke_20260611_0735`。
- 远端生成并列出：
  - `/root/rober/onboard/runtime/maps/pc_integrated_smoke_20260611_0735.yaml`
  - `/root/rober/onboard/runtime/maps/pc_integrated_smoke_20260611_0735.pgm`
- 远端 latest 显示：
  - `map_once_observed=true`
  - `map_file_observed=true`
  - `map_metadata_observed=true`
- PC proxy 返回 `proxy_status=lifecycle_failed`，原因是 helper root cause：`/scan_once_not_observed`。这是正确的 fail-closed 结果，不伪装成完整 map lifecycle pass。

### Localization / Path

- Blocked with root cause。
- PC 代理调用 `POST /api/robot-control/nav2/proof/refresh`，未调用 Nav2 start、NavigateToPose、`/cmd_vel` 或 base manual。
- 代理返回 `proxy_status=refresh_forwarded`，但 latest artifact 为 `blocked_with_root_cause`：
  - `path_generated=false`
  - `path_generation_succeeded=false`
  - `path_point_count=0`
  - root causes：`sigint_before_final_artifact`、`helper_process_timeout_after_partial_artifact`
  - 细节中还显示 `tf_source_probe_not_executed`。
- `/api/localize/proof/latest` 仍有历史定位 runtime 读回，`localization_status=nav2_no_motion_localization_runtime_observed`；但本轮不能声明新的 path readiness 通过。

### Stop / No-motion Safety

- 通过。
- 本轮唯一底盘类动作是 `POST /api/robot-control/base/stop`，远端 endpoint 为 `/api/base/stop`，HTTP 200。
- `robot_control_executed=false`。
- `00_integrated_smoke_summary.json` 记录：
  - `forbidden_nonzero_motion_calls_from_this_script=[]`
  - `dangerous_true_hits=[]`
- 本轮调用清单没有 `/api/base/manual`，没有 `/cmd_vel`，没有 `forward/back/left/right` 请求。
- artifact 全局 grep 出现 `/api/base/manual` 和 `/cmd_vel` 的位置均为安全边界文本、blocked commands 列表或 false 字段，不是本轮真实调用。
- 上位机 final cleanup/readback：
  - `trashbot-upper-robot-api.service=active`
  - `/dev/ttyS5`：`lsof` / `fuser` 无占用输出
  - `/dev/ttyACM0`：`lsof` / `fuser` 无占用输出
  - `pgrep` 未发现 `o3_map_lifecycle_proof`、`o10_amcl_nav2_runtime_proof`、`lidar_driver`、`slam_toolbox`、`map_server`、`amcl`、`planner_server`、`controller_server` 残留

## 验证命令

- 本地 workstation API 启动在空闲端口：
  - `PORT=8793 npm run api`
  - 结果：`pc-tools workstation API listening on http://127.0.0.1:8793`
- Browser/DOM smoke：
  - 通过，artifact：`browser_dom_first_screen_and_advanced_tools.json`
- 真实上位机综合 smoke：
  - 通过采集，artifact：`00_integrated_smoke_summary.json` 与 `17_interpretation_summary.json`
- final cleanup/readback：
  - 通过采集，artifact：`final_cleanup_readback.log`
- `git diff --check`：
  - 通过，无输出。

## 失败定位

- Camera：页面 WebRTC 状态显示 streaming/connected/live，peer cleanup 成功，但 `<video>` 未出现 `srcObject` 或像素尺寸；本轮不把它记为可见画面成功。
- Map：YAML/PGM 与 metadata 已生成，但 helper root cause 为 `/scan_once_not_observed`，PC proxy 因此 `lifecycle_failed`。
- Localization/path：本轮 Nav2 no-motion refresh 没有生成路径，root cause 为 helper timeout after partial artifact 与 `tf_source_probe_not_executed`。

## 剩余风险

- 本轮不证明浏览器画面首帧可见。
- 本轮不证明地图质量、SLAM 长稳、Nav2 可执行路径、真实 NavigateToPose 或 fixed-route execution。
- 本轮不证明任何非零运动、WAVE ROVER HIL、`/cmd_vel`、`/api/base/manual`、safe-to-control 或 delivery success。
- 本轮只新增 sprint 留档与 artifact，未修改产品代码。

## 完成前反思

- 已限制改动在本轮允许的 sprint 目录内。
- 未修改 `onboard/**`、`docs/vendor/**`、硬件配置、launch、底盘/串口/运动协议代码。
- 没有为扩大功能改 UI。
- 已把 blocked/root cause 明确写入留档，没有把部分证据伪装成成功。
- 验证缺口已归入剩余风险。
