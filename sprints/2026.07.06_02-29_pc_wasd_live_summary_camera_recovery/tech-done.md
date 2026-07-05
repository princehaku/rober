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
git diff --check
```

结果：

- `npm run lint` 通过。
- `npm run test -- catalog.test.ts -t "live-summary route exposes"` 通过。
- `npm run test` 通过：3 个 test file，453 个测试用例通过。
- `npm run build` 通过；Vite 仅输出已有的大 bundle 警告。
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

## 剩余风险

- 实时图传仍未出首帧；当前证据继续指向 DV20 上游输入、线材、接口、供电、采集卡/摄像头本体或 known-good UVC 复测。
- `T=1001 L/R` 反馈仍为 0/0；本轮证明的是手控命令 raw L/R 非零、上车执行和 auto stop，不等于 vendor feedback L/R 非零闭环。
- 本轮没有执行 Nav2 路线发车；地图/路线/雷达点状态通过现有 live-summary 读取保持可见。
