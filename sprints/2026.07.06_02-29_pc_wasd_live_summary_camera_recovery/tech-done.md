# 2026.07.06 02:29｜pc_wasd_live_summary_camera_recovery｜WASD raw 证据平铺与图传恢复复验

## sprint_type

micro

## 本轮目标

继续推进 PC 端打开即用目标：

- 地图、Nav2 路线、雷达点、目标点保持在 7001 页面可见。
- WASD/键盘手控的真实 raw L/R 非零证据能直接从 `live-summary` 读取。
- 对 DV20 实时图传再执行一次上车 USB/UVC 恢复 smoke，确认是否能恢复首帧。

## 实际改动

- `pc-tools/workstation/src/server/index.ts`
  - `GET /api/robot-control/live-summary` 新增平铺字段：
    `command_raw_nonzero_proven`、`command_raw_lr_nonzero_proven`、`command_raw_twist_nonzero_proven`、
    `command_raw_latest_left/right`、`command_raw_latest_linear_x/angular_z`、`motion_evidence_complete`、
    `motion_evidence_source`、`keyboard_command_raw_lr_nonzero`、
    `keyboard_command_raw_latest_left/right`、`keyboard_motion_evidence_complete`。
  - 这些字段只读来自同一次 summary 聚合，不新增运动命令。
- `pc-tools/workstation/src/shared/contracts.ts`
  - 同步 live-summary TypeScript 合同。
- `pc-tools/workstation/test/catalog.test.ts`
  - 增加 live-summary 默认 raw false 断言。
  - 增加 keyboard query 证据场景，确认 live-summary 直接返回 `keyboard_command_raw_lr_nonzero=true`。
- `pc-tools/README.md`
- `docs/product/pc_tools_workstation.md`
- `OKR.md`
  - 同步真实 7001 WASD raw L/R 复验和 DV20 USB recovery smoke 结果。
- 2026-07-06 02:40 CST 追加 PC 地图太小修正：
  - PC 首页和 `/map` 默认缩放从 `200%` 提升到 `300%`。
  - `GET /api/robot-control/summary` / `live-summary` 的 `map_display_default_zoom_percent` 与
    `map_display_direct_map_default_zoom_percent` 同步为 `300%`。
  - ROS2 配套口径继续保持分层：普通用户用 PC 大地图；RViz2/Nav2 RViz 插件与 Foxglove Bridge
    只作工程观察，不替代简易控制台，也不发送运动命令。
- 2026-07-06 03:05 CST 追加自由移动 start 修复：
  - `onboard/scripts/upper_robot_api.py`
    - 增加 `/free_roam_autonomy` runtime 自愈：`/api/free-roam/autonomy/start` 或 stop 写参数前，
      先确认节点/参数服务；缺失时用固定 argv 托管启动
      `ros2 run ros2_trashbot_nav free_roam_autonomy_node`。
    - 托管启动默认仍锁住 `enable_cmd_vel_publish=false` 与 `motion_hil_unlocked=false`，
      只在后续固定参数序列成功后解锁本次低速自由移动。
    - `ros2 param load` 等待窗口从 10s 调整到 30s；参数服务查询慢时先用 node list 避免重复启动同名节点。
    - 失败原因从笼统 `free_roam_param_sequence_failed` 收紧为可行动的
      `free_roam_runtime_unavailable_after_managed_start` 等短 reason。
  - `onboard/scripts/test_upper_robot_api_free_roam.py`
    - 补充缺 runtime 时托管启动、托管启动后仍不可用时失败 reason 的离线合同测试。
  - `pc-tools/README.md`、`docs/product/pc_tools_workstation.md`、`OKR.md`
    - 同步自由移动不依赖相机首帧/雷达 proof 发车、真实 start/stop 复验结果和剩余边界。
- 2026-07-06 03:16 CST 追加共享图传 live-summary 短字段：
  - `pc-tools/workstation/src/server/index.ts`
    - `GET /api/robot-control/live-summary` 平铺
      `camera_shared_preview_single_upstream`、`camera_shared_preview_client_count`、
      `camera_shared_preview_upstream_active`、`camera_shared_preview_content_type_loaded`、
      `camera_shared_preview_cached_frame_loaded`、`camera_shared_preview_last_failure_reason`、
      `camera_shared_preview_last_remote_http_status`。
    - 字段只读来自同一次 summary 聚合，不新开 WebRTC、不额外启动相机流、不发送底盘/导航命令。
  - `pc-tools/workstation/src/shared/contracts.ts`
    - 同步 live-summary TypeScript 合同。
  - `pc-tools/workstation/test/catalog.test.ts`
    - 增加 live-summary 短字段与 `live_closure_summary` / `readback_summary.camera` 同源断言。
  - `pc-tools/README.md`、`docs/product/pc_tools_workstation.md`
    - 同步普通现场 `curl/jq` 可直接确认多人共享预览、非独占和最近失败原因的口径。
- 2026-07-06 03:26 CST 追加共享 MJPEG 冷却窗口诊断修正：
  - `pc-tools/workstation/src/server/index.ts`
    - 将 `mjpeg_auto_retry_cooldown_after_first_frame_failure` 与
      `first_frame_recent_failure_cooldown` 纳入首帧失败 reason 集合。
    - 从上车 payload 的 `last_first_frame_failure_reason` 和
      `last_first_frame_error.first_frame_format_attempts` 继续生成
      `source_first_frame_failed` 与多格式“无首帧”摘要。
  - `pc-tools/workstation/test/catalog.test.ts`
    - 增加共享 MJPEG 冷却失败场景，确认 PC status 不退回 `waiting_for_first_frame`。
  - `pc-tools/README.md`、`docs/product/pc_tools_workstation.md`
    - 同步相机服务重启/冷却窗口内的普通用户诊断口径。
- 2026-07-06 03:36 CST 追加 USB recovery 零帧分类修正：
  - `onboard/scripts/camera_usb_recovery_smoke.py`
    - `v4l2-ctl` recovery 增加 `--stream-poll --verbose`，解析
      `VIDIOC_STREAMON returned 0 (Success)`、`select timeout` 和输出字节数。
    - 新增 `status=streamon_success_zero_byte_no_frame`，并输出
      `streamon_success_observed`、`select_timeout_observed`、`zero_byte_no_frame_observed`、
      `stream_status_summary`、`software_capture_exhausted`、`known_good_uvc_required`、
      `camera_input_signal_check_required`。
    - 高速 USB 且 STREAMON 成功但 0 字节时，下一步明确指向摄像头输入信号、线/接口/供电或
      known-good UVC，而不是继续归因 PC 页面独占或 STREAMON 失败。
  - `pc-tools/workstation/src/server/index.ts`
    - `POST /api/robot-control/camera/usb-recovery` 透传上述只读诊断字段，运动/串口/Nav2 标志继续固定 false。
  - `pc-tools/workstation/src/shared/contracts.ts`
    - 同步 USB recovery TypeScript 合同。
  - `pc-tools/workstation/test/catalog.test.ts`
    - 增加 PC 代理透传新字段断言。
  - `pc-tools/workstation/test/App.test.ts`
    - 更新自动 USB recovery proof fixture，页面只读状态使用精确的零帧分类。
  - `pc-tools/README.md`、`docs/product/pc_tools_workstation.md`
    - 同步当前相机诊断口径和剩余现场动作。
- 2026-07-06 03:47 CST 追加普通首页雷达贴图打开即用修正：
  - `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
    - `scheduleInitialRadarMapRefresh()` 不再把初始雷达贴图补刷新交给 live-loop 的 5s 节流。
    - 首屏 `summary` / `map_preview` 仍在读取时，会按 `700ms x 4` 重试，空闲后直接执行
      `refreshRadarProof({ focusAfterReady:false, mapPreviewAfter:true })`。
    - 普通首页和 `/map` DOM 都暴露 retry 参数和 no-motion 边界：
      `data-initial-radar-map-refresh-retry-delay-ms=700`、
      `data-initial-radar-map-refresh-max-attempts=4`、
      `data-initial-radar-map-refresh-starts-radar-lifecycle=false`、
      `data-initial-radar-map-refresh-sends-motion=false`。
  - `pc-tools/workstation/test/App.test.ts`
    - 新增普通首页自动刷新 stale 雷达 overlay 的测试，确认只调用固定
      `/api/robot-control/radar/scan-proof/refresh`，不调用 radar start、map start、manual、Nav2 execute、
      free-roam start 或 `/cmd_vel`。
  - `pc-tools/README.md`、`docs/product/pc_tools_workstation.md`
    - 同步普通首页打开即用地图/雷达贴图修正，以及本轮相机 audio bind 复测仍 0 字节事实。
- 2026-07-06 04:05 CST 追加 USB recovery audio 恢复闭环与代理透传：
  - `onboard/scripts/camera_usb_recovery_smoke.py`
    - 临时解绑同复合设备 `snd-usb-audio` 后，会按本次解绑记录尝试 bind 回去。
    - 新增 `audio_rebind_ok`、`audio_bind_status_after_rebind`、`topology_after_audio_rebind`；
      `audio_rebind_ok` 以最终 driver 链接为准，避免 sysfs bind 单次返回码比最终状态保守时误判失败。
  - `onboard/scripts/test_camera_usb_recovery_smoke.py`
    - 增加 USB audio unbind/rebind 离线测试，避免 recovery smoke 留下现场设备状态漂移。
  - `pc-tools/workstation/src/server/index.ts`
    - `POST /api/robot-control/camera/usb-recovery` 透传 audio 恢复证据，运动/串口/Nav2 标志继续固定 false。
  - `pc-tools/workstation/src/shared/contracts.ts`
    - 同步 USB recovery TypeScript 合同。
  - `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
    - 普通页 recovery proof DOM 暴露 `data-auto-usb-recovery-audio-rebind-ok`。
  - `pc-tools/workstation/test/catalog.test.ts`
  - `pc-tools/workstation/test/App.test.ts`
    - 增加 PC 代理透传与普通页 DOM 断言。
  - `pc-tools/README.md`、`docs/product/pc_tools_workstation.md`、`OKR.md`
    - 同步 DV20 audio 恢复闭环、UVC quirk 矩阵仍 0 字节、ROS2 配套仍为 RViz2/Foxglove 工程观察。

## 现场验证

硬件资料来源：

- `docs/vendor/VENDOR_INDEX.md`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h`

真实 7001 手控复验：

```bash
curl -X POST 'http://127.0.0.1:7001/api/robot-control/base/manual?baseUrl=http://192.168.1.11:8787' \
  -H 'content-type: application/json' \
  --data '{"direction":"forward","speed_mps":0.08,"duration_ms":240,"command_mode":"pwm"}'
```

结果：

- `proxy_status=command_forwarded`
- `remote_http_status=200`
- `manual_command_executed=true`
- `auto_stop_executed=true`
- `command_raw_lr_nonzero_proven=true`
- `command_raw_latest_left=164`
- `command_raw_latest_right=164`
- `wheel_feedback_lr_nonzero_proven=false`

真实相机恢复复验：

```bash
ssh -p 7878 root@192.168.1.11 \
  'python3 /root/rober/onboard/scripts/camera_usb_recovery_smoke.py --device /dev/video1'
```

结果：

- USB 设备：`3-1`
- USB 视频速率：`480M`
- `uvcvideo quirks=0`
- 已执行 USB reauthorize、autosuspend 关闭、audio 复合接口解绑、相机服务停启
- `YUYV@320x240@20`：10s timeout，0 字节
- `MJPG@480x320@30`：10s timeout，0 字节
- `status=streamon_failed`
- `stream_failure_class=high_speed_zero_byte_no_frame`

真实自由移动 start/stop 复验：

```bash
curl -X POST 'http://127.0.0.1:7001/api/robot-control/free-roam/autonomy/start?baseUrl=http://192.168.1.11:8787' \
  -H 'content-type: application/json' \
  --data '{"confirm_operator_safety":true,"confirm_mapping_active":false}'

curl -X POST 'http://127.0.0.1:7001/api/robot-control/free-roam/autonomy/stop?baseUrl=http://192.168.1.11:8787' \
  -H 'content-type: application/json' \
  --data '{}'
```

结果：

- 上车脚本已同步到 `/root/rober/onboard/scripts/upper_robot_api.py`，远端 `python3 -m py_compile` 通过。
- `trashbot-upper-robot-api.service` 重启后 `GET /api/health` 返回 `status=ready`。
- 直连上车 start：
  - `status=requested`
  - `command_result.ok=true`
  - `managed_runtime.status=started_and_param_available`
  - `start_runtime_wait.ok=true`
  - `latest_decision_state=avoiding`
  - `latest_cmd_vel_publish_enabled=true`
  - `publishes_cmd_vel=true`
  - `sends_motion_commands=true`
- PC 代理 start：
  - `proxy_status=autonomy_forwarded`
  - `remote_http_status=200`
  - `status=requested`
  - `latest_decision_state=avoiding`
  - `latest_cmd_vel_publish_enabled=true`
- PC 代理 stop：
  - `proxy_status=autonomy_forwarded`
  - `remote_http_status=200`
  - `status=requested`
  - `latest_decision_state=stopping`
  - `latest_cmd_vel_publish_enabled=false`
- stop 后 final latest：
  - `decision_state=stopping`
  - `cmd_vel_publish_enabled=false`
  - `free_roam_motion_ready=false`

API 重启后 PC 状态复验：

- `POST /api/robot-control/base/manual` 使用 `command_mode=ros`、`direction=forward`、`speed_mps=0.08`、
  `duration_ms=240`，返回 `command_forwarded`、`manual_command_executed=true`、`auto_stop_executed=true`、
  `command_raw_lr_nonzero_proven=true`、`command_raw_twist_nonzero_proven=true`、raw `L=-164/R=164`。
- 雷达贴图刷新 `POST /api/robot-control/radar/scan-proof/refresh` 返回 `refresh_forwarded`；
  随后 live-summary 返回：
  - `map_current_visible=true`
  - `path_current_visible=true`
  - `radar_map_points_visible=true`
  - `camera_current_visible=false`
  - `camera_source_diagnosis_status=uvc_no_frame_not_exclusive`
  - `keyboard_ready=true`
  - `keyboard_continuous_ready=true`
  - `command_raw_lr_nonzero_proven=true`
  - `free_roam_motion_without_radar_allowed=true`
  - `delivery_success=true`

## 本地验证

已通过：

```bash
cd pc-tools/workstation
npm run test -- catalog.test.ts -t "live-summary route exposes"
npm run test -- catalog.test.ts -t "live-summary"
npm run test -- catalog.test.ts -t "keeps the open PC page live and keyboard-ready"
npm run lint
npm run test
npm run build
cd /Users/m1/apps/rober
python3 -m unittest onboard/scripts/test_upper_robot_api_free_roam.py
python3 -m py_compile onboard/scripts/upper_robot_api.py onboard/scripts/test_upper_robot_api_free_roam.py
git diff --check
```

结果：

- `npm run lint` 通过。
- `npm run test -- catalog.test.ts -t "live-summary route exposes"` 通过。
- `npm run test` 通过：3 个 test file，453 个测试用例通过。
- `npm run build` 通过；Vite 仅输出已有的大 bundle 警告。
- `python3 -m unittest onboard/scripts/test_upper_robot_api_free_roam.py` 通过：13 个测试用例通过。
- `python3 -m py_compile onboard/scripts/upper_robot_api.py onboard/scripts/test_upper_robot_api_free_roam.py` 通过。
- `git diff --check` 通过。
- 重启 `0.0.0.0:7001` 后，`/api/robot-control/summary` 与 `/api/robot-control/live-summary` 均返回：
  - `map_display_default_zoom_percent=300%`
  - `map_display_direct_map_default_zoom_percent=300%`
  - `map_display_fit_zoom_percent=100%`
  - `map_display_max_zoom_percent=1200%`
  - `map_display_ros2_companion_tools=["rviz2","foxglove"]`
  - `map_display_companion_replaces_pc_ui=false`
  - `map_display_starts_ros2=false`
  - `map_display_starts_rviz2=false`
  - `map_display_starts_foxglove=false`
  - `map_display_starts_nav2=false`
- 重启 `0.0.0.0:7001` 后，`GET /api/robot-control/live-summary?baseUrl=http://192.168.1.11:8787` 返回：
  - `status=ready_for_motion`
  - `map_current_visible=true`
  - `path_current_visible=true`
  - `radar_map_points_visible=true`
  - `camera_current_visible=false`
  - `camera_source_diagnosis_status=uvc_no_frame_not_exclusive`
  - `camera_hardware_action_label=检查摄像头输入/供电后复测`
  - `camera_blocks_free_move=false`
  - `keyboard_ready=true`
  - `keyboard_continuous_ready=true`
  - `command_raw_lr_nonzero_proven=true`
  - `command_raw_latest_left=164`
  - `command_raw_latest_right=164`
  - `keyboard_command_raw_lr_nonzero=true`
  - `keyboard_motion_evidence_complete=true`
  - `wheel_lr_nonzero_proven=false`
  - `delivery_success=true`
- 2026-07-06 03:16 CST 实车只读复验：
  - `GET /api/robot-control/live-summary?baseUrl=http://192.168.1.11:8787` 返回：
    - `map_display_primary_url=/map`
    - `map_display_default_zoom_percent=300%`
    - `map_display_ros2_companion_tools=["rviz2","foxglove"]`
    - `map_display_companion_replaces_pc_ui=false`
    - `map_display_starts_ros2=false`
  - 重启 `0.0.0.0:7001` 后，同一 live-summary 返回新增共享图传短字段：
    - `camera_shared_preview_single_upstream=true`
    - `camera_shared_preview_client_count="0"`
    - `camera_shared_preview_upstream_active="false"`
    - `camera_shared_preview_content_type_loaded="false"`
    - `camera_shared_preview_cached_frame_loaded="false"`
    - `camera_shared_preview_last_failure_reason="camera_source_first_frame_failed"`
    - `camera_shared_preview_last_remote_http_status="200"`
  - `GET /api/robot-control/camera/mjpeg/status?baseUrl=http://192.168.1.11:8787` 返回：
    - `status=source_first_frame_failed`
    - `source_diagnosis_status=uvc_no_frame_not_exclusive`
    - `source_failure_reason=probe_total_timeout`
    - `shared_preview_everyone_can_join=true`
    - `exclusive_camera_claim=false`
    - `shared_capture=true`
    - `camera_blocks_free_move=false`
    - 最近 MJPEG/first-frame 尝试仍为多格式无首帧，实时图传未恢复。
- 2026-07-06 03:23 CST 继续相机底层恢复复验：
  - DV20 仍在 USB `480M` high-speed，`/dev/video1` 是 capture，`/dev/video2` 是 metadata。
  - `v4l2-ctl` 对 `MJPG@640x480`、`MJPG@480x320`、`YUYV@320x240` 均 `VIDIOC_STREAMON returned 0`
    后 `select timeout`，输出文件 0 字节。
  - 临时重载 `uvcvideo nodrop=1 timeout=1000 quirks=128` 并 USB reauthorize 后，MJPG/YUYV 仍 0 字节；
    已恢复 `uvcvideo quirks=0 nodrop=0 timeout=5000` 并重启 `trashbot-local-webrtc-camera.service`。
  - 手控 raw 通过 `POST /api/robot-control/base/manual` 补回：
    `command_raw_lr_nonzero_proven=true`、`command_raw_twist_nonzero_proven=true`、raw `L=164/R=164`。
- 2026-07-06 03:26 CST 本地新增测试：
  - `npm run test -- catalog.test.ts -t "cooldown failure"` 通过。
  - `npm run test -- catalog.test.ts -t "MJPEG"` 通过：17 个 MJPEG 相关测试通过。
  - `npm run lint` 通过。
  - `npm run test` 通过：3 个 test file，454 个测试用例通过。
  - `npm run build` 通过；Vite 仅输出已有的大 bundle 警告。
  - `git diff --check` 通过。
  - 重启 `0.0.0.0:7001` 后复验：
    - `camera/mjpeg/status.status=source_first_frame_failed`
    - `source_diagnosis_status=uvc_no_frame_not_exclusive`
    - `source_failure_reason=first_frame_total_timeout`
    - `shared_preview_everyone_can_join=true`
    - `exclusive_camera_claim=false`
    - `camera_blocks_free_move=false`
    - `live-summary.status=ready_for_motion`
    - `map_current_visible=true`
    - `path_current_visible=true`
    - `radar_map_points_visible=true`
    - `keyboard_ready=true`
    - `command_raw_lr_nonzero_proven=true`
- 2026-07-06 03:36 CST 本地与上车新增验证：
  - `python3 -m unittest onboard/scripts/test_camera_usb_recovery_smoke.py` 通过：5 个测试用例通过。
  - `cd pc-tools/workstation && npm run test -- catalog.test.ts -t "USB recovery"` 通过。
  - `cd pc-tools/workstation && npm run test -- App.test.ts -t "USB recovery"` 通过。
  - `cd pc-tools/workstation && npm run lint` 通过。
  - `cd pc-tools/workstation && npm run test` 通过：3 个 test file，454 个测试用例通过。
  - `cd pc-tools/workstation && npm run build` 通过；Vite 仅输出已有的大 bundle 警告。
  - `python3 -m py_compile onboard/scripts/camera_usb_recovery_smoke.py` 通过。
  - `git diff --check` 通过。
  - 已把 `onboard/scripts/camera_usb_recovery_smoke.py` 同步到上位机
    `/root/rober/onboard/scripts/camera_usb_recovery_smoke.py` 并 `py_compile` 通过。
  - 上位机真实 `/dev/video1` recovery 返回：
    - `status=streamon_success_zero_byte_no_frame`
    - `frame_observed=false`
    - `usb_video_speed=480M`
    - `stream_failure_class=high_speed_zero_byte_no_frame`
    - `streamon_success_observed=true`
    - `select_timeout_observed=true`
    - `zero_byte_no_frame_observed=true`
    - `stream_status_summary=YUYV@320x240@20=streamon_success_zero_byte_no_frame;MJPG@480x320@30=streamon_success_zero_byte_no_frame`
    - `software_capture_exhausted=true`
    - `known_good_uvc_required=true`
    - `camera_input_signal_check_required=true`
    - `robot_control_executed=false`
    - `publishes_cmd_vel=false`
    - `opens_base_uart=false`
  - recovery 结束后上位机 `trashbot-local-webrtc-camera.service` 为 `active`，`uvcvideo` 参数保持
    `quirks=0`、`nodrop=0`、`timeout=5000`。
  - 重启本机 `0.0.0.0:7001` 后，PC 代理
    `POST /api/robot-control/camera/usb-recovery?baseUrl=http://192.168.1.11:8787` 返回同样的新字段，并确认
    `robot_control_executed=false`、`publishes_cmd_vel=false`、`opens_base_uart=false`、
    `starts_nav2=false`、`starts_manual=false`、`starts_keyboard=false`、`starts_free_roam=false`、
    `starts_map_runtime=false`。
  - 触发一次 PC MJPEG 代理短拉后，`/api/robot-control/camera/mjpeg/status` 回到
    `source_first_frame_failed / uvc_no_frame_not_exclusive / first_frame_total_timeout`。
  - 最新 live-summary 返回：
    - `status=ready_for_motion`
    - `map_current_visible=true`
    - `path_current_visible=true`
    - `radar_map_points_visible=true`
    - `camera_current_visible=false`
    - `camera_source_diagnosis_status=uvc_no_frame_not_exclusive`
    - `camera_shared_preview_single_upstream=true`
    - `camera_shared_preview_last_failure_reason=first_frame_total_timeout`
    - `keyboard_ready=true`
    - `command_raw_lr_nonzero_proven=true`
    - `wheel_lr_nonzero_proven=false`
    - `delivery_success=true`
    - `map_display_primary_url=/map`
    - `map_display_default_zoom_percent=300%`
    - `map_display_direct_map_default_zoom_percent=300%`
    - `map_display_ros2_companion_tools=["rviz2","foxglove"]`
    - `map_display_companion_replaces_pc_ui=false`
- 2026-07-06 03:47 CST 普通首页雷达贴图与相机补充验证：
  - `cd pc-tools/workstation && npm run test -- App.test.ts -t "ordinary home map"` 通过。
  - `cd pc-tools/workstation && npm run test -- App.test.ts -t "direct map entry"` 通过。
  - `cd pc-tools/workstation && npm run test -- App.test.ts -t "no-motion map radar refresh action"` 通过。
  - `cd pc-tools/workstation && npm run lint` 通过。
  - `cd pc-tools/workstation && npm run test` 通过：3 个 test file，455 个测试用例通过。
  - `cd pc-tools/workstation && npm run build` 通过；Vite 仅输出已有的大 bundle 警告。
  - 上位机排查补充：
    - `trashbot-local-webrtc-camera.service` active。
    - DV20 audio 接口已 bind 回 `snd-usb-audio`，`lsusb -t` 显示 Video/Audio 均在 USB `480M`。
    - 停相机服务后独占直采 `YUYV@320x240@20` 与 `MJPG@640x480@30`：
      `VIDIOC_STREAMON returned 0 (Success)` 后 `select timeout`，输出文件仍 0 字节。
    - ROS2 当前没有可直接替代的 `/camera/image_raw` 等真实图像 topic。
  - 重启本机 `0.0.0.0:7001` 后，先读 live-summary 再触发一次 MJPEG 只读拉流，最终 live-summary 返回：
    - `status=ready_for_motion`
    - `map_current_visible=true`
    - `path_current_visible=true`
    - `radar_map_points_visible=true`
    - `camera_current_visible=false`
    - `camera_source_diagnosis_status=uvc_no_frame_not_exclusive`
    - `camera_shared_preview_single_upstream=true`
    - `camera_shared_preview_last_failure_reason=first_frame_total_timeout`
    - `keyboard_ready=true`
    - `keyboard_continuous_ready=true`
    - `command_raw_lr_nonzero_proven=true`
    - `wheel_lr_nonzero_proven=false`
    - `delivery_success=true`
- 2026-07-06 04:05 CST 相机 UVC quirk 与 audio 恢复复验：
  - 停止 `trashbot-local-webrtc-camera.service` 后，对 DV20 `/dev/video1` 临时测试
    `uvcvideo quirks=16/128/256/4/2/144/400/20/272`，分别抓
    `YUYV@320x240@20` 与 `MJPG@480x320@30`。
  - 所有组合均为 `VIDIOC_STREAMON returned 0 (Success)` 后 `select timeout`，输出文件 0 字节。
  - 测试结束后恢复 `uvcvideo quirks=0,nodrop=0,timeout=5000`，相机服务恢复 `active`。
  - 新版 `camera_usb_recovery_smoke.py --device /dev/video1` 真实返回：
    - `status=streamon_success_zero_byte_no_frame`
    - `stream_failure_class=high_speed_zero_byte_no_frame`
    - `streamon_success_observed=true`
    - `zero_byte_no_frame_observed=true`
    - `audio_rebind_ok=true`
    - `audio_bind_status_after_rebind.3-1:1.2.bound_to_snd_usb_audio=true`
    - `audio_bind_status_after_rebind.3-1:1.3.bound_to_snd_usb_audio=true`
    - `robot_control_executed=false`
    - `publishes_cmd_vel=false`
    - `opens_base_uart=false`
  - 上位机最终状态：
    - `trashbot-local-webrtc-camera.service=active`
    - `uvcvideo quirks=0,nodrop=0,timeout=5000`
    - `lsusb -t` 显示 DV20 Video 接口为 `uvcvideo`、Audio 接口为 `snd-usb-audio`。
  - 新版 7001 PC 代理
    `POST /api/robot-control/camera/usb-recovery?baseUrl=http://192.168.1.11:8787`
    已透传：
    - `proxy_status=recovery_forwarded`
    - `remote_http_status=200`
    - `audio_rebind_ok=true`
    - `topology_after_audio_rebind` 包含 `Driver=snd-usb-audio`
    - `stream_failure_class=high_speed_zero_byte_no_frame`
  - 触发一次 PC MJPEG 只读拉流后，`camera/mjpeg/status` 返回
    `source_first_frame_failed / uvc_no_frame_not_exclusive / first_frame_total_timeout`，
    且 `shared_preview_everyone_can_join=true`、`exclusive_camera_claim=false`、`camera_blocks_free_move=false`。
  - 同轮补雷达刷新和短手控后，最新版 `live-summary` 返回：
    - `status=ready_for_motion`
    - `map_current_visible=true`
    - `path_current_visible=true`
    - `radar_map_points_visible=true`
    - `camera_current_visible=false`
    - `camera_source_diagnosis_status=uvc_no_frame_not_exclusive`
    - `camera_shared_preview_single_upstream=true`
    - `camera_shared_preview_last_failure_reason=first_frame_total_timeout`
    - `keyboard_ready=true`
    - `keyboard_continuous_ready=true`
    - `command_raw_lr_nonzero_proven=true`
    - `command_raw_latest_left=164`
    - `command_raw_latest_right=164`
    - `wheel_lr_nonzero_proven=false`
    - `delivery_success=true`
    - `map_display_default_zoom_percent=300%`
    - `map_display_ros2_companion_tools=["rviz2","foxglove"]`
    - `map_display_companion_replaces_pc_ui=false`

## 剩余风险

- 实时图传仍未出首帧；当前证据继续指向 DV20 上游输入、线材、接口、供电、采集卡/摄像头本体或 known-good UVC 复测。
- `T=1001 L/R` 反馈仍为 0/0；本轮证明的是手控命令 raw L/R 非零、上车执行和 auto stop，不等于 vendor feedback L/R 非零闭环。
- 自由移动 start 已真实发起并进入 `avoiding`；当前近障碍读数使状态机原地换向，不代表已经完成大范围自动扫图或建图验收。
- 本轮没有重新执行完整 Nav2 路线发车；地图/路线/雷达点状态通过现有 live-summary 读取保持可见。
